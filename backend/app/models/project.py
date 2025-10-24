"""
项目相关数据模型
存储加密货币项目基本信息和快照数据
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Float, Integer, DateTime, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Project(Base):
    """
    加密货币项目表
    存储项目的基本信息和元数据
    """
    __tablename__ = "projects"

    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 项目标识
    symbol: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    coingecko_id: Mapped[Optional[str]] = mapped_column(String(100), unique=True, index=True)

    # 基本信息
    description: Mapped[Optional[str]] = mapped_column(Text)
    website: Mapped[Optional[str]] = mapped_column(String(500))
    whitepaper_url: Mapped[Optional[str]] = mapped_column(String(500))
    blockchain: Mapped[Optional[str]] = mapped_column(String(50))  # 主链: ethereum, bsc, solana等

    # 合约地址（JSON存储多链地址）
    contract_addresses: Mapped[Optional[dict]] = mapped_column(JSON)
    # 例: {"ethereum": "0x...", "bsc": "0x..."}

    # 社交媒体
    twitter_handle: Mapped[Optional[str]] = mapped_column(String(100))
    telegram_url: Mapped[Optional[str]] = mapped_column(String(200))
    discord_url: Mapped[Optional[str]] = mapped_column(String(200))
    reddit_url: Mapped[Optional[str]] = mapped_column(String(200))

    # 元数据
    categories: Mapped[Optional[list]] = mapped_column(JSON)  # ["DeFi", "DEX"]
    tags: Mapped[Optional[list]] = mapped_column(JSON)

    # 时间戳
    first_seen: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_updated: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # 关系
    snapshots: Mapped[list["ProjectSnapshot"]] = relationship(
        "ProjectSnapshot",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="ProjectSnapshot.timestamp.desc()"
    )
    reports: Mapped[list["Report"]] = relationship(
        "Report",
        back_populates="project",
        cascade="all, delete-orphan"
    )

    # 索引
    __table_args__ = (
        Index("ix_projects_symbol_name", "symbol", "name"),
        Index("ix_projects_blockchain", "blockchain"),
    )

    def __repr__(self):
        return f"<Project {self.symbol} - {self.name}>"


class ProjectSnapshot(Base):
    """
    项目数据快照表
    按时间序列存储项目的市场数据、链上数据、社交数据
    """
    __tablename__ = "project_snapshots"

    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 外键
    project_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # 时间戳
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    # ================================
    # 市场数据（来自CoinGecko）
    # ================================
    price_usd: Mapped[Optional[float]] = mapped_column(Float)
    price_btc: Mapped[Optional[float]] = mapped_column(Float)
    market_cap: Mapped[Optional[float]] = mapped_column(Float)
    total_volume_24h: Mapped[Optional[float]] = mapped_column(Float)
    circulating_supply: Mapped[Optional[float]] = mapped_column(Float)
    total_supply: Mapped[Optional[float]] = mapped_column(Float)
    max_supply: Mapped[Optional[float]] = mapped_column(Float)

    # 价格变化百分比
    price_change_24h: Mapped[Optional[float]] = mapped_column(Float)
    price_change_7d: Mapped[Optional[float]] = mapped_column(Float)
    price_change_30d: Mapped[Optional[float]] = mapped_column(Float)

    # 市值排名
    market_cap_rank: Mapped[Optional[int]] = mapped_column(Integer)

    # ================================
    # 链上数据（来自Etherscan/BSCScan）
    # ================================
    holder_count: Mapped[Optional[int]] = mapped_column(Integer)
    total_transactions: Mapped[Optional[int]] = mapped_column(Integer)
    transaction_count_24h: Mapped[Optional[int]] = mapped_column(Integer)
    active_addresses_24h: Mapped[Optional[int]] = mapped_column(Integer)

    # ================================
    # 社交数据（来自Twitter/Reddit）
    # ================================
    twitter_followers: Mapped[Optional[int]] = mapped_column(Integer)
    twitter_mentions_24h: Mapped[Optional[int]] = mapped_column(Integer)
    reddit_subscribers: Mapped[Optional[int]] = mapped_column(Integer)
    reddit_active_users: Mapped[Optional[int]] = mapped_column(Integer)

    # ================================
    # 情感分析
    # ================================
    sentiment_score: Mapped[Optional[float]] = mapped_column(Float)  # -1.0 到 1.0
    sentiment_volume: Mapped[Optional[int]] = mapped_column(Integer)  # 样本数量

    # ================================
    # 原始数据（JSON）
    # ================================
    raw_market_data: Mapped[Optional[dict]] = mapped_column(JSON)
    raw_onchain_data: Mapped[Optional[dict]] = mapped_column(JSON)
    raw_social_data: Mapped[Optional[dict]] = mapped_column(JSON)

    # 关系
    project: Mapped["Project"] = relationship("Project", back_populates="snapshots")

    # 索引
    __table_args__ = (
        Index("ix_snapshots_project_timestamp", "project_id", "timestamp"),
        Index("ix_snapshots_timestamp", "timestamp"),
    )

    def __repr__(self):
        return f"<ProjectSnapshot project_id={self.project_id} at {self.timestamp}>"
