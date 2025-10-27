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
    所有依赖项健康检查

    检查数据库、Redis等所有外部依赖
    """
    # TODO: 添加Redis健康检查
    # TODO: 添加外部API健康检查（CoinGecko、OpenRouter等）

    db_health = await check_database_health()

    all_healthy = db_health["status"] == "healthy"

    if not all_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "healthy" if all_healthy else "degraded",
        "timestamp": datetime.now().isoformat(),
        "dependencies": {
            "database": db_health,
            # TODO: 添加更多依赖项
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
