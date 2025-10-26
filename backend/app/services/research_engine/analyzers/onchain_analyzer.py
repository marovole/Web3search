"""
链上数据分析器
分析用户活动、协议基本面、持币分布等链上指标
"""
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
import yaml

from app.services.llm import llm_client, ModelConfig
from app.core.config import settings


class OnchainAnalyzer:
    """
    链上数据分析器
    参考：openspec/changes/add-crypto-ai-search-platform/specs/ai-analysis/spec.md
    Scenario: 链上数据分析（基本面）
    """

    def __init__(self):
        """初始化链上数据分析器"""
        self.llm_client = llm_client
        self._load_prompts()

    def _load_prompts(self):
        """加载提示词模板"""
        prompts_dir = Path(settings.BASE_DIR) / "prompts" / "deep_research"
        onchain_yaml_path = prompts_dir / "onchain.yaml"

        if not onchain_yaml_path.exists():
            raise FileNotFoundError(f"链上数据提示词文件不存在: {onchain_yaml_path}")

        with open(onchain_yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        self.system_prompt = data.get("system_prompt", "")
        self.user_prompt_template = data.get("user_prompt_template", "")
        self.model_config = data.get("model_config", {})
        self.output_validation = data.get("output_validation", {})

    async def analyze(
        self,
        aggregated_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        链上数据分析

        Args:
            aggregated_data: 聚合后的项目数据（来自DataAggregator）

        Returns:
            Dict: 链上数据分析结果
        """
        # 提取必要数据
        symbol = aggregated_data.get("symbol", "Unknown")
        project_info = aggregated_data.get("project_info", {})
        market_data = aggregated_data.get("market_data", {})
        onchain_data = aggregated_data.get("onchain_data", {})

        # 分析各个维度
        user_activity = self._analyze_user_activity(onchain_data)
        protocol_fundamentals = self._analyze_protocol_fundamentals(onchain_data, market_data)
        token_distribution = self._analyze_token_distribution(onchain_data)

        # 格式化提示词
        user_prompt = self._format_prompt(
            symbol=symbol,
            project_name=project_info.get("name", symbol),
            current_price=market_data.get("current_price", "N/A"),
            market_cap=market_data.get("market_cap", "N/A"),
            market_cap_rank=market_data.get("market_cap_rank", "N/A"),
            user_activity=user_activity,
            protocol_fundamentals=protocol_fundamentals,
            token_distribution=token_distribution,
        )

        # 调用LLM生成（使用qwen3-235b）
        try:
            result = await self._call_llm(user_prompt, use_fallback=False)
        except Exception as e:
            print(f"⚠️ 主模型调用失败: {e}，尝试fallback模型")
            try:
                result = await self._call_llm(user_prompt, use_fallback=True)
            except Exception as fallback_error:
                print(f"❌ Fallback模型也失败: {fallback_error}")
                return self._create_error_response(symbol, str(fallback_error))

        # 验证输出格式
        if not self._validate_output(result):
            print("⚠️ 输出格式验证失败，使用默认值补全")
            result = self._fix_invalid_output(result, symbol)

        return result

    def _analyze_user_activity(self, onchain_data: Dict) -> Dict:
        """
        分析用户活动指标

        Args:
            onchain_data: 链上数据

        Returns:
            Dict: 用户活动指标
        """
        # 提取活跃地址数据
        active_addresses_24h = onchain_data.get("active_addresses", 0)
        active_addresses_7d = onchain_data.get("active_addresses_7d", active_addresses_24h * 5)
        active_addresses_30d = onchain_data.get("active_addresses_30d", active_addresses_24h * 15)

        # 判断趋势
        growth_7d = onchain_data.get("active_addresses_growth_7d", 0)
        if growth_7d > 10:
            trend = "上升"
        elif growth_7d < -10:
            trend = "下降"
        else:
            trend = "稳定"

        # 新用户数据
        total_unique_addresses = onchain_data.get("total_unique_addresses", 0)
        new_addresses_30d = onchain_data.get("new_addresses_30d", 0)
        new_user_growth_rate = (
            (new_addresses_30d / total_unique_addresses * 100)
            if total_unique_addresses > 0
            else 0
        )

        # 交易活动
        transactions_24h = onchain_data.get("transactions_24h", 0)
        avg_transactions_7d = onchain_data.get("avg_transactions_7d", transactions_24h)
        total_transactions_30d = onchain_data.get("total_transactions_30d", transactions_24h * 30)

        tx_growth = onchain_data.get("transaction_growth_30d", 0)
        if tx_growth > 10:
            tx_trend = "上升"
        elif tx_growth < -10:
            tx_trend = "下降"
        else:
            tx_trend = "稳定"

        return {
            "active_addresses_24h": active_addresses_24h,
            "active_addresses_7d": active_addresses_7d,
            "active_addresses_30d": active_addresses_30d,
            "active_addresses_trend": trend,
            "total_unique_addresses": total_unique_addresses,
            "new_addresses_30d": new_addresses_30d,
            "new_user_growth_rate": round(new_user_growth_rate, 2),
            "transactions_24h": transactions_24h,
            "avg_transactions_7d": avg_transactions_7d,
            "total_transactions_30d": total_transactions_30d,
            "transaction_trend": tx_trend,
        }

    def _analyze_protocol_fundamentals(self, onchain_data: Dict, market_data: Dict) -> Dict:
        """
        分析协议基本面

        Args:
            onchain_data: 链上数据
            market_data: 市场数据

        Returns:
            Dict: 协议基本面指标
        """
        # TVL数据
        current_tvl = onchain_data.get("tvl", 0)
        tvl_change_30d = onchain_data.get("tvl_change_30d", 0)
        tvl_change_90d = onchain_data.get("tvl_change_90d", 0)
        tvl_rank = onchain_data.get("tvl_rank", 999)

        # 协议收入
        protocol_fees_30d = onchain_data.get("protocol_fees_30d", 0)
        protocol_revenue_30d = onchain_data.get("protocol_revenue_30d", protocol_fees_30d * 0.7)
        annualized_revenue = protocol_revenue_30d * 12
        revenue_growth_rate = onchain_data.get("revenue_growth_rate", 0)

        # 收入分配
        staker_share = onchain_data.get("staker_share", 70)
        treasury_buyback_share = onchain_data.get("treasury_buyback_share", 20)
        burn_share = onchain_data.get("burn_share", 10)
        team_share = onchain_data.get("team_share", 0)

        # 回购/燃烧
        buyback_amount_30d = onchain_data.get("buyback_amount_30d", 0)
        burn_amount_30d = onchain_data.get("burn_amount_30d", 0)
        supply_impact = onchain_data.get("supply_impact", 0)

        # 估值指标
        market_cap = market_data.get("market_cap", 0)
        mcap_to_tvl = (market_cap / current_tvl) if current_tvl > 0 else 0
        pe_ratio = (market_cap / annualized_revenue) if annualized_revenue > 0 else 0

        return {
            "current_tvl": current_tvl,
            "tvl_change_30d": tvl_change_30d,
            "tvl_change_90d": tvl_change_90d,
            "tvl_rank": tvl_rank,
            "protocol_fees_30d": protocol_fees_30d,
            "protocol_revenue_30d": protocol_revenue_30d,
            "annualized_revenue": annualized_revenue,
            "revenue_growth_rate": revenue_growth_rate,
            "staker_share": staker_share,
            "treasury_buyback_share": treasury_buyback_share,
            "burn_share": burn_share,
            "team_share": team_share,
            "buyback_amount_30d": buyback_amount_30d,
            "burn_amount_30d": burn_amount_30d,
            "supply_impact": supply_impact,
            "market_cap": market_cap,
            "mcap_to_tvl": round(mcap_to_tvl, 2),
            "pe_ratio": round(pe_ratio, 1),
        }

    def _analyze_token_distribution(self, onchain_data: Dict) -> Dict:
        """
        分析持币分布

        Args:
            onchain_data: 链上数据

        Returns:
            Dict: 持币分布指标
        """
        # 持币集中度
        top_10_holders_pct = onchain_data.get("top_10_holders_pct", 0)
        top_100_holders_pct = onchain_data.get("top_100_holders_pct", 0)
        gini_coefficient = onchain_data.get("gini_coefficient", 0.7)

        # 判断集中度评级
        if top_10_holders_pct > 50:
            concentration_rating = "高集中度"
        elif top_10_holders_pct > 30:
            concentration_rating = "中等集中度"
        else:
            concentration_rating = "低集中度"

        # 鲸鱼活动
        whale_count = onchain_data.get("whale_count", 0)
        whale_holdings_pct = onchain_data.get("whale_holdings_pct", 0)
        whale_net_flow_30d = onchain_data.get("whale_net_flow_30d", 0)

        # 判断鲸鱼活动趋势
        if whale_net_flow_30d > 0:
            whale_activity_trend = "积累"
        elif whale_net_flow_30d < 0:
            whale_activity_trend = "分销"
        else:
            whale_activity_trend = "稳定"

        # 机构持币
        institutional_addresses = onchain_data.get("institutional_addresses", 0)
        institutional_holdings = onchain_data.get("institutional_holdings", 0)
        institutional_holdings_pct = onchain_data.get("institutional_holdings_pct", 0)
        major_institutions = onchain_data.get("major_institutions", [])
        if isinstance(major_institutions, list):
            major_institutions_str = ", ".join(major_institutions[:5])
        else:
            major_institutions_str = str(major_institutions)

        # 交易所余额
        exchange_balance = onchain_data.get("exchange_balance", 0)
        exchange_balance_pct = onchain_data.get("exchange_balance_pct", 0)
        exchange_net_flow_30d = onchain_data.get("exchange_net_flow_30d", 0)

        return {
            "top_10_holders_pct": top_10_holders_pct,
            "top_100_holders_pct": top_100_holders_pct,
            "gini_coefficient": gini_coefficient,
            "concentration_rating": concentration_rating,
            "whale_count": whale_count,
            "whale_holdings_pct": whale_holdings_pct,
            "whale_net_flow_30d": whale_net_flow_30d,
            "whale_activity_trend": whale_activity_trend,
            "institutional_addresses": institutional_addresses,
            "institutional_holdings": institutional_holdings,
            "institutional_holdings_pct": institutional_holdings_pct,
            "major_institutions": major_institutions_str,
            "exchange_balance": exchange_balance,
            "exchange_balance_pct": exchange_balance_pct,
            "exchange_net_flow_30d": exchange_net_flow_30d,
        }

    def _format_prompt(
        self,
        symbol: str,
        project_name: str,
        current_price: Any,
        market_cap: Any,
        market_cap_rank: Any,
        user_activity: Dict,
        protocol_fundamentals: Dict,
        token_distribution: Dict,
    ) -> str:
        """格式化用户提示词"""
        # 替换模板占位符
        prompt = self.user_prompt_template.format(
            symbol=symbol,
            project_name=project_name,
            current_price=current_price,
            market_cap=market_cap,
            market_cap_rank=market_cap_rank,
            # 用户活动
            active_addresses_24h=user_activity.get("active_addresses_24h", "N/A"),
            active_addresses_7d=user_activity.get("active_addresses_7d", "N/A"),
            active_addresses_30d=user_activity.get("active_addresses_30d", "N/A"),
            active_addresses_trend=user_activity.get("active_addresses_trend", "N/A"),
            total_unique_addresses=user_activity.get("total_unique_addresses", "N/A"),
            new_addresses_30d=user_activity.get("new_addresses_30d", "N/A"),
            new_user_growth_rate=user_activity.get("new_user_growth_rate", "N/A"),
            transactions_24h=user_activity.get("transactions_24h", "N/A"),
            avg_transactions_7d=user_activity.get("avg_transactions_7d", "N/A"),
            total_transactions_30d=user_activity.get("total_transactions_30d", "N/A"),
            transaction_trend=user_activity.get("transaction_trend", "N/A"),
            # 协议基本面
            current_tvl=protocol_fundamentals.get("current_tvl", "N/A"),
            tvl_change_30d=protocol_fundamentals.get("tvl_change_30d", "N/A"),
            tvl_change_90d=protocol_fundamentals.get("tvl_change_90d", "N/A"),
            tvl_rank=protocol_fundamentals.get("tvl_rank", "N/A"),
            protocol_fees_30d=protocol_fundamentals.get("protocol_fees_30d", "N/A"),
            protocol_revenue_30d=protocol_fundamentals.get("protocol_revenue_30d", "N/A"),
            annualized_revenue=protocol_fundamentals.get("annualized_revenue", "N/A"),
            revenue_growth_rate=protocol_fundamentals.get("revenue_growth_rate", "N/A"),
            staker_share=protocol_fundamentals.get("staker_share", "N/A"),
            treasury_buyback_share=protocol_fundamentals.get("treasury_buyback_share", "N/A"),
            burn_share=protocol_fundamentals.get("burn_share", "N/A"),
            team_share=protocol_fundamentals.get("team_share", "N/A"),
            buyback_amount_30d=protocol_fundamentals.get("buyback_amount_30d", "N/A"),
            burn_amount_30d=protocol_fundamentals.get("burn_amount_30d", "N/A"),
            supply_impact=protocol_fundamentals.get("supply_impact", "N/A"),
            # 持币分布
            top_10_holders_pct=token_distribution.get("top_10_holders_pct", "N/A"),
            top_100_holders_pct=token_distribution.get("top_100_holders_pct", "N/A"),
            gini_coefficient=token_distribution.get("gini_coefficient", "N/A"),
            concentration_rating=token_distribution.get("concentration_rating", "N/A"),
            whale_count=token_distribution.get("whale_count", "N/A"),
            whale_holdings_pct=token_distribution.get("whale_holdings_pct", "N/A"),
            whale_net_flow_30d=token_distribution.get("whale_net_flow_30d", "N/A"),
            whale_activity_trend=token_distribution.get("whale_activity_trend", "N/A"),
            institutional_addresses=token_distribution.get("institutional_addresses", "N/A"),
            institutional_holdings=token_distribution.get("institutional_holdings", "N/A"),
            institutional_holdings_pct=token_distribution.get("institutional_holdings_pct", "N/A"),
            major_institutions=token_distribution.get("major_institutions", "N/A"),
            exchange_balance=token_distribution.get("exchange_balance", "N/A"),
            exchange_balance_pct=token_distribution.get("exchange_balance_pct", "N/A"),
            exchange_net_flow_30d=token_distribution.get("exchange_net_flow_30d", "N/A"),
        )

        return prompt

    async def _call_llm(self, user_prompt: str, use_fallback: bool = False) -> Dict[str, Any]:
        """
        调用LLM生成链上数据分析

        Args:
            user_prompt: 用户提示词
            use_fallback: 是否使用fallback模型

        Returns:
            Dict: 解析后的JSON响应
        """
        model = (
            self.model_config.get("fallback_model", ModelConfig.QUICK_CHAT)
            if use_fallback
            else self.model_config.get("primary_model", ModelConfig.DEEP_RESEARCH_SUMMARY)
        )

        temperature = self.model_config.get("temperature", 0.4)
        max_tokens = self.model_config.get("max_tokens", 2000)

        # 调用LLM
        response = await self.llm_client.chat_completion(
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
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
        验证输出格式

        Args:
            result: LLM生成的结果

        Returns:
            bool: 是否符合格式要求
        """
        required_fields = self.output_validation.get("required_fields", [])

        # 检查必填字段
        for field in required_fields:
            if field not in result:
                print(f"❌ 缺少必填字段: {field}")
                return False

        # 验证onchain_health_score
        if "onchain_health_score" in result:
            ohs = result["onchain_health_score"]
            ohs_required = self.output_validation.get("onchain_health_score_structure", {}).get("required_fields", [])
            for field in ohs_required:
                if field not in ohs:
                    print(f"❌ onchain_health_score缺少字段: {field}")
                    return False

            # 验证score范围
            score = ohs.get("score", -1)
            score_range = self.output_validation.get("onchain_health_score_structure", {}).get("score_range", {})
            if not (score_range.get("min", 0) <= score <= score_range.get("max", 100)):
                print(f"❌ onchain_health_score.score超出范围: {score}")
                return False

        return True

    def _fix_invalid_output(self, result: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """
        修复无效输出（补全缺失字段）

        Args:
            result: 原始结果
            symbol: 币种符号

        Returns:
            Dict: 修复后的结果
        """
        from datetime import datetime, timezone

        # 补全user_activity
        if "user_activity" not in result:
            result["user_activity"] = {}

        ua = result["user_activity"]
        ua.setdefault("active_addresses", {"daily": 0, "weekly": 0, "monthly": 0, "trend": "稳定", "growth_rate_30d": "0%", "interpretation": "数据不足"})
        ua.setdefault("new_users", {"new_addresses_30d": 0, "growth_rate": "0%", "interpretation": "数据不足"})
        ua.setdefault("transaction_activity", {"daily_txs": 0, "trend": "稳定", "interpretation": "数据不足"})
        ua.setdefault("overall_narrative", f"{symbol}的用户活动数据不完整。")

        # 补全protocol_fundamentals
        if "protocol_fundamentals" not in result:
            result["protocol_fundamentals"] = {}

        pf = result["protocol_fundamentals"]
        pf.setdefault("tvl", {"current": 0, "change_30d": "0%", "change_90d": "0%", "rank": 999, "interpretation": "数据不足"})
        pf.setdefault("revenue", {"fees_30d": 0, "revenue_30d": 0, "annualized_revenue": 0, "growth_rate": "0%", "interpretation": "数据不足"})
        pf.setdefault("revenue_distribution", {"staker_share": 0, "treasury_buyback": 0, "burn": 0, "model": "N/A", "interpretation": "数据不足"})
        pf.setdefault("valuation_metrics", {"market_cap": 0, "tvl": 0, "mcap_to_tvl": 0, "pe_ratio": 0, "interpretation": "数据不足"})
        pf.setdefault("overall_narrative", f"{symbol}的协议基本面数据不完整。")

        # 补全token_distribution
        if "token_distribution" not in result:
            result["token_distribution"] = {}

        td = result["token_distribution"]
        td.setdefault("concentration", {"top_10_pct": 0, "top_100_pct": 0, "gini_coefficient": 0, "rating": "中等集中度", "interpretation": "数据不足"})
        td.setdefault("whale_activity", {"whale_count": 0, "whale_holdings_pct": 0, "net_flow_30d": "0", "trend": "稳定", "interpretation": "数据不足"})
        td.setdefault("exchange_balance", {"balance_pct": 0, "net_flow_30d": "0", "interpretation": "数据不足"})
        td.setdefault("overall_narrative", f"{symbol}的持币分布数据不完整。")

        # 补全onchain_health_score
        if "onchain_health_score" not in result:
            result["onchain_health_score"] = {}

        ohs = result["onchain_health_score"]
        ohs.setdefault("score", 50)
        ohs.setdefault("rating", "一般")
        ohs.setdefault("strengths", ["数据不足"])
        ohs.setdefault("weaknesses", ["数据不足"])
        ohs.setdefault("outlook", f"{symbol}的链上数据分析不完整，需要更多数据。")

        result.setdefault("data_sources", [])
        result.setdefault("updated_at", datetime.now(timezone.utc).isoformat())

        return result

    def _create_error_response(self, symbol: str, error_msg: str) -> Dict[str, Any]:
        """
        创建错误响应

        Args:
            symbol: 币种符号
            error_msg: 错误信息

        Returns:
            Dict: 错误响应数据
        """
        from datetime import datetime, timezone

        return {
            "user_activity": {
                "active_addresses": {"daily": 0, "weekly": 0, "monthly": 0, "trend": "数据不足", "growth_rate_30d": "N/A", "interpretation": "分析失败"},
                "new_users": {"new_addresses_30d": 0, "growth_rate": "N/A", "interpretation": "分析失败"},
                "transaction_activity": {"daily_txs": 0, "trend": "数据不足", "interpretation": "分析失败"},
                "overall_narrative": f"{symbol}的用户活动分析失败。",
            },
            "protocol_fundamentals": {
                "tvl": {"current": 0, "change_30d": "N/A", "change_90d": "N/A", "rank": 999, "interpretation": "分析失败"},
                "revenue": {"fees_30d": 0, "revenue_30d": 0, "annualized_revenue": 0, "growth_rate": "N/A", "interpretation": "分析失败"},
                "revenue_distribution": {"staker_share": 0, "treasury_buyback": 0, "burn": 0, "model": "N/A", "interpretation": "分析失败"},
                "valuation_metrics": {"market_cap": 0, "tvl": 0, "mcap_to_tvl": 0, "pe_ratio": 0, "interpretation": "分析失败"},
                "overall_narrative": f"{symbol}的协议基本面分析失败。",
            },
            "token_distribution": {
                "concentration": {"top_10_pct": 0, "top_100_pct": 0, "gini_coefficient": 0, "rating": "数据不足", "interpretation": "分析失败"},
                "whale_activity": {"whale_count": 0, "whale_holdings_pct": 0, "net_flow_30d": "0", "trend": "数据不足", "interpretation": "分析失败"},
                "exchange_balance": {"balance_pct": 0, "net_flow_30d": "0", "interpretation": "分析失败"},
                "overall_narrative": f"{symbol}的持币分布分析失败。",
            },
            "onchain_health_score": {
                "score": 30,
                "rating": "差",
                "strengths": [],
                "weaknesses": ["分析失败"],
                "outlook": f"{symbol}的链上数据分析失败: {error_msg}",
            },
            "data_sources": [],
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "error": error_msg,
        }


# 全局单例
onchain_analyzer = OnchainAnalyzer()
