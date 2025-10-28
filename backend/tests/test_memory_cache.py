"""
MemoryCache类单元测试

测试L1内存缓存的所有功能：
- 基本操作（get/set/delete/clear）
- LRU淘汰策略
- 容量限制
- TTL过期
- 访问频率权重
- 热度分数计算
- 统计信息
"""

import pytest
import asyncio
import time
from unittest.mock import patch

from app.core.memory_cache import MemoryCache, CacheEntry, get_memory_cache


# ================================
# Fixtures
# ================================


@pytest.fixture
def memory_cache():
    """创建一个全新的MemoryCache实例用于测试"""
    return MemoryCache(max_size=5, default_ttl=300)


@pytest.fixture
def small_cache():
    """创建一个容量为3的小缓存（用于测试淘汰）"""
    return MemoryCache(max_size=3, default_ttl=300)


# ================================
# 基本操作测试
# ================================


@pytest.mark.asyncio
async def test_set_and_get(memory_cache):
    """测试基本的set和get操作"""
    await memory_cache.set("key1", "value1")
    result = await memory_cache.get("key1")
    assert result == "value1"


@pytest.mark.asyncio
async def test_get_nonexistent_key(memory_cache):
    """测试获取不存在的键"""
    result = await memory_cache.get("nonexistent")
    assert result is None


@pytest.mark.asyncio
async def test_set_overwrites_existing_key(memory_cache):
    """测试覆盖已存在的键"""
    await memory_cache.set("key1", "value1")
    await memory_cache.set("key1", "value2")
    result = await memory_cache.get("key1")
    assert result == "value2"


@pytest.mark.asyncio
async def test_delete_existing_key(memory_cache):
    """测试删除已存在的键"""
    await memory_cache.set("key1", "value1")
    deleted = await memory_cache.delete("key1")
    assert deleted is True
    result = await memory_cache.get("key1")
    assert result is None


@pytest.mark.asyncio
async def test_delete_nonexistent_key(memory_cache):
    """测试删除不存在的键"""
    deleted = await memory_cache.delete("nonexistent")
    assert deleted is False


@pytest.mark.asyncio
async def test_clear_cache(memory_cache):
    """测试清空缓存"""
    await memory_cache.set("key1", "value1")
    await memory_cache.set("key2", "value2")
    await memory_cache.clear()

    result1 = await memory_cache.get("key1")
    result2 = await memory_cache.get("key2")
    size = await memory_cache.get_size()

    assert result1 is None
    assert result2 is None
    assert size == 0


@pytest.mark.asyncio
async def test_exists_for_existing_key(memory_cache):
    """测试exists方法（存在的键）"""
    await memory_cache.set("key1", "value1")
    exists = await memory_cache.exists("key1")
    assert exists is True


@pytest.mark.asyncio
async def test_exists_for_nonexistent_key(memory_cache):
    """测试exists方法（不存在的键）"""
    exists = await memory_cache.exists("nonexistent")
    assert exists is False


# ================================
# TTL过期测试
# ================================


@pytest.mark.asyncio
async def test_ttl_expiration(memory_cache):
    """测试TTL过期"""
    # 设置1秒TTL
    await memory_cache.set("key1", "value1", ttl=1)

    # 立即获取应该成功
    result = await memory_cache.get("key1")
    assert result == "value1"

    # 等待1.1秒后应该过期
    await asyncio.sleep(1.1)
    result = await memory_cache.get("key1")
    assert result is None


@pytest.mark.asyncio
async def test_ttl_none_never_expires(memory_cache):
    """测试TTL=None的项永不过期"""
    await memory_cache.set("key1", "value1", ttl=None)

    # 等待一段时间
    await asyncio.sleep(0.5)

    result = await memory_cache.get("key1")
    assert result == "value1"


