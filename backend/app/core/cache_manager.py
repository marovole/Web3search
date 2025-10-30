"""
缓存管理器（L1/L2缓存协调）

实现两级缓存架构：
- L1: 内存缓存（MemoryCache，100条记录）
- L2: Redis缓存（QueryCache，10,000条记录）

协调策略：
- 查询：L1 → L2 → 数据源（L2命中时回填L1）
- 写入：Write-through（同时写L1和L2）
- 删除：同时删除L1和L2

性能目标：
- L1命中率：60-70%（热点数据）
- 总命中率：85%+（L1+L2）
- L1延迟：<1ms
- L2延迟：<10ms
"""

import logging
from typing import Any, Optional, Dict
from dataclasses import dataclass
from datetime import datetime
import time

from app.core.memory_cache import get_memory_cache, MemoryCache
from app.core.query_cache import (
    QueryCache,
    DataType,
    TTL_CONFIG,
    generate_query_hash,
)
from app.core.metrics import metrics_collector

logger = logging.getLogger(__name__)


@dataclass
class CacheResult:
    """
    缓存结果包装类
    
    包含缓存数据和元数据，用于生成响应头
    """
    data: Dict[str, Any]
    cache_status: str  # "HIT-L1" | "HIT-L2" | "MISS"
    cache_age: Optional[int] = None  # 缓存年龄（秒）
    data_source: str = "live"  # "cached" | "live" | "fallback"
    
    def to_headers(self) -> Dict[str, str]:
        """
        转换为HTTP响应头
        
        Returns:
            包含X-Cache, X-Cache-Age, X-Data-Source的字典
        """
        headers = {
            "X-Cache": self.cache_status,
            "X-Data-Source": self.data_source,
        }
        if self.cache_age is not None:
            headers["X-Cache-Age"] = str(self.cache_age)
        return headers


