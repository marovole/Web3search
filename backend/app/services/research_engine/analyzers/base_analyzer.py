"""
基础分析器
为所有分析器提供统一的基类和通用功能
"""
import json
import time
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

from app.services.llm import llm_client, ModelConfig
from app.services.prompt_manager import prompt_manager
from app.services.research_engine.analyzers.analyzer_output import (
    AnalyzerOutput,
    create_analyzer_output,
    create_error_output,
)


class BaseAnalyzer(ABC):
    """
    基础分析器抽象类
    所有分析器都应该继承此类
    """

    def __init__(self, template_name: str, analyzer_name: str):
        """
        初始化分析器

        Args:
            template_name: Prompt模板名称（不含.yaml后缀）
            analyzer_name: 分析器名称（用于日志和输出）
        """
        self.template_name = template_name
        self.analyzer_name = analyzer_name
        self.llm_client = llm_client
        self.prompt_manager = prompt_manager

        # 加载模板元数据
        try:
            metadata = self.prompt_manager.get_template_metadata(template_name)
            self.model = metadata["model"]
            self.temperature = metadata["temperature"]
            self.max_tokens = metadata["max_tokens"]
        except FileNotFoundError:
            # 如果新模板不存在，使用默认配置
            print(f"⚠️ 模板 {template_name} 不存在，使用默认配置")
            self.model = ModelConfig.DEEP_RESEARCH_SUMMARY
            self.temperature = 0.6
            self.max_tokens = 800

    @abstractmethod
    def _prepare_template_variables(self, aggregated_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        准备模板变量（子类必须实现）

        Args:
            aggregated_data: 聚合的项目数据

        Returns:
            Dict: 模板变量字典
        """
        pass

    @abstractmethod
    def _parse_response(self, content: str) -> Dict[str, Any]:
        """
        解析LLM响应（子类必须实现）

        Args:
            content: LLM返回的文本

        Returns:
            Dict: 解析后的结构化数据
        """
        pass

    @abstractmethod
    def _validate_output(self, result: Dict[str, Any]) -> bool:
        """
        验证输出格式（子类必须实现）

        Args:
            result: 解析后的结果

        Returns:
            bool: 是否通过验证
        """
        pass

    @abstractmethod
    def _fix_invalid_output(self, result: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """
        修复无效输出（子类必须实现）

        Args:
            result: 原始结果
            symbol: 币种符号

        Returns:
            Dict: 修复后的结果
        """
        pass

    def _render_prompt(self, **template_vars) -> str:
        """
        渲染Prompt模板

        Args:
            **template_vars: 模板变量

        Returns:
            str: 渲染后的prompt
        """
        try:
            # 尝试使用新模板
            method_name = f"get_{self.template_name}_prompt"
            if hasattr(self.prompt_manager, method_name):
                method = getattr(self.prompt_manager, method_name)
                return method(**template_vars)
            else:
                # 使用通用渲染方法
                config = self.prompt_manager.get_template_with_config(
                    self.template_name,
                    **template_vars
                )
                return config["prompt"]
        except FileNotFoundError:
            # 如果新模板不存在，返回空字符串（子类需要处理fallback）
            print(f"⚠️ 无法渲染模板 {self.template_name}")
            return ""

    async def _call_llm(
        self,
        prompt: str,
        use_fallback: bool = False
    ) -> str:
        """
        调用LLM生成分析

        Args:
            prompt: 完整的prompt
            use_fallback: 是否使用fallback模型

        Returns:
            str: LLM返回的原始文本
        """
        model = self.model if not use_fallback else ModelConfig.QUICK_CHAT

        response = await self.llm_client.chat_completion(
            messages=[
                {"role": "user", "content": prompt},
            ],
            model=model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

        return response.get("content", "")

    def _clean_json_response(self, content: str) -> str:
        """
        清理JSON响应（移除markdown代码块等）

        Args:
            content: 原始响应

        Returns:
            str: 清理后的JSON字符串
        """
        content = content.strip()

        # 移除markdown代码块标记
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]

        if content.endswith("```"):
            content = content[:-3]

        return content.strip()

    async def analyze(
        self,
        query: str,
        aggregated_data: Dict[str, Any],
    ) -> AnalyzerOutput:
        """
        执行分析（通用流程）

        Args:
            query: 用户查询
            aggregated_data: 聚合的项目数据

        Returns:
            AnalyzerOutput: 分析结果
        """
        start_time = time.time()
        symbol = aggregated_data.get("symbol", "Unknown")

        # 1. 准备模板变量
        template_vars = self._prepare_template_variables(aggregated_data)

        # 2. 渲染prompt
        prompt = self._render_prompt(**template_vars)

        if not prompt:
            # Prompt渲染失败，返回错误
            return create_error_output(
                analyzer_name=self.analyzer_name,
                error_msg=f"无法渲染{self.analyzer_name}的Prompt模板",
                model_used=self.model,
            )

        # 3. 调用LLM
        model_used = self.model
        fallback_used = False

        try:
            content = await self._call_llm(prompt, use_fallback=False)
        except Exception as e:
            print(f"⚠️ {self.analyzer_name} 主模型调用失败: {e}，尝试fallback")
            try:
                content = await self._call_llm(prompt, use_fallback=True)
                model_used = ModelConfig.QUICK_CHAT
                fallback_used = True
            except Exception as fallback_error:
                print(f"❌ {self.analyzer_name} Fallback模型也失败: {fallback_error}")
                return create_error_output(
                    analyzer_name=self.analyzer_name,
                    error_msg=f"{symbol}的{self.analyzer_name}分析失败: {str(fallback_error)}",
                    model_used=model_used,
                )

        # 4. 解析响应
        try:
            result = self._parse_response(content)
        except Exception as e:
            print(f"❌ {self.analyzer_name} 解析响应失败: {e}")
            return create_error_output(
                analyzer_name=self.analyzer_name,
                error_msg=f"解析响应失败: {str(e)}",
                model_used=model_used,
            )

        # 5. 验证输出
        validation_warnings = []
        if not self._validate_output(result):
            print(f"⚠️ {self.analyzer_name} 输出格式验证失败，使用默认值补全")
            validation_warnings.append("输出格式验证失败，已使用默认值补全")
            result = self._fix_invalid_output(result, symbol)

        # 6. 计算生成时间
        generation_time_ms = int((time.time() - start_time) * 1000)

        # 7. 返回AnalyzerOutput
        return create_analyzer_output(
            data=result,
            analyzer_name=self.analyzer_name,
            model_used=model_used,
            fallback_used=fallback_used,
            generation_time_ms=generation_time_ms,
            confidence=result.get("confidence", 70),
            data_sources=result.get("data_sources", ["CoinGecko"]),
            visualization_hints=result.get("visualization_hints", []),
            validation_passed=len(validation_warnings) == 0,
            validation_warnings=validation_warnings,
        )
