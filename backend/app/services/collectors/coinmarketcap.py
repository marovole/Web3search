"""
CoinMarketCap数据采集器
作为CoinGecko的备用数据源，采集加密货币市场数据
"""
import asyncio
from typing import Dict, Any, Optional, List
import httpx
from datetime import datetime

from app.core.config import settings
from app.core.redis_client import cache_get_json, cache_set
from app.core.structlog_config import get_logger

logger = get_logger(__name__)


class CoinMarketCapCollector:
    """
    CoinMarketCap API客户端
    提供加密货币市场数据采集功能（CoinGecko的fallback）
    """

    def __init__(self):
        """初始化CoinMarketCap客户端"""
        self.base_url = settings.COINMARKETCAP_BASE_URL
        self.api_key = settings.COINMARKETCAP_API_KEY
        self.timeout = 30.0

        # 请求头
        self.headers = {
            "X-CMC_PRO_API_KEY": self.api_key,
            "Accept": "application/json",
        }

    async def _request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
        cache_ttl: int = 300,
    ) -> Dict[str, Any]:
        """
        发送HTTP请求到CoinMarketCap API

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
        cache_key = f"coinmarketcap:{endpoint}:{str(params)}"
        if use_cache:
            cached = await cache_get_json(cache_key)
            if cached:
                logger.debug("cache_hit", source="coinmarketcap", endpoint=endpoint)
                return cached

        # 发送请求（带简单重试）
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(url, params=params, headers=self.headers)
                    response.raise_for_status()
                    data = response.json()

                    # CoinMarketCap返回格式：{"data": {...}, "status": {...}}
                    if "data" not in data:
                        raise Exception(f"Invalid CoinMarketCap response: {data}")

                    # 缓存结果
                    if use_cache:
                        await cache_set(cache_key, data, cache_ttl)

                    logger.info(
                        "api_success",
                        source="coinmarketcap",
                        endpoint=endpoint,
                        attempt=attempt + 1
                    )
                    return data

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:  # Rate limit
                    wait_time = 2 ** attempt
                    logger.warning(
                        "rate_limit",
                        source="coinmarketcap",
                        wait_time=wait_time,
                        attempt=attempt + 1
                    )
                    await asyncio.sleep(wait_time)
                    continue
                elif e.response.status_code in [401, 403]:  # 永久错误
                    logger.error(
                        "auth_error",
                        source="coinmarketcap",
                        status_code=e.response.status_code
                    )
                    raise Exception(f"CoinMarketCap API authentication error: {e.response.status_code}")
                else:
                    logger.error(
                        "http_error",
                        source="coinmarketcap",
                        status_code=e.response.status_code,
                        attempt=attempt + 1
                    )
                    if attempt < 2:
                        await asyncio.sleep(1)
                        continue
                    raise Exception(f"CoinMarketCap API error: {e.response.status_code}")

            except Exception as e:
                logger.error(
                    "request_error",
                    source="coinmarketcap",
                    error=str(e),
                    attempt=attempt + 1
                )
                if attempt < 2:
                    await asyncio.sleep(1)
                    continue
                else:
                    raise Exception(f"CoinMarketCap request failed: {str(e)}")

        raise Exception("CoinMarketCap API reached max retries")

    # ================================
    # 核心数据采集方法
    # ================================

    async def get_coin_data(
        self,
        symbol: str,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        获取币种基础信息

        Args:
            symbol: 币种符号（如"BTC"）
            use_cache: 是否使用缓存

        Returns:
            Dict: 币种信息
        """
        try:
            # CoinMarketCap使用symbol查询
            response = await self._request(
                "/v2/cryptocurrency/info",
                params={"symbol": symbol.upper()},
                use_cache=use_cache,
                cache_ttl=3600,  # 基础信息缓存1小时
            )

            data = response.get("data", {}).get(symbol.upper())
            if not data or len(data) == 0:
                raise Exception(f"Coin {symbol} not found on CoinMarketCap")

            # 如果有多个结果，取第一个
            if isinstance(data, list):
                data = data[0]

            return {
                "id": data.get("id"),
                "name": data.get("name"),
                "symbol": data.get("symbol"),
                "slug": data.get("slug"),
                "description": data.get("description"),
                "website": data.get("urls", {}).get("website", [None])[0],
                "twitter": data.get("urls", {}).get("twitter", [None])[0],
                "reddit": data.get("urls", {}).get("reddit", [None])[0],
                "github": data.get("urls", {}).get("source_code", [None])[0],
                "logo": data.get("logo"),
                "tags": data.get("tags", []),
                "platform": data.get("platform"),
                "contract_address": data.get("platform", {}).get("token_address") if data.get("platform") else None,
            }

        except Exception as e:
            logger.error("get_coin_data_failed", symbol=symbol, error=str(e))
            raise

    async def get_market_data(
        self,
        symbol: str,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        获取市场数据（价格、市值、交易量等）

        Args:
            symbol: 币种符号
            use_cache: 是否使用缓存

        Returns:
            Dict: 市场数据
        """
        try:
            response = await self._request(
                "/v2/cryptocurrency/quotes/latest",
                params={"symbol": symbol.upper(), "convert": "USD"},
                use_cache=use_cache,
                cache_ttl=60,  # 价格数据缓存1分钟
            )

            data = response.get("data", {}).get(symbol.upper())
            if not data or len(data) == 0:
                raise Exception(f"Market data for {symbol} not found")

            # 如果有多个结果，取第一个
            if isinstance(data, list):
                data = data[0]

            quote = data.get("quote", {}).get("USD", {})

            return {
                "price": quote.get("price"),
                "market_cap": quote.get("market_cap"),
                "volume_24h": quote.get("volume_24h"),
                "volume_change_24h": quote.get("volume_change_24h"),
                "percent_change_1h": quote.get("percent_change_1h"),
                "percent_change_24h": quote.get("percent_change_24h"),
                "percent_change_7d": quote.get("percent_change_7d"),
                "percent_change_30d": quote.get("percent_change_30d"),
                "market_cap_dominance": quote.get("market_cap_dominance"),
                "circulating_supply": data.get("circulating_supply"),
                "total_supply": data.get("total_supply"),
                "max_supply": data.get("max_supply"),
                "cmc_rank": data.get("cmc_rank"),
                "last_updated": quote.get("last_updated"),
            }

        except Exception as e:
            logger.error("get_market_data_failed", symbol=symbol, error=str(e))
            raise

    async def search_coins(
        self,
        query: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        搜索币种

        Args:
            query: 搜索关键词
            limit: 返回结果数量

        Returns:
            List: 搜索结果列表
        """
        try:
            # CoinMarketCap的搜索功能需要使用map端点
            response = await self._request(
                "/v1/cryptocurrency/map",
                params={"symbol": query.upper(), "limit": limit},
                use_cache=True,
                cache_ttl=3600,
            )

            data = response.get("data", [])

            return [
                {
                    "id": coin.get("id"),
                    "name": coin.get("name"),
                    "symbol": coin.get("symbol"),
                    "slug": coin.get("slug"),
                    "rank": coin.get("rank"),
                    "is_active": coin.get("is_active", 1) == 1,
                }
                for coin in data
            ]

        except Exception as e:
            logger.error("search_coins_failed", query=query, error=str(e))
            return []


# 全局实例
coinmarketcap_collector = CoinMarketCapCollector()
