"""
Fallback Manager - 数据源回退管理器

提供数据源优先级管理和自动fallback功能
当主数据源失败时，自动切换到备用数据源
"""
from typing import Dict, Any, List, Callable, Optional, Type
from enum import Enum
import time

from app.core.structlog_config import get_logger
from app.services.collectors.coingecko import CoinGeckoCollector
from app.services.collectors.coinmarketcap import CoinMarketCapCollector
from app.services.collectors.etherscan import EtherscanCollector
from app.services.collectors.blockchair import BlockchairCollector

logger = get_logger(__name__)


class DataSourceType(str, Enum):
    """数据源类型"""
    MARKET = "market"  # 市场数据（价格、市值）
    ONCHAIN_ETH = "onchain_eth"  # 以太坊链上数据
    ONCHAIN_BSC = "onchain_bsc"  # BSC链上数据
    SOCIAL_TWITTER = "social_twitter"  # Twitter数据
    SOCIAL_REDDIT = "social_reddit"  # Reddit数据


class FallbackManager:
    """
    Fallback管理器

    管理数据源优先级和自动切换逻辑
    """

    def __init__(self):
        """初始化Fallback Manager"""
        # 数据源优先级配置（按优先级排序）
        self.source_priorities: Dict[DataSourceType, List[Type]] = {
            DataSourceType.MARKET: [
                CoinGeckoCollector,  # 主数据源
                CoinMarketCapCollector,  # 备用数据源
            ],
            DataSourceType.ONCHAIN_ETH: [
                EtherscanCollector,  # 主数据源
                BlockchairCollector,  # 备用数据源
            ],
            # 其他数据源可以后续扩展
        }

        # 数据源健康状态追踪
        self.source_health: Dict[str, Dict[str, Any]] = {}

    async def fetch_with_fallback(
        self,
        source_type: DataSourceType,
        method_name: str,
        *args,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        使用fallback机制获取数据

        Args:
            source_type: 数据源类型
            method_name: 要调用的方法名
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            Optional[Dict]: 数据，如果所有数据源都失败则返回None

        Example:
            >>> manager = FallbackManager()
            >>> data = await manager.fetch_with_fallback(
            >>>     DataSourceType.MARKET,
            >>>     "get_coin_data",
            >>>     symbol="BTC"
            >>> )
        """
        sources = self.source_priorities.get(source_type, [])
        if not sources:
            logger.error("no_sources_configured", source_type=source_type)
            return None

        last_error = None

        for i, collector_class in enumerate(sources):
            collector_name = collector_class.__name__
            is_primary = i == 0

            try:
                # 创建collector实例
                collector = collector_class()

                # 检查方法是否存在
                if not hasattr(collector, method_name):
                    logger.warning(
                        "method_not_found",
                        collector=collector_name,
                        method=method_name
                    )
                    continue

                # 调用方法
                method = getattr(collector, method_name)
                start_time = time.time()

                logger.info(
                    "fetching_data",
                    source=collector_name,
                    method=method_name,
                    is_primary=is_primary,
                    attempt=i + 1
                )

                result = await method(*args, **kwargs)
                duration = time.time() - start_time

                # 记录成功
                self._record_success(collector_name, duration)

                logger.info(
                    "fetch_success",
                    source=collector_name,
                    method=method_name,
                    duration_ms=round(duration * 1000, 2),
                    is_fallback=not is_primary
                )

                return result

            except Exception as e:
                last_error = e
                duration = time.time() - start_time if 'start_time' in locals() else 0

                # 记录失败
                self._record_failure(collector_name, str(e))

                logger.warning(
                    "fetch_failed",
                    source=collector_name,
                    method=method_name,
                    error=str(e),
                    error_type=type(e).__name__,
                    duration_ms=round(duration * 1000, 2),
                    is_primary=is_primary,
                    attempting_fallback=i < len(sources) - 1
                )

                # 如果不是最后一个数据源，继续尝试下一个
                if i < len(sources) - 1:
                    logger.info(
                        "switching_to_fallback",
                        from_source=collector_name,
                        to_source=sources[i + 1].__name__
                    )
                    continue
                else:
                    # 所有数据源都失败了
                    logger.error(
                        "all_sources_failed",
                        source_type=source_type,
                        method=method_name,
                        last_error=str(last_error)
                    )

        # 所有数据源都失败
        return None

    def _record_success(self, source_name: str, duration: float):
        """
        记录数据源成功

        Args:
            source_name: 数据源名称
            duration: 请求耗时（秒）
        """
        if source_name not in self.source_health:
            self.source_health[source_name] = {
                "success_count": 0,
                "failure_count": 0,
                "last_success": None,
                "last_failure": None,
                "avg_duration": 0,
            }

        health = self.source_health[source_name]
        health["success_count"] += 1
        health["last_success"] = time.time()

        # 更新平均耗时（简单移动平均）
        if health["avg_duration"] == 0:
            health["avg_duration"] = duration
        else:
            health["avg_duration"] = (health["avg_duration"] + duration) / 2

    def _record_failure(self, source_name: str, error: str):
        """
        记录数据源失败

        Args:
            source_name: 数据源名称
            error: 错误信息
        """
        if source_name not in self.source_health:
            self.source_health[source_name] = {
                "success_count": 0,
                "failure_count": 0,
                "last_success": None,
                "last_failure": None,
                "avg_duration": 0,
            }

        health = self.source_health[source_name]
        health["failure_count"] += 1
        health["last_failure"] = time.time()
        health["last_error"] = error

    def get_source_health(self, source_name: Optional[str] = None) -> Dict[str, Any]:
        """
        获取数据源健康状态

        Args:
            source_name: 数据源名称，如果为None则返回所有数据源

        Returns:
            Dict: 健康状态信息
        """
        if source_name:
            return self.source_health.get(source_name, {})
        return self.source_health

    def get_success_rate(self, source_name: str) -> float:
        """
        获取数据源成功率

        Args:
            source_name: 数据源名称

        Returns:
            float: 成功率（0-1）
        """
        health = self.source_health.get(source_name)
        if not health:
            return 0.0

        total = health["success_count"] + health["failure_count"]
        if total == 0:
            return 0.0

        return health["success_count"] / total


# 全局实例
fallback_manager = FallbackManager()
