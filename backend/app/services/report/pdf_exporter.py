from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any


class PDFExporter:
    async def export_report(self, report: Any) -> Path:
        """Create a stub PDF file for the given report and return its path."""
        content = getattr(report, "content_markdown", "Report export") or "Report export"
        fd, path_str = tempfile.mkstemp(suffix=".pdf")
        with open(fd, "w") as f:
            f.write(content if isinstance(content, str) else str(content))
        return Path(path_str)


pdf_exporter = PDFExporter()
