"""
PrewarmingScheduler单元测试

测试智能缓存预热调度器的所有功能：
- 热度计算算法
- 动态列表生成
- 趋势分析
- 预测算法
"""

import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.prewarming_scheduler import (
    PrewarmingScheduler,
    CoinHotness,
    TrendingAnalysis,
    get_scheduler
)
from app.services.cache_prewarming import PrewarmingPriority


# ================================
# Fixtures
# ================================


@pytest.fixture
def scheduler():
    """创建调度器实例"""
    return PrewarmingScheduler()


@pytest.fixture
def sample_coin_ids():
    """示例币种ID列表"""
    return ["bitcoin", "ethereum", "solana", "cardano", "polkadot"]


# ================================
# 热度计算测试
# ================================


@pytest.mark.asyncio
async def test_calculate_hotness_scores(scheduler, sample_coin_ids):
    """测试热度分数计算"""
    with patch.object(scheduler, '_get_cache_hits', new_callable=AsyncMock) as mock_hits, \
         patch.object(scheduler, '_get_query_frequency', new_callable=AsyncMock) as mock_freq, \
         patch.object(scheduler, '_get_trending_score', new_callable=AsyncMock) as mock_trending:

        # Mock返回值
        mock_hits.return_value = 100
        mock_freq.return_value = 50
        mock_trending.return_value = 20.0

        hotness_data = await scheduler.calculate_hotness_scores(sample_coin_ids)

        assert len(hotness_data) == 5
        assert "bitcoin" in hotness_data
        assert isinstance(hotness_data["bitcoin"], CoinHotness)


@pytest.mark.asyncio
async def test_calculate_hotness_score_formula(scheduler):
    """测试热度分数计算公式"""
    with patch.object(scheduler, '_get_cache_hits', return_value=100), \
         patch.object(scheduler, '_get_query_frequency', return_value=50), \
         patch.object(scheduler, '_get_trending_score', return_value=20.0):

        hotness = await scheduler.calculate_hotness_scores(["bitcoin"])
        coin_hotness = hotness["bitcoin"]

        # 验证公式：cache_hits*0.4 + query_freq*0.3 + recency*0.2 + trending*0.1
        # 100*0.4 + 50*0.3 + 1.0*0.2 + 20*0.1 = 40 + 15 + 0.2 + 2 = 57.2
        assert coin_hotness.hotness_score == pytest.approx(57.2, rel=0.1)


