"""
Tokenomics Analyzer
代币经济学分析器 - 供应结构、解锁时间表、价值捕获路径
"""
import yaml
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timedelta
from app.services.llm.openrouter_client import OpenRouterClient


class TokenomicsAnalyzer:
    """代币经济学分析器"""

    def __init__(self):
        """初始化代币经济学分析器"""
        self._load_prompts()
        self.llm_client = OpenRouterClient()

    def _load_prompts(self):
        """加载 prompt 模板"""
        prompt_path = Path(__file__).parent.parent.parent.parent.parent / "prompts" / "deep_research" / "tokenomics.yaml"

        with open(prompt_path, 'r', encoding='utf-8') as f:
            prompts = yaml.safe_load(f)

        self.system_prompt = prompts["system_prompt"]
        self.user_prompt_template = prompts["user_prompt_template"]
        self.output_format = prompts["output_format"]
        self.validation_rules = prompts["validation_rules"]
        self.model_config = prompts["model_config"]

    def _analyze_supply_structure(self, tokenomics_data: Dict) -> Dict:
        """
        分析供应结构

        Args:
            tokenomics_data: 代币经济学数据

        Returns:
            供应结构字典
        """
        total_supply = tokenomics_data.get("total_supply", 0)
        circulating_supply = tokenomics_data.get("circulating_supply", 0)
        max_supply = tokenomics_data.get("max_supply", total_supply)

        # 计算流通率
        circulation_rate = 0
        if total_supply > 0:
            circulation_rate = round((circulating_supply / total_supply) * 100, 1)

        # 分配明细
        allocation = tokenomics_data.get("allocation", {})

        return {
            "total_supply": total_supply,
            "circulating_supply": circulating_supply,
            "circulation_rate": circulation_rate,
            "max_supply": max_supply if max_supply else "无上限",
            "allocation": allocation
        }

    def _analyze_unlock_schedule(self, tokenomics_data: Dict, circulating_supply: float) -> Dict:
        """
        分析解锁时间表

        Args:
            tokenomics_data: 代币经济学数据
            circulating_supply: 流通供应量

        Returns:
            解锁时间表字典
        """
        unlock_schedule = tokenomics_data.get("unlock_schedule", [])

        # 计算未来6个月和12个月的解锁总量
        today = datetime.now()
        six_months_later = today + timedelta(days=180)
        twelve_months_later = today + timedelta(days=365)

        next_6months_unlock = 0
        next_12months_unlock = 0
        upcoming_unlocks = []

        for unlock in unlock_schedule:
            unlock_date_str = unlock.get("date", "")
            amount = unlock.get("amount", 0)

            try:
                unlock_date = datetime.strptime(unlock_date_str, "%Y-%m-%d")

                # 计算占流通量的百分比
                percent_of_circulating = 0
                if circulating_supply > 0:
                    percent_of_circulating = round((amount / circulating_supply) * 100, 2)

                unlock_info = {
                    "date": unlock_date_str,
                    "amount": amount,
                    "percent_of_circulating": percent_of_circulating,
                    "beneficiary": unlock.get("beneficiary", "Unknown")
                }

                # 评估影响
                if percent_of_circulating >= 10:
                    unlock_info["impact"] = "高"
                elif percent_of_circulating >= 5:
                    unlock_info["impact"] = "中"
                else:
                    unlock_info["impact"] = "低"

                upcoming_unlocks.append(unlock_info)

                # 累计解锁量
                if unlock_date <= six_months_later:
                    next_6months_unlock += amount
                if unlock_date <= twelve_months_later:
                    next_12months_unlock += amount

            except ValueError:
                # 日期格式错误，跳过
                continue

        # 评估解锁压力
        unlock_pressure = "低"
        pressure_rationale = "解锁压力可控"

        if circulating_supply > 0:
            six_month_percent = (next_6months_unlock / circulating_supply) * 100
            if six_month_percent >= 20:
                unlock_pressure = "高"
                pressure_rationale = f"未来6个月解锁{six_month_percent:.1f}%流通量，抛压较大"
            elif six_month_percent >= 10:
                unlock_pressure = "中"
                pressure_rationale = f"未来6个月解锁{six_month_percent:.1f}%流通量，抛压中等"
            else:
                pressure_rationale = f"未来6个月解锁{six_month_percent:.1f}%流通量，抛压较小"

        return {
            "upcoming_unlocks": upcoming_unlocks[:5],  # 最多显示5个即将解锁
            "next_6months_unlock": next_6months_unlock,
            "next_12months_unlock": next_12months_unlock,
            "unlock_pressure": unlock_pressure,
            "pressure_rationale": pressure_rationale
        }

    def _analyze_value_capture(self, tokenomics_data: Dict) -> Dict:
        """
        分析价值捕获路径

        Args:
            tokenomics_data: 代币经济学数据

        Returns:
            价值捕获字典
        """
        value_capture = tokenomics_data.get("value_capture", {})

        mechanisms = value_capture.get("mechanisms", [])
        revenue_share = value_capture.get("revenue_share_to_holders", "0%")
        deflationary = value_capture.get("deflationary", False)
        flywheel_effect = value_capture.get("flywheel_effect", "弱")

        return {
            "mechanisms": mechanisms,
            "revenue_share_to_holders": revenue_share,
            "deflationary": deflationary,
            "flywheel_effect": flywheel_effect
        }

    def _format_allocation_data(self, allocation: Dict) -> str:
        """
        格式化分配数据

        Args:
            allocation: 分配字典

        Returns:
            格式化的分配数据文本
        """
        if not allocation:
            return "暂无分配数据"

        lines = []
        for key, value in allocation.items():
            if isinstance(value, dict):
                percent = value.get("percent", 0)
                vesting = value.get("vesting_period", "N/A")
                lines.append(f"- {key}: {percent}% ({vesting})")
            else:
                lines.append(f"- {key}: {value}")

        return "\n".join(lines) if lines else "暂无分配数据"

    def _format_unlock_schedule(self, unlock_schedule: List[Dict]) -> str:
        """
        格式化解锁时间表

        Args:
            unlock_schedule: 解锁列表

        Returns:
            格式化的解锁时间表文本
        """
        if not unlock_schedule:
            return "暂无解锁时间表数据"

        lines = []
        for unlock in unlock_schedule[:5]:  # 最多显示5个
            date = unlock.get("date", "N/A")
            amount = unlock.get("amount", 0)
            beneficiary = unlock.get("beneficiary", "N/A")
            percent = unlock.get("percent_of_circulating", 0)

            lines.append(f"- {date}: {amount:,.0f} ({beneficiary}, 占流通量{percent:.2f}%)")

        return "\n".join(lines) if lines else "暂无解锁时间表数据"

    def _format_value_capture(self, mechanisms: List[Dict]) -> str:
        """
        格式化价值捕获机制

        Args:
            mechanisms: 价值捕获机制列表

        Returns:
            格式化的价值捕获机制文本
        """
        if not mechanisms:
            return "暂无价值捕获机制数据"

        lines = []
        for mech in mechanisms:
            mech_type = mech.get("type", "Unknown")
            description = mech.get("description", "")
            lines.append(f"- {mech_type}: {description}")

        return "\n".join(lines) if lines else "暂无价值捕获机制数据"

    def _format_prompt(self, aggregated_data: Dict) -> str:
        """
        格式化 prompt

        Args:
            aggregated_data: 聚合数据

        Returns:
            格式化的 prompt
        """
        # 提取数据
        symbol = aggregated_data.get("symbol", "Unknown")
        market_data = aggregated_data.get("market_data", {})
        tokenomics_data = aggregated_data.get("tokenomics", {})

        # 供应信息
        total_supply = tokenomics_data.get("total_supply", 0)
        circulating_supply = tokenomics_data.get("circulating_supply", 0)
        max_supply = tokenomics_data.get("max_supply", total_supply)

        circulation_rate = 0
        if total_supply > 0:
            circulation_rate = (circulating_supply / total_supply) * 100

        # 市场数据
        market_cap = market_data.get("market_cap", 0)
        fdv = market_data.get("fdv", market_cap)

        # 协议收入和回购
        onchain_data = aggregated_data.get("onchain_data", {})
        protocol_revenue_30d = onchain_data.get("protocol_revenue_30d", 0)
        buyback_burn_30d = onchain_data.get("buyback_burn_30d", 0)

        # 分配结构
        allocation = tokenomics_data.get("allocation", {})
        allocation_data = self._format_allocation_data(allocation)

        # 解锁时间表
        unlock_schedule = tokenomics_data.get("unlock_schedule", [])
        unlock_schedule_text = self._format_unlock_schedule(unlock_schedule)

        # 价值捕获机制
        value_capture = tokenomics_data.get("value_capture", {})
        mechanisms = value_capture.get("mechanisms", [])
        value_capture_text = self._format_value_capture(mechanisms)

        # 填充模板
        prompt = self.user_prompt_template.format(
            symbol=symbol,
            total_supply=total_supply,
            circulating_supply=circulating_supply,
            circulation_rate=circulation_rate,
            max_supply=max_supply if max_supply else "无上限",
            allocation_data=allocation_data,
            unlock_schedule=unlock_schedule_text,
            value_capture_mechanisms=value_capture_text,
            market_cap=market_cap,
            fdv=fdv,
            protocol_revenue_30d=protocol_revenue_30d,
            buyback_burn_30d=buyback_burn_30d
        )

        return prompt

    async def analyze(self, aggregated_data: Dict) -> Dict:
        """
        执行代币经济学分析

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

        # 验证 supply_structure
        if "supply_structure" in output:
            ss = output["supply_structure"]
            if "circulation_rate" in ss:
                rate = ss["circulation_rate"]
                if not isinstance(rate, (int, float)) or rate < 0 or rate > 100:
                    errors.append(f"circulation_rate must be 0-100, got {rate}")

        # 验证 unlock_schedule
        if "unlock_schedule" in output:
            us = output["unlock_schedule"]
            if "unlock_pressure" in us:
                valid_pressures = ["高", "中", "低"]
                if us["unlock_pressure"] not in valid_pressures:
                    errors.append(f"Invalid unlock_pressure: {us['unlock_pressure']}")

        # 验证 value_capture
        if "value_capture" in output:
            vc = output["value_capture"]
            if "deflationary" in vc and not isinstance(vc["deflationary"], bool):
                errors.append(f"deflationary must be boolean")
            if "flywheel_effect" in vc:
                valid_effects = ["强", "中", "弱"]
                if vc["flywheel_effect"] not in valid_effects:
                    errors.append(f"Invalid flywheel_effect: {vc['flywheel_effect']}")

        # 验证 token_utility
        if "token_utility" in output:
            tu = output["token_utility"]
            if "utility_score" in tu:
                score = tu["utility_score"]
                if not isinstance(score, (int, float)) or score < 0 or score > 10:
                    errors.append(f"utility_score must be 0-10, got {score}")

        # 验证 incentive_alignment
        if "incentive_alignment" in output:
            ia = output["incentive_alignment"]
            if "alignment_score" in ia:
                score = ia["alignment_score"]
                if not isinstance(score, (int, float)) or score < 0 or score > 10:
                    errors.append(f"alignment_score must be 0-10, got {score}")

        # 验证 tokenomics_health_score
        if "tokenomics_health_score" in output:
            ths = output["tokenomics_health_score"]
            if "score" in ths:
                score = ths["score"]
                if not isinstance(score, (int, float)) or score < 0 or score > 100:
                    errors.append(f"tokenomics_health_score must be 0-100, got {score}")

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
        if "supply_structure" not in output:
            output["supply_structure"] = {
                "total_supply": 0,
                "circulating_supply": 0,
                "circulation_rate": 0,
                "max_supply": "数据不足",
                "emission_rate": "数据不足",
                "allocation_breakdown": {},
                "distribution_fairness": "中等",
                "fairness_rationale": "数据不足"
            }

        if "unlock_schedule" not in output:
            output["unlock_schedule"] = {
                "upcoming_unlocks": [],
                "next_6months_unlock": 0,
                "next_12months_unlock": 0,
                "unlock_pressure": "中",
                "pressure_rationale": "数据不足"
            }

        if "value_capture" not in output:
            output["value_capture"] = {
                "mechanisms": [],
                "revenue_share_to_holders": "0%",
                "deflationary": False,
                "flywheel_effect": "弱",
                "flywheel_description": "数据不足"
            }

        if "token_utility" not in output:
            output["token_utility"] = {
                "use_cases": [],
                "demand_drivers": [],
                "utility_score": 5,
                "utility_rating": "中"
            }

        if "inflation_deflation" not in output:
            output["inflation_deflation"] = {
                "current_inflation_rate": "数据不足",
                "future_inflation_rate": "数据不足",
                "deflation_mechanisms": [],
                "net_inflation": "数据不足",
                "inflation_vs_revenue_growth": "数据不足",
                "sustainability": "需观察"
            }

        if "risk_assessment" not in output:
            output["risk_assessment"] = {
                "tokenomics_risks": [],
                "death_spiral_risk": "中",
                "risk_rationale": "数据不足",
                "mitigation_factors": []
            }

        if "incentive_alignment" not in output:
            output["incentive_alignment"] = {
                "aligned_with_protocol_success": False,
                "alignment_score": 5,
                "alignment_factors": [],
                "misalignment_concerns": []
            }

        if "tokenomics_health_score" not in output:
            output["tokenomics_health_score"] = {
                "score": 50,
                "rating": "一般 (40-59)",
                "strengths": [],
                "weaknesses": []
            }

        if "summary" not in output:
            output["summary"] = "代币经济学分析数据不足，无法给出明确结论"

        # 修复分数范围
        if "supply_structure" in output and "circulation_rate" in output["supply_structure"]:
            rate = output["supply_structure"]["circulation_rate"]
            if not isinstance(rate, (int, float)):
                output["supply_structure"]["circulation_rate"] = 50
            elif rate < 0:
                output["supply_structure"]["circulation_rate"] = 0
            elif rate > 100:
                output["supply_structure"]["circulation_rate"] = 100

        if "token_utility" in output and "utility_score" in output["token_utility"]:
            score = output["token_utility"]["utility_score"]
            if not isinstance(score, (int, float)):
                output["token_utility"]["utility_score"] = 5
            elif score < 0:
                output["token_utility"]["utility_score"] = 0
            elif score > 10:
                output["token_utility"]["utility_score"] = 10

        if "incentive_alignment" in output and "alignment_score" in output["incentive_alignment"]:
            score = output["incentive_alignment"]["alignment_score"]
            if not isinstance(score, (int, float)):
                output["incentive_alignment"]["alignment_score"] = 5
            elif score < 0:
                output["incentive_alignment"]["alignment_score"] = 0
            elif score > 10:
                output["incentive_alignment"]["alignment_score"] = 10

        if "tokenomics_health_score" in output and "score" in output["tokenomics_health_score"]:
            score = output["tokenomics_health_score"]["score"]
            if not isinstance(score, (int, float)):
                output["tokenomics_health_score"]["score"] = 50
            elif score < 0:
                output["tokenomics_health_score"]["score"] = 0
            elif score > 100:
                output["tokenomics_health_score"]["score"] = 100

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
            "supply_structure": {
                "total_supply": 0,
                "circulating_supply": 0,
                "circulation_rate": 0,
                "max_supply": "数据不足",
                "emission_rate": "数据不足",
                "allocation_breakdown": {},
                "distribution_fairness": "数据不足",
                "fairness_rationale": error_message
            },
            "unlock_schedule": {
                "upcoming_unlocks": [],
                "next_6months_unlock": 0,
                "next_12months_unlock": 0,
                "unlock_pressure": "未知",
                "pressure_rationale": error_message
            },
            "value_capture": {
                "mechanisms": [],
                "revenue_share_to_holders": "数据不足",
                "deflationary": False,
                "flywheel_effect": "数据不足",
                "flywheel_description": error_message
            },
            "token_utility": {
                "use_cases": [],
                "demand_drivers": [],
                "utility_score": 0,
                "utility_rating": "数据不足"
            },
            "inflation_deflation": {
                "current_inflation_rate": "数据不足",
                "future_inflation_rate": "数据不足",
                "deflation_mechanisms": [],
                "net_inflation": "数据不足",
                "inflation_vs_revenue_growth": "数据不足",
                "sustainability": "数据不足"
            },
            "risk_assessment": {
                "tokenomics_risks": [],
                "death_spiral_risk": "未知",
                "risk_rationale": error_message,
                "mitigation_factors": []
            },
            "incentive_alignment": {
                "aligned_with_protocol_success": False,
                "alignment_score": 0,
                "alignment_factors": [],
                "misalignment_concerns": []
            },
            "tokenomics_health_score": {
                "score": 0,
                "rating": "数据不足",
                "strengths": [],
                "weaknesses": []
            },
            "summary": f"代币经济学分析失败: {error_message}"
        }


# 创建全局单例
tokenomics_analyzer = TokenomicsAnalyzer()
