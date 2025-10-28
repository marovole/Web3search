"""
缓存预热系统单元测试 (Stage 1 任务 1.8)

测试覆盖：
- 数据结构（PrewarmingTask, PrewarmingResult, Priority）
- PrewarmingManager单例模式
- Top 100币种列表获取
- 预热队列构建和优先级分配
- 单币种/批量预热功能
- 失败重试机制（指数退避）
- 完整预热流程
- 统计功能
"""
import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Dict, Any

from app.services.cache_prewarming import (
    PrewarmingManager,
    PrewarmingTask,
    PrewarmingResult,
    PrewarmingPriority,
    prewarming_manager,
    initialize_prewarming,
    run_top10_prewarming,
    run_top100_prewarming,
    run_full_prewarming,
    get_prewarming_stats,
)


# ================================
# 1. 数据结构测试（3个）
# ================================


def test_prewarming_priority_enum():
    """测试：PrewarmingPriority枚举值"""
    assert PrewarmingPriority.HIGH.value == "high"
    assert PrewarmingPriority.MEDIUM.value == "medium"
    assert PrewarmingPriority.LOW.value == "low"

    # 验证枚举成员数量
    assert len(PrewarmingPriority) == 3


def test_prewarming_task_creation():
    """测试：PrewarmingTask数据结构创建"""
    task = PrewarmingTask(
        coin_id="bitcoin",
        symbol="BTC",
        priority=PrewarmingPriority.HIGH,
        market_cap_rank=1,
    )

    assert task.coin_id == "bitcoin"
    assert task.symbol == "BTC"
    assert task.priority == PrewarmingPriority.HIGH
    assert task.market_cap_rank == 1
    assert task.retry_count == 0
    assert task.last_attempt is None


def test_prewarming_result_creation():
    """测试：PrewarmingResult数据结构创建"""
    task = PrewarmingTask(
        coin_id="ethereum",
        symbol="ETH",
        priority=PrewarmingPriority.MEDIUM,
        market_cap_rank=2,
    )

    result = PrewarmingResult(
        task=task,
        success=True,
        duration=1.23,
        cached_data_size=5000,
    )

    assert result.task == task
    assert result.success is True
    assert result.duration == 1.23
    assert result.error is None
    assert result.cached_data_size == 5000
    assert isinstance(result.timestamp, datetime)


# ================================
# 2. 单例模式测试（1个）
# ================================


def test_prewarming_manager_singleton():
    """测试：PrewarmingManager单例模式"""
    manager1 = PrewarmingManager()
    manager2 = PrewarmingManager()

    # 验证是同一个实例
    assert manager1 is manager2

    # 验证与全局实例相同
    assert manager1 is prewarming_manager


# ================================
# 3. Top币种获取测试（2个）
# ================================


@pytest.mark.asyncio
async def test_fetch_top_coins_success():
    """测试：成功获取Top 100币种列表"""
    manager = PrewarmingManager()

    # Mock CoinGecko API响应
    mock_coins_data = [
        {"id": "bitcoin", "symbol": "btc", "market_cap_rank": 1},
        {"id": "ethereum", "symbol": "eth", "market_cap_rank": 2},
        {"id": "binancecoin", "symbol": "bnb", "market_cap_rank": 3},
    ]

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_response = MagicMock()  # response本身不是async
        mock_response.json = MagicMock(return_value=mock_coins_data)  # json()是同步方法
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        # 执行获取
        top_coins = await manager.fetch_top_coins(limit=3)

        # 验证结果
        assert len(top_coins) == 3
        assert top_coins[0]["id"] == "bitcoin"
        assert top_coins[0]["symbol"] == "BTC"  # 应该转为大写
        assert top_coins[0]["market_cap_rank"] == 1

        assert top_coins[1]["id"] == "ethereum"
        assert top_coins[2]["id"] == "binancecoin"


