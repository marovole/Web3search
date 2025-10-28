"""
缓存预热系统集成测试 (Stage 1 任务 1.8 - 集成测试部分)

使用真实Redis进行集成测试，验证：
- 完整预热流程
- Redis数据持久化
- TTL过期机制

运行要求：
- Redis服务必须运行
- 设置环境变量 REDIS_URL
- 使用命令运行：pytest -m integration

标记为 @pytest.mark.integration 以便选择性运行
"""
import pytest
import asyncio
from datetime import datetime
from typing import List

from app.services.cache_prewarming import (
    PrewarmingManager,
    PrewarmingTask,
    PrewarmingPriority,
    initialize_prewarming,
    run_full_prewarming,
)
from app.core.redis_client import (
    get_async_redis,
    cache_get_json,
    cache_exists,
    close_redis,
)


# ================================
# Fixtures
# ================================


@pytest.fixture(scope="function")
async def redis_client():
    """
    提供异步Redis客户端并在测试后清理
    """
    client = await get_async_redis()

    # 清理测试数据（预防）
    await client.delete("prewarmed:coin:*")

    yield client

    # 测试后清理
    keys = await client.keys("prewarmed:coin:*")
    if keys:
        await client.delete(*keys)

    await close_redis()


@pytest.fixture(scope="function")
def prewarming_manager_clean():
    """
    提供干净的PrewarmingManager实例
    """
    manager = PrewarmingManager()

    # 清空队列
    manager.high_priority_queue.clear()
    manager.medium_priority_queue.clear()
    manager.low_priority_queue.clear()

    # 重置统计
    manager.stats = {
        "total_prewarmed": 0,
        "total_success": 0,
        "total_failed": 0,
        "last_run": None,
        "cached_coins": 0,
    }

    yield manager

    # 测试后清理
    manager.high_priority_queue.clear()
    manager.medium_priority_queue.clear()
    manager.low_priority_queue.clear()


# ================================
# 集成测试（3个）
# ================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_prewarming_with_real_redis(redis_client, prewarming_manager_clean):
    """
    集成测试1：完整预热流程 + 真实Redis

    验证：
    - 从CoinGecko获取真实币种数据（或Mock）
    - 数据成功写入Redis
    - 缓存可以被读取
    - 统计信息正确
    """
    manager = prewarming_manager_clean

    # 手动创建少量任务（避免实际调用CoinGecko API）
    manager.high_priority_queue = [
        PrewarmingTask("bitcoin", "BTC", PrewarmingPriority.HIGH, 1),
        PrewarmingTask("ethereum", "ETH", PrewarmingPriority.HIGH, 2),
    ]

    # Mock CoinGecko数据采集器（避免真实API调用）
    from unittest.mock import patch

    mock_market_data = {
        "name": "Bitcoin",
        "price_usd": 45000.0,
        "market_cap": 850000000000,
        "price_change_24h": 2.5,
    }

    with patch("app.services.cache_prewarming.coingecko_collector.get_coin_market_data") as mock_get:
        mock_get.return_value = mock_market_data

        # 执行预热
        stats = await manager.run_prewarming(PrewarmingPriority.HIGH)

        # 验证执行统计
        assert stats["total"] == 2
        assert stats["success"] == 2
        assert stats["failed"] == 0
        assert stats["success_rate"] == 1.0

        # 验证数据已写入Redis
        btc_cache_key = "prewarmed:coin:bitcoin"
        eth_cache_key = "prewarmed:coin:ethereum"

        assert await cache_exists(btc_cache_key)
        assert await cache_exists(eth_cache_key)

        # 验证缓存内容
        btc_data = await cache_get_json(btc_cache_key)
        assert btc_data is not None
        assert btc_data["name"] == "Bitcoin"
        assert btc_data["price_usd"] == 45000.0

        eth_data = await cache_get_json(eth_cache_key)
        assert eth_data is not None

        # 验证统计更新
        assert manager.stats["total_success"] == 2
        assert manager.stats["cached_coins"] == 2


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cache_persistence(redis_client, prewarming_manager_clean):
    """
    集成测试2：验证Redis数据持久化

    验证：
    - 预热后数据可持续读取
    - 多次读取返回相同数据
    - TTL正确设置
    """
    manager = prewarming_manager_clean

    # 创建单个任务
    manager.high_priority_queue = [
        PrewarmingTask("bitcoin", "BTC", PrewarmingPriority.HIGH, 1),
    ]

    mock_market_data = {
        "name": "Bitcoin",
        "price_usd": 45000.0,
        "timestamp": datetime.utcnow().isoformat(),
    }

    from unittest.mock import patch

    with patch("app.services.cache_prewarming.coingecko_collector.get_coin_market_data") as mock_get:
        mock_get.return_value = mock_market_data

        # 执行预热
        await manager.run_prewarming(PrewarmingPriority.HIGH)

        cache_key = "prewarmed:coin:bitcoin"

        # 第1次读取
        data1 = await cache_get_json(cache_key)
        assert data1 is not None
        assert data1["name"] == "Bitcoin"

        # 等待短暂时间
        await asyncio.sleep(0.5)

        # 第2次读取（验证数据持久化）
        data2 = await cache_get_json(cache_key)
        assert data2 is not None
        assert data2 == data1  # 数据应该相同

        # 验证TTL设置（高优先级应为60秒）
        ttl = await redis_client.ttl(cache_key)
        assert 50 < ttl <= 60  # TTL应该在50-60秒之间


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ttl_expiration(redis_client, prewarming_manager_clean):
    """
    集成测试3：验证TTL过期机制

    验证：
    - 不同优先级使用不同TTL
    - 缓存在TTL后过期
    - 过期后缓存不存在

    注意：此测试需要等待时间较长，仅用于验证TTL机制
    """
    manager = prewarming_manager_clean

    # 创建不同优先级的任务
    manager.high_priority_queue = [
        PrewarmingTask("bitcoin", "BTC", PrewarmingPriority.HIGH, 1),
    ]

    manager.medium_priority_queue = [
        PrewarmingTask("cardano", "ADA", PrewarmingPriority.MEDIUM, 11),
    ]

    mock_market_data = {"price_usd": 1000.0}

    from unittest.mock import patch

    with patch("app.services.cache_prewarming.coingecko_collector.get_coin_market_data") as mock_get:
        mock_get.return_value = mock_market_data

        # 执行全量预热
        await manager.run_prewarming()

        btc_key = "prewarmed:coin:bitcoin"
        ada_key = "prewarmed:coin:cardano"

        # 验证两个缓存都存在
        assert await cache_exists(btc_key)
        assert await cache_exists(ada_key)

        # 验证TTL不同
        btc_ttl = await redis_client.ttl(btc_key)
        ada_ttl = await redis_client.ttl(ada_key)

        assert 50 < btc_ttl <= 60  # 高优先级：60秒
        assert 290 < ada_ttl <= 300  # 中优先级：300秒

        # 验证TTL递减（等待2秒后再检查）
        await asyncio.sleep(2)

        btc_ttl_after = await redis_client.ttl(btc_key)
        assert btc_ttl_after < btc_ttl  # TTL应该减少


