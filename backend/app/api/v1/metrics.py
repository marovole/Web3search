"""
性能指标API端点（任务 9.7）
"""
from fastapi import APIRouter, Query
from typing import Optional

from app.core.metrics import metrics_collector, get_metrics_summary, reset_metrics

router = APIRouter()


@router.get("/metrics")
async def get_metrics(
    endpoint: Optional[str] = Query(None, description="特定端点名称（可选）"),
    api: Optional[str] = Query(None, description="特定API名称（可选）"),
):
    """
    获取性能指标

    返回完整的性能指标摘要，包括：
    - 响应时间统计（P50/P95/P99）
    - 缓存命中率
    - API调用成功率
    - 数据源可用性

    Args:
        endpoint: 过滤特定端点的响应时间（可选）
        api: 过滤特定API的调用统计（可选）

    Returns:
        dict: 性能指标摘要
    """
    # 如果指定了特定端点或API，返回过滤后的结果
    if endpoint:
        return {
            "endpoint": endpoint,
            "response_time_stats": metrics_collector.get_response_time_percentiles(endpoint),
        }

    if api:
        return {
            "api": api,
            "api_stats": metrics_collector.get_api_stats(api),
        }

    # 返回完整摘要
    return get_metrics_summary()


@router.get("/metrics/response-time")
async def get_response_time_metrics(
    endpoint: Optional[str] = Query(None, description="端点名称（可选）")
):
    """
    获取响应时间统计

    Args:
        endpoint: 端点名称（可选），如果不提供则返回所有端点

    Returns:
        dict: 响应时间百分位数统计
    """
    if endpoint:
        return {
            "endpoint": endpoint,
            "stats": metrics_collector.get_response_time_percentiles(endpoint),
        }

    return {
        "all_endpoints": metrics_collector.get_all_response_time_stats()
    }


@router.get("/metrics/cache")
async def get_cache_metrics():
    """
    获取缓存统计

    Returns:
        dict: 缓存命中率和请求数
    """
    return metrics_collector.get_cache_stats()


@router.get("/metrics/api")
async def get_api_metrics(
    api_name: Optional[str] = Query(None, description="API名称（可选）")
):
    """
    获取API调用统计

    Args:
        api_name: API名称（可选），如果不提供则返回所有API

    Returns:
        dict: API成功率和调用次数
    """
    if api_name:
        return {
            "api": api_name,
            "stats": metrics_collector.get_api_stats(api_name),
        }

    return {
        "overall": metrics_collector.get_api_stats(),
        "by_api": metrics_collector.get_all_api_stats(),
    }


@router.get("/metrics/data-sources")
async def get_data_source_metrics(
    source_name: Optional[str] = Query(None, description="数据源名称（可选）")
):
    """
    获取数据源可用性统计

    Args:
        source_name: 数据源名称（可选），如果不提供则返回所有数据源

    Returns:
        dict: 数据源可用性和状态
    """
    return metrics_collector.get_data_source_availability(source_name)


@router.post("/metrics/reset")
async def reset_all_metrics():
    """
    重置所有性能指标

    警告：此操作将清除所有历史统计数据

    Returns:
        dict: 重置确认消息
    """
    reset_metrics()
    return {
        "success": True,
        "message": "所有性能指标已重置"
    }
