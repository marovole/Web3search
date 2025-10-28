"""
启动预加载器单元测试 (Stage 4 任务 4.7)

测试覆盖：
- 启动预加载流程
- 并发控制（验证最多5个并发）
- 超时处理（30秒超时）
- 失败不影响启动
- 空列表处理
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.startup_preloader import (
    StartupPreloader,
    get_preloader,
    run_startup_preloading
)
from app.services.cache_prewarming import PrewarmingPriority


# ================================
# Fixtures
# ================================

@pytest.fixture
def preloader():
    """创建预加载器实例"""
    return StartupPreloader()


@pytest.fixture
def mock_scheduler():
    """Mock调度器"""
    scheduler = AsyncMock()
    scheduler.get_priority_list = AsyncMock(return_value=[
        "bitcoin", "ethereum", "solana", "cardano", "polkadot",
        "avalanche", "polygon", "chainlink", "uniswap", "litecoin"
    ])
    return scheduler


@pytest.fixture
def mock_prewarming_manager():
    """Mock预热管理器"""
    manager = AsyncMock()
    manager.add_task = AsyncMock(return_value=True)
    return manager


# ================================
# 启动预加载流程测试
# ================================

@pytest.mark.asyncio
async def test_run_startup_preloading_success(mock_scheduler, mock_prewarming_manager):
    """测试：成功的启动预加载"""
    with patch('app.services.startup_preloader.get_scheduler', return_value=mock_scheduler), \
         patch('app.services.startup_preloader.get_prewarming_manager', return_value=mock_prewarming_manager):

        # 在patch之后创建preloader
        preloader = StartupPreloader()
        stats = await preloader.run()

        assert stats["coins_prewarmed"] == 10
        assert stats["coins_failed"] == 0
        assert stats["timed_out"] is False
        assert stats["started_at"] is not None
        assert stats["completed_at"] is not None
        assert stats["duration_seconds"] >= 0  # Mock任务可能很快，接受0


@pytest.mark.asyncio
async def test_run_startup_preloading_partial_failure(mock_scheduler):
    """测试：部分币种预热失败"""
    # Mock管理器：前5个成功，后5个失败
    manager = AsyncMock()
    manager.add_task = AsyncMock(side_effect=[
        True, True, True, True, True,
        False, False, False, False, False
    ])

    with patch('app.services.startup_preloader.get_scheduler', return_value=mock_scheduler), \
         patch('app.services.startup_preloader.get_prewarming_manager', return_value=manager):

        preloader = StartupPreloader()
        stats = await preloader.run()

        assert stats["coins_prewarmed"] == 5
        assert stats["coins_failed"] == 5
        assert stats["timed_out"] is False


@pytest.mark.asyncio
async def test_run_startup_preloading_empty_list(preloader):
    """测试：空币种列表"""
    scheduler = AsyncMock()
    scheduler.get_priority_list = AsyncMock(return_value=[])

    with patch('app.services.startup_preloader.get_scheduler', return_value=scheduler):
        stats = await preloader.run()

        assert stats["coins_prewarmed"] == 0
        assert stats["coins_failed"] == 0


# ================================
# 并发控制测试
# ================================

@pytest.mark.asyncio
async def test_concurrent_prewarming_control(preloader, mock_scheduler):
    """测试：并发控制（最多5个并发）"""
    # 记录并发执行的任务数
    active_tasks = []
    max_concurrent = 0

    async def mock_add_task(*args, **kwargs):
        # 记录当前活跃任务数
        active_tasks.append(1)
        current_concurrent = len(active_tasks)
        nonlocal max_concurrent
        max_concurrent = max(max_concurrent, current_concurrent)

        # 模拟延迟
        await asyncio.sleep(0.01)

        active_tasks.pop()
        return True

    manager = AsyncMock()
    manager.add_task = mock_add_task

    with patch('app.services.startup_preloader.get_scheduler', return_value=mock_scheduler), \
         patch.object(preloader, 'prewarming_manager', manager):

        await preloader.run()

        # 验证最多5个并发
        assert max_concurrent <= 5


# ================================
# 超时处理测试
# ================================

@pytest.mark.asyncio
async def test_run_startup_preloading_timeout(mock_scheduler):
    """测试：预加载超时（30秒）"""
    # Mock一个永不返回的任务
    async def never_returns(*args, **kwargs):
        await asyncio.sleep(100)  # 模拟永不返回
        return True

    manager = AsyncMock()
    manager.add_task = never_returns

    with patch('app.services.startup_preloader.get_scheduler', return_value=mock_scheduler), \
         patch('app.services.startup_preloader.get_prewarming_manager', return_value=manager):

        preloader = StartupPreloader()
        # 临时设置超时为0.1秒（加速测试）
        preloader.TIMEOUT_SECONDS = 0.1

        stats = await preloader.run()

        assert stats["timed_out"] is True
        assert stats["completed_at"] is not None


# ================================
# 异常处理测试
# ================================

@pytest.mark.asyncio
async def test_run_startup_preloading_exception_does_not_block(preloader, mock_scheduler):
    """测试：异常不阻塞启动"""
    # Mock调度器抛出异常
    scheduler = AsyncMock()
    scheduler.get_priority_list = AsyncMock(side_effect=Exception("Test error"))

    with patch('app.services.startup_preloader.get_scheduler', return_value=scheduler):
        stats = await preloader.run()

        # 应该返回统计信息，而不是抛出异常
        assert stats is not None
        assert stats["completed_at"] is not None


@pytest.mark.asyncio
async def test_prewarm_single_coin_exception(preloader):
    """测试：单个币种预热异常"""
    manager = AsyncMock()
    manager.add_task = AsyncMock(side_effect=Exception("Test error"))

    semaphore = asyncio.Semaphore(5)

    with patch.object(preloader, 'prewarming_manager', manager):
        result = await preloader._prewarm_single_coin("bitcoin", semaphore)

        assert result is False


# ================================
# 统计信息测试
# ================================

def test_get_stats(preloader):
    """测试：获取统计信息"""
    stats = preloader.get_stats()

    assert "started_at" in stats
    assert "completed_at" in stats
    assert "coins_prewarmed" in stats
    assert "coins_failed" in stats
    assert "duration_seconds" in stats
    assert "timed_out" in stats


# ================================
# 单例模式测试
# ================================

def test_get_preloader_singleton():
    """测试：单例模式"""
    preloader1 = get_preloader()
    preloader2 = get_preloader()

    assert preloader1 is preloader2


# ================================
# 便捷函数测试
# ================================

@pytest.mark.asyncio
async def test_run_startup_preloading_convenience_function(mock_scheduler, mock_prewarming_manager):
    """测试：便捷函数"""
    with patch('app.services.startup_preloader.get_scheduler', return_value=mock_scheduler), \
         patch('app.services.startup_preloader.get_prewarming_manager', return_value=mock_prewarming_manager):

        stats = await run_startup_preloading()

        assert stats is not None
        assert "coins_prewarmed" in stats


# ================================
# 边界条件测试
# ================================

@pytest.mark.asyncio
async def test_preload_with_large_coin_list():
    """测试：大量币种列表"""
    # 生成100个币种
    large_list = [f"coin_{i}" for i in range(100)]

    scheduler = AsyncMock()
    scheduler.get_priority_list = AsyncMock(return_value=large_list)

    manager = AsyncMock()
    manager.add_task = AsyncMock(return_value=True)

    with patch('app.services.startup_preloader.get_scheduler', return_value=scheduler), \
         patch('app.services.startup_preloader.get_prewarming_manager', return_value=manager):

        preloader = StartupPreloader()
        stats = await preloader.run()

        assert stats["coins_prewarmed"] == 100
        assert stats["coins_failed"] == 0


@pytest.mark.asyncio
async def test_preload_with_single_coin():
    """测试：单个币种"""
    scheduler = AsyncMock()
    scheduler.get_priority_list = AsyncMock(return_value=["bitcoin"])

    manager = AsyncMock()
    manager.add_task = AsyncMock(return_value=True)

    with patch('app.services.startup_preloader.get_scheduler', return_value=scheduler), \
         patch('app.services.startup_preloader.get_prewarming_manager', return_value=manager):

        preloader = StartupPreloader()
        stats = await preloader.run()

        assert stats["coins_prewarmed"] == 1
        assert stats["coins_failed"] == 0
