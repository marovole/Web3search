"""
智能缓存预热调度器

实现功能：
- 热度计算算法（基于缓存命中统计 + 查询频率）
- 动态预热列表生成（分高/中/低优先级）
- 时间窗口趋势分析（1小时、24小时、7天）
- 预测即将热门的币种

热度分数计算公式：
hotness_score = (
    cache_hit_count * 0.4 +           # 缓存命中次数
    query_frequency * 0.3 +            # 查询频率
    recency_weight * 0.2 +             # 最近访问权重
    trending_score * 0.1               # 趋势分数（增长率）
)
"""

import logging
import time
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict

from app.core.redis_client import (
    redis_client,
    cache_get,
    cache_set,
    cache_increment,
)
from app.services.cache_prewarming import PrewarmingPriority

logger = logging.getLogger(__name__)


# ================================
# 数据结构
# ================================


@dataclass
class CoinHotness:
    """币种热度数据"""

    coin_id: str
    hotness_score: float
    cache_hits: int
    query_frequency: int
    recency_weight: float
    trending_score: float
    last_updated: float


@dataclass
class TrendingAnalysis:
    """趋势分析结果"""

    coin_id: str
    growth_rate_1h: float    # 1小时增长率
    growth_rate_24h: float   # 24小时增长率
    growth_rate_7d: float    # 7天增长率
    is_trending: bool        # 是否处于上升趋势
    prediction_score: float  # 预测分数（未来热门可能性）


# ================================
# 预热调度器
# ================================


