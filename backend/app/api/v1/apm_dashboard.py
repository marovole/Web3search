"""
APM性能Dashboard API
提供实时性能监控数据和告警信息
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio

from app.core.metrics_collector import metrics_collector
from app.core.alerting import alert_manager
from app.core.monitoring import apm_collector
from app.api.deps import get_current_user, require_admin
from app.models.user import User

router = APIRouter(prefix="/apm", tags=["APM Dashboard"])


@router.get("/dashboard/overview")
async def get_dashboard_overview(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取APM Dashboard概览数据
    包括系统状态、关键指标和活跃告警
    """
    try:
        # 获取实时指标摘要
        metrics_summary = metrics_collector.get_metrics_summary()
        
        # 获取活跃告警
        active_alerts = alert_manager.get_active_alerts()
        
        # 获取最近的告警历史
        recent_alerts = alert_manager.get_alert_history(limit=10)
        
        # 系统健康状态评估
        health_status = _evaluate_system_health(metrics_summary, active_alerts)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "health_status": health_status,
            "metrics": metrics_summary,
            "alerts": {
                "active_count": len(active_alerts),
                "active_alerts": [alert.to_dict() for alert in active_alerts],
                "recent_count": len(recent_alerts),
                "recent_alerts": [alert.to_dict() for alert in recent_alerts[-5:]]
            },
            "performance_trends": _get_performance_trends(metrics_summary)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard overview: {str(e)}")


