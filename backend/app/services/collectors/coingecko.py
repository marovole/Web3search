"""
CoinGecko数据采集器
采集加密货币市场数据、价格、市值等信息
"""
import asyncio
from typing import Dict, Any, Optional, List
import httpx
from datetime import datetime
import time

from app.core.config import settings
from app.core.redis_client import cache_get_json, cache_set
from app.core.structlog_config import get_logger

logger = get_logger(__name__)


class CoinGeckoCollector:
    """
    CoinGecko API客户端
    提供加密货币市场数据采集功能
    """

    def __init__(self):
        """初始化CoinGecko客户端"""
        self.base_url = settings.COINGECKO_BASE_URL
        self.api_key = settings.COINGECKO_API_KEY
        self.timeout = 30.0

        # 请求头
        self.headers = {}
        if self.api_key:
            self.headers["x-cg-pro-api-key"] = self.api_key

    async def _request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
        cache_ttl: int = 300,
    ) -> Dict[str, Any]:
        """
        发送HTTP请求到CoinGecko API

        Args:
            endpoint: API端点
            params: 查询参数
            use_cache: 是否使用缓存
            cache_ttl: 缓存时间（秒）

        Returns:
            Dict: API响应数据

        Raises:
            Exception: API请求失败
        """
        url = f"{self.base_url}{endpoint}"

        # 检查缓存
        cache_key = f"coingecko:{endpoint}:{str(params)}"
        if use_cache:
            cached = await cache_get_json(cache_key)
            if cached:
                return cached

        # 发送请求（带重试）
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(url, params=params, headers=self.headers)
                    response.raise_for_status()
                    data = response.json()

                    # 缓存结果
                    if use_cache:
                        await cache_set(cache_key, data, cache_ttl)

                    return data

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:  # Rate limit
                    wait_time = 2 ** attempt
                    print(f"⚠️ CoinGecko限流，等待{wait_time}秒...")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise Exception(f"CoinGecko API错误: {e.response.status_code}")

            except Exception as e:
                if attempt < 2:
                    await asyncio.sleep(1)
                    continue
                else:
                    raise Exception(f"CoinGecko请求失败: {str(e)}")

        # 返回友好的错误信息，而不是抛出异常
        logger.error(f"CoinGecko API请求达到最大重试次数: {endpoint}")
        return {
            "error": True,
            "message": "CoinGecko API暂时不可用，请稍后再试",
            "endpoint": endpoint,
            "attempts": 3
        }

    # ================================
    # 核心数据采集方法
    # ================================

    async def get_coin_data(
        self,
        coin_id: str,
        include_market_data: bool = True,
        include_community_data: bool = True,
        include_developer_data: bool = False,
    ) -> Dict[str, Any]:
        """
        获取币种详细信息

        Args:
            coin_id: CoinGecko币种ID（如"bitcoin"）
            include_market_data: 包含市场数据
            include_community_data: 包含社区数据
            include_developer_data: 包含开发者数据

        Returns:
            Dict: 币种详细数据
        """
        params = {
            "localization": "false",
            "tickers": "false",
            "market_data": str(include_market_data).lower(),
            "community_data": str(include_community_data).lower(),
            "developer_data": str(include_developer_data).lower(),
        }

        return await self._request(
            f"/coins/{coin_id}",
            params=params,
            use_cache=True,
            cache_ttl=settings.CACHE_TTL_PRICE,  # 60秒缓存
        )

    async def get_coin_market_data(self, coin_id: str) -> Dict[str, Any]:
        """
        获取币种市场数据（价格、市值、交易量等）

        Args:
            coin_id: CoinGecko币种ID

        Returns:
            Dict: 市场数据
        """
        data = await self.get_coin_data(
            coin_id,
            include_market_data=True,
            include_community_data=False,
        )

        if not data or "market_data" not in data:
            return {}

        market_data = data["market_data"]

        return {
            "symbol": data.get("symbol", "").upper(),
            "name": data.get("name"),
            "price_usd": market_data.get("current_price", {}).get("usd"),
            "price_btc": market_data.get("current_price", {}).get("btc"),
            "market_cap": market_data.get("market_cap", {}).get("usd"),
            "market_cap_rank": market_data.get("market_cap_rank"),
            "total_volume_24h": market_data.get("total_volume", {}).get("usd"),
            "price_change_24h": market_data.get("price_change_percentage_24h"),
            "price_change_7d": market_data.get("price_change_percentage_7d"),
            "price_change_30d": market_data.get("price_change_percentage_30d"),
            "circulating_supply": market_data.get("circulating_supply"),
            "total_supply": market_data.get("total_supply"),
            "max_supply": market_data.get("max_supply"),
            "ath": market_data.get("ath", {}).get("usd"),
            "ath_date": market_data.get("ath_date", {}).get("usd"),
            "atl": market_data.get("atl", {}).get("usd"),
            "atl_date": market_data.get("atl_date", {}).get("usd"),
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def get_coin_info(self, coin_id: str) -> Dict[str, Any]:
        """
        获取币种基本信息（名称、描述、链接等）

        Args:
            coin_id: CoinGecko币种ID

        Returns:
            Dict: 基本信息
        """
        data = await self.get_coin_data(
            coin_id,
            include_market_data=False,
            include_community_data=True,
        )

        if not data:
            return {}

        # 提取合约地址
        contract_addresses = {}
        platforms = data.get("platforms", {})
        for platform, address in platforms.items():
            if address:
                contract_addresses[platform] = address

        # 提取社交链接
        links = data.get("links", {})

        return {
            "coingecko_id": data.get("id"),
            "symbol": data.get("symbol", "").upper(),
            "name": data.get("name"),
            "description": data.get("description", {}).get("en", ""),
            "website": links.get("homepage", [None])[0],
            "whitepaper": links.get("whitepaper"),
            "blockchain": data.get("asset_platform_id"),
            "contract_addresses": contract_addresses,
            "categories": data.get("categories", []),
            "twitter_handle": links.get("twitter_screen_name"),
            "telegram_url": links.get("telegram_channel_identifier"),
            "reddit_url": links.get("subreddit_url"),
        }

    async def get_trending_coins(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取热门/趋势币种

        Args:
            limit: 返回数量

        Returns:
            List[Dict]: 趋势币种列表
        """
        data = await self._request(
            "/search/trending",
            use_cache=True,
            cache_ttl=300,  # 5分钟缓存
        )

        trending = []
        for item in data.get("coins", [])[:limit]:
            coin = item.get("item", {})
            trending.append({
                "coingecko_id": coin.get("id"),
                "symbol": coin.get("symbol"),
                "name": coin.get("name"),
                "market_cap_rank": coin.get("market_cap_rank"),
                "thumb": coin.get("thumb"),
                "score": coin.get("score", 0),
            })

        return trending

    async def search_coins(self, query: str) -> List[Dict[str, Any]]:
        """
        搜索币种

        Args:
            query: 搜索关键词（币种名称或符号）

        Returns:
            List[Dict]: 搜索结果列表
        """
        data = await self._request(
            "/search",
            params={"query": query},
            use_cache=True,
            cache_ttl=3600,  # 1小时缓存
        )

        results = []
        for coin in data.get("coins", [])[:10]:
            results.append({
                "coingecko_id": coin.get("id"),
                "symbol": coin.get("symbol"),
                "name": coin.get("name"),
                "market_cap_rank": coin.get("market_cap_rank"),
                "thumb": coin.get("thumb"),
            })

        return results

    async def get_market_chart(
        self,
        coin_id: str,
        days: int = 7,
        interval: str = "daily",
    ) -> Dict[str, Any]:
        """
        获取历史市场数据图表

        Args:
            coin_id: CoinGecko币种ID
            days: 天数（1, 7, 14, 30, 90, 180, 365, max）
            interval: 间隔（daily, hourly）

        Returns:
            Dict: 历史数据
        """
        params = {
            "vs_currency": "usd",
            "days": days,
            "interval": interval,
        }

        data = await self._request(
            f"/coins/{coin_id}/market_chart",
            params=params,
            use_cache=True,
            cache_ttl=3600,  # 1小时缓存
        )

        return {
            "prices": data.get("prices", []),
            "market_caps": data.get("market_caps", []),
            "total_volumes": data.get("total_volumes", []),
        }

    async def get_global_market_data(self) -> Dict[str, Any]:
        """
        获取全局市场数据（总市值、BTC占比等）

        Returns:
            Dict: 全局市场数据
        """
        data = await self._request(
            "/global",
            use_cache=True,
            cache_ttl=300,  # 5分钟缓存
        )

        global_data = data.get("data", {})

        return {
            "total_market_cap_usd": global_data.get("total_market_cap", {}).get("usd"),
            "total_volume_24h_usd": global_data.get("total_volume", {}).get("usd"),
            "bitcoin_dominance": global_data.get("market_cap_percentage", {}).get("btc"),
            "ethereum_dominance": global_data.get("market_cap_percentage", {}).get("eth"),
            "active_cryptocurrencies": global_data.get("active_cryptocurrencies"),
            "markets": global_data.get("markets"),
            "timestamp": datetime.utcnow().isoformat(),
        }


# ================================
# 全局实例
# ================================

coingecko_collector = CoinGeckoCollector()
