"""
缓存管理API端点

提供缓存预热、统计查询和管理功能
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import logging

from app.services.cache_prewarming import (
    get_prewarming_manager,
    PrewarmingPriority
)
from app.core.cache_manager import get_cache_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cache", tags=["cache"])


# ================================
# Pydantic模型
# ================================


class PrewarmRequest(BaseModel):
    """缓存预热请求"""

    coin_ids: List[str] = Field(
        ...,
        description="要预热的币种ID列表（CoinGecko ID）",
        example=["bitcoin", "ethereum", "solana"]
    )
    priority: Optional[str] = Field(
        default="medium",
        description="预热优先级: high, medium, low",
        example="high"
    )
    force: bool = Field(
        default=False,
        description="是否强制重新预热（忽略现有缓存）"
    )


class PrewarmResponse(BaseModel):
    """缓存预热响应"""

    message: str
    queued_coins: int
    priority: str
    estimated_time_seconds: int
    timestamp: str


# ================================
# API端点
# ================================


@router.post("/prewarm", response_model=PrewarmResponse)
async def prewarm_cache(request: PrewarmRequest):
    """
    手动触发缓存预热

    预热指定币种的数据到L1和L2缓存中。

    **参数：**
    - `coin_ids`: 要预热的币种ID列表（CoinGecko格式）
    - `priority`: 预热优先级（high/medium/low），默认medium
    - `force`: 是否强制重新获取数据（默认false，使用现有缓存）

    **示例：**
    ```json
    {
      "coin_ids": ["bitcoin", "ethereum"],
      "priority": "high",
      "force": false
    }
    ```
    """
    try:
        # 验证priority参数
        try:
            priority_enum = PrewarmingPriority[request.priority.upper()]
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid priority: {request.priority}. "
                       f"Must be one of: high, medium, low"
            )

        # 验证coin_ids
        if not request.coin_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="coin_ids cannot be empty"
            )

        if len(request.coin_ids) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Too many coins (max 100 per request)"
            )

        # 获取预热管理器
        prewarming_manager = get_prewarming_manager()

        # 添加预热任务到队列
        queued_count = 0
        for coin_id in request.coin_ids:
            success = await prewarming_manager.add_task(
                coin_id=coin_id,
                priority=priority_enum,
                force_refresh=request.force
            )
            if success:
                queued_count += 1

        # 估算预热时间（每个币种约2-3秒）
        estimated_time = queued_count * 2.5

        logger.info(
            f"Cache prewarm requested: {queued_count} coins, "
            f"priority={request.priority}, force={request.force}"
        )

        return PrewarmResponse(
            message=f"Successfully queued {queued_count} coins for prewarming",
            queued_coins=queued_count,
            priority=request.priority,
            estimated_time_seconds=int(estimated_time),
            timestamp=datetime.now().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prewarm cache failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to prewarm cache: {str(e)}"
        )


@router.get("/stats")
async def get_cache_stats():
    """
    获取缓存统计信息

    返回L1和L2缓存的详细统计数据，包括：
    - 命中率
    - 缓存大小
    - 命中/未命中次数
    - 淘汰次数

    **响应示例：**
    ```json
    {
      "l1": {
        "size": 85,
        "max_size": 100,
        "hit_rate": 0.65,
        "hits": 650,
        "misses": 350
      },
      "l2": {
        "total_hits": 8500,
        "total_misses": 1500,
        "hit_rate": 0.85
      },
      "combined": {
        "total_hits": 9150,
        "total_misses": 1850,
        "hit_rate": 0.832
      }
    }
    ```
    """
    try:
        cache_manager = get_cache_manager()
        stats = await cache_manager.get_stats()

        return {
            "timestamp": datetime.now().isoformat(),
            "stats": stats
        }

    except Exception as e:
        logger.error(f"Get cache stats failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cache stats: {str(e)}"
        )


@router.post("/clear")
async def clear_l1_cache():
    """
    清空L1内存缓存

    清除所有L1缓存数据，但保留L2 Redis缓存。
    通常用于调试或强制刷新缓存。

    **注意：** 这会导致短时间内命中率下降，直到L1重新填充。
    """
    try:
        cache_manager = get_cache_manager()
        await cache_manager.clear_l1()

        logger.info("L1 cache cleared via API")

        return {
            "message": "L1 cache cleared successfully",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Clear L1 cache failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}"
        )


@router.get("/l1/keys")
async def get_l1_cache_keys():
    """
    获取L1缓存键列表（调试用）

    返回当前L1缓存中的所有缓存键。

    **注意：** 此端点主要用于调试，生产环境应谨慎使用。
    """
    try:
        cache_manager = get_cache_manager()
        keys = await cache_manager.get_l1_keys()
        size = await cache_manager.get_l1_size()

        return {
            "timestamp": datetime.now().isoformat(),
            "size": size,
            "keys": keys
        }

    except Exception as e:
        logger.error(f"Get L1 keys failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get L1 keys: {str(e)}"
        )


@router.get("/prewarming/status")
async def get_prewarming_status():
    """
    获取缓存预热任务状态（Stage 4任务4.4）

    返回当前预热队列的状态信息，包括：
    - 队列中的任务数
    - 正在执行的任务
    - 预热统计（成功/失败次数）
    - 调度器统计（最后更新时间、优先级列表大小）
    - 热度分数Top 10
    - 预测的未来热门币种
    """
    try:
        from app.services.prewarming_scheduler import get_scheduler
        from app.core.redis_client import redis_client

        prewarming_manager = get_prewarming_manager()
        scheduler = get_scheduler()

        # 预热管理器状态
        manager_status = prewarming_manager.get_status()

        # 调度器统计
        scheduler_stats = scheduler.get_stats()

        # 获取优先级列表大小
        async with redis_client() as redis:
            high_priority_size = await redis.llen("prewarming:high_priority")
            medium_priority_size = await redis.llen("prewarming:medium_priority")
            low_priority_size = await redis.llen("prewarming:low_priority")

        # 获取热度分数Top 10
        async with redis_client() as redis:
            top_coins = await redis.zrevrange(
                "hotness:scores",
                0,
                9,  # Top 10
                withscores=True
            )

        # 格式化Top 10
        hotness_top10 = []
        for item in top_coins:
            if isinstance(item, tuple):
                coin_id, score = item
            else:
                # 如果返回格式不同，尝试解析
                coin_id = item
                score = 0

            hotness_top10.append({
                "coin_id": coin_id.decode() if isinstance(coin_id, bytes) else coin_id,
                "hotness_score": round(float(score), 2)
            })

        # 获取预测的未来热门币种
        predictions = await scheduler.predict_hot_coins(limit=10)
        predicted_coins = [
            {
                "coin_id": coin_id,
                "prediction_score": round(score, 2)
            }
            for coin_id, score in predictions
        ]

        return {
            "timestamp": datetime.now().isoformat(),
            "manager": manager_status,
            "scheduler": {
                **scheduler_stats,
                "priority_list_sizes": {
                    "high": high_priority_size,
                    "medium": medium_priority_size,
                    "low": low_priority_size
                }
            },
            "hotness_top10": hotness_top10,
            "predicted_hot_coins": predicted_coins
        }

    except Exception as e:
        logger.error(f"Get prewarming status failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get prewarming status: {str(e)}"
        )


@router.get("/scheduler/status")
async def get_scheduler_status():
    """
    获取调度器状态（Stage 4任务4.6）

    返回调度器的详细状态信息，包括：
    - 热度分数排名（Top 20）
    - 优先级列表统计
    - 趋势分析结果
    - 预测结果

    **响应示例：**
    ```json
    {
      "timestamp": "2025-10-28T12:00:00Z",
      "last_update": "2025-10-28T11:00:00Z",
      "hotness_rankings": [
        {"coin_id": "bitcoin", "score": 98.5},
        {"coin_id": "ethereum", "score": 95.2}
      ],
      "priority_lists": {
        "high": 10,
        "medium": 100,
        "low": 50
      },
      "predictions": [
        {"coin_id": "solana", "score": 85.3}
      ]
    }
    ```
    """
    try:
        from app.services.prewarming_scheduler import get_scheduler
        from app.core.redis_client import redis_client

        scheduler = get_scheduler()

        # 调度器基本统计
        scheduler_stats = scheduler.get_stats()

        # 获取优先级列表大小
        async with redis_client() as redis:
            high_priority_size = await redis.llen("prewarming:high_priority")
            medium_priority_size = await redis.llen("prewarming:medium_priority")
            low_priority_size = await redis.llen("prewarming:low_priority")

        # 获取热度分数Top 20
        async with redis_client() as redis:
            top_coins = await redis.zrevrange(
                "hotness:scores",
                0,
                19,  # Top 20
                withscores=True
            )

        # 格式化Top 20
        hotness_rankings = []
        for item in top_coins:
            if isinstance(item, tuple):
                coin_id, score = item
            else:
                coin_id = item
                score = 0

            hotness_rankings.append({
                "coin_id": coin_id.decode() if isinstance(coin_id, bytes) else coin_id,
                "hotness_score": round(float(score), 2)
            })

        # 获取预测的未来热门币种（Top 10）
        predictions = await scheduler.predict_hot_coins(limit=10)
        predicted_coins = [
            {
                "coin_id": coin_id,
                "prediction_score": round(score, 2)
            }
            for coin_id, score in predictions
        ]

        return {
            "timestamp": datetime.now().isoformat(),
            "last_update": scheduler_stats.get("last_update_datetime"),
            "hotness_rankings": hotness_rankings,
            "priority_lists": {
                "high": high_priority_size,
                "medium": medium_priority_size,
                "low": low_priority_size,
                "total": high_priority_size + medium_priority_size + low_priority_size
            },
            "predictions": predicted_coins
        }

    except Exception as e:
        logger.error(f"Get scheduler status failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get scheduler status: {str(e)}"
        )


@router.get("/dashboard")
async def get_cache_dashboard():
    """
    获取缓存Dashboard完整数据（Stage 4任务4.6）

    整合所有缓存相关指标，提供一站式Dashboard数据导出。
    包括：
    - L1/L2缓存统计（命中率、大小、性能）
    - 预热队列状态（队列大小、执行统计）
    - 调度器状态（热度排名、预测）
    - 系统性能指标

    **响应示例：**
    ```json
    {
      "timestamp": "2025-10-28T12:00:00Z",
      "cache": {
        "l1": {"size": 85, "hit_rate": 0.65},
        "l2": {"hit_rate": 0.85},
        "combined_hit_rate": 0.832
      },
      "prewarming": {
        "queue_size": 25,
        "stats": {"total_prewarmed": 1000}
      },
      "scheduler": {
        "hotness_top10": [...],
        "predictions": [...]
      },
      "performance": {
        "avg_response_time_ms": 125.5,
        "p95_response_time_ms": 450.2
      }
    }
    ```
    """
    try:
        from app.services.prewarming_scheduler import get_scheduler
        from app.core.metrics import metrics_collector
        from app.core.redis_client import redis_client

        # 1. 获取缓存统计
        cache_manager = get_cache_manager()
        cache_stats = await cache_manager.get_stats()

        # 2. 获取预热状态
        prewarming_manager = get_prewarming_manager()
        prewarming_status = prewarming_manager.get_status()

        # 3. 获取调度器状态
        scheduler = get_scheduler()
        scheduler_stats = scheduler.get_stats()

        # 4. 获取热度分数Top 10
        async with redis_client() as redis:
            top_coins = await redis.zrevrange(
                "hotness:scores",
                0,
                9,  # Top 10
                withscores=True
            )

        hotness_top10 = []
        for item in top_coins:
            if isinstance(item, tuple):
                coin_id, score = item
            else:
                coin_id = item
                score = 0

            hotness_top10.append({
                "coin_id": coin_id.decode() if isinstance(coin_id, bytes) else coin_id,
                "hotness_score": round(float(score), 2)
            })

        # 5. 获取预测
        predictions = await scheduler.predict_hot_coins(limit=10)
        predicted_coins = [
            {
                "coin_id": coin_id,
                "prediction_score": round(score, 2)
            }
            for coin_id, score in predictions
        ]

        # 6. 获取性能指标
        metrics_summary = metrics_collector.get_summary()

        # 7. 计算组合命中率
        l1_stats = cache_stats.get("l1", {})
        l2_stats = cache_stats.get("l2", {})
        combined_stats = cache_stats.get("combined", {})

        return {
            "timestamp": datetime.now().isoformat(),
            "cache": {
                "l1": {
                    "size": l1_stats.get("size", 0),
                    "max_size": l1_stats.get("max_size", 100),
                    "hit_rate": round(l1_stats.get("hit_rate", 0.0), 4),
                    "hits": l1_stats.get("hits", 0),
                    "misses": l1_stats.get("misses", 0),
                    "evictions": l1_stats.get("evictions", 0)
                },
                "l2": {
                    "hit_rate": round(l2_stats.get("hit_rate", 0.0), 4),
                    "total_hits": l2_stats.get("total_hits", 0),
                    "total_misses": l2_stats.get("total_misses", 0)
                },
                "combined": {
                    "hit_rate": round(combined_stats.get("hit_rate", 0.0), 4),
                    "total_hits": combined_stats.get("total_hits", 0),
                    "total_misses": combined_stats.get("total_misses", 0)
                }
            },
            "prewarming": {
                "queue_size": prewarming_status.get("queue_size", 0),
                "queue_breakdown": prewarming_status.get("queue_breakdown", {}),
                "is_running": prewarming_status.get("is_running", False),
                "stats": prewarming_status.get("stats", {})
            },
            "scheduler": {
                "last_update": scheduler_stats.get("last_update_datetime"),
                "hotness_top10": hotness_top10,
                "predictions": predicted_coins,
                "stats": scheduler_stats
            },
            "performance": {
                "avg_response_time_ms": round(
                    metrics_summary.get("avg_response_time_ms", 0), 2
                ),
                "p95_response_time_ms": round(
                    metrics_summary.get("p95_response_time_ms", 0), 2
                ),
                "p99_response_time_ms": round(
                    metrics_summary.get("p99_response_time_ms", 0), 2
                ),
                "cache_hit_rate": round(
                    metrics_summary.get("cache_hit_rate", 0.0), 4
                ),
                "api_success_rate": round(
                    metrics_summary.get("api_success_rate", 0.0), 4
                )
            }
        }

    except Exception as e:
        logger.error(f"Get cache dashboard failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cache dashboard: {str(e)}"
        )
