"""
PDF 导出器
将 Markdown 报告转换为 PDF 格式
"""
import os
from pathlib import Path
from typing import Optional
from datetime import datetime


class PDFExporter:
    """
    PDF 导出器
    使用 WeasyPrint 将 Markdown 转换为专业的 PDF 报告
    """

    def __init__(self):
        """初始化 PDF 导出器"""
        self.template_dir = Path(__file__).parent / "templates"
        self.template_dir.mkdir(exist_ok=True)

        # CSS 样式路径
        self.css_path = self.template_dir / "pdf_style.css"

    def export_to_pdf(
        self,
        markdown_content: str,
        output_path: str,
        title: Optional[str] = None
    ) -> str:
        """
        将 Markdown 内容导出为 PDF

        Args:
            markdown_content: Markdown 格式的报告内容
            output_path: PDF 输出路径（绝对路径）
            title: 报告标题（可选）

        Returns:
            str: 生成的 PDF 文件路径

        Raises:
            Exception: PDF 生成失败时抛出异常
        """
        try:
            import markdown2
            from weasyprint import HTML, CSS

            # 1. Markdown → HTML
            html_content = self._markdown_to_html(markdown_content, title)

            # 2. 应用 CSS 样式
            css = self._load_css()

            # 3. HTML → PDF
            HTML(string=html_content).write_pdf(
                output_path,
                stylesheets=[CSS(string=css)] if css else None
            )

            return output_path

        except ImportError as e:
            raise Exception(f"缺少依赖库: {str(e)}. 请安装: pip install markdown2 weasyprint")

        except Exception as e:
            raise Exception(f"PDF 生成失败: {str(e)}")

    def _markdown_to_html(self, markdown_content: str, title: Optional[str] = None) -> str:
        """
        将 Markdown 转换为 HTML

        Args:
            markdown_content: Markdown 内容
            title: 页面标题

        Returns:
            str: HTML 内容
        """
        import markdown2

        # 使用 markdown2 转换（支持表格、代码块等扩展）
        html_body = markdown2.markdown(
            markdown_content,
            extras=[
                "tables",           # 表格支持
                "fenced-code-blocks",  # 代码块
                "break-on-newline",    # 换行支持
                "header-ids",          # 标题 ID
                "toc",                 # 目录
            ]
        )

        # 构建完整的 HTML 文档
        page_title = title or "加密货币研究报告"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

        html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{page_title}</title>
</head>
<body>
    <div class="header">
        <h1 class="document-title">{page_title}</h1>
        <p class="document-subtitle">生成时间: {timestamp}</p>
    </div>

    <div class="content">
        {html_body}
    </div>

    <div class="footer">
        <p>© {datetime.now().year} Web3 AI Search Engine | 本报告由 AI 自动生成，仅供参考</p>
    </div>
</body>
</html>"""

        return html_template

    def _load_css(self) -> str:
        """
        加载 CSS 样式

        Returns:
            str: CSS 内容
        """
        # 如果存在外部 CSS 文件，加载它
        if self.css_path.exists():
            try:
                with open(self.css_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except:
                pass

        # 否则返回默认样式
        return self._get_default_css()

    def _get_default_css(self) -> str:
        """
        获取默认 CSS 样式

        Returns:
            str: 默认 CSS
        """
        return """
/* PDF 报告样式表 */

/* 页面设置 */
@page {
    size: A4;
    margin: 2.5cm 2cm;

    @top-center {
        content: "Web3 加密货币 AI 搜索引擎";
        font-size: 10pt;
        font-family: Arial, sans-serif;
        color: #666;
        border-bottom: 1px solid #ddd;
        padding-bottom: 5pt;
    }

    @bottom-right {
        content: "第 " counter(page) " 页";
        font-size: 10pt;
        font-family: Arial, sans-serif;
        color: #666;
    }
}

/* 基础样式 */
body {
    font-family: 'Helvetica Neue', 'Arial', 'Microsoft YaHei', sans-serif;
    font-size: 11pt;
    line-height: 1.6;
    color: #333;
    background: white;
}

/* 标题样式 */
h1 {
    font-size: 24pt;
    font-weight: bold;
    color: #1a1a1a;
    margin-top: 0;
    margin-bottom: 20pt;
    padding-bottom: 10pt;
    border-bottom: 3px solid #2E86DE;
}

h2 {
    font-size: 18pt;
    font-weight: bold;
    color: #2c3e50;
    margin-top: 24pt;
    margin-bottom: 12pt;
    padding-bottom: 6pt;
    border-bottom: 2px solid #ecf0f1;
    page-break-after: avoid;
}

