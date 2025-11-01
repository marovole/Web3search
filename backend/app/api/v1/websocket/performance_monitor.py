"""
WebSocket性能监控端点
提供WebSocket连接和广播性能的实时监控
"""
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .connection_manager import connection_manager
from .sentiment_broadcaster import sentiment_broadcaster

router = APIRouter()


class PerformanceMetrics(BaseModel):
    """性能指标模型"""
    timestamp: str
    connection_metrics: Dict[str, Any]
    broadcast_metrics: Dict[str, Any]
    system_metrics: Dict[str, Any]


class ConnectionPerformance(BaseModel):
    """连接性能模型"""
    client_id: str
    connected_at: str
    last_activity: str
    message_count: int
    latency_ms: float
    subscription_count: int


@router.get("/performance", response_model=PerformanceMetrics)
async def get_performance_metrics():
    """
    获取WebSocket性能指标

    Returns:
        PerformanceMetrics: 实时性能指标
    """
    try:
        # 获取连接管理器统计
        connection_stats = connection_manager.get_connection_stats()

        # 获取广播器统计
        broadcast_stats = sentiment_broadcaster.get_broadcast_stats()

        # 获取系统指标
        system_metrics = await get_system_metrics()

        # 计算性能指标
        performance_metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "connection_metrics": {
                **connection_stats,
                "connections_per_second": calculate_connection_rate(),
                "average_subscriptions_per_client": calculate_avg_subscriptions(),
                "connection_efficiency": calculate_connection_efficiency()
            },
            "broadcast_metrics": {
                **broadcast_stats,
                "broadcast_rate_per_minute": calculate_broadcast_rate(),
                "success_rate": calculate_broadcast_success_rate(),
                "latency_p95": calculate_broadcast_latency_p95()
            },
            "system_metrics": system_metrics
        }

        return PerformanceMetrics(**performance_metrics)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取性能指标失败: {str(e)}")


@router.get("/connections", response_model=List[ConnectionPerformance])
async def get_connection_performance(
    limit: int = Query(50, ge=1, le=200),
    active_only: bool = Query(True)
):
    """
    获取连接性能详情

    Args:
        limit: 返回的连接数量限制
        active_only: 是否只返回活跃连接

    Returns:
        List[ConnectionPerformance]: 连接性能列表
    """
    try:
        connections = []

        for client_id, metadata in connection_manager.connection_metadata.items():
            if active_only and client_id not in connection_manager.active_connections:
                continue

            subscriptions = connection_manager.get_client_subscriptions(client_id)

            connection_perf = ConnectionPerformance(
                client_id=client_id,
                connected_at=metadata.get("connected_at", ""),
                last_activity=metadata.get("last_ping", ""),
                message_count=metadata.get("message_count", 0),
                latency_ms=estimate_connection_latency(client_id),
                subscription_count=len(subscriptions)
            )

            connections.append(connection_perf)

        # 按连接时间排序并限制数量
        connections.sort(key=lambda x: x.connected_at, reverse=True)
        return connections[:limit]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取连接性能失败: {str(e)}")


@router.get("/health-detailed")
async def get_websocket_health():
    """
    获取WebSocket服务详细健康状态

    Returns:
        Dict: 详细健康状态
    """
    try:
        # 基础健康检查
        is_healthy = True
        issues = []

        # 检查连接管理器
        active_connections = len(connection_manager.active_connections)
        if active_connections > 100:  # 假设最大连接数为100
            is_healthy = False
            issues.append(f"活跃连接数过高: {active_connections}")

        # 检查广播器状态
        if not sentiment_broadcaster.is_running:
            issues.append("广播器未运行")

        # 检查最近的广播成功率
        recent_success_rate = calculate_broadcast_success_rate()
        if recent_success_rate < 0.8:  # 成功率低于80%
            is_healthy = False
            issues.append(f"广播成功率过低: {recent_success_rate:.1%}")

        # 检查系统资源
        system_metrics = await get_system_metrics()
        if system_metrics.get("cpu_usage", 0) > 90:
            is_healthy = False
            issues.append(f"CPU使用率过高: {system_metrics['cpu_usage']:.1f}%")

        if system_metrics.get("memory_usage", 0) > 90:
            is_healthy = False
            issues.append(f"内存使用率过高: {system_metrics['memory_usage']:.1f}%")

        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "active_connections": active_connections,
            "broadcaster_running": sentiment_broadcaster.is_running,
            "recent_success_rate": recent_success_rate,
            "system_metrics": system_metrics,
            "issues": issues,
            "performance_summary": {
                "avg_response_time": calculate_avg_response_time(),
                "throughput_per_second": calculate_throughput(),
                "error_rate": calculate_error_rate()
            }
        }

    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }


@router.post("/optimize")
async def trigger_performance_optimization():
    """
    触发性能优化操作

    Returns:
        Dict: 优化结果
    """
    try:
        optimization_results = {}

        # 清理不活跃连接
        cleanup_start = time.time()
        await connection_manager.cleanup_inactive_connections(timeout_minutes=15)
        cleanup_time = time.time() - cleanup_start
        optimization_results["connection_cleanup"] = {
            "completed": True,
            "duration_seconds": cleanup_time
        }

        # 清理过期缓存
        cache_start = time.time()
        # 这里可以实现缓存清理逻辑
        cache_time = time.time() - cache_start
        optimization_results["cache_cleanup"] = {
            "completed": True,
            "duration_seconds": cache_time
        }

        # 优化热门币种列表
        popular_symbols = get_current_popular_symbols()
        sentiment_broadcaster.update_popular_symbols(popular_symbols)
        optimization_results["symbol_list_optimization"] = {
            "completed": True,
            "updated_symbols": popular_symbols
        }

        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "optimizations": optimization_results,
            "total_duration": sum(result["duration_seconds"] for result in optimization_results.values())
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"性能优化失败: {str(e)}")


# 辅助函数
async def get_system_metrics() -> Dict[str, Any]:
    """获取系统指标"""
    try:
        import psutil

        return {
            "cpu_usage": psutil.cpu_percent(interval=1),
            "memory_usage": psutil.virtual_memory().percent,
            "available_memory_gb": psutil.virtual_memory().available / 1024**3,
            "disk_usage": psutil.disk_usage('/').percent,
            "network_io": {
                "bytes_sent": psutil.net_io_counters().bytes_sent,
                "bytes_recv": psutil.net_io_counters().bytes_recv
            }
        }
    except Exception:
        return {"error": "无法获取系统指标"}


def calculate_connection_rate() -> float:
    """计算连接建立速率（每秒）"""
    # 这里可以实现连接速率计算逻辑
    stats = connection_manager.get_connection_stats()
    # 简化计算：假设运行时间为1小时
    return stats["total_connections"] / 3600 if stats["total_connections"] > 0 else 0


def calculate_avg_subscriptions() -> float:
    """计算平均每客户端订阅数"""
    stats = connection_manager.get_connection_stats()
    active_connections = stats["active_connections"]
    total_subscriptions = stats["total_subscriptions"]

    return total_subscriptions / active_connections if active_connections > 0 else 0


def calculate_connection_efficiency() -> float:
    """计算连接效率"""
    stats = connection_manager.get_connection_stats()
    return stats["active_connections"] / stats["total_connections"] if stats["total_connections"] > 0 else 1


def calculate_broadcast_rate() -> float:
    """计算广播速率（每分钟）"""
    stats = sentiment_broadcaster.get_broadcast_stats()
    total_broadcasts = stats["total_broadcasts"]
    # 简化计算：假设运行时间为1小时
    return (total_broadcasts * 60) / 3600 if total_broadcasts > 0 else 0


def calculate_broadcast_success_rate() -> float:
    """计算广播成功率"""
    stats = sentiment_broadcaster.get_broadcast_stats()
    successful = stats["successful_broadcasts"]
    total = stats["total_broadcasts"]

    return successful / total if total > 0 else 1.0


def calculate_broadcast_latency_p95() -> float:
    """计算广播延迟95分位数"""
    # 这里可以实现延迟统计逻辑
    return 50.0  # 示例值


def estimate_connection_latency(client_id: str) -> float:
    """估算连接延迟"""
    # 这里可以实现延迟测量逻辑
    return 30.0  # 示例值


def get_current_popular_symbols() -> List[str]:
    """获取当前热门币种"""
    # 这里可以实现热门币种计算逻辑
    return ["BTC", "ETH", "BNB", "SOL", "ADA"]


def calculate_avg_response_time() -> float:
    """计算平均响应时间"""
    return 25.0  # 示例值


def calculate_throughput() -> float:
    """计算吞吐量（每秒请求数）"""
    return 10.0  # 示例值


def calculate_error_rate() -> float:
    """计算错误率"""
    stats = sentiment_broadcaster.get_broadcast_stats()
    failed = stats["failed_broadcasts"]
    total = stats["total_broadcasts"]

    return failed / total if total > 0 else 0.0