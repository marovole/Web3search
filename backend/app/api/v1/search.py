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
async def autocomplete_search(
    q: str = Query(..., min_length=1, max_length=100, description="搜索关键词"),
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
    # 调用CoinGecko搜索
    results = await coingecko_collector.search_coins(q)

    # 转换为响应格式
    items = [AutocompleteItem(**item) for item in results]

    return AutocompleteResponse(results=items, count=len(items))
