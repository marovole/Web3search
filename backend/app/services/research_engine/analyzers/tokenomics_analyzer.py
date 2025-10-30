"""
Tokenomics Analyzer
代币经济学分析器 - 供应结构、解锁时间表、价值捕获路径
"""
import yaml
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timedelta
from app.services.llm import llm_client
from app.services.research_engine.analyzers.analyzer_output import (
    AnalyzerOutput,
    create_analyzer_output,
    create_error_output,
)


class TokenomicsAnalyzer:
    """代币经济学分析器"""

    def __init__(self):
        """初始化代币经济学分析器"""
        self._load_prompts()
        self.llm_client = llm_client

    def _load_prompts(self):
        """加载 prompt 模板"""
        from app.core.config import settings
        prompt_path = settings.BASE_DIR / "prompts" / "deep_research" / "tokenomics.yaml"

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

    def _analyze_inflation_model(self, tokenomics_data: Dict, market_data: Dict) -> Dict:
        """
        分析通胀模型

        Args:
            tokenomics_data: 代币经济学数据
            market_data: 市场数据

        Returns:
            通胀模型分析字典
        """
        total_supply = tokenomics_data.get("total_supply", 0)
        max_supply = tokenomics_data.get("max_supply", total_supply)

        # 新发行量（如果有）
        new_issuance_annual = tokenomics_data.get("new_issuance_annual", 0)
        staking_rewards_annual = tokenomics_data.get("staking_rewards_annual", 0)

        # 计算年化通胀率
        inflation_rate = 0
        if total_supply > 0:
            total_new_tokens = new_issuance_annual + staking_rewards_annual
            inflation_rate = (total_new_tokens / total_supply) * 100

        # 评估通胀压力
        if inflation_rate >= 10:
            inflation_pressure = "高"
            inflation_assessment = f"年化通胀率{inflation_rate:.1f}%过高，可能导致币价承压"
        elif inflation_rate >= 5:
            inflation_pressure = "中"
            inflation_assessment = f"年化通胀率{inflation_rate:.1f}%适中，需要持续监控"
        elif inflation_rate > 0:
            inflation_pressure = "低"
            inflation_assessment = f"年化通胀率{inflation_rate:.1f}%较低，通胀压力可控"
        else:
            inflation_pressure = "无通胀"
            inflation_assessment = "无新增发行，低通胀或通缩机制"

        # 是否有上限
        has_max_supply = max_supply and max_supply != total_supply
        supply_limit = max_supply if has_max_supply else "无上限"

        return {
            "inflation_rate_annual": round(inflation_rate, 2),
            "new_issuance_annual": new_issuance_annual,
            "staking_rewards_annual": staking_rewards_annual,
            "inflation_pressure": inflation_pressure,
            "inflation_assessment": inflation_assessment,
            "has_max_supply": has_max_supply,
            "supply_limit": supply_limit,
        }

    def _analyze_team_and_investors(self, project_data: Dict) -> Dict:
        """
        分析项目团队和投资者

        Args:
            project_data: 项目数据

        Returns:
            团队和投资者分析字典
        """
        team = project_data.get("team", [])
        investors = project_data.get("investors", [])
        advisors = project_data.get("advisors", [])

        # 团队分析
        team_size = len(team)
        team_experience_score = 0
        notable_team_members = []

        for member in team:
            experience = member.get("experience_years", 0)
            team_experience_score += experience

            # 识别知名成员
            if member.get("notable", False) or experience >= 10:
                notable_team_members.append(member.get("name", "Unknown"))

        avg_experience = team_experience_score / team_size if team_size > 0 else 0

        # 团队质量评估
        if team_size >= 10 and avg_experience >= 5:
            team_quality = "优秀"
            team_assessment = f"团队规模{team_size}人，平均经验{avg_experience:.1f}年，实力雄厚"
        elif team_size >= 5 and avg_experience >= 3:
            team_quality = "良好"
            team_assessment = f"团队规模{team_size}人，平均经验{avg_experience:.1f}年，经验丰富"
        elif team_size >= 3:
            team_quality = "一般"
            team_assessment = f"团队规模{team_size}人，经验相对有限"
        else:
            team_quality = "待观察"
            team_assessment = "团队信息不足，建议进一步了解"

        # 投资者分析
        investor_count = len(investors)
        notable_investors = []

        for investor in investors:
            if investor.get("notable", False) or investor.get("tier", "") in ["A", "A+", "顶级"]:
                notable_investors.append(investor.get("name", "Unknown"))

        # 投资者质量评估
        if investor_count >= 20 or len(notable_investors) >= 5:
            investor_quality = "优秀"
            investor_assessment = f"获得{investor_count}家机构投资，其中{len(notable_investors)}家顶级机构"
        elif investor_count >= 10 or len(notable_investors) >= 2:
            investor_quality = "良好"
            investor_assessment = f"获得{investor_count}家机构投资，有一定认可度"
        elif investor_count >= 3:
            investor_quality = "一般"
            investor_assessment = f"获得{investor_count}家机构投资"
        else:
            investor_quality = "待观察"
            investor_assessment = "投资者信息有限"

        return {
            "team_size": team_size,
            "avg_team_experience": round(avg_experience, 1),
            "notable_team_members": notable_team_members[:5],  # 最多显示5个
            "team_quality": team_quality,
            "team_assessment": team_assessment,
            "investor_count": investor_count,
            "notable_investors": notable_investors[:5],  # 最多显示5个
            "investor_quality": investor_quality,
            "investor_assessment": investor_assessment,
            "advisor_count": len(advisors),
        }

    def _analyze_business_model(self, project_data: Dict, onchain_data: Dict) -> Dict:
        """
        分析业务模式和收入

        Args:
            project_data: 项目数据
            onchain_data: 链上数据

        Returns:
            业务模式分析字典
        """
        business_model = project_data.get("business_model", {})
        revenue_streams = business_model.get("revenue_streams", [])
        protocol_revenue_30d = onchain_data.get("protocol_revenue_30d", 0)
        tvl = onchain_data.get("tvl", 0)

        # 收入多样性分析
        revenue_diversity = len(revenue_streams)
        if revenue_diversity >= 3:
            revenue_stability = "高"
            revenue_assessment = f"收入来源多样（{revenue_diversity}种），稳定性较高"
        elif revenue_diversity >= 2:
            revenue_stability = "中"
            revenue_assessment = f"收入来源适中（{revenue_diversity}种）"
        else:
            revenue_stability = "低"
            revenue_assessment = f"收入来源单一（{revenue_diversity}种），存在风险"

        # 收入可持续性
        if protocol_revenue_30d > 0 and tvl > 0:
            yield_rate = (protocol_revenue_30d * 365) / tvl * 100  # 年化收益率
            if yield_rate >= 20:
                sustainability = "优秀"
                sustainability_assessment = f"协议年化收益率{yield_rate:.1f}%很高，收入可持续性强"
            elif yield_rate >= 10:
                sustainability = "良好"
                sustainability_assessment = f"协议年化收益率{yield_rate:.1f}%适中"
            elif yield_rate >= 5:
                sustainability = "一般"
                sustainability_assessment = f"协议年化收益率{yield_rate:.1f}%较低"
            else:
                sustainability = "待观察"
                sustainability_assessment = f"协议年化收益率{yield_rate:.1f}%很低，需关注收入来源"
        else:
            sustainability = "数据不足"
            sustainability_assessment = "协议收入数据不足"
            yield_rate = 0

        # 用户获取成本分析
        user_acquisition = business_model.get("user_acquisition_cost", 0)
        ltv_cac_ratio = business_model.get("ltv_cac_ratio", 0)

        if ltv_cac_ratio >= 3:
            unit_economics = "优秀"
            economics_assessment = f"LTV/CAC比率{ltv_cac_ratio:.1f}很高，单位经济性良好"
        elif ltv_cac_ratio >= 1.5:
            unit_economics = "良好"
            economics_assessment = f"LTV/CAC比率{ltv_cac_ratio:.1f}适中"
        else:
            unit_economics = "待观察"
            economics_assessment = "单位经济性数据不足或不理想"

        return {
            "revenue_streams": revenue_streams,
            "revenue_diversity": revenue_diversity,
            "revenue_stability": revenue_stability,
            "revenue_assessment": revenue_assessment,
            "protocol_revenue_30d": protocol_revenue_30d,
            "yield_rate_annual": round(yield_rate, 2),
            "sustainability": sustainability,
            "sustainability_assessment": sustainability_assessment,
            "unit_economics": unit_economics,
            "economics_assessment": economics_assessment,
            "ltv_cac_ratio": ltv_cac_ratio,
        }

    def _analyze_competitive_advantage(self, project_data: Dict, market_data: Dict) -> Dict:
        """
        分析竞争优势

        Args:
            project_data: 项目数据
            market_data: 市场数据

        Returns:
            竞争优势分析字典
        """
        competitive_advantages = project_data.get("competitive_advantages", [])
        market_position = project_data.get("market_position", {})
        moat_strength = market_position.get("moat_strength", "弱")

        # 技术优势分析
        tech_advantages = [adv for adv in competitive_advantages if adv.get("type") == "技术"]
        network_advantages = [adv for adv in competitive_advantages if adv.get("type") == "网络效应"]
        brand_advantages = [adv for adv in competitive_advantages if adv.get("type") == "品牌"]

        # 综合评分
        advantage_score = len(competitive_advantages)
        if advantage_score >= 5:
            competitive_strength = "强"
            competitive_assessment = f"拥有{advantage_score}项核心竞争优势，竞争力很强"
        elif advantage_score >= 3:
            competitive_strength = "中等"
            competitive_assessment = f"拥有{advantage_score}项竞争优势，竞争力一般"
        else:
            competitive_strength = "弱"
            competitive_assessment = "竞争优势不明显，需要加强差异化"

        # 市场份额分析
        market_share = market_position.get("market_share", 0)
        market_rank = market_position.get("market_rank", 0)

        if market_rank <= 3:
            market_dominance = "领导者"
            dominance_assessment = f"市场排名第{market_rank}位，具有市场主导地位"
        elif market_rank <= 10:
            market_dominance = "挑战者"
            dominance_assessment = f"市场排名第{market_rank}位，是有力挑战者"
        elif market_rank <= 50:
            market_dominance = "跟随者"
            dominance_assessment = f"市场排名第{market_rank}位，属于跟随者"
        else:
            market_dominance = "边缘参与者"
            dominance_assessment = "市场地位较低"

        return {
            "competitive_advantages": competitive_advantages[:5],  # 最多显示5个
            "advantage_count": advantage_score,
            "competitive_strength": competitive_strength,
            "competitive_assessment": competitive_assessment,
            "market_share": market_share,
            "market_rank": market_rank,
            "market_dominance": market_dominance,
            "dominance_assessment": dominance_assessment,
            "moat_strength": moat_strength,
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

    def _format_prompt(
        self,
        aggregated_data: Dict,
        supply_structure: Dict,
        unlock_schedule: Dict,
        inflation_model: Dict,
        team_investors: Dict,
        business_model: Dict,
        competitive_advantage: Dict,
        value_capture: Dict
    ) -> str:
        """
        格式化 prompt

        Args:
            aggregated_data: 聚合数据
            supply_structure: 供应结构分析
            unlock_schedule: 解锁时间表分析
            inflation_model: 通胀模型分析
            team_investors: 团队和投资者分析
            business_model: 业务模式分析
            competitive_advantage: 竞争优势分析
            value_capture: 价值捕获分析

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

        # 格式化新增分析数据
        team_info = f"团队规模: {team_investors.get('team_size', 0)}人, 质量: {team_investors.get('team_quality', '未知')}"
        investor_info = f"投资者: {team_investors.get('investor_count', 0)}家, 质量: {team_investors.get('investor_quality', '未知')}"

        business_info = f"收入来源: {business_model.get('revenue_diversity', 0)}种, 稳定性: {business_model.get('revenue_stability', '未知')}"

        competitive_info = f"竞争优势: {competitive_advantage.get('advantage_count', 0)}项, 强度: {competitive_advantage.get('competitive_strength', '未知')}"

        inflation_info = f"通胀率: {inflation_model.get('inflation_rate_annual', 0)}%, 压力: {inflation_model.get('inflation_pressure', '未知')}"

        # 填充模板
        prompt = self.user_prompt_template.format(
            symbol=symbol,
            total_supply=supply_structure.get("total_supply", 0),
            circulating_supply=supply_structure.get("circulating_supply", 0),
            circulation_rate=supply_structure.get("circulation_rate", 0),
            max_supply=supply_structure.get("max_supply", "无上限"),
            allocation_data=self._format_allocation_data(supply_structure.get("allocation", {})),
            unlock_schedule=self._format_unlock_schedule(unlock_schedule.get("upcoming_unlocks", [])),
            value_capture_mechanisms=self._format_value_capture(value_capture.get("mechanisms", [])),
            market_cap=market_data.get("market_cap", 0),
            fdv=market_data.get("fdv", market_data.get("market_cap", 0)),
            protocol_revenue_30d=business_model.get("protocol_revenue_30d", 0),
            buyback_burn_30d=0,  # 暂时设为0，需要从onchain_data获取
            # 新增的分析维度
            team_info=team_info,
            investor_info=investor_info,
            business_info=business_info,
            competitive_info=competitive_info,
            inflation_info=inflation_info,
            unlock_pressure=unlock_schedule.get("unlock_pressure", "未知"),
            revenue_sustainability=business_model.get("sustainability", "未知"),
            market_dominance=competitive_advantage.get("market_dominance", "未知"),
        )

        return prompt

    async def analyze(self, aggregated_data: Dict) -> AnalyzerOutput:
        """
        执行代币经济学分析

        Args:
            aggregated_data: 聚合数据

        Returns:
            AnalyzerOutput: 包含代币经济学分析数据、元数据和可视化提示
        """
        start_time = time.time()
        symbol = aggregated_data.get("symbol", "Unknown")

        try:
            # 提取数据
            tokenomics_data = aggregated_data.get("tokenomics", {})
            market_data = aggregated_data.get("market_data", {})
            project_data = aggregated_data.get("project_info", {})
            onchain_data = aggregated_data.get("onchain_data", {})

            # 执行各项分析
            supply_structure = self._analyze_supply_structure(tokenomics_data)
            unlock_schedule = self._analyze_unlock_schedule(tokenomics_data, supply_structure.get("circulating_supply", 0))
            inflation_model = self._analyze_inflation_model(tokenomics_data, market_data)
            team_investors = self._analyze_team_and_investors(project_data)
            business_model = self._analyze_business_model(project_data, onchain_data)
            competitive_advantage = self._analyze_competitive_advantage(project_data, market_data)
            value_capture = self._analyze_value_capture(tokenomics_data)

            # 格式化 prompt
            user_prompt = self._format_prompt(
                aggregated_data,
                supply_structure,
                unlock_schedule,
                inflation_model,
                team_investors,
                business_model,
                competitive_advantage,
                value_capture
            )

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
                analyzer_name="TokenomicsAnalyzer",
                model_used=model_used,
                fallback_used=fallback_used,
                generation_time_ms=generation_time_ms,
                confidence=result.get("tokenomics_health_score", {}).get("confidence"),
                data_sources=["CoinGecko", "TokenTerminal"],
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

        if "inflation_model" not in output:
            output["inflation_model"] = {
                "inflation_rate_annual": 0,
                "new_issuance_annual": 0,
                "staking_rewards_annual": 0,
                "inflation_pressure": "低",
                "inflation_assessment": "数据不足",
                "has_max_supply": False,
                "supply_limit": "无上限"
            }

        if "team_and_investors" not in output:
            output["team_and_investors"] = {
                "team_size": 0,
                "avg_team_experience": 0,
                "notable_team_members": [],
                "team_quality": "待观察",
                "team_assessment": "数据不足",
                "investor_count": 0,
                "notable_investors": [],
                "investor_quality": "待观察",
                "investor_assessment": "数据不足",
                "advisor_count": 0
            }

        if "business_model" not in output:
            output["business_model"] = {
                "revenue_streams": [],
                "revenue_diversity": 0,
                "revenue_stability": "低",
                "revenue_assessment": "数据不足",
                "protocol_revenue_30d": 0,
                "yield_rate_annual": 0,
                "sustainability": "数据不足",
                "sustainability_assessment": "数据不足",
                "unit_economics": "待观察",
                "economics_assessment": "数据不足",
                "ltv_cac_ratio": 0
            }

        if "competitive_advantage" not in output:
            output["competitive_advantage"] = {
                "competitive_advantages": [],
                "advantage_count": 0,
                "competitive_strength": "弱",
                "competitive_assessment": "数据不足",
                "market_share": 0,
                "market_rank": 0,
                "market_dominance": "边缘参与者",
                "dominance_assessment": "数据不足",
                "moat_strength": "弱"
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
            analyzer_name="TokenomicsAnalyzer",
            error_msg=f"代币经济学分析失败: {error_message}",
            model_used=model_used,
        )


# 创建全局单例
tokenomics_analyzer = TokenomicsAnalyzer()