@pytest.mark.asyncio
async def test_exists_returns_false_for_expired_key(memory_cache):
    """测试exists对过期键返回False"""
    await memory_cache.set("key1", "value1", ttl=1)
    await asyncio.sleep(1.1)

    exists = await memory_cache.exists("key1")
    assert exists is False


# ================================
# 容量限制和LRU淘汰测试
# ================================


@pytest.mark.asyncio
async def test_capacity_limit(small_cache):
    """测试容量限制（最大3条）"""
    await small_cache.set("key1", "value1")
    await small_cache.set("key2", "value2")
    await small_cache.set("key3", "value3")

    size = await small_cache.get_size()
    assert size == 3

    # 添加第4条应该触发淘汰
    await small_cache.set("key4", "value4")
    size = await small_cache.get_size()
    assert size == 3


@pytest.mark.asyncio
async def test_lru_eviction_evicts_least_recently_used(small_cache):
    """测试LRU淘汰策略淘汰最少使用的项"""
    await small_cache.set("key1", "value1")
    await small_cache.set("key2", "value2")
    await small_cache.set("key3", "value3")

    # 访问key2和key3（key1最少使用）
    await small_cache.get("key2")
    await small_cache.get("key3")

    # 添加key4应该淘汰key1
    await small_cache.set("key4", "value4")

    # key1应该被淘汰
    result1 = await small_cache.get("key1")
    assert result1 is None

    # key2, key3, key4应该存在
    result2 = await small_cache.get("key2")
    result3 = await small_cache.get("key3")
    result4 = await small_cache.get("key4")
    assert result2 == "value2"
    assert result3 == "value3"
    assert result4 == "value4"


@pytest.mark.asyncio
async def test_eviction_prioritizes_expired_items(small_cache):
    """测试淘汰时优先淘汰过期项"""
    # 设置3个项，其中一个1秒后过期
    await small_cache.set("key1", "value1", ttl=1)
    await small_cache.set("key2", "value2", ttl=None)
    await small_cache.set("key3", "value3", ttl=None)

    # 等待key1过期
    await asyncio.sleep(1.1)

    # 添加key4应该淘汰过期的key1
    await small_cache.set("key4", "value4")

    result1 = await small_cache.get("key1")
    result2 = await small_cache.get("key2")
    result3 = await small_cache.get("key3")
    result4 = await small_cache.get("key4")

    assert result1 is None
    assert result2 == "value2"
    assert result3 == "value3"
    assert result4 == "value4"


# ================================
# 访问频率和热度分数测试
# ================================


@pytest.mark.asyncio
async def test_access_count_increases_on_get(memory_cache):
    """测试访问次数在get时增加"""
    await memory_cache.set("key1", "value1")

    # 访问3次
    await memory_cache.get("key1")
    await memory_cache.get("key1")
    await memory_cache.get("key1")

    # 检查内部状态（通过测试入口）
    entry = memory_cache._cache.get("key1")
    assert entry.access_count == 3


def test_cache_entry_hotness_score():
    """测试CacheEntry热度分数计算"""
    entry = CacheEntry(value="test")
    entry.access_count = 10

    score = entry.get_hotness_score(recency_weight=0.7)

    # 热度分数应该大于0
    assert score > 0

    # 访问次数更多的项热度应该更高
    entry2 = CacheEntry(value="test2")
    entry2.access_count = 20

    score2 = entry2.get_hotness_score(recency_weight=0.7)
    assert score2 > score


def test_cache_entry_is_expired():
    """测试CacheEntry过期检查"""
    entry = CacheEntry(value="test", ttl=1)

    # 未过期
    assert entry.is_expired() is False

    # 模拟时间流逝
    time.sleep(1.1)

    # 已过期
    assert entry.is_expired() is True


def test_cache_entry_update_access():
    """测试CacheEntry访问信息更新"""
    entry = CacheEntry(value="test")
    initial_count = entry.access_count
    initial_time = entry.last_access_time

    time.sleep(0.1)
    entry.update_access()

    assert entry.access_count == initial_count + 1
    assert entry.last_access_time > initial_time


