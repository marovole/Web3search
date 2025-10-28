"""
性能指标追踪系统（任务 9.7）

提供全面的性能监控功能：
1. 响应时间统计（P50/P95/P99）
2. 缓存命中率监控
3. API调用成功率
4. 数据源可用性
"""
import time
import asyncio
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from collections import defaultdict, deque
from functools import wraps
import statistics
from enum import Enum


# ================================
# 指标类型
# ================================

class MetricType(str, Enum):
    """指标类型"""
    RESPONSE_TIME = "response_time"      # 响应时间
    CACHE_HIT = "cache_hit"              # 缓存命中
    CACHE_MISS = "cache_miss"            # 缓存未命中
    API_SUCCESS = "api_success"          # API调用成功
    API_FAILURE = "api_failure"          # API调用失败
    DATA_SOURCE_UP = "data_source_up"    # 数据源可用
    DATA_SOURCE_DOWN = "data_source_down" # 数据源不可用


# ================================
# 性能指标收集器
# ================================

class MetricsCollector:
    """
    性能指标收集器

    功能：
    1. 记录响应时间并计算百分位数
    2. 统计缓存命中率
    3. 追踪API调用成功率
    4. 监控数据源可用性
    """

    def __init__(self, max_samples: int = 10000):
        """
        初始化指标收集器

        Args:
            max_samples: 每个指标保留的最大样本数
        """
        self.max_samples = max_samples

        # 响应时间样本（使用 deque 自动限制大小）
        self.response_times: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=max_samples)
        )

        # 计数器
        self.counters: Dict[str, int] = defaultdict(int)

        # 数据源状态
        self.data_source_status: Dict[str, bool] = {}
        self.data_source_last_check: Dict[str, datetime] = {}

        # 统计开始时间
        self.start_time = datetime.utcnow()

    # ================================
    # 响应时间追踪
    # ================================

    def record_response_time(self, endpoint: str, duration: float):
        """
        记录响应时间

        Args:
            endpoint: 端点名称（如 "quick_chat", "deep_research"）
            duration: 响应时间（秒）
        """
        self.response_times[endpoint].append(duration)

    def get_response_time_percentiles(
        self,
        endpoint: str
    ) -> Dict[str, float]:
        """
        计算响应时间百分位数

        Args:
            endpoint: 端点名称

        Returns:
            Dict: 包含 P50/P95/P99/mean/min/max
        """
        samples = list(self.response_times.get(endpoint, []))

        if not samples:
            return {
                "p50": 0.0,
                "p95": 0.0,
                "p99": 0.0,
                "mean": 0.0,
                "min": 0.0,
                "max": 0.0,
                "count": 0,
            }

        sorted_samples = sorted(samples)
        count = len(sorted_samples)

        return {
            "p50": statistics.median(sorted_samples),
            "p95": sorted_samples[int(count * 0.95)] if count > 0 else 0.0,
            "p99": sorted_samples[int(count * 0.99)] if count > 0 else 0.0,
            "mean": statistics.mean(sorted_samples),
            "min": min(sorted_samples),
            "max": max(sorted_samples),
            "count": count,
        }

    def get_all_response_time_stats(self) -> Dict[str, Dict[str, float]]:
        """
        获取所有端点的响应时间统计

        Returns:
            Dict: 所有端点的百分位数统计
        """
        return {
            endpoint: self.get_response_time_percentiles(endpoint)
            for endpoint in self.response_times.keys()
        }

    # ================================
    # 缓存命中率追踪
    # ================================

    def record_cache_hit(self, cache_key: Optional[str] = None):
        """
        记录缓存命中

        Args:
            cache_key: 缓存键（可选，用于细粒度追踪）
        """
        self.counters["cache_hit_total"] += 1
        if cache_key:
            self.counters[f"cache_hit_{cache_key}"] += 1

    def record_cache_miss(self, cache_key: Optional[str] = None):
        """
        记录缓存未命中

        Args:
            cache_key: 缓存键（可选）
        """
        self.counters["cache_miss_total"] += 1
        if cache_key:
            self.counters[f"cache_miss_{cache_key}"] += 1

    def get_cache_hit_rate(self, cache_key: Optional[str] = None) -> float:
        """
        计算缓存命中率

        Args:
            cache_key: 缓存键（可选，如果提供则返回该键的命中率）

        Returns:
            float: 命中率（0.0-1.0）
        """
        if cache_key:
            hits = self.counters.get(f"cache_hit_{cache_key}", 0)
            misses = self.counters.get(f"cache_miss_{cache_key}", 0)
        else:
            hits = self.counters.get("cache_hit_total", 0)
            misses = self.counters.get("cache_miss_total", 0)

        total = hits + misses
        if total == 0:
            return 0.0

        return hits / total

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            Dict: 缓存命中率和请求数
        """
        hits = self.counters.get("cache_hit_total", 0)
        misses = self.counters.get("cache_miss_total", 0)
        total = hits + misses

        return {
            "hit_rate": self.get_cache_hit_rate(),
            "hits": hits,
            "misses": misses,
            "total_requests": total,
        }

    # ================================
    # API调用成功率追踪
    # ================================

    def record_api_success(self, api_name: str):
        """
        记录API调用成功

        Args:
            api_name: API名称（如 "coingecko", "etherscan"）
        """
        self.counters[f"api_success_{api_name}"] += 1
        self.counters["api_success_total"] += 1

    def record_api_failure(self, api_name: str):
        """
        记录API调用失败

        Args:
            api_name: API名称
        """
        self.counters[f"api_failure_{api_name}"] += 1
        self.counters["api_failure_total"] += 1

    def get_api_success_rate(self, api_name: Optional[str] = None) -> float:
        """
        计算API调用成功率

        Args:
            api_name: API名称（可选，如果提供则返回该API的成功率）

        Returns:
            float: 成功率（0.0-1.0）
        """
        if api_name:
            success = self.counters.get(f"api_success_{api_name}", 0)
            failure = self.counters.get(f"api_failure_{api_name}", 0)
        else:
            success = self.counters.get("api_success_total", 0)
            failure = self.counters.get("api_failure_total", 0)

        total = success + failure
        if total == 0:
            return 0.0

        return success / total

    def get_api_stats(self, api_name: Optional[str] = None) -> Dict[str, Any]:
        """
        获取API调用统计

        Args:
            api_name: API名称（可选）

        Returns:
            Dict: API成功率和调用次数
        """
        if api_name:
            success = self.counters.get(f"api_success_{api_name}", 0)
            failure = self.counters.get(f"api_failure_{api_name}", 0)
        else:
            success = self.counters.get("api_success_total", 0)
            failure = self.counters.get("api_failure_total", 0)

        total = success + failure

        return {
            "success_rate": self.get_api_success_rate(api_name),
            "success_count": success,
            "failure_count": failure,
            "total_calls": total,
        }

    def get_all_api_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有API的统计信息

        Returns:
            Dict: 所有API的成功率统计
        """
        api_names = set()
        for key in self.counters.keys():
            if key.startswith("api_success_") and not key.endswith("_total"):
                api_name = key.replace("api_success_", "")
                api_names.add(api_name)

        return {
            api_name: self.get_api_stats(api_name)
            for api_name in api_names
        }

    # ================================
    # 数据源可用性追踪
    # ================================

    def update_data_source_status(self, source_name: str, is_available: bool):
        """
        更新数据源状态

        Args:
            source_name: 数据源名称
            is_available: 是否可用
        """
        self.data_source_status[source_name] = is_available
        self.data_source_last_check[source_name] = datetime.utcnow()

        # 同时更新计数器
        if is_available:
            self.counters[f"data_source_up_{source_name}"] += 1
        else:
            self.counters[f"data_source_down_{source_name}"] += 1

    def get_data_source_availability(
        self,
        source_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取数据源可用性

        Args:
            source_name: 数据源名称（可选）

        Returns:
            Dict: 数据源状态和可用性百分比
        """
        if source_name:
            up_count = self.counters.get(f"data_source_up_{source_name}", 0)
            down_count = self.counters.get(f"data_source_down_{source_name}", 0)
            total = up_count + down_count

            return {
                "source": source_name,
                "current_status": self.data_source_status.get(source_name),
                "last_check": self.data_source_last_check.get(source_name),
                "availability": (up_count / total * 100) if total > 0 else 0.0,
                "up_count": up_count,
                "down_count": down_count,
            }
        else:
            # 返回所有数据源状态
            sources = set(self.data_source_status.keys())
            return {
                source: self.get_data_source_availability(source)
                for source in sources
            }

    # ================================
    # 预热任务统计（Phase 15）
    # ================================

    def get_prewarming_stats(self) -> Dict[str, Any]:
        """
        获取缓存预热任务统计

        Returns:
            Dict: 预热任务统计信息
        """
        # 高优先级任务统计
        high_executed = self.counters.get("prewarming_task_executed.priority:high", 0)
        high_failed = self.counters.get("prewarming_task_failed.priority:high", 0)

        # 中优先级任务统计
        medium_executed = self.counters.get("prewarming_task_executed.priority:medium", 0)
        medium_failed = self.counters.get("prewarming_task_failed.priority:medium", 0)

        # 热度更新统计
        hotness_updated = self.counters.get("hotness_scores_updated", 0)
        hotness_failed = self.counters.get("hotness_update_failed", 0)

        # 计算成功率
        total_executed = high_executed + medium_executed
        total_failed = high_failed + medium_failed
        total_tasks = total_executed + total_failed

        success_rate = (
            (total_executed / total_tasks * 100)
            if total_tasks > 0
            else 0.0
        )

        return {
            "success_rate": round(success_rate, 2),
            "high_priority": {
                "executed": high_executed,
                "failed": high_failed,
                "success_rate": (
                    (high_executed / (high_executed + high_failed) * 100)
                    if (high_executed + high_failed) > 0
                    else 0.0
                )
            },
            "medium_priority": {
                "executed": medium_executed,
                "failed": medium_failed,
                "success_rate": (
                    (medium_executed / (medium_executed + medium_failed) * 100)
                    if (medium_executed + medium_failed) > 0
                    else 0.0
                )
            },
            "hotness_updates": {
                "success": hotness_updated,
                "failed": hotness_failed,
                "success_rate": (
                    (hotness_updated / (hotness_updated + hotness_failed) * 100)
                    if (hotness_updated + hotness_failed) > 0
                    else 0.0
                )
            },
            "total_tasks": total_tasks
        }

    # ================================
    # 全局统计和导出
    # ================================

    def get_summary(self) -> Dict[str, Any]:
        """
        获取性能指标总览

        Returns:
            Dict: 完整的性能指标摘要
        """
        uptime = (datetime.utcnow() - self.start_time).total_seconds()

        return {
            "uptime_seconds": uptime,
            "response_times": self.get_all_response_time_stats(),
            "cache": self.get_cache_stats(),
            "api_calls": {
                "overall": self.get_api_stats(),
                "by_api": self.get_all_api_stats(),
            },
            "data_sources": self.get_data_source_availability(),
            "prewarming": self.get_prewarming_stats(),
            "timestamp": datetime.utcnow().isoformat(),
        }

    def reset(self):
        """重置所有指标"""
        self.response_times.clear()
        self.counters.clear()
        self.data_source_status.clear()
        self.data_source_last_check.clear()
        self.start_time = datetime.utcnow()


# ================================
# 全局实例
# ================================

metrics_collector = MetricsCollector()


# ================================
# 装饰器：自动追踪响应时间
# ================================

def track_response_time(endpoint_name: str):
    """
    装饰器：自动追踪函数响应时间

    Args:
        endpoint_name: 端点名称

    Example:
        @track_response_time("quick_chat")
        async def quick_chat(query: str):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start
                metrics_collector.record_response_time(endpoint_name, duration)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start
                metrics_collector.record_response_time(endpoint_name, duration)

        # 判断是否是异步函数
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# ================================
# 装饰器：自动追踪API调用
# ================================

def track_api_call(api_name: str):
    """
    装饰器：自动追踪API调用成功率

    Args:
        api_name: API名称

    Example:
        @track_api_call("coingecko")
        async def get_coin_data(coin_id: str):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs)
                metrics_collector.record_api_success(api_name)
                return result
            except Exception as e:
                metrics_collector.record_api_failure(api_name)
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                metrics_collector.record_api_success(api_name)
                return result
            except Exception as e:
                metrics_collector.record_api_failure(api_name)
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# ================================
# 便捷函数
# ================================

def get_metrics_summary() -> Dict[str, Any]:
    """
    便捷函数：获取性能指标总览

    Returns:
        Dict: 完整的性能指标摘要
    """
    return metrics_collector.get_summary()


def reset_metrics():
    """便捷函数：重置所有指标"""
    metrics_collector.reset()
