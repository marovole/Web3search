"""
搜索API端点
提供加密货币搜索和自动补全功能
"""
from fastapi import APIRouter, Query
from typing import List
from pydantic import BaseModel

from app.services.collectors.coingecko import coingecko_collector

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


@router.get("/search/autocomplete", response_model=AutocompleteResponse)
async def autocomplete_search(
    q: str = Query(..., min_length=1, max_length=100, description="搜索关键词"),
) -> AutocompleteResponse:
    """
    搜索自动补全API

    根据用户输入的关键词，返回匹配的加密货币列表

    Args:
        q: 搜索关键词（币种名称或符号）

    Returns:
        AutocompleteResponse: 搜索结果列表

    Example:
        GET /api/v1/search/autocomplete?q=btc

        Response:
        {
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
    """
    # 调用CoinGecko搜索
    results = await coingecko_collector.search_coins(q)

    # 转换为响应格式
    items = [AutocompleteItem(**item) for item in results]

    return AutocompleteResponse(results=items, count=len(items))