class CacheManager:
    """
    缓存管理器

    协调L1内存缓存和L2 Redis缓存的统一接口
    """

    def __init__(
        self,
        l1_cache: Optional[MemoryCache] = None,
        l2_cache: Optional[QueryCache] = None
    ):
        """
        初始化缓存管理器

        Args:
            l1_cache: L1内存缓存实例，None则使用全局实例
            l2_cache: L2 Redis缓存实例，None则创建新实例
        """
        # L1: 内存缓存
        self._l1_cache = l1_cache or get_memory_cache()

        # L2: Redis缓存
        self._l2_cache = l2_cache or QueryCache()

        logger.info("CacheManager initialized with L1 + L2 architecture")

    async def get(
        self,
        query: str,
        symbol: Optional[str] = None,
        data_type: Optional[DataType] = None,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> Optional[CacheResult]:
        """
        获取缓存数据（L1 → L2 → None），返回包含元数据的CacheResult

        查询流程：
        1. 尝试从L1内存缓存获取
        2. L1 miss -> 尝试从L2 Redis获取
        3. L2 hit -> 回填L1缓存
        4. L2 miss -> 返回None

        Args:
            query: 查询字符串
            symbol: 代币符号
            data_type: 数据类型
            additional_params: 额外参数

        Returns:
            CacheResult对象（包含数据和元数据）或None
        """
        # 生成缓存键
        cache_key = generate_query_hash(query, symbol, data_type, additional_params)

        # 1. 尝试L1缓存
        start_time = time.time()
        l1_entry = await self._l1_cache.get_entry(cache_key)
        l1_latency = (time.time() - start_time) * 1000  # 转换为毫秒

        if l1_entry is not None:
            logger.debug(
                f"L1 cache hit: {cache_key}, latency: {l1_latency:.2f}ms"
            )
            # 记录L1命中指标
            metrics_collector.record_cache_hit(
                cache_key=f"L1:{data_type.value if data_type else 'other'}"
            )
            
            # 计算缓存年龄
            cache_age = int(time.time() - l1_entry.created_at)
            
            return CacheResult(
                data=l1_entry.value if isinstance(l1_entry.value, dict) else {"content": l1_entry.value},
                cache_status="HIT-L1",
                cache_age=cache_age,
                data_source="cached"
            )

        logger.debug(f"L1 cache miss: {cache_key}")

        # 2. L1未命中，尝试L2缓存
        start_time = time.time()
        l2_result = await self._l2_cache.get(
            query, symbol, data_type, additional_params
        )
        l2_latency = (time.time() - start_time) * 1000

        if l2_result is not None:
            logger.debug(
                f"L2 cache hit: {cache_key}, latency: {l2_latency:.2f}ms"
            )
            # 记录L2命中指标
            metrics_collector.record_cache_hit(
                cache_key=f"L2:{data_type.value if data_type else 'other'}"
            )

            # 提取实际数据和元数据
            actual_data = l2_result.get("data", l2_result)
            metadata = l2_result.get("metadata", {})
            
            # 计算缓存年龄
            cache_age = None
            if "cached_at" in metadata:
                try:
                    cached_at_str = metadata["cached_at"]
                    # 处理ISO格式时间戳
                    if cached_at_str.endswith("Z"):
                        cached_at_str = cached_at_str[:-1] + "+00:00"
                    cached_at = datetime.fromisoformat(cached_at_str)
                    cache_age = int((datetime.utcnow() - cached_at.replace(tzinfo=None)).total_seconds())
                except Exception as e:
                    logger.warning(f"Failed to parse cached_at: {e}")

            # 3. L2命中，回填L1缓存
            try:
                # 获取TTL
                ttl = TTL_CONFIG.get(
                    data_type or DataType.OTHER,
                    TTL_CONFIG[DataType.OTHER]
                )

                # 回填L1
                await self._l1_cache.set(cache_key, actual_data, ttl)
                logger.debug(f"L1 cache backfilled from L2: {cache_key}")

            except Exception as e:
                logger.warning(f"Failed to backfill L1 cache: {e}")

            return CacheResult(
                data=actual_data if isinstance(actual_data, dict) else {"content": actual_data},
                cache_status="HIT-L2",
                cache_age=cache_age,
                data_source="cached"
            )

        logger.debug(f"L2 cache miss: {cache_key}")
        # 记录L2未命中
        metrics_collector.record_cache_miss(
            cache_key=f"L2:{data_type.value if data_type else 'other'}"
        )

        return None

    async def get_without_metadata(
        self,
        query: str,
        symbol: Optional[str] = None,
        data_type: Optional[DataType] = None,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        获取缓存数据（不返回元数据，向后兼容）
        
        这是一个便捷方法，向后兼容旧的代码
        
        Returns:
            缓存数据或None
        """
        result = await self.get(query, symbol, data_type, additional_params)
        return result.data if result else None

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
        设置缓存数据（Write-through: 同时写L1和L2）

        写入流程：
        1. 同时写入L1和L2
        2. 使用相同的TTL策略

        Args:
            query: 查询字符串
            data: 要缓存的数据
            symbol: 代币符号
            data_type: 数据类型
            additional_params: 额外参数
            custom_ttl: 自定义TTL（秒）

        Returns:
            是否成功（L2成功即为成功，L1失败不影响）
        """
        # 生成缓存键
        cache_key = generate_query_hash(query, symbol, data_type, additional_params)

        # 确定TTL
        if custom_ttl is not None:
            ttl = custom_ttl
        else:
            ttl = TTL_CONFIG.get(
                data_type or DataType.OTHER,
                TTL_CONFIG[DataType.OTHER]
            )

        # 1. 写入L2 Redis缓存（主存储）
        l2_success = await self._l2_cache.set(
            query=query,
            data=data,
            symbol=symbol,
            data_type=data_type,
            additional_params=additional_params,
            custom_ttl=custom_ttl
        )

        if not l2_success:
            logger.error(f"L2 cache write failed: {cache_key}")
            return False

        # 2. 写入L1内存缓存
        try:
            await self._l1_cache.set(cache_key, data, ttl)
            logger.debug(
                f"Cache write success (L1+L2): {cache_key}, ttl={ttl}s"
            )
        except Exception as e:
            # L1写入失败不影响整体成功（L2已成功）
            logger.warning(
                f"L1 cache write failed (L2 ok): {cache_key}, error: {e}"
            )

        return True

    async def delete(
        self,
        query: str,
        symbol: Optional[str] = None,
        data_type: Optional[DataType] = None,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        删除缓存（同时删除L1和L2）

        Args:
            query: 查询字符串
            symbol: 代币符号
            data_type: 数据类型
            additional_params: 额外参数

        Returns:
            是否成功（至少一个删除成功）
        """
        # 生成缓存键
        cache_key = generate_query_hash(query, symbol, data_type, additional_params)

        # 同时删除L1和L2
        l1_deleted = await self._l1_cache.delete(cache_key)
        l2_deleted = await self._l2_cache.invalidate(
            query, symbol, data_type, additional_params
        )

        success = l1_deleted or l2_deleted

        if success:
            logger.debug(
                f"Cache deleted: {cache_key}, "
                f"L1={l1_deleted}, L2={l2_deleted}"
            )

        return success

    async def exists(
        self,
        query: str,
        symbol: Optional[str] = None,
        data_type: Optional[DataType] = None,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        检查缓存是否存在（检查L1或L2）

        Args:
            query: 查询字符串
            symbol: 代币符号
            data_type: 数据类型
            additional_params: 额外参数

        Returns:
            是否存在（L1或L2存在即为存在）
        """
        # 生成缓存键
        cache_key = generate_query_hash(query, symbol, data_type, additional_params)

        # 先检查L1
        l1_exists = await self._l1_cache.exists(cache_key)
        if l1_exists:
            return True

        # L1不存在，检查L2
        return await self._l2_cache.exists(
            query, symbol, data_type, additional_params
        )

    async def clear_l1(self) -> None:
        """清空L1内存缓存"""
        await self._l1_cache.clear()
        logger.info("L1 cache cleared")

    async def get_stats(self) -> Dict[str, Any]:
        """
        获取合并的缓存统计信息（L1 + L2）

        Returns:
            统计信息字典，包含：
            - l1: L1缓存统计
            - l2: L2缓存统计
            - combined: 合并统计（总命中率等）
        """
        # 获取L1统计
        l1_stats = self._l1_cache.get_stats()

        # 获取L2统计
        l2_stats = await self._l2_cache.get_stats()

        # 计算合并统计
        total_hits = l1_stats["hits"] + l2_stats["total_hits"]
        total_misses = l1_stats["misses"] + l2_stats["total_misses"]
        total_requests = total_hits + total_misses
        combined_hit_rate = (
            total_hits / total_requests if total_requests > 0 else 0.0
        )

        return {
            "l1": l1_stats,
            "l2": l2_stats,
            "combined": {
                "total_hits": total_hits,
                "total_misses": total_misses,
                "total_requests": total_requests,
                "hit_rate": round(combined_hit_rate, 4),
                "l1_hit_rate": l1_stats["hit_rate"],
                "l2_hit_rate": l2_stats["hit_rate"],
            }
        }

    async def get_l1_keys(self) -> list[str]:
        """获取L1缓存的所有键（调试用）"""
        return await self._l1_cache.get_all_keys()

    async def get_l1_size(self) -> int:
        """获取L1缓存当前大小"""
        return await self._l1_cache.get_size()


# ================================
# 全局单例实例
# ================================

_cache_manager_instance: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """
    获取全局缓存管理器实例（单例模式）

    Returns:
        CacheManager实例
    """
    global _cache_manager_instance

    if _cache_manager_instance is None:
        _cache_manager_instance = CacheManager()
        logger.info("Global CacheManager instance created")

    return _cache_manager_instance


# ================================
# 便捷函数（向后兼容query_cache接口）
# ================================


async def get_cached_query(
    query: str,
    symbol: Optional[str] = None,
    data_type: Optional[DataType] = None,
    **kwargs
) -> Optional[Dict[str, Any]]:
    """
    便捷函数：从缓存获取查询结果（L1+L2）

    Args:
        query: 查询字符串
        symbol: 代币符号
        data_type: 数据类型
        **kwargs: 其他参数

    Returns:
        缓存数据或None
    """
    cache_manager = get_cache_manager()
    return await cache_manager.get(query, symbol, data_type, kwargs or None)


async def set_cached_query(
    query: str,
    data: Dict[str, Any],
    symbol: Optional[str] = None,
    data_type: Optional[DataType] = None,
    custom_ttl: Optional[int] = None,
    **kwargs
) -> bool:
    """
    便捷函数：设置查询结果缓存（L1+L2）

    Args:
        query: 查询字符串
        data: 要缓存的数据
        symbol: 代币符号
        data_type: 数据类型
        custom_ttl: 自定义TTL（秒）
        **kwargs: 其他参数

    Returns:
        是否成功
    """
    cache_manager = get_cache_manager()
    return await cache_manager.set(
        query, data, symbol, data_type, kwargs or None, custom_ttl
    )


async def invalidate_cached_query(
    query: str,
    symbol: Optional[str] = None,
    data_type: Optional[DataType] = None,
    **kwargs
) -> bool:
    """
    便捷函数：使查询缓存失效（L1+L2）

    Args:
        query: 查询字符串
        symbol: 代币符号
        data_type: 数据类型
        **kwargs: 其他参数

    Returns:
        是否成功
    """
    cache_manager = get_cache_manager()
    return await cache_manager.delete(query, symbol, data_type, kwargs or None)


async def get_cache_stats() -> Dict[str, Any]:
    """
    便捷函数：获取缓存统计（L1+L2）

    Returns:
        合并的缓存统计信息
    """
    cache_manager = get_cache_manager()
    return await cache_manager.get_stats()
