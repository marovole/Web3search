"""
报告生成器
将研究结果格式化为Markdown报告
"""
from typing import Dict, Any
from datetime import datetime

from app.services.prompt_manager import prompt_manager


class ReportGenerator:
    """
    报告生成器
    负责将Deep Research结果组装成格式化的Markdown报告
    """

    def __init__(self):
        """初始化报告生成器"""
        self.prompt_manager = prompt_manager

    def generate_markdown(self, research_result: Dict[str, Any]) -> str:
        """
        生成Markdown格式的报告

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

        # 项目概览
        if sections.get("overview"):
            report_parts.append(sections["overview"])
            report_parts.append("\n---\n")

        # 技术分析
        if sections.get("technical_analysis"):
            report_parts.append(sections["technical_analysis"])
            report_parts.append("\n---\n")

        # 市场分析
        if sections.get("market_analysis"):
            report_parts.append(sections["market_analysis"])
            report_parts.append("\n---\n")

        # 社区分析
        if sections.get("community_analysis"):
            report_parts.append(sections["community_analysis"])
            report_parts.append("\n---\n")

        # 风险评估
        if sections.get("risk_assessment"):
            report_parts.append(sections["risk_assessment"])
            report_parts.append("\n---\n")

        # 竞品分析
        if sections.get("competitor_analysis"):
            report_parts.append(sections["competitor_analysis"])
            report_parts.append("\n---\n")

        # 结论
        report_parts.append("## 🎯 结论\n")
        report_parts.append(f"{conclusion}\n")
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


# ================================
# 全局实例
# ================================

report_generator = ReportGenerator()
