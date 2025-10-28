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

        # 临时文件目录
        self.temp_dir = Path(__file__).parent / "temp_pdf"
        self.temp_dir.mkdir(exist_ok=True)

    def export_to_pdf(
        self,
        markdown_content: str,
        output_path: str,
        title: Optional[str] = None,
        timeout: int = 30
    ) -> str:
        """
        将 Markdown 内容导出为 PDF（增强版，支持超时控制）

        Args:
            markdown_content: Markdown 格式的报告内容
            output_path: PDF 输出路径（绝对路径）
            title: 报告标题（可选）
            timeout: 生成超时时间（秒，默认30秒）

        Returns:
            str: 生成的 PDF 文件路径

        Raises:
            Exception: PDF 生成失败时抛出异常
        """
        import time
        from concurrent.futures import ThreadPoolExecutor, TimeoutError

        start_time = time.time()

        try:
            import markdown2
            from weasyprint import HTML, CSS

            print(f"  📄 开始PDF导出: {os.path.basename(output_path)}")

            # 1. Markdown → HTML
            print("  🔄 转换Markdown到HTML...")
            html_content = self._markdown_to_html(markdown_content, title)

            # 2. 应用 CSS 样式
            print("  🎨 应用CSS样式...")
            css = self._load_css()

            # 3. HTML → PDF（带超时控制）
            print(f"  ⚙️  生成PDF文件（超时: {timeout}秒）...")

            def generate_pdf():
                HTML(string=html_content).write_pdf(
                    output_path,
                    stylesheets=[CSS(string=css)] if css else None
                )

            # 使用线程池执行PDF生成，带超时控制
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(generate_pdf)
                try:
                    future.result(timeout=timeout)
                except TimeoutError:
                    raise Exception(f"PDF生成超时（>{timeout}秒）")

            # 验证文件是否生成成功
            if not os.path.exists(output_path):
                raise Exception("PDF文件生成失败：文件不存在")

            file_size = os.path.getsize(output_path)
            if file_size == 0:
                raise Exception("PDF文件生成失败：文件大小为0")

            elapsed_time = time.time() - start_time
            print(f"  ✅ PDF生成成功！文件大小: {file_size / 1024:.2f} KB, 耗时: {elapsed_time:.2f}秒")

            return output_path

        except ImportError as e:
            raise Exception(f"缺少依赖库: {str(e)}. 请安装: pip install markdown2 weasyprint")

        except TimeoutError:
            raise Exception(f"PDF 生成超时（超过 {timeout} 秒）")

        except Exception as e:
            # 清理可能生成的不完整文件
            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except:
                    pass

            elapsed_time = time.time() - start_time
            print(f"  ❌ PDF生成失败（耗时: {elapsed_time:.2f}秒）: {str(e)}")
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
    font-family: 'Noto Sans CJK SC', 'Noto Sans CJK TC', 'Microsoft YaHei',
                 'PingFang SC', 'Hiragino Sans GB', 'SimSun', 'SimHei',
                 'Arial Unicode MS', 'Helvetica Neue', 'Arial', sans-serif;
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

/* 图表样式 - 针对Base64嵌入的图片 */
img[src^="data:image"] {
    max-width: 100%;
    max-height: 500pt;
    height: auto;
    display: block;
    margin: 16pt auto;
    page-break-inside: avoid;
    border: 1px solid #e0e0e0;
    border-radius: 4pt;
    padding: 8pt;
    background-color: #ffffff;
    box-shadow: 0 2pt 4pt rgba(0,0,0,0.1);
}

/* 图表标题样式 */
h3 + img,
h4 + img {
    margin-top: 12pt;
}

/* 确保表格在PDF中正确渲染 */
table {
    table-layout: auto;
    word-wrap: break-word;
}

/* 表格单元格文本换行 */
td, th {
    word-wrap: break-word;
    overflow-wrap: break-word;
    max-width: 200pt;
}

/* 数字列右对齐 */
td:has(> :only-child:is(span, strong):matches("[0-9]+")) {
    text-align: right;
}

/* Emoji 支持 */
.emoji {
    font-family: 'Apple Color Emoji', 'Segoe UI Emoji', 'Noto Color Emoji', sans-serif;
}
"""

    def generate_temp_pdf_path(self, filename: str = None) -> str:
        """
        生成临时PDF文件路径

        Args:
            filename: 文件名（不含扩展名）

        Returns:
            str: 临时PDF文件的绝对路径
        """
        import uuid

        if not filename:
            filename = f"report_{uuid.uuid4().hex[:8]}"

        # 确保文件名安全
        safe_filename = "".join(c for c in filename if c.isalnum() or c in ('-', '_'))
        pdf_filename = f"{safe_filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        return str(self.temp_dir / pdf_filename)

    def cleanup_old_temp_files(self, max_age_hours: int = 24):
        """
        清理过期的临时PDF文件

        Args:
            max_age_hours: 文件最大保留时间（小时）
        """
        import time

        try:
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600

            deleted_count = 0
            for pdf_file in self.temp_dir.glob("*.pdf"):
                file_age = current_time - pdf_file.stat().st_mtime
                if file_age > max_age_seconds:
                    try:
                        pdf_file.unlink()
                        deleted_count += 1
                    except Exception as e:
                        print(f"  ⚠️  删除临时文件失败 {pdf_file.name}: {e}")

            if deleted_count > 0:
                print(f"  🧹 清理了 {deleted_count} 个过期的临时PDF文件")

        except Exception as e:
            print(f"  ⚠️  清理临时文件出错: {e}")

    def cleanup_temp_file(self, file_path: str):
        """
        清理指定的临时文件

        Args:
            file_path: 要删除的文件路径
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"  🗑️  已删除临时文件: {os.path.basename(file_path)}")
        except Exception as e:
            print(f"  ⚠️  删除临时文件失败: {e}")

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

# 自动清理过期的临时文件（24小时）
pdf_exporter.cleanup_old_temp_files(max_age_hours=24)
