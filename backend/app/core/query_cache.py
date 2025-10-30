"""
查询缓存服务（任务 9.1-9.2, 9.7）

提供智能查询缓存功能：
1. 查询标准化和哈希
2. 基于数据类型的 TTL 策略
3. 缓存统计和监控
4. 性能指标追踪集成（任务 9.7）
"""
import hashlib
import json
import logging
from typing import Any, Optional, Dict
from enum import Enum
from datetime import datetime

from app.core.redis_client import (
    cache_get,
    cache_set,
    cache_get_json,
    cache_exists,
    cache_delete,
    cache_increment,
)
from app.core.metrics import metrics_collector

logger = logging.getLogger(__name__)


# ================================
# 数据类型和TTL配置（任务 9.2）
# ================================


class DataType(str, Enum):
    """数据类型枚举"""
    PRICE = "price"                    # 价格数据
    MARKET_DATA = "market_data"        # 市场数据（交易量、市值等）
    SOCIAL_DATA = "social_data"        # 社交数据
    ONCHAIN_DATA = "onchain_data"      # 链上数据
    NEWS = "news"                      # 新闻数据
    ANALYSIS = "analysis"              # AI 分析结果
    SEARCH_RESULT = "search_result"    # 搜索结果
    QUICK_CHAT = "quick_chat"          # Quick Chat响应
    DEEP_RESEARCH = "deep_research"    # Deep Research报告
    OTHER = "other"                    # 其他数据


# TTL 配置（秒）
TTL_CONFIG: Dict[DataType, int] = {
    DataType.PRICE: 5 * 60,           # 价格数据: 5 分钟
    DataType.MARKET_DATA: 5 * 60,     # 市场数据: 5 分钟
    DataType.SOCIAL_DATA: 10 * 60,    # 社交数据: 10 分钟
    DataType.ONCHAIN_DATA: 10 * 60,   # 链上数据: 10 分钟
    DataType.NEWS: 15 * 60,           # 新闻数据: 15 分钟
    DataType.ANALYSIS: 10 * 60,       # AI 分析: 10 分钟
    DataType.SEARCH_RESULT: 10 * 60,  # 搜索结果: 10 分钟
    DataType.QUICK_CHAT: 5 * 60,      # Quick Chat: 5 分钟
    DataType.DEEP_RESEARCH: 60 * 60,  # Deep Research: 60 分钟
    DataType.OTHER: 10 * 60,          # 其他: 10 分钟（默认）
}


# ================================
# 查询标准化和哈希（任务 9.1）
# ================================


def normalize_query(query: str) -> str:
    """
    标准化查询字符串

    处理：
    - 去除首尾空格
    - 转换为小写
    - 去除多余空格（连续空格转为单个）
    - 去除标点符号变体

    Args:
        query: 原始查询字符串

    Returns:
        str: 标准化后的查询

    Examples:
        >>> normalize_query("  BTC Price  ")
        "btc price"
        >>> normalize_query("What's   the  price?")
        "what's the price"
    """
    # 去除首尾空格并转小写
    normalized = query.strip().lower()

    # 去除多余空格
    normalized = " ".join(normalized.split())

    return normalized


def generate_query_hash(
    query: str,
    symbol: Optional[str] = None,
    data_type: Optional[DataType] = None,
    additional_params: Optional[Dict[str, Any]] = None
) -> str:
    """
    生成查询哈希（用作缓存键）

    Args:
        query: 查询字符串
        symbol: 代币符号（可选）
        data_type: 数据类型（可选）
        additional_params: 额外参数（可选）

    Returns:
        str: 查询哈希（MD5）

    Examples:
        >>> generate_query_hash("BTC price", symbol="BTC")
        'query:3d2e8f9a1b4c5d6e7f8a9b0c1d2e3f4'
    """
    # 标准化查询
    normalized_query = normalize_query(query)

    # 构建哈希输入
    hash_input_parts = [normalized_query]

    if symbol:
        hash_input_parts.append(symbol.upper())

    if data_type:
        hash_input_parts.append(data_type.value)

    if additional_params:
        # 将参数转为排序后的JSON字符串（确保一致性）
        sorted_params = json.dumps(additional_params, sort_keys=True)
        hash_input_parts.append(sorted_params)

    # 生成哈希
    hash_input = "|".join(hash_input_parts)
    hash_value = hashlib.md5(hash_input.encode("utf-8")).hexdigest()

    # 添加前缀以便识别
    return f"query:{hash_value}"


# ================================
# 查询缓存服务
# ================================


