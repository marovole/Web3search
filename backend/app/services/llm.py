"""
LLM服务模块
使用OpenRouter API集成多个免费LLM模型
"""
import asyncio
from typing import AsyncGenerator, List, Dict, Any, Optional
from openai import AsyncOpenAI
import tiktoken

from app.core.config import settings


# ================================
# 模型配置
# ================================

class ModelConfig:
    """模型配置类"""

    # 快速对话模型（3秒响应）
    QUICK_CHAT = "qwen/qwen3-30b-a3b:free"

    # 深度研究模型
    DEEP_RESEARCH_SUMMARY = "qwen/qwen3-235b-a22b:free"  # TL;DR生成
    DEEP_RESEARCH_ANALYSIS = "deepseek/deepseek-r1-0528:free"  # 技术分析

    # 备用模型
    FALLBACK = "openai/gpt-oss-20b:free"

    # 模型最大token限制
    MAX_TOKENS = {
        QUICK_CHAT: 8000,
        DEEP_RESEARCH_SUMMARY: 32000,
        DEEP_RESEARCH_ANALYSIS: 64000,
        FALLBACK: 8000,
    }


# ================================
# LLM客户端
# ================================

class LLMClient:
    """
    OpenRouter LLM客户端
    提供异步调用、重试机制、多模型路由
    """

    def __init__(self):
        """初始化OpenRouter客户端"""
        self.client = AsyncOpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url=settings.OPENROUTER_BASE_URL,
        )

        # Token计数器（使用cl100k_base编码）
        try:
            self.encoding = tiktoken.get_encoding("cl100k_base")
        except Exception:
            self.encoding = None

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = ModelConfig.QUICK_CHAT,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False,
        retry_count: int = 3,
    ) -> Dict[str, Any] | AsyncGenerator[str, None]:
        """
        调用聊天完成接口

        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            model: 模型名称
            temperature: 温度参数 (0-1)
            max_tokens: 最大生成token数
            stream: 是否流式返回
            retry_count: 重试次数

        Returns:
            Dict: 完整响应或流式生成器
        """
        for attempt in range(retry_count):
            try:
                # 检查token数量
                prompt_tokens = self.count_tokens(messages)
                max_context = ModelConfig.MAX_TOKENS.get(model, 8000)

                if prompt_tokens > max_context - max_tokens:
                    raise ValueError(
                        f"提示词过长: {prompt_tokens} tokens "
                        f"(最大: {max_context - max_tokens})"
                    )

                # 调用API
                response = await self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=stream,
                )

                if stream:
                    return self._stream_response(response)
                else:
                    return self._parse_response(response)

            except Exception as e:
                if attempt < retry_count - 1:
                    # 重试前等待（指数退避）
                    await asyncio.sleep(2 ** attempt)
                    continue
                else:
                    # 最后一次失败，尝试降级到备用模型
                    if model != ModelConfig.FALLBACK:
                        print(f"⚠️ 模型 {model} 失败，降级到备用模型")
                        return await self.chat_completion(
                            messages=messages,
                            model=ModelConfig.FALLBACK,
                            temperature=temperature,
                            max_tokens=max_tokens,
                            stream=stream,
                            retry_count=1,  # 备用模型只尝试一次
                        )
                    else:
                        raise Exception(f"LLM API调用失败: {str(e)}")

    async def _stream_response(self, response) -> AsyncGenerator[str, None]:
        """
        处理流式响应（任务 8.1 优化）

        实现功能：
        - 50ms chunk间隔控制，提供更平滑的打字机效果
        - Chunk缓冲机制，避免过快输出
        - 自动合并小chunk，减少网络开销
        """
        buffer = ""
        last_yield_time = asyncio.get_event_loop().time()
        chunk_interval = 0.05  # 50ms间隔
        min_chunk_size = 5  # 最小chunk大小（字符数）

        async for chunk in response:
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if delta.content:
                    buffer += delta.content

                    # 检查是否应该yield
                    current_time = asyncio.get_event_loop().time()
                    time_since_last_yield = current_time - last_yield_time

                    # 条件：达到时间间隔 或 缓冲区足够大
                    should_yield = (
                        time_since_last_yield >= chunk_interval or
                        len(buffer) >= min_chunk_size * 2
                    )

                    if should_yield and buffer:
                        yield buffer
                        buffer = ""
                        last_yield_time = current_time

                        # 添加延迟，确保50ms间隔
                        if time_since_last_yield < chunk_interval:
                            await asyncio.sleep(chunk_interval - time_since_last_yield)

        # 确保缓冲区中的最后内容被发送
        if buffer:
            yield buffer

    def _parse_response(self, response) -> Dict[str, Any]:
        """解析完整响应"""
        choice = response.choices[0]
        return {
            "content": choice.message.content,
            "role": choice.message.role,
            "finish_reason": choice.finish_reason,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            },
        }

    def count_tokens(self, messages: List[Dict[str, str]]) -> int:
        """
        计算消息列表的token数量

        Args:
            messages: 消息列表

        Returns:
            int: token数量
        """
        if not self.encoding:
            # 如果编码器不可用，使用粗略估计（1 token ≈ 4 字符）
            total_chars = sum(len(msg.get("content", "")) for msg in messages)
            return total_chars // 4

        # 精确计数
        num_tokens = 0
        for message in messages:
            # 每条消息的开销: <|im_start|>role\ncontent<|im_end|>
            num_tokens += 4
            for key, value in message.items():
                num_tokens += len(self.encoding.encode(value))
        num_tokens += 2  # 每次回复的开销
        return num_tokens

    # ================================
    # 便捷方法：不同场景的预设
    # ================================

    async def quick_chat(
        self,
        user_message: str,
        system_message: Optional[str] = None,
        stream: bool = False,
    ) -> Dict[str, Any] | AsyncGenerator[str, None]:
        """
        快速对话模式（3秒内响应）

        Args:
            user_message: 用户消息
            system_message: 系统提示词
            stream: 是否流式返回

        Returns:
            Dict: 响应结果
        """
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": user_message})

        return await self.chat_completion(
            messages=messages,
            model=ModelConfig.QUICK_CHAT,
            temperature=0.7,
            max_tokens=1024,
            stream=stream,
        )

    async def deep_research_summary(
        self,
        context: str,
        query: str,
    ) -> str:
        """
        深度研究：生成TL;DR摘要

        Args:
            context: 研究上下文（数据汇总）
            query: 用户查询

        Returns:
            str: 摘要内容
        """
        messages = [
            {
                "role": "system",
                "content": "你是一位专业的加密货币分析师，擅长总结复杂信息。",
            },
            {
                "role": "user",
                "content": f"""基于以下数据，为用户查询生成简洁的TL;DR摘要（2-3句话）：

查询: {query}

数据:
{context}

要求:
- 突出最关键的发现
- 使用简洁专业的语言
- 不要包含细节数据
""",
            },
        ]

        response = await self.chat_completion(
            messages=messages,
            model=ModelConfig.DEEP_RESEARCH_SUMMARY,
            temperature=0.5,
            max_tokens=512,
            stream=False,
        )

        return response["content"]

    async def deep_research_analysis(
        self,
        context: str,
        query: str,
        analysis_type: str,
    ) -> str:
        """
        深度研究：生成特定维度的分析

        Args:
            context: 研究上下文
            query: 用户查询
            analysis_type: 分析类型（technical, fundamental, community等）

        Returns:
            str: 分析内容
        """
        analysis_prompts = {
            "technical": "从技术角度分析项目的代码质量、安全性和创新性",
            "fundamental": "从基本面分析项目的经济模型、团队背景和发展前景",
            "community": "从社区维度分析项目的社区活跃度、舆情和影响力",
            "market": "从市场角度分析项目的价格表现、交易量和市值趋势",
            "risk": "识别项目面临的主要风险因素和潜在问题",
            "competitor": "对比分析竞争对手，找出项目的优势和劣势",
        }

        prompt = analysis_prompts.get(analysis_type, "进行全面分析")

        messages = [
            {
                "role": "system",
                "content": "你是一位资深的加密货币分析师，擅长深度研究和批判性思考。",
            },
            {
                "role": "user",
                "content": f"""基于以下数据，{prompt}：

查询: {query}

数据:
{context}

要求:
- 提供有数据支撑的分析
- 客观评估优势和风险
- 给出具体的论据和推理过程
- 使用Markdown格式，包含小标题
""",
            },
        ]

        response = await self.chat_completion(
            messages=messages,
            model=ModelConfig.DEEP_RESEARCH_ANALYSIS,
            temperature=0.6,
            max_tokens=3072,
            stream=False,
        )

        return response["content"]

    async def generate_report_section(
        self,
        section_title: str,
        data: Dict[str, Any],
        template: str,
    ) -> str:
        """
        生成报告的某个章节

        Args:
            section_title: 章节标题
            data: 相关数据
            template: 章节模板

        Returns:
            str: 生成的章节内容
        """
        messages = [
            {
                "role": "system",
                "content": "你是一位专业的加密货币分析师，擅长撰写结构化的研究报告。",
            },
            {
                "role": "user",
                "content": f"""请根据以下模板和数据，生成报告的"{section_title}"章节：

模板:
{template}

数据:
{data}

要求:
- 严格按照模板结构
- 使用Markdown格式
- 数据准确，论述清晰
- 包含必要的图表说明
""",
            },
        ]

        response = await self.chat_completion(
            messages=messages,
            model=ModelConfig.DEEP_RESEARCH_ANALYSIS,
            temperature=0.5,
            max_tokens=2048,
            stream=False,
        )

        return response["content"]


# ================================
# 全局实例
# ================================

# 创建全局LLM客户端实例
llm_client = LLMClient()


# ================================
# 辅助函数
# ================================

async def test_models():
    """测试所有模型是否可用"""
    test_message = "Hello! Please respond with 'OK' if you can hear me."
    models = [
        ModelConfig.QUICK_CHAT,
        ModelConfig.DEEP_RESEARCH_SUMMARY,
        ModelConfig.DEEP_RESEARCH_ANALYSIS,
        ModelConfig.FALLBACK,
    ]

    results = {}
    for model in models:
        try:
            response = await llm_client.chat_completion(
                messages=[{"role": "user", "content": test_message}],
                model=model,
                max_tokens=50,
            )
            results[model] = "✅ OK"
        except Exception as e:
            results[model] = f"❌ Failed: {str(e)}"

    return results
