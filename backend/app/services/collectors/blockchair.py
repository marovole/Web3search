"""
Blockchair数据采集器
作为Etherscan/BSCScan的备用数据源，采集链上数据
"""
import asyncio
from typing import Dict, Any, Optional
import httpx
from datetime import datetime

from app.core.config import settings
from app.core.redis_client import cache_get_json, cache_set
from app.core.structlog_config import get_logger

logger = get_logger(__name__)


class BlockchairCollector:
    """
    Blockchair API客户端
    提供多链链上数据采集功能（Etherscan的fallback）
    支持：Bitcoin, Ethereum, BSC等
    """

    def __init__(self):
        """初始化Blockchair客户端"""
        self.base_url = settings.BLOCKCHAIR_BASE_URL
        self.api_key = settings.BLOCKCHAIR_API_KEY
        self.timeout = 30.0

    async def _request(
        self,
        blockchain: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
        cache_ttl: int = 300,
    ) -> Dict[str, Any]:
        """
        发送HTTP请求到Blockchair API

        Args:
            blockchain: 区块链名称（bitcoin, ethereum, bsc等）
            endpoint: API端点
            params: 查询参数
            use_cache: 是否使用缓存
            cache_ttl: 缓存时间（秒）

        Returns:
            Dict: API响应数据
        """
        url = f"{self.base_url}/{blockchain}/{endpoint}"

        # 添加API key到参数
        if params is None:
            params = {}
        if self.api_key:
            params["key"] = self.api_key

        # 检查缓存
        cache_key = f"blockchair:{blockchain}:{endpoint}:{str(params)}"
        if use_cache:
            cached = await cache_get_json(cache_key)
            if cached:
                logger.debug("cache_hit", source="blockchair", blockchain=blockchain, endpoint=endpoint)
                return cached

        # 发送请求
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    data = response.json()

                    # 检查Blockchair响应格式
                    if "data" not in data:
                        raise Exception(f"Invalid Blockchair response: {data}")

                    # 缓存结果
                    if use_cache:
                        await cache_set(cache_key, data, cache_ttl)

                    logger.info(
                        "api_success",
                        source="blockchair",
                        blockchain=blockchain,
                        endpoint=endpoint,
                        attempt=attempt + 1
                    )
                    return data

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    wait_time = 2 ** attempt
                    logger.warning("rate_limit", source="blockchair", wait_time=wait_time)
                    await asyncio.sleep(wait_time)
                    continue
                elif e.response.status_code in [401, 403]:
                    logger.error("auth_error", source="blockchair", status_code=e.response.status_code)
                    raise Exception(f"Blockchair authentication error: {e.response.status_code}")
                else:
                    logger.error("http_error", source="blockchair", status_code=e.response.status_code)
                    if attempt < 2:
                        await asyncio.sleep(1)
                        continue
                    raise Exception(f"Blockchair API error: {e.response.status_code}")

            except Exception as e:
                logger.error("request_error", source="blockchair", error=str(e), attempt=attempt + 1)
                if attempt < 2:
                    await asyncio.sleep(1)
                    continue
                else:
                    raise Exception(f"Blockchair request failed: {str(e)}")

        raise Exception("Blockchair API reached max retries")

    # ================================
    # Ethereum数据采集
    # ================================

    async def get_eth_address_info(
        self,
        address: str,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        获取以太坊地址信息

        Args:
            address: 以太坊地址
            use_cache: 是否使用缓存

        Returns:
            Dict: 地址信息
        """
        try:
            response = await self._request(
                "ethereum",
                f"dashboards/address/{address}",
                use_cache=use_cache,
                cache_ttl=60,
            )

            data = response.get("data", {}).get(address, {})
            address_data = data.get("address", {})

            return {
                "address": address,
                "balance": float(address_data.get("balance", 0)) / 10**18,  # Wei to ETH
                "balance_usd": address_data.get("balance_usd"),
                "received": float(address_data.get("received", 0)) / 10**18,
                "spent": float(address_data.get("spent", 0)) / 10**18,
                "transaction_count": address_data.get("transaction_count", 0),
                "first_seen": address_data.get("first_seen_receiving"),
                "last_seen": address_data.get("last_seen_spending"),
            }

        except Exception as e:
            logger.error("get_eth_address_info_failed", address=address, error=str(e))
            raise

    async def get_eth_token_info(
        self,
        token_address: str,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        获取ERC-20代币信息

        Args:
            token_address: 代币合约地址
            use_cache: 是否使用缓存

        Returns:
            Dict: 代币信息
        """
        try:
            response = await self._request(
                "ethereum",
                f"erc-20/{token_address}/stats",
                use_cache=use_cache,
                cache_ttl=300,
            )

            data = response.get("data", {})

            return {
                "address": token_address,
                "name": data.get("name"),
                "symbol": data.get("symbol"),
                "decimals": data.get("decimals"),
                "total_supply": data.get("total_supply"),
                "holders_count": data.get("holders_count"),
                "transfers_count": data.get("transfers_count"),
                "price_usd": data.get("price_usd"),
                "market_cap_usd": data.get("market_cap_usd"),
            }

        except Exception as e:
            logger.error("get_eth_token_info_failed", token_address=token_address, error=str(e))
            raise

    # ================================
    # BSC数据采集
    # ================================

    async def get_bsc_address_info(
        self,
        address: str,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        获取BSC地址信息

        Args:
            address: BSC地址
            use_cache: 是否使用缓存

        Returns:
            Dict: 地址信息
        """
        try:
            response = await self._request(
                "bsc",  # BSC在Blockchair的链名称
                f"dashboards/address/{address}",
                use_cache=use_cache,
                cache_ttl=60,
            )

            data = response.get("data", {}).get(address, {})
            address_data = data.get("address", {})

            return {
                "address": address,
                "balance": float(address_data.get("balance", 0)) / 10**18,  # Wei to BNB
                "balance_usd": address_data.get("balance_usd"),
                "transaction_count": address_data.get("transaction_count", 0),
                "first_seen": address_data.get("first_seen_receiving"),
                "last_seen": address_data.get("last_seen_spending"),
            }

        except Exception as e:
            logger.error("get_bsc_address_info_failed", address=address, error=str(e))
            raise

    # ================================
    # Bitcoin数据采集
    # ================================

    async def get_btc_address_info(
        self,
        address: str,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        获取比特币地址信息

        Args:
            address: 比特币地址
            use_cache: 是否使用缓存

        Returns:
            Dict: 地址信息
        """
        try:
            response = await self._request(
                "bitcoin",
                f"dashboards/address/{address}",
                use_cache=use_cache,
                cache_ttl=60,
            )

            data = response.get("data", {}).get(address, {})
            address_data = data.get("address", {})

            return {
                "address": address,
                "balance": float(address_data.get("balance", 0)) / 10**8,  # Satoshi to BTC
                "received": float(address_data.get("received", 0)) / 10**8,
                "spent": float(address_data.get("spent", 0)) / 10**8,
                "transaction_count": address_data.get("transaction_count", 0),
                "first_seen": address_data.get("first_seen_receiving"),
                "last_seen": address_data.get("last_seen_spending"),
            }

        except Exception as e:
            logger.error("get_btc_address_info_failed", address=address, error=str(e))
            raise


# 全局实例
blockchair_collector = BlockchairCollector()