@pytest.mark.asyncio
async def test_fetch_top_coins_api_error():
    """测试：API请求失败时的错误处理"""
    manager = PrewarmingManager()

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.side_effect = Exception("API connection failed")

        # 验证异常被正确抛出
        with pytest.raises(Exception) as exc_info:
            await manager.fetch_top_coins(limit=10)

        assert "API connection failed" in str(exc_info.value)


# ================================
# 4. 队列构建测试（2个）
# ================================


@pytest.mark.asyncio
async def test_build_prewarming_queues_priority_allocation():
    """测试：预热队列构建和优先级分配"""
    manager = PrewarmingManager()

    # Mock Top 100币种数据
    mock_coins = []
    for i in range(1, 101):
        mock_coins.append({
            "id": f"coin-{i}",
            "symbol": f"C{i}",
            "market_cap_rank": i,
        })

    with patch.object(manager, "fetch_top_coins", return_value=mock_coins):
        stats = await manager.build_prewarming_queues(limit=100)

        # 验证统计信息
        assert stats["high"] == 10  # Top 10 -> 高优先级
        assert stats["medium"] == 90  # Top 11-100 -> 中优先级
        assert stats["low"] == 0  # 无低优先级
        assert stats["total"] == 100

        # 验证队列内容
        assert len(manager.high_priority_queue) == 10
        assert len(manager.medium_priority_queue) == 90
        assert len(manager.low_priority_queue) == 0

        # 验证优先级分配正确
        assert all(
            task.priority == PrewarmingPriority.HIGH
            for task in manager.high_priority_queue
        )
        assert all(
            task.priority == PrewarmingPriority.MEDIUM
            for task in manager.medium_priority_queue
        )

        # 验证排名边界
        assert manager.high_priority_queue[0].market_cap_rank == 1
        assert manager.high_priority_queue[-1].market_cap_rank == 10
        assert manager.medium_priority_queue[0].market_cap_rank == 11
        assert manager.medium_priority_queue[-1].market_cap_rank == 100


@pytest.mark.asyncio
async def test_build_prewarming_queues_empty():
    """测试：空币种列表时的队列构建"""
    manager = PrewarmingManager()

    with patch.object(manager, "fetch_top_coins", return_value=[]):
        stats = await manager.build_prewarming_queues(limit=0)

        assert stats["high"] == 0
        assert stats["medium"] == 0
        assert stats["low"] == 0
        assert stats["total"] == 0


# ================================
# 5. 单币种预热测试（2个）
# ================================


@pytest.mark.asyncio
async def test_prewarm_single_coin_success():
    """测试：单币种预热成功"""
    manager = PrewarmingManager()

    task = PrewarmingTask(
        coin_id="bitcoin",
        symbol="BTC",
        priority=PrewarmingPriority.HIGH,
        market_cap_rank=1,
    )

    # Mock market data
    mock_market_data = {
        "name": "Bitcoin",
        "price_usd": 45000.0,
        "market_cap": 850000000000,
    }

    with patch("app.services.cache_prewarming.coingecko_collector.get_coin_market_data") as mock_get, \
         patch("app.services.cache_prewarming.cache_set") as mock_cache_set:

        mock_get.return_value = mock_market_data
        mock_cache_set.return_value = True

        # 执行预热
        result = await manager.prewarm_single_coin(task)

        # 验证结果
        assert result.success is True
        assert result.duration > 0
        assert result.error is None
        assert result.task == task

        # 验证cache_set被调用
        mock_cache_set.assert_called_once()
        call_args = mock_cache_set.call_args
        assert call_args[0][0] == "prewarmed:coin:bitcoin"  # cache_key
        assert call_args[0][1] == mock_market_data  # data
        assert call_args[0][2] == 60  # TTL for HIGH priority


