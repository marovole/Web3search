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
    获取缓存预热任务状态

    返回当前预热队列的状态信息，包括：
    - 队列中的任务数
    - 正在执行的任务
    - 预热统计（成功/失败次数）
    """
    try:
        prewarming_manager = get_prewarming_manager()
        status_info = prewarming_manager.get_status()

        return {
            "timestamp": datetime.now().isoformat(),
            "status": status_info
        }

    except Exception as e:
        logger.error(f"Get prewarming status failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get prewarming status: {str(e)}"
        )
