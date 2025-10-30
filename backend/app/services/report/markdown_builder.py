"""
专业级 Markdown 报告生成器
基于机构级研究报告标准，提供完整的结构化报告生成能力

✨ 核心特性：
- 自动目录生成与锚点链接系统
- 专业报告结构模板（标题、章节、附录）
- 丰富的图表和表格嵌入
- 标准化格式规范和样式指南
- 多维度内容组织系统
- 报告质量验证和一致性检查

本模块为Web3投资研究提供机构级报告生成服务。
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

from app.services.report.table_generator import table_generator
from app.services.report.chart_generator import chart_generator


class MarkdownBuilder:
    """
    专业级 Markdown 报告构建器
    基于机构级研究报告标准，提供完整的结构化报告生成能力

    核心特性：
    - 自动目录生成与锚点链接系统
    - 专业报告结构模板和样式指南
    - 标准化格式规范和质量控制
    - 模块化组件系统
    """

    # 报告结构模板定义
    REPORT_STRUCTURE = {
        "front_matter": {
            "title_page": True,
            "table_of_contents": True,
            "executive_summary": True
        },
        "main_content": {
            "tldr": True,
            "timeframe_analysis": True,
            "sentiment_analysis": True,
            "technical_analysis": True,
            "onchain_analysis": True,
            "competitor_analysis": True,
            "tokenomics_analysis": True,
            "risk_assessment": True,
            "conclusion": True
        },
        "back_matter": {
            "disclaimer": True,
            "metadata": True,
            "references": True
        }
    }

    # 样式指南定义
    STYLE_GUIDELINES = {
        "headers": {
            "h1": {"prefix": "# ", "underline": False, "anchor": True},
            "h2": {"prefix": "## ", "underline": False, "anchor": True},
            "h3": {"prefix": "### ", "underline": False, "anchor": False},
            "h4": {"prefix": "#### ", "underline": False, "anchor": False},
        },
        "text_formatting": {
            "bold": "**{}**",
            "italic": "*{}*",
            "highlight": "`{}`",
            "code_block": "```\n{}\n```",
            "blockquote": "> {}",
        },
        "lists": {
            "bullet": "- {}",
            "numbered": "{}. {}",
            "checklist": "- [{}] {}",
        },
        "tables": {
            "alignment": {"left": ":---", "center": ":---:", "right": "---:"},
            "max_columns": 8,
            "min_rows": 1,
        },
        "callouts": {
            "info": "> ℹ️ **信息**: {}",
            "warning": "> ⚠️ **警告**: {}",
            "success": "> ✅ **成功**: {}",
            "error": "> ❌ **错误**: {}",
            "tip": "> 💡 **提示**: {}",
        }
    }

    def __init__(self):
        """初始化专业级 Markdown 构建器"""
        self.sections = []  # 存储章节信息
        self.toc_enabled = True  # 是否启用目录生成
        self.anchors_enabled = True  # 是否启用锚点链接
        self.formatting_enabled = True  # 是否启用格式优化
        self.compact_mode = False  # 是否启用紧凑模式
        self.quality_checks = True  # 是否启用质量检查
        self.style_guide_enabled = True  # 是否启用样式指南

        # 表格和图表生成器
        self.table_generator = table_generator
        self.chart_generator = chart_generator

        # 组件系统
        self.components = {}  # 已注册的组件
        self.component_config = {}  # 组件配置
        self._register_default_components()

        # 元数据和版本管理
        self.report_metadata = {}  # 报告元数据
        self.version_history = []  # 版本历史
        self.current_version = "1.0.0"  # 当前版本
        self.change_log = []  # 变更日志

    def _register_default_components(self):
        """
        注册默认的报告组件
        """
        # 核心组件
        self.register_component("header", ReportHeaderComponent())
        self.register_component("toc", TableOfContentsComponent())
        self.register_component("tldr", TLDRComponent())
        self.register_component("timeframe", TimeframeAnalysisComponent())
        self.register_component("sentiment", SentimentAnalysisComponent())
        self.register_component("technical", TechnicalAnalysisComponent())
        self.register_component("onchain", OnchainAnalysisComponent())
        self.register_component("competitor", CompetitorAnalysisComponent())
        self.register_component("tokenomics", TokenomicsAnalysisComponent())
        self.register_component("risk", RiskAssessmentComponent())
        self.register_component("conclusion", ConclusionComponent())
        self.register_component("disclaimer", DisclaimerComponent())
        self.register_component("metadata", MetadataComponent())

    def register_component(self, name: str, component: 'ReportComponent'):
        """
        注册报告组件

        Args:
            name: 组件名称
            component: 组件实例
        """
        self.components[name] = component
        self.component_config[name] = component.get_default_config()

    def configure_component(self, name: str, config: Dict[str, Any]):
        """
        配置组件

        Args:
            name: 组件名称
            config: 配置字典
        """
        if name in self.component_config:
            self.component_config[name].update(config)
        else:
            self.component_config[name] = config

    def render_component(self, name: str, data: Dict[str, Any], **kwargs) -> str:
        """
        渲染组件

        Args:
            name: 组件名称
            data: 组件数据
            **kwargs: 额外参数（可包含analyzer_outputs）

        Returns:
            str: 渲染后的Markdown内容
        """
        if name not in self.components:
            return f"<!-- 组件 '{name}' 未找到 -->"

        component = self.components[name]
        config = self.component_config.get(name, {})

        try:
            # 确保analyzer_outputs传递给组件
            if "analyzer_outputs" not in kwargs and isinstance(data, dict):
                analyzer_outputs = data.get("analyzer_outputs") or kwargs.get("analyzer_outputs")
                if analyzer_outputs:
                    kwargs["analyzer_outputs"] = analyzer_outputs
            
            return component.render(data, config, self, **kwargs)
        except Exception as e:
            if self.quality_checks:
                print(f"⚠️ 组件 '{name}' 渲染失败: {str(e)}")
            return f"<!-- 组件 '{name}' 渲染失败: {str(e)} -->"

    def generate_table_from_analyzer(self, analyzer_key: str, analyzer_outputs: Dict[str, Any], table_type: str = None) -> str:
        """
        从analyzer输出生成表格

        Args:
            analyzer_key: analyzer的键名（如 "competitor", "technical"）
            analyzer_outputs: analyzer输出字典
            table_type: 表格类型（如 "competitor_comparison", "valuation_multiples"），如果为None则自动推断

        Returns:
            str: Markdown格式的表格，如果失败则返回空字符串
        """
        if not analyzer_outputs or analyzer_key not in analyzer_outputs:
            return ""

        analyzer_data = analyzer_outputs[analyzer_key].get("data", {})
        if not analyzer_data or analyzer_data.get("error"):
            return ""

        try:
            if analyzer_key == "competitor":
                if table_type == "valuation_multiples":
                    return self.table_generator.generate_valuation_table(analyzer_data)
                else:
                    return self.table_generator.generate_competitor_table(analyzer_data)
            elif analyzer_key == "technical":
                return self.table_generator.generate_levels_table(analyzer_data)
            elif analyzer_key == "tokenomics":
                return self.table_generator.generate_unlock_table(analyzer_data)
            elif analyzer_key == "risk":
                return self.table_generator.generate_risk_matrix_table(analyzer_data)
            elif analyzer_key == "conclusion":
                return self.table_generator.generate_catalyst_calendar_table(analyzer_data)
        except Exception as e:
            if self.quality_checks:
                print(f"⚠️ 表格生成失败 ({analyzer_key}/{table_type}): {str(e)}")
            return ""

        return ""

    def generate_chart_from_analyzer(self, analyzer_key: str, analyzer_outputs: Dict[str, Any], chart_type: str = None) -> str:
        """
        从analyzer输出生成图表

        Args:
            analyzer_key: analyzer的键名（如 "timeframe", "sentiment"）
            analyzer_outputs: analyzer输出字典
            chart_type: 图表类型（如 "price_trend", "sentiment_distribution"），如果为None则自动推断

        Returns:
            str: Markdown格式的图表（Base64编码），如果失败则返回空字符串
        """
        if not analyzer_outputs or analyzer_key not in analyzer_outputs:
            return ""

        analyzer_data = analyzer_outputs[analyzer_key].get("data", {})
        if not analyzer_data or analyzer_data.get("error"):
            return ""

        try:
            if analyzer_key == "timeframe":
                return self.chart_generator.generate_price_chart(analyzer_data)
            elif analyzer_key == "sentiment":
                return self.chart_generator.generate_sentiment_chart(analyzer_data)
            elif analyzer_key == "competitor":
                if chart_type == "valuation_comparison":
                    return self.chart_generator.generate_valuation_comparison_chart(analyzer_data)
            elif analyzer_key == "risk":
                return self.chart_generator.generate_risk_heatmap(analyzer_data)
        except Exception as e:
            if self.quality_checks:
                print(f"⚠️ 图表生成失败 ({analyzer_key}/{chart_type}): {str(e)}")
            return ""

        return ""

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
        根据样式指南格式化强调文本

        Args:
            text: 文本内容
            style: 样式类型 (bold, italic, highlight, code)

        Returns:
            str: 格式化的文本
        """
        if not self.formatting_enabled or not self.style_guide_enabled:
            return text

        style_templates = self.STYLE_GUIDELINES["text_formatting"]
        template = style_templates.get(style, "{}")

        if "{}" in template:
            return template.format(text)
        else:
            return text

    def format_header(self, level: int, title: str, anchor: bool = None) -> str:
        """
        根据样式指南格式化标题

        Args:
            level: 标题级别 (1-6)
            title: 标题文本
            anchor: 是否启用锚点（可选，默认为样式指南设置）

        Returns:
            str: 格式化的标题
        """
        if not self.formatting_enabled or not self.style_guide_enabled:
            return f"{'#' * level} {title}"

        header_key = f"h{level}"
        header_style = self.STYLE_GUIDELINES["headers"].get(header_key, {"prefix": f"{'#' * level} ", "anchor": False})

        prefix = header_style["prefix"]
        use_anchor = anchor if anchor is not None else (header_style.get("anchor", False) and self.anchors_enabled)

        header = f"{prefix}{title}"
        if use_anchor:
            anchor_id = self.generate_anchor_id(title)
            header += f" <a id=\"{anchor_id}\"></a>"

        return header

    def format_list_item(self, item: str, level: int = 0, style: str = "bullet", checked: bool = None) -> str:
        """
        根据样式指南格式化列表项

        Args:
            item: 列表项内容
            level: 缩进级别
            style: 列表样式 (bullet, numbered, checklist)
            checked: 清单项状态 (仅对checklist有效)

        Returns:
            str: 格式化的列表项
        """
        if not self.formatting_enabled or not self.style_guide_enabled:
            return f"{'  ' * level}- {item}"

        list_templates = self.STYLE_GUIDELINES["lists"]
        template = list_templates.get(style, "- {}")

        indent = "  " * level

        if style == "checklist" and checked is not None:
            check_mark = "x" if checked else " "
            return f"{indent}{template.format(check_mark, item)}"
        else:
            return f"{indent}{template.format(item)}"

    def format_callout(self, content: str, type: str = "info") -> str:
        """
        根据样式指南格式化提示框

        Args:
            content: 提示内容
            type: 提示类型 (info, warning, success, error, tip)

        Returns:
            str: 格式化的提示框
        """
        if not self.formatting_enabled or not self.style_guide_enabled:
            return f"{content}"

        callout_templates = self.STYLE_GUIDELINES["callouts"]
        template = callout_templates.get(type, "> ℹ️ **信息**: {}")

        if "{}" in template:
            return template.format(content)
        else:
            return content

    def format_table(self, headers: list, rows: list, alignments: list = None) -> str:
        """
        根据样式指南格式化表格

        Args:
            headers: 表头列表
            rows: 数据行列表
            alignments: 对齐方式列表 (left, center, right)

        Returns:
            str: 格式化的Markdown表格
        """
        if not headers or not rows:
            return ""

        if not self.formatting_enabled or not self.style_guide_enabled:
            # 基础表格格式
            table_lines = [f"| {' | '.join(headers)} |"]
            table_lines.append(f"| {' | '.join(['---'] * len(headers))} |")
            for row in rows:
                table_lines.append(f"| {' | '.join(str(cell) for cell in row)} |")
            return "\n".join(table_lines)

        # 检查表格规范
        max_cols = self.STYLE_GUIDELINES["tables"]["max_columns"]
        if len(headers) > max_cols:
            self._log_style_violation(f"表格列数({len(headers)})超过最大限制({max_cols})")

        min_rows = self.STYLE_GUIDELINES["tables"]["min_rows"]
        if len(rows) < min_rows:
            self._log_style_violation(f"表格行数({len(rows)})低于最小要求({min_rows})")

        # 生成对齐行
        if not alignments:
            alignments = ["left"] * len(headers)

        alignment_templates = self.STYLE_GUIDELINES["tables"]["alignment"]
        separator_row = []
        for align in alignments:
            separator_row.append(alignment_templates.get(align, ":---"))

        # 构建表格
        table_lines = [f"| {' | '.join(headers)} |"]
        table_lines.append(f"| {' | '.join(separator_row)} |")

        for row in rows:
            # 确保行数据长度匹配表头
            while len(row) < len(headers):
                row.append("")
            row_data = row[:len(headers)]  # 截断多余列
            table_lines.append(f"| {' | '.join(str(cell) for cell in row_data)} |")

        return "\n".join(table_lines)

    def _log_style_violation(self, message: str):
        """
        记录样式违规（用于质量控制）

        Args:
            message: 违规信息
        """
        if self.quality_checks:
            print(f"⚠️ 样式指南违规: {message}")

    def validate_markdown_syntax(self, markdown_content: str) -> Dict[str, Any]:
        """
        验证Markdown语法正确性

        Args:
            markdown_content: Markdown内容

        Returns:
            Dict: 验证结果
        """
        issues = []
        score = 100

        # 检查标题层级
        lines = markdown_content.split('\n')
        header_levels = []

        for line in lines:
            if line.startswith('#'):
                level = len(line.split()[0]) if line.split() else 0
                header_levels.append(level)

                # 检查标题层级跳跃
                if len(header_levels) > 1:
                    prev_level = header_levels[-2]
                    if level > prev_level + 1:
                        issues.append(f"标题层级跳跃: 从H{prev_level}直接到H{level}")
                        score -= 5

        # 检查表格格式
        table_pattern = r'\|.*\|.*\|\n\|.*:?-+:?.*\|'
        if not re.search(table_pattern, markdown_content, re.MULTILINE):
            pass  # 表格检查可以更复杂，这里简化

        # 检查链接格式
        link_pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
        invalid_links = []
        for match in re.finditer(link_pattern, markdown_content):
            link_text, url = match.groups()
            if not url or url.strip() == "":
                invalid_links.append(link_text)

        if invalid_links:
            issues.append(f"发现{len(invalid_links)}个无效链接")
            score -= len(invalid_links) * 2

        return {
            "valid": len(issues) == 0,
            "score": max(0, score),
            "issues": issues,
            "grade": self._calculate_quality_grade(score)
        }

    # ================================
    # 元数据和版本管理
    # ================================

    def set_report_metadata(self, metadata: Dict[str, Any]):
        """
        设置报告元数据

        Args:
            metadata: 元数据字典
        """
        self.report_metadata.update(metadata)

        # 设置默认元数据
        if "created_at" not in self.report_metadata:
            self.report_metadata["created_at"] = datetime.utcnow().isoformat()

        if "generator_version" not in self.report_metadata:
            self.report_metadata["generator_version"] = self.current_version

        if "template_version" not in self.report_metadata:
            self.report_metadata["template_version"] = "2.0.0"

    def get_report_metadata(self) -> Dict[str, Any]:
        """
        获取报告元数据

        Returns:
            Dict: 报告元数据
        """
        return self.report_metadata.copy()

    def update_version(self, new_version: str, changes: List[str] = None):
        """
        更新报告版本

        Args:
            new_version: 新版本号
            changes: 变更列表
        """
        # 保存当前版本到历史
        self.version_history.append({
            "version": self.current_version,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": self.report_metadata.copy(),
            "changes": self.change_log.copy()
        })

        # 更新到新版本
        self.current_version = new_version
        self.report_metadata["generator_version"] = new_version
        self.report_metadata["updated_at"] = datetime.utcnow().isoformat()

        # 添加变更记录
        if changes:
            self.change_log.extend(changes)

    def add_change_record(self, change_type: str, description: str, component: str = None):
        """
        添加变更记录

        Args:
            change_type: 变更类型 (added, modified, removed, fixed)
            description: 变更描述
            component: 受影响的组件
        """
        change_record = {
            "type": change_type,
            "description": description,
            "component": component,
            "timestamp": datetime.utcnow().isoformat(),
            "version": self.current_version
        }

        self.change_log.append(change_record)

    def get_version_history(self) -> List[Dict[str, Any]]:
        """
        获取版本历史

        Returns:
            List: 版本历史列表
        """
        return self.version_history.copy()

    def generate_version_info(self) -> str:
        """
        生成版本信息Markdown

        Returns:
            str: 版本信息Markdown
        """
        parts = ["## 📋 版本信息\n\n"]

        # 当前版本
        parts.append(f"**当前版本**: {self.current_version}\n")
        parts.append(f"**生成时间**: {self.report_metadata.get('created_at', '未知')}\n")
        parts.append(f"**最后更新**: {self.report_metadata.get('updated_at', '未知')}\n\n")

        # 版本历史
        if self.version_history:
            parts.append("### 版本历史\n\n")
            parts.append("| 版本 | 时间 | 主要变更 |\n")
            parts.append("|------|------|----------|\n")

            for version_info in reversed(self.version_history[-5:]):  # 显示最近5个版本
                version = version_info["version"]
                timestamp = version_info["timestamp"][:10]  # 只显示日期
                changes = version_info.get("changes", [])
                change_summary = changes[-1]["description"] if changes else "版本更新"
                if len(change_summary) > 50:
                    change_summary = change_summary[:47] + "..."

                parts.append(f"| {version} | {timestamp} | {change_summary} |\n")

            parts.append("\n")

        # 变更日志
        if self.change_log:
            parts.append("### 最新变更\n\n")
            for change in self.change_log[-10:]:  # 显示最近10个变更
                change_type_icons = {
                    "added": "➕",
                    "modified": "✏️",
                    "removed": "➖",
                    "fixed": "🐛"
                }
                icon = change_type_icons.get(change["type"], "📝")
                component = f" ({change['component']})" if change.get("component") else ""
                parts.append(f"{icon} {change['description']}{component}\n")
            parts.append("\n")

        # 技术规格
        parts.append("### 技术规格\n\n")
        parts.append(f"- **报告格式**: Markdown v2.0\n")
        parts.append(f"- **样式指南**: 机构级研究标准\n")
        parts.append(f"- **组件系统**: 模块化架构\n")
        parts.append(f"- **质量控制**: 自动验证\n\n")

        return "".join(parts)

    def embed_metadata_in_report(self, report_content: str) -> str:
        """
        在报告中嵌入元数据注释

        Args:
            report_content: 报告内容

        Returns:
            str: 包含元数据的报告内容
        """
        metadata_comment = f"<!--\n{self._generate_metadata_yaml()}\n-->\n\n"

        # 在报告开头插入元数据注释
        return metadata_comment + report_content

    def _generate_metadata_yaml(self) -> str:
        """
        生成YAML格式的元数据

        Returns:
            str: YAML格式元数据
        """
        import yaml

        metadata = {
            "report": {
                "version": self.current_version,
                "created_at": self.report_metadata.get("created_at"),
                "updated_at": self.report_metadata.get("updated_at"),
                "symbol": self.report_metadata.get("symbol"),
                "generator": "Web3 AI Search Engine v2.0"
            },
            "components": list(self.components.keys()),
            "quality_score": self.report_metadata.get("quality_score", 0),
            "generation_time": self.report_metadata.get("generation_time", 0),
            "data_sources": self.report_metadata.get("data_sources", [])
        }

        return yaml.dump(metadata, default_flow_style=False, allow_unicode=True)

    def validate_report_integrity(self, report_content: str) -> Dict[str, Any]:
        """
        验证报告完整性

        Args:
            report_content: 报告内容

        Returns:
            Dict: 验证结果
        """
        issues = []
        score = 100

        # 检查必要章节
        required_sections = ["TL;DR", "风险评估", "投资结论", "免责声明"]
        for section in required_sections:
            if section not in report_content:
                issues.append(f"缺少必要章节: {section}")
                score -= 20

        # 检查元数据
        if not self.report_metadata.get("created_at"):
            issues.append("缺少创建时间元数据")
            score -= 5

        if not self.report_metadata.get("symbol"):
            issues.append("缺少代币符号元数据")
            score -= 5

        # 检查版本信息
        if not self.current_version:
            issues.append("缺少版本信息")
            score -= 10

        # 检查数据源
        data_sources = self.report_metadata.get("data_sources", [])
        if len(data_sources) < 2:
            issues.append("数据源数量不足（建议至少2个）")
            score -= 10

        return {
            "valid": len(issues) == 0,
            "integrity_score": max(0, score),
            "issues": issues,
            "metadata_complete": bool(self.report_metadata),
            "version_tracked": bool(self.version_history)
        }

    def _calculate_quality_grade(self, score: int) -> str:
        """
        根据分数计算质量等级

        Args:
            score: 质量分数

        Returns:
            str: 质量等级
        """
        if score >= 95:
            return "A+"
        elif score >= 90:
            return "A"
        elif score >= 85:
            return "B+"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C+"
        elif score >= 60:
            return "C"
        else:
            return "D"


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
        构建增强版 Markdown 报告（基于组件系统）

        Args:
            analyses: 包含所有分析器输出的字典
            include_toc: 是否包含目录

        Returns:
            str: 完整的增强版 Markdown 报告
        """
        # 重置章节列表
        self.sections = []

        parts = []

        # 按照报告结构模板构建报告
        report_structure = self.REPORT_STRUCTURE

        # 前言部分
        if report_structure["front_matter"]["title_page"]:
            header_content = self.render_component("header", analyses)
            parts.append(header_content)

        if include_toc and report_structure["front_matter"]["table_of_contents"]:
            toc_content = self.render_component("toc", {})
            if toc_content:
                parts.append(toc_content)

        # 获取analyzer_outputs（如果存在）
        analyzer_outputs = analyses.get("analyzer_outputs", {})

        # 主要内容
        main_sections = [
            ("tldr", "tldr"),
            ("timeframe", "timeframe"),
            ("sentiment", "sentiment"),
            ("technical", "technical"),
            ("onchain", "onchain"),
            ("competitor", "competitor"),
            ("tokenomics", "tokenomics"),
            ("risk", "risk"),
            ("conclusion", "conclusion")
        ]

        for component_name, data_key in main_sections:
            if report_structure["main_content"].get(data_key, True):
                section_data = analyses.get(data_key, {})
                # 传递analyzer_outputs给组件
                section_content = self.render_component(
                    component_name, 
                    section_data, 
                    analyzer_outputs=analyzer_outputs
                )
                if section_content.strip():  # 只添加非空内容
                    parts.append(section_content)
                    parts.append(self.format_section_separator())

        # 结尾部分
        if report_structure["back_matter"]["disclaimer"]:
            disclaimer_content = self.render_component("disclaimer", {})
            if disclaimer_content:
                parts.append(disclaimer_content)
                parts.append(self.format_section_separator())

        if report_structure["back_matter"]["metadata"]:
            metadata_content = self.render_component("metadata", analyses)
            if metadata_content:
                parts.append(metadata_content)

        # 添加导航页脚
        if self.anchors_enabled:
            nav_footer = self.generate_navigation_footer()
            if nav_footer:
                parts.append(nav_footer)

        # 生成并插入目录
        if include_toc and self.toc_enabled and report_structure["front_matter"]["table_of_contents"]:
            toc = self.generate_table_of_contents(max_level=3)
            if toc and len(parts) > 0:
                # 将目录插入到标题后面
                header_end_pattern = "\n---\n\n"
                header_end_index = parts[0].find(header_end_pattern)
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
# 组件系统
# ================================

class ReportComponent:
    """
    报告组件基类
    所有报告组件都继承此类
    """

    def get_default_config(self) -> Dict[str, Any]:
        """
        获取组件默认配置

        Returns:
            Dict: 默认配置
        """
        return {
            "enabled": True,
            "level": 2,
            "include_in_toc": True,
            "required_data_keys": []
        }

    def validate_data(self, data: Dict[str, Any], config: Dict[str, Any]) -> bool:
        """
        验证组件数据

        Args:
            data: 组件数据
            config: 组件配置

        Returns:
            bool: 数据是否有效
        """
        required_keys = config.get("required_data_keys", [])
        return all(key in data for key in required_keys)

    def render(self, data: Dict[str, Any], config: Dict[str, Any],
               builder: 'MarkdownBuilder', **kwargs) -> str:
        """
        渲染组件

        Args:
            data: 组件数据
            config: 组件配置
            builder: Markdown构建器实例
            **kwargs: 额外参数

        Returns:
            str: 渲染后的Markdown内容
        """
        if not config.get("enabled", True):
            return ""

        if not self.validate_data(data, config):
            return builder.format_callout(
                f"组件 {self.__class__.__name__} 缺少必要数据",
                "warning"
            )

        return self._render_content(data, config, builder, **kwargs)

    def _render_content(self, data: Dict[str, Any], config: Dict[str, Any],
                       builder: 'MarkdownBuilder', **kwargs) -> str:
        """
        渲染组件内容（子类实现）

        Args:
            data: 组件数据
            config: 组件配置
            builder: Markdown构建器实例
            **kwargs: 额外参数

        Returns:
            str: 渲染后的Markdown内容
        """
        raise NotImplementedError("子类必须实现 _render_content 方法")


class ReportHeaderComponent(ReportComponent):
    """报告标题组件"""

    def get_default_config(self):
        config = super().get_default_config()
        config.update({
            "level": 1,
            "include_metadata": True,
            "include_summary": True
        })
        return config

    def _render_content(self, data, config, builder, **kwargs):
        symbol = data.get("symbol", "Unknown")
        query = data.get("query", "")
        timestamp = data.get("timestamp", datetime.utcnow().isoformat())

        parts = []

        # 主标题
        title = builder.format_header(config["level"], f"{symbol} 深度研究报告")
        parts.append(title)

        # 元数据
        if config["include_metadata"]:
            try:
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                date_str = dt.strftime("%Y年%m月%d日 %H:%M UTC")
            except:
                date_str = timestamp

            parts.append(f"**生成时间**: {builder.format_emphasis_text(date_str, 'code')}")
            parts.append(f"**用户查询**: {builder.format_emphasis_text(query, 'italic')}")
            parts.append(f"**研究机构**: {builder.format_emphasis_text('Web3 AI Search Engine', 'bold')}")
            parts.append(f"**报告类型**: {builder.format_emphasis_text('多维度深度研究报告', 'highlight')}")

        parts.append(builder.format_section_separator())

        # 报告概览
        if config["include_summary"]:
            parts.append("## 📊 报告概览\n\n")
            parts.append(builder.format_callout(
                f"本报告通过AI驱动的多维度分析引擎，为 {builder.format_emphasis_text(symbol, 'bold')} 提供全面的投资研究分析。",
                "info"
            ))

        return "\n".join(parts)


class TableOfContentsComponent(ReportComponent):
    """目录组件"""

    def get_default_config(self):
        config = super().get_default_config()
        config.update({
            "max_level": 3,
            "include_navigation": True
        })
        return config

    def _render_content(self, data, config, builder, **kwargs):
        return builder.generate_table_of_contents(config["max_level"])


class TLDRComponent(ReportComponent):
    """TL;DR摘要组件 - 核心判断和置信度"""

    def get_default_config(self):
        config = super().get_default_config()
        config.update({
            "required_data_keys": ["one_sentence"],
            "include_confidence": True,
            "include_sentiment_balance": True,
            "include_risk_reward": True,
            "confidence_levels": ["low", "medium", "high", "very_high"]
        })
        return config

    def _render_content(self, data, config, builder, **kwargs):
        parts = []

        # 核心投资论点 - 增强版
        if "one_sentence" in data:
            parts.append("### 🎯 核心投资论点\n\n")
            parts.append(f"**{data['one_sentence']}**\n\n")

            # 置信度评分
            if config["include_confidence"] and "confidence_score" in data:
                confidence_score = data["confidence_score"]
                confidence_level = self._calculate_confidence_level(confidence_score, config["confidence_levels"])
                confidence_icon = self._get_confidence_icon(confidence_level)

                parts.append(f"**置信度**: {confidence_icon} {confidence_level.title()} ({confidence_score}/100)\n\n")

        # 看涨vs看跌平衡分析
        if config["include_sentiment_balance"]:
            bull_case = data.get("bull_case", [])
            bear_case = data.get("bear_case", [])

            if bull_case or bear_case:
                parts.append("### ⚖️ 多空平衡分析\n\n")

                # 看涨理由
                if bull_case:
                    parts.append("#### 🐂 看涨理由\n\n")
                    for i, reason in enumerate(bull_case, 1):
                        parts.append(f"{i}. {reason}\n")
                    parts.append("\n")

                # 看跌理由
                if bear_case:
                    parts.append("#### 🐻 看跌理由\n\n")
                    for i, reason in enumerate(bear_case, 1):
                        parts.append(f"{i}. {reason}\n")
                    parts.append("\n")

                # 平衡评分
                balance_score = self._calculate_balance_score(bull_case, bear_case)
                balance_text = self._interpret_balance_score(balance_score)
                parts.append(f"**多空平衡**: {balance_text} ({balance_score:+.1f})\n\n")

        # 关键催化剂时间线
        if "key_catalysts" in data and data["key_catalysts"]:
            parts.append("### ⏰ 关键催化剂时间线\n\n")

            catalysts = data["key_catalysts"]
            if isinstance(catalysts, list):
                for i, catalyst in enumerate(catalysts, 1):
                    parts.append(f"{i}. {catalyst}\n")
            else:
                # 处理结构化催化剂数据
                for catalyst in catalysts:
                    if isinstance(catalyst, dict):
                        time_window = catalyst.get("time_window", "未知")
                        event = catalyst.get("event", "未知事件")
                        impact = catalyst.get("impact", "未知")
                        probability = catalyst.get("probability", "未知")

                        parts.append(f"- **[{time_window}]** {event}\n")
                        parts.append(f"  - 预期影响: {impact}\n")
                        parts.append(f"  - 发生概率: {probability}\n")
                    else:
                        parts.append(f"- {catalyst}\n")
            parts.append("\n")

        # 投资建议矩阵
        if config["include_risk_reward"] and self._has_investment_data(data):
            parts.append("### 📈 投资建议矩阵\n\n")

            # 构建建议矩阵
            matrix_data = self._build_investment_matrix(data)
            if matrix_data:
                headers = ["维度", "评估", "权重", "评分"]
                rows = []

                for dimension, assessment in matrix_data.items():
                    rows.append([
                        dimension,
                        assessment.get("assessment", "未知"),
                        f"{assessment.get('weight', 0)}%",
                        assessment.get("score", 0)
                    ])

                matrix_table = builder.format_table(headers, rows)
                parts.append(matrix_table)
                parts.append("\n")

                # 计算综合评分
                total_score = sum(item.get("score", 0) * item.get("weight", 0) / 100 for item in matrix_data.values())
                recommendation = self._generate_recommendation(total_score)

                parts.append(f"**综合评分**: {total_score:.1f}/100\n")
                parts.append(f"**投资建议**: {recommendation}\n\n")

        # 快速参考面板
        if config["include_confidence"]:
            parts.append("### 📋 快速参考\n\n")
            quick_ref = self._build_quick_reference(data)
            for key, value in quick_ref.items():
                parts.append(f"- **{key}**: {value}\n")
            parts.append("\n")

        return "".join(parts)

    def _calculate_confidence_level(self, score: int, levels: list) -> str:
        """计算置信度等级"""
        if score >= 90:
            return levels[3] if len(levels) > 3 else "high"
        elif score >= 75:
            return levels[2] if len(levels) > 2 else "medium"
        elif score >= 60:
            return levels[1] if len(levels) > 1 else "medium"
        else:
            return levels[0] if levels else "low"

    def _get_confidence_icon(self, level: str) -> str:
        """获取置信度图标"""
        icons = {
            "very_high": "🟢",
            "high": "🟡",
            "medium": "🟠",
            "low": "🔴"
        }
        return icons.get(level, "⚪")

    def _calculate_balance_score(self, bull_case: list, bear_case: list) -> float:
        """计算多空平衡评分 (-100 到 +100)"""
        bull_weight = len(bull_case) * 1.2  # 看涨理由权重稍高
        bear_weight = len(bear_case) * 1.0

        if bull_weight + bear_weight == 0:
            return 0

        balance = (bull_weight - bear_weight) / (bull_weight + bear_weight) * 100
        return round(balance, 1)

    def _interpret_balance_score(self, score: float) -> str:
        """解释平衡评分"""
        if score > 30:
            return "强烈看涨 🐂"
        elif score > 10:
            return "温和看涨 📈"
        elif score > -10:
            return "中性平衡 ⚖️"
        elif score > -30:
            return "温和看跌 📉"
        else:
            return "强烈看跌 🐻"

    def _has_investment_data(self, data: dict) -> bool:
        """检查是否有投资相关数据"""
        investment_keys = ["risk_level", "investment_horizon", "expected_return", "max_drawdown"]
        return any(key in data for key in investment_keys)

    def _build_investment_matrix(self, data: dict) -> dict:
        """构建投资建议矩阵"""
        matrix = {}

        # 风险评估
        if "risk_level" in data:
            risk_score = self._quantify_risk_level(data["risk_level"])
            matrix["风险水平"] = {
                "assessment": data["risk_level"],
                "weight": 25,
                "score": risk_score
            }

        # 时间期限
        if "investment_horizon" in data:
            horizon_score = self._quantify_time_horizon(data["investment_horizon"])
            matrix["时间期限"] = {
                "assessment": data["investment_horizon"],
                "weight": 20,
                "score": horizon_score
            }

        # 预期收益
        if "expected_return" in data:
            return_score = min(100, max(0, float(data["expected_return"].strip("%")) * 2))
            matrix["预期收益"] = {
                "assessment": data["expected_return"],
                "weight": 30,
                "score": return_score
            }

        # 最大回撤
        if "max_drawdown" in data:
            drawdown_score = 100 - min(100, abs(float(data["max_drawdown"].strip("%"))))
            matrix["最大回撤"] = {
                "assessment": data["max_drawdown"],
                "weight": 25,
                "score": drawdown_score
            }

        return matrix

    def _quantify_risk_level(self, risk_level: str) -> int:
        """量化风险等级"""
        risk_map = {
            "极低": 90,
            "低": 75,
            "中等": 50,
            "高": 25,
            "极高": 10
        }
        return risk_map.get(risk_level, 50)

    def _quantify_time_horizon(self, horizon: str) -> int:
        """量化时间期限"""
        horizon_map = {
            "短期(1-3月)": 70,
            "中期(3-6月)": 80,
            "长期(6-12月)": 90,
            "超长期(1年以上)": 95
        }
        return horizon_map.get(horizon, 50)

    def _generate_recommendation(self, total_score: float) -> str:
        """生成投资建议"""
        if total_score >= 85:
            return "强烈推荐 🟢"
        elif total_score >= 70:
            return "推荐 🟡"
        elif total_score >= 55:
            return "观望 🟠"
        elif total_score >= 40:
            return "谨慎 🔴"
        else:
            return "不推荐 ⚫"

    def _build_quick_reference(self, data: dict) -> dict:
        """构建快速参考面板"""
        ref = {}

        if "symbol" in data:
            ref["代币符号"] = data["symbol"]

        if "current_price" in data:
            ref["当前价格"] = f"${data['current_price']:,.2f}"

        if "confidence_score" in data:
            ref["置信度"] = f"{data['confidence_score']}/100"

        if "risk_level" in data:
            ref["风险等级"] = data["risk_level"]

        if "investment_horizon" in data:
            ref["建议期限"] = data["investment_horizon"]

        return ref


class TimeframeAnalysisComponent(ReportComponent):
    """时间窗分析组件 - 多维度时间序列分析"""

    def get_default_config(self):
        config = super().get_default_config()
        config.update({
            "include_chart": True,
            "timeframes": ["24h", "7d", "30d"],
            "include_momentum_analysis": True,
            "include_regime_detection": True,
            "include_seasonal_patterns": True,
            "max_events_per_window": 5
        })
        return config

    def _render_content(self, data, config, builder, **kwargs):
        parts = []

        # 生成价格趋势图（如果启用且analyzer_outputs可用）
        if config["include_chart"]:
            analyzer_outputs = kwargs.get("analyzer_outputs") or data.get("analyzer_outputs", {})
            if analyzer_outputs and "timeframe" in analyzer_outputs:
                chart_markdown = builder.generate_chart_from_analyzer("timeframe", analyzer_outputs)
                if chart_markdown:
                    parts.append("### 📈 价格走势图\n\n")
                    parts.append(chart_markdown)
                    parts.append("\n")

        # 市场动量概览
        if config["include_momentum_analysis"] and "overall_momentum" in data:
            parts.append("### 📊 市场动量概览\n\n")
            momentum = data["overall_momentum"]
            momentum_icon = self._get_momentum_icon(momentum)
            parts.append(f"**整体动量**: {momentum_icon} {momentum}\n\n")

            # 动量强度分析
            momentum_score = self._quantify_momentum(momentum)
            parts.append(f"**动量强度**: {momentum_score}/100\n\n")

        # 趋势转折检测
        if config["include_regime_detection"] and data.get("regime_shift"):
            parts.append("### 🔄 趋势转折检测\n\n")
            regime_info = data.get("regime_shift_description", "检测到趋势变化")
            parts.append(f"**转折信号**: {regime_info}\n\n")

            # 转折概率
            if "regime_shift_probability" in data:
                prob = data["regime_shift_probability"]
                prob_icon = "🟢" if prob > 70 else "🟡" if prob > 50 else "🔴"
                parts.append(f"**转折概率**: {prob_icon} {prob}%\n\n")

        # 多时间窗深度分析
        if "windows" in data and data["windows"]:
            parts.append("### ⏱️ 多时间窗深度分析\n\n")

            # 时间窗优先级排序
            timeframe_priority = {"24h": 0, "7d": 1, "30d": 2}
            sorted_windows = sorted(
                data["windows"],
                key=lambda w: timeframe_priority.get(w.get('timeframe', ''), 99)
            )

            for window in sorted_windows:
                timeframe = window.get('timeframe', '未知时间窗')
                if timeframe in config["timeframes"]:
                    parts.append(f"#### {timeframe} 时间窗\n\n")

                    # 趋势分析
                    trend = window.get('trend', '未知')
                    trend_icon = self._get_trend_icon(trend)
                    parts.append(f"**趋势方向**: {trend_icon} {trend}\n")

                    # 趋势强度
                    if "trend_strength" in window:
                        strength = window["trend_strength"]
                        strength_icon = "🟢" if strength > 70 else "🟡" if strength > 40 else "🔴"
                        parts.append(f"**趋势强度**: {strength_icon} {strength}/100\n")

                    parts.append("\n")

                    # 量化指标面板
                    metrics = window.get("metrics", {})
                    if metrics:
                        parts.append("##### 📈 量化指标\n\n")
                        metrics_table = self._build_metrics_table(metrics, builder)
                        parts.append(metrics_table)
                        parts.append("\n")

                    # 关键事件时间线
                    if window.get("key_events"):
                        parts.append("##### 📅 关键事件时间线\n\n")
                        events = window["key_events"][:config["max_events_per_window"]]
                        for i, event in enumerate(events, 1):
                            parts.append(f"{i}. {event}\n")
                        parts.append("\n")

                    # 支撑阻力分析
                    if window.get("support_resistance"):
                        sr_data = window["support_resistance"]
                        parts.append("##### 📊 支撑阻力分析\n\n")
                        sr_table = self._build_support_resistance_table(sr_data, builder)
                        parts.append(sr_table)
                        parts.append("\n")

        # 季节性模式识别
        if config["include_seasonal_patterns"] and data.get("seasonal_patterns"):
            parts.append("### 📅 季节性模式识别\n\n")
            patterns = data["seasonal_patterns"]
            for pattern in patterns:
                pattern_name = pattern.get("pattern", "未知模式")
                strength = pattern.get("strength", 0)
                description = pattern.get("description", "")

                strength_icon = "🟢" if strength > 70 else "🟡" if strength > 40 else "🔴"
                parts.append(f"- **{pattern_name}**: {strength_icon} 强度 {strength}/100\n")
                if description:
                    parts.append(f"  - {description}\n")
            parts.append("\n")

        # 综合趋势评估
        if data.get("trend_summary"):
            parts.append("### 🎯 综合趋势评估\n\n")
            summary = data["trend_summary"]

            # 趋势一致性评分
            if "consistency_score" in summary:
                consistency = summary["consistency_score"]
                consistency_icon = "🟢" if consistency > 80 else "🟡" if consistency > 60 else "🔴"
                parts.append(f"**趋势一致性**: {consistency_icon} {consistency}/100\n\n")

            # 主要驱动因素
            if "key_drivers" in summary:
                parts.append("**主要驱动因素**:\n\n")
                for driver in summary["key_drivers"]:
                    parts.append(f"- {driver}\n")
                parts.append("\n")

            # 前瞻性展望
            if "forward_looking" in summary:
                parts.append(f"**前瞻性展望**: {summary['forward_looking']}\n\n")

        return "".join(parts)

    def _get_momentum_icon(self, momentum: str) -> str:
        """获取动量图标"""
        momentum_icons = {
            "极强上涨": "🚀",
            "强上涨": "📈",
            "温和上涨": "↗️",
            "横盘震荡": "➡️",
            "温和下跌": "↘️",
            "强下跌": "📉",
            "极强下跌": "💥"
        }
        return momentum_icons.get(momentum, "⚪")

    def _quantify_momentum(self, momentum: str) -> int:
        """量化动量强度"""
        momentum_scores = {
            "极强上涨": 95,
            "强上涨": 80,
            "温和上涨": 65,
            "横盘震荡": 50,
            "温和下跌": 35,
            "强下跌": 20,
            "极强下跌": 5
        }
        return momentum_scores.get(momentum, 50)

    def _get_trend_icon(self, trend: str) -> str:
        """获取趋势图标"""
        trend_icons = {
            "强势上涨": "🟢",
            "上涨": "↗️",
            "横盘": "➡️",
            "下跌": "↘️",
            "强势下跌": "🔴",
            "震荡": "🔄"
        }
        return trend_icons.get(trend, "⚪")

    def _build_metrics_table(self, metrics: dict, builder) -> str:
        """构建量化指标表格"""
        headers = ["指标", "数值", "解读"]
        rows = []

        if metrics.get("price_change_pct") is not None:
            change = metrics["price_change_pct"]
            interpretation = "上涨" if change > 0 else "下跌" if change < 0 else "持平"
            rows.append(["价格变化", f"{change:+.2f}%", interpretation])

        if metrics.get("volume_change_pct") is not None:
            vol_change = metrics["volume_change_pct"]
            vol_interp = "放量" if vol_change > 20 else "缩量" if vol_change < -20 else "正常"
            rows.append(["成交量变化", f"{vol_change:+.2f}%", vol_interp])

        if metrics.get("volatility") is not None:
            vol = metrics["volatility"]
            vol_interp = "高波动" if vol > 5 else "正常波动" if vol > 2 else "低波动"
            rows.append(["波动率", f"{vol:.2f}%", vol_interp])

        if metrics.get("sentiment_score") is not None:
            sent = metrics["sentiment_score"]
            sent_interp = "乐观" if sent > 60 else "中性" if sent > 40 else "悲观"
            rows.append(["情绪得分", f"{sent:.1f}/100", sent_interp])

        if metrics.get("fear_greed_index") is not None:
            fgi = metrics["fear_greed_index"]
            fgi_interp = "贪婪" if fgi > 75 else "恐惧" if fgi < 25 else "中性"
            rows.append(["恐惧贪婪指数", f"{fgi}/100", fgi_interp])

        return builder.format_table(headers, rows) if rows else ""

    def _build_support_resistance_table(self, sr_data: dict, builder) -> str:
        """构建支撑阻力表格"""
        headers = ["类型", "价位", "强度", "测试次数"]
        rows = []

        if "resistance_levels" in sr_data:
            for level in sr_data["resistance_levels"][:3]:  # 最多显示3个
                price = level.get("price", 0)
                strength = level.get("strength", 0)
                tests = level.get("tests", 0)
                strength_text = "强" if strength > 70 else "中" if strength > 40 else "弱"
                rows.append(["阻力位", f"${price:,.4f}", strength_text, str(tests)])

        if "support_levels" in sr_data:
            for level in sr_data["support_levels"][:3]:  # 最多显示3个
                price = level.get("price", 0)
                strength = level.get("strength", 0)
                tests = level.get("tests", 0)
                strength_text = "强" if strength > 70 else "中" if strength > 40 else "弱"
                rows.append(["支撑位", f"${price:,.4f}", strength_text, str(tests)])

        return builder.format_table(headers, rows) if rows else ""


class SentimentAnalysisComponent(ReportComponent):
    """情绪分析组件 - 量化情绪和趋势追踪"""

    def get_default_config(self):
        config = super().get_default_config()
        config.update({
            "include_chart": True,
            "include_social_metrics": True,
            "include_sentiment_trends": True,
            "include_fomo_fear_analysis": True,
            "include_influencer_analysis": True,
            "include_sentiment_drivers": True,
            "max_topics": 10
        })
        return config

    def _render_content(self, data, config, builder, **kwargs):
        parts = []

        # 情绪概览仪表盘
        parts.append("### 😊 情绪概览仪表盘\n\n")

        # 整体情绪评分
        if "sentiment_score" in data:
            score = data["sentiment_score"]
            sentiment_level = self._classify_sentiment_level(score)
            sentiment_icon = self._get_sentiment_icon(sentiment_level)
            
            parts.append(f"**综合情绪得分**: {sentiment_icon} {score:.1f}/100 ({sentiment_level})\n\n")

        if "overall_sentiment" in data:
            parts.append(f"**情绪描述**: {data['overall_sentiment']}\n\n")

        # FOMO和恐慌指数
        if config["include_fomo_fear_analysis"]:
            parts.append("### 📊 FOMO与恐慌指数\n\n")

            if "fomo_index" in data:
                fomo = data["fomo_index"]
                fomo_level = self._classify_fomo_level(fomo)
                fomo_icon = self._get_fomo_icon(fomo_level)
                parts.append(f"**FOMO指数**: {fomo_icon} {fomo}/100 ({fomo_level})\n")

            if "fear_index" in data:
                fear = data["fear_index"]
                fear_level = self._classify_fear_level(fear)
                fear_icon = self._get_fear_icon(fear_level)
                parts.append(f"**恐慌指数**: {fear_icon} {fear}/100 ({fear_level})\n")

            if "fomo_index" in data and "fear_index" in data:
                market_state = self._analyze_market_state(data["fomo_index"], data["fear_index"])
                parts.append(f"**市场状态**: {market_state}\n")

            parts.append("\n")

        # 社交媒体平台详细分析
        if config["include_social_metrics"] and "social_metrics" in data and data["social_metrics"]:
            parts.append("### 📱 社交媒体平台分析\n\n")

            # 构建社交媒体对比表格
            social_table = self._build_social_metrics_table(data["social_metrics"], builder)
            parts.append(social_table)
            parts.append("\n")

            # 各平台详细数据
            for metric in data["social_metrics"]:
                platform = metric.get("platform", "未知平台")
                parts.append(f"#### {platform} 详细数据\n\n")

                # 提及数据
                parts.append(f"- **提及次数**: {metric.get('mention_count', 0):,}\n")
                parts.append(f"- **活跃用户**: {metric.get('active_users', 0):,}\n")
                parts.append(f"- **互动数**: {metric.get('interactions', 0):,}\n")

                # 情绪分析
                sentiment_score = metric.get('sentiment_score', 0)
                sentiment_icon = self._get_sentiment_icon_by_score(sentiment_score)
                parts.append(f"- **情绪得分**: {sentiment_icon} {sentiment_score:.2f} (-1到+1)\n")

                # 互动率
                engagement_rate = metric.get('engagement_rate', 0)
                engagement_icon = "🟢" if engagement_rate > 5 else "🟡" if engagement_rate > 2 else "🔴"
                parts.append(f"- **互动率**: {engagement_icon} {engagement_rate:.2f}%\n")

                # 热门话题
                if metric.get("top_topics"):
                    parts.append("- **热门话题**:\n")
                    for topic in metric["top_topics"][:config["max_topics"]]:
                        parts.append(f"  - {topic}\n")

                parts.append("\n")

        # 情绪趋势分析
        if config["include_sentiment_trends"] and "sentiment_trends" in data:
            trends = data["sentiment_trends"]
            parts.append("### 📈 情绪趋势分析\n\n")

            # 趋势方向
            if "trend_direction" in trends:
                direction = trends["trend_direction"]
                direction_icon = "📈" if direction == "上升" else "📉" if direction == "下降" else "➡️"
                parts.append(f"**趋势方向**: {direction_icon} {direction}\n")

            # 趋势强度
            if "trend_strength" in trends:
                strength = trends["trend_strength"]
                strength_icon = "🟢" if strength > 70 else "🟡" if strength > 40 else "🔴"
                parts.append(f"**趋势强度**: {strength_icon} {strength}/100\n")

            # 情绪变化速度
            if "change_velocity" in trends:
                velocity = trends["change_velocity"]
                velocity_text = "快速变化" if abs(velocity) > 20 else "温和变化" if abs(velocity) > 10 else "稳定"
                parts.append(f"**变化速度**: {velocity_text} ({velocity:+.1f}/天)\n")

            parts.append("\n")

            # 情绪历史趋势表格
            if "historical_data" in trends:
                parts.append("#### 📊 历史情绪趋势\n\n")
                history_table = self._build_sentiment_history_table(trends["historical_data"], builder)
                parts.append(history_table)
                parts.append("\n")

        # 情绪驱动因素
        if config["include_sentiment_drivers"] and "sentiment_drivers" in data:
            drivers = data["sentiment_drivers"]
            parts.append("### 🔍 情绪驱动因素分析\n\n")

            if drivers:
                # 分类展示驱动因素
                positive_drivers = [d for d in drivers if d.get("impact", 0) > 0]
                negative_drivers = [d for d in drivers if d.get("impact", 0) < 0]

                if positive_drivers:
                    parts.append("#### ✅ 正面驱动因素\n\n")
                    for driver in positive_drivers[:5]:
                        impact = driver.get("impact", 0)
                        description = driver.get("description", "未知")
                        parts.append(f"- **{description}** (影响: +{impact:.1f})\n")
                    parts.append("\n")

                if negative_drivers:
                    parts.append("#### ⚠️ 负面驱动因素\n\n")
                    for driver in negative_drivers[:5]:
                        impact = driver.get("impact", 0)
                        description = driver.get("description", "未知")
                        parts.append(f"- **{description}** (影响: {impact:.1f})\n")
                    parts.append("\n")
            else:
                parts.append("暂无明确的情绪驱动因素\n\n")

        # 意见领袖分析
        if config["include_influencer_analysis"] and "influencer_sentiment" in data:
            influencers = data["influencer_sentiment"]
            parts.append("### 👥 意见领袖情绪分析\n\n")

            if influencers:
                # 构建KOL情绪汇总表格
                kol_table = self._build_influencer_table(influencers, builder)
                parts.append(kol_table)
                parts.append("\n")

                # 总体KOL情绪
                avg_kol_sentiment = sum(item.get("sentiment", 0) for item in influencers) / len(influencers)
                kol_icon = "🟢" if avg_kol_sentiment > 0.3 else "🔴" if avg_kol_sentiment < -0.3 else "🟡"
                parts.append(f"**KOL平均情绪**: {kol_icon} {avg_kol_sentiment:+.2f}\n\n")
            else:
                parts.append("暂无意见领袖数据\n\n")

        # 情绪分布可视化
        if config["include_chart"]:
            analyzer_outputs = kwargs.get("analyzer_outputs") or data.get("analyzer_outputs", {})
            if analyzer_outputs and "sentiment" in analyzer_outputs:
                chart_markdown = builder.generate_chart_from_analyzer("sentiment", analyzer_outputs)
                if chart_markdown:
                    parts.append("### 📊 情绪分布可视化\n\n")
                    parts.append("#### 情绪分布饼图\n\n")
                    parts.append(chart_markdown)
                    parts.append("\n")

        # 情绪预测
        if "sentiment_forecast" in data:
            forecast = data["sentiment_forecast"]
            parts.append("### 🔮 情绪预测\n\n")

            if "next_7d" in forecast:
                next_7d = forecast["next_7d"]
                forecast_icon = "📈" if next_7d > 0 else "📉" if next_7d < 0 else "➡️"
                parts.append(f"**7天预测**: {forecast_icon} {next_7d:+.1f}\n")

            if "confidence" in forecast:
                confidence = forecast["confidence"]
                conf_icon = "🟢" if confidence > 70 else "🟡" if confidence > 50 else "🔴"
                parts.append(f"**预测置信度**: {conf_icon} {confidence}%\n")

            parts.append("\n")

        return "".join(parts)

    def _classify_sentiment_level(self, score: float) -> str:
        """分类情绪等级"""
        if score >= 75:
            return "极度乐观"
        elif score >= 60:
            return "乐观"
        elif score >= 45:
            return "中性偏乐观"
        elif score >= 30:
            return "中性"
        elif score >= 15:
            return "中性偏悲观"
        elif score >= 0:
            return "悲观"
        else:
            return "极度悲观"

    def _get_sentiment_icon(self, level: str) -> str:
        """获取情绪图标"""
        icons = {
            "极度乐观": "🟢🟢",
            "乐观": "🟢",
            "中性偏乐观": "🟡🟢",
            "中性": "🟡",
            "中性偏悲观": "🟡🔴",
            "悲观": "🔴",
            "极度悲观": "🔴🔴"
        }
        return icons.get(level, "⚪")

    def _get_sentiment_icon_by_score(self, score: float) -> str:
        """根据得分获取情绪图标"""
        if score > 0.5:
            return "🟢"
        elif score > 0.2:
            return "🟡"
        elif score > -0.2:
            return "⚪"
        elif score > -0.5:
            return "🟠"
        else:
            return "🔴"

    def _classify_fomo_level(self, fomo: int) -> str:
        """分类FOMO等级"""
        if fomo >= 80:
            return "极度FOMO"
        elif fomo >= 60:
            return "高FOMO"
        elif fomo >= 40:
            return "中等FOMO"
        elif fomo >= 20:
            return "低FOMO"
        else:
            return "无FOMO"

    def _get_fomo_icon(self, level: str) -> str:
        """获取FOMO图标"""
        icons = {
            "极度FOMO": "🚀",
            "高FOMO": "📈",
            "中等FOMO": "↗️",
            "低FOMO": "➡️",
            "无FOMO": "⚪"
        }
        return icons.get(level, "⚪")

    def _classify_fear_level(self, fear: int) -> str:
        """分类恐慌等级"""
        if fear >= 80:
            return "极度恐慌"
        elif fear >= 60:
            return "高恐慌"
        elif fear >= 40:
            return "中等恐慌"
        elif fear >= 20:
            return "低恐慌"
        else:
            return "无恐慌"

    def _get_fear_icon(self, level: str) -> str:
        """获取恐慌图标"""
        icons = {
            "极度恐慌": "💥",
            "高恐慌": "📉",
            "中等恐慌": "↘️",
            "低恐慌": "➡️",
            "无恐慌": "⚪"
        }
        return icons.get(level, "⚪")

    def _analyze_market_state(self, fomo: int, fear: int) -> str:
        """分析市场状态"""
        if fomo > 70 and fear < 30:
            return "极度贪婪 - 注意回调风险 🚨"
        elif fomo > 50 and fear < 40:
            return "贪婪 - 市场过热 ⚠️"
        elif fear > 70 and fomo < 30:
            return "极度恐慌 - 可能触底 🟢"
        elif fear > 50 and fomo < 40:
            return "恐慌 - 机会区域 📈"
        else:
            return "平衡状态 - 正常波动 ⚖️"

    def _build_social_metrics_table(self, metrics: list, builder) -> str:
        """构建社交媒体指标对比表格"""
        headers = ["平台", "提及数", "情绪得分", "互动率", "趋势"]
        rows = []

        for metric in metrics:
            platform = metric.get("platform", "未知")
            mentions = metric.get("mention_count", 0)
            sentiment = metric.get("sentiment_score", 0)
            engagement = metric.get("engagement_rate", 0)
            trend = metric.get("trend", "未知")

            trend_icon = "📈" if trend == "上升" else "📉" if trend == "下降" else "➡️"
            sentiment_icon = self._get_sentiment_icon_by_score(sentiment)

            rows.append([
                platform,
                f"{mentions:,}",
                f"{sentiment_icon} {sentiment:+.2f}",
                f"{engagement:.2f}%",
                trend_icon
            ])

        return builder.format_table(headers, rows) if rows else ""

    def _build_sentiment_history_table(self, history: list, builder) -> str:
        """构建情绪历史趋势表格"""
        headers = ["日期", "情绪得分", "变化", "趋势"]
        rows = []

        for entry in history[-7:]:  # 显示最近7天
            date = entry.get("date", "未知")
            score = entry.get("score", 0)
            change = entry.get("change", 0)
            trend = entry.get("trend", "持平")

            change_icon = "📈" if change > 0 else "📉" if change < 0 else "➡️"
            sentiment_icon = self._get_sentiment_icon_by_score(score)

            rows.append([
                date,
                f"{sentiment_icon} {score:.1f}",
                f"{change_icon} {change:+.1f}",
                trend
            ])

        return builder.format_table(headers, rows) if rows else ""

    def _build_influencer_table(self, influencers: list, builder) -> str:
        """构建意见领袖情绪表格"""
        headers = ["KOL", "情绪", "影响度", "观点"]
        rows = []

        for influencer in influencers[:10]:  # 显示前10个
            name = influencer.get("name", "未知")
            sentiment = influencer.get("sentiment", 0)
            influence = influencer.get("influence_score", 0)
            view = influencer.get("view", "未知")

            sentiment_icon = self._get_sentiment_icon_by_score(sentiment)
            influence_level = "高" if influence > 70 else "中" if influence > 40 else "低"

            rows.append([
                name,
                f"{sentiment_icon} {sentiment:+.2f}",
                influence_level,
                view[:30] + "..." if len(view) > 30 else view
            ])

        return builder.format_table(headers, rows) if rows else ""


class TechnicalAnalysisComponent(ReportComponent):
    """技术分析组件"""

    def get_default_config(self):
        config = super().get_default_config()
        config.update({
            "include_indicators": True,
            "include_levels": True
        })
        return config

    def _render_content(self, data, config, builder, **kwargs):
        parts = []

        # 价格指标
        if "price_metrics" in data:
            pm = data["price_metrics"]
            parts.append("### 价格指标\n\n")
            parts.append(f"- **当前价格**: ${pm.get('current_price', 0):,.4f}\n")
            if pm.get("price_change_24h_pct") is not None:
                parts.append(f"- **24小时涨跌**: {pm['price_change_24h_pct']:+.2f}%\n")
            parts.append("\n")

        # 技术指标
        if config["include_indicators"] and "technical_indicators" in data:
            ti = data["technical_indicators"]
            parts.append("### 技术指标\n\n")
            if ti.get("rsi") is not None:
                parts.append(f"- **RSI**: {ti['rsi']:.1f}\n")
            if ti.get("macd_signal"):
                parts.append(f"- **MACD 信号**: {ti['macd_signal']}\n")
            parts.append("\n")

        # 生成技术分析表格（支撑阻力位）
        if config["include_levels"]:
            analyzer_outputs = kwargs.get("analyzer_outputs") or data.get("analyzer_outputs", {})
            if analyzer_outputs and "technical" in analyzer_outputs:
                table_markdown = builder.generate_table_from_analyzer("technical", analyzer_outputs)
                if table_markdown:
                    parts.append("### 📊 关键价位分析\n\n")
                    parts.append(table_markdown)
                    parts.append("\n")

        return "".join(parts)


class OnchainAnalysisComponent(ReportComponent):
    """链上分析组件 - TVL和交易指标深度分析"""

    def get_default_config(self):
        config = super().get_default_config()
        config.update({
            "include_metrics": True,
            "include_whales": True,
            "include_tvl": True,
            "include_holder_analysis": True,
            "include_exchange_flows": True,
            "include_nvt_analysis": True,
            "include_network_health": True
        })
        return config

    def _render_content(self, data, config, builder, **kwargs):
        parts = []

        # TVL概览
        if config["include_tvl"] and "tvl" in data:
            tvl_data = data["tvl"]
            parts.append("### 💰 TVL (总锁定价值) 分析\n\n")

            if "current_tvl" in tvl_data:
                current_tvl = tvl_data["current_tvl"]
                parts.append(f"**当前TVL**: ${current_tvl:,.0f}\n")

            if "tvl_change_24h" in tvl_data:
                tvl_change = tvl_data["tvl_change_24h"]
                change_icon = "🟢" if tvl_change > 0 else "🔴" if tvl_change < 0 else "⚪"
                parts.append(f"**24h变化**: {change_icon} {tvl_change:+.2f}%\n")

            if "tvl_change_7d" in tvl_data:
                tvl_change_7d = tvl_data["tvl_change_7d"]
                parts.append(f"**7天变化**: {tvl_change_7d:+.2f}%\n")

            if "tvl_composition" in tvl_data:
                parts.append("\n#### TVL构成\n\n")
                composition_table = self._build_tvl_composition_table(tvl_data["tvl_composition"], builder)
                parts.append(composition_table)
            parts.append("\n")

        # 链上活动指标汇总
        if config["include_metrics"] and "onchain_metrics" in data:
            om = data["onchain_metrics"]
            parts.append("### ⛓️ 链上活动指标汇总\n\n")

            # 构建指标汇总表格
            metrics_table = self._build_onchain_metrics_table(om, builder)
            parts.append(metrics_table)
            parts.append("\n")

            # 活跃度分析
            if om.get("active_addresses_24h") or om.get("active_addresses_7d"):
                parts.append("#### 📊 地址活跃度分析\n\n")
                if om.get("active_addresses_24h"):
                    parts.append(f"- **24h 活跃地址**: {om['active_addresses_24h']:,}\n")
                if om.get("active_addresses_7d"):
                    parts.append(f"- **7天活跃地址**: {om['active_addresses_7d']:,}\n")
                if om.get("new_addresses_24h"):
                    parts.append(f"- **24h 新增地址**: {om['new_addresses_24h']:,}\n")
                parts.append("\n")

            # 交易活动分析
            if om.get("transaction_count_24h") or om.get("transaction_volume_24h"):
                parts.append("#### 💸 交易活动分析\n\n")
                if om.get("transaction_count_24h"):
                    parts.append(f"- **24h 交易数**: {om['transaction_count_24h']:,}\n")
                if om.get("transaction_volume_24h"):
                    parts.append(f"- **24h 交易量**: ${om['transaction_volume_24h']:,.0f}\n")
                if om.get("avg_transaction_size"):
                    parts.append(f"- **平均交易规模**: ${om['avg_transaction_size']:,.2f}\n")
                parts.append("\n")

        # NVT分析（网络价值/交易量）
        if config["include_nvt_analysis"] and "nvt_ratio" in data:
            nvt = data["nvt_ratio"]
            parts.append("### 📈 NVT比率分析\n\n")
            parts.append(f"**NVT比率**: {nvt:.2f}\n\n")

            nvt_interpretation = self._interpret_nvt_ratio(nvt)
            parts.append(f"**解读**: {nvt_interpretation}\n\n")

        # 持币分布分析
        if config["include_holder_analysis"] and "holder_distribution" in data:
            hd = data["holder_distribution"]
            parts.append("### 👥 持币分布分析\n\n")

            # 持币分布表格
            holder_table = self._build_holder_distribution_table(hd, builder)
            parts.append(holder_table)
            parts.append("\n")

            # 集中度分析
            if hd.get("top10_concentration_pct") is not None:
                concentration = hd["top10_concentration_pct"]
                concentration_level = self._assess_concentration(concentration)
                parts.append(f"**持币集中度**: {concentration_level} (Top 10占比: {concentration:.2f}%)\n\n")

        # 巨鲸动向分析
        if config["include_whales"] and "whale_movements" in data:
            whales = data["whale_movements"]
            parts.append("### 🐋 巨鲸动向分析\n\n")

            if whales:
                # 构建巨鲸动向表格
                whale_table = self._build_whale_movements_table(whales, builder)
                parts.append(whale_table)
                parts.append("\n")

                # 巨鲸情绪分析
                whale_sentiment = self._analyze_whale_sentiment(whales)
                sentiment_icon = "🟢" if whale_sentiment > 0 else "🔴" if whale_sentiment < 0 else "🟡"
                parts.append(f"**巨鲸情绪**: {sentiment_icon} {whale_sentiment:+.1f}\n\n")
            else:
                parts.append("暂无巨鲸交易数据\n\n")

        # 交易所资金流向
        if config["include_exchange_flows"] and "exchange_flows" in data:
            flows = data["exchange_flows"]
            parts.append("### 💱 交易所资金流向\n\n")

            if isinstance(flows, dict):
                if flows.get("inflow_24h") or flows.get("outflow_24h"):
                    inflow = flows.get("inflow_24h", 0)
                    outflow = flows.get("outflow_24h", 0)
                    net_flow = outflow - inflow

                    parts.append(f"- **24h 流入**: ${inflow:,.0f}\n")
                    parts.append(f"- **24h 流出**: ${outflow:,.0f}\n")
                    flow_icon = "🟢" if net_flow > 0 else "🔴" if net_flow < 0 else "⚪"
                    parts.append(f"- **净流出**: {flow_icon} ${net_flow:+,.0f}\n\n")

                    flow_interpretation = self._interpret_exchange_flow(net_flow)
                    parts.append(f"**解读**: {flow_interpretation}\n\n")
            else:
                parts.append(f"**流向**: {flows}\n\n")

        # 网络健康度
        if config["include_network_health"] and "network_health" in data:
            health = data["network_health"]
            parts.append("### 🏥 网络健康度评估\n\n")

            if isinstance(health, dict):
                health_score = health.get("score", 0)
                health_level = self._assess_network_health(health_score)
                health_icon = "🟢" if health_score > 70 else "🟡" if health_score > 50 else "🔴"

                parts.append(f"**健康度评分**: {health_icon} {health_score}/100 ({health_level})\n\n")

                if health.get("indicators"):
                    parts.append("**关键指标**:\n\n")
                    for indicator, value in health["indicators"].items():
                        parts.append(f"- {indicator}: {value}\n")
                    parts.append("\n")
            else:
                parts.append(f"**网络健康**: {health}\n\n")

        # 链上数据可视化占位符
        parts.append("### 📊 链上数据可视化\n\n")
        parts.append("#### TVL趋势图\n\n")
        parts.append("![TVL趋势](chart://tvl_trend.png)\n\n")
        parts.append("#### 活跃地址趋势\n\n")
        parts.append("![活跃地址](chart://active_addresses.png)\n\n")
        parts.append("#### 持币分布图\n\n")
        parts.append("![持币分布](chart://holder_distribution.png)\n\n")

        return "".join(parts)

    def _build_tvl_composition_table(self, composition: dict, builder) -> str:
        """构建TVL构成表格"""
        headers = ["协议/池子", "TVL", "占比", "变化"]
        rows = []

        for protocol, data in composition.items():
            tvl = data.get("tvl", 0)
            percentage = data.get("percentage", 0)
            change = data.get("change_24h", 0)

            change_icon = "🟢" if change > 0 else "🔴" if change < 0 else "⚪"

            rows.append([
                protocol[:30],
                f"${tvl:,.0f}",
                f"{percentage:.2f}%",
                f"{change_icon} {change:+.2f}%"
            ])

        return builder.format_table(headers, rows) if rows else ""

    def _build_onchain_metrics_table(self, metrics: dict, builder) -> str:
        """构建链上指标汇总表格"""
        headers = ["指标", "数值", "变化", "状态"]
        rows = []

        if metrics.get("active_addresses_24h"):
            rows.append([
                "活跃地址(24h)",
                f"{metrics['active_addresses_24h']:,}",
                f"{metrics.get('active_addresses_change', 0):+.1f}%",
                "正常"
            ])

        if metrics.get("transaction_count_24h"):
            rows.append([
                "交易数(24h)",
                f"{metrics['transaction_count_24h']:,}",
                f"{metrics.get('transaction_count_change', 0):+.1f}%",
                "正常"
            ])

        if metrics.get("transaction_volume_24h"):
            rows.append([
                "交易量(24h)",
                f"${metrics['transaction_volume_24h']:,.0f}",
                f"{metrics.get('transaction_volume_change', 0):+.1f}%",
                "正常"
            ])

        if metrics.get("gas_fees_avg"):
            rows.append([
                "平均Gas费",
                f"${metrics['gas_fees_avg']:.4f}",
                f"{metrics.get('gas_fees_change', 0):+.1f}%",
                "正常"
            ])

        return builder.format_table(headers, rows) if rows else ""

    def _interpret_nvt_ratio(self, nvt: float) -> str:
        """解读NVT比率"""
        if nvt < 15:
            return "网络价值被低估，可能处于价值洼地"
        elif nvt < 30:
            return "网络价值合理，交易活跃度良好"
        elif nvt < 50:
            return "网络价值偏高，交易活跃度相对较低"
        else:
            return "网络价值明显偏高，可能存在泡沫风险"

    def _build_holder_distribution_table(self, distribution: dict, builder) -> str:
        """构建持币分布表格"""
        headers = ["类别", "地址数", "持币占比", "平均持币量"]
        rows = []

        if distribution.get("total_holders"):
            rows.append([
                "总持币地址",
                f"{distribution['total_holders']:,}",
                "100%",
                "-"
            ])

        if distribution.get("whale_holders"):
            whale_pct = (distribution.get("whale_holders", 0) / distribution.get("total_holders", 1)) * 100
            rows.append([
                "巨鲸(>1%)",
                f"{distribution['whale_holders']:,}",
                f"{whale_pct:.2f}%",
                "-"
            ])

        if distribution.get("retail_holders"):
            retail_pct = (distribution.get("retail_holders", 0) / distribution.get("total_holders", 1)) * 100
            rows.append([
                "散户(<0.01%)",
                f"{distribution['retail_holders']:,}",
                f"{retail_pct:.2f}%",
                "-"
            ])

        return builder.format_table(headers, rows) if rows else ""

    def _assess_concentration(self, concentration: float) -> str:
        """评估持币集中度"""
        if concentration > 60:
            return "高度集中 🚨"
        elif concentration > 40:
            return "中度集中 ⚠️"
        elif concentration > 20:
            return "相对分散 ✓"
        else:
            return "分散良好 ✓✓"

    def _build_whale_movements_table(self, movements: list, builder) -> str:
        """构建巨鲸动向表格"""
        headers = ["时间", "类型", "金额", "方向", "影响"]
        rows = []

        for movement in movements[:10]:  # 显示最近10条
            if isinstance(movement, dict):
                time = movement.get("time", "未知")
                movement_type = movement.get("type", "未知")
                amount = movement.get("amount", 0)
                direction = movement.get("direction", "未知")
                impact = movement.get("impact", "未知")

                direction_icon = "📥" if direction == "流入" else "📤" if direction == "流出" else "➡️"
                impact_icon = "🟢" if "积极" in str(impact) else "🔴" if "消极" in str(impact) else "🟡"

                rows.append([
                    time[:10],
                    movement_type,
                    f"${amount:,.0f}",
                    f"{direction_icon} {direction}",
                    f"{impact_icon} {impact}"
                ])
            else:
                rows.append(["未知", "未知", "未知", "未知", "未知"])

        return builder.format_table(headers, rows) if rows else ""

    def _analyze_whale_sentiment(self, movements: list) -> float:
        """分析巨鲸情绪"""
        if not movements:
            return 0

        sentiment_scores = []
        for movement in movements:
            if isinstance(movement, dict):
                direction = movement.get("direction", "")
                amount = movement.get("amount", 0)

                if direction == "流入":
                    sentiment_scores.append(amount)
                elif direction == "流出":
                    sentiment_scores.append(-amount)

        if not sentiment_scores:
            return 0

        total_sentiment = sum(sentiment_scores)
        # 归一化到-100到+100
        max_amount = max(abs(s) for s in sentiment_scores) if sentiment_scores else 1
        normalized = (total_sentiment / max_amount) * 100 if max_amount > 0 else 0
        return min(100, max(-100, normalized))

    def _interpret_exchange_flow(self, net_flow: float) -> str:
        """解读交易所资金流向"""
        if net_flow > 1000000:
            return "大量资金从交易所流出，看涨信号强烈 🟢"
        elif net_flow > 100000:
            return "资金从交易所流出，轻度看涨 📈"
        elif net_flow > -100000:
            return "资金流向平衡，中性 ⚖️"
        elif net_flow > -1000000:
            return "资金流入交易所，轻度看跌 📉"
        else:
            return "大量资金流入交易所，看跌信号 🟠"

    def _assess_network_health(self, score: int) -> str:
        """评估网络健康度"""
        if score >= 80:
            return "优秀"
        elif score >= 60:
            return "良好"
        elif score >= 40:
            return "一般"
        elif score >= 20:
            return "较差"
        else:
            return "危险"


class CompetitorAnalysisComponent(ReportComponent):
    """竞品对比分析组件 - 多维度竞争分析"""

    def get_default_config(self):
        config = super().get_default_config()
        config.update({
            "include_comparison": True,
            "include_valuation": True,
            "include_competitive_matrix": True,
            "include_market_share": True,
            "max_competitors": 5
        })
        return config

    def _render_content(self, data, config, builder, **kwargs):
        parts = []

        # 市场地位概览
        parts.append("### 🏆 市场地位概览\n\n")

        if "market_position" in data:
            position = data["market_position"]
            position_icon = self._get_position_icon(position)
            parts.append(f"**市场地位**: {position_icon} {position}\n")

        if "market_share_pct" in data:
            share = data["market_share_pct"]
            parts.append(f"**市场份额**: {share:.2f}%\n")

        if "market_rank" in data:
            rank = data["market_rank"]
            parts.append(f"**市场排名**: 第{rank}位\n")

        parts.append("\n")

        # 竞品对比表格
        if config["include_comparison"]:
            analyzer_outputs = kwargs.get("analyzer_outputs") or data.get("analyzer_outputs", {})
            if analyzer_outputs and "competitor" in analyzer_outputs:
                # 使用table_generator生成竞品对比表
                comparison_table = builder.generate_table_from_analyzer("competitor", analyzer_outputs)
                if comparison_table:
                    parts.append("### 📊 竞品对比分析\n\n")
                    parts.append(comparison_table)
                    parts.append("\n")
            elif "competitors" in data:
                competitors = data["competitors"]
                parts.append("### 📊 竞品对比分析\n\n")
                if competitors:
                    # 构建竞品对比表格（回退到内部方法）
                    comparison_table = self._build_competitor_comparison_table(competitors[:config["max_competitors"]], builder)
                    parts.append(comparison_table)
                    parts.append("\n")

                # 详细竞品分析
                for competitor in competitors[:config["max_competitors"]]:
                    comp_name = competitor.get("name", "未知")
                    parts.append(f"#### {comp_name}\n\n")

                    if competitor.get("description"):
                        parts.append(f"**项目描述**: {competitor['description']}\n\n")

                    if competitor.get("market_cap"):
                        parts.append(f"- **市值**: ${competitor['market_cap']:,.0f}\n")
                    if competitor.get("price"):
                        parts.append(f"- **价格**: ${competitor['price']:,.4f}\n")
                    if competitor.get("users"):
                        parts.append(f"- **用户数**: {competitor['users']:,}\n")

                    parts.append("\n")
            else:
                parts.append("暂无竞品数据\n\n")

        # 估值倍数对比
        if config["include_valuation"]:
            analyzer_outputs = kwargs.get("analyzer_outputs") or data.get("analyzer_outputs", {})
            if analyzer_outputs and "competitor" in analyzer_outputs:
                # 使用table_generator生成估值倍数表
                valuation_table = builder.generate_table_from_analyzer("competitor", analyzer_outputs, table_type="valuation_multiples")
                if valuation_table:
                    parts.append("### 💰 估值倍数对比\n\n")
                    parts.append(valuation_table)
                    parts.append("\n")
            elif "valuation_multiples" in data:
                vm = data["valuation_multiples"]
                parts.append("### 💰 估值倍数对比\n\n")
                # 构建估值倍数表格（回退到内部方法）
                valuation_table = self._build_valuation_multiples_table(vm, builder)
                parts.append(valuation_table)
                parts.append("\n")

        # 竞争优势与劣势
        parts.append("### ⚖️ 竞争优势与劣势分析\n\n")

        if "competitive_advantages" in data and data["competitive_advantages"]:
            parts.append("#### ✅ 竞争优势\n\n")
            for i, adv in enumerate(data["competitive_advantages"], 1):
                parts.append(f"{i}. {adv}\n")
            parts.append("\n")

        if "competitive_threats" in data and data["competitive_threats"]:
            parts.append("#### ⚠️ 竞争威胁\n\n")
            for i, threat in enumerate(data["competitive_threats"], 1):
                parts.append(f"{i}. {threat}\n")
            parts.append("\n")

        # 竞争矩阵
        if config["include_competitive_matrix"] and "competitive_matrix" in data:
            matrix = data["competitive_matrix"]
            parts.append("### 📈 竞争矩阵分析\n\n")

            competitive_table = self._build_competitive_matrix_table(matrix, builder)
            parts.append(competitive_table)
            parts.append("\n")

        # 差异化分析
        if "differentiation" in data:
            diff = data["differentiation"]
            parts.append("### 🎯 差异化分析\n\n")

            if isinstance(diff, dict):
                if diff.get("unique_features"):
                    parts.append("**独特功能**:\n\n")
                    for feature in diff["unique_features"]:
                        parts.append(f"- {feature}\n")
                    parts.append("\n")

                if diff.get("differentiation_score"):
                    score = diff["differentiation_score"]
                    score_icon = "🟢" if score > 70 else "🟡" if score > 50 else "🔴"
                    parts.append(f"**差异化评分**: {score_icon} {score}/100\n\n")
            else:
                parts.append(f"{diff}\n\n")

        # 竞争可视化
        analyzer_outputs = kwargs.get("analyzer_outputs") or data.get("analyzer_outputs", {})
        if analyzer_outputs and "competitor" in analyzer_outputs:
            chart_markdown = builder.generate_chart_from_analyzer("competitor", analyzer_outputs, chart_type="valuation_comparison")
            if chart_markdown:
                parts.append("### 📊 竞争可视化\n\n")
                parts.append("#### 估值倍数对比图\n\n")
                parts.append(chart_markdown)
                parts.append("\n")

        return "".join(parts)

    def _get_position_icon(self, position: str) -> str:
        """获取市场地位图标"""
        if "领先" in position or "第一" in position:
            return "🥇"
        elif "第二" in position or "前三" in position:
            return "🥈"
        elif "前五" in position:
            return "🥉"
        else:
            return "📊"

    def _build_competitor_comparison_table(self, competitors: list, builder) -> str:
        """构建竞品对比表格"""
        headers = ["项目", "市值", "价格", "24h涨跌", "用户数", "评分"]
        rows = []

        for competitor in competitors:
            name = competitor.get("name", "未知")
            market_cap = competitor.get("market_cap", 0)
            price = competitor.get("price", 0)
            change_24h = competitor.get("change_24h_pct", 0)
            users = competitor.get("users", 0)
            score = competitor.get("score", 0)

            change_icon = "🟢" if change_24h > 0 else "🔴" if change_24h < 0 else "⚪"
            score_icon = "🟢" if score > 70 else "🟡" if score > 50 else "🔴"

            rows.append([
                name[:20],
                f"${market_cap:,.0f}" if market_cap > 0 else "-",
                f"${price:,.4f}" if price > 0 else "-",
                f"{change_icon} {change_24h:+.2f}%",
                f"{users:,}" if users > 0 else "-",
                f"{score_icon} {score}/100"
            ])

        return builder.format_table(headers, rows) if rows else ""

    def _build_valuation_multiples_table(self, multiples: dict, builder) -> str:
        """构建估值倍数表格"""
        headers = ["估值指标", "当前值", "行业平均", "解读"]
        rows = []

        if multiples.get("ps_ratio") is not None:
            ps = multiples["ps_ratio"]
            ps_avg = multiples.get("ps_ratio_avg", 0)
            ps_interp = "低估" if ps < ps_avg * 0.8 else "高估" if ps > ps_avg * 1.2 else "合理"
            rows.append(["P/S比率", f"{ps:.2f}", f"{ps_avg:.2f}", ps_interp])

        if multiples.get("fdv_revenue") is not None:
            fdv_rev = multiples["fdv_revenue"]
            fdv_rev_avg = multiples.get("fdv_revenue_avg", 0)
            fdv_interp = "低估" if fdv_rev < fdv_rev_avg * 0.8 else "高估" if fdv_rev > fdv_rev_avg * 1.2 else "合理"
            rows.append(["FDV/Revenue", f"{fdv_rev:.2f}", f"{fdv_rev_avg:.2f}", fdv_interp])

        if multiples.get("fdv_tvl") is not None:
            fdv_tvl = multiples["fdv_tvl"]
            fdv_tvl_avg = multiples.get("fdv_tvl_avg", 0)
            tvl_interp = "低估" if fdv_tvl < fdv_tvl_avg * 0.8 else "高估" if fdv_tvl > fdv_tvl_avg * 1.2 else "合理"
            rows.append(["FDV/TVL", f"{fdv_tvl:.2f}", f"{fdv_tvl_avg:.2f}", tvl_interp])

        return builder.format_table(headers, rows) if rows else ""

    def _build_competitive_matrix_table(self, matrix: dict, builder) -> str:
        """构建竞争矩阵表格"""
        headers = ["维度", "评分", "排名", "优势"]
        rows = []

        dimensions = ["技术", "市场", "团队", "资金", "社区"]
        for dim in dimensions:
            if dim in matrix:
                score = matrix[dim].get("score", 0)
                rank = matrix[dim].get("rank", 0)
                advantage = matrix[dim].get("advantage", "未知")

                score_icon = "🟢" if score > 70 else "🟡" if score > 50 else "🔴"

                rows.append([
                    dim,
                    f"{score_icon} {score}/100",
                    f"第{rank}位" if rank > 0 else "-",
                    advantage[:30]
                ])

        return builder.format_table(headers, rows) if rows else ""


class TokenomicsAnalysisComponent(ReportComponent):
    """代币经济学分析组件 - 供应结构和价值捕获机制"""

    def get_default_config(self):
        config = super().get_default_config()
        config.update({
            "include_supply": True,
            "include_allocation": True,
            "include_unlock_schedule": True,
            "include_value_capture": True,
            "include_tokenomics_rating": True
        })
        return config

    def _render_content(self, data, config, builder, **kwargs):
        parts = []

        # 供应结构概览
        if config["include_supply"] and "supply_structure" in data:
            ss = data["supply_structure"]
            parts.append("### 💰 供应结构概览\n\n")

            total_supply = ss.get('total_supply', 0)
            circulating_supply = ss.get('circulating_supply', 0)
            circulating_ratio = (circulating_supply / total_supply * 100) if total_supply > 0 else 0

            parts.append(f"- **总供应量**: {total_supply:,.0f}\n")
            parts.append(f"- **流通供应量**: {circulating_supply:,.0f}\n")
            parts.append(f"- **流通率**: {circulating_ratio:.2f}%\n\n")

            # 流通率解读
            ratio_icon = "🟢" if circulating_ratio > 80 else "🟡" if circulating_ratio > 50 else "🔴"
            ratio_interp = self._interpret_circulating_ratio(circulating_ratio)
            parts.append(f"**流通率解读**: {ratio_icon} {ratio_interp}\n\n")

            # 代币分配
            if config["include_allocation"] and ss.get("allocation"):
                parts.append("#### 📊 代币分配结构\n\n")
                allocation_table = self._build_allocation_table(ss["allocation"], builder)
                parts.append(allocation_table)
                parts.append("\n")

        # 解锁时间表
        if config["include_unlock_schedule"]:
            analyzer_outputs = kwargs.get("analyzer_outputs") or data.get("analyzer_outputs", {})
            if analyzer_outputs and "tokenomics" in analyzer_outputs:
                # 使用table_generator生成解锁时间表
                unlock_table = builder.generate_table_from_analyzer("tokenomics", analyzer_outputs)
                if unlock_table:
                    parts.append("### ⏰ 代币解锁时间表\n\n")
                    parts.append(unlock_table)
                    parts.append("\n")
            elif "unlock_schedule" in data:
                schedule = data["unlock_schedule"]
                parts.append("### ⏰ 代币解锁时间表\n\n")
                if schedule:
                    unlock_table = self._build_unlock_schedule_table(schedule, builder)
                    parts.append(unlock_table)
                    parts.append("\n")

                    # 解锁压力分析
                    unlock_pressure = self._analyze_unlock_pressure(schedule)
                    pressure_icon = "🔴" if unlock_pressure["pressure_level"] == "高" else "🟡" if unlock_pressure["pressure_level"] == "中" else "🟢"
                    parts.append(f"**解锁压力**: {pressure_icon} {unlock_pressure['pressure_level']}\n")
                    parts.append(f"- 未来30天解锁: {unlock_pressure['unlock_30d']:,.0f} ({unlock_pressure['unlock_30d_pct']:.2f}%)\n")
                    parts.append(f"- 未来90天解锁: {unlock_pressure['unlock_90d']:,.0f} ({unlock_pressure['unlock_90d_pct']:.2f}%)\n\n")
                else:
                    parts.append("暂无解锁时间表数据\n\n")

        # 价值捕获机制
        if config["include_value_capture"] and "value_capture" in data:
            vc = data["value_capture"]
            parts.append("### 🎯 价值捕获机制\n\n")

            if isinstance(vc, dict):
                mechanisms = []
                if vc.get("governance"):
                    mechanisms.append(("治理", vc["governance"]))
                if vc.get("staking"):
                    mechanisms.append(("质押", vc["staking"]))
                if vc.get("buyback_burn"):
                    mechanisms.append(("回购销毁", vc["buyback_burn"]))
                if vc.get("revenue_share"):
                    mechanisms.append(("收益分成", vc["revenue_share"]))

                if mechanisms:
                    for name, desc in mechanisms:
                        parts.append(f"- **{name}**: {desc}\n")
                    parts.append("\n")
            else:
                parts.append(f"{vc}\n\n")

        # 代币经济学评级
        if config["include_tokenomics_rating"] and "tokenomics_rating" in data:
            rating = data["tokenomics_rating"]
            parts.append("### ⭐ 代币经济学评级\n\n")

            if isinstance(rating, dict):
                score = rating.get("score", 0)
                level = rating.get("level", "未知")
                score_icon = "🟢" if score > 70 else "🟡" if score > 50 else "🔴"

                parts.append(f"**综合评分**: {score_icon} {score}/100 ({level})\n\n")

                if rating.get("factors"):
                    parts.append("**评分因素**:\n\n")
                    for factor, score_factor in rating["factors"].items():
                        parts.append(f"- {factor}: {score_factor}/100\n")
                    parts.append("\n")
            else:
                parts.append(f"**评级**: {rating}\n\n")

        # 飞轮效应分析
        if "flywheel_effect" in data:
            flywheel = data["flywheel_effect"]
            parts.append("### 🔄 飞轮效应分析\n\n")

            if isinstance(flywheel, dict):
                parts.append(f"**飞轮强度**: {flywheel.get('strength', '未知')}\n")
                if flywheel.get("description"):
                    parts.append(f"**描述**: {flywheel['description']}\n")
                parts.append("\n")
            else:
                parts.append(f"{flywheel}\n\n")

        # 代币经济学可视化占位符
        parts.append("### 📊 代币经济学可视化\n\n")
        parts.append("#### 代币分配饼图\n\n")
        parts.append("![代币分配](chart://token_allocation.png)\n\n")
        parts.append("#### 解锁时间表\n\n")
        parts.append("![解锁时间表](chart://unlock_schedule.png)\n\n")

        return "".join(parts)

    def _interpret_circulating_ratio(self, ratio: float) -> str:
        """解读流通率"""
        if ratio > 80:
            return "流通率很高，市场供应充足"
        elif ratio > 50:
            return "流通率适中，需关注未来解锁"
        elif ratio > 30:
            return "流通率较低，存在较大解锁压力"
        else:
            return "流通率很低，需密切关注解锁风险"

    def _build_allocation_table(self, allocation: dict, builder) -> str:
        """构建代币分配表格"""
        headers = ["分配对象", "占比", "数量", "状态"]
        rows = []

        for beneficiary, pct in allocation.items():
            amount = (pct / 100) * 1000000  # 假设总供应量为示例值
            status = "已解锁" if pct < 50 else "部分锁定" if pct < 80 else "锁定中"

            rows.append([
                beneficiary[:30],
                f"{pct:.2f}%",
                f"{amount:,.0f}",
                status
            ])

        return builder.format_table(headers, rows) if rows else ""

    def _build_unlock_schedule_table(self, schedule: list, builder) -> str:
        """构建解锁时间表"""
        headers = ["时间", "解锁量", "占比", "接收方"]
        rows = []

        for unlock in schedule[:12]:  # 显示未来12个月
            if isinstance(unlock, dict):
                date = unlock.get("date", "未知")
                amount = unlock.get("amount", 0)
                percentage = unlock.get("percentage", 0)
                recipient = unlock.get("recipient", "未知")

                rows.append([
                    date[:10],
                    f"{amount:,.0f}",
                    f"{percentage:.2f}%",
                    recipient[:20]
                ])

        return builder.format_table(headers, rows) if rows else ""

    def _analyze_unlock_pressure(self, schedule: list) -> dict:
        """分析解锁压力"""
        from datetime import datetime, timedelta

        now = datetime.now()
        unlock_30d = 0
        unlock_90d = 0
        total_unlock = sum(item.get("amount", 0) for item in schedule if isinstance(item, dict))

        for unlock in schedule:
            if isinstance(unlock, dict):
                unlock_date_str = unlock.get("date", "")
                amount = unlock.get("amount", 0)

                try:
                    unlock_date = datetime.fromisoformat(unlock_date_str.replace("Z", "+00:00"))
                    days_diff = (unlock_date - now).days

                    if 0 <= days_diff <= 30:
                        unlock_30d += amount
                    if 0 <= days_diff <= 90:
                        unlock_90d += amount
                except:
                    pass

        unlock_30d_pct = (unlock_30d / total_unlock * 100) if total_unlock > 0 else 0
        unlock_90d_pct = (unlock_90d / total_unlock * 100) if total_unlock > 0 else 0

        # 判断压力等级
        if unlock_30d_pct > 20:
            pressure_level = "高"
        elif unlock_30d_pct > 10:
            pressure_level = "中"
        else:
            pressure_level = "低"

        return {
            "pressure_level": pressure_level,
            "unlock_30d": unlock_30d,
            "unlock_30d_pct": unlock_30d_pct,
            "unlock_90d": unlock_90d,
            "unlock_90d_pct": unlock_90d_pct
        }


class RiskAssessmentComponent(ReportComponent):
    """风险评估组件 - 矩阵评分和全面风险分析"""

    def get_default_config(self):
        config = super().get_default_config()
        config.update({
            "include_matrix": True,
            "include_catalysts": True,
            "include_scenario_analysis": True,
            "include_risk_reward": True,
            "include_tail_risks": True,
            "include_mitigation": True
        })
        return config

    def _render_content(self, data, config, builder, **kwargs):
        parts = []

        # 整体风险评级仪表盘
        parts.append("### ⚠️ 整体风险评级\n\n")

        if "overall_risk_rating" in data:
            rating = data["overall_risk_rating"]
            risk_icon = self._get_risk_icon(rating)
            parts.append(f"**风险等级**: {risk_icon} {rating}\n")

        if "overall_risk_score" in data:
            score = data["overall_risk_score"]
            score_icon = self._get_risk_score_icon(score)
            parts.append(f"**风险评分**: {score_icon} {score}/10\n\n")

        # 风险矩阵评分表
        if config["include_matrix"]:
            analyzer_outputs = kwargs.get("analyzer_outputs") or data.get("analyzer_outputs", {})
            if analyzer_outputs and "risk" in analyzer_outputs:
                # 使用table_generator生成风险矩阵表
                risk_matrix = builder.generate_table_from_analyzer("risk", analyzer_outputs)
                if risk_matrix:
                    parts.append("### 📊 风险矩阵评分\n\n")
                    parts.append(risk_matrix)
                    parts.append("\n")
            elif "risks" in data:
                parts.append("### 📊 风险矩阵评分\n\n")
                risks = data["risks"]
                risk_matrix = self._build_risk_matrix(risks, builder)
                parts.append(risk_matrix)
                parts.append("\n")

            # 风险优先级排序（如果有risks数据）
            prioritized_risks = []
            if "risks" in data:
                prioritized_risks = self._prioritize_risks(data["risks"])
            if prioritized_risks:
                parts.append("#### 🔴 高风险项（需重点关注）\n\n")
                for risk in prioritized_risks[:5]:
                    parts.append(f"- **{risk['name']}** - {risk['category']}\n")
                    parts.append(f"  - 严重程度: {risk['severity']} | 概率: {risk['probability']}\n")
                    parts.append(f"  - 综合风险: {risk['risk_score']}/100\n")
                parts.append("\n")

        # 分类风险详细分析
        if "risks" in data:
            risks = data["risks"]
            parts.append("### 🔍 分类风险详细分析\n\n")

            risk_categories = {
                "technical": ("⚙️ 技术风险", "技术漏洞、智能合约风险、基础设施问题"),
                "market": ("📊 市场风险", "价格波动、流动性风险、市场操纵"),
                "regulatory": ("🏛️ 监管风险", "政策变化、合规要求、监管不确定性"),
                "competitive": ("🏁 竞争风险", "市场地位、技术替代、竞争优势"),
                "tokenomics": ("💰 代币经济学风险", "供应结构、解锁抛压、价值捕获"),
                "liquidity": ("💧 流动性风险", "交易深度、流动性提供、交易所风险"),
                "operational": ("⚙️ 运营风险", "团队风险、开发进度、治理风险")
            }

            for category, (title, description) in risk_categories.items():
                items = risks.get(category, [])
                if items:
                    parts.append(f"#### {title}\n\n")
                    parts.append(f"*{description}*\n\n")

                    for item in items:
                        risk_name = item.get('risk', '未知风险')
                        severity = item.get('severity', '未知')
                        probability = item.get('probability', '未知')
                        impact = item.get('price_impact', '未知')
                        mitigation = item.get('mitigation', None)

                        # 风险严重程度图标
                        severity_icon = self._get_severity_icon(severity)
                        probability_icon = self._get_probability_icon(probability)

                        parts.append(f"- **{risk_name}**\n")
                        parts.append(f"  - 严重程度: {severity_icon} {severity}\n")
                        parts.append(f"  - 发生概率: {probability_icon} {probability}\n")
                        if impact != '未知':
                            parts.append(f"  - 价格影响: {impact}\n")
                        if mitigation:
                            parts.append(f"  - 缓解措施: {mitigation}\n")
                    parts.append("\n")

        # 催化剂日历
        if config["include_catalysts"] and "catalysts" in data:
            catalysts = data["catalysts"]
            parts.append("### ⏰ 催化剂日历\n\n")

            timeframe_mapping = {
                "short_term": "短期（2-4周）",
                "medium_term": "中期（1-2月）",
                "long_term": "长期（3-6月）"
            }

            for timeframe, timeframe_cn in timeframe_mapping.items():
                items = catalysts.get(timeframe, [])
                if items:
                    parts.append(f"#### {timeframe_cn}\n\n")

                    # 构建催化剂表格
                    catalyst_table = self._build_catalyst_table(items, builder)
                    parts.append(catalyst_table)
                    parts.append("\n")

        # 风险收益分析
        if config["include_risk_reward"] and "risk_reward_analysis" in data:
            rra = data["risk_reward_analysis"]
            parts.append("### 📈 风险收益分析\n\n")

            if "upside_potential" in rra:
                upside = rra["upside_potential"]
                upside_icon = "📈" if isinstance(upside, str) and "高" in upside else "📊"
                parts.append(f"**上行潜力**: {upside_icon} {upside}\n")

            if "downside_risk" in rra:
                downside = rra["downside_risk"]
                downside_icon = "📉" if isinstance(downside, str) and "高" in downside else "📊"
                parts.append(f"**下行风险**: {downside_icon} {downside}\n")

            if "risk_reward_ratio" in rra:
                rr = rra["risk_reward_ratio"]
                rr_icon = "🟢" if rr > 2 else "🟡" if rr > 1 else "🔴"
                parts.append(f"**风险收益比**: {rr_icon} {rr:.2f}:1\n")

            if "asymmetry" in rra:
                parts.append(f"**不对称性**: {rra['asymmetry']}\n")

            parts.append("\n")

        # 尾部风险
        if config["include_tail_risks"] and "tail_risks" in data:
            tail_risks = data["tail_risks"]
            if tail_risks:
                parts.append("### 🚨 尾部风险（黑天鹅事件）\n\n")
                for i, tail_risk in enumerate(tail_risks[:5], 1):
                    risk_desc = tail_risk if isinstance(tail_risk, str) else tail_risk.get("description", "未知风险")
                    parts.append(f"{i}. {risk_desc}\n")
                parts.append("\n")

        # 情景分析
        if config["include_scenario_analysis"] and "scenario_analysis" in data:
            scenarios = data["scenario_analysis"]
            parts.append("### 🎭 情景分析\n\n")

            if scenarios:
                for scenario in scenarios[:3]:  # 显示前3个情景
                    scenario_name = scenario.get('scenario', '未知情景')
                    probability = scenario.get('probability', 0)
                    price_target = scenario.get('price_target', '未知')
                    triggers = scenario.get('triggers', [])
                    narrative = scenario.get('narrative', '')

                    prob_icon = "🟢" if probability > 40 else "🟡" if probability > 20 else "🔴"

                    parts.append(f"#### {scenario_name}\n\n")
                    parts.append(f"- **发生概率**: {prob_icon} {probability}%\n")
                    parts.append(f"- **价格目标**: {price_target}\n")

                    if triggers:
                        parts.append("- **触发条件**:\n")
                        for trigger in triggers:
                            parts.append(f"  - {trigger}\n")

                    if narrative:
                        parts.append(f"- **叙述**: {narrative}\n")

                    parts.append("\n")

        # 风险缓解建议
        if config["include_mitigation"] and "mitigation_strategies" in data:
            strategies = data["mitigation_strategies"]
            parts.append("### 🛡️ 风险缓解策略\n\n")

            if strategies:
                for strategy in strategies:
                    strategy_name = strategy.get("strategy", "未知策略")
                    effectiveness = strategy.get("effectiveness", 0)
                    description = strategy.get("description", "")

                    eff_icon = "🟢" if effectiveness > 70 else "🟡" if effectiveness > 40 else "🔴"

                    parts.append(f"- **{strategy_name}** (有效性: {eff_icon} {effectiveness}%)\n")
                    if description:
                        parts.append(f"  - {description}\n")
                parts.append("\n")

        # 风险可视化
        if config["include_matrix"]:
            analyzer_outputs = kwargs.get("analyzer_outputs") or data.get("analyzer_outputs", {})
            if analyzer_outputs and "risk" in analyzer_outputs:
                chart_markdown = builder.generate_chart_from_analyzer("risk", analyzer_outputs)
                if chart_markdown:
                    parts.append("### 📊 风险可视化\n\n")
                    parts.append("#### 风险矩阵热力图\n\n")
                    parts.append(chart_markdown)
                    parts.append("\n")

        return "".join(parts)

    def _get_risk_icon(self, rating: str) -> str:
        """获取风险等级图标"""
        icons = {
            "极低": "🟢",
            "低": "🟡",
            "中等": "🟠",
            "高": "🔴",
            "极高": "🚨"
        }
        return icons.get(rating, "⚪")

    def _get_risk_score_icon(self, score: int) -> str:
        """获取风险评分图标"""
        if score <= 2:
            return "🟢"
        elif score <= 4:
            return "🟡"
        elif score <= 6:
            return "🟠"
        elif score <= 8:
            return "🔴"
        else:
            return "🚨"

    def _get_severity_icon(self, severity: str) -> str:
        """获取严重程度图标"""
        icons = {
            "极低": "🟢",
            "低": "🟡",
            "中等": "🟠",
            "高": "🔴",
            "极高": "🚨"
        }
        return icons.get(severity, "⚪")

    def _get_probability_icon(self, probability: str) -> str:
        """获取概率图标"""
        icons = {
            "极低": "🟢",
            "低": "🟡",
            "中等": "🟠",
            "高": "🔴",
            "极高": "🚨"
        }
        return icons.get(probability, "⚪")

    def _build_risk_matrix(self, risks: dict, builder) -> str:
        """构建风险矩阵表格"""
        headers = ["风险类别", "风险项", "严重程度", "概率", "综合风险", "优先级"]
        rows = []

        risk_categories = {
            "technical": "技术风险",
            "market": "市场风险",
            "regulatory": "监管风险",
            "competitive": "竞争风险",
            "tokenomics": "代币经济学风险",
            "liquidity": "流动性风险",
            "operational": "运营风险"
        }

        for category, category_name in risk_categories.items():
            items = risks.get(category, [])
            for item in items:
                risk_name = item.get('risk', '未知风险')
                severity = item.get('severity', '未知')
                probability = item.get('probability', '未知')

                # 计算综合风险分数
                risk_score = self._calculate_risk_score(severity, probability)
                priority = self._calculate_priority(risk_score)

                severity_icon = self._get_severity_icon(severity)
                probability_icon = self._get_probability_icon(probability)
                priority_icon = "🔴" if priority == "高" else "🟡" if priority == "中" else "🟢"

                rows.append([
                    category_name,
                    risk_name[:30] + "..." if len(risk_name) > 30 else risk_name,
                    f"{severity_icon} {severity}",
                    f"{probability_icon} {probability}",
                    f"{risk_score}/100",
                    f"{priority_icon} {priority}"
                ])

        return builder.format_table(headers, rows) if rows else "暂无风险数据"

    def _calculate_risk_score(self, severity: str, probability: str) -> int:
        """计算综合风险分数"""
        severity_scores = {"极低": 20, "低": 40, "中等": 60, "高": 80, "极高": 100}
        probability_scores = {"极低": 20, "低": 40, "中等": 60, "高": 80, "极高": 100}

        sev_score = severity_scores.get(severity, 50)
        prob_score = probability_scores.get(probability, 50)

        # 加权平均（严重程度权重更高）
        return int((sev_score * 0.6 + prob_score * 0.4))

    def _calculate_priority(self, risk_score: int) -> str:
        """计算优先级"""
        if risk_score >= 70:
            return "高"
        elif risk_score >= 50:
            return "中"
        else:
            return "低"

    def _prioritize_risks(self, risks: dict) -> list:
        """风险优先级排序"""
        prioritized = []

        for category, items in risks.items():
            for item in items:
                severity = item.get('severity', '未知')
                probability = item.get('probability', '未知')
                risk_score = self._calculate_risk_score(severity, probability)

                prioritized.append({
                    "name": item.get('risk', '未知风险'),
                    "category": category,
                    "severity": severity,
                    "probability": probability,
                    "risk_score": risk_score
                })

        # 按风险分数降序排序
        prioritized.sort(key=lambda x: x["risk_score"], reverse=True)
        return prioritized

    def _build_catalyst_table(self, catalysts: list, builder) -> str:
        """构建催化剂表格"""
        headers = ["事件", "时间窗", "影响", "概率", "价格影响"]
        rows = []

        for catalyst in catalysts:
            event = catalyst.get('event', '未知事件')
            timeframe = catalyst.get('timeframe', '未知')
            impact = catalyst.get('impact', '未知')
            probability = catalyst.get('probability', '未知')
            price_impact = catalyst.get('price_impact', '未知')

            impact_icon = "🟢" if "积极" in str(impact) else "🔴" if "消极" in str(impact) else "🟡"
            prob_icon = self._get_probability_icon(probability)

            rows.append([
                event[:40] + "..." if len(event) > 40 else event,
                timeframe,
                f"{impact_icon} {impact}",
                f"{prob_icon} {probability}",
                price_impact
            ])

        return builder.format_table(headers, rows) if rows else "暂无催化剂数据"


class ConclusionComponent(ReportComponent):
    """结论组件"""

    def get_default_config(self):
        config = super().get_default_config()
        config.update({
            "include_recommendation": True,
            "include_outlook": True
        })
        return config

    def _render_content(self, data, config, builder, **kwargs):
        parts = []

        # 投资结论
        if "investment_recommendation" in data:
            ir = data["investment_recommendation"]
            parts.append("### 💡 投资建议\n\n")
            parts.append(f"**评级**: {ir.get('rating', '未知')}\n")
            parts.append(f"**行动**: {ir.get('action', '未知')}\n\n")

        # 生成催化剂日历表
        analyzer_outputs = kwargs.get("analyzer_outputs") or data.get("analyzer_outputs", {})
        if analyzer_outputs and "conclusion" in analyzer_outputs:
            table_markdown = builder.generate_table_from_analyzer("conclusion", analyzer_outputs)
            if table_markdown:
                parts.append("### 📅 催化剂日历\n\n")
                parts.append(table_markdown)
                parts.append("\n")

        return "".join(parts)


class DisclaimerComponent(ReportComponent):
    """免责声明组件"""

    def _render_content(self, data, config, builder, **kwargs):
        return """## ⚠️ 免责声明