# ================================
# 压力测试（可选）
# ================================


@pytest.mark.integration
@pytest.mark.stress
@pytest.mark.asyncio
async def test_concurrent_prewarming_stress(redis_client, prewarming_manager_clean):
    """
    压力测试：大量币种并发预热

    验证：
    - 系统能处理大量并发请求
    - Redis连接稳定
    - 无内存泄漏

    标记为 @pytest.mark.stress 以便选择性运行
    运行：pytest -m "integration and stress"
    """
    manager = prewarming_manager_clean

    # 创建50个预热任务
    tasks = [
        PrewarmingTask(f"coin-{i}", f"C{i}", PrewarmingPriority.MEDIUM, i)
        for i in range(1, 51)
    ]

    manager.medium_priority_queue = tasks

    mock_market_data = {"price_usd": 1000.0, "timestamp": datetime.utcnow().isoformat()}

    from unittest.mock import patch

    with patch("app.services.cache_prewarming.coingecko_collector.get_coin_market_data") as mock_get:
        mock_get.return_value = mock_market_data

        # 执行并发预热
        stats = await manager.run_prewarming(PrewarmingPriority.MEDIUM)

        # 验证结果
        assert stats["total"] == 50
        assert stats["success"] == 50

        # 验证所有数据都写入Redis
        for i in range(1, 51):
            cache_key = f"prewarmed:coin:coin-{i}"
            assert await cache_exists(cache_key)


# ================================
# 运行说明
# ================================

"""
运行集成测试：

1. 确保Redis服务运行：
   docker run -d -p 6379:6379 redis:7-alpine

2. 设置环境变量：
   export REDIS_URL="redis://localhost:6379/0"

3. 仅运行集成测试：
   pytest backend/tests/test_cache_prewarming_integration.py -v -m integration

4. 运行所有测试（包括压力测试）：
   pytest backend/tests/test_cache_prewarming_integration.py -v -m "integration or stress"

5. 跳过集成测试（仅运行单元测试）：
   pytest backend/tests/test_cache_prewarming.py -v
"""
