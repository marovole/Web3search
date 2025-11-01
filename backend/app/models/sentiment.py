"""
社交情绪分析数据模型
定义社交情绪相关的数据库模型和ORM映射
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class SentimentAnalysis(Base):
    """情感分析主表"""
    __tablename__ = "sentiment_analysis"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), index=True, nullable=False)
    platform = Column(String(20), nullable=False)  # twitter, reddit, telegram, comprehensive
    sentiment_score = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    classification = Column(String(20), nullable=False)  # positive, negative, neutral, strong_positive, strong_negative
    
    # 数据量指标
    volume = Column(Integer, default=0)  # 帖子/消息/推文数量
    engagement = Column(Integer, default=0)  # 总参与度（点赞、评论、转发等）
    
    # 情感分布
    sentiment_distribution = Column(JSON)  # {"positive": 60.5, "negative": 20.3, "neutral": 19.2}
    
    # 详细数据
    raw_data = Column(JSON)  # 原始平台数据
    insights = Column(JSON)  # 分析洞察
    
    # 时间范围
    time_range_hours = Column(Integer, default=24)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    kol_analysis = relationship("KOLAnalysis", back_populates="sentiment", uselist=False)
    platform_metrics = relationship("PlatformMetrics", back_populates="sentiment", cascade="all, delete-orphan")


class KOLAnalysis(Base):
    """KOL（关键意见领袖）分析表"""
    __tablename__ = "kol_analysis"

    id = Column(Integer, primary_key=True, index=True)
    sentiment_id = Column(Integer, ForeignKey("sentiment_analysis.id"), nullable=False)
    
    # KOL统计
    kol_count = Column(Integer, default=0)
    positive_kol_count = Column(Integer, default=0)
    negative_kol_count = Column(Integer, default=0)
    neutral_kol_count = Column(Integer, default=0)
    
    # 加权情感得分
    weighted_sentiment_score = Column(Float, default=0.0)
    total_engagement = Column(Integer, default=0)
    
    # KOL详细信息
    kol_details = Column(JSON)  # [{"username": "...", "sentiment": "...", "engagement": "..."}]
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    sentiment = relationship("SentimentAnalysis", back_populates="kol_analysis")


class PlatformMetrics(Base):
    """平台指标详细数据表"""
    __tablename__ = "platform_metrics"

    id = Column(Integer, primary_key=True, index=True)
    sentiment_id = Column(Integer, ForeignKey("sentiment_analysis.id"), nullable=False)
    platform = Column(String(20), nullable=False)  # twitter, reddit, telegram
    
    # 平台特定指标
    platform_sentiment_score = Column(Float, default=0.0)
    platform_volume = Column(Integer, default=0)
    platform_engagement = Column(Integer, default=0)
    
    # 权重和影响力
    platform_weight = Column(Float, default=0.0)
    influence_factor = Column(Float, default=1.0)
    
    # 平台详细数据
    platform_data = Column(JSON)  # 平台原始数据
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    sentiment = relationship("SentimentAnalysis", back_populates="platform_metrics")


class SentimentTrend(Base):
    """情感趋势数据表"""
    __tablename__ = "sentiment_trend"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), index=True, nullable=False)
    date = Column(DateTime, index=True, nullable=False)
    
    # 日情感指标
    daily_sentiment_avg = Column(Float, default=0.0)
    daily_sentiment_high = Column(Float, default=0.0)
    daily_sentiment_low = Column(Float, default=0.0)
    
    # 日数据量
    daily_volume = Column(Integer, default=0)
    daily_engagement = Column(Integer, default=0)
    
    # 趋势方向
    trend_direction = Column(String(20), default="neutral")  # up, down, neutral
    trend_strength = Column(Float, default=0.0)  # 趋势强度 0-1
    
    # 平台贡献度
    platform_contributions = Column(JSON)  # {"twitter": 0.4, "reddit": 0.35, "telegram": 0.25}
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TrendingTopic(Base):
    """热门话题数据表"""
    __tablename__ = "trending_topics"

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(String(100), index=True, nullable=False)  # 唯一话题标识
    title = Column(String(500), nullable=False)
    content_preview = Column(Text)
    
    # 来源平台
    source_platform = Column(String(20), nullable=False)  # twitter, reddit, telegram
    
    # 热度指标
    engagement_score = Column(Integer, default=0)
    view_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    
    # 加密货币相关性
    mentioned_symbols = Column(JSON)  # ["BTC", "ETH", "DOGE"]
    crypto_relevance_score = Column(Float, default=0.0)
    
    # 时间信息
    first_seen = Column(DateTime, default=datetime.utcnow)
    peak_time = Column(DateTime)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 状态
    is_active = Column(Boolean, default=True)
    trend_score = Column(Float, default=0.0)
    
    # 详细数据
    metadata = Column(JSON)  # 额外的元数据
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SentimentAlert(Base):
    """情感预警数据表"""
    __tablename__ = "sentiment_alerts"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), index=True, nullable=False)
    alert_type = Column(String(50), nullable=False)  # sentiment_spike, volume_surge, unusual_pattern
    
    # 预警级别
    severity = Column(String(20), default="medium")  # low, medium, high, critical
    
    # 预警条件
    trigger_value = Column(Float)  # 触发值
    threshold_value = Column(Float)  # 阈值
    change_percentage = Column(Float)  # 变化百分比
    
    # 预警内容
    title = Column(String(200), nullable=False)
    description = Column(Text)
    recommendation = Column(Text)  # 建议措施
    
    # 状态
    is_active = Column(Boolean, default=True)
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(String(100))
    acknowledged_at = Column(DateTime)
    
    # 时间信息
    triggered_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)
    
    # 相关数据
    related_sentiment_id = Column(Integer, ForeignKey("sentiment_analysis.id"))
    context_data = Column(JSON)  # 额外的上下文数据
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SocialPlatformConfig(Base):
    """社交平台配置表"""
    __tablename__ = "social_platform_config"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String(20), unique=True, nullable=False)  # twitter, reddit, telegram
    
    # API配置
    api_endpoint = Column(String(500))
    rate_limit_per_hour = Column(Integer, default=100)
    timeout_seconds = Column(Integer, default=30)
    
    # 数据采集配置
    max_results_per_request = Column(Integer, default=100)
    default_time_range_hours = Column(Integer, default=24)
    
    # 权重配置
    default_weight = Column(Float, default=0.0)
    influence_multiplier = Column(Float, default=1.0)
    
    # 状态
    is_enabled = Column(Boolean, default=True)
    last_success_at = Column(DateTime)
    error_count = Column(Integer, default=0)
    last_error = Column(Text)
    
    # 特定配置
    config_data = Column(JSON)  # 平台特定配置
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
