"""
搜索API端点
提供加密货币搜索和自动补全功能
"""
from fastapi import APIRouter, Query, Depends
from typing import List
from pydantic import BaseModel

from app.services.collectors.coingecko import coingecko_collector
from app.core.business_tracker import track_feature_usage, tracker
from app.core.business_metrics import FeatureType
from app.core.funnel_analyzer import funnel_analyzer, FunnelType, FunnelStage
from app.core.conversion_monitor import conversion_monitor, ConversionEventType, ConversionEvent
from app.api.middleware.auth import optional_auth
from app.models.user import User
from app.core.redis_client import get_redis_client
import time
from datetime import datetime

# 创建router
router = APIRouter()


# ================================
# Response Models
# ================================


class AutocompleteItem(BaseModel):
    """搜索自动补全项"""

    coingecko_id: str
    symbol: str
    name: str
    market_cap_rank: int | None = None
    thumb: str | None = None


class AutocompleteResponse(BaseModel):
    """搜索自动补全响应"""

    results: List[AutocompleteItem]
    count: int


# ================================
# API Endpoints
# ================================


@router.get(
    "/search/autocomplete",
    response_model=AutocompleteResponse,
    summary="搜索自动补全",
    description="根据用户输入返回匹配的加密货币列表",
    tags=["Search"],
    responses={
        200: {
            "description": "成功返回搜索结果",
            "content": {
                "application/json": {
                    "example": {
                        "results": [
                            {
                                "coingecko_id": "bitcoin",
                                "symbol": "BTC",
                                "name": "Bitcoin",
                                "market_cap_rank": 1,
                                "thumb": "https://..."
                            }
                        ],
                        "count": 1
                    }
                }
            }
        },
        400: {"description": "搜索关键词无效"},
        500: {"description": "服务器内部错误"},
    }
)
@track_feature_usage(FeatureType.SEARCH, "autocomplete_search")
async def autocomplete_search(
    q: str = Query(..., min_length=1, max_length=100, description="搜索关键词"),
    current_user: User | None = Depends(optional_auth),
) -> AutocompleteResponse:
    """
    搜索自动补全API - 实时搜索加密货币

    该端点根据用户输入的关键词,返回匹配的加密货币列表。支持按币种名称或符号搜索。

    **特性:**
    - ⚡ 快速响应（< 500ms）
    - 🔍 模糊搜索（支持部分匹配）
    - 📊 按市值排名排序
    - 🖼️ 包含币种图标
    - 💰 CoinGecko数据源

    **搜索策略:**
    - 优先匹配币种符号（如 "BTC" → Bitcoin）
    - 其次匹配币种名称（如 "bit" → Bitcoin, BitTorrent）
    - 最多返回10个结果

    **速率限制:**
    - 30次/分钟（基于IP）

    **请求示例:**
    ```bash
    # 搜索BTC
    curl "http://localhost:8000/api/v1/search/autocomplete?q=btc"

    # 搜索包含"uni"的币种
    curl "http://localhost:8000/api/v1/search/autocomplete?q=uni"
    ```

    **响应示例:**
    ```json
    {
      "results": [
        {
          "coingecko_id": "bitcoin",
          "symbol": "BTC",
          "name": "Bitcoin",
          "market_cap_rank": 1,
          "thumb": "https://assets.coingecko.com/coins/images/1/thumb/bitcoin.png"
        },
        {
          "coingecko_id": "bitcoin-cash",
          "symbol": "BCH",
          "name": "Bitcoin Cash",
          "market_cap_rank": 20,
          "thumb": "https://..."
        }
      ],
      "count": 2
    }
    ```

    **用途:**
    - 🔍 前端搜索框自动补全
    - 📝 用户输入验证
    - 🎯 币种选择器
    """
    start_time = time.time()
    
    # 调用CoinGecko搜索
    results = await coingecko_collector.search_coins(q)
    
    # 转换为响应格式
    items = [AutocompleteItem(**item) for item in results]
    
    # 追踪搜索业务指标
    if current_user:
        try:
            await tracker.track_search_query(
                user_id=current_user.id,
                query=q,
                results_count=len(items),
                duration_ms=(time.time() - start_time) * 1000
            )
            
            # 检查是否是首次搜索
            redis_client = get_redis_client()
            search_history_key = f"search_history:{current_user.id}"
            first_search = await redis_client.get(search_history_key) is None
            
            if first_search:
                # 追踪首次搜索漏斗事件
                await funnel_analyzer.track_funnel_event(
                    user_id=current_user.id,
                    funnel_type=FunnelType.USER_ONBOARDING,
                    stage=FunnelStage.FIRST_SEARCH,
                    properties={
                        "query": q,
                        "results_count": len(items),
                        "search_duration": (time.time() - start_time) * 1000
                    }
                )
                
                # 追踪首次搜索转化事件
                conversion_event = ConversionEvent(
                    event_type=ConversionEventType.FIRST_SEARCH,
                    user_id=current_user.id,
                    timestamp=datetime.now(),
                    properties={
                        "query": q,
                        "results_count": len(items),
                        "search_duration": (time.time() - start_time) * 1000
                    },
                    conversion_value=0.5
                )
                await conversion_monitor.track_conversion_event(conversion_event)
            
            # 记录搜索历史
            await redis_client.set(search_history_key, "1", ex=86400 * 30)  # 30天过期
            
            # 追踪搜索到聊天漏斗的起始阶段
            await funnel_analyzer.track_funnel_event(
                user_id=current_user.id,
                funnel_type=FunnelType.SEARCH_TO_CHAT,
                stage=FunnelStage.SEARCH_INITIATED,
                properties={
                    "query": q,
                    "results_count": len(items)
                }
            )
            
        except Exception as e:
            print(f"⚠️ 搜索业务指标追踪失败: {e}")

    return AutocompleteResponse(results=items, count=len(items))