@pytest.mark.asyncio
async def test_prewarm_single_coin_failure():
    """测试：单币种预热失败"""
    manager = PrewarmingManager()

    task = PrewarmingTask(
        coin_id="invalid-coin",
        symbol="INV",
        priority=PrewarmingPriority.LOW,
        market_cap_rank=999,
    )

    with patch("app.services.cache_prewarming.coingecko_collector.get_coin_market_data") as mock_get:
        mock_get.side_effect = Exception("Coin not found")

        # 执行预热
        result = await manager.prewarm_single_coin(task)

        # 验证失败结果
        assert result.success is False
        assert result.error == "Coin not found"
        assert result.task == task


# ================================
# 6. 批量预热测试（2个）
# ================================


@pytest.mark.asyncio
async def test_prewarm_batch_concurrent():
    """测试：批量并发预热"""
    manager = PrewarmingManager()

    tasks = [
        PrewarmingTask("bitcoin", "BTC", PrewarmingPriority.HIGH, 1),
        PrewarmingTask("ethereum", "ETH", PrewarmingPriority.HIGH, 2),
        PrewarmingTask("binancecoin", "BNB", PrewarmingPriority.HIGH, 3),
    ]

    mock_market_data = {"price_usd": 1000.0}

    with patch("app.services.cache_prewarming.coingecko_collector.get_coin_market_data") as mock_get, \
         patch("app.services.cache_prewarming.cache_set") as mock_cache_set:

        mock_get.return_value = mock_market_data
        mock_cache_set.return_value = True

        # 执行批量预热
        results = await manager.prewarm_batch(tasks, max_concurrent=2)

        # 验证所有任务都完成
        assert len(results) == 3
        assert all(result.success for result in results)

        # 验证并发调用（所有任务都应该被处理）
        assert mock_get.call_count == 3


@pytest.mark.asyncio
async def test_prewarm_batch_mixed_results():
    """测试：批量预热部分成功场景"""
    manager = PrewarmingManager()

    tasks = [
        PrewarmingTask("bitcoin", "BTC", PrewarmingPriority.HIGH, 1),
        PrewarmingTask("invalid", "INV", PrewarmingPriority.HIGH, 999),
        PrewarmingTask("ethereum", "ETH", PrewarmingPriority.HIGH, 2),
    ]

    async def mock_get_side_effect(coin_id):
        if coin_id == "invalid":
            raise Exception("Coin not found")
        return {"price_usd": 1000.0}

    with patch("app.services.cache_prewarming.coingecko_collector.get_coin_market_data") as mock_get, \
         patch("app.services.cache_prewarming.cache_set") as mock_cache_set:

        mock_get.side_effect = mock_get_side_effect
        mock_cache_set.return_value = True

        # 执行批量预热
        results = await manager.prewarm_batch(tasks, max_concurrent=3)

        # 验证结果
        assert len(results) == 3
        assert results[0].success is True  # bitcoin成功
        assert results[1].success is False  # invalid失败
        assert results[2].success is True  # ethereum成功

        # 验证失败原因
        assert "Coin not found" in results[1].error


# ================================
# 7. 重试机制测试（3个）
# ================================


@pytest.mark.asyncio
async def test_prewarm_with_retry_first_success():
    """测试：首次尝试即成功"""
    manager = PrewarmingManager()

    task = PrewarmingTask("bitcoin", "BTC", PrewarmingPriority.HIGH, 1)
    mock_market_data = {"price_usd": 45000.0}

    with patch("app.services.cache_prewarming.coingecko_collector.get_coin_market_data") as mock_get, \
         patch("app.services.cache_prewarming.cache_set") as mock_cache_set:

        mock_get.return_value = mock_market_data
        mock_cache_set.return_value = True

        # 执行带重试的预热
        result = await manager.prewarm_with_retry(task)

        # 验证首次成功
        assert result.success is True
        assert task.retry_count == 0
        assert mock_get.call_count == 1  # 只调用一次


