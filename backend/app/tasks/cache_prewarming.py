"""
缓存预热Celery任务

定时执行缓存预热，包括：
1. prewarm_hot_coins - Top 10热门币种预热（每1分钟）
2. prewarm_trending_coins - Top 100趋势币种预热（每5分钟）
3. update_hotness_scores - 更新热度分数（每小时）
"""

import logging
from typing import Dict, Any
import asyncio

from app.tasks.celery_app import celery_app
from app.services.cache_prewarming import (
    get_prewarming_manager,
    PrewarmingPriority,
)
from app.services.prewarming_scheduler import get_scheduler
from app.services.data_sources.coingecko_client import coingecko_client
from app.core.metrics import metrics_collector

logger = logging.getLogger(__name__)


# ================================
# 辅助函数
# ================================


def run_async(coro):
    """
    在Celery任务中运行异步函数

    Args:
        coro: 协程对象

    Returns:
        协程的返回值
    """
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)


# ================================
# Celery任务
# ================================


@celery_app.task(
    name="app.tasks.cache_prewarming.prewarm_hot_coins",
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def prewarm_hot_coins(self) -> Dict[str, Any]:
    """
    预热Top 10热门币种

    优先级：高
    频率：每1分钟
    目标：确保最热门币种始终在缓存中

    Returns:
        Dict: 执行统计
    """
    logger.info("Starting prewarm_hot_coins task")

    try:
        # 1. 获取调度器和预热管理器
        scheduler = get_scheduler()
        manager = get_prewarming_manager()

        # 2. 获取高优先级列表
        coin_ids = run_async(
            scheduler.get_priority_list(PrewarmingPriority.HIGH)
        )

        if not coin_ids:
            logger.warning("No high priority coins found")
            return {
                "status": "success",
                "coins_prewarmed": 0,
                "reason": "no_coins"
            }

        # 3. 批量添加预热任务
        queued_count = 0
        for coin_id in coin_ids:
            success = run_async(
                manager.add_task(
                    coin_id=coin_id,
                    priority=PrewarmingPriority.HIGH,
                    force_refresh=False
                )
            )
            if success:
                queued_count += 1

        # 4. 记录指标
        metrics_collector.counters["prewarming_task_executed.priority:high"] += 1

        logger.info(
            f"Prewarm hot coins completed: "
            f"queued={queued_count}/{len(coin_ids)}"
        )

        return {
            "status": "success",
            "coins_prewarmed": queued_count,
            "total_coins": len(coin_ids)
        }

    except Exception as e:
        logger.error(f"Prewarm hot coins failed: {e}", exc_info=True)

        # 记录失败指标
        metrics_collector.counters["prewarming_task_failed.priority:high"] += 1

        # 重试
        raise self.retry(exc=e)


@celery_app.task(
    name="app.tasks.cache_prewarming.prewarm_trending_coins",
    bind=True,
    max_retries=3,
    default_retry_delay=300
)
def prewarm_trending_coins(self) -> Dict[str, Any]:
    """
    预热Top 100趋势币种

    优先级：中
    频率：每5分钟
    目标：覆盖大部分用户查询

    Returns:
        Dict: 执行统计
    """
    logger.info("Starting prewarm_trending_coins task")

    try:
        # 1. 获取调度器和预热管理器
        scheduler = get_scheduler()
        manager = get_prewarming_manager()

        # 2. 获取中优先级列表
        coin_ids = run_async(
            scheduler.get_priority_list(PrewarmingPriority.MEDIUM)
        )

        if not coin_ids:
            logger.warning("No medium priority coins found")
            return {
                "status": "success",
                "coins_prewarmed": 0,
                "reason": "no_coins"
            }

        # 3. 批量添加预热任务（限制数量避免过载）
        queued_count = 0
        for coin_id in coin_ids[:100]:  # 最多100个
            success = run_async(
                manager.add_task(
                    coin_id=coin_id,
                    priority=PrewarmingPriority.MEDIUM,
                    force_refresh=False
                )
            )
            if success:
                queued_count += 1

        # 4. 记录指标
        metrics_collector.counters["prewarming_task_executed.priority:medium"] += 1

        logger.info(
            f"Prewarm trending coins completed: "
            f"queued={queued_count}/{min(len(coin_ids), 100)}"
        )

        return {
            "status": "success",
            "coins_prewarmed": queued_count,
            "total_coins": min(len(coin_ids), 100)
        }

    except Exception as e:
        logger.error(f"Prewarm trending coins failed: {e}", exc_info=True)

        # 记录失败指标
        metrics_collector.counters["prewarming_task_failed.priority:medium"] += 1

        # 重试
        raise self.retry(exc=e)


@celery_app.task(
    name="app.tasks.cache_prewarming.update_hotness_scores",
    bind=True,
    max_retries=3,
    default_retry_delay=600
)
def update_hotness_scores(self) -> Dict[str, Any]:
    """
    更新热度分数和优先级列表

    优先级：默认
    频率：每小时
    目标：根据最新访问数据调整预热策略

    Returns:
        Dict: 执行统计
    """
    logger.info("Starting update_hotness_scores task")

    try:
        # 1. 获取调度器
        scheduler = get_scheduler()

        # 2. 获取Top 100币种列表（从CoinGecko）
        top_coins = run_async(
            coingecko_client.get_trending_coins(limit=100)
        )

        if not top_coins:
            logger.warning("Failed to get top coins from CoinGecko")
            return {
                "status": "failed",
                "reason": "no_coins_from_api"
            }

        coin_ids = [coin["id"] for coin in top_coins]

        # 3. 计算热度分数
        hotness_data = run_async(
            scheduler.calculate_hotness_scores(coin_ids)
        )

        # 4. 更新优先级列表
        priority_counts = run_async(
            scheduler.update_priority_lists(hotness_data)
        )

        # 5. 预测未来热门币种
        predictions = run_async(
            scheduler.predict_hot_coins(limit=20)
        )

        # 6. 记录指标
        metrics_collector.counters["hotness_scores_updated"] += 1

        logger.info(
            f"Hotness scores updated: "
            f"analyzed={len(hotness_data)}, "
            f"high={priority_counts['high']}, "
            f"medium={priority_counts['medium']}, "
            f"predicted={len(predictions)}"
        )

        return {
            "status": "success",
            "coins_analyzed": len(hotness_data),
            "priority_counts": priority_counts,
            "predictions_count": len(predictions),
            "top_predictions": [
                {"coin_id": cid, "score": score}
                for cid, score in predictions[:5]
            ]
        }

    except Exception as e:
        logger.error(
            f"Update hotness scores failed: {e}",
            exc_info=True
        )

        # 记录失败指标
        metrics_collector.counters["hotness_update_failed"] += 1

        # 重试
        raise self.retry(exc=e)


# ================================
# 手动触发函数
# ================================


def trigger_immediate_prewarm(
    priority: PrewarmingPriority = PrewarmingPriority.HIGH
) -> Dict[str, Any]:
    """
    手动触发立即预热

    用于API端点或调试

    Args:
        priority: 预热优先级

    Returns:
        Dict: 执行结果
    """
    logger.info(f"Manual trigger prewarm: priority={priority}")

    if priority == PrewarmingPriority.HIGH:
        result = prewarm_hot_coins.apply_async()
    else:
        result = prewarm_trending_coins.apply_async()

    return {
        "task_id": result.id,
        "priority": priority.value,
        "status": "queued"
    }
