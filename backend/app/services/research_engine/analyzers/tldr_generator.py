"""
TL;DR 生成器
生成符合specs要求的TL;DR摘要（核心判断+置信度+总结）
"""
import json
import time
from typing import Dict, Any, Optional

from app.services.llm import llm_client, ModelConfig
from app.services.prompt_manager import prompt_manager
from app.services.research_engine.analyzers.analyzer_output import (
    AnalyzerOutput,
    create_analyzer_output,
    create_error_output,
)


class TLDRGenerator:
    """
    TL;DR生成器
    参考：openspec/changes/add-crypto-ai-search-platform/specs/ai-analysis/spec.md
    Scenario: TL;DR生成符合标准格式
    """

    def __init__(self):
        """初始化TL;DR生成器"""
        self.llm_client = llm_client
        self.prompt_manager = prompt_manager

        # 获取模板元数据
        metadata = self.prompt_manager.get_template_metadata("tldr")
        self.model = metadata["model"]
        self.temperature = metadata["temperature"]
        self.max_tokens = metadata["max_tokens"]

        # 输出格式验证规则
        self.required_fields = ["core_thesis", "confidence", "one_liner"]
        self.valid_thesis_values = ["Bull", "Neutral", "Bear"]
        self.confidence_range = {"min": 0, "max": 100}

    async def generate_tldr(
        self,
        query: str,
        aggregated_data: Dict[str, Any],
    ) -> AnalyzerOutput:
        """
        生成TL;DR摘要

        Args:
            query: 用户查询
            aggregated_data: 聚合后的项目数据（来自DataAggregator）

        Returns:
            AnalyzerOutput: 包含TL;DR数据、元数据和可视化提示
            data格式：
            {
                "judgment": "BULL | NEUTRAL | BEAR",
                "judgment_emoji": "🟢 | 🟡 | 🔴",
                "confidence": 85,
                "confidence_level": "高",
                "summary": "一句话总结...",
                "key_metrics": {...},
                "reasoning": "判断理由..."
            }
        """
        start_time = time.time()

        # 提取必要数据
        symbol = aggregated_data.get("symbol", "Unknown")
        project_info = aggregated_data.get("project_info", {})
        market_data = aggregated_data.get("market_data", {})
        social_data = aggregated_data.get("social_data", {})
        onchain_data = aggregated_data.get("onchain_data", {})

        # 格式化提示词
        user_prompt = self._format_prompt(
            query=query,
            symbol=symbol,
            project_info=project_info,
            market_data=market_data,
            social_data=social_data,
            onchain_data=onchain_data,
        )

        # 调用LLM生成
        model_used = self.model
        fallback_used = False

        try:
            # 使用模板配置的主模型
            result = await self._call_llm(user_prompt, use_fallback=False)
        except Exception as e:
            print(f"⚠️ 主模型调用失败: {e}，尝试fallback模型")
            try:
                # Fallback到快速模型
                result = await self._call_llm(user_prompt, use_fallback=True)
                model_used = ModelConfig.QUICK_CHAT
                fallback_used = True
            except Exception as fallback_error:
                # 如果两个模型都失败，返回错误响应
                print(f"❌ Fallback模型也失败: {fallback_error}")
                return self._create_error_response(symbol, str(fallback_error), model_used)

        # 验证输出格式
        validation_warnings = []
        if not self._validate_output(result):
            print("⚠️ 输出格式验证失败，使用默认值补全")
            validation_warnings.append("输出格式验证失败，已使用默认值补全")
            result = self._fix_invalid_output(result, symbol)
        else:
            # 格式正确，转换为旧格式
            result = self._transform_output_format(result, symbol)

        # 计算生成时间
        generation_time_ms = int((time.time() - start_time) * 1000)

        # 包装为AnalyzerOutput
        return create_analyzer_output(
            data=result,
            analyzer_name="TldrGenerator",
            model_used=model_used,
            fallback_used=fallback_used,
            generation_time_ms=generation_time_ms,
            confidence=result.get("confidence"),
            data_sources=["CoinGecko", "Twitter", "Reddit"],
            visualization_hints=[],  # TL;DR不需要可视化
            validation_passed=len(validation_warnings) == 0,
            validation_warnings=validation_warnings,
        )

    def _format_prompt(
        self,
        query: str,
        symbol: str,
        project_info: Dict,
        market_data: Dict,
        social_data: Dict,
        onchain_data: Dict,
    ) -> str:
        """格式化用户提示词，使用PromptManager"""
        # 安全提取数据（带默认值）
        current_price = market_data.get("current_price", "N/A")
        market_cap = market_data.get("market_cap", "N/A")
        price_change_24h = market_data.get("price_change_percentage_24h", 0)
        price_change_7d = market_data.get("price_change_percentage_7d", 0)
        price_change_30d = market_data.get("price_change_percentage_30d", 0)
        volume_24h = market_data.get("total_volume", "N/A")

        project_name = project_info.get("name", symbol)

        twitter_followers = social_data.get("twitter", {}).get("followers", "N/A")
        reddit_subscribers = social_data.get("reddit", {}).get("subscribers", "N/A")
        twitter_sentiment = social_data.get("twitter", {}).get("sentiment", "中性")
        reddit_sentiment = social_data.get("reddit", {}).get("sentiment", "中性")

        active_addresses = onchain_data.get("active_addresses", "N/A")
        daily_transactions = onchain_data.get("daily_transactions", "N/A")

        # 使用PromptManager渲染模板
        prompt = self.prompt_manager.get_tldr_prompt(
            project_name=project_name,
            price=current_price,
            market_cap=str(market_cap),
            volume_24h=str(volume_24h),
            price_change_24h=price_change_24h,
            price_change_7d=price_change_7d,
            price_change_30d=price_change_30d,
            active_addresses=str(active_addresses),
            daily_transactions=str(daily_transactions),
            twitter_sentiment=f"{twitter_sentiment} ({twitter_followers} followers)",
            reddit_sentiment=f"{reddit_sentiment} ({reddit_subscribers} subscribers)",
        )

        return prompt

    async def _call_llm(self, user_prompt: str, use_fallback: bool = False) -> Dict[str, Any]:
        """
        调用LLM生成TL;DR

        Args:
            user_prompt: 渲染后的完整prompt（包含system和user部分）
            use_fallback: 是否使用fallback模型

        Returns:
            Dict: 解析后的JSON响应
        """
        # 使用模板配置的模型，或fallback到默认模型
        model = self.model if not use_fallback else ModelConfig.QUICK_CHAT

        # 调用LLM
        response = await self.llm_client.chat_completion(
            messages=[
                {"role": "user", "content": user_prompt},
            ],
            model=model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

        content = response.get("content", "")

        # 尝试解析JSON
        try:
            # 移除可能的markdown代码块标记
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            result = json.loads(content)
            return result
        except json.JSONDecodeError as e:
            print(f"❌ JSON解析失败: {e}\n原始内容:\n{content}")
            raise ValueError(f"LLM返回了无效的JSON: {str(e)}")

    def _validate_output(self, result: Dict[str, Any]) -> bool:
        """
        验证输出格式（适配新模板格式）

        Args:
            result: LLM生成的结果

        Returns:
            bool: 是否符合格式要求
        """
        # 检查必填字段
        for field in self.required_fields:
            if field not in result:
                print(f"❌ 缺少必填字段: {field}")
                return False

        # 验证core_thesis值
        core_thesis = result.get("core_thesis", "")
        if core_thesis not in self.valid_thesis_values:
            print(f"❌ core_thesis值无效: {core_thesis}")
            return False

        # 验证confidence范围
        confidence = result.get("confidence", -1)
        if not (self.confidence_range["min"] <= confidence <= self.confidence_range["max"]):
            print(f"❌ confidence超出范围: {confidence}")
            return False

        # 验证one_liner长度
        one_liner = result.get("one_liner", "")
        if not (50 <= len(one_liner) <= 300):
            print(f"⚠️ one_liner长度不符合要求: {len(one_liner)}字")
            # 长度问题不算严重错误，只警告

        return True

    def _transform_output_format(self, result: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """
        将新格式转换为旧格式（保持向后兼容）

        新格式:
        {
            "core_thesis": "Bull/Neutral/Bear",
            "confidence": 85,
            "one_liner": "一句话总结",
            "key_metrics": {...}
        }

        转换为旧格式:
        {
            "judgment": "BULL/NEUTRAL/BEAR",
            "judgment_emoji": "🟢/🟡/🔴",
            "confidence": 85,
            "confidence_level": "高/中/低",
            "summary": "一句话总结",
            "key_metrics": {...},
            "reasoning": "..."
        }

        Args:
            result: 新格式的结果
            symbol: 币种符号

        Returns:
            Dict: 旧格式的结果
        """
        # 映射core_thesis到judgment
        thesis_to_judgment = {
            "Bull": "BULL",
            "Neutral": "NEUTRAL",
            "Bear": "BEAR",
        }
        judgment = thesis_to_judgment.get(result.get("core_thesis", "Neutral"), "NEUTRAL")

        # 映射judgment到emoji
        judgment_emoji_map = {
            "BULL": "🟢",
            "NEUTRAL": "🟡",
            "BEAR": "🔴",
        }
        judgment_emoji = judgment_emoji_map[judgment]

        # 映射confidence到confidence_level
        confidence = result.get("confidence", 50)
        if confidence >= 80:
            confidence_level = "高"
        elif confidence >= 60:
            confidence_level = "中等"
        else:
            confidence_level = "低"

        # 转换为旧格式
        transformed = {
            "judgment": judgment,
            "judgment_emoji": judgment_emoji,
            "confidence": confidence,
            "confidence_level": confidence_level,
            "summary": result.get("one_liner", f"{symbol}项目的数据不完整，暂时无法给出明确判断。"),
            "key_metrics": result.get("key_metrics", {}),
            "reasoning": result.get("one_liner", "数据不足，需要更多信息。"),  # one_liner兼作reasoning
        }

        return transformed

    def _fix_invalid_output(self, result: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """
        修复无效输出（补全缺失字段）

        Args:
            result: 原始结果
            symbol: 币种符号

        Returns:
            Dict: 修复后的旧格式结果
        """
        # 尝试从新格式或旧格式中提取数据
        core_thesis = result.get("core_thesis", result.get("judgment", "Neutral"))
        if core_thesis in ["BULL", "NEUTRAL", "BEAR"]:
            # 如果是旧格式的值，转换为新格式
            core_thesis = core_thesis.capitalize()

        confidence = result.get("confidence", 50)
        one_liner = result.get("one_liner", result.get("summary", f"{symbol}项目的数据不完整，暂时无法给出明确判断。"))

        # 构建有效的新格式
        fixed_new_format = {
            "core_thesis": core_thesis if core_thesis in self.valid_thesis_values else "Neutral",
            "confidence": max(0, min(100, confidence)),
            "one_liner": one_liner,
            "key_metrics": result.get("key_metrics", {}),
        }

        # 转换为旧格式
        return self._transform_output_format(fixed_new_format, symbol)

    def _create_error_response(self, symbol: str, error_msg: str, model_used: str) -> AnalyzerOutput:
        """
        创建错误响应

        Args:
            symbol: 币种符号
            error_msg: 错误信息
            model_used: 尝试使用的模型

        Returns:
            AnalyzerOutput: 错误响应
        """
        return create_error_output(
            analyzer_name="TldrGenerator",
            error_msg=f"{symbol}项目的TL;DR生成失败: {error_msg}",
            model_used=model_used,
        )


# 全局单例
tldr_generator = TLDRGenerator()
