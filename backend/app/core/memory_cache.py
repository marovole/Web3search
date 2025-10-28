"""
L1内存缓存实现

使用LRU（Least Recently Used）淘汰策略的进程内缓存，
支持访问频率权重和容量限制。

主要特性：
- LRU淘汰策略（基于OrderedDict）
- 异步线程安全操作
- 访问频率权重计算
- TTL过期支持
- 统计信息收集
"""

import asyncio
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Optional, Dict
import logging

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """缓存项数据结构"""

    value: Any
    created_at: float = field(default_factory=time.time)
    last_access_time: float = field(default_factory=time.time)
    access_count: int = 0
    ttl: Optional[int] = None  # TTL in seconds

    def is_expired(self) -> bool:
        """检查缓存项是否过期"""
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl

    def update_access(self):
        """更新访问信息"""
        self.last_access_time = time.time()
        self.access_count += 1

    def get_hotness_score(self, recency_weight: float = 0.7) -> float:
        """
        计算热度分数（用于淘汰决策）

        热度 = 访问频率 * 新鲜度权重
        - access_count: 访问次数越多，分数越高
        - recency: 最近访问时间越近，分数越高

        Args:
            recency_weight: 新鲜度权重（0-1），默认0.7

        Returns:
            float: 热度分数，越高表示越热门
        """
        age = time.time() - self.created_at
        recency = 1.0 / (1.0 + age / 3600.0)  # 1小时衰减因子

        frequency = self.access_count

        return frequency * (recency_weight * recency + (1 - recency_weight))


class MemoryCache:
    """
    L1内存缓存

    使用LRU淘汰策略的进程内缓存，支持：
    - 容量限制（默认100条）
    - 访问频率权重
    - TTL过期
    - 异步线程安全操作
    """

    def __init__(
        self,
        max_size: int = 100,
        default_ttl: Optional[int] = None,
        recency_weight: float = 0.7
    ):
        """
        初始化内存缓存

        Args:
            max_size: 最大缓存条目数
            default_ttl: 默认TTL（秒），None表示不过期
            recency_weight: 新鲜度权重（0-1），用于热度计算
        """
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._recency_weight = recency_weight
        self._lock = asyncio.Lock()

        # 统计信息
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "expirations": 0,
            "writes": 0
        }

        logger.info(
            f"MemoryCache initialized: max_size={max_size}, "
            f"default_ttl={default_ttl}, recency_weight={recency_weight}"
        )

    async def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存值，不存在或过期返回None
        """
        async with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                self._stats["misses"] += 1
                return None

            # 检查是否过期
            if entry.is_expired():
                del self._cache[key]
                self._stats["expirations"] += 1
                self._stats["misses"] += 1
                logger.debug(f"Cache key expired: {key}")
                return None

            # 更新访问信息
            entry.update_access()

            # LRU: 移动到末尾（最近使用）
            self._cache.move_to_end(key)

            self._stats["hits"] += 1
            return entry.value

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> None:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl: TTL（秒），None使用默认值
        """
        async with self._lock:
            # 如果key已存在，更新值
            if key in self._cache:
                entry = self._cache[key]
                entry.value = value
                entry.created_at = time.time()
                entry.ttl = ttl if ttl is not None else self._default_ttl
                self._cache.move_to_end(key)
            else:
                # 新增缓存项
                # 检查容量，必要时淘汰
                if len(self._cache) >= self._max_size:
                    await self._evict()

                entry = CacheEntry(
                    value=value,
                    ttl=ttl if ttl is not None else self._default_ttl
                )
                self._cache[key] = entry

            self._stats["writes"] += 1
            logger.debug(f"Cache set: {key}, ttl={entry.ttl}")

    async def delete(self, key: str) -> bool:
        """
        删除缓存项

        Args:
            key: 缓存键

        Returns:
            是否删除成功
        """
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"Cache deleted: {key}")
                return True
            return False

    async def clear(self) -> None:
        """清空所有缓存"""
        async with self._lock:
            self._cache.clear()
            logger.info("Cache cleared")

    async def exists(self, key: str) -> bool:
        """
        检查缓存键是否存在且未过期

        Args:
            key: 缓存键

        Returns:
            是否存在
        """
        async with self._lock:
            if key not in self._cache:
                return False

            entry = self._cache[key]
            if entry.is_expired():
                del self._cache[key]
                self._stats["expirations"] += 1
                return False

            return True

    async def _evict(self) -> None:
        """
        淘汰缓存项

        淘汰策略：
        1. 优先淘汰过期项
        2. 基于热度分数淘汰（LRU + 访问频率）
        """
        # 首先尝试淘汰过期项
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired()
        ]

        if expired_keys:
            for key in expired_keys:
                del self._cache[key]
                self._stats["expirations"] += 1
            logger.debug(f"Evicted {len(expired_keys)} expired entries")
            return

        # 没有过期项，基于热度分数淘汰
        if not self._cache:
            return

        # 计算所有项的热度分数
        scored_items = [
            (key, entry.get_hotness_score(self._recency_weight))
            for key, entry in self._cache.items()
        ]

        # 淘汰热度最低的项
        key_to_evict = min(scored_items, key=lambda x: x[1])[0]
        del self._cache[key_to_evict]
        self._stats["evictions"] += 1

        logger.debug(f"Evicted cache entry: {key_to_evict}")

    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            统计信息字典
        """
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = (
            self._stats["hits"] / total_requests
            if total_requests > 0
            else 0.0
        )

        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "hit_rate": hit_rate,
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "evictions": self._stats["evictions"],
            "expirations": self._stats["expirations"],
            "writes": self._stats["writes"]
        }

    def reset_stats(self) -> None:
        """重置统计信息"""
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "expirations": 0,
            "writes": 0
        }
        logger.info("Cache stats reset")

    async def get_all_keys(self) -> list[str]:
        """获取所有缓存键（用于调试）"""
        async with self._lock:
            return list(self._cache.keys())

    async def get_size(self) -> int:
        """获取当前缓存大小"""
        async with self._lock:
            return len(self._cache)


# 全局L1缓存实例（单例）
_memory_cache_instance: Optional[MemoryCache] = None


def get_memory_cache(
    max_size: int = 100,
    default_ttl: Optional[int] = 300,  # 5分钟
    recency_weight: float = 0.7
) -> MemoryCache:
    """
    获取全局L1内存缓存实例（单例模式）

    Args:
        max_size: 最大缓存条目数
        default_ttl: 默认TTL（秒）
        recency_weight: 新鲜度权重

    Returns:
        MemoryCache实例
    """
    global _memory_cache_instance

    if _memory_cache_instance is None:
        _memory_cache_instance = MemoryCache(
            max_size=max_size,
            default_ttl=default_ttl,
            recency_weight=recency_weight
        )
        logger.info("Global L1 memory cache instance created")

    return _memory_cache_instance
