"""
Report Generation Module
Generates Markdown reports, tables, charts, PDFs, and validates quality
"""
from app.services.report.report_generator import ReportGenerator, report_generator
from app.services.report.markdown_builder import MarkdownBuilder, markdown_builder
from app.services.report.table_generator import TableGenerator, table_generator
from app.services.report.chart_generator import ChartGenerator, chart_generator
from app.services.report.pdf_exporter import PDFExporter, pdf_exporter
from app.services.report.quality_validator import (
    ReportQualityValidator,
    quality_validator,
    validate_markdown_syntax,
    estimate_reading_time
)

__all__ = [
    # Legacy
    "ReportGenerator",
    "report_generator",
    # Markdown Builder
    "MarkdownBuilder",
    "markdown_builder",
    # Table Generator
    "TableGenerator",
    "table_generator",
    # Chart Generator
    "ChartGenerator",
    "chart_generator",
    # PDF Exporter
    "PDFExporter",
    "pdf_exporter",
    # Quality Validator
    "ReportQualityValidator",
    "quality_validator",
    "validate_markdown_syntax",
    "estimate_reading_time",
]