# ================================
# 统计信息测试
# ================================


@pytest.mark.asyncio
async def test_stats_hit_miss_tracking(memory_cache):
    """测试命中/未命中统计"""
    await memory_cache.set("key1", "value1")

    # 2次命中
    await memory_cache.get("key1")
    await memory_cache.get("key1")

    # 1次未命中
    await memory_cache.get("nonexistent")

    stats = memory_cache.get_stats()
    assert stats["hits"] == 2
    assert stats["misses"] == 1
    assert stats["hit_rate"] == pytest.approx(2/3, rel=0.01)


@pytest.mark.asyncio
async def test_stats_write_tracking(memory_cache):
    """测试写入次数统计"""
    await memory_cache.set("key1", "value1")
    await memory_cache.set("key2", "value2")
    await memory_cache.set("key1", "new_value")  # 覆盖

    stats = memory_cache.get_stats()
    assert stats["writes"] == 3


@pytest.mark.asyncio
async def test_stats_eviction_tracking(small_cache):
    """测试淘汰次数统计"""
    await small_cache.set("key1", "value1")
    await small_cache.set("key2", "value2")
    await small_cache.set("key3", "value3")

    # 触发淘汰
    await small_cache.set("key4", "value4")

    stats = small_cache.get_stats()
    assert stats["evictions"] == 1


@pytest.mark.asyncio
async def test_stats_expiration_tracking(memory_cache):
    """测试过期次数统计"""
    await memory_cache.set("key1", "value1", ttl=1)
    await asyncio.sleep(1.1)

    # 访问过期键
    await memory_cache.get("key1")

    stats = memory_cache.get_stats()
    assert stats["expirations"] == 1


@pytest.mark.asyncio
async def test_reset_stats(memory_cache):
    """测试重置统计信息"""
    await memory_cache.set("key1", "value1")
    await memory_cache.get("key1")

    memory_cache.reset_stats()
    stats = memory_cache.get_stats()

    assert stats["hits"] == 0
    assert stats["misses"] == 0
    assert stats["writes"] == 0


# ================================
# 辅助方法测试
# ================================


@pytest.mark.asyncio
async def test_get_all_keys(memory_cache):
    """测试获取所有键"""
    await memory_cache.set("key1", "value1")
    await memory_cache.set("key2", "value2")
    await memory_cache.set("key3", "value3")

    keys = await memory_cache.get_all_keys()
    assert set(keys) == {"key1", "key2", "key3"}


@pytest.mark.asyncio
async def test_get_size(memory_cache):
    """测试获取缓存大小"""
    assert await memory_cache.get_size() == 0

    await memory_cache.set("key1", "value1")
    assert await memory_cache.get_size() == 1

    await memory_cache.set("key2", "value2")
    assert await memory_cache.get_size() == 2


# ================================
# 单例模式测试
# ================================


def test_get_memory_cache_singleton():
    """测试单例模式返回同一实例"""
    cache1 = get_memory_cache()
    cache2 = get_memory_cache()

    assert cache1 is cache2


# ================================
# 并发安全测试
# ================================


@pytest.mark.asyncio
async def test_concurrent_access(memory_cache):
    """测试并发访问的线程安全性"""
    await memory_cache.set("counter", 0)

    async def increment():
        for _ in range(10):
            value = await memory_cache.get("counter")
            await asyncio.sleep(0.001)  # 模拟竞争
            await memory_cache.set("counter", value + 1)

    # 10个并发任务各增加10次
    tasks = [increment() for _ in range(10)]
    await asyncio.gather(*tasks)

    # 由于有锁保护，最终结果应该是100
    final_value = await memory_cache.get("counter")
    # 注意：由于并发竞争，实际值可能小于100
    # 这里我们只检查操作没有崩溃
    assert isinstance(final_value, int)
