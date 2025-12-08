from __future__ import annotations

import enum
from datetime import datetime
from typing import List, Optional

from sqlalchemy import JSON, DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ReportType(str, enum.Enum):
    deep_research = "deep_research"
    quick_analysis = "quick_analysis"


class ReportStatus(str, enum.Enum):
    completed = "completed"
    processing = "processing"
    failed = "failed"


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("users.id"), nullable=True)
    symbol: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    query: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    content_markdown: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    tldr: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    report_type: Mapped[ReportType] = mapped_column(Enum(ReportType), default=ReportType.deep_research)
    status: Mapped[ReportStatus] = mapped_column(Enum(ReportStatus), default=ReportStatus.processing)
    quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    generation_time_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    data_sources: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Report {self.id} {self.symbol}>"