class QueryCache:
    """
    查询缓存服务类

    提供：
    - 智能查询缓存（基于查询哈希）
    - 基于数据类型的 TTL 策略
    - 缓存统计和监控
    """

    def __init__(self):
        """初始化缓存服务"""
        self.stats_key_prefix = "cache_stats:"

    async def get(
        self,
        query: str,
        symbol: Optional[str] = None,
        data_type: Optional[DataType] = None,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        从缓存获取查询结果

        Args:
            query: 查询字符串
            symbol: 代币符号（可选）
            data_type: 数据类型（可选）
            additional_params: 额外参数（可选）

        Returns:
            Optional[Dict]: 缓存的结果，不存在返回 None
        """
        try:
            # 生成查询哈希
            cache_key = generate_query_hash(query, symbol, data_type, additional_params)

            # 从缓存获取
            cached_data = await cache_get_json(cache_key)

            if cached_data:
                # 记录缓存命中
                await self._record_hit(data_type or DataType.OTHER)

                logger.debug(
                    f"缓存命中",
                    extra={
                        "cache_key": cache_key,
                        "query": query,
                        "symbol": symbol,
                        "data_type": data_type.value if data_type else None,
                    }
                )

                return cached_data

            # 记录缓存未命中
            await self._record_miss(data_type or DataType.OTHER)

            logger.debug(
                f"缓存未命中",
                extra={
                    "cache_key": cache_key,
                    "query": query,
                    "symbol": symbol,
                }
            )

            return None

        except Exception as e:
            logger.error(f"缓存获取失败: {e}", exc_info=True)
            return None

    async def set(
        self,
        query: str,
        data: Dict[str, Any],
        symbol: Optional[str] = None,
        data_type: Optional[DataType] = None,
        additional_params: Optional[Dict[str, Any]] = None,
        custom_ttl: Optional[int] = None
    ) -> bool:
        """
        设置查询结果缓存

        Args:
            query: 查询字符串
            data: 要缓存的数据
            symbol: 代币符号（可选）
            data_type: 数据类型（可选）
            additional_params: 额外参数（可选）
            custom_ttl: 自定义TTL（秒），None则使用默认策略

        Returns:
            bool: 是否成功
        """
        try:
            # 生成查询哈希
            cache_key = generate_query_hash(query, symbol, data_type, additional_params)

            # 确定TTL
            if custom_ttl is not None:
                ttl = custom_ttl
            else:
                ttl = TTL_CONFIG.get(data_type or DataType.OTHER, TTL_CONFIG[DataType.OTHER])

            # 添加缓存元数据
            cache_data = {
                "data": data,
                "metadata": {
                    "cached_at": datetime.utcnow().isoformat(),
                    "ttl": ttl,
                    "query": query,
                    "symbol": symbol,
                    "data_type": data_type.value if data_type else None,
                }
            }

            # 设置缓存
            success = await cache_set(cache_key, cache_data, ttl)

            if success:
                # 记录缓存写入
                await self._record_write(data_type or DataType.OTHER)

                logger.debug(
                    f"缓存写入成功",
                    extra={
                        "cache_key": cache_key,
                        "query": query,
                        "symbol": symbol,
                        "data_type": data_type.value if data_type else None,
                        "ttl": ttl,
                    }
                )

            return success

        except Exception as e:
            logger.error(f"缓存写入失败: {e}", exc_info=True)
            return False

    async def invalidate(
        self,
        query: str,
        symbol: Optional[str] = None,
        data_type: Optional[DataType] = None,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        使缓存失效（删除）

        Args:
            query: 查询字符串
            symbol: 代币符号（可选）
            data_type: 数据类型（可选）
            additional_params: 额外参数（可选）

        Returns:
            bool: 是否成功
        """
        try:
            # 生成查询哈希
            cache_key = generate_query_hash(query, symbol, data_type, additional_params)

            # 删除缓存
            deleted = await cache_delete(cache_key)

            if deleted > 0:
                logger.debug(
                    f"缓存失效成功",
                    extra={
                        "cache_key": cache_key,
                        "query": query,
                        "symbol": symbol,
                    }
                )
                return True

            return False

        except Exception as e:
            logger.error(f"缓存失效失败: {e}", exc_info=True)
            return False

    async def exists(
        self,
        query: str,
        symbol: Optional[str] = None,
        data_type: Optional[DataType] = None,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        检查缓存是否存在

        Args:
            query: 查询字符串
            symbol: 代币符号（可选）
            data_type: 数据类型（可选）
            additional_params: 额外参数（可选）

        Returns:
            bool: 是否存在
        """
        try:
            cache_key = generate_query_hash(query, symbol, data_type, additional_params)
            return await cache_exists(cache_key)
        except Exception as e:
            logger.error(f"缓存检查失败: {e}", exc_info=True)
            return False

    # ================================
    # 缓存统计
    # ================================

    async def _record_hit(self, data_type: DataType) -> None:
        """记录缓存命中（任务 9.7 集成指标追踪）"""
        try:
            # 全局命中计数（Redis）
            await cache_increment(f"{self.stats_key_prefix}hits")

            # 按数据类型的命中计数（Redis）
            await cache_increment(f"{self.stats_key_prefix}hits:{data_type.value}")

            # 记录到性能指标系统（任务 9.7）
            metrics_collector.record_cache_hit(cache_key=data_type.value)
        except Exception as e:
            logger.error(f"记录缓存命中失败: {e}")

    async def _record_miss(self, data_type: DataType) -> None:
        """记录缓存未命中（任务 9.7 集成指标追踪）"""
        try:
            # 全局未命中计数（Redis）
            await cache_increment(f"{self.stats_key_prefix}misses")

            # 按数据类型的未命中计数（Redis）
            await cache_increment(f"{self.stats_key_prefix}misses:{data_type.value}")

            # 记录到性能指标系统（任务 9.7）
            metrics_collector.record_cache_miss(cache_key=data_type.value)
        except Exception as e:
            logger.error(f"记录缓存未命中失败: {e}")

    async def _record_write(self, data_type: DataType) -> None:
        """记录缓存写入"""
        try:
            # 全局写入计数
            await cache_increment(f"{self.stats_key_prefix}writes")

            # 按数据类型的写入计数
            await cache_increment(f"{self.stats_key_prefix}writes:{data_type.value}")
        except Exception as e:
            logger.error(f"记录缓存写入失败: {e}")

    async def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            Dict: 统计信息
                - total_hits: 总命中次数
                - total_misses: 总未命中次数
                - total_writes: 总写入次数
                - hit_rate: 命中率（0-1）
                - by_type: 按数据类型的统计
        """
        try:
            # 获取全局统计
            total_hits = int(await cache_get(f"{self.stats_key_prefix}hits") or 0)
            total_misses = int(await cache_get(f"{self.stats_key_prefix}misses") or 0)
            total_writes = int(await cache_get(f"{self.stats_key_prefix}writes") or 0)

            # 计算命中率
            total_requests = total_hits + total_misses
            hit_rate = total_hits / total_requests if total_requests > 0 else 0.0

            # 按数据类型统计
            by_type = {}
            for data_type in DataType:
                type_hits = int(await cache_get(f"{self.stats_key_prefix}hits:{data_type.value}") or 0)
                type_misses = int(await cache_get(f"{self.stats_key_prefix}misses:{data_type.value}") or 0)
                type_writes = int(await cache_get(f"{self.stats_key_prefix}writes:{data_type.value}") or 0)

                type_requests = type_hits + type_misses
                type_hit_rate = type_hits / type_requests if type_requests > 0 else 0.0

                by_type[data_type.value] = {
                    "hits": type_hits,
                    "misses": type_misses,
                    "writes": type_writes,
                    "requests": type_requests,
                    "hit_rate": round(type_hit_rate, 4),
                }

            return {
                "total_hits": total_hits,
                "total_misses": total_misses,
                "total_writes": total_writes,
                "total_requests": total_requests,
                "hit_rate": round(hit_rate, 4),
                "by_type": by_type,
            }

        except Exception as e:
            logger.error(f"获取缓存统计失败: {e}", exc_info=True)
            return {
                "error": str(e),
                "total_hits": 0,
                "total_misses": 0,
                "total_writes": 0,
                "hit_rate": 0.0,
            }


# ================================
# 单例实例
# ================================

# 全局查询缓存实例
query_cache = QueryCache()


# ================================
# 便捷函数
# ================================


async def get_cached_query(
    query: str,
    symbol: Optional[str] = None,
    data_type: Optional[DataType] = None,
    **kwargs
) -> Optional[Dict[str, Any]]:
    """
    便捷函数：从缓存获取查询结果

    Args:
        query: 查询字符串
        symbol: 代币符号
        data_type: 数据类型
        **kwargs: 其他参数

    Returns:
        Optional[Dict]: 缓存的结果
    """
    return await query_cache.get(query, symbol, data_type, kwargs or None)


async def set_cached_query(
    query: str,
    data: Dict[str, Any],
    symbol: Optional[str] = None,
    data_type: Optional[DataType] = None,
    custom_ttl: Optional[int] = None,
    **kwargs
) -> bool:
    """
    便捷函数：设置查询结果缓存

    Args:
        query: 查询字符串
        data: 要缓存的数据
        symbol: 代币符号
        data_type: 数据类型
        custom_ttl: 自定义TTL（秒）
        **kwargs: 其他参数

    Returns:
        bool: 是否成功
    """
    return await query_cache.set(query, data, symbol, data_type, kwargs or None, custom_ttl)


async def invalidate_cached_query(
    query: str,
    symbol: Optional[str] = None,
    data_type: Optional[DataType] = None,
    **kwargs
) -> bool:
    """
    便捷函数：使查询缓存失效

    Args:
        query: 查询字符串
        symbol: 代币符号
        data_type: 数据类型
        **kwargs: 其他参数

    Returns:
        bool: 是否成功
    """
    return await query_cache.invalidate(query, symbol, data_type, kwargs or None)


async def get_cache_stats() -> Dict[str, Any]:
    """
    便捷函数：获取缓存统计

    Returns:
        Dict: 缓存统计信息
    """
    return await query_cache.get_stats()
