"""
Prompt监控系统（任务 12.5）

功能：
1. 生成质量监控
2. Token消耗追踪
3. 响应时间监控
4. 错误率统计
5. 实时指标仪表板数据
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
import logging
import time
from enum import Enum

logger = logging.getLogger(__name__)


# ================================
# 监控指标类型
# ================================

class MetricType(str, Enum):
    """指标类型"""
    QUALITY_SCORE = "quality_score"  # 质量得分
    TOKEN_COUNT = "token_count"  # Token数量
    RESPONSE_TIME = "response_time"  # 响应时间（ms）
    ERROR_RATE = "error_rate"  # 错误率
    REQUEST_COUNT = "request_count"  # 请求数


# ================================
# 监控事件
# ================================

@dataclass
class PromptEvent:
    """Prompt事件"""
    prompt_name: str  # Prompt名称
    prompt_version: str  # 版本号
    timestamp: datetime
    quality_score: Optional[float] = None  # 质量得分（0-1）
    token_count: int = 0  # Token数
    response_time_ms: float = 0.0  # 响应时间
    success: bool = True  # 是否成功
    error_message: Optional[str] = None  # 错误信息
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AggregatedMetrics:
    """聚合指标"""
    prompt_name: str
    time_window: str  # 时间窗口（如"1h", "24h"）
    total_requests: int
    successful_requests: int
    failed_requests: int
    error_rate: float
    avg_quality_score: float
    avg_token_count: float
    avg_response_time_ms: float
    p50_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "prompt_name": self.prompt_name,
            "time_window": self.time_window,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "error_rate": self.error_rate,
            "avg_quality_score": self.avg_quality_score,
            "avg_token_count": self.avg_token_count,
            "avg_response_time_ms": self.avg_response_time_ms,
            "p50_response_time_ms": self.p50_response_time_ms,
            "p95_response_time_ms": self.p95_response_time_ms,
            "p99_response_time_ms": self.p99_response_time_ms,
            "timestamp": self.timestamp.isoformat()
        }


# ================================
# 时间窗口管理
# ================================

class TimeWindow:
    """时间窗口"""

    def __init__(self, window_size: timedelta, max_events: int = 10000):
        """
        初始化时间窗口

        Args:
            window_size: 窗口大小
            max_events: 最大事件数
        """
        self.window_size = window_size
        self.events: deque = deque(maxlen=max_events)

    def add_event(self, event: PromptEvent):
        """添加事件"""
        self.events.append(event)

    def get_events(self, since: Optional[datetime] = None) -> List[PromptEvent]:
        """
        获取时间窗口内的事件

        Args:
            since: 起始时间（默认为当前时间-窗口大小）

        Returns:
            List[PromptEvent]: 事件列表
        """
        if since is None:
            since = datetime.utcnow() - self.window_size

        return [e for e in self.events if e.timestamp >= since]

    def clear_old_events(self):
        """清理过期事件"""
        cutoff = datetime.utcnow() - self.window_size
        while self.events and self.events[0].timestamp < cutoff:
            self.events.popleft()


# ================================
# 监控器
# ================================

class PromptMonitor:
    """Prompt监控器"""

    def __init__(self):
        """初始化监控器"""
        # 时间窗口：1小时、24小时
        self.window_1h = TimeWindow(timedelta(hours=1))
        self.window_24h = TimeWindow(timedelta(hours=24))

        # 按prompt名称分组的窗口
        self.prompt_windows: Dict[str, TimeWindow] = {}

        # 实时计数器
        self.total_requests = 0
        self.total_errors = 0
        self.total_tokens = 0

    def track_event(self, event: PromptEvent):
        """
        追踪事件

        Args:
            event: Prompt事件
        """
        # 添加到全局窗口
        self.window_1h.add_event(event)
        self.window_24h.add_event(event)

        # 添加到prompt特定窗口
        if event.prompt_name not in self.prompt_windows:
            self.prompt_windows[event.prompt_name] = TimeWindow(timedelta(hours=24))

        self.prompt_windows[event.prompt_name].add_event(event)

        # 更新计数器
        self.total_requests += 1
        if not event.success:
            self.total_errors += 1
        self.total_tokens += event.token_count

        # 定期清理
        if self.total_requests % 100 == 0:
            self._cleanup()

    def get_metrics(
        self,
        prompt_name: Optional[str] = None,
        time_window: str = "1h"
    ) -> AggregatedMetrics:
        """
        获取聚合指标

        Args:
            prompt_name: Prompt名称（None表示所有）
            time_window: 时间窗口（"1h" 或 "24h"）

        Returns:
            AggregatedMetrics: 聚合指标
        """
        # 选择时间窗口
        if time_window == "1h":
            window = self.window_1h
        else:
            window = self.window_24h

        # 获取事件
        if prompt_name:
            # 特定prompt的事件
            prompt_window = self.prompt_windows.get(prompt_name)
            if not prompt_window:
                # 返回空指标
                return self._empty_metrics(prompt_name, time_window)
            events = prompt_window.get_events()
        else:
            # 所有事件
            events = window.get_events()
            prompt_name = "all"

        # 计算指标
        return self._compute_metrics(events, prompt_name, time_window)

    def _compute_metrics(
        self,
        events: List[PromptEvent],
        prompt_name: str,
        time_window: str
    ) -> AggregatedMetrics:
        """计算聚合指标"""
        if not events:
            return self._empty_metrics(prompt_name, time_window)

        total = len(events)
        successful = sum(1 for e in events if e.success)
        failed = total - successful
        error_rate = failed / total if total > 0 else 0.0

        # 质量得分
        quality_scores = [e.quality_score for e in events if e.quality_score is not None]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0

        # Token数
        avg_tokens = sum(e.token_count for e in events) / total if total > 0 else 0.0

        # 响应时间
        response_times = [e.response_time_ms for e in events]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0.0

        # 百分位数
        sorted_times = sorted(response_times)
        p50 = self._percentile(sorted_times, 50)
        p95 = self._percentile(sorted_times, 95)
        p99 = self._percentile(sorted_times, 99)

        return AggregatedMetrics(
            prompt_name=prompt_name,
            time_window=time_window,
            total_requests=total,
            successful_requests=successful,
            failed_requests=failed,
            error_rate=error_rate,
            avg_quality_score=avg_quality,
            avg_token_count=avg_tokens,
            avg_response_time_ms=avg_response_time,
            p50_response_time_ms=p50,
            p95_response_time_ms=p95,
            p99_response_time_ms=p99,
            timestamp=datetime.utcnow()
        )

    def _empty_metrics(self, prompt_name: str, time_window: str) -> AggregatedMetrics:
        """空指标"""
        return AggregatedMetrics(
            prompt_name=prompt_name,
            time_window=time_window,
            total_requests=0,
            successful_requests=0,
            failed_requests=0,
            error_rate=0.0,
            avg_quality_score=0.0,
            avg_token_count=0.0,
            avg_response_time_ms=0.0,
            p50_response_time_ms=0.0,
            p95_response_time_ms=0.0,
            p99_response_time_ms=0.0,
            timestamp=datetime.utcnow()
        )

    @staticmethod
    def _percentile(sorted_list: List[float], percentile: int) -> float:
        """计算百分位数"""
        if not sorted_list:
            return 0.0

        k = (len(sorted_list) - 1) * percentile / 100
        f = int(k)
        c = f + 1

        if c >= len(sorted_list):
            return sorted_list[-1]

        d0 = sorted_list[f] * (c - k)
        d1 = sorted_list[c] * (k - f)
        return d0 + d1

    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        获取仪表板数据

        Returns:
            Dict[str, Any]: 仪表板数据
        """
        # 全局指标
        metrics_1h = self.get_metrics(time_window="1h")
        metrics_24h = self.get_metrics(time_window="24h")

        # 每个prompt的指标
        prompt_metrics = {}
        for prompt_name in self.prompt_windows.keys():
            prompt_metrics[prompt_name] = self.get_metrics(
                prompt_name=prompt_name,
                time_window="1h"
            ).to_dict()

        return {
            "global": {
                "1h": metrics_1h.to_dict(),
                "24h": metrics_24h.to_dict()
            },
            "by_prompt": prompt_metrics,
            "counters": {
                "total_requests": self.total_requests,
                "total_errors": self.total_errors,
                "total_tokens": self.total_tokens
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    def get_alerts(self) -> List[Dict[str, Any]]:
        """
        获取告警信息

        Returns:
            List[Dict[str, Any]]: 告警列表
        """
        alerts = []

        # 检查错误率
        metrics = self.get_metrics(time_window="1h")
        if metrics.error_rate > 0.05:  # 5%阈值
            alerts.append({
                "type": "high_error_rate",
                "severity": "warning",
                "message": f"错误率过高：{metrics.error_rate:.1%}",
                "threshold": 0.05,
                "actual": metrics.error_rate
            })

        # 检查响应时间
        if metrics.p95_response_time_ms > 3000:  # 3秒阈值
            alerts.append({
                "type": "slow_response",
                "severity": "warning",
                "message": f"P95响应时间过长：{metrics.p95_response_time_ms:.0f}ms",
                "threshold": 3000,
                "actual": metrics.p95_response_time_ms
            })

        # 检查质量得分
        if 0 < metrics.avg_quality_score < 0.6:  # 60%阈值
            alerts.append({
                "type": "low_quality",
                "severity": "warning",
                "message": f"平均质量得分偏低：{metrics.avg_quality_score:.2f}",
                "threshold": 0.6,
                "actual": metrics.avg_quality_score
            })

        return alerts

    def _cleanup(self):
        """清理过期事件"""
        self.window_1h.clear_old_events()
        self.window_24h.clear_old_events()

        for window in self.prompt_windows.values():
            window.clear_old_events()


# ================================
# 监控装饰器
# ================================

def monitor_prompt(prompt_name: str, prompt_version: str = "unknown"):
    """
    监控装饰器

    用法：
        @monitor_prompt("quick_chat", "v1.0.0")
        def generate_response(query):
            ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            error_message = None
            result = None

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error_message = str(e)
                raise
            finally:
                # 计算响应时间
                response_time = (time.time() - start_time) * 1000  # ms

                # 创建事件
                event = PromptEvent(
                    prompt_name=prompt_name,
                    prompt_version=prompt_version,
                    timestamp=datetime.utcnow(),
                    response_time_ms=response_time,
                    success=success,
                    error_message=error_message
                )

                # 追踪
                prompt_monitor.track_event(event)

        return wrapper
    return decorator


# ================================
# 全局实例
# ================================

prompt_monitor = PromptMonitor()


# ================================
# 便捷函数
# ================================

def track_prompt_usage(
    prompt_name: str,
    prompt_version: str,
    quality_score: Optional[float] = None,
    token_count: int = 0,
    response_time_ms: float = 0.0,
    success: bool = True,
    error_message: Optional[str] = None
):
    """
    便捷函数：追踪Prompt使用

    Args:
        prompt_name: Prompt名称
        prompt_version: 版本号
        quality_score: 质量得分
        token_count: Token数
        response_time_ms: 响应时间
        success: 是否成功
        error_message: 错误信息
    """
    event = PromptEvent(
        prompt_name=prompt_name,
        prompt_version=prompt_version,
        timestamp=datetime.utcnow(),
        quality_score=quality_score,
        token_count=token_count,
        response_time_ms=response_time_ms,
        success=success,
        error_message=error_message
    )

    prompt_monitor.track_event(event)


def get_monitoring_dashboard() -> Dict[str, Any]:
    """
    便捷函数：获取监控仪表板

    Returns:
        Dict[str, Any]: 仪表板数据
    """
    return prompt_monitor.get_dashboard_data()


def get_monitoring_alerts() -> List[Dict[str, Any]]:
    """
    便捷函数：获取监控告警

    Returns:
        List[Dict[str, Any]]: 告警列表
    """
    return prompt_monitor.get_alerts()
