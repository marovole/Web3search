"""
报告生成器
将研究结果格式化为Markdown报告
"""
from typing import Dict, Any, List
from datetime import datetime

from app.services.prompt_manager import prompt_manager
from app.services.report.table_generator import table_generator
from app.services.report.chart_generator import chart_generator


class ReportGenerator:
    """
    报告生成器
    负责将Deep Research结果组装成格式化的Markdown报告
    """

    def __init__(self):
        """初始化报告生成器"""
        self.prompt_manager = prompt_manager
        self.table_generator = table_generator
        self.chart_generator = chart_generator

    def generate_markdown(self, research_result: Dict[str, Any]) -> str:
        """
        生成Markdown格式的报告（增强版，支持表格和图表）

        Args:
            research_result: Deep Research引擎返回的研究结果

        Returns:
            str: Markdown格式的完整报告
        """
        symbol = research_result.get("symbol", "Unknown")
        query = research_result.get("query", "")
        tldr = research_result.get("tldr", "")
        sections = research_result.get("sections", {})
        conclusion = research_result.get("conclusion", "")
        generation_time = research_result.get("generation_time", 0)
        models_used = research_result.get("models_used", {})
        data_sources = research_result.get("data_sources", [])
        timestamp = research_result.get("timestamp", datetime.utcnow().isoformat())

        # 新增：获取analyzer_outputs和visualization_hints
        analyzer_outputs = research_result.get("analyzer_outputs", {})
        visualization_hints = research_result.get("visualization_hints", [])

        # 如果有analyzer_outputs，生成表格和图表
        tables = {}
        charts = {}
        if analyzer_outputs:
            print("  📊 生成表格和图表...")
            tables = self._generate_tables_from_analyzers(analyzer_outputs)
            charts = self._generate_charts_from_analyzers(analyzer_outputs)
            print(f"  ✅ 生成了 {len(tables)} 个表格和 {len(charts)} 个图表")

        # 组装报告
        report_parts = []

        # 标题
        report_parts.append(f"# {symbol} 深度研究报告\n")
        report_parts.append(f"**生成时间**: {timestamp}\n")
        report_parts.append(f"**用户查询**: {query}\n")
        report_parts.append(f"**分析师**: Web3 Search AI\n")
        report_parts.append("\n---\n")

        # TL;DR
        report_parts.append("## 📌 TL;DR\n")
        report_parts.append(f"{tldr}\n")
        report_parts.append("\n---\n")

        # 时间窗分析（新增）
        if sections.get("timeframe"):
            report_parts.append("## ⏰ 时间窗分析\n")
            report_parts.append(f"{sections['timeframe']}\n")
            # 插入价格走势图
            if "price_trend" in charts:
                report_parts.append("\n### 价格走势图\n")
                report_parts.append(charts["price_trend"])
            report_parts.append("\n---\n")

        # 情绪分析（新增）
        if sections.get("sentiment"):
            report_parts.append("## 😊 情绪分析\n")
            report_parts.append(f"{sections['sentiment']}\n")
            # 插入情绪分布图
            if "sentiment_distribution" in charts:
                report_parts.append("\n### 社交媒体提及分布\n")
                report_parts.append(charts["sentiment_distribution"])
            report_parts.append("\n---\n")

        # 技术分析
        if sections.get("technical_analysis"):
            report_parts.append("## 📈 技术分析\n")
            report_parts.append(f"{sections['technical_analysis']}\n")
            # 插入支撑阻力位表格
            if "technical_levels" in tables:
                report_parts.append("\n### 关键价位\n")
                report_parts.append(tables["technical_levels"])
            report_parts.append("\n---\n")

        # 链上分析（新增）
        if sections.get("onchain_analysis"):
            report_parts.append("## ⛓️ 链上分析\n")
            report_parts.append(f"{sections['onchain_analysis']}\n")
            report_parts.append("\n---\n")

        # 竞品分析
        if sections.get("competitor_analysis"):
            report_parts.append("## 🔍 竞品分析\n")
            report_parts.append(f"{sections['competitor_analysis']}\n")
            # 插入竞品对比表
            if "competitor_comparison" in tables:
                report_parts.append("\n### 竞品对比\n")
                report_parts.append(tables["competitor_comparison"])
            # 插入估值倍数表
            if "valuation_multiples" in tables:
                report_parts.append("\n### 估值倍数对比\n")
                report_parts.append(tables["valuation_multiples"])
            # 插入估值对比图
            if "valuation_comparison" in charts:
                report_parts.append("\n### 估值倍数对比图\n")
                report_parts.append(charts["valuation_comparison"])
            report_parts.append("\n---\n")

        # 代币经济学（新增）
        if sections.get("tokenomics"):
            report_parts.append("## 💰 代币经济学\n")
            report_parts.append(f"{sections['tokenomics']}\n")
            # 插入代币解锁时间表
            if "unlock_schedule" in tables:
                report_parts.append("\n### 代币解锁时间表\n")
                report_parts.append(tables["unlock_schedule"])
            report_parts.append("\n---\n")

        # 风险评估
        if sections.get("risk_assessment"):
            report_parts.append("## ⚠️ 风险评估\n")
            report_parts.append(f"{sections['risk_assessment']}\n")
            # 插入风险矩阵表
            if "risk_matrix" in tables:
                report_parts.append("\n### 风险矩阵\n")
                report_parts.append(tables["risk_matrix"])
            # 插入风险热力图
            if "risk_heatmap" in charts:
                report_parts.append("\n### 风险热力图\n")
                report_parts.append(charts["risk_heatmap"])
            report_parts.append("\n---\n")

        # 结论
        report_parts.append("## 🎯 结论与投资建议\n")
        report_parts.append(f"{conclusion}\n")
        # 插入催化剂日历
        if "catalyst_calendar" in tables:
            report_parts.append("\n### 催化剂日历\n")
            report_parts.append(tables["catalyst_calendar"])
        report_parts.append("\n---\n")

        # 免责声明
        disclaimer = self.prompt_manager.get_disclaimer()
        report_parts.append(disclaimer)
        report_parts.append("\n---\n")

        # 报告元数据
        report_parts.append("## 📊 报告元数据\n")
        report_parts.append("\n### 数据来源\n")
        for source in data_sources:
            report_parts.append(f"- {source}\n")

        report_parts.append("\n### 使用模型\n")
        for task, model in models_used.items():
            report_parts.append(f"- **{task}**: {model}\n")

        report_parts.append(f"\n**报告生成耗时**: {generation_time:.2f} 秒\n")

        # 新增：统计信息
        if tables or charts:
            report_parts.append(f"**包含表格**: {len(tables)} 个\n")
            report_parts.append(f"**包含图表**: {len(charts)} 个\n")

        return "".join(report_parts)

    def generate_summary(self, research_result: Dict[str, Any]) -> str:
        """
        生成报告摘要（用于列表显示）

        Args:
            research_result: 研究结果

        Returns:
            str: 摘要文本
        """
        symbol = research_result.get("symbol", "Unknown")
        tldr = research_result.get("tldr", "")

        # 截取TL;DR的前200个字符
        if len(tldr) > 200:
            summary = tldr[:200] + "..."
        else:
            summary = tldr

        return f"**{symbol}**: {summary}"

    def generate_title(self, research_result: Dict[str, Any]) -> str:
        """
        生成报告标题

        Args:
            research_result: 研究结果

        Returns:
            str: 报告标题
        """
        symbol = research_result.get("symbol", "Unknown")
        timestamp = research_result.get("timestamp", "")

        # 格式化时间
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            date_str = dt.strftime("%Y-%m-%d %H:%M")
        except:
            date_str = "未知时间"

        return f"{symbol} 深度研究报告 - {date_str}"

    def calculate_quality_score(self, research_result: Dict[str, Any]) -> int:
        """
        计算报告质量得分（0-100）

        Args:
            research_result: 研究结果

        Returns:
            int: 质量得分
        """
        score = 0

        # 基础分：30分
        score += 30

        # TL;DR质量：10分
        tldr = research_result.get("tldr", "")
        if len(tldr) > 50:
            score += 10

        # 章节完整性：每个章节10分，最多60分
        sections = research_result.get("sections", {})
        section_count = sum(1 for v in sections.values() if v and not v.startswith("⚠️"))
        score += min(section_count * 10, 60)

        return min(score, 100)

    def _generate_tables_from_analyzers(self, analyzer_outputs: Dict[str, Dict[str, Any]]) -> Dict[str, str]:
        """
        从analyzer输出中自动生成表格

        Args:
            analyzer_outputs: 所有analyzer的输出

        Returns:
            Dict[str, str]: {analyzer_key: markdown_table}
        """
        tables = {}

        try:
            # 竞品分析表格
            if "competitor" in analyzer_outputs:
                competitor_data = analyzer_outputs["competitor"].get("data", {})
                if not competitor_data.get("error"):
                    # 竞品对比表
                    tables["competitor_comparison"] = self.table_generator.generate_competitor_table(competitor_data)
                    # 估值倍数表
                    tables["valuation_multiples"] = self.table_generator.generate_valuation_table(competitor_data)

            # 技术分析表格
            if "technical" in analyzer_outputs:
                technical_data = analyzer_outputs["technical"].get("data", {})
                if not technical_data.get("error"):
                    # 支撑阻力位表
                    tables["technical_levels"] = self.table_generator.generate_levels_table(technical_data)

            # 代币经济学表格
            if "tokenomics" in analyzer_outputs:
                tokenomics_data = analyzer_outputs["tokenomics"].get("data", {})
                if not tokenomics_data.get("error"):
                    # 代币解锁时间表
                    tables["unlock_schedule"] = self.table_generator.generate_unlock_table(tokenomics_data)

            # 风险评估表格
            if "risk" in analyzer_outputs:
                risk_data = analyzer_outputs["risk"].get("data", {})
                if not risk_data.get("error"):
                    # 风险矩阵表
                    tables["risk_matrix"] = self.table_generator.generate_risk_matrix_table(risk_data)

            # 结论中的催化剂日历
            if "conclusion" in analyzer_outputs:
                conclusion_data = analyzer_outputs["conclusion"].get("data", {})
                if not conclusion_data.get("error"):
                    # 催化剂日历表
                    tables["catalyst_calendar"] = self.table_generator.generate_catalyst_calendar_table(conclusion_data)

        except Exception as e:
            print(f"⚠️ 表格生成出错: {str(e)}")

        return tables

    def _generate_charts_from_analyzers(self, analyzer_outputs: Dict[str, Dict[str, Any]]) -> Dict[str, str]:
        """
        从analyzer输出中自动生成图表

        Args:
            analyzer_outputs: 所有analyzer的输出

        Returns:
            Dict[str, str]: {analyzer_key: base64_encoded_chart}
        """
        charts = {}

        try:
            # 时间窗分析 - 价格走势图
            if "timeframe" in analyzer_outputs:
                timeframe_data = analyzer_outputs["timeframe"].get("data", {})
                if not timeframe_data.get("error"):
                    charts["price_trend"] = self.chart_generator.generate_price_chart(timeframe_data)

            # 情绪分析 - 情绪分布饼图
            if "sentiment" in analyzer_outputs:
                sentiment_data = analyzer_outputs["sentiment"].get("data", {})
                if not sentiment_data.get("error"):
                    charts["sentiment_distribution"] = self.chart_generator.generate_sentiment_chart(sentiment_data)

            # 竞品分析 - 估值对比图
            if "competitor" in analyzer_outputs:
                competitor_data = analyzer_outputs["competitor"].get("data", {})
                if not competitor_data.get("error"):
                    charts["valuation_comparison"] = self.chart_generator.generate_valuation_comparison_chart(competitor_data)

            # 风险评估 - 风险热力图
            if "risk" in analyzer_outputs:
                risk_data = analyzer_outputs["risk"].get("data", {})
                if not risk_data.get("error"):
                    charts["risk_heatmap"] = self.chart_generator.generate_risk_heatmap(risk_data)

        except Exception as e:
            print(f"⚠️ 图表生成出错: {str(e)}")

        return charts


# ================================
# 全局实例
# ================================

report_generator = ReportGenerator()
