"""
报告生成器
将研究结果格式化为Markdown报告
"""
from typing import Dict, Any, List
from datetime import datetime

from app.services.prompt_manager import prompt_manager
from app.services.report.table_generator import table_generator
from app.services.report.chart_generator import chart_generator
from app.services.report.quality_validator import quality_validator
from app.services.report.markdown_builder import markdown_builder


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
        self.markdown_builder = markdown_builder

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

        # 组装最终报告
        markdown_content = "".join(report_parts)

        # 调用质量验证器
        try:
            print("  🔍 执行质量验证...")
            quality_score, quality_details = quality_validator.validate_report(
                markdown_content=markdown_content,
                sections=sections,
                data_sources=data_sources,
                report_type="deep_research",
                metadata={
                    "generation_time_seconds": generation_time,
                    "tables_count": len(tables),
                    "charts_count": len(charts)
                }
            )
            print(f"  📊 报告质量得分: {quality_score}/100 ({quality_details.get('grade', 'N/A')})")
            if quality_details.get('issues'):
                print(f"     建议改进: {', '.join(quality_details['issues'][:2])}")
        except Exception as e:
            print(f"  ⚠️ 质量验证出错（不影响报告生成）: {str(e)}")

        return markdown_content

    def generate_markdown_enhanced(self, research_result: Dict[str, Any],
                                 include_toc: bool = True,
                                 enable_formatting: bool = True) -> str:
        """
        生成增强版 Markdown 报告（支持目录、锚点、格式优化）

        Args:
            research_result: Deep Research引擎返回的研究结果
            include_toc: 是否包含目录
            enable_formatting: 是否启用格式优化

        Returns:
            str: 增强版 Markdown 格式的完整报告
        """
        print("  📝 使用增强版Markdown Builder生成报告...")

        # 配置markdown_builder
        self.markdown_builder.toc_enabled = include_toc
        self.markdown_builder.anchors_enabled = include_toc  # 启用目录时也启用锚点
        self.markdown_builder.formatting_enabled = enable_formatting

        # 转换数据格式以适应markdown_builder的接口
        analyses_data = self._convert_to_markdown_builder_format(research_result)

        # 使用增强版markdown_builder生成报告
        try:
            enhanced_report = self.markdown_builder.build_report_enhanced(
                analyses_data,
                include_toc=include_toc
            )
            print("  ✅ 增强版Markdown报告生成成功")
            return enhanced_report
        except Exception as e:
            print(f"  ⚠️ 增强版报告生成失败，回退到标准版: {str(e)}")
            # 回退到标准版
            return self.generate_markdown(research_result)

    def _convert_to_markdown_builder_format(self, research_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        将research_result转换为markdown_builder期望的格式

        Args:
            research_result: Deep Research结果

        Returns:
            Dict: 适配markdown_builder格式的数据
        """
        symbol = research_result.get("symbol", "Unknown")
        query = research_result.get("query", "")
        timestamp = research_result.get("timestamp", datetime.utcnow().isoformat())
        tldr = research_result.get("tldr", "")
        sections = research_result.get("sections", {})
        conclusion = research_result.get("conclusion", "")
        generation_time = research_result.get("generation_time", 0)
        models_used = research_result.get("models_used", {})
        data_sources = research_result.get("data_sources", [])
        
        # 获取analyzer_outputs用于生成表格和图表
        analyzer_outputs = research_result.get("analyzer_outputs", {})

        # 构建analyses数据结构
        analyses_data = {
            "symbol": symbol,
            "query": query,
            "timestamp": timestamp,
            "tldr": self._parse_tldr_text(tldr) if isinstance(tldr, str) else tldr,
            "timeframe": self._parse_section_text(sections.get("timeframe")) if "timeframe" in sections else None,
            "sentiment": self._parse_section_text(sections.get("sentiment")) if "sentiment" in sections else None,
            "technical": self._parse_section_text(sections.get("technical_analysis")) if "technical_analysis" in sections else None,
            "onchain": self._parse_section_text(sections.get("onchain_analysis")) if "onchain_analysis" in sections else None,
            "competitor": self._parse_section_text(sections.get("competitor_analysis")) if "competitor_analysis" in sections else None,
            "tokenomics": self._parse_section_text(sections.get("tokenomics")) if "tokenomics" in sections else None,
            "risk": self._parse_section_text(sections.get("risk_assessment")) if "risk_assessment" in sections else None,
            "conclusion": self._parse_section_text(conclusion) if conclusion else None,
            "data_sources": data_sources,
            "models_used": models_used,
            "generation_time": generation_time,
            "analyzer_outputs": analyzer_outputs  # 传递analyzer_outputs供组件使用
        }

        return analyses_data

    def _parse_tldr_text(self, tldr_text: str) -> Dict[str, Any]:
        """
        解析TL;DR文本为结构化数据

        Args:
            tldr_text: TL;DR文本

        Returns:
            Dict: 结构化的TL;DR数据
        """
        # 简单解析，实际使用时可以根据具体格式调整
        return {
            "one_sentence": tldr_text[:100] + "..." if len(tldr_text) > 100 else tldr_text,
            "summary": tldr_text,
            "bull_case": ["基本面强劲", "技术领先"],  # 示例数据
            "bear_case": ["市场波动", "竞争激烈"],  # 示例数据
            "key_catalysts": ["技术创新", "生态扩展"]  # 示例数据
        }

    def _parse_section_text(self, section_text: str) -> Dict[str, Any]:
        """
        解析章节文本为结构化数据

        Args:
            section_text: 章节文本

        Returns:
            Dict: 结构化的章节数据
        """
        if not section_text or section_text.startswith("⚠️"):
            return {"error": "数据不可用"}

        return {
            "summary": section_text,
            "analysis": section_text
        }

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
                    try:
                        # 竞品对比表
                        tables["competitor_comparison"] = self.table_generator.generate_competitor_table(competitor_data)
                        print(f"    ✅ 竞品对比表已生成")
                    except Exception as e:
                        print(f"    ⚠️ 竞品对比表生成失败: {str(e)}")
                    try:
                        # 估值倍数表
                        tables["valuation_multiples"] = self.table_generator.generate_valuation_table(competitor_data)
                        print(f"    ✅ 估值倍数表已生成")
                    except Exception as e:
                        print(f"    ⚠️ 估值倍数表生成失败: {str(e)}")

            # 技术分析表格
            if "technical" in analyzer_outputs:
                technical_data = analyzer_outputs["technical"].get("data", {})
                if not technical_data.get("error"):
                    try:
                        # 支撑阻力位表
                        tables["technical_levels"] = self.table_generator.generate_levels_table(technical_data)
                        print(f"    ✅ 技术分析表已生成")
                    except Exception as e:
                        print(f"    ⚠️ 技术分析表生成失败: {str(e)}")

            # 代币经济学表格
            if "tokenomics" in analyzer_outputs:
                tokenomics_data = analyzer_outputs["tokenomics"].get("data", {})
                if not tokenomics_data.get("error"):
                    try:
                        # 代币解锁时间表
                        tables["unlock_schedule"] = self.table_generator.generate_unlock_table(tokenomics_data)
                        print(f"    ✅ 代币解锁表已生成")
                    except Exception as e:
                        print(f"    ⚠️ 代币解锁表生成失败: {str(e)}")

            # 风险评估表格
            if "risk" in analyzer_outputs:
                risk_data = analyzer_outputs["risk"].get("data", {})
                if not risk_data.get("error"):
                    try:
                        # 风险矩阵表
                        tables["risk_matrix"] = self.table_generator.generate_risk_matrix_table(risk_data)
                        print(f"    ✅ 风险矩阵表已生成")
                    except Exception as e:
                        print(f"    ⚠️ 风险矩阵表生成失败: {str(e)}")

            # 结论中的催化剂日历
            if "conclusion" in analyzer_outputs:
                conclusion_data = analyzer_outputs["conclusion"].get("data", {})
                if not conclusion_data.get("error"):
                    try:
                        # 催化剂日历表
                        tables["catalyst_calendar"] = self.table_generator.generate_catalyst_calendar_table(conclusion_data)
                        print(f"    ✅ 催化剂日历表已生成")
                    except Exception as e:
                        print(f"    ⚠️ 催化剂日历表生成失败: {str(e)}")

        except Exception as e:
            print(f"⚠️ 表格生成流程出错: {str(e)}")

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
                    try:
                        charts["price_trend"] = self.chart_generator.generate_price_chart(timeframe_data)
                        print(f"    ✅ 价格走势图已生成")
                    except Exception as e:
                        print(f"    ⚠️ 价格走势图生成失败: {str(e)}")

            # 情绪分析 - 情绪分布饼图
            if "sentiment" in analyzer_outputs:
                sentiment_data = analyzer_outputs["sentiment"].get("data", {})
                if not sentiment_data.get("error"):
                    try:
                        charts["sentiment_distribution"] = self.chart_generator.generate_sentiment_chart(sentiment_data)
                        print(f"    ✅ 情绪分布图已生成")
                    except Exception as e:
                        print(f"    ⚠️ 情绪分布图生成失败: {str(e)}")

            # 竞品分析 - 估值对比图
            if "competitor" in analyzer_outputs:
                competitor_data = analyzer_outputs["competitor"].get("data", {})
                if not competitor_data.get("error"):
                    try:
                        charts["valuation_comparison"] = self.chart_generator.generate_valuation_comparison_chart(competitor_data)
                        print(f"    ✅ 估值对比图已生成")
                    except Exception as e:
                        print(f"    ⚠️ 估值对比图生成失败: {str(e)}")

            # 风险评估 - 风险热力图
            if "risk" in analyzer_outputs:
                risk_data = analyzer_outputs["risk"].get("data", {})
                if not risk_data.get("error"):
                    try:
                        charts["risk_heatmap"] = self.chart_generator.generate_risk_heatmap(risk_data)
                        print(f"    ✅ 风险热力图已生成")
                    except Exception as e:
                        print(f"    ⚠️ 风险热力图生成失败: {str(e)}")

        except Exception as e:
            print(f"⚠️ 图表生成流程出错: {str(e)}")

        return charts


# ================================
# 全局实例
# ================================

report_generator = ReportGenerator()
