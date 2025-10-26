"""
热点/趋势API端点
提供市场热点识别和趋势分析功能
"""
from fastapi import APIRouter, Query
from typing import List
from pydantic import BaseModel

from app.services.hotspot_analyzer import hotspot_analyzer

# 创建router
router = APIRouter()


# ================================
# Response Models
# ================================


class ScoresBreakdown(BaseModel):
    """热点分数明细"""

    twitter: float
    reddit: float
    price: float
    volume: float
    news: float


class HotspotItem(BaseModel):
    """热点项目"""

    coin_id: str
    symbol: str
    name: str
    market_cap_rank: int
    price_usd: float | None = None
    price_change_24h: float | None = None
    volume_24h: float | None = None
    total_score: float
    scores_breakdown: ScoresBreakdown
    timestamp: str


class HotspotsResponse(BaseModel):
    """热点列表响应"""

    hotspots: List[HotspotItem]
    count: int
    updated_at: str


# ================================
# API Endpoints
# ================================


@router.get("/trending/hotspots", response_model=HotspotsResponse)
async def get_hotspots(
    limit: int = Query(default=10, ge=1, le=50, description="返回数量"),
    force_refresh: bool = Query(default=False, description="强制刷新（忽略缓存）"),
) -> HotspotsResponse:
    """
    获取当前市场热点

    根据多个维度自动识别当前最热门的加密货币项目：
    - Twitter提及量（25%权重）
    - Reddit讨论量（20%权重）
    - 24h价格变化（30%权重）
    - 24h交易量（15%权重）
    - 新闻数量（10%权重）

    Args:
        limit: 返回热点数量（1-50）
        force_refresh: 强制刷新，忽略缓存

    Returns:
        HotspotsResponse: 热点列表

    Example:
        GET /api/v1/trending/hotspots?limit=10

        Response:
        {
            "hotspots": [
                {
                    "coin_id": "bitcoin",
                    "symbol": "BTC",
                    "name": "Bitcoin",
                    "market_cap_rank": 1,
                    "price_usd": 45000.0,
                    "price_change_24h": 5.2,
                    "volume_24h": 30000000000,
                    "total_score": 85.5,
                    "scores_breakdown": {
                        "twitter": 22.5,
                        "reddit": 18.0,
                        "price": 25.5,
                        "volume": 14.5,
                        "news": 5.0
                    },
                    "timestamp": "2025-01-26T10:00:00"
                }
            ],
            "count": 1,
            "updated_at": "2025-01-26T10:00:00"
        }
    """
    from datetime import datetime

    # 获取热点数据
    hotspots = await hotspot_analyzer.get_hotspots(limit=limit, force_refresh=force_refresh)

    # 转换为响应格式
    items = [HotspotItem(**hotspot) for hotspot in hotspots]

    return HotspotsResponse(
        hotspots=items, count=len(items), updated_at=datetime.utcnow().isoformat()
    )
