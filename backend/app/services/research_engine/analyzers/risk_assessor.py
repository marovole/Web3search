"""
Risk Assessor
风险评估器 - 识别催化剂、风险因素、影响评估
"""
import yaml
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from app.services.llm.openrouter_client import OpenRouterClient


class RiskAssessor:
    """风险评估器"""

    def __init__(self):
        """初始化风险评估器"""
        self._load_prompts()
        self.llm_client = OpenRouterClient()

    def _load_prompts(self):
        """加载 prompt 模板"""
        prompt_path = Path(__file__).parent.parent.parent.parent.parent / "prompts" / "deep_research" / "risk.yaml"

        with open(prompt_path, 'r', encoding='utf-8') as f:
            prompts = yaml.safe_load(f)

        self.system_prompt = prompts["system_prompt"]
        self.user_prompt_template = prompts["user_prompt_template"]
        self.output_format = prompts["output_format"]
        self.validation_rules = prompts["validation_rules"]
        self.model_config = prompts["model_config"]

    def _format_recent_events(self, aggregated_data: Dict) -> str:
        """
        格式化近期事件

        Args:
            aggregated_data: 聚合数据

        Returns:
            格式化的近期事件文本
        """
        events = aggregated_data.get("recent_events", [])

        if not events:
            return "暂无近期重要事件数据"

        lines = []
        for event in events[:5]:  # 最多显示5个事件
            if isinstance(event, dict):
                title = event.get("title", "未知事件")
                date = event.get("date", "日期未知")
                lines.append(f"- {title} ({date})")
            elif isinstance(event, str):
                lines.append(f"- {event}")

        return "\n".join(lines) if lines else "暂无近期重要事件数据"

    def _format_competition_summary(self, aggregated_data: Dict) -> str:
        """
        格式化竞争总结

        Args:
            aggregated_data: 聚合数据

        Returns:
            格式化的竞争总结文本
        """
        competitors = aggregated_data.get("competitors", [])

        if not competitors:
            return "暂无竞争对手数据"

        lines = []

        # 主要竞品
        competitor_names = [c.get("name", "Unknown") for c in competitors[:3]]
        if competitor_names:
            lines.append(f"- 主要竞品：{', '.join(competitor_names)}")

        # 市场份额（如果有）
        market_share = aggregated_data.get("market_share", None)
        if market_share:
            lines.append(f"- 市场份额：{market_share}")

        # 竞争压力
        competition_intensity = aggregated_data.get("competition_intensity", "中等")
        lines.append(f"- 竞争强度：{competition_intensity}")

        return "\n".join(lines) if lines else "暂无竞争对手数据"

    def _format_unlock_summary(self, aggregated_data: Dict) -> str:
        """
        格式化解锁总结

        Args:
            aggregated_data: 聚合数据

        Returns:
            格式化的解锁总结文本
        """
        tokenomics = aggregated_data.get("tokenomics", {})
        unlock_schedule = tokenomics.get("unlock_schedule", [])

        if not unlock_schedule:
            return "暂无代币解锁数据"

        lines = []
        total_unlock = 0

        for unlock in unlock_schedule[:3]:  # 最多显示3个即将解锁
            if isinstance(unlock, dict):
                date = unlock.get("date", "日期未知")
                amount = unlock.get("amount", 0)
                beneficiary = unlock.get("beneficiary", "未知")
                total_unlock += amount
                lines.append(f"- {date}: {amount:,.0f} ({beneficiary})")

        if total_unlock > 0:
            circulating = tokenomics.get("circulating_supply", 1)
            percent = (total_unlock / circulating) * 100 if circulating > 0 else 0
            lines.insert(0, f"- 未来6个月解锁总量：{total_unlock:,.0f}（{percent:.1f}%流通量）")

        return "\n".join(lines) if lines else "暂无代币解锁数据"

    def _format_tech_status(self, aggregated_data: Dict) -> str:
        """
        格式化技术/产品状态

        Args:
            aggregated_data: 聚合数据

        Returns:
            格式化的技术状态文本
        """
        tech_status = aggregated_data.get("tech_status", {})

        if not tech_status:
            return "暂无技术状态数据"

        lines = []

        # 产品状态
        if "product_status" in tech_status:
            lines.append(f"- 产品状态：{tech_status['product_status']}")

        # 开发进度
        if "development" in tech_status:
            lines.append(f"- 开发进度：{tech_status['development']}")

        # 安全审计
        if "audits" in tech_status:
            lines.append(f"- 安全审计：{tech_status['audits']}")

        # 如果没有详细信息，使用默认
        if not lines:
            lines.append("- 产品运行稳定，无重大安全事件")
            lines.append("- 持续开发中，定期发布更新")

        return "\n".join(lines)

    def _format_regulatory_environment(self, aggregated_data: Dict) -> str:
        """
        格式化监管环境

        Args:
            aggregated_data: 聚合数据

        Returns:
            格式化的监管环境文本
        """
        regulatory = aggregated_data.get("regulatory", {})

        if not regulatory:
            return "暂无监管环境数据"

        lines = []

        # 监管状态
        if "status" in regulatory:
            lines.append(f"- 监管状态：{regulatory['status']}")

        # 合规情况
        if "compliance" in regulatory:
            lines.append(f"- 合规情况：{regulatory['compliance']}")

        # 监管风险
        if "risk_level" in regulatory:
            lines.append(f"- 监管风险：{regulatory['risk_level']}")

        # 如果没有详细信息，使用默认
        if not lines:
            lines.append("- 监管环境不确定，DeFi 监管趋严")
            lines.append("- 项目尚未明确监管合规路径")

        return "\n".join(lines)

    def _format_prompt(self, aggregated_data: Dict) -> str:
        """
        格式化 prompt

        Args:
            aggregated_data: 聚合数据

        Returns:
            格式化的 prompt
        """
        # 提取基本信息
        symbol = aggregated_data.get("symbol", "Unknown")
        market_data = aggregated_data.get("market_data", {})
        onchain_data = aggregated_data.get("onchain_data", {})

        name = market_data.get("name", symbol)
        category = market_data.get("category", "Unknown")
        market_cap = market_data.get("market_cap", 0)
        active_users_24h = onchain_data.get("active_addresses_24h", 0)

        # 格式化各部分
        recent_events = self._format_recent_events(aggregated_data)
        competition_summary = self._format_competition_summary(aggregated_data)
        unlock_summary = self._format_unlock_summary(aggregated_data)
        tech_status = self._format_tech_status(aggregated_data)
        regulatory_environment = self._format_regulatory_environment(aggregated_data)

        # 填充模板
        prompt = self.user_prompt_template.format(
            symbol=symbol,
            name=name,
            category=category,
            market_cap=market_cap,
            active_users_24h=active_users_24h,
            recent_events=recent_events,
            competition_summary=competition_summary,
            unlock_summary=unlock_summary,
            tech_status=tech_status,
            regulatory_environment=regulatory_environment
        )

        return prompt

    async def analyze(self, aggregated_data: Dict) -> Dict:
        """
        执行风险评估

        Args:
            aggregated_data: 聚合数据

        Returns:
            分析结果字典
        """
        try:
            # 格式化 prompt
            user_prompt = self._format_prompt(aggregated_data)

            # 调用 LLM
            result = await self._call_llm(user_prompt)

            if result is None:
                return self._create_error_response("LLM 调用失败")

            # 验证输出
            is_valid, errors = self._validate_output(result)

            if not is_valid:
                # 尝试修复
                result = self._fix_invalid_output(result, errors)

            result["error"] = False
            return result

        except Exception as e:
            return self._create_error_response(f"分析过程出错: {str(e)}")

    async def _call_llm(self, user_prompt: str) -> Optional[Dict]:
        """
        调用 LLM

        Args:
            user_prompt: 用户 prompt

        Returns:
            LLM 响应字典
        """
        try:
            # 主模型
            response = await self.llm_client.chat_completion(
                model=self.model_config["primary_model"],
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
                    return json.loads(json_str)

        except Exception as e:
            print(f"Primary model failed: {e}")

        # Fallback 模型
        try:
            response = await self.llm_client.chat_completion(
                model=self.model_config["fallback_model"],
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
                    return json.loads(json_str)

        except Exception as e:
            print(f"Fallback model failed: {e}")

        return None

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

        # 验证 catalysts
        if "catalysts" in output:
            catalysts = output["catalysts"]
            for timeframe in ["short_term", "medium_term", "long_term"]:
                if timeframe not in catalysts or not isinstance(catalysts[timeframe], list):
                    errors.append(f"catalysts.{timeframe} must be a list")

        # 验证 risks
        if "risks" in output:
            risks = output["risks"]
            risk_types = ["regulatory", "technical", "competitive", "market", "tokenomics"]
            for risk_type in risk_types:
                if risk_type not in risks or not isinstance(risks[risk_type], list):
                    errors.append(f"risks.{risk_type} must be a list")

        # 验证 risk_reward_analysis
        if "risk_reward_analysis" in output:
            rra = output["risk_reward_analysis"]
            if "risk_reward_ratio" in rra:
                ratio = rra["risk_reward_ratio"]
                if not isinstance(ratio, (int, float)) or ratio < 0:
                    errors.append(f"risk_reward_ratio must be a positive number, got {ratio}")

        # 验证 overall_risk_rating
        if "overall_risk_rating" in output:
            orr = output["overall_risk_rating"]
            if "score" in orr:
                score = orr["score"]
                if not isinstance(score, (int, float)) or score < 0 or score > 10:
                    errors.append(f"overall_risk_rating.score must be 0-10, got {score}")

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
        if "catalysts" not in output:
            output["catalysts"] = {
                "short_term": [],
                "medium_term": [],
                "long_term": []
            }

        if "risks" not in output:
            output["risks"] = {
                "regulatory": [],
                "technical": [],
                "competitive": [],
                "market": [],
                "tokenomics": []
            }

        if "risk_reward_analysis" not in output:
            output["risk_reward_analysis"] = {
                "upside_potential": "数据不足",
                "downside_risk": "数据不足",
                "risk_reward_ratio": 1.0,
                "asymmetry": "对称",
                "rationale": "数据不足"
            }

        if "tail_risks" not in output:
            output["tail_risks"] = []

        if "scenario_analysis" not in output:
            output["scenario_analysis"] = {
                "bull_case": {
                    "triggers": [],
                    "price_target": "数据不足",
                    "probability": "数据不足"
                },
                "base_case": {
                    "triggers": [],
                    "price_target": "数据不足",
                    "probability": "数据不足"
                },
                "bear_case": {
                    "triggers": [],
                    "price_target": "数据不足",
                    "probability": "数据不足"
                }
            }

        if "overall_risk_rating" not in output:
            output["overall_risk_rating"] = {
                "rating": "中等风险",
                "score": 5,
                "risk_factors_summary": "数据不足",
                "catalyst_summary": "数据不足",
                "recommendation": "谨慎配置"
            }

        if "summary" not in output:
            output["summary"] = "风险评估数据不足，无法给出明确结论"

        # 修复 risk_reward_ratio
        if "risk_reward_analysis" in output and "risk_reward_ratio" in output["risk_reward_analysis"]:
            ratio = output["risk_reward_analysis"]["risk_reward_ratio"]
            if not isinstance(ratio, (int, float)) or ratio < 0:
                output["risk_reward_analysis"]["risk_reward_ratio"] = 1.0

        # 修复 overall_risk_rating.score
        if "overall_risk_rating" in output and "score" in output["overall_risk_rating"]:
            score = output["overall_risk_rating"]["score"]
            if not isinstance(score, (int, float)):
                output["overall_risk_rating"]["score"] = 5
            elif score < 0:
                output["overall_risk_rating"]["score"] = 0
            elif score > 10:
                output["overall_risk_rating"]["score"] = 10

        return output

    def _create_error_response(self, error_message: str) -> Dict:
        """
        创建错误响应

        Args:
            error_message: 错误消息

        Returns:
            错误响应字典
        """
        return {
            "error": True,
            "message": error_message,
            "catalysts": {
                "short_term": [],
                "medium_term": [],
                "long_term": []
            },
            "risks": {
                "regulatory": [],
                "technical": [],
                "competitive": [],
                "market": [],
                "tokenomics": []
            },
            "risk_reward_analysis": {
                "upside_potential": "数据不足",
                "downside_risk": "数据不足",
                "risk_reward_ratio": 0,
                "asymmetry": "数据不足",
                "rationale": error_message
            },
            "tail_risks": [],
            "scenario_analysis": {
                "bull_case": {
                    "triggers": [],
                    "price_target": "数据不足",
                    "probability": "数据不足"
                },
                "base_case": {
                    "triggers": [],
                    "price_target": "数据不足",
                    "probability": "数据不足"
                },
                "bear_case": {
                    "triggers": [],
                    "price_target": "数据不足",
                    "probability": "数据不足"
                }
            },
            "overall_risk_rating": {
                "rating": "数据不足",
                "score": 0,
                "risk_factors_summary": error_message,
                "catalyst_summary": error_message,
                "recommendation": "数据不足"
            },
            "summary": f"风险评估失败: {error_message}"
        }


# 创建全局单例
risk_assessor = RiskAssessor()
