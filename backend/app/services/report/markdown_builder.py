"""
Markdown 报告构建器 [增强版]
基于分析器输出生成完整的 Markdown 格式报告

✨ 新增功能：
- 自动目录生成（Table of Contents）
- 锚点链接支持（章节跳转）
- 报告格式优化
- 完整的章节结构管理

本模块提供高级Markdown构建功能，可与ReportGenerator配合使用。
"""
from typing import Dict, Any, Optional
from datetime import datetime

from app.schemas.research import (
    FullReportSchema,
    TLDRSchema,
    TimeframeSchema,
    SentimentSchema,
    TechnicalSchema,
    OnchainSchema,
    CompetitorSchema,
    TokenomicsSchema,
    RiskSchema,
    ConclusionSchema,
)


import re
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

from app.schemas.research import (
    FullReportSchema,
    TLDRSchema,
    TimeframeSchema,
    SentimentSchema,
    TechnicalSchema,
    OnchainSchema,
    CompetitorSchema,
    TokenomicsSchema,
    RiskSchema,
    ConclusionSchema,
)


class MarkdownBuilder:
    """
    Markdown 报告构建器 [增强版]
    将分析器的输出格式化为专业的 Markdown 报告

    新增功能：
    - 自动目录生成
    - 锚点链接支持
    - 章节结构管理
    - 格式优化
    """

    def __init__(self):
        """初始化 Markdown 构建器"""
        self.sections = []  # 存储章节信息
        self.toc_enabled = True  # 是否启用目录生成
        self.anchors_enabled = True  # 是否启用锚点链接
        self.formatting_enabled = True  # 是否启用格式优化
        self.compact_mode = False  # 是否启用紧凑模式

    def generate_anchor_id(self, title: str) -> str:
        """
        生成锚点ID

        Args:
            title: 章节标题

        Returns:
            str: 锚点ID
        """
        # 移除特殊字符，保留中英文、数字和连字符
        anchor = re.sub(r'[^\w\u4e00-\u9fff\s-]', '', title)
        # 替换空格为连字符
        anchor = re.sub(r'\s+', '-', anchor.strip())
        # 转换为小写
        return anchor.lower()

    def add_section(self, level: int, title: str, content: str = "", anchor_id: str = None) -> str:
        """
        添加章节并返回格式化的Markdown

        Args:
            level: 章节级别（1-6）
            title: 章节标题
            content: 章节内容
            anchor_id: 自定义锚点ID（可选）

        Returns:
            str: 格式化的Markdown章节
        """
        if not anchor_id:
            anchor_id = self.generate_anchor_id(title)

        # 记录章节信息
        section_info = {
            'level': level,
            'title': title,
            'anchor_id': anchor_id,
            'content_length': len(content)
        }
        self.sections.append(section_info)

        # 生成章节标题
        prefix = '#' * level
        if self.anchors_enabled and level <= 3:  # 只为1-3级标题添加锚点
            header = f"{prefix} {title} <a id=\"{anchor_id}\"></a>\n\n"
        else:
            header = f"{prefix} {title}\n\n"

        return header + content

    def generate_table_of_contents(self, max_level: int = 3) -> str:
        """
        生成目录

        Args:
            max_level: 目录的最大层级

        Returns:
            str: Markdown格式的目录
        """
        if not self.toc_enabled or not self.sections:
            return ""

        toc_parts = ["## 📋 目录\n\n"]

        for section in self.sections:
            if section['level'] <= max_level:
                # 计算缩进
                indent = "  " * (section['level'] - 1)
                # 生成目录项
                if self.anchors_enabled:
                    toc_item = f"{indent}- [{section['title']}](#{section['anchor_id']})\n"
                else:
                    toc_item = f"{indent}- {section['title']}\n"
                toc_parts.append(toc_item)

        # 添加快速导航链接
        if self.anchors_enabled:
            toc_parts.append("\n### 🔗 快速导航\n\n")
            toc_parts.append("- [返回顶部 ⬆️](#report-header)\n")
            toc_parts.append("- [查看报告概览 📊](#报告概览)\n")

        toc_parts.append("\n---\n\n")
        return "".join(toc_parts)

    def add_back_to_top_link(self, section_title: str = None) -> str:
        """
        添加返回顶部链接

        Args:
            section_title: 章节标题（可选）

        Returns:
            str: 返回顶部的Markdown链接
        """
        if not self.anchors_enabled:
            return ""

        if section_title:
            return f"\n\n---\n\n*返回顶部: [⬆️ 回到目录](#目录) | [🏠 回到报告标题](#report-header)*\n\n"
        else:
            return f"\n\n---\n\n*返回顶部: [⬆️ 回到目录](#目录) | [🏠 回到报告标题](#report-header)*\n\n"

    def generate_navigation_footer(self) -> str:
        """
        生成导航页脚

        Returns:
            str: 导航页脚的Markdown
        """
        if not self.anchors_enabled or not self.sections:
            return ""

        footer_parts = ["\n\n---\n\n## 🔗 报告导航\n\n"]

        # 主要章节快速导航
        main_sections = [s for s in self.sections if s['level'] <= 2]
        if main_sections:
            footer_parts.append("### 主要章节\n\n")
            for section in main_sections[:10]:  # 限制显示数量
                footer_parts.append(f"- [{section['title']}](#{section['anchor_id']})\n")

        # 实用链接
        footer_parts.append("\n### 实用链接\n\n")
        footer_parts.append("- [📋 返回目录](#目录)\n")
        footer_parts.append("- [🏠 回到顶部](#report-header)\n")

        footer_parts.append("\n---\n")
        return "".join(footer_parts)

    def format_section_separator(self, level: int = 1) -> str:
        """
        生成章节分隔符

        Args:
            level: 分隔符级别

        Returns:
            str: 格式化的分隔符
        """
        if not self.formatting_enabled:
            return "\n---\n\n"

        if level == 1:
            return "\n---\n\n"
        elif level == 2:
            return "\n---\n\n"
        else:
            return "\n---\n\n"

    def format_emphasis_text(self, text: str, style: str = "bold") -> str:
        """
        格式化强调文本

        Args:
            text: 文本内容
            style: 样式类型 (bold, italic, highlight, code)

        Returns:
            str: 格式化的文本
        """
        if not self.formatting_enabled:
            return text

        if style == "bold":
            return f"**{text}**"
        elif style == "italic":
            return f"*{text}*"
        elif style == "highlight":
            return f"**_{text}_**"
        elif style == "code":
            return f"`{text}`"
        else:
            return text

    def format_list_item(self, item: str, level: int = 0, emoji: str = None) -> str:
        """
        格式化列表项

        Args:
            item: 列表项内容
            level: 缩进级别
            emoji: 表情符号（可选）

        Returns:
            str: 格式化的列表项
        """
        if not self.formatting_enabled:
            return f"{'  ' * level}- {item}\n"

        indent = "  " * level
        if emoji:
            return f"{indent}- {emoji} {item}\n"
        else:
            return f"{indent}- {item}\n"

    def format_callout(self, content: str, type: str = "info") -> str:
        """
        格式化提示框

        Args:
            content: 提示内容
            type: 提示类型 (info, warning, success, error)

        Returns:
            str: 格式化的提示框
        """
        if not self.formatting_enabled:
            return f"{content}\n\n"

        emojis = {
            "info": "ℹ️",
            "warning": "⚠️",
            "success": "✅",
            "error": "❌",
            "tip": "💡",
            "note": "📝"
        }

        emoji = emojis.get(type, "ℹ️")
        return f"> {emoji} **{type.title()}**: {content}\n\n"

    def format_key_metrics(self, metrics: Dict[str, Any], title: str = "关键指标") -> str:
        """
        格式化关键指标卡片

        Args:
            metrics: 指标字典
            title: 卡片标题

        Returns:
            str: 格式化的指标卡片
        """
        if not self.formatting_enabled or not metrics:
            return ""

        parts = [f"### {title}\n\n"]
        parts.append("| 指标 | 数值 | 说明 |\n")
        parts.append("|------|------|------|\n")

        for key, value in metrics.items():
            if isinstance(value, (int, float)):
                formatted_value = f"{value:,}" if isinstance(value, int) else f"{value:.2f}"
            else:
                formatted_value = str(value)

            parts.append(f"| **{key}** | {formatted_value} | - |\n")

        parts.append("\n")
        return "".join(parts)

    def create_cross_reference(self, target_section: str, link_text: str = None) -> str:
        """
        创建交叉引用链接

        Args:
            target_section: 目标章节标题
            link_text: 链接文本（可选）

        Returns:
            str: 交叉引用链接
        """
        if not self.anchors_enabled:
            return target_section

        # 查找目标章节的锚点ID
        anchor_id = None
        for section in self.sections:
            if section['title'] == target_section:
                anchor_id = section['anchor_id']
                break

        if not anchor_id:
            return target_section

        # 生成锚点ID
        generated_anchor = self.generate_anchor_id(target_section)
        link_text = link_text or target_section
        return f"[{link_text}](#{generated_anchor})"

    def add_related_sections_links(self, current_section: str, related_sections: List[str]) -> str:
        """
        添加相关章节链接

        Args:
            current_section: 当前章节标题
            related_sections: 相关章节标题列表

        Returns:
            str: 相关章节链接的Markdown
        """
        if not self.anchors_enabled or not related_sections:
            return ""

        links = []
        for section_title in related_sections:
            link = self.create_cross_reference(section_title)
            links.append(link)

        if links:
            return f"\n\n### 🔗 相关章节\n\n{', '.join(links)}\n\n"
        return ""

    def build_report_enhanced(self, analyses: Dict[str, Any], include_toc: bool = True) -> str:
        """
        构建增强版 Markdown 报告（支持目录和锚点）

        Args:
            analyses: 包含所有分析器输出的字典
            include_toc: 是否包含目录

        Returns:
            str: 完整的增强版 Markdown 报告
        """
        # 重置章节列表
        self.sections = []

        parts = []

        # 1. 报告标题和元信息
        header_content = self._build_header_enhanced(analyses)
        parts.append(header_content)
        parts.append("\n---\n\n")

        # 2. TL;DR
        tldr_content = self._build_tldr_section_enhanced(analyses.get("tldr"))
        parts.append(tldr_content)
        parts.append("\n---\n\n")

        # 3. 时间窗分析
        timeframe_content = self._build_timeframe_section_enhanced(analyses.get("timeframe"))
        parts.append(timeframe_content)
        parts.append("\n---\n\n")

        # 4. 社区情绪分析
        sentiment_content = self._build_sentiment_section_enhanced(analyses.get("sentiment"))
        parts.append(sentiment_content)
        parts.append("\n---\n\n")

        # 5. 技术面分析
        technical_content = self._build_technical_section_enhanced(analyses.get("technical"))
        parts.append(technical_content)
        parts.append("\n---\n\n")

        # 6. 链上数据分析
        onchain_content = self._build_onchain_section_enhanced(analyses.get("onchain"))
        parts.append(onchain_content)
        parts.append("\n---\n\n")

        # 7. 竞品对比分析
        competitor_content = self._build_competitor_section_enhanced(analyses.get("competitor"))
        parts.append(competitor_content)
        parts.append("\n---\n\n")

        # 8. 代币经济学分析
        tokenomics_content = self._build_tokenomics_section_enhanced(analyses.get("tokenomics"))
        parts.append(tokenomics_content)
        parts.append("\n---\n\n")

        # 9. 风险评估
        risk_content = self._build_risk_section_enhanced(analyses.get("risk"))
        parts.append(risk_content)
        parts.append("\n---\n\n")

        # 10. 投资结论
        conclusion_content = self._build_conclusion_section_enhanced(analyses.get("conclusion"))
        parts.append(conclusion_content)
        parts.append("\n---\n\n")

        # 11. 免责声明
        disclaimer_content = self._build_disclaimer_enhanced()
        parts.append(disclaimer_content)
        parts.append("\n---\n\n")

        # 12. 报告元数据
        metadata_content = self._build_metadata_enhanced(analyses)
        parts.append(metadata_content)

        # 13. 添加导航页脚
        if self.anchors_enabled:
            nav_footer = self.generate_navigation_footer()
            parts.append(nav_footer)

        # 14. 生成目录（插入在标题之后）
        if include_toc and self.toc_enabled:
            toc = self.generate_table_of_contents(max_level=3)
            # 将目录插入到标题后面
            header_end_index = parts[0].find("\n---\n\n")
            if header_end_index != -1:
                header_with_toc = (
                    parts[0][:header_end_index] +
                    "\n" + toc +
                    parts[0][header_end_index:]
                )
                parts[0] = header_with_toc

        return "".join(parts)

    def build_report(self, analyses: Dict[str, Any]) -> str:
        """
        构建完整的 Markdown 报告（保持向后兼容）

        Args:
            analyses: 包含所有分析器输出的字典

        Returns:
            str: 完整的 Markdown 报告
        """
        # 默认使用增强版方法，但不包含目录以保持向后兼容
        return self.build_report_enhanced(analyses, include_toc=False)

    def _build_header_enhanced(self, analyses: Dict[str, Any]) -> str:
        """构建报告标题和元信息（增强版，支持锚点和格式优化）"""
        symbol = analyses.get("symbol", "Unknown")
        query = analyses.get("query", "")
        timestamp = analyses.get("timestamp", datetime.utcnow().isoformat())

        # 格式化时间
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            date_str = dt.strftime("%Y年%m月%d日 %H:%M UTC")
        except:
            date_str = timestamp

        parts = [f"# {symbol} 深度研究报告\n\n"]

        # 使用格式化方法
        parts.append(f"**生成时间**: {self.format_emphasis_text(date_str, 'code')}\n")
        parts.append(f"**用户查询**: {self.format_emphasis_text(query, 'italic')}\n")
        parts.append(f"**研究机构**: {self.format_emphasis_text('Web3 AI Search Engine', 'bold')}\n")
        parts.append(f"**报告类型**: {self.format_emphasis_text('多维度深度研究报告', 'highlight')}\n")

        parts.append(self.format_section_separator())

        # 报告概览
        parts.append("## 📊 报告概览\n\n")

        if self.formatting_enabled:
            parts.append(self.format_callout(
                f"本报告通过AI驱动的多维度分析引擎，为 {self.format_emphasis_text(symbol, 'bold')} 提供全面的投资研究分析。",
                "info"
            ))

        parts.append("### 🎯 核心分析维度\n\n")

        # 使用格式化列表项
        dimensions = [
            ("TL;DR", "核心投资论点摘要", "📌"),
            ("时间窗分析", "短期、中期、长期趋势分析", "⏰"),
            ("社区情绪", "社交媒体情绪和讨论热度", "💭"),
            ("技术面分析", "价格指标、技术指标、关键价位", "📈"),
            ("链上数据", "持币分布、链上活动、巨鲸动向", "🔗"),
            ("竞品对比", "市场地位、竞争优势、估值分析", "🏆"),
            ("代币经济学", "供应结构、解锁时间表、价值捕获", "💰"),
            ("风险评估", "风险因素、催化剂、情景分析", "⚠️"),
            ("投资结论", "综合评估、投资建议、关键指标", "🎯")
        ]

        for name, desc, emoji in dimensions:
            parts.append(self.format_list_item(f"**{name}**: {desc}", 0, emoji))

        parts.append("\n")

        # 添加阅读提示
        if self.formatting_enabled:
            parts.append(self.format_callout(
                "💡 **阅读提示**: 点击目录中的章节可以快速跳转到对应内容，使用文末的导航链接可以方便地返回顶部。",
                "tip"
            ))

        header_content = "".join(parts)
        return self.add_section(1, f"{symbol} 深度研究报告", header_content, "report-header")

    def _build_tldr_section_enhanced(self, tldr: Optional[Dict]) -> str:
        """构建 TL;DR 章节（增强版，支持锚点）"""
        if not tldr or tldr.get("error"):
            content = "⚠️ TL;DR 分析暂时不可用"
            return self.add_section(2, "📌 TL;DR", content, "tldr-section")

        parts = []

        # 一句话总结
        if "one_sentence" in tldr:
            parts.append(f"### 核心论点\n\n**{tldr['one_sentence']}**\n\n")

        # 看涨理由
        if "bull_case" in tldr and tldr["bull_case"]:
            parts.append("### 🐂 看涨理由\n\n")
            for i, reason in enumerate(tldr["bull_case"], 1):
                parts.append(f"{i}. {reason}\n")
            parts.append("\n")

        # 看跌理由
        if "bear_case" in tldr and tldr["bear_case"]:
            parts.append("### 🐻 看跌理由\n\n")
            for i, reason in enumerate(tldr["bear_case"], 1):
                parts.append(f"{i}. {reason}\n")
            parts.append("\n")

        # 关键催化剂
        if "key_catalysts" in tldr and tldr["key_catalysts"]:
            parts.append("### ⚡ 关键催化剂\n\n")
            for catalyst in tldr["key_catalysts"]:
                parts.append(f"- {catalyst}\n")
            parts.append("\n")

        # 风险等级和投资期限
        if "risk_level" in tldr or "investment_horizon" in tldr:
            parts.append("### 📊 投资参数\n\n")
            if "risk_level" in tldr:
                parts.append(f"- **风险等级**: {tldr['risk_level']}\n")
            if "investment_horizon" in tldr:
                parts.append(f"- **建议投资期限**: {tldr['investment_horizon']}\n")
            parts.append("\n")

        # 综合摘要
        if "summary" in tldr:
            parts.append(f"### 综合评估\n\n{tldr['summary']}\n\n")

        content = "".join(parts)
        return self.add_section(2, "📌 TL;DR", content, "tldr-section")

    def _build_timeframe_section_enhanced(self, timeframe: Optional[Dict]) -> str:
        """构建时间窗分析章节（增强版）"""
        if not timeframe or timeframe.get("error"):
            content = "⚠️ 时间窗分析暂时不可用"
            return self.add_section(2, "⏰ 时间窗分析", content, "timeframe-section")

        # 使用原有的逻辑构建内容
        content = self._build_timeframe_section(timeframe).replace("## ⏰ 时间窗分析\n\n", "")
        return self.add_section(2, "⏰ 时间窗分析", content, "timeframe-section")

    def _build_sentiment_section_enhanced(self, sentiment: Optional[Dict]) -> str:
        """构建情绪分析章节（增强版）"""
        if not sentiment or sentiment.get("error"):
            content = "⚠️ 情绪分析暂时不可用"
            return self.add_section(2, "💭 社区情绪分析", content, "sentiment-section")

        content = self._build_sentiment_section(sentiment).replace("## 💭 社区情绪分析\n\n", "")
        return self.add_section(2, "💭 社区情绪分析", content, "sentiment-section")

    def _build_technical_section_enhanced(self, technical: Optional[Dict]) -> str:
        """构建技术面分析章节（增强版）"""
        if not technical or technical.get("error"):
            content = "⚠️ 技术面分析暂时不可用"
            return self.add_section(2, "📈 技术面分析", content, "technical-section")

        content = self._build_technical_section(technical).replace("## 📈 技术面分析\n\n", "")
        return self.add_section(2, "📈 技术面分析", content, "technical-section")

    def _build_onchain_section_enhanced(self, onchain: Optional[Dict]) -> str:
        """构建链上分析章节（增强版）"""
        if not onchain or onchain.get("error"):
            content = "⚠️ 链上分析暂时不可用"
            return self.add_section(2, "🔗 链上数据分析", content, "onchain-section")

        content = self._build_onchain_section(onchain).replace("## 🔗 链上数据分析\n\n", "")
        return self.add_section(2, "🔗 链上数据分析", content, "onchain-section")

    def _build_competitor_section_enhanced(self, competitor: Optional[Dict]) -> str:
        """构建竞品分析章节（增强版）"""
        if not competitor or competitor.get("error"):
            content = "⚠️ 竞品分析暂时不可用"
            return self.add_section(2, "🏆 竞品对比分析", content, "competitor-section")

        content = self._build_competitor_section(competitor).replace("## 🏆 竞品对比分析\n\n", "")
        return self.add_section(2, "🏆 竞品对比分析", content, "competitor-section")

    def _build_tokenomics_section_enhanced(self, tokenomics: Optional[Dict]) -> str:
        """构建代币经济学章节（增强版）"""
        if not tokenomics or tokenomics.get("error"):
            content = "⚠️ 代币经济学分析暂时不可用"
            return self.add_section(2, "💰 代币经济学分析", content, "tokenomics-section")

        content = self._build_tokenomics_section(tokenomics).replace("## 💰 代币经济学分析\n\n", "")
        return self.add_section(2, "💰 代币经济学分析", content, "tokenomics-section")

    def _build_risk_section_enhanced(self, risk: Optional[Dict]) -> str:
        """构建风险评估章节（增强版）"""
        if not risk or risk.get("error"):
            content = "⚠️ 风险评估暂时不可用"
            return self.add_section(2, "⚠️ 风险评估", content, "risk-section")

        content = self._build_risk_section(risk).replace("## ⚠️ 风险评估\n\n", "")
        return self.add_section(2, "⚠️ 风险评估", content, "risk-section")

    def _build_conclusion_section_enhanced(self, conclusion: Optional[Dict]) -> str:
        """构建投资结论章节（增强版）"""
        if not conclusion or conclusion.get("error"):
            content = "⚠️ 投资结论暂时不可用"
            return self.add_section(2, "🎯 投资结论", content, "conclusion-section")

        content = self._build_conclusion_section(conclusion).replace("## 🎯 投资结论\n\n", "")
        return self.add_section(2, "🎯 投资结论", content, "conclusion-section")

    def _build_disclaimer_enhanced(self) -> str:
        """构建免责声明（增强版）"""
        content = self._build_disclaimer().replace("## ⚠️ 免责声明\n\n", "")
        return self.add_section(2, "⚠️ 免责声明", content, "disclaimer-section")

    def _build_metadata_enhanced(self, analyses: Dict[str, Any]) -> str:
        """构建报告元数据（增强版）"""
        content = self._build_metadata(analyses).replace("## 📊 报告元数据\n\n", "")
        return self.add_section(2, "📊 报告元数据", content, "metadata-section")

    def _build_header(self, analyses: Dict[str, Any]) -> str:
        """构建报告标题和元信息"""
        symbol = analyses.get("symbol", "Unknown")
        query = analyses.get("query", "")
        timestamp = analyses.get("timestamp", datetime.utcnow().isoformat())

        # 格式化时间
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            date_str = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        except:
            date_str = timestamp

        return f"""# {symbol} 深度研究报告

**生成时间**: {date_str}
**用户查询**: {query}
**研究机构**: Web3 AI Search Engine
**报告类型**: 多维度深度研究报告
"""

    def _build_tldr_section(self, tldr: Optional[Dict]) -> str:
        """构建 TL;DR 章节"""
        if not tldr or tldr.get("error"):
            return "## 📌 TL;DR\n\n⚠️ TL;DR 分析暂时不可用\n"

        parts = ["## 📌 TL;DR\n\n"]

        # 一句话总结
        if "one_sentence" in tldr:
            parts.append(f"### 核心论点\n\n**{tldr['one_sentence']}**\n\n")

        # 看涨理由
        if "bull_case" in tldr and tldr["bull_case"]:
            parts.append("### 🐂 看涨理由\n\n")
            for i, reason in enumerate(tldr["bull_case"], 1):
                parts.append(f"{i}. {reason}\n")
            parts.append("\n")

        # 看跌理由
        if "bear_case" in tldr and tldr["bear_case"]:
            parts.append("### 🐻 看跌理由\n\n")
            for i, reason in enumerate(tldr["bear_case"], 1):
                parts.append(f"{i}. {reason}\n")
            parts.append("\n")

        # 关键催化剂
        if "key_catalysts" in tldr and tldr["key_catalysts"]:
            parts.append("### ⚡ 关键催化剂\n\n")
            for catalyst in tldr["key_catalysts"]:
                parts.append(f"- {catalyst}\n")
            parts.append("\n")

        # 风险等级和投资期限
        if "risk_level" in tldr or "investment_horizon" in tldr:
            parts.append("### 📊 投资参数\n\n")
            if "risk_level" in tldr:
                parts.append(f"- **风险等级**: {tldr['risk_level']}\n")
            if "investment_horizon" in tldr:
                parts.append(f"- **建议投资期限**: {tldr['investment_horizon']}\n")
            parts.append("\n")

        # 综合摘要
        if "summary" in tldr:
            parts.append(f"### 综合评估\n\n{tldr['summary']}\n\n")

        return "".join(parts)

    def _build_timeframe_section(self, timeframe: Optional[Dict]) -> str:
        """构建时间窗分析章节"""
        if not timeframe or timeframe.get("error"):
            return "## ⏰ 时间窗分析\n\n⚠️ 时间窗分析暂时不可用\n"

        parts = ["## ⏰ 时间窗分析\n\n"]

        # 整体动量
        if "overall_momentum" in timeframe:
            parts.append(f"**整体动量**: {timeframe['overall_momentum']}\n\n")

        # 趋势转折
        if timeframe.get("regime_shift"):
            parts.append(f"**趋势转折**: {timeframe.get('regime_shift_description', '是')}\n\n")

        # 各时间窗分析
        if "windows" in timeframe and timeframe["windows"]:
            parts.append("### 多时间窗分析\n\n")
            for window in timeframe["windows"]:
                parts.append(f"#### {window.get('timeframe', '未知时间窗')}\n\n")
                parts.append(f"- **趋势**: {window.get('trend', '未知')}\n")

                # 指标
                metrics = window.get("metrics", {})
                if metrics:
                    parts.append("- **关键指标**:\n")
                    if metrics.get("price_change_pct") is not None:
                        parts.append(f"  - 价格变化: {metrics['price_change_pct']:+.2f}%\n")
                    if metrics.get("volume_change_pct") is not None:
                        parts.append(f"  - 成交量变化: {metrics['volume_change_pct']:+.2f}%\n")
                    if metrics.get("sentiment_score") is not None:
                        parts.append(f"  - 情绪得分: {metrics['sentiment_score']:.1f}/100\n")

                # 关键事件
                if window.get("key_events"):
                    parts.append("- **关键事件**:\n")
                    for event in window["key_events"]:
                        parts.append(f"  - {event}\n")

                # 叙述
                if window.get("narrative"):
                    parts.append(f"\n{window['narrative']}\n")

                parts.append("\n")

        # 综合分析
        if "summary" in timeframe:
            parts.append(f"### 综合分析\n\n{timeframe['summary']}\n\n")

        return "".join(parts)

    def _build_sentiment_section(self, sentiment: Optional[Dict]) -> str:
        """构建情绪分析章节"""
        if not sentiment or sentiment.get("error"):
            return "## 💭 社区情绪分析\n\n⚠️ 情绪分析暂时不可用\n"

        parts = ["## 💭 社区情绪分析\n\n"]

        # 整体情绪
        if "overall_sentiment" in sentiment:
            parts.append(f"**整体情绪**: {sentiment['overall_sentiment']}\n")
        if "sentiment_score" in sentiment:
            parts.append(f"**情绪得分**: {sentiment['sentiment_score']:.1f}/100\n\n")

        # FOMO 和恐慌指数
        if "fomo_index" in sentiment or "fear_index" in sentiment:
            parts.append("### 情绪指数\n\n")
            if "fomo_index" in sentiment:
                parts.append(f"- **FOMO 指数**: {sentiment['fomo_index']}/100\n")
            if "fear_index" in sentiment:
                parts.append(f"- **恐慌指数**: {sentiment['fear_index']}/100\n")
            parts.append("\n")

        # 社交媒体指标
        if "social_metrics" in sentiment and sentiment["social_metrics"]:
            parts.append("### 社交媒体数据\n\n")
            for metric in sentiment["social_metrics"]:
                platform = metric.get("platform", "未知平台")
                parts.append(f"#### {platform}\n\n")
                parts.append(f"- 提及次数: {metric.get('mention_count', 0):,}\n")
                parts.append(f"- 情绪得分: {metric.get('sentiment_score', 0):.2f} (-1 到 1)\n")
                parts.append(f"- 互动率: {metric.get('engagement_rate', 0):.2f}%\n")

                if metric.get("top_topics"):
                    parts.append("- 热门话题:\n")
                    for topic in metric["top_topics"]:
                        parts.append(f"  - {topic}\n")
                parts.append("\n")

        # 情绪驱动因素
        if "sentiment_drivers" in sentiment and sentiment["sentiment_drivers"]:
            parts.append("### 情绪驱动因素\n\n")
            for driver in sentiment["sentiment_drivers"]:
                parts.append(f"- {driver}\n")
            parts.append("\n")

        # 情绪变化趋势
        if "sentiment_shift" in sentiment:
            parts.append(f"**情绪变化**: {sentiment['sentiment_shift']}\n\n")

        # 综合分析
        if "summary" in sentiment:
            parts.append(f"### 综合分析\n\n{sentiment['summary']}\n\n")

        return "".join(parts)

    def _build_technical_section(self, technical: Optional[Dict]) -> str:
        """构建技术面分析章节"""
        if not technical or technical.get("error"):
            return "## 📈 技术面分析\n\n⚠️ 技术面分析暂时不可用\n"

        parts = ["## 📈 技术面分析\n\n"]

        # 价格指标
        if "price_metrics" in technical:
            pm = technical["price_metrics"]
            parts.append("### 价格指标\n\n")
            parts.append(f"- **当前价格**: ${pm.get('current_price', 0):,.4f}\n")
            if pm.get("price_change_24h_pct") is not None:
                parts.append(f"- **24小时涨跌**: {pm['price_change_24h_pct']:+.2f}%\n")
            if pm.get("high_24h"):
                parts.append(f"- **24小时最高**: ${pm['high_24h']:,.4f}\n")
            if pm.get("low_24h"):
                parts.append(f"- **24小时最低**: ${pm['low_24h']:,.4f}\n")
            if pm.get("all_time_high"):
                parts.append(f"- **历史最高**: ${pm['all_time_high']:,.4f}\n")
            if pm.get("ath_distance_pct") is not None:
                parts.append(f"- **距ATH**: {pm['ath_distance_pct']:+.2f}%\n")
            parts.append("\n")

        # 技术指标
        if "technical_indicators" in technical:
            ti = technical["technical_indicators"]
            parts.append("### 技术指标\n\n")
            if ti.get("rsi") is not None:
                parts.append(f"- **RSI**: {ti['rsi']:.1f}\n")
            if ti.get("macd_signal"):
                parts.append(f"- **MACD 信号**: {ti['macd_signal']}\n")
            if ti.get("moving_averages"):
                parts.append("- **均线状态**:\n")
                for ma, status in ti["moving_averages"].items():
                    parts.append(f"  - {ma}: {status}\n")
            parts.append("\n")

        # 关键价位
        if "key_levels" in technical:
            kl = technical["key_levels"]
            parts.append("### 关键价位\n\n")
            if kl.get("resistance"):
                parts.append("**阻力位**:\n")
                for level in kl["resistance"]:
                    parts.append(f"- ${level:,.4f}\n")
                parts.append("\n")
            if kl.get("support"):
                parts.append("**支撑位**:\n")
                for level in kl["support"]:
                    parts.append(f"- ${level:,.4f}\n")
                parts.append("\n")

        # 交易信号
        if "trading_signals" in technical and technical["trading_signals"]:
            parts.append("### 交易信号\n\n")
            for signal in technical["trading_signals"]:
                parts.append(f"- {signal}\n")
            parts.append("\n")

        # 技术面展望
        if "technical_outlook" in technical:
            parts.append(f"**技术面展望**: {technical['technical_outlook']}\n\n")

        # 综合分析
        if "summary" in technical:
            parts.append(f"### 综合分析\n\n{technical['summary']}\n\n")

        return "".join(parts)

    def _build_onchain_section(self, onchain: Optional[Dict]) -> str:
        """构建链上分析章节"""
        if not onchain or onchain.get("error"):
            return "## 🔗 链上数据分析\n\n⚠️ 链上分析暂时不可用\n"

        parts = ["## 🔗 链上数据分析\n\n"]

        # 持币分布
        if "holder_distribution" in onchain:
            hd = onchain["holder_distribution"]
            parts.append("### 持币分布\n\n")
            parts.append(f"- **总持币地址数**: {hd.get('total_holders', 0):,}\n")
            parts.append(f"- **巨鲸数量** (>1%): {hd.get('whale_holders', 0):,}\n")
            parts.append(f"- **散户数量** (<0.01%): {hd.get('retail_holders', 0):,}\n")
            if hd.get("top10_concentration_pct") is not None:
                parts.append(f"- **Top 10 持币占比**: {hd['top10_concentration_pct']:.2f}%\n")
            parts.append("\n")

        # 链上指标
        if "onchain_metrics" in onchain:
            om = onchain["onchain_metrics"]
            parts.append("### 链上活动指标\n\n")
            if om.get("active_addresses_24h"):
                parts.append(f"- **24h 活跃地址**: {om['active_addresses_24h']:,}\n")
            if om.get("transaction_count_24h"):
                parts.append(f"- **24h 交易数**: {om['transaction_count_24h']:,}\n")
            if om.get("transaction_volume_24h"):
                parts.append(f"- **24h 交易量**: ${om['transaction_volume_24h']:,.0f}\n")
            if om.get("exchange_inflow_24h") and om.get("exchange_outflow_24h"):
                net_flow = om["exchange_outflow_24h"] - om["exchange_inflow_24h"]
                parts.append(f"- **24h 交易所净流出**: ${net_flow:+,.0f}\n")
            parts.append("\n")

        # 巨鲸动向
        if "whale_movements" in onchain and onchain["whale_movements"]:
            parts.append("### 巨鲸动向\n\n")
            for movement in onchain["whale_movements"]:
                parts.append(f"- {movement}\n")
            parts.append("\n")

        # 交易所流向
        if "exchange_flows" in onchain:
            parts.append(f"**交易所流向**: {onchain['exchange_flows']}\n\n")

        # 筹码集中度信号
        if "accumulation_signal" in onchain:
            parts.append(f"**筹码集中度**: {onchain['accumulation_signal']}\n\n")

        # 链上健康度
        if "onchain_health" in onchain:
            parts.append(f"**链上健康度**: {onchain['onchain_health']}\n\n")

        # 综合分析
        if "summary" in onchain:
            parts.append(f"### 综合分析\n\n{onchain['summary']}\n\n")

        return "".join(parts)

    def _build_competitor_section(self, competitor: Optional[Dict]) -> str:
        """构建竞品分析章节"""
        if not competitor or competitor.get("error"):
            return "## 🏆 竞品对比分析\n\n⚠️ 竞品分析暂时不可用\n"

        parts = ["## 🏆 竞品对比分析\n\n"]

        # 市场地位
        if "market_position" in competitor:
            parts.append(f"**市场地位**: {competitor['market_position']}\n")
        if competitor.get("market_share_pct") is not None:
            parts.append(f"**市场份额**: {competitor['market_share_pct']:.2f}%\n\n")

        # 竞品列表将在 table_generator 中生成表格

        # 估值倍数
        if "valuation_multiples" in competitor:
            vm = competitor["valuation_multiples"]
            parts.append("### 估值倍数\n\n")
            if vm.get("ps_ratio") is not None:
                parts.append(f"- **P/S 比率**: {vm['ps_ratio']:.2f}\n")
            if vm.get("fdv_revenue") is not None:
                parts.append(f"- **FDV/Revenue**: {vm['fdv_revenue']:.2f}\n")
            if vm.get("fdv_tvl") is not None:
                parts.append(f"- **FDV/TVL**: {vm['fdv_tvl']:.2f}\n")
            parts.append("\n")

        # 竞争优势
        if "competitive_advantages" in competitor and competitor["competitive_advantages"]:
            parts.append("### 竞争优势\n\n")
            for adv in competitor["competitive_advantages"]:
                parts.append(f"- ✅ {adv}\n")
            parts.append("\n")

        # 竞争威胁
        if "competitive_threats" in competitor and competitor["competitive_threats"]:
            parts.append("### 竞争威胁\n\n")
            for threat in competitor["competitive_threats"]:
                parts.append(f"- ⚠️ {threat}\n")
            parts.append("\n")

        # 估值评估
        if "valuation_assessment" in competitor:
            parts.append(f"**估值评估**: {competitor['valuation_assessment']}\n\n")

        # 综合分析
        if "summary" in competitor:
            parts.append(f"### 综合分析\n\n{competitor['summary']}\n\n")

        return "".join(parts)

    def _build_tokenomics_section(self, tokenomics: Optional[Dict]) -> str:
        """构建代币经济学章节"""
        if not tokenomics or tokenomics.get("error"):
            return "## 💰 代币经济学分析\n\n⚠️ 代币经济学分析暂时不可用\n"

        parts = ["## 💰 代币经济学分析\n\n"]

        # 供应结构
        if "supply_structure" in tokenomics:
            ss = tokenomics["supply_structure"]
            parts.append("### 供应结构\n\n")
            parts.append(f"- **总供应量**: {ss.get('total_supply', 0):,.0f}\n")
            parts.append(f"- **流通供应量**: {ss.get('circulating_supply', 0):,.0f}\n")
            if ss.get("circulating_ratio_pct") is not None:
                parts.append(f"- **流通率**: {ss['circulating_ratio_pct']:.2f}%\n")
            if ss.get("allocation"):
                parts.append("\n**代币分配**:\n")
                for beneficiary, pct in ss["allocation"].items():
                    parts.append(f"- {beneficiary}: {pct:.2f}%\n")
            parts.append("\n")

        # 解锁时间表将在 table_generator 中生成表格

        # 解锁抛压
        if "unlock_pressure" in tokenomics:
            parts.append(f"**解锁抛压**: {tokenomics['unlock_pressure']}\n\n")

        # 价值捕获机制
        if "value_capture" in tokenomics:
            vc = tokenomics["value_capture"]
            parts.append("### 价值捕获机制\n\n")
            if vc.get("governance"):
                parts.append(f"- **治理**: {vc['governance']}\n")
            if vc.get("staking"):
                parts.append(f"- **质押**: {vc['staking']}\n")
            if vc.get("buyback_burn"):
                parts.append(f"- **回购销毁**: {vc['buyback_burn']}\n")
            if vc.get("revenue_share"):
                parts.append(f"- **收益分成**: {vc['revenue_share']}\n")
            parts.append("\n")

        # 代币经济学评级
        if "tokenomics_rating" in tokenomics:
            parts.append(f"**代币经济学评级**: {tokenomics['tokenomics_rating']}\n\n")

        # 飞轮效应
        if "flywheel_effect" in tokenomics:
            parts.append(f"**飞轮效应**: {tokenomics['flywheel_effect']}\n\n")

        # 综合分析
        if "summary" in tokenomics:
            parts.append(f"### 综合分析\n\n{tokenomics['summary']}\n\n")

        return "".join(parts)

    def _build_risk_section(self, risk: Optional[Dict]) -> str:
        """构建风险评估章节"""
        if not risk or risk.get("error"):
            return "## ⚠️ 风险评估\n\n⚠️ 风险评估暂时不可用\n"

        parts = ["## ⚠️ 风险评估\n\n"]

        # 整体风险评级
        if "overall_risk_rating" in risk:
            parts.append(f"**整体风险评级**: {risk['overall_risk_rating']}\n")
        if "overall_risk_score" in risk:
            parts.append(f"**风险分数**: {risk['overall_risk_score']}/10\n\n")

        # 催化剂（按时间窗分类）
        if "catalysts" in risk:
            cats = risk["catalysts"]
            parts.append("### 催化剂日历\n\n")

            for timeframe, items in cats.items():
                if items:
                    timeframe_cn = {
                        "short_term": "短期（2-4周）",
                        "medium_term": "中期（1-2月）",
                        "long_term": "长期（3-6月）"
                    }.get(timeframe, timeframe)

                    parts.append(f"#### {timeframe_cn}\n\n")
                    for item in items:
                        parts.append(f"- **{item.get('event', '未知事件')}**\n")
                        parts.append(f"  - 时间窗: {item.get('timeframe', '未知')}\n")
                        parts.append(f"  - 影响: {item.get('impact', '未知')}\n")
                        parts.append(f"  - 概率: {item.get('probability', '未知')}\n")
                        parts.append(f"  - 价格影响: {item.get('price_impact', '未知')}\n")
                        if item.get("description"):
                            parts.append(f"  - 描述: {item['description']}\n")
                        parts.append("\n")

        # 风险因素（按类别分类）
        if "risks" in risk:
            risks = risk["risks"]
            parts.append("### 风险因素\n\n")

            risk_categories = {
                "regulatory": "🏛️ 监管风险",
                "technical": "⚙️ 技术风险",
                "competitive": "🏁 竞争风险",
                "market": "📊 市场风险",
                "tokenomics": "💰 代币经济学风险"
            }

            for category, title in risk_categories.items():
                items = risks.get(category, [])
                if items:
                    parts.append(f"#### {title}\n\n")
                    for item in items:
                        parts.append(f"- **{item.get('risk', '未知风险')}**\n")
                        parts.append(f"  - 严重程度: {item.get('severity', '未知')}\n")
                        parts.append(f"  - 概率: {item.get('probability', '未知')}\n")
                        parts.append(f"  - 价格影响: {item.get('price_impact', '未知')}\n")
                        if item.get("mitigation"):
                            parts.append(f"  - 缓解措施: {item['mitigation']}\n")
                        parts.append("\n")

        # 风险收益分析
        if "risk_reward_analysis" in risk:
            rra = risk["risk_reward_analysis"]
            parts.append("### 风险收益分析\n\n")
            parts.append(f"- **上行潜力**: {rra.get('upside_potential', '未知')}\n")
            parts.append(f"- **下行风险**: {rra.get('downside_risk', '未知')}\n")
            parts.append(f"- **风险收益比**: {rra.get('risk_reward_ratio', 0):.2f}\n")
            parts.append(f"- **不对称性**: {rra.get('asymmetry', '未知')}\n\n")

        # 尾部风险
        if "tail_risks" in risk and risk["tail_risks"]:
            parts.append("### 尾部风险\n\n")
            for tail_risk in risk["tail_risks"]:
                parts.append(f"- 🚨 {tail_risk}\n")
            parts.append("\n")

        # 情景分析
        if "scenario_analysis" in risk and risk["scenario_analysis"]:
            parts.append("### 情景分析\n\n")
            for scenario in risk["scenario_analysis"]:
                parts.append(f"#### {scenario.get('scenario', '未知情景')}\n\n")
                parts.append(f"- **概率**: {scenario.get('probability', 0)}%\n")
                parts.append(f"- **价格目标**: {scenario.get('price_target', '未知')}\n")
                if scenario.get("triggers"):
                    parts.append("- **触发条件**:\n")
                    for trigger in scenario["triggers"]:
                        parts.append(f"  - {trigger}\n")
                if scenario.get("narrative"):
                    parts.append(f"- **叙述**: {scenario['narrative']}\n")
                parts.append("\n")

        # 风险调整后建议
        if "risk_adjusted_recommendation" in risk:
            parts.append(f"**风险调整后建议**: {risk['risk_adjusted_recommendation']}\n\n")

        # 综合分析
        if "summary" in risk:
            parts.append(f"### 综合分析\n\n{risk['summary']}\n\n")

        return "".join(parts)

    def _build_conclusion_section(self, conclusion: Optional[Dict]) -> str:
        """构建投资结论章节"""
        if not conclusion or conclusion.get("error"):
            return "## 🎯 投资结论\n\n⚠️ 投资结论暂时不可用\n"

        parts = ["## 🎯 投资结论\n\n"]

        # 执行摘要
        if "executive_summary" in conclusion:
            es = conclusion["executive_summary"]
            parts.append("### 📋 执行摘要\n\n")

            if es.get("one_sentence_thesis"):
                parts.append(f"**核心投资论点**: {es['one_sentence_thesis']}\n\n")

            if es.get("bull_thesis"):
                parts.append("**看涨论点**:\n")
                for thesis in es["bull_thesis"]:
                    parts.append(f"- ✅ {thesis}\n")
                parts.append("\n")

            if es.get("bear_thesis"):
                parts.append("**看跌论点**:\n")
                for thesis in es["bear_thesis"]:
                    parts.append(f"- ⚠️ {thesis}\n")
                parts.append("\n")

            if es.get("key_assumptions"):
                parts.append("**关键假设**:\n")
                for assumption in es["key_assumptions"]:
                    parts.append(f"- {assumption}\n")
                parts.append("\n")

            if es.get("invalidation_triggers"):
                parts.append("**失效触发器**:\n")
                for trigger in es["invalidation_triggers"]:
                    parts.append(f"- 🚨 {trigger}\n")
                parts.append("\n")

        # 投资展望
        if "investment_outlook" in conclusion:
            io = conclusion["investment_outlook"]
            parts.append("### 📊 投资展望\n\n")

            for term, data in [("短期", io.get("short_term")), ("中期", io.get("medium_term"))]:
                if data:
                    parts.append(f"#### {term} ({data.get('timeframe', '未知')})\n\n")
                    parts.append(f"- **观点**: {data.get('view', '未知')}\n")
                    parts.append(f"- **价格目标**: {data.get('price_target', '未知')}\n")
                    if data.get("key_events"):
                        parts.append("- **关键事件**:\n")
                        for event in data["key_events"]:
                            parts.append(f"  - {event}\n")
                    if data.get("rationale"):
                        parts.append(f"- **理由**: {data['rationale']}\n")
                    parts.append("\n")

        # 关键跟踪指标
        if "key_metrics_to_watch" in conclusion and conclusion["key_metrics_to_watch"]:
            parts.append("### 📈 关键跟踪指标\n\n")
            for i, metric in enumerate(conclusion["key_metrics_to_watch"], 1):
                parts.append(f"**{i}. {metric.get('metric', '未知指标')}**\n")
                parts.append(f"- 当前值: {metric.get('current_value', '未知')}\n")
                parts.append(f"- 目标值: {metric.get('target', '未知')}\n")
                parts.append(f"- 重要性: {metric.get('importance', '未知')}\n")
                if metric.get("rationale"):
                    parts.append(f"- 理由: {metric['rationale']}\n")
                parts.append("\n")

        # 置信度评估
        if "confidence_assessment" in conclusion:
            ca = conclusion["confidence_assessment"]
            parts.append("### 🎲 置信度评估\n\n")
            parts.append(f"- **整体置信度**: {ca.get('overall_confidence', 0)}/100 ({ca.get('confidence_level', '未知')})\n")
            parts.append(f"- **数据质量**: {ca.get('data_quality', '未知')}\n")
            parts.append(f"- **分析完整性**: {ca.get('analysis_completeness', '未知')}\n")
            if ca.get("uncertainty_factors"):
                parts.append("- **不确定性因素**:\n")
                for factor in ca["uncertainty_factors"]:
                    parts.append(f"  - {factor}\n")
            if ca.get("confidence_rationale"):
                parts.append(f"- **置信度理由**: {ca['confidence_rationale']}\n")
            parts.append("\n")

        # 投资建议
        if "investment_recommendation" in conclusion:
            ir = conclusion["investment_recommendation"]
            parts.append("### 💡 投资建议\n\n")
            parts.append(f"**评级**: {ir.get('rating', '未知')}\n")
            parts.append(f"**行动**: {ir.get('action', '未知')}\n")
            parts.append(f"**建议仓位**: {ir.get('position_sizing', '未知')}\n\n")

            if ir.get("entry_strategy"):
                parts.append(f"**进场策略**: {ir['entry_strategy']}\n\n")
            if ir.get("exit_strategy"):
                parts.append(f"**出场策略**: {ir['exit_strategy']}\n\n")

            if ir.get("risk_management"):
                parts.append("**风险管理措施**:\n")
                for measure in ir["risk_management"]:
                    parts.append(f"- {measure}\n")
                parts.append("\n")

            if ir.get("suitable_for"):
                parts.append(f"**适合人群**: {ir['suitable_for']}\n")
            if ir.get("not_suitable_for"):
                parts.append(f"**不适合人群**: {ir['not_suitable_for']}\n\n")

        # 最终结论
        if "final_verdict" in conclusion:
            fv = conclusion["final_verdict"]
            parts.append("### 🏁 最终结论\n\n")
            parts.append(f"**结论**: {fv.get('verdict', '未知')}\n")
            parts.append(f"**确信度**: {fv.get('conviction_level', '未知')}\n")
            parts.append(f"**时间期限**: {fv.get('time_horizon', '未知')}\n")
            parts.append(f"**预期收益**: {fv.get('expected_return', '未知')}\n")
            parts.append(f"**最大回撤风险**: {fv.get('max_drawdown_risk', '未知')}\n")
            parts.append(f"**风险收益比**: {fv.get('risk_reward_ratio', 0):.2f}\n\n")

            if fv.get("summary"):
                parts.append(f"**总结**: {fv['summary']}\n\n")

        return "".join(parts)

    def _build_disclaimer(self) -> str:
        """构建免责声明"""
        return """## ⚠️ 免责声明

本报告由 AI 自动生成，仅供参考，不构成投资建议。加密货币市场波动性极大，投资有风险，入市需谨慎。

**重要提示**:
- 本报告基于公开数据和 AI 分析生成，可能存在数据延迟或分析偏差
- 加密货币投资风险极高，可能导致本金全部损失
- 请在投资前进行独立研究，必要时咨询专业金融顾问
- 过往表现不代表未来收益
- 本报告不应作为买入、卖出或持有任何加密货币的依据
"""

    def _build_metadata(self, analyses: Dict[str, Any]) -> str:
        """构建报告元数据"""
        parts = ["## 📊 报告元数据\n\n"]

        # 数据来源（增强版 - 学术引用风格）
        data_sources = analyses.get("data_sources", [])
        if data_sources:
            parts.append("### 📚 数据来源与参考文献\n\n")
            parts.append("*本报告综合以下可信数据源，确保信息准确性和时效性*\n\n")

            # 数据源映射（增强的详细信息）
            source_details = {
                "CoinGecko": {
                    "name": "CoinGecko",
                    "url": "https://www.coingecko.com",
                    "description": "全球最大的加密货币数据聚合平台，提供实时价格、市值、交易量等市场数据",
                    "category": "Market Data"
                },
                "Etherscan": {
                    "name": "Etherscan",
                    "url": "https://etherscan.io",
                    "description": "以太坊区块链浏览器，提供链上交易、智能合约、持有者分布等数据",
                    "category": "On-chain Data"
                },
                "Twitter": {
                    "name": "Twitter/X",
                    "url": "https://twitter.com",
                    "description": "社交媒体平台，用于分析社区讨论热度、项目官方动态和KOL观点",
                    "category": "Social Sentiment"
                },
                "Reddit": {
                    "name": "Reddit",
                    "url": "https://reddit.com",
                    "description": "全球最大的加密货币社区论坛，反映真实用户观点和讨论趋势",
                    "category": "Community Sentiment"
                },
                "CryptoPanic": {
                    "name": "CryptoPanic",
                    "url": "https://cryptopanic.com",
                    "description": "加密货币新闻聚合器，汇总全球主流媒体的最新资讯",
                    "category": "News & Media"
                }
            }

            # 按类别分组显示
            categories = {}
            for source in data_sources:
                detail = source_details.get(source, {
                    "name": source,
                    "url": "#",
                    "description": "数据提供方",
                    "category": "Other"
                })
                category = detail["category"]
                if category not in categories:
                    categories[category] = []
                categories[category].append(detail)

            # 生成引用列表
            ref_index = 1
            for category in sorted(categories.keys()):
                parts.append(f"#### {category}\n\n")
                for detail in categories[category]:
                    parts.append(f"[{ref_index}] **{detail['name']}**  \n")
                    parts.append(f"   {detail['description']}  \n")
                    parts.append(f"   🔗 [{detail['url']}]({detail['url']})  \n")
                    parts.append(f"   📅 访问时间: {analyses.get('timestamp', 'N/A')}\n\n")
                    ref_index += 1

            parts.append("---\n\n")

        # 使用的模型
        models_used = analyses.get("models_used", {})
        if models_used:
            parts.append("### AI 模型\n\n")
            for task, model in models_used.items():
                parts.append(f"- **{task}**: {model}\n")
            parts.append("\n")

        # 生成统计
        generation_time = analyses.get("generation_time", 0)
        quality_score = analyses.get("quality_score", 0)

        parts.append("### 生成统计\n\n")
        parts.append(f"- **报告生成耗时**: {generation_time:.2f} 秒\n")
        parts.append(f"- **质量得分**: {quality_score}/100\n\n")

        # 版权信息
        parts.append("---\n\n")
        parts.append("*本报告由 [Web3 AI Search Engine](https://github.com/your-repo) 生成*\n")

        return "".join(parts)


# ================================
# 全局实例
# ================================

markdown_builder = MarkdownBuilder()