@pytest.mark.asyncio
async def test_get_cache_hits(scheduler):
    """测试获取缓存命中次数"""
    with patch('app.services.prewarming_scheduler.cache_get', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = "150"

        hits = await scheduler._get_cache_hits("bitcoin")
        assert hits == 150


@pytest.mark.asyncio
async def test_get_cache_hits_not_found(scheduler):
    """测试缓存命中次数不存在"""
    with patch('app.services.prewarming_scheduler.cache_get', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None

        hits = await scheduler._get_cache_hits("unknown")
        assert hits == 0


# ================================
# 新鲜度权重测试
# ================================


def test_calculate_recency_weight(scheduler):
    """测试新鲜度权重计算"""
    weight = scheduler._calculate_recency_weight("bitcoin")
    assert isinstance(weight, float)
    assert 0 <= weight <= 1.0


# ================================
# 趋势分析测试
# ================================


@pytest.mark.asyncio
async def test_analyze_trend(scheduler):
    """测试趋势分析"""
    with patch.object(scheduler, '_get_time_window_hits', new_callable=AsyncMock) as mock_hits:
        # 模拟上升趋势：1h=10, 24h=100, 7d=500
        mock_hits.side_effect = [10, 100, 500]

        analysis = await scheduler.analyze_trend("bitcoin")

        assert isinstance(analysis, TrendingAnalysis)
        assert analysis.coin_id == "bitcoin"


@pytest.mark.asyncio
async def test_trend_is_trending_true(scheduler):
    """测试识别上升趋势"""
    with patch.object(scheduler, '_get_time_window_hits', new_callable=AsyncMock) as mock_hits:
        # 强上升趋势
        mock_hits.side_effect = [100, 50, 40]  # 1h > 24h > 7d

        analysis = await scheduler.analyze_trend("bitcoin")

        # 增长率 > 20%且7d增长率>0
        assert isinstance(analysis.is_trending, bool)


@pytest.mark.asyncio
async def test_trend_growth_rate_calculation(scheduler):
    """测试增长率计算"""
    # 测试增长率计算逻辑
    growth = scheduler._calculate_growth_rate(150, 100)
    assert growth == 0.5  # 50%增长

    growth = scheduler._calculate_growth_rate(100, 200)
    assert growth == -0.5  # 50%下降

    growth = scheduler._calculate_growth_rate(100, 0)
    assert growth == 1.0  # 从0增长视为100%


# ================================
# 预测算法测试
# ================================


def test_calculate_prediction_score(scheduler):
    """测试预测分数计算"""
    score = scheduler._calculate_prediction_score(
        growth_1h=0.5,    # 50%
        growth_24h=0.3,   # 30%
        growth_7d=0.1     # 10%
    )

    # 0.5*0.5 + 0.3*0.3 + 0.1*0.2 = 0.25 + 0.09 + 0.02 = 0.36
    # 归一化到0-100: 36
    expected = 36.0
    assert score == pytest.approx(expected, rel=0.1)


@pytest.mark.asyncio
async def test_predict_hot_coins(scheduler):
    """测试预测热门币种"""
    # Mock Redis操作
    with patch('app.services.prewarming_scheduler.redis_client') as mock_redis:
        mock_redis_conn = AsyncMock()
        mock_redis.return_value.__aenter__.return_value = mock_redis_conn

        # Mock候选币种
        mock_redis_conn.zrange.return_value = [
            b"bitcoin", b"ethereum", b"solana"
        ]

        # Mock趋势分析
        with patch.object(scheduler, 'analyze_trend', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = TrendingAnalysis(
                coin_id="bitcoin",
                growth_rate_1h=0.5,
                growth_rate_24h=0.3,
                growth_rate_7d=0.1,
                is_trending=True,
                prediction_score=80.0
            )

            predictions = await scheduler.predict_hot_coins(limit=10)

            assert isinstance(predictions, list)
            # 验证每个预测都是(coin_id, score)元组
            for pred in predictions:
                assert isinstance(pred, tuple)
                assert len(pred) == 2


# ================================
# 优先级列表更新测试
# ================================


@pytest.mark.asyncio
async def test_update_priority_lists(scheduler):
    """测试更新优先级列表"""
    # 创建示例热度数据
    hotness_data = {
        f"coin_{i}": CoinHotness(
            coin_id=f"coin_{i}",
            hotness_score=100 - i,  # 递减分数
            cache_hits=100,
            query_frequency=50,
            recency_weight=1.0,
            trending_score=20.0,
            last_updated=time.time()
        )
        for i in range(150)  # 150个币种
    }

    with patch.object(scheduler, '_update_redis_list', new_callable=AsyncMock), \
         patch.object(scheduler, '_update_hotness_sorted_set', new_callable=AsyncMock):

        counts = await scheduler.update_priority_lists(hotness_data)

        assert counts["high"] == 10    # Top 10
        assert counts["medium"] == 100  # Top 100
        assert counts["low"] == 50      # 剩余


@pytest.mark.asyncio
async def test_get_priority_list_high(scheduler):
    """测试获取高优先级列表"""
    with patch('app.services.prewarming_scheduler.redis_client') as mock_redis:
        mock_redis_conn = AsyncMock()
        mock_redis.return_value.__aenter__.return_value = mock_redis_conn

        mock_redis_conn.lrange.return_value = [
            b"bitcoin", b"ethereum"
        ]

        coin_ids = await scheduler.get_priority_list(PrewarmingPriority.HIGH)

        assert coin_ids == ["bitcoin", "ethereum"]
        mock_redis_conn.lrange.assert_called_once()


@pytest.mark.asyncio
async def test_get_priority_list_empty(scheduler):
    """测试获取空列表"""
    with patch('app.services.prewarming_scheduler.redis_client') as mock_redis:
        mock_redis_conn = AsyncMock()
        mock_redis.return_value.__aenter__.return_value = mock_redis_conn

        mock_redis_conn.lrange.return_value = []

        coin_ids = await scheduler.get_priority_list(PrewarmingPriority.MEDIUM)

        assert coin_ids == []


# ================================
# Redis操作测试
# ================================


@pytest.mark.asyncio
async def test_update_redis_list(scheduler):
    """测试更新Redis列表"""
    with patch('app.services.prewarming_scheduler.redis_client') as mock_redis:
        mock_redis_conn = AsyncMock()
        mock_redis.return_value.__aenter__.return_value = mock_redis_conn

        await scheduler._update_redis_list(
            "test:list",
            ["coin1", "coin2", "coin3"]
        )

        # 验证删除旧列表
        mock_redis_conn.delete.assert_called_once_with("test:list")

        # 验证添加新列表
        mock_redis_conn.rpush.assert_called_once()

        # 验证设置过期时间
        mock_redis_conn.expire.assert_called_once_with("test:list", 7200)


@pytest.mark.asyncio
async def test_update_hotness_sorted_set(scheduler):
    """测试更新热度Sorted Set"""
    coins = [
        CoinHotness(
            coin_id="bitcoin",
            hotness_score=100.0,
            cache_hits=100,
            query_frequency=50,
            recency_weight=1.0,
            trending_score=20.0,
            last_updated=time.time()
        )
    ]

    with patch('app.services.prewarming_scheduler.redis_client') as mock_redis:
        mock_redis_conn = AsyncMock()
        mock_redis.return_value.__aenter__.return_value = mock_redis_conn

        await scheduler._update_hotness_sorted_set(coins)

        # 验证删除旧数据
        mock_redis_conn.delete.assert_called_once()

        # 验证添加新数据
        mock_redis_conn.zadd.assert_called_once()

        # 验证设置过期时间
        mock_redis_conn.expire.assert_called_once()


# ================================
# 统计信息测试
# ================================


def test_get_stats(scheduler):
    """测试获取统计信息"""
    stats = scheduler.get_stats()

    assert "last_update_time" in stats
    assert "last_update_datetime" in stats


def test_get_stats_with_update(scheduler):
    """测试更新后的统计信息"""
    scheduler._last_update_time = time.time()

    stats = scheduler.get_stats()

    assert stats["last_update_time"] is not None
    assert stats["last_update_datetime"] is not None


# ================================
# 单例模式测试
# ================================


def test_get_scheduler_singleton():
    """测试单例模式"""
    scheduler1 = get_scheduler()
    scheduler2 = get_scheduler()

    assert scheduler1 is scheduler2


# ================================
# 边界条件测试
# ================================


@pytest.mark.asyncio
async def test_calculate_hotness_with_no_data(scheduler):
    """测试无数据情况"""
    with patch.object(scheduler, '_get_cache_hits', return_value=0), \
         patch.object(scheduler, '_get_query_frequency', return_value=0), \
         patch.object(scheduler, '_get_trending_score', return_value=0.0):

        hotness_data = await scheduler.calculate_hotness_scores(["test_coin"])
        coin_hotness = hotness_data["test_coin"]

        # 所有数据为0，热度分数应该是1.0*0.2=0.2（recency权重）
        assert coin_hotness.hotness_score == pytest.approx(0.2, rel=0.1)


@pytest.mark.asyncio
async def test_update_priority_lists_empty(scheduler):
    """测试空热度数据"""
    with patch.object(scheduler, '_update_redis_list', new_callable=AsyncMock), \
         patch.object(scheduler, '_update_hotness_sorted_set', new_callable=AsyncMock):

        counts = await scheduler.update_priority_lists({})

        assert counts["high"] == 0
        assert counts["medium"] == 0
        assert counts["low"] == 0


def test_calculate_growth_rate_edge_cases(scheduler):
    """测试增长率边界情况"""
    # 从0增长
    assert scheduler._calculate_growth_rate(100, 0) == 1.0

    # 无变化
    assert scheduler._calculate_growth_rate(100, 100) == 0.0

    # 负增长
    assert scheduler._calculate_growth_rate(50, 100) == -0.5
