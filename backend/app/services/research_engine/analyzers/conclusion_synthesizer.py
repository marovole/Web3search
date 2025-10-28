"""
Conclusion Synthesizer
结论综合器 - 综合所有分析、生成最终观点和建议
"""
import yaml
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from app.services.llm import llm_client
from app.services.research_engine.analyzers.analyzer_output import (
    AnalyzerOutput,
    create_analyzer_output,
    create_error_output,
)


class ConclusionSynthesizer:
    """结论综合器"""

    def __init__(self):
        """初始化结论综合器"""
        self._load_prompts()
        self.llm_client = llm_client

    def _load_prompts(self):
        """加载 prompt 模板"""
        from app.core.config import settings
        prompt_path = settings.BASE_DIR / "prompts" / "deep_research" / "conclusion.yaml"

        with open(prompt_path, 'r', encoding='utf-8') as f:
            prompts = yaml.safe_load(f)

        self.system_prompt = prompts["system_prompt"]
        self.user_prompt_template = prompts["user_prompt_template"]
        self.output_format = prompts["output_format"]
        self.validation_rules = prompts["validation_rules"]
        self.model_config = prompts["model_config"]

    def _extract_summary(self, analysis: Dict, key: str, default: str = "暂无数据") -> str:
        """
        从分析结果中提取摘要

        Args:
            analysis: 分析结果
            key: 摘要键名
            default: 默认值

        Returns:
            摘要文本
        """
        if not analysis or analysis.get("error"):
            return default

        # 尝试获取summary字段
        if "summary" in analysis:
            return analysis["summary"]

        # 根据不同分析器提取关键信息
        return default

    def _format_prompt(self, all_analyses: Dict) -> str:
        """
        格式化 prompt

        Args:
            all_analyses: 所有分析结果的字典

        Returns:
            格式化的 prompt
        """
        symbol = all_analyses.get("symbol", "Unknown")

        # 提取各个分析器的摘要
        tldr_summary = self._extract_summary(all_analyses.get("tldr", {}), "summary")
        timeframe_summary = self._extract_summary(all_analyses.get("timeframe", {}), "summary")
        sentiment_summary = self._extract_summary(all_analyses.get("sentiment", {}), "summary")
        technical_summary = self._extract_summary(all_analyses.get("technical", {}), "summary")
        onchain_summary = self._extract_summary(all_analyses.get("onchain", {}), "summary")
        competitor_summary = self._extract_summary(all_analyses.get("competitor", {}), "summary")
        tokenomics_summary = self._extract_summary(all_analyses.get("tokenomics", {}), "summary")
        risk_summary = self._extract_summary(all_analyses.get("risk", {}), "summary")

        # 填充模板
        prompt = self.user_prompt_template.format(
            symbol=symbol,
            tldr_summary=tldr_summary,
            timeframe_summary=timeframe_summary,
            sentiment_summary=sentiment_summary,
            technical_summary=technical_summary,
            onchain_summary=onchain_summary,
            competitor_summary=competitor_summary,
            tokenomics_summary=tokenomics_summary,
            risk_summary=risk_summary
        )

        return prompt

    async def analyze(self, all_analyses: Dict) -> AnalyzerOutput:
        """
        执行结论综合

        Args:
            all_analyses: 所有分析结果的字典，包含：
                - symbol: 代币符号
                - tldr: TL;DR分析结果
                - timeframe: 时间窗分析结果
                - sentiment: 情绪分析结果
                - technical: 技术面分析结果
                - onchain: 链上分析结果
                - competitor: 竞品分析结果
                - tokenomics: 代币经济学分析结果
                - risk: 风险评估结果

        Returns:
            AnalyzerOutput: 包含结论综合数据、元数据和可视化提示
        """
        start_time = time.time()
        symbol = all_analyses.get("symbol", "Unknown")

        try:
            # 格式化 prompt
            user_prompt = self._format_prompt(all_analyses)

            # 调用 LLM（返回 result, model_used, fallback_used 三元组）
            result, model_used, fallback_used = await self._call_llm(user_prompt)

            if result is None:
                return self._create_error_response("LLM 调用失败", model_used)

            # 验证输出
            is_valid, errors = self._validate_output(result)

            validation_warnings = []
            if not is_valid:
                # 尝试修复
                validation_warnings.append(f"输出验证失败: {', '.join(errors)}")
                result = self._fix_invalid_output(result, errors)

            # 计算生成时间
            generation_time_ms = int((time.time() - start_time) * 1000)

            # 包装为AnalyzerOutput
            return create_analyzer_output(
                data=result,
                analyzer_name="ConclusionSynthesizer",
                model_used=model_used,
                fallback_used=fallback_used,
                generation_time_ms=generation_time_ms,
                confidence=result.get("final_rating", {}).get("confidence"),
                data_sources=["All Analyzers"],
                visualization_hints=[],
                validation_passed=len(validation_warnings) == 0,
                validation_warnings=validation_warnings,
            )

        except Exception as e:
            return self._create_error_response(f"分析过程出错: {str(e)}", self.model_config.get("primary_model", "unknown"))

    async def _call_llm(self, user_prompt: str) -> Tuple[Optional[Dict], str, bool]:
        """
        调用 LLM

        Args:
            user_prompt: 用户 prompt

        Returns:
            三元组: (LLM响应字典, 使用的模型, 是否使用fallback)
        """
        model_used = self.model_config["primary_model"]
        fallback_used = False

        try:
            # 主模型
            response = await self.llm_client.chat_completion(
                model=model_used,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.model_config["temperature"],
                max_tokens=self.model_config["max_tokens"]
            )

            if response and "choices" in response:
                content = response["choices"][0]["message"]["content"]
                # 提取 JSON
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                if json_start != -1 and json_end > json_start:
                    json_str = content[json_start:json_end]
                    return json.loads(json_str), model_used, fallback_used

        except Exception as e:
            print(f"Primary model failed: {e}")

        # Fallback 模型
        model_used = self.model_config["fallback_model"]
        fallback_used = True

        try:
            response = await self.llm_client.chat_completion(
                model=model_used,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.model_config["temperature"],
                max_tokens=self.model_config["max_tokens"]
            )

            if response and "choices" in response:
                content = response["choices"][0]["message"]["content"]
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                if json_start != -1 and json_end > json_start:
                    json_str = content[json_start:json_end]
                    return json.loads(json_str), model_used, fallback_used

        except Exception as e:
            print(f"Fallback model failed: {e}")

        return None, model_used, fallback_used

    def _validate_output(self, output: Dict) -> Tuple[bool, List[str]]:
        """
        验证输出

        Args:
            output: LLM 输出

        Returns:
            (是否有效, 错误列表)
        """
        errors = []

        # 检查必需字段
        required_fields = self.validation_rules["required_fields"]
        for field in required_fields:
            if field not in output:
                errors.append(f"Missing required field: {field}")

        # 验证 confidence_assessment
        if "confidence_assessment" in output:
            ca = output["confidence_assessment"]
            if "overall_confidence" in ca:
                conf = ca["overall_confidence"]
                if not isinstance(conf, (int, float)) or conf < 0 or conf > 100:
                    errors.append(f"overall_confidence must be 0-100, got {conf}")

        # 验证 key_metrics_to_watch
        if "key_metrics_to_watch" in output:
            metrics = output["key_metrics_to_watch"]
            if not isinstance(metrics, list):
                errors.append("key_metrics_to_watch must be a list")
            elif len(metrics) != 5:
                errors.append(f"key_metrics_to_watch must have 5 items, got {len(metrics)}")

        # 验证 final_verdict
        if "final_verdict" in output:
            fv = output["final_verdict"]
            if "risk_reward_ratio" in fv:
                ratio = fv["risk_reward_ratio"]
                if not isinstance(ratio, (int, float)) or ratio < 0:
                    errors.append(f"risk_reward_ratio must be a positive number, got {ratio}")

        return (len(errors) == 0, errors)

    def _fix_invalid_output(self, output: Dict, errors: List[str]) -> Dict:
        """
        修复无效输出

        Args:
            output: 无效输出
            errors: 错误列表

        Returns:
            修复后的输出
        """
        # 补充缺失字段
        if "executive_summary" not in output:
            output["executive_summary"] = {
                "one_sentence_thesis": "数据不足，无法生成投资论点",
                "bull_thesis": [],
                "bear_thesis": [],
                "key_assumptions": [],
                "invalidation_triggers": []
            }

        if "investment_outlook" not in output:
            output["investment_outlook"] = {
                "short_term": {
                    "timeframe": "1-2周",
                    "view": "中性",
                    "price_target": "数据不足",
                    "key_events": [],
                    "rationale": "数据不足"
                },
                "medium_term": {
                    "timeframe": "1-2月",
                    "view": "中性",
                    "price_target": "数据不足",
                    "key_events": [],
                    "rationale": "数据不足"
                }
            }

        if "key_metrics_to_watch" not in output or len(output.get("key_metrics_to_watch", [])) != 5:
            output["key_metrics_to_watch"] = [
                {"metric": "数据不足", "current_value": "N/A", "target": "N/A", "importance": "中", "rationale": "数据不足"}
                for _ in range(5)
            ]

        if "confidence_assessment" not in output:
            output["confidence_assessment"] = {
                "overall_confidence": 50,
                "confidence_level": "中",
                "data_quality": "一般",
                "analysis_completeness": "部分缺失",
                "uncertainty_factors": [],
                "confidence_rationale": "数据不足"
            }

        if "investment_recommendation" not in output:
            output["investment_recommendation"] = {
                "rating": "中性",
                "action": "观望",
                "position_sizing": "0%",
                "entry_strategy": "数据不足",
                "exit_strategy": "数据不足",
                "risk_management": [],
                "suitable_for": "数据不足",
                "not_suitable_for": "数据不足"
            }

        if "catalyst_calendar" not in output:
            output["catalyst_calendar"] = []

        if "comparative_analysis" not in output:
            output["comparative_analysis"] = {
                "vs_competitors": "数据不足",
                "vs_sector": "数据不足",
                "vs_market": "数据不足"
            }

        if "final_verdict" not in output:
            output["final_verdict"] = {
                "verdict": "中性",
                "conviction_level": "低",
                "time_horizon": "数据不足",
                "expected_return": "数据不足",
                "max_drawdown_risk": "数据不足",
                "risk_reward_ratio": 1.0,
                "summary": "数据不足，无法给出明确结论"
            }

        # 修复 overall_confidence
        if "confidence_assessment" in output and "overall_confidence" in output["confidence_assessment"]:
            conf = output["confidence_assessment"]["overall_confidence"]
            if not isinstance(conf, (int, float)):
                output["confidence_assessment"]["overall_confidence"] = 50
            elif conf < 0:
                output["confidence_assessment"]["overall_confidence"] = 0
            elif conf > 100:
                output["confidence_assessment"]["overall_confidence"] = 100

        # 修复 risk_reward_ratio
        if "final_verdict" in output and "risk_reward_ratio" in output["final_verdict"]:
            ratio = output["final_verdict"]["risk_reward_ratio"]
            if not isinstance(ratio, (int, float)) or ratio < 0:
                output["final_verdict"]["risk_reward_ratio"] = 1.0

        return output

    def _create_error_response(self, error_message: str, model_used: str) -> AnalyzerOutput:
        """
        创建错误响应

        Args:
            error_message: 错误消息
            model_used: 尝试使用的模型

        Returns:
            AnalyzerOutput: 错误响应
        """
        return create_error_output(
            analyzer_name="ConclusionSynthesizer",
            error_msg=f"结论综合失败: {error_message}",
            model_used=model_used,
        )


# 创建全局单例
conclusion_synthesizer = ConclusionSynthesizer()