h3 {
    font-size: 14pt;
    font-weight: bold;
    color: #34495e;
    margin-top: 16pt;
    margin-bottom: 8pt;
    page-break-after: avoid;
}

h4 {
    font-size: 12pt;
    font-weight: bold;
    color: #555;
    margin-top: 12pt;
    margin-bottom: 6pt;
}

/* 段落样式 */
p {
    margin-bottom: 8pt;
    text-align: justify;
    orphans: 3;
    widows: 3;
}

/* 列表样式 */
ul, ol {
    margin-bottom: 10pt;
    padding-left: 24pt;
}

li {
    margin-bottom: 4pt;
}

/* 表格样式 */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 12pt 0;
    font-size: 10pt;
    page-break-inside: avoid;
}

thead {
    background-color: #2E86DE;
    color: white;
}

th {
    padding: 8pt;
    text-align: left;
    font-weight: bold;
    border: 1px solid #ddd;
}

td {
    padding: 6pt 8pt;
    border: 1px solid #ddd;
}

tbody tr:nth-child(even) {
    background-color: #f8f9fa;
}

tbody tr:hover {
    background-color: #e8f4f8;
}

/* 代码块样式 */
code {
    font-family: 'Courier New', 'Consolas', monospace;
    font-size: 9pt;
    background-color: #f4f4f4;
    padding: 2pt 4pt;
    border-radius: 3pt;
}

pre {
    background-color: #f8f8f8;
    border: 1px solid #ddd;
    border-radius: 4pt;
    padding: 10pt;
    overflow-x: auto;
    page-break-inside: avoid;
}

pre code {
    background-color: transparent;
    padding: 0;
}

/* 引用样式 */
blockquote {
    border-left: 4pt solid #2E86DE;
    padding-left: 12pt;
    margin-left: 0;
    margin-right: 0;
    font-style: italic;
    color: #555;
    background-color: #f9f9f9;
    padding: 10pt 12pt;
    page-break-inside: avoid;
}

/* 分隔线 */
hr {
    border: none;
    border-top: 2px solid #ecf0f1;
    margin: 20pt 0;
}

/* 链接样式 */
a {
    color: #2E86DE;
    text-decoration: none;
}

a:hover {
    text-decoration: underline;
}

/* 图片样式 */
img {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 12pt auto;
    page-break-inside: avoid;
}

/* 页眉页脚 */
.header {
    text-align: center;
    margin-bottom: 30pt;
    page-break-after: avoid;
}

.document-title {
    font-size: 28pt;
    font-weight: bold;
    color: #1a1a1a;
    margin-bottom: 10pt;
}

.document-subtitle {
    font-size: 12pt;
    color: #666;
    font-style: italic;
}

.footer {
    margin-top: 30pt;
    padding-top: 12pt;
    border-top: 1px solid #ddd;
    text-align: center;
    font-size: 9pt;
    color: #999;
}

/* 强调文本 */
strong, b {
    font-weight: bold;
    color: #2c3e50;
}

em, i {
    font-style: italic;
}

/* 避免孤立的标题 */
h1, h2, h3, h4, h5, h6 {
    page-break-after: avoid;
}

/* 避免表格和图片跨页 */
table, img, pre, blockquote {
    page-break-inside: avoid;
}

/* 章节内容 */
.content {
    margin-top: 20pt;
}

/* 元数据样式 */
.metadata {
    background-color: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 4pt;
    padding: 12pt;
    margin: 12pt 0;
    font-size: 10pt;
}

/* 警告框样式 */
.warning {
    background-color: #fff3cd;
    border-left: 4pt solid #ffc107;
    padding: 10pt 12pt;
    margin: 12pt 0;
    page-break-inside: avoid;
}

.error {
    background-color: #f8d7da;
    border-left: 4pt solid #dc3545;
    padding: 10pt 12pt;
    margin: 12pt 0;
    page-break-inside: avoid;
}

.info {
    background-color: #d1ecf1;
    border-left: 4pt solid #17a2b8;
    padding: 10pt 12pt;
    margin: 12pt 0;
    page-break-inside: avoid;
}
"""

    def create_default_css_file(self):
        """
        创建默认的 CSS 文件（如果不存在）
        """
        if not self.css_path.exists():
            try:
                with open(self.css_path, 'w', encoding='utf-8') as f:
                    f.write(self._get_default_css())
                print(f"✅ 已创建默认 CSS 文件: {self.css_path}")
            except Exception as e:
                print(f"❌ 创建 CSS 文件失败: {e}")


# ================================
# 全局实例
# ================================

pdf_exporter = PDFExporter()

# 自动创建默认 CSS 文件
pdf_exporter.create_default_css_file()
