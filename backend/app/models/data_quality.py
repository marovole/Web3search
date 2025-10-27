"""
数据质量报告数据模型（任务6.7）

存储数据质量检查报告和指标
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Float, Integer, DateTime, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class DataQualityReport(Base):
    """
    数据质量报告表（任务6.7）

    按时间序列存储数据质量检查结果
    """
    __tablename__ = "data_quality_reports"

    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 时间戳
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    # ================================
    # 聚合指标
    # ================================
    total_projects_checked: Mapped[int] = mapped_column(Integer, default=0)

    # 平均质量指标（任务6.6）
    avg_completeness: Mapped[float] = mapped_column(Float, default=0.0)  # 平均完整度
    avg_accuracy: Mapped[float] = mapped_column(Float, default=0.0)  # 平均准确度
    avg_timeliness: Mapped[float] = mapped_column(Float, default=0.0)  # 平均时效性
    avg_overall_score: Mapped[float] = mapped_column(Float, default=0.0)  # 平均综合得分

    # ================================
    # 告警统计（任务6.1-6.5）
    # ================================
    price_anomalies_count: Mapped[int] = mapped_column(Integer, default=0)  # 价格异常数量
    market_cap_inconsistencies_count: Mapped[int] = mapped_column(Integer, default=0)  # 市值不一致数量
    stale_data_count: Mapped[int] = mapped_column(Integer, default=0)  # 过期数据数量
    incomplete_data_count: Mapped[int] = mapped_column(Integer, default=0)  # 不完整数据数量
    zscore_anomalies_count: Mapped[int] = mapped_column(Integer, default=0)  # Z-score异常数量

    # 总问题数
    total_warnings: Mapped[int] = mapped_column(Integer, default=0)
    total_errors: Mapped[int] = mapped_column(Integer, default=0)
    total_critical: Mapped[int] = mapped_column(Integer, default=0)

    # ================================
    # 质量等级分布
    # ================================
    excellent_count: Mapped[int] = mapped_column(Integer, default=0)  # 优秀（>=0.9）
    good_count: Mapped[int] = mapped_column(Integer, default=0)  # 良好（>=0.7）
    fair_count: Mapped[int] = mapped_column(Integer, default=0)  # 一般（>=0.5）
    poor_count: Mapped[int] = mapped_column(Integer, default=0)  # 差（<0.5）

    # ================================
    # 详细结果（JSON）
    # ================================
    detailed_results: Mapped[Optional[dict]] = mapped_column(JSON)  # 每个项目的详细质量报告
    summary: Mapped[Optional[dict]] = mapped_column(JSON)  # 汇总统计信息

    # 索引
    __table_args__ = (
        Index("ix_data_quality_reports_timestamp", "timestamp"),
        Index("ix_data_quality_reports_overall_score", "avg_overall_score"),
    )

    def __repr__(self):
        return f"<DataQualityReport at {self.timestamp} (avg_score={self.avg_overall_score:.3f})>"