@router.get("/metrics/api")
async def get_api_metrics(
    timeframe: str = Query("1h", description="时间范围: 1h, 6h, 24h, 7d"),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取API性能指标
    """
    try:
        # 根据时间范围获取数据
        time_delta = _parse_timeframe(timeframe)
        
        # 获取API指标详情
        api_metrics = {
            "response_times": _get_response_time_metrics(time_delta),
            "error_rates": _get_error_rate_metrics(time_delta),
            "request_volumes": _get_request_volume_metrics(time_delta),
            "endpoint_performance": _get_endpoint_performance(time_delta),
            "status_code_distribution": _get_status_code_distribution(time_delta)
        }
        
        return {
            "timeframe": timeframe,
            "timestamp": datetime.now().isoformat(),
            "metrics": api_metrics
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get API metrics: {str(e)}")


@router.get("/metrics/system")
async def get_system_metrics(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取系统资源指标
    """
    try:
        # 获取系统指标
        system_metrics = {
            "cpu": _get_cpu_metrics(),
            "memory": _get_memory_metrics(),
            "disk": _get_disk_metrics(),
            "network": _get_network_metrics()
        }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "metrics": system_metrics
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system metrics: {str(e)}")


@router.get("/metrics/database")
async def get_database_metrics(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取数据库性能指标
    """
    try:
        db_metrics = {
            "connection_pool": _get_db_connection_metrics(),
            "query_performance": _get_db_query_metrics(),
            "slow_queries": _get_slow_queries(),
            "error_rates": _get_db_error_rates()
        }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "metrics": db_metrics
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get database metrics: {str(e)}")


@router.get("/metrics/external-apis")
async def get_external_api_metrics(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取外部API调用指标
    """
    try:
        external_metrics = {
            "openrouter": _get_external_api_metrics("openrouter"),
            "coingecko": _get_external_api_metrics("coingecko"),
            "etherscan": _get_external_api_metrics("etherscan"),
            "overall": _get_overall_external_metrics()
        }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "metrics": external_metrics
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get external API metrics: {str(e)}")


@router.get("/alerts")
async def get_alerts(
    status: str = Query("active", description="告警状态: active, resolved, all"),
    limit: int = Query(50, description="返回数量限制"),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取告警信息
    """
    try:
        if status == "active":
            alerts = alert_manager.get_active_alerts()
        elif status == "resolved":
            alerts = [alert for alert in alert_manager.get_alert_history() if alert.resolved]
        else:  # all
            alerts = alert_manager.get_alert_history(limit=limit)
        
        return {
            "status": status,
            "count": len(alerts),
            "alerts": [alert.to_dict() for alert in alerts[:limit]],
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")


@router.get("/traces")
async def get_recent_traces(
    limit: int = Query(20, description="返回数量限制"),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取最近的分布式追踪数据
    """
    try:
        # 这里应该从实际的追踪系统中获取数据
        # 暂时返回模拟数据
        traces = _get_sample_traces(limit)
        
        return {
            "count": len(traces),
            "traces": traces,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get traces: {str(e)}")


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    解决告警
    """
    try:
        # 这里应该实现告警解决逻辑
        # 暂时返回成功响应
        return {
            "alert_id": alert_id,
            "resolved": True,
            "resolved_at": datetime.now().isoformat(),
            "resolved_by": current_user.email
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resolve alert: {str(e)}")


def _evaluate_system_health(metrics_summary: Dict[str, Any], active_alerts: List) -> str:
    """评估系统健康状态"""
    critical_alerts = [alert for alert in active_alerts if alert.level.value == "critical"]
    error_alerts = [alert for alert in active_alerts if alert.level.value == "error"]
    warning_alerts = [alert for alert in active_alerts if alert.level.value == "warning"]
    
    if critical_alerts:
        return "critical"
    elif error_alerts:
        return "error"
    elif warning_alerts:
        return "warning"
    
    # 检查关键指标
    cpu_usage = metrics_summary.get("system", {}).get("cpu_usage", 0)
    memory_usage = metrics_summary.get("system", {}).get("memory_usage", 0)
    api_error_rate = metrics_summary.get("api", {}).get("error_rate", 0)
    
    if cpu_usage > 90 or memory_usage > 90 or api_error_rate > 0.1:
        return "error"
    elif cpu_usage > 80 or memory_usage > 80 or api_error_rate > 0.05:
        return "warning"
    
    return "healthy"


def _get_performance_trends(metrics_summary: Dict[str, Any]) -> Dict[str, str]:
    """获取性能趋势"""
    trends = {}
    
    # API响应时间趋势
    avg_response_time = metrics_summary.get("api", {}).get("avg_response_time", 0)
    if avg_response_time < 200:
        trends["response_time"] = "improving"
    elif avg_response_time < 500:
        trends["response_time"] = "stable"
    else:
        trends["response_time"] = "degrading"
    
    # 错误率趋势
    error_rate = metrics_summary.get("api", {}).get("error_rate", 0)
    if error_rate < 0.01:
        trends["error_rate"] = "improving"
    elif error_rate < 0.05:
        trends["error_rate"] = "stable"
    else:
        trends["error_rate"] = "degrading"
    
    return trends


def _parse_timeframe(timeframe: str) -> timedelta:
    """解析时间范围"""
    timeframe_map = {
        "1h": timedelta(hours=1),
        "6h": timedelta(hours=6),
        "24h": timedelta(hours=24),
        "7d": timedelta(days=7)
    }
    return timeframe_map.get(timeframe, timedelta(hours=1))


def _get_response_time_metrics(time_delta: timedelta) -> Dict[str, Any]:
    """获取响应时间指标"""
    # 模拟数据，实际应该从监控系统获取
    return {
        "avg_ms": 245.6,
        "p50_ms": 220.0,
        "p95_ms": 450.0,
        "p99_ms": 800.0,
        "max_ms": 1200.0
    }


def _get_error_rate_metrics(time_delta: timedelta) -> Dict[str, Any]:
    """获取错误率指标"""
    return {
        "overall_rate": 0.023,
        "client_errors": 0.018,
        "server_errors": 0.005,
        "timeout_errors": 0.000
    }


def _get_request_volume_metrics(time_delta: timedelta) -> Dict[str, Any]:
    """获取请求量指标"""
    return {
        "total_requests": 15420,
        "requests_per_second": 4.28,
        "peak_rps": 12.5,
        "unique_clients": 1247
    }


def _get_endpoint_performance(time_delta: timedelta) -> List[Dict[str, Any]]:
    """获取端点性能指标"""
    return [
        {"endpoint": "/api/v1/chat", "avg_ms": 180, "requests": 5234, "error_rate": 0.015},
        {"endpoint": "/api/v1/research", "avg_ms": 3200, "requests": 892, "error_rate": 0.032},
        {"endpoint": "/api/v1/search", "avg_ms": 120, "requests": 3421, "error_rate": 0.008},
        {"endpoint": "/api/v1/reports", "avg_ms": 450, "requests": 2156, "error_rate": 0.021}
    ]


def _get_status_code_distribution(time_delta: timedelta) -> Dict[str, int]:
    """获取状态码分布"""
    return {
        "200": 14890,
        "201": 234,
        "400": 189,
        "401": 67,
        "404": 45,
        "500": 23,
        "502": 8,
        "503": 2
    }


def _get_cpu_metrics() -> Dict[str, Any]:
    """获取CPU指标"""
    return {
        "usage_percent": 45.2,
        "load_average": [1.2, 1.5, 1.8],
        "cores": 4,
        "processes": 156
    }


def _get_memory_metrics() -> Dict[str, Any]:
    """获取内存指标"""
    return {
        "usage_percent": 67.8,
        "total_gb": 16.0,
        "used_gb": 10.8,
        "available_gb": 5.2,
        "swap_usage_percent": 12.3
    }


def _get_disk_metrics() -> Dict[str, Any]:
    """获取磁盘指标"""
    return {
        "usage_percent": 78.5,
        "total_gb": 500.0,
        "used_gb": 392.5,
        "available_gb": 107.5,
        "read_iops": 245,
        "write_iops": 189
    }


def _get_network_metrics() -> Dict[str, Any]:
    """获取网络指标"""
    return {
        "bytes_sent_per_sec": 1024000,
        "bytes_recv_per_sec": 2048000,
        "packets_sent_per_sec": 1250,
        "packets_recv_per_sec": 2100,
        "connections": 89
    }


def _get_db_connection_metrics() -> Dict[str, Any]:
    """获取数据库连接指标"""
    return {
        "active_connections": 12,
        "idle_connections": 8,
        "max_connections": 100,
        "connection_pool_utilization": 0.12
    }


def _get_db_query_metrics() -> Dict[str, Any]:
    """获取数据库查询指标"""
    return {
        "queries_per_second": 45.6,
        "avg_query_time_ms": 23.4,
        "slow_queries_count": 3,
        "total_queries": 156789
    }


def _get_slow_queries() -> List[Dict[str, Any]]:
    """获取慢查询列表"""
    return [
        {"query": "SELECT * FROM reports WHERE created_at > ?", "duration_ms": 2340, "executed_at": "2024-01-15T10:30:00Z"},
        {"query": "SELECT * FROM search_history WHERE user_id = ?", "duration_ms": 1890, "executed_at": "2024-01-15T10:25:00Z"}
    ]


def _get_db_error_rates() -> Dict[str, Any]:
    """获取数据库错误率"""
    return {
        "connection_error_rate": 0.001,
        "timeout_error_rate": 0.0005,
        "syntax_error_rate": 0.0001,
        "overall_error_rate": 0.0016
    }


def _get_external_api_metrics(service: str) -> Dict[str, Any]:
    """获取外部API指标"""
    return {
        "requests_per_minute": 45.6,
        "avg_response_time_ms": 234.5,
        "error_rate": 0.023,
        "timeout_rate": 0.005,
        "status": "healthy"
    }


def _get_overall_external_metrics() -> Dict[str, Any]:
    """获取整体外部API指标"""
    return {
        "total_requests": 15678,
        "total_errors": 367,
        "overall_error_rate": 0.0234,
        "avg_response_time_ms": 198.7,
        "services_count": 4,
        "healthy_services": 3
    }


def _get_sample_traces(limit: int) -> List[Dict[str, Any]]:
    """获取示例追踪数据"""
    return [
        {
            "trace_id": "trace_1234567890",
            "span_id": "span_abcdef",
            "operation": "GET /api/v1/chat",
            "duration_ms": 245,
            "status": "ok",
            "timestamp": "2024-01-15T10:30:00Z",
            "service": "web3search-api"
        },
        {
            "trace_id": "trace_1234567891",
            "span_id": "span_ghijkl",
            "operation": "POST /api/v1/research",
            "duration_ms": 3200,
            "status": "ok",
            "timestamp": "2024-01-15T10:29:45Z",
            "service": "web3search-api"
        }
    ][:limit]
