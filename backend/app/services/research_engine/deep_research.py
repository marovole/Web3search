"""
Deep Research 引擎
生成15-30秒的深度研究报告
"""
import asyncio
from typing import Dict, Any, Optional, Callable, Awaitable
from datetime import datetime

from app.services.llm import llm_client, ModelConfig
from app.services.data_aggregator import data_aggregator
from app.services.prompt_manager import prompt_manager


class DeepResearchEngine:
    """
    Deep Research 引擎
    生成全面深入的加密货币项目分析报告
    """

    def __init__(self):
        """初始化Deep Research引擎"""
        self.llm_client = llm_client
        self.data_aggregator = data_aggregator
        self.prompt_manager = prompt_manager

    async def research(
        self,
        query: str,
        symbol: Optional[str] = None,
        progress_callback: Optional[Callable[[str, int], Awaitable[None]]] = None,
    ) -> Dict[str, Any]:
        """
        执行深度研究（任务 8.2 - 添加进度提示）

        Args:
            query: 用户查询
            symbol: 币种符号（可选，会从query中提取）
            progress_callback: 进度回调函数，接收(message: str, progress: int)

        Returns:
            Dict: 研究报告数据
        """
        start_time = datetime.utcnow()

        # 提取币种符号
        if not symbol:
            symbol = self._extract_symbol(query)

        print(f"🔍 开始深度研究: {symbol}")

        # 发送进度：开始
        if progress_callback:
            await progress_callback("🔍 开始深度研究分析...", 0)

        # 步骤1: 聚合数据（并行获取）
        print("  📊 采集数据...")
        if progress_callback:
            await progress_callback("📊 正在收集市场数据、链上数据和社交媒体数据...", 25)

        aggregated_data = await self.data_aggregator.aggregate_project_data(symbol)

        if "error" in aggregated_data:
            return {
                "error": aggregated_data["error"],
                "symbol": symbol,
            }

        # 步骤2: 格式化数据为LLM可读格式
        formatted_data = self.data_aggregator.format_for_llm(aggregated_data)

        # 步骤3: 三阶段分析
        print("  🤖 生成分析...")
        if progress_callback:
            await progress_callback("🤖 正在进行深度分析（生成摘要、技术分析、市场分析等）...", 50)

        # 阶段1: 生成TL;DR（快速模型）
        tldr = await self._generate_tldr(query, formatted_data)

        # 阶段2: 六维度分析（并行生成）
        sections = await self._generate_sections(query, formatted_data, aggregated_data)

        # 发送进度：分析完成，生成报告
        if progress_callback:
            await progress_callback("📝 正在生成研究报告和投资建议...", 75)

        # 阶段3: 生成结论和建议
        conclusion = await self._generate_conclusion(
            query,
            tldr,
            sections,
            formatted_data,
        )

        # 组装完整报告
        end_time = datetime.utcnow()
        generation_time = (end_time - start_time).total_seconds()

        report = {
            "symbol": symbol,
            "query": query,
            "tldr": tldr,
            "sections": sections,
            "conclusion": conclusion,
            "data_sources": [
                "CoinGecko",
                "Etherscan/BSCScan",
                "Twitter",
                "Reddit",
                "CryptoPanic",
            ],
            "models_used": {
                "tldr": ModelConfig.DEEP_RESEARCH_SUMMARY,
                "sections": ModelConfig.DEEP_RESEARCH_ANALYSIS,
                "conclusion": ModelConfig.DEEP_RESEARCH_ANALYSIS,
            },
            "generation_time": generation_time,
            "timestamp": datetime.utcnow().isoformat(),
        }

        print(f"✅ 研究完成，耗时 {generation_time:.2f} 秒")

        # 发送进度：完成
        if progress_callback:
            await progress_callback(f"✅ 研究报告生成完成！（耗时 {generation_time:.1f} 秒）", 100)

        return report

    def _extract_symbol(self, query: str) -> str:
        """从查询中提取币种符号"""
        # 简单实现，与QuickChat相同
        common_symbols = {
            "比特币": "BTC",
            "以太坊": "ETH",
            "币安币": "BNB",
        }

        query_lower = query.lower()
        for name, symbol in common_symbols.items():
            if name in query_lower:
                return symbol

        # 检查大写符号
        words = query.split()
        for word in words:
            word_upper = word.upper()
            if len(word_upper) >= 2 and len(word_upper) <= 10:
                if word_upper in ["BTC", "ETH", "BNB", "XRP", "DOGE", "SOL"]:
                    return word_upper

        return "BTC"

    async def _generate_tldr(
        self,
        query: str,
        formatted_data: Dict[str, str],
    ) -> str:
        """
        生成TL;DR摘要

        Args:
            query: 用户查询
            formatted_data: 格式化数据

        Returns:
            str: TL;DR摘要
        """
        prompt = self.prompt_manager.get_tldr_prompt(
            query=query,
            market_data=formatted_data.get("market_data", ""),
            project_info=formatted_data.get("project_info", ""),
            social_data=formatted_data.get("social_data", ""),
        )

        # 使用高质量模型生成摘要
        summary = await self.llm_client.deep_research_summary(
            context=prompt,
            query=query,
        )

        return summary

    async def _generate_sections(
        self,
        query: str,
        formatted_data: Dict[str, str],
        raw_data: Dict[str, Any],
    ) -> Dict[str, str]:
        """
        并行生成六个分析维度的内容

        Args:
            query: 用户查询
            formatted_data: 格式化数据
            raw_data: 原始数据

        Returns:
            Dict[str, str]: 各维度分析内容
        """
        # 并行生成所有维度
        overview, technical, market, community, risk, competitor = await asyncio.gather(
            self._generate_overview(query, formatted_data),
            self._generate_technical_analysis(query, formatted_data, raw_data),
            self._generate_market_analysis(query, formatted_data),
            self._generate_community_analysis(query, formatted_data),
            self._generate_risk_assessment(query, formatted_data, raw_data),
            self._generate_competitor_analysis(query, formatted_data, raw_data),
            return_exceptions=True,
        )

        # 处理异常结果
        if isinstance(overview, Exception):
            overview = f"⚠️ 生成失败: {str(overview)}"
        if isinstance(technical, Exception):
            technical = f"⚠️ 生成失败: {str(technical)}"
        if isinstance(market, Exception):
            market = f"⚠️ 生成失败: {str(market)}"
        if isinstance(community, Exception):
            community = f"⚠️ 生成失败: {str(community)}"
        if isinstance(risk, Exception):
            risk = f"⚠️ 生成失败: {str(risk)}"
        if isinstance(competitor, Exception):
            competitor = f"⚠️ 生成失败: {str(competitor)}"

        return {
            "overview": overview,
            "technical_analysis": technical,
            "market_analysis": market,
            "community_analysis": community,
            "risk_assessment": risk,
            "competitor_analysis": competitor,
        }

    async def _generate_overview(
        self,
        query: str,
        formatted_data: Dict[str, str],
    ) -> str:
        """生成项目概览"""
        prompt = self.prompt_manager.get_overview_prompt(
            query=query,
            project_info=formatted_data.get("project_info", ""),
            market_data=formatted_data.get("market_data", ""),
        )

        return await self.llm_client.deep_research_analysis(
            context=prompt,
            query=query,
            analysis_type="fundamental",
        )

    async def _generate_technical_analysis(
        self,
        query: str,
        formatted_data: Dict[str, str],
        raw_data: Dict[str, Any],
    ) -> str:
        """生成技术分析"""
        onchain_data = raw_data.get("onchain_data", {})

        # 检查合约验证状态
        contract_verified = False
        for chain, data in onchain_data.items():
            if isinstance(data, dict) and data.get("is_verified"):
                contract_verified = True
                break

        prompt = self.prompt_manager.get_technical_analysis_prompt(
            query=query,
            project_info=formatted_data.get("project_info", ""),
            onchain_data=formatted_data.get("onchain_data", ""),
            contract_verified=contract_verified,
        )

        return await self.llm_client.deep_research_analysis(
            context=prompt,
            query=query,
            analysis_type="technical",
        )

    async def _generate_market_analysis(
        self,
        query: str,
        formatted_data: Dict[str, str],
    ) -> str:
        """生成市场分析"""
        prompt = self.prompt_manager.get_market_analysis_prompt(
            query=query,
            market_data=formatted_data.get("market_data", ""),
            historical_data="",  # 可以添加图表数据
        )

        return await self.llm_client.deep_research_analysis(
            context=prompt,
            query=query,
            analysis_type="market",
        )

    async def _generate_community_analysis(
        self,
        query: str,
        formatted_data: Dict[str, str],
    ) -> str:
        """生成社区分析"""
        prompt = self.prompt_manager.get_community_analysis_prompt(
            query=query,
            twitter_data=formatted_data.get("social_data", ""),
            reddit_data=formatted_data.get("social_data", ""),
            news_data=formatted_data.get("news_data", ""),
        )

        return await self.llm_client.deep_research_analysis(
            context=prompt,
            query=query,
            analysis_type="community",
        )

    async def _generate_risk_assessment(
        self,
        query: str,
        formatted_data: Dict[str, str],
        raw_data: Dict[str, Any],
    ) -> str:
        """生成风险评估"""
        prompt = self.prompt_manager.get_risk_assessment_prompt(
            query=query,
            project_info=formatted_data.get("project_info", ""),
            market_data=formatted_data.get("market_data", ""),
            onchain_data=formatted_data.get("onchain_data", ""),
            news_data=formatted_data.get("news_data", ""),
        )

        return await self.llm_client.deep_research_analysis(
            context=prompt,
            query=query,
            analysis_type="risk",
        )

    async def _generate_competitor_analysis(
        self,
        query: str,
        formatted_data: Dict[str, str],
        raw_data: Dict[str, Any],
    ) -> str:
        """生成竞品分析"""
        # 获取项目类别
        project_info = raw_data.get("project_info", {})
        categories = project_info.get("categories", [])

        # 简单实现：使用类别信息
        category_str = ", ".join(categories) if categories else "加密货币"

        prompt = self.prompt_manager.get_competitor_analysis_prompt(
            query=query,
            target_project=formatted_data.get("project_info", ""),
            competitors=f"类别: {category_str}",
        )

        return await self.llm_client.deep_research_analysis(
            context=prompt,
            query=query,
            analysis_type="competitor",
        )

    async def _generate_conclusion(
        self,
        query: str,
        tldr: str,
        sections: Dict[str, str],
        formatted_data: Dict[str, str],
    ) -> str:
        """
        生成结论和投资建议

        Args:
            query: 用户查询
            tldr: TL;DR摘要
            sections: 各维度分析
            formatted_data: 格式化数据

        Returns:
            str: 结论内容
        """
        # 构建上下文
        context = f"""
基于以下分析，总结项目的关键发现并给出投资建议：

TL;DR: {tldr}

市场数据: {formatted_data.get('market_data', '')}

风险评估: {sections.get('risk_assessment', '')[:500]}

要求：
- 列出3-5个关键发现
- 给出投资建议（保守/中性/积极）
- 说明理由
- 保持客观和谨慎
"""

        return await self.llm_client.deep_research_analysis(
            context=context,
            query=query,
            analysis_type="risk",
        )


# ================================
# 全局实例
# ================================

deep_research_engine = DeepResearchEngine()