@pytest.mark.asyncio
async def test_prewarm_with_retry_eventual_success():
    """测试：重试后成功"""
    manager = PrewarmingManager()

    task = PrewarmingTask("bitcoin", "BTC", PrewarmingPriority.HIGH, 1)
    mock_market_data = {"price_usd": 45000.0}

    call_count = 0

    async def mock_get_side_effect(coin_id):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise Exception("Temporary API error")
        return mock_market_data

    with patch("app.services.cache_prewarming.coingecko_collector.get_coin_market_data") as mock_get, \
         patch("app.services.cache_prewarming.cache_set") as mock_cache_set, \
         patch("asyncio.sleep", return_value=None):  # 跳过延迟

        mock_get.side_effect = mock_get_side_effect
        mock_cache_set.return_value = True

        # 执行带重试的预热
        result = await manager.prewarm_with_retry(task)

        # 验证第3次成功
        assert result.success is True
        assert mock_get.call_count == 3


@pytest.mark.asyncio
async def test_prewarm_with_retry_max_retries_exceeded():
    """测试：达到最大重试次数后失败"""
    manager = PrewarmingManager()

    task = PrewarmingTask("invalid", "INV", PrewarmingPriority.HIGH, 999)

    with patch("app.services.cache_prewarming.coingecko_collector.get_coin_market_data") as mock_get, \
         patch("asyncio.sleep", return_value=None):  # 跳过延迟

        mock_get.side_effect = Exception("Persistent API error")

        # 执行带重试的预热
        result = await manager.prewarm_with_retry(task)

        # 验证最终失败
        assert result.success is False
        assert "Persistent API error" in result.error
        assert mock_get.call_count == 3  # 重试3次


# ================================
# 8. 完整流程测试（2个）
# ================================


@pytest.mark.asyncio
async def test_run_prewarming_by_priority():
    """测试：按优先级执行预热"""
    manager = PrewarmingManager()

    # 设置高优先级队列
    manager.high_priority_queue = [
        PrewarmingTask("bitcoin", "BTC", PrewarmingPriority.HIGH, 1),
        PrewarmingTask("ethereum", "ETH", PrewarmingPriority.HIGH, 2),
    ]
    manager.medium_priority_queue = []
    manager.low_priority_queue = []

    mock_market_data = {"price_usd": 1000.0}

    with patch("app.services.cache_prewarming.coingecko_collector.get_coin_market_data") as mock_get, \
         patch("app.services.cache_prewarming.cache_set") as mock_cache_set:

        mock_get.return_value = mock_market_data
        mock_cache_set.return_value = True

        # 执行高优先级预热
        stats = await manager.run_prewarming(PrewarmingPriority.HIGH)

        # 验证统计信息
        assert stats["total"] == 2
        assert stats["success"] == 2
        assert stats["failed"] == 0
        assert stats["success_rate"] == 1.0
        assert stats["duration"] > 0


@pytest.mark.asyncio
async def test_run_prewarming_all_queues():
    """测试：全量预热（所有队列）"""
    manager = PrewarmingManager()

    # 设置所有队列
    manager.high_priority_queue = [
        PrewarmingTask("bitcoin", "BTC", PrewarmingPriority.HIGH, 1),
    ]
    manager.medium_priority_queue = [
        PrewarmingTask("cardano", "ADA", PrewarmingPriority.MEDIUM, 11),
    ]
    manager.low_priority_queue = [
        PrewarmingTask("longcoin", "LONG", PrewarmingPriority.LOW, 200),
    ]

    mock_market_data = {"price_usd": 1000.0}

    with patch("app.services.cache_prewarming.coingecko_collector.get_coin_market_data") as mock_get, \
         patch("app.services.cache_prewarming.cache_set") as mock_cache_set:

        mock_get.return_value = mock_market_data
        mock_cache_set.return_value = True

        # 执行全量预热（priority=None）
        stats = await manager.run_prewarming(priority=None)

        # 验证所有队列都被处理
        assert stats["total"] == 3
        assert stats["success"] == 3


# ================================
# 9. 统计功能测试（1个）
# ================================


