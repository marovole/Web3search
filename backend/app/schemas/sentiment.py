"""
社交情绪分析相关的Pydantic模型
定义API请求和响应的数据结构
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum


class PlatformEnum(str, Enum):
    """支持的社交平台枚举"""
    TWITTER = "twitter"
    REDDIT = "reddit"
    TELEGRAM = "telegram"
    COMPREHENSIVE = "comprehensive"


class SentimentClassification(str, Enum):
    """情感分类枚举"""
    STRONG_POSITIVE = "strong_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    STRONG_NEGATIVE = "strong_negative"


class AlertSeverity(str, Enum):
    """预警级别枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# 请求模型
class SentimentRequest(BaseModel):
    """情感分析请求模型"""
    symbol: str = Field(..., min_length=1, max_length=20, description="币种符号")
    time_range_hours: int = Field(24, ge=1, le=168, description="时间范围（小时）")
    platforms: Optional[List[PlatformEnum]] = Field(None, description="要分析的平台列表")
    include_kol: bool = Field(True, description="是否包含KOL分析")
    save_to_db: bool = Field(True, description="是否保存到数据库")
    
    @validator('symbol')
    def validate_symbol(cls, v):
        return v.upper().strip()


class SentimentComparisonRequest(BaseModel):
    """情感对比分析请求模型"""
    symbols: List[str] = Field(..., min_items=1, max_items=10, description="币种符号列表")
    time_range_hours: int = Field(24, ge=1, le=168, description="时间范围（小时）")
    
    @validator('symbols')
    def validate_symbols(cls, v):
        return [symbol.upper().strip() for symbol in v]


# 响应模型
class BaseResponse(BaseModel):
    """基础响应模型"""
    success: bool
    message: str
    timestamp: str


class PlatformBreakdown(BaseModel):
    """平台分解数据模型"""
    sentiment_score: float
    volume: int
    engagement: int
    weight: float
    data: Dict[str, Any]


class KOLAnalysis(BaseModel):
    """KOL分析数据模型"""
    kol_count: int
    positive_kol_count: int
    negative_kol_count: int
    neutral_kol_count: int
    weighted_sentiment_score: float
    total_engagement: int
    kol_sentiments: List[Dict[str, Any]]


class TrendAnalysis(BaseModel):
    """趋势分析数据模型"""
    volume_trend: str
    sentiment_trend: str


class SentimentData(BaseModel):
    """情感分析数据模型"""
    symbol: str
    time_range_hours: int
    final_sentiment_score: float
    confidence: float
    sentiment_classification: SentimentClassification
    total_volume: int
    total_engagement: int
    active_platforms: int
    sentiment_distribution: Dict[str, float]
    platform_breakdown: Dict[str, PlatformBreakdown]
    kol_analysis: Optional[KOLAnalysis]
    trend_analysis: Dict[str, TrendAnalysis]
    insights: List[str]
    timestamp: str


class SentimentResponse(BaseResponse):
    """情感分析响应模型"""
    data: SentimentData


class TrendingTopic(BaseModel):
    """热门话题数据模型"""
    title: str
    content_preview: Optional[str]
    source_platform: str
    engagement_score: int
    view_count: Optional[int]
    share_count: Optional[int]
    comment_count: Optional[int]
    mentioned_symbols: List[str]
    crypto_relevance_score: float
    first_seen: Optional[str]
    peak_time: Optional[str]
    last_updated: str
    is_active: bool
    trend_score: float


class TrendingTopicsData(BaseModel):
    """热门话题数据模型"""
    topics: List[TrendingTopic]
    total_topics: int
    platforms: List[str]
    time_range_hours: int


class TrendingTopicsResponse(BaseResponse):
    """热门话题响应模型"""
    data: TrendingTopicsData


class SentimentComparisonItem(BaseModel):
    """情感对比项目模型"""
    symbol: str
    sentiment_score: float
    confidence: float
    volume: int
    engagement: int
    classification: SentimentClassification
    platforms: int


class SentimentComparisonData(BaseModel):
    """情感对比数据模型"""
    comparisons: List[SentimentComparisonItem]
    time_range_hours: int
    total_symbols: int


