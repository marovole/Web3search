"""
热点/趋势API端点
提供市场热点识别和趋势分析功能
"""
from fastapi import APIRouter, Query, HTTPException
from typing import List
from pydantic import BaseModel, ValidationError

from app.services.hotspot_analyzer import hotspot_analyzer
import traceback

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


@router.get(
    "/trending/hotspots",
    response_model=HotspotsResponse,
    summary="获取市场热点",
    description="多维度识别当前最热门的加密货币",
    tags=["Trending"],
    responses={
        200: {
            "description": "成功返回热点列表",
            "content": {
                "application/json": {
                    "example": {
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
                }
            }
        },
        500: {"description": "服务器内部错误"},
    }
)
async def get_hotspots(
    limit: int = Query(default=10, ge=1, le=50, description="返回数量"),
    force_refresh: bool = Query(default=False, description="强制刷新（忽略缓存）"),
) -> HotspotsResponse:
    """
    获取市场热点 - 多维度识别热门加密货币

    该端点使用多个维度的实时数据,自动识别当前市场最热门的加密货币项目。

    **评分算法:**
    热点得分基于5个维度的加权计算（总分100分）：
    - 🐦 Twitter提及量（25%权重）- 社交媒体热度
    - 💬 Reddit讨论量（20%权重）- 社区活跃度
    - 📈 24h价格变化（30%权重）- 市场表现
    - 💰 24h交易量（15%权重）- 流动性指标
    - 📰 新闻数量（10%权重）- 媒体关注度

    **特性:**
    - ⚡ 每15分钟更新一次
    - 📊 多维度综合评分
    - 🔄 支持强制刷新
    - 💾 Redis缓存加速

    **速率限制:**
    - 30次/分钟（基于IP）

    **请求示例:**
    ```bash
    # 获取Top 10热点
    curl "http://localhost:8000/api/v1/trending/hotspots?limit=10"

    # 获取Top 20热点，强制刷新
    curl "http://localhost:8000/api/v1/trending/hotspots?limit=20&force_refresh=true"
    ```

    **响应示例:**
    ```json
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
    ```

    **得分解读:**
    - 80-100分: 🔥 极热（强烈关注）
    - 60-79分: 🌡️ 热门（值得关注）
    - 40-59分: 📊 活跃（正常水平）
    - <40分: 📉 冷清（关注度低）

    **用途:**
    - 🎯 发现市场机会
    - 📰 追踪热门话题
    - 💡 投资决策参考
    - 🔔 监控市场动态

    **数据源:**
    - CoinGecko - 价格和交易量
    - Twitter API - 社交媒体数据
    - Reddit API - 社区讨论数据
    - CryptoPanic - 新闻数据
    """
    from datetime import datetime

    try:
        # 获取热点数据
        hotspots = await hotspot_analyzer.get_hotspots(limit=limit, force_refresh=force_refresh)
        
        # 处理空结果
        if not hotspots:
            return HotspotsResponse(
                hotspots=[], count=0, updated_at=datetime.utcnow().isoformat()
            )

        # 转换为响应格式，过滤无效数据
        items = []
        for hotspot in hotspots:
            try:
                # 验证必需字段
                if not hotspot.get("coin_id") or not hotspot.get("symbol") or not hotspot.get("name"):
                    print(f"⚠️ 跳过无效热点项: 缺少必需字段")
                    continue
                
                # 确保scores_breakdown存在
                if "scores_breakdown" not in hotspot:
                    print(f"⚠️ 跳过无效热点项: 缺少scores_breakdown")
                    continue
                
                items.append(HotspotItem(**hotspot))
            except ValidationError as e:
                print(f"⚠️ 跳过无效热点项: {e}")
                continue
            except Exception as e:
                print(f"⚠️ 处理热点项时出错: {e}")
                continue

        return HotspotsResponse(
            hotspots=items, count=len(items), updated_at=datetime.utcnow().isoformat()
        )
    
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        # 记录详细错误信息
        error_msg = str(e)
        print(f"❌ 获取热点数据错误: {error_msg}")
        traceback.print_exc()
        
        # 返回友好的错误响应
        raise HTTPException(
            status_code=500,
            detail=f"热点分析服务暂时不可用，请稍后重试。错误: {error_msg if 'DEBUG' in str(e) else '服务内部错误'}"
        )
