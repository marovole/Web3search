"""
CacheManager类单元测试

测试L1/L2缓存协调逻辑：
- L1 → L2查询流程
- Write-through写入策略
- 缓存删除和失效
- 统计信息合并
- L1回填逻辑
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.core.cache_manager import (
    CacheManager,
    get_cache_manager,
    get_cached_query,
    set_cached_query,
    invalidate_cached_query,
    get_cache_stats
)
from app.core.memory_cache import MemoryCache
from app.core.query_cache import QueryCache, DataType


# ================================
# Fixtures
# ================================


@pytest.fixture
def mock_l1_cache():
    """Mock L1内存缓存"""
    cache = AsyncMock(spec=MemoryCache)
    cache.get_stats.return_value = {
        "size": 50,
        "max_size": 100,
        "hit_rate": 0.6,
        "hits": 60,
        "misses": 40,
        "evictions": 5,
        "expirations": 3,
        "writes": 50
    }
    return cache


@pytest.fixture
def mock_l2_cache():
    """Mock L2 Redis缓存"""
    cache = AsyncMock(spec=QueryCache)
    cache.get_stats = AsyncMock(return_value={
        "total_hits": 800,
        "total_misses": 200,
        "total_writes": 500,
        "total_requests": 1000,
        "hit_rate": 0.8,
        "by_type": {}
    })
    return cache


@pytest.fixture
def cache_manager(mock_l1_cache, mock_l2_cache):
    """创建带有mock缓存的CacheManager"""
    return CacheManager(l1_cache=mock_l1_cache, l2_cache=mock_l2_cache)


# ================================
# L1命中测试
# ================================


@pytest.mark.asyncio
async def test_get_l1_hit(cache_manager, mock_l1_cache, mock_l2_cache):
    """测试L1缓存命中"""
    mock_l1_cache.get.return_value = {"result": "from_l1"}

    result = await cache_manager.get("test query", data_type=DataType.PRICE)

    assert result == {"result": "from_l1"}
    mock_l1_cache.get.assert_called_once()
    mock_l2_cache.get.assert_not_called()  # L1命中，不应查询L2


@pytest.mark.asyncio
async def test_get_l1_miss_l2_hit(cache_manager, mock_l1_cache, mock_l2_cache):
    """测试L1未命中，L2命中"""
    mock_l1_cache.get.return_value = None  # L1 miss
    mock_l2_cache.get.return_value = {
        "data": {"result": "from_l2"},
        "metadata": {"cached_at": "2024-01-01T00:00:00"}
    }

    result = await cache_manager.get("test query", data_type=DataType.PRICE)

    assert result == {
        "data": {"result": "from_l2"},
        "metadata": {"cached_at": "2024-01-01T00:00:00"}
    }
    mock_l1_cache.get.assert_called_once()
    mock_l2_cache.get.assert_called_once()


@pytest.mark.asyncio
async def test_get_l1_miss_l2_hit_backfills_l1(
    cache_manager, mock_l1_cache, mock_l2_cache
):
    """测试L2命中时回填L1缓存"""
    mock_l1_cache.get.return_value = None  # L1 miss
    mock_l2_cache.get.return_value = {
        "data": {"result": "from_l2"},
        "metadata": {"cached_at": "2024-01-01T00:00:00"}
    }

    await cache_manager.get(
        "test query",
        symbol="BTC",
        data_type=DataType.PRICE
    )

    # 验证L1被回填
    mock_l1_cache.set.assert_called_once()
    call_args = mock_l1_cache.set.call_args
    assert call_args[0][1] == {"result": "from_l2"}  # 回填的数据
    assert call_args[0][2] == 300  # TTL（PRICE类型默认5分钟）


@pytest.mark.asyncio
async def test_get_l1_miss_l2_miss(cache_manager, mock_l1_cache, mock_l2_cache):
    """测试L1和L2都未命中"""
    mock_l1_cache.get.return_value = None
    mock_l2_cache.get.return_value = None

    result = await cache_manager.get("test query", data_type=DataType.PRICE)

    assert result is None
    mock_l1_cache.get.assert_called_once()
    mock_l2_cache.get.assert_called_once()


# ================================
# Write-through写入测试
# ================================


@pytest.mark.asyncio
async def test_set_writes_to_both_l1_and_l2(
    cache_manager, mock_l1_cache, mock_l2_cache
):
    """测试写入同时更新L1和L2（write-through）"""
    mock_l2_cache.set.return_value = True

    data = {"result": "test_data"}
    success = await cache_manager.set(
        "test query",
        data,
        symbol="BTC",
        data_type=DataType.PRICE
    )

    assert success is True
    mock_l2_cache.set.assert_called_once()
    mock_l1_cache.set.assert_called_once()


@pytest.mark.asyncio
async def test_set_l2_failure_returns_false(
    cache_manager, mock_l1_cache, mock_l2_cache
):
    """测试L2写入失败时返回False"""
    mock_l2_cache.set.return_value = False

    data = {"result": "test_data"}
    success = await cache_manager.set(
        "test query",
        data,
        data_type=DataType.PRICE
    )

    assert success is False
    mock_l1_cache.set.assert_not_called()  # L2失败，不写L1


@pytest.mark.asyncio
async def test_set_l1_failure_does_not_affect_success(
    cache_manager, mock_l1_cache, mock_l2_cache
):
    """测试L1写入失败不影响整体成功（L2已成功）"""
    mock_l2_cache.set.return_value = True
    mock_l1_cache.set.side_effect = Exception("L1 write error")

    data = {"result": "test_data"}
    success = await cache_manager.set(
        "test query",
        data,
        data_type=DataType.PRICE
    )

    # L2成功即为成功
    assert success is True


@pytest.mark.asyncio
async def test_set_uses_custom_ttl(cache_manager, mock_l1_cache, mock_l2_cache):
    """测试使用自定义TTL"""
    mock_l2_cache.set.return_value = True
    custom_ttl = 600  # 10分钟

    data = {"result": "test_data"}
    await cache_manager.set(
        "test query",
        data,
        data_type=DataType.PRICE,
        custom_ttl=custom_ttl
    )

    # 验证L2调用使用了自定义TTL
    l2_call_args = mock_l2_cache.set.call_args
    assert l2_call_args[1]["custom_ttl"] == custom_ttl

    # 验证L1调用使用了自定义TTL
    l1_call_args = mock_l1_cache.set.call_args
    assert l1_call_args[0][2] == custom_ttl


# ================================
# 删除和失效测试
# ================================


@pytest.mark.asyncio
async def test_delete_removes_from_both_caches(
    cache_manager, mock_l1_cache, mock_l2_cache
):
    """测试删除同时清除L1和L2"""
    mock_l1_cache.delete.return_value = True
    mock_l2_cache.invalidate.return_value = True

    success = await cache_manager.delete(
        "test query",
        symbol="BTC",
        data_type=DataType.PRICE
    )

    assert success is True
    mock_l1_cache.delete.assert_called_once()
    mock_l2_cache.invalidate.assert_called_once()


@pytest.mark.asyncio
async def test_delete_succeeds_if_either_cache_deletes(
    cache_manager, mock_l1_cache, mock_l2_cache
):
    """测试至少一个缓存删除成功即为成功"""
    # L1成功，L2失败
    mock_l1_cache.delete.return_value = True
    mock_l2_cache.invalidate.return_value = False

    success = await cache_manager.delete("test query")
    assert success is True

    # L1失败，L2成功
    mock_l1_cache.delete.return_value = False
    mock_l2_cache.invalidate.return_value = True

    success = await cache_manager.delete("test query")
    assert success is True

    # 都失败
    mock_l1_cache.delete.return_value = False
    mock_l2_cache.invalidate.return_value = False

    success = await cache_manager.delete("test query")
    assert success is False


# ================================
# exists测试
# ================================


@pytest.mark.asyncio
async def test_exists_checks_l1_first(
    cache_manager, mock_l1_cache, mock_l2_cache
):
    """测试exists优先检查L1"""
    mock_l1_cache.exists.return_value = True

    exists = await cache_manager.exists("test query")

    assert exists is True
    mock_l1_cache.exists.assert_called_once()
    mock_l2_cache.exists.assert_not_called()  # L1存在，不检查L2


@pytest.mark.asyncio
async def test_exists_checks_l2_if_l1_miss(
    cache_manager, mock_l1_cache, mock_l2_cache
):
    """测试L1不存在时检查L2"""
    mock_l1_cache.exists.return_value = False
    mock_l2_cache.exists.return_value = True

    exists = await cache_manager.exists("test query")

    assert exists is True
    mock_l1_cache.exists.assert_called_once()
    mock_l2_cache.exists.assert_called_once()


# ================================
# 统计信息测试
# ================================


@pytest.mark.asyncio
async def test_get_stats_combines_l1_and_l2(
    cache_manager, mock_l1_cache, mock_l2_cache
):
    """测试合并L1和L2统计信息"""
    stats = await cache_manager.get_stats()

    assert "l1" in stats
    assert "l2" in stats
    assert "combined" in stats

    # 验证合并统计
    combined = stats["combined"]
    assert combined["total_hits"] == 60 + 800  # L1 + L2
    assert combined["total_misses"] == 40 + 200
    assert combined["total_requests"] == 900 + 200


@pytest.mark.asyncio
async def test_get_stats_calculates_combined_hit_rate(
    cache_manager, mock_l1_cache, mock_l2_cache
):
    """测试计算合并命中率"""
    stats = await cache_manager.get_stats()

    combined = stats["combined"]
    expected_hit_rate = (60 + 800) / (60 + 40 + 800 + 200)
    assert combined["hit_rate"] == pytest.approx(expected_hit_rate, rel=0.01)


# ================================
# 辅助方法测试
# ================================


@pytest.mark.asyncio
async def test_clear_l1(cache_manager, mock_l1_cache):
    """测试清空L1缓存"""
    await cache_manager.clear_l1()
    mock_l1_cache.clear.assert_called_once()


@pytest.mark.asyncio
async def test_get_l1_keys(cache_manager, mock_l1_cache):
    """测试获取L1缓存键"""
    mock_l1_cache.get_all_keys.return_value = ["key1", "key2", "key3"]

    keys = await cache_manager.get_l1_keys()
    assert keys == ["key1", "key2", "key3"]


@pytest.mark.asyncio
async def test_get_l1_size(cache_manager, mock_l1_cache):
    """测试获取L1缓存大小"""
    mock_l1_cache.get_size.return_value = 42

    size = await cache_manager.get_l1_size()
    assert size == 42


# ================================
# 单例模式测试
# ================================


def test_get_cache_manager_singleton():
    """测试单例模式返回同一实例"""
    manager1 = get_cache_manager()
    manager2 = get_cache_manager()

    assert manager1 is manager2


# ================================
# 便捷函数测试
# ================================


@pytest.mark.asyncio
@patch('app.core.cache_manager.get_cache_manager')
async def test_get_cached_query_convenience_function(mock_get_manager):
    """测试get_cached_query便捷函数"""
    mock_manager = AsyncMock()
    mock_manager.get.return_value = {"result": "test"}
    mock_get_manager.return_value = mock_manager

    result = await get_cached_query("test query", symbol="BTC")

    assert result == {"result": "test"}
    mock_manager.get.assert_called_once()


@pytest.mark.asyncio
@patch('app.core.cache_manager.get_cache_manager')
async def test_set_cached_query_convenience_function(mock_get_manager):
    """测试set_cached_query便捷函数"""
    mock_manager = AsyncMock()
    mock_manager.set.return_value = True
    mock_get_manager.return_value = mock_manager

    data = {"result": "test"}
    success = await set_cached_query("test query", data, symbol="BTC")

    assert success is True
    mock_manager.set.assert_called_once()


@pytest.mark.asyncio
@patch('app.core.cache_manager.get_cache_manager')
async def test_invalidate_cached_query_convenience_function(mock_get_manager):
    """测试invalidate_cached_query便捷函数"""
    mock_manager = AsyncMock()
    mock_manager.delete.return_value = True
    mock_get_manager.return_value = mock_manager

    success = await invalidate_cached_query("test query", symbol="BTC")

    assert success is True
    mock_manager.delete.assert_called_once()


@pytest.mark.asyncio
@patch('app.core.cache_manager.get_cache_manager')
async def test_get_cache_stats_convenience_function(mock_get_manager):
    """测试get_cache_stats便捷函数"""
    mock_manager = AsyncMock()
    mock_manager.get_stats.return_value = {"test": "stats"}
    mock_get_manager.return_value = mock_manager

    stats = await get_cache_stats()

    assert stats == {"test": "stats"}
    mock_manager.get_stats.assert_called_once()