class SentimentComparisonResponse(BaseResponse):
    """情感对比响应模型"""
    data: SentimentComparisonData


class SentimentHistoryItem(BaseModel):
    """情感历史数据模型"""
    date: str
    sentiment_score: float
    confidence: float
    classification: SentimentClassification
    volume: int
    engagement: int
    sentiment_distribution: Dict[str, float]


class SentimentHistoryData(BaseModel):
    """情感历史数据模型"""
    symbol: str
    time_range_days: int
    history: List[SentimentHistoryItem]
    total_records: int


class SentimentAlert(BaseModel):
    """情感预警数据模型"""
    id: int
    symbol: str
    sentiment_score: float
    classification: SentimentClassification
    confidence: float
    volume: int
    created_at: str
    insights: Optional[List[str]]


class SentimentAlertData(BaseModel):
    """情感预警数据模型"""
    alerts: List[SentimentAlert]
    total_count: int
    filters: Dict[str, Any]


class SentimentAlertResponse(BaseResponse):
    """情感预警响应模型"""
    data: SentimentAlertData


class PlatformStatus(BaseModel):
    """平台状态数据模型"""
    name: str
    enabled: bool
    rate_limit: int
    weight: float
    description: str
    last_success: Optional[str]
    error_count: int


class PlatformStatusData(BaseModel):
    """平台状态数据模型"""
    platforms: Dict[str, PlatformStatus]
    total_enabled: int
    engine_status: str


class SentimentStatsData(BaseModel):
    """情感统计数据模型"""
    time_range_days: int
    total_analyses: int
    sentiment_distribution: Dict[str, Union[int, float]]
    average_sentiment: float
    popular_symbols: List[Dict[str, Any]]


# WebSocket消息模型
class WebSocketMessage(BaseModel):
    """WebSocket消息基础模型"""
    type: str
    timestamp: str
    data: Dict[str, Any]


class SentimentUpdateMessage(WebSocketMessage):
    """情感更新消息模型"""
    type: str = "sentiment_update"
    data: SentimentData


class AlertTriggerMessage(WebSocketMessage):
    """预警触发消息模型"""
    type: str = "alert_triggered"
    data: SentimentAlert


class TrendingTopicUpdateMessage(WebSocketMessage):
    """热门话题更新消息模型"""
    type: str = "trending_topics_update"
    data: TrendingTopicsData


# 批量操作模型
class BatchSentimentRequest(BaseModel):
    """批量情感分析请求模型"""
    symbols: List[str] = Field(..., min_items=1, max_items=50, description="币种符号列表")
    time_range_hours: int = Field(24, ge=1, le=168, description="时间范围（小时）")
    platforms: Optional[List[PlatformEnum]] = Field(None, description="要分析的平台列表")
    include_kol: bool = Field(True, description="是否包含KOL分析")
    
    @validator('symbols')
    def validate_symbols(cls, v):
        return [symbol.upper().strip() for symbol in v]


class BatchSentimentResponse(BaseResponse):
    """批量情感分析响应模型"""
    data: List[SentimentData]
    total_processed: int
    failed_symbols: List[str]


# 配置模型
class PlatformConfig(BaseModel):
    """平台配置模型"""
    platform: PlatformEnum
    enabled: bool = True
    rate_limit_per_hour: int = Field(100, ge=1, le=1000)
    timeout_seconds: int = Field(30, ge=5, le=300)
    max_results_per_request: int = Field(100, ge=1, le=1000)
    default_weight: float = Field(0.33, ge=0.0, le=1.0)
    influence_multiplier: float = Field(1.0, ge=0.1, le=5.0)


class SentimentEngineConfig(BaseModel):
    """情感分析引擎配置模型"""
    enable_vader: bool = True
    enable_bert: bool = False
    enable_keywords: bool = True
    enable_emoji: bool = True
    cache_ttl_seconds: int = Field(300, ge=60, le=3600)
    batch_size: int = Field(10, ge=1, le=100)
    kol_weight_factor: float = Field(2.0, ge=1.0, le=10.0)
    platforms: List[PlatformConfig]