class PrewarmingScheduler:
    """
    智能缓存预热调度器

    职责：
    1. 收集和分析缓存访问统计
    2. 计算币种热度分数
    3. 生成动态预热列表
    4. 预测即将热门的币种
    """

    # Redis键前缀
    HOTNESS_KEY = "hotness:scores"              # Sorted Set: 热度分数
    CACHE_HITS_KEY_PREFIX = "cache_stats:hits"  # String: 缓存命中计数
    QUERY_FREQ_KEY_PREFIX = "query_freq"        # String: 查询频率
    TREND_DATA_KEY_PREFIX = "trend_data"        # Hash: 趋势数据

    # 预热列表键
    HIGH_PRIORITY_LIST = "prewarming:high_priority"    # Top 10
    MEDIUM_PRIORITY_LIST = "prewarming:medium_priority"  # Top 100
    LOW_PRIORITY_LIST = "prewarming:low_priority"      # 其他

    # 热度计算权重
    CACHE_HIT_WEIGHT = 0.4
    QUERY_FREQ_WEIGHT = 0.3
    RECENCY_WEIGHT = 0.2
    TRENDING_WEIGHT = 0.1

    # 趋势判断阈值
    TRENDING_THRESHOLD = 0.2  # 20%增长视为上升趋势

    def __init__(self):
        """初始化调度器"""
        self._last_update_time: Optional[float] = None
        logger.info("PrewarmingScheduler initialized")

    async def calculate_hotness_scores(
        self,
        coin_ids: List[str]
    ) -> Dict[str, CoinHotness]:
        """
        计算币种热度分数

        Args:
            coin_ids: 币种ID列表

        Returns:
            Dict[coin_id, CoinHotness]: 热度数据字典
        """
        logger.info(f"Calculating hotness scores for {len(coin_ids)} coins")

        hotness_data = {}

        for coin_id in coin_ids:
            # 1. 获取缓存命中次数
            cache_hits = await self._get_cache_hits(coin_id)

            # 2. 获取查询频率
            query_freq = await self._get_query_frequency(coin_id)

            # 3. 计算新鲜度权重
            recency = self._calculate_recency_weight(coin_id)

            # 4. 获取趋势分数
            trending_score = await self._get_trending_score(coin_id)

            # 5. 计算综合热度分数
            hotness_score = (
                cache_hits * self.CACHE_HIT_WEIGHT +
                query_freq * self.QUERY_FREQ_WEIGHT +
                recency * self.RECENCY_WEIGHT +
                trending_score * self.TRENDING_WEIGHT
            )

            hotness_data[coin_id] = CoinHotness(
                coin_id=coin_id,
                hotness_score=hotness_score,
                cache_hits=cache_hits,
                query_frequency=query_freq,
                recency_weight=recency,
                trending_score=trending_score,
                last_updated=time.time()
            )

        logger.info(f"Calculated hotness scores for {len(hotness_data)} coins")
        return hotness_data

    async def _get_cache_hits(self, coin_id: str) -> int:
        """获取缓存命中次数"""
        try:
            key = f"{self.CACHE_HITS_KEY_PREFIX}:{coin_id}"
            hits = await cache_get(key)
            return int(hits) if hits else 0
        except Exception as e:
            logger.error(f"Failed to get cache hits for {coin_id}: {e}")
            return 0

    async def _get_query_frequency(self, coin_id: str) -> int:
        """
        获取查询频率（最近1小时）

        注：这里简化实现，实际应该从时间序列数据中计算
        """
        try:
            key = f"{self.QUERY_FREQ_KEY_PREFIX}:1h:{coin_id}"
            freq = await cache_get(key)
            return int(freq) if freq else 0
        except Exception as e:
            logger.error(f"Failed to get query frequency for {coin_id}: {e}")
            return 0

    def _calculate_recency_weight(self, coin_id: str) -> float:
        """
        计算新鲜度权重

        最近访问的币种权重更高
        使用指数衰减：weight = e^(-age / half_life)
        """
        # 简化实现：假设所有币种的新鲜度相同
        # 实际应该从L1缓存或访问日志中获取最后访问时间
        return 1.0

    async def _get_trending_score(self, coin_id: str) -> float:
        """
        获取趋势分数

        基于24小时增长率计算
        """
        try:
            analysis = await self.analyze_trend(coin_id)
            if analysis.is_trending:
                # 归一化到0-100范围
                return min(abs(analysis.growth_rate_24h) * 100, 100)
            return 0.0
        except Exception as e:
            logger.error(f"Failed to get trending score for {coin_id}: {e}")
            return 0.0

    async def analyze_trend(self, coin_id: str) -> TrendingAnalysis:
        """
        分析币种趋势

        比较不同时间窗口的访问量/命中量变化

        Args:
            coin_id: 币种ID

        Returns:
            TrendingAnalysis: 趋势分析结果
        """
        # 获取不同时间窗口的数据
        hits_1h = await self._get_time_window_hits(coin_id, "1h")
        hits_24h = await self._get_time_window_hits(coin_id, "24h")
        hits_7d = await self._get_time_window_hits(coin_id, "7d")

        # 计算增长率
        growth_1h = self._calculate_growth_rate(hits_1h, hits_1h)
        growth_24h = self._calculate_growth_rate(hits_24h, hits_1h)
        growth_7d = self._calculate_growth_rate(hits_7d, hits_24h)

        # 判断是否上升趋势
        is_trending = (
            growth_24h > self.TRENDING_THRESHOLD and
            growth_7d > 0
        )

        # 计算预测分数
        prediction_score = self._calculate_prediction_score(
            growth_1h, growth_24h, growth_7d
        )

        return TrendingAnalysis(
            coin_id=coin_id,
            growth_rate_1h=growth_1h,
            growth_rate_24h=growth_24h,
            growth_rate_7d=growth_7d,
            is_trending=is_trending,
            prediction_score=prediction_score
        )

    async def _get_time_window_hits(
        self,
        coin_id: str,
        window: str
    ) -> int:
        """
        获取时间窗口内的命中次数

        Args:
            coin_id: 币种ID
            window: 时间窗口（1h/24h/7d）

        Returns:
            int: 命中次数
        """
        try:
            key = f"{self.TREND_DATA_KEY_PREFIX}:{window}:{coin_id}"
            hits = await cache_get(key)
            return int(hits) if hits else 0
        except Exception as e:
            logger.error(
                f"Failed to get {window} hits for {coin_id}: {e}"
            )
            return 0

    def _calculate_growth_rate(
        self,
        current: int,
        previous: int
    ) -> float:
        """
        计算增长率

        Args:
            current: 当前值
            previous: 之前值

        Returns:
            float: 增长率（-1.0 到 +∞）
        """
        if previous == 0:
            return 1.0 if current > 0 else 0.0

        return (current - previous) / previous

    def _calculate_prediction_score(
        self,
        growth_1h: float,
        growth_24h: float,
        growth_7d: float
    ) -> float:
        """
        计算预测分数（未来热门可能性）

        使用加权平均，近期增长率权重更高
        """
        score = (
            growth_1h * 0.5 +    # 最近1小时权重最高
            growth_24h * 0.3 +   # 24小时权重次之
            growth_7d * 0.2      # 7天权重最低
        )

        # 归一化到0-100
        return max(0, min(score * 100, 100))

    async def update_priority_lists(
        self,
        hotness_data: Dict[str, CoinHotness]
    ) -> Dict[str, int]:
        """
        更新优先级列表

        根据热度分数动态调整预热列表

        Args:
            hotness_data: 热度数据字典

        Returns:
            Dict[priority_level, count]: 各优先级币种数量
        """
        logger.info("Updating priority lists")

        # 按热度分数排序
        sorted_coins = sorted(
            hotness_data.values(),
            key=lambda x: x.hotness_score,
            reverse=True
        )

        # 分配优先级
        high_priority = [c.coin_id for c in sorted_coins[:10]]    # Top 10
        medium_priority = [c.coin_id for c in sorted_coins[:100]]  # Top 100
        low_priority = [c.coin_id for c in sorted_coins[100:]]    # 其他

        # 写入Redis
        await self._update_redis_list(
            self.HIGH_PRIORITY_LIST,
            high_priority
        )
        await self._update_redis_list(
            self.MEDIUM_PRIORITY_LIST,
            medium_priority
        )
        await self._update_redis_list(
            self.LOW_PRIORITY_LIST,
            low_priority
        )

        # 更新热度分数到Sorted Set
        await self._update_hotness_sorted_set(sorted_coins)

        self._last_update_time = time.time()

        logger.info(
            f"Priority lists updated: "
            f"high={len(high_priority)}, "
            f"medium={len(medium_priority)}, "
            f"low={len(low_priority)}"
        )

        return {
            "high": len(high_priority),
            "medium": len(medium_priority),
            "low": len(low_priority)
        }

    async def _update_redis_list(
        self,
        key: str,
        coin_ids: List[str]
    ) -> None:
        """更新Redis列表"""
        try:
            async with redis_client() as redis:
                # 删除旧列表
                await redis.delete(key)

                # 添加新列表
                if coin_ids:
                    await redis.rpush(key, *coin_ids)

                # 设置过期时间（2小时）
                await redis.expire(key, 7200)
        except Exception as e:
            logger.error(f"Failed to update Redis list {key}: {e}")

    async def _update_hotness_sorted_set(
        self,
        sorted_coins: List[CoinHotness]
    ) -> None:
        """更新热度分数Sorted Set"""
        try:
            async with redis_client() as redis:
                # 删除旧数据
                await redis.delete(self.HOTNESS_KEY)

                # 添加新数据
                if sorted_coins:
                    mapping = {
                        c.coin_id: c.hotness_score
                        for c in sorted_coins
                    }
                    await redis.zadd(self.HOTNESS_KEY, mapping)

                # 设置过期时间（2小时）
                await redis.expire(self.HOTNESS_KEY, 7200)
        except Exception as e:
            logger.error(f"Failed to update hotness sorted set: {e}")

    async def get_priority_list(
        self,
        priority: PrewarmingPriority
    ) -> List[str]:
        """
        获取指定优先级的预热列表

        Args:
            priority: 优先级

        Returns:
            List[str]: 币种ID列表
        """
        key_map = {
            PrewarmingPriority.HIGH: self.HIGH_PRIORITY_LIST,
            PrewarmingPriority.MEDIUM: self.MEDIUM_PRIORITY_LIST,
            PrewarmingPriority.LOW: self.LOW_PRIORITY_LIST
        }

        key = key_map.get(priority)
        if not key:
            logger.error(f"Invalid priority: {priority}")
            return []

        try:
            async with redis_client() as redis:
                coin_ids = await redis.lrange(key, 0, -1)
                return [cid.decode() if isinstance(cid, bytes) else cid
                        for cid in coin_ids]
        except Exception as e:
            logger.error(
                f"Failed to get priority list for {priority}: {e}"
            )
            return []

    async def predict_hot_coins(
        self,
        limit: int = 20
    ) -> List[Tuple[str, float]]:
        """
        预测即将热门的币种

        基于趋势分析和预测分数

        Args:
            limit: 返回数量限制

        Returns:
            List[Tuple[coin_id, prediction_score]]: 预测结果
        """
        logger.info(f"Predicting hot coins (limit={limit})")

        try:
            # 从热度Sorted Set获取候选币种
            async with redis_client() as redis:
                candidates = await redis.zrange(
                    self.HOTNESS_KEY,
                    0,
                    99,  # Top 100作为候选
                    withscores=False
                )

            if not candidates:
                logger.warning("No candidates for prediction")
                return []

            # 解码
            candidates = [
                c.decode() if isinstance(c, bytes) else c
                for c in candidates
            ]

            # 分析每个候选币种的趋势
            predictions = []
            for coin_id in candidates:
                analysis = await self.analyze_trend(coin_id)

                if analysis.is_trending:
                    predictions.append((
                        coin_id,
                        analysis.prediction_score
                    ))

            # 按预测分数排序
            predictions.sort(key=lambda x: x[1], reverse=True)

            result = predictions[:limit]
            logger.info(f"Predicted {len(result)} hot coins")
            return result

        except Exception as e:
            logger.error(f"Failed to predict hot coins: {e}", exc_info=True)
            return []

    def get_stats(self) -> Dict[str, any]:
        """
        获取调度器统计信息

        Returns:
            Dict: 统计信息
        """
        return {
            "last_update_time": self._last_update_time,
            "last_update_datetime": (
                datetime.fromtimestamp(self._last_update_time).isoformat()
                if self._last_update_time
                else None
            )
        }


# ================================
# 全局实例（单例）
# ================================

_scheduler_instance: Optional[PrewarmingScheduler] = None


def get_scheduler() -> PrewarmingScheduler:
    """
    获取全局调度器实例（单例模式）

    Returns:
        PrewarmingScheduler: 调度器实例
    """
    global _scheduler_instance

    if _scheduler_instance is None:
        _scheduler_instance = PrewarmingScheduler()
        logger.info("Global PrewarmingScheduler instance created")

    return _scheduler_instance