def test_get_stats():
    """测试：获取预热统计信息"""
    manager = PrewarmingManager()

    # 设置队列状态
    manager.high_priority_queue = [MagicMock()] * 5
    manager.medium_priority_queue = [MagicMock()] * 20
    manager.low_priority_queue = [MagicMock()] * 10

    # 设置统计数据
    manager.stats = {
        "total_prewarmed": 100,
        "total_success": 95,
        "total_failed": 5,
        "last_run": "2025-10-28T12:00:00",
        "cached_coins": 95,
    }

    # 获取统计
    stats = manager.get_stats()

    # 验证统计信息
    assert stats["total_prewarmed"] == 100
    assert stats["total_success"] == 95
    assert stats["total_failed"] == 5
    assert stats["last_run"] == "2025-10-28T12:00:00"
    assert stats["cached_coins"] == 95

    # 验证队列大小
    assert stats["queue_sizes"]["high"] == 5
    assert stats["queue_sizes"]["medium"] == 20
    assert stats["queue_sizes"]["low"] == 10


# ================================
# 10. TTL策略测试（1个）
# ================================


def test_get_ttl_by_priority():
    """测试：根据优先级获取正确的TTL"""
    manager = PrewarmingManager()

    # 验证不同优先级的TTL
    assert manager._get_ttl_by_priority(PrewarmingPriority.HIGH) == 60  # 1分钟
    assert manager._get_ttl_by_priority(PrewarmingPriority.MEDIUM) == 300  # 5分钟
    assert manager._get_ttl_by_priority(PrewarmingPriority.LOW) == 900  # 15分钟


# ================================
# 11. 便捷函数测试（4个）
# ================================


@pytest.mark.asyncio
async def test_initialize_prewarming():
    """测试：初始化预热系统（便捷函数）"""
    mock_coins = [{"id": f"coin-{i}", "symbol": f"C{i}", "market_cap_rank": i} for i in range(1, 11)]

    with patch.object(prewarming_manager, "fetch_top_coins", return_value=mock_coins):
        stats = await initialize_prewarming(limit=10)

        assert stats["total"] == 10
        assert stats["high"] == 10  # All in top 10


@pytest.mark.asyncio
async def test_run_top10_prewarming():
    """测试：执行Top 10预热（便捷函数）"""
    prewarming_manager.high_priority_queue = [
        PrewarmingTask(f"coin-{i}", f"C{i}", PrewarmingPriority.HIGH, i) for i in range(1, 11)
    ]

    with patch("app.services.cache_prewarming.coingecko_collector.get_coin_market_data") as mock_get, \
         patch("app.services.cache_prewarming.cache_set") as mock_cache_set:

        mock_get.return_value = {"price_usd": 1000.0}
        mock_cache_set.return_value = True

        stats = await run_top10_prewarming()

        assert stats["total"] == 10


@pytest.mark.asyncio
async def test_run_top100_prewarming():
    """测试：执行Top 100预热（便捷函数）"""
    prewarming_manager.medium_priority_queue = [
        PrewarmingTask(f"coin-{i}", f"C{i}", PrewarmingPriority.MEDIUM, i) for i in range(11, 21)
    ]

    with patch("app.services.cache_prewarming.coingecko_collector.get_coin_market_data") as mock_get, \
         patch("app.services.cache_prewarming.cache_set") as mock_cache_set:

        mock_get.return_value = {"price_usd": 1000.0}
        mock_cache_set.return_value = True

        stats = await run_top100_prewarming()

        assert stats["total"] == 10  # 我们只添加了10个任务


def test_get_prewarming_stats():
    """测试：获取预热统计（便捷函数）"""
    prewarming_manager.stats = {
        "total_prewarmed": 50,
        "total_success": 48,
        "total_failed": 2,
    }

    stats = get_prewarming_stats()

    assert stats["total_prewarmed"] == 50
    assert stats["total_success"] == 48
    assert stats["total_failed"] == 2
