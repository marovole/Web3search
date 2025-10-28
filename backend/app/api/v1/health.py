"""
健康检查API端点
用于监控服务可用性和依赖项状态
"""
from fastapi import APIRouter, Response, status
from datetime import datetime

from app.core.database import check_database_health, get_pool_stats
from app.core.db_middleware import performance_collector

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def basic_health():
    """
    基础健康检查

    返回服务基本状态
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "web3search_backend",
    }


@router.get("/database")
async def database_health(response: Response):
    """
    数据库健康检查

    检查数据库连接状态、响应延迟和连接池统计
    """
    health_data = await check_database_health()

    # 如果数据库不健康，返回503状态码
    if health_data["status"] == "unhealthy":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "timestamp": datetime.now().isoformat(),
        **health_data,
    }


@router.get("/database/pool")
async def database_pool_stats():
    """
    数据库连接池统计信息

    返回连接池当前状态和配置
    """
    return {
        "timestamp": datetime.now().isoformat(),
        "pool_stats": get_pool_stats(),
    }


@router.get("/dependencies")
async def dependencies_health(response: Response):
    """
    所有依赖项健康检查（Stage 4任务4.3）

    检查数据库、Redis、缓存、预热服务等所有外部依赖

    返回格式：
    - status: healthy（全部正常）| degraded（部分降级）| unhealthy（关键依赖失败）
    - dependencies: 各依赖项的详细健康状态
    """
    from app.core.redis_client import check_redis_health
    from app.core.cache_manager import get_cache_manager
    from app.services.cache_prewarming import get_prewarming_manager

    # 检查所有依赖项
    db_health = await check_database_health()
    redis_health = await check_redis_health()

    # 检查L1缓存状态
    try:
        cache_manager = get_cache_manager()
        cache_stats = await cache_manager.get_stats()
        cache_health = {
            "status": "healthy",
            "l1_size": cache_stats["l1"]["size"],
            "l1_capacity": cache_stats["l1"]["max_size"],
            "l1_hit_rate": cache_stats["l1"]["hit_rate"],
            "l2_hit_rate": cache_stats["l2"]["hit_rate"]
        }
    except Exception as e:
        cache_health = {
            "status": "unhealthy",
            "error": str(e)
        }

    # 检查预热服务状态
    try:
        prewarming_manager = get_prewarming_manager()
        prewarming_status = prewarming_manager.get_status()
        prewarming_health = {
            "status": "healthy",
            "queue_size": prewarming_status.get("queue_size", 0),
            "is_running": prewarming_status.get("is_running", False),
            "stats": prewarming_status.get("stats", {})
        }
    except Exception as e:
        prewarming_health = {
            "status": "unhealthy",
            "error": str(e)
        }

    # 判断整体健康状态
    statuses = [
        db_health["status"],
        redis_health["status"],
        cache_health["status"],
        prewarming_health["status"]
    ]

    # 如果有任何unhealthy，整体为unhealthy
    if "unhealthy" in statuses:
        overall_status = "unhealthy"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    # 如果有degraded，整体为degraded
    elif "degraded" in statuses:
        overall_status = "degraded"
    else:
        overall_status = "healthy"

    return {
        "status": overall_status,
        "timestamp": datetime.now().isoformat(),
        "dependencies": {
            "database": db_health,
            "redis": redis_health,
            "cache": cache_health,
            "prewarming": prewarming_health
        },
    }


@router.get("/metrics/database")
async def database_metrics():
    """
    数据库性能指标

    返回查询统计信息、慢查询等
    """
    return {
        "timestamp": datetime.now().isoformat(),
        "performance": performance_collector.get_stats(),
        "pool": get_pool_stats(),
    }


@router.post("/metrics/database/reset")
async def reset_database_metrics():
    """
    重置数据库性能统计

    清除累积的性能数据
    """
    performance_collector.reset_stats()
    return {
        "message": "Database metrics reset successfully",
        "timestamp": datetime.now().isoformat(),
    }
