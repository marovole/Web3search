"""
Etherscan/BSCScan数据采集器
采集链上数据：交易数、持有者、活跃地址等
"""
import asyncio
from typing import Dict, Any, Optional, List
import httpx
from datetime import datetime

from app.core.config import settings
from app.core.redis_client import cache_get_json, cache_set


class BlockchainExplorerCollector:
    """
    区块链浏览器API客户端（Etherscan/BSCScan）
    提供链上数据采集功能
    """

    def __init__(self, chain: str = "ethereum"):
        """
        初始化区块链浏览器客户端

        Args:
            chain: 链类型（"ethereum" 或 "bsc"）
        """
        self.chain = chain

        if chain == "ethereum":
            self.base_url = settings.ETHERSCAN_BASE_URL
            self.api_key = settings.ETHERSCAN_API_KEY
        elif chain == "bsc":
            self.base_url = settings.BSCSCAN_BASE_URL
            self.api_key = settings.BSCSCAN_API_KEY
        else:
            raise ValueError(f"不支持的链类型: {chain}")

        self.timeout = 30.0

    async def _request(
        self,
        module: str,
        action: str,
        params: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
        cache_ttl: int = 600,
    ) -> Dict[str, Any]:
        """
        发送HTTP请求到区块链浏览器API

        Args:
            module: API模块
            action: API动作
            params: 额外参数
            use_cache: 是否使用缓存
            cache_ttl: 缓存时间（秒）

        Returns:
            Dict: API响应数据

        Raises:
            Exception: API请求失败
        """
        # 构建查询参数
        query_params = {
            "module": module,
            "action": action,
            "apikey": self.api_key,
        }
        if params:
            query_params.update(params)

        # 检查缓存
        cache_key = f"{self.chain}:{module}:{action}:{str(params)}"
        if use_cache:
            cached = await cache_get_json(cache_key)
            if cached:
                return cached

        # 发送请求（带重试）
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(self.base_url, params=query_params)
                    response.raise_for_status()
                    data = response.json()

                    # 检查API响应状态
                    if data.get("status") == "1" and data.get("message") == "OK":
                        result = data.get("result")

                        # 缓存结果
                        if use_cache:
                            await cache_set(cache_key, result, cache_ttl)

                        return result
                    elif data.get("status") == "0":
                        # API返回错误
                        error_msg = data.get("result") or data.get("message")
                        if "rate limit" in str(error_msg).lower():
                            wait_time = 2 ** attempt
                            print(f"⚠️ {self.chain}限流，等待{wait_time}秒...")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            raise Exception(f"{self.chain} API错误: {error_msg}")
                    else:
                        raise Exception(f"{self.chain} 未知响应格式")

            except httpx.HTTPStatusError as e:
                if attempt < 2:
                    await asyncio.sleep(1)
                    continue
                else:
                    raise Exception(f"{self.chain} HTTP错误: {e.response.status_code}")

            except Exception as e:
                if attempt < 2:
                    await asyncio.sleep(1)
                    continue
                else:
                    raise Exception(f"{self.chain}请求失败: {str(e)}")

        raise Exception(f"{self.chain} API请求达到最大重试次数")

    # ================================
    # ERC20代币数据采集
    # ================================

    async def get_token_total_supply(self, contract_address: str) -> Optional[float]:
        """
        获取代币总供应量

        Args:
            contract_address: 合约地址

        Returns:
            float: 总供应量
        """
        try:
            result = await self._request(
                module="stats",
                action="tokensupply",
                params={"contractaddress": contract_address},
                cache_ttl=3600,  # 1小时缓存
            )
            return float(result) if result else None
        except Exception as e:
            print(f"⚠️ 获取代币总供应量失败: {e}")
            return None

    async def get_token_holder_count(self, contract_address: str) -> Optional[int]:
        """
        获取代币持有者数量（注意：需要Pro API）

        Args:
            contract_address: 合约地址

        Returns:
            int: 持有者数量
        """
        # 注意：免费API不支持此功能
        # 这里返回None，实际项目中需要Pro API或使用第三方服务
        print(f"⚠️ 代币持有者数量需要Pro API")
        return None

    async def get_token_transfers(
        self,
        contract_address: str,
        address: Optional[str] = None,
        start_block: int = 0,
        end_block: int = 99999999,
        page: int = 1,
        offset: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        获取代币转账记录

        Args:
            contract_address: 合约地址
            address: 特定地址（可选）
            start_block: 起始区块
            end_block: 结束区块
            page: 页码
            offset: 每页数量

        Returns:
            List[Dict]: 转账记录列表
        """
        params = {
            "contractaddress": contract_address,
            "startblock": start_block,
            "endblock": end_block,
            "page": page,
            "offset": offset,
            "sort": "desc",
        }

        if address:
            params["address"] = address

        try:
            result = await self._request(
                module="account",
                action="tokentx",
                params=params,
                cache_ttl=300,  # 5分钟缓存
            )

            if isinstance(result, list):
                return result
            return []

        except Exception as e:
            print(f"⚠️ 获取代币转账记录失败: {e}")
            return []

    async def get_token_stats_24h(self, contract_address: str) -> Dict[str, Any]:
        """
        获取代币24小时统计数据

        Args:
            contract_address: 合约地址

        Returns:
            Dict: 24小时统计数据
        """
        # 获取最近100笔转账
        transfers = await self.get_token_transfers(
            contract_address=contract_address,
            offset=100,
        )

        if not transfers:
            return {
                "transaction_count_24h": 0,
                "unique_addresses_24h": 0,
                "total_value_transferred": 0,
            }

        # 计算24小时内的交易
        now = datetime.utcnow()
        cutoff_timestamp = int((now.timestamp() - 86400))  # 24小时前

        recent_transfers = []
        unique_addresses = set()

        for tx in transfers:
            timestamp = int(tx.get("timeStamp", 0))
            if timestamp >= cutoff_timestamp:
                recent_transfers.append(tx)
                unique_addresses.add(tx.get("from", ""))
                unique_addresses.add(tx.get("to", ""))

        return {
            "transaction_count_24h": len(recent_transfers),
            "unique_addresses_24h": len(unique_addresses),
            "timestamp": datetime.utcnow().isoformat(),
        }

    # ================================
    # 账户数据采集
    # ================================

    async def get_address_balance(self, address: str) -> Optional[float]:
        """
        获取地址余额（ETH/BNB）

        Args:
            address: 钱包地址

        Returns:
            float: 余额（单位：ETH/BNB）
        """
        try:
            result = await self._request(
                module="account",
                action="balance",
                params={"address": address, "tag": "latest"},
                cache_ttl=60,  # 1分钟缓存
            )

            # 转换为ETH/BNB（Wei -> Ether）
            balance_wei = int(result)
            balance_ether = balance_wei / (10 ** 18)
            return balance_ether

        except Exception as e:
            print(f"⚠️ 获取地址余额失败: {e}")
            return None

    async def get_address_transactions(
        self,
        address: str,
        start_block: int = 0,
        end_block: int = 99999999,
        page: int = 1,
        offset: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        获取地址交易记录

        Args:
            address: 钱包地址
            start_block: 起始区块
            end_block: 结束区块
            page: 页码
            offset: 每页数量

        Returns:
            List[Dict]: 交易记录列表
        """
        params = {
            "address": address,
            "startblock": start_block,
            "endblock": end_block,
            "page": page,
            "offset": offset,
            "sort": "desc",
        }

        try:
            result = await self._request(
                module="account",
                action="txlist",
                params=params,
                cache_ttl=300,  # 5分钟缓存
            )

            if isinstance(result, list):
                return result
            return []

        except Exception as e:
            print(f"⚠️ 获取地址交易记录失败: {e}")
            return []

    # ================================
    # 合约数据采集
    # ================================

    async def get_contract_source_code(self, contract_address: str) -> Dict[str, Any]:
        """
        获取合约源代码

        Args:
            contract_address: 合约地址

        Returns:
            Dict: 合约信息
        """
        try:
            result = await self._request(
                module="contract",
                action="getsourcecode",
                params={"address": contract_address},
                cache_ttl=86400,  # 24小时缓存
            )

            if isinstance(result, list) and len(result) > 0:
                return result[0]
            return {}

        except Exception as e:
            print(f"⚠️ 获取合约源代码失败: {e}")
            return {}

    async def is_contract_verified(self, contract_address: str) -> bool:
        """
        检查合约是否已验证

        Args:
            contract_address: 合约地址

        Returns:
            bool: 是否已验证
        """
        source_code = await self.get_contract_source_code(contract_address)
        return bool(source_code.get("SourceCode"))

    # ================================
    # 综合数据采集
    # ================================

    async def get_token_onchain_data(self, contract_address: str) -> Dict[str, Any]:
        """
        获取代币的综合链上数据

        Args:
            contract_address: 合约地址

        Returns:
            Dict: 链上数据汇总
        """
        # 并行获取多个数据
        total_supply, stats_24h, is_verified = await asyncio.gather(
            self.get_token_total_supply(contract_address),
            self.get_token_stats_24h(contract_address),
            self.is_contract_verified(contract_address),
            return_exceptions=True,
        )

        # 处理异常结果
        if isinstance(total_supply, Exception):
            total_supply = None
        if isinstance(stats_24h, Exception):
            stats_24h = {}
        if isinstance(is_verified, Exception):
            is_verified = False

        return {
            "chain": self.chain,
            "contract_address": contract_address,
            "total_supply": total_supply,
            "transaction_count_24h": stats_24h.get("transaction_count_24h", 0),
            "active_addresses_24h": stats_24h.get("unique_addresses_24h", 0),
            "is_verified": is_verified,
            "timestamp": datetime.utcnow().isoformat(),
        }


# ================================
# 全局实例
# ================================

etherscan_collector = BlockchainExplorerCollector(chain="ethereum")
bscscan_collector = BlockchainExplorerCollector(chain="bsc")
