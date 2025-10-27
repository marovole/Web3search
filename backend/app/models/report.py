"""
报告数据模型
存储生成的研究报告
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Integer, DateTime, JSON, Index, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.core.database import Base


class ReportType(str, enum.Enum):
    """报告类型枚举"""
    QUICK_CHAT = "quick_chat"  # 快速对话
    DEEP_RESEARCH = "deep_research"  # 深度研究


class ReportStatus(str, enum.Enum):
    """报告状态枚举"""
    PENDING = "pending"  # 等待生成
    PROCESSING = "processing"  # 生成中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败


class Report(Base):
    """
    研究报告表
    存储AI生成的加密货币项目分析报告
    """
    __tablename__ = "reports"

    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 外键
    project_id: Mapped[Optional[int]] = mapped_column(Integer, index=True)
    conversation_id: Mapped[Optional[int]] = mapped_column(Integer, index=True)

    # 报告元数据
    report_type: Mapped[ReportType] = mapped_column(
        SQLEnum(ReportType, native_enum=False),
        nullable=False,
        index=True
    )
    status: Mapped[ReportStatus] = mapped_column(
        SQLEnum(ReportStatus, native_enum=False),
        default=ReportStatus.PENDING,
        nullable=False,
        index=True
    )

    # 用户查询
    query: Mapped[str] = mapped_column(Text, nullable=False)

    # 报告标题
    title: Mapped[Optional[str]] = mapped_column(String(500))

    # 报告内容（Markdown格式）
    content_markdown: Mapped[Optional[str]] = mapped_column(Text)

    # TL;DR摘要
    tldr: Mapped[Optional[str]] = mapped_column(Text)

    # 报告章节（JSON存储结构化内容）
    sections: Mapped[Optional[dict]] = mapped_column(JSON)
    # 例: {
    #   "overview": {...},
    #   "technical_analysis": {...},
    #   "market_analysis": {...},
    #   "community_analysis": {...},
    #   "risk_assessment": {...},
    #   "competitor_comparison": {...}
    # }

    # 数据来源
    data_sources: Mapped[Optional[list]] = mapped_column(JSON)
    # 例: ["coingecko", "etherscan", "twitter", "reddit"]

    # 使用的模型
    models_used: Mapped[Optional[dict]] = mapped_column(JSON)
    # 例: {
    #   "summary": "qwen/qwen3-235b-a22b:free",
    #   "analysis": "deepseek/deepseek-r1-0528:free"
    # }

    # 统计信息
    generation_time_seconds: Mapped[Optional[float]] = mapped_column(JSON)  # 生成耗时
    token_usage: Mapped[Optional[dict]] = mapped_column(JSON)  # Token使用量
    # 例: {"prompt_tokens": 1000, "completion_tokens": 2000, "total_tokens": 3000}

    # 质量评分（0-100）
    quality_score: Mapped[Optional[int]] = mapped_column(Integer)

    # 错误信息（如果失败）
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    # PDF导出路径
    pdf_path: Mapped[Optional[str]] = mapped_column(String(500))

    # 分享功能
    share_token: Mapped[Optional[str]] = mapped_column(String(64), unique=True, index=True)
    share_enabled: Mapped[bool] = mapped_column(default=False, nullable=False)
    share_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # 用于项目识别的符号
    symbol: Mapped[Optional[str]] = mapped_column(String(20), index=True)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # 关系
    project: Mapped[Optional["Project"]] = relationship("Project", back_populates="reports")
    conversation: Mapped[Optional["Conversation"]] = relationship(
        "Conversation",
        back_populates="reports"
    )

    # 索引
    __table_args__ = (
        # 复合索引：按项目和创建时间查询
        Index("ix_reports_project_created", "project_id", "created_at"),
        # 复合索引：按类型和状态筛选
        Index("ix_reports_type_status", "report_type", "status"),
        # 复合索引：按符号和创建时间查询（常用于获取特定加密货币的最新报告）
        Index("ix_reports_symbol_created", "symbol", "created_at"),
        # 复合索引：按状态和创建时间（用于管理界面显示待处理报告）
        Index("ix_reports_status_created", "status", "created_at"),
        # 复合索引：按符号、类型和状态（用于精确筛选）
        Index("ix_reports_symbol_type_status", "symbol", "report_type", "status"),
        # 注意：created_at已经通过 index=True 创建了索引，无需重复定义
    )

    def __repr__(self):
        return f"<Report {self.id} - {self.report_type.value} - {self.status.value}>"

    @property
    def is_completed(self) -> bool:
        """报告是否已完成"""
        return self.status == ReportStatus.COMPLETED

    @property
    def is_failed(self) -> bool:
        """报告是否失败"""
        return self.status == ReportStatus.FAILED

    @property
    def is_processing(self) -> bool:
        """报告是否正在生成"""
        return self.status == ReportStatus.PROCESSING

    @property
    def is_share_valid(self) -> bool:
        """分享链接是否有效"""
        if not self.share_enabled or not self.share_token:
            return False
        if self.share_expires_at and self.share_expires_at < datetime.utcnow():
            return False
        return True

    def generate_share_token(self) -> str:
        """生成分享令牌"""
        import secrets
        self.share_token = secrets.token_urlsafe(32)
        return self.share_token

    def enable_sharing(self, expires_in_days: Optional[int] = None) -> str:
        """启用分享"""
        if not self.share_token:
            self.generate_share_token()
        self.share_enabled = True
        if expires_in_days:
            from datetime import timedelta
            self.share_expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        return self.share_token

    def disable_sharing(self):
        """禁用分享"""
        self.share_enabled = False