本报告由 AI 自动生成，仅供参考，不构成投资建议。加密货币市场波动性极大，投资有风险，入市需谨慎。

**重要提示**:
- 本报告基于公开数据和 AI 分析生成，可能存在数据延迟或分析偏差
- 加密货币投资风险极高，可能导致本金全部损失
- 请在投资前进行独立研究，必要时咨询专业金融顾问
- 过往表现不代表未来收益
- 本报告不应作为买入、卖出或持有任何加密货币的依据
"""


class MetadataComponent(ReportComponent):
    """元数据组件"""

    def get_default_config(self):
        config = super().get_default_config()
        config.update({
            "include_sources": True,
            "include_stats": True
        })
        return config

    def _render_content(self, data, config, builder, **kwargs):
        parts = ["## 📊 报告元数据\n\n"]

        # 数据来源
        if config["include_sources"] and "data_sources" in data:
            data_sources = data["data_sources"]
            if data_sources:
                parts.append("### 📚 数据来源\n\n")
                parts.append("*本报告综合以下可信数据源*\n\n")

                source_details = {
                    "CoinGecko": {"name": "CoinGecko", "desc": "全球最大的加密货币数据聚合平台"},
                    "Etherscan": {"name": "Etherscan", "desc": "以太坊区块链浏览器"},
                    "Twitter": {"name": "Twitter/X", "desc": "社交媒体平台"},
                    "CryptoPanic": {"name": "CryptoPanic", "desc": "加密货币新闻聚合器"}
                }

                for source in data_sources:
                    detail = source_details.get(source, {"name": source, "desc": "数据提供方"})
                    parts.append(f"- **{detail['name']}**: {detail['desc']}\n")

                parts.append("\n")

        # 生成统计
        if config["include_stats"]:
            parts.append("### 生成统计\n\n")
            generation_time = data.get("generation_time", 0)
            quality_score = data.get("quality_score", 0)

            parts.append(f"- **报告生成耗时**: {generation_time:.2f} 秒\n")
            parts.append(f"- **质量得分**: {quality_score}/100\n\n")

        return "".join(parts)


# ================================
# 全局实例
# ================================

markdown_builder = MarkdownBuilder()
