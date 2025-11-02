"""
OpenTelemetry配置和分布式追踪
提供高级APM功能和分布式追踪能力
"""
import logging
from typing import Optional, Dict, Any
import os
from contextlib import contextmanager

from app.core.config import settings

logger = logging.getLogger(__name__)

# 全局OpenTelemetry实例
_tracer_provider = None
_meter_provider = None


def init_opentelemetry():
    """
    初始化OpenTelemetry
    包括追踪、指标和日志的集成
    """
    global _tracer_provider, _meter_provider
    
    # 检查是否启用OpenTelemetry
    if not settings.ENVIRONMENT in ("production", "staging", "stage"):
        logger.info("⚠️ OpenTelemetry disabled in development environment")
        return
    
    try:
        from opentelemetry import trace, metrics
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        from opentelemetry.instrumentation.redis import RedisInstrumentor
        from opentelemetry.propagate import set_global_textmap
        from opentelemetry.propagators.b3 import B3MultiFormat
        from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION, DEPLOYMENT_ENVIRONMENT
        
        # 创建资源标识
        resource = Resource.create({
            SERVICE_NAME: "web3search-api",
            SERVICE_VERSION: settings.API_VERSION or "1.0.0",
            DEPLOYMENT_ENVIRONMENT: settings.ENVIRONMENT,
        })
        
        # 配置追踪
        _tracer_provider = TracerProvider(resource=resource)
        
        # 配置OTLP导出器（发送到Sentry或其他兼容的后端）
        otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
        span_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
        span_processor = BatchSpanProcessor(span_exporter)
        _tracer_provider.add_span_processor(span_processor)
        
        # 设置全局追踪提供者
        trace.set_tracer_provider(_tracer_provider)
        
        # 配置指标
        _meter_provider = MeterProvider(resource=resource)
        metric_reader = PeriodicExportingMetricReader(
            exporter=OTLPMetricExporter(endpoint=otlp_endpoint),
            export_interval_millis=30000,  # 30秒导出一次
        )
        _meter_provider.register_metric_reader(metric_reader)
        metrics.set_meter_provider(_meter_provider)
        
        # 配置传播器（用于分布式追踪上下文传播）
        set_global_textmap(B3MultiFormat())
        
        # 自动instrumentation
        FastAPIInstrumentor().instrument()
        HTTPXClientInstrumentor().instrument()
        SQLAlchemyInstrumentor().instrument()
        RedisInstrumentor().instrument()
        
        logger.info(f"✅ OpenTelemetry initialized: environment={settings.ENVIRONMENT}")
        
    except ImportError as e:
        logger.warning(f"⚠️ OpenTelemetry packages not installed: {e}")
    except Exception as e:
        logger.error(f"❌ Failed to initialize OpenTelemetry: {e}")


def get_tracer(name: str = __name__):
    """
    获取追踪器
    
    Args:
        name: 追踪器名称
        
    Returns:
        OpenTelemetry追踪器
    """
    try:
        from opentelemetry import trace
        return trace.get_tracer(name)
    except ImportError:
        return None


def get_meter(name: str = __name__):
    """
    获取指标收集器
    
    Args:
        name: 指标收集器名称
        
    Returns:
        OpenTelemetry指标收集器
    """
    try:
        from opentelemetry import metrics
        return metrics.get_meter(name)
    except ImportError:
        return None


@contextmanager
def trace_span(name: str, attributes: Optional[Dict[str, Any]] = None):
    """
    创建追踪span
    
    Usage:
        with trace_span("api_call", {"endpoint": "/api/v1/chat"}):
            # 执行操作
            result = await some_function()
    
    Args:
        name: span名称
        attributes: 属性字典
    """
    tracer = get_tracer()
    if not tracer:
        yield None
        return
    
    with tracer.start_as_current_span(name) as span:
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, str(value))
        yield span


def record_counter(name: str, value: int = 1, attributes: Optional[Dict[str, Any]] = None):
    """
    记录计数器指标
    
    Args:
        name: 指标名称
        value: 增加值（默认1）
        attributes: 属性
    """
    meter = get_meter()
    if not meter:
        return
    
    try:
        counter = meter.create_counter(name)
        counter.add(value, attributes or {})
    except Exception as e:
        logger.warning(f"Failed to record counter {name}: {e}")


def record_histogram(name: str, value: float, attributes: Optional[Dict[str, Any]] = None):
    """
    记录直方图指标（用于响应时间等）
    
    Args:
        name: 指标名称
        value: 指标值
        attributes: 属性
    """
    meter = get_meter()
    if not meter:
        return
    
    try:
        histogram = meter.create_histogram(name, "ms")
        histogram.record(value, attributes or {})
    except Exception as e:
        logger.warning(f"Failed to record histogram {name}: {e}")


def record_gauge(name: str, value: float, attributes: Optional[Dict[str, Any]] = None):
    """
    记录仪表指标（用于当前值监控）
    
    Args:
        name: 指标名称
        value: 指标值
        attributes: 属性
    """
    meter = get_meter()
    if not meter:
        return
    
    try:
        gauge = meter.create_up_down_counter(name)
        gauge.add(value, attributes or {})
    except Exception as e:
        logger.warning(f"Failed to record gauge {name}: {e}")


class OpenTelemetryAPM:
    """
    OpenTelemetry APM收集器
    提供高级应用性能监控功能
    """
    
    def __init__(self):
        self.tracer = get_tracer("web3search.apm")
        self.meter = get_meter("web3search.apm")
        
        # 预定义指标
        self._setup_metrics()
    
    def _setup_metrics(self):
        """设置预定义指标"""
        if not self.meter:
            return
        
        try:
            # API调用指标
            self.api_duration = self.meter.create_histogram(
                "api_request_duration",
                "ms",
                "API请求响应时间"
            )
            self.api_counter = self.meter.create_counter(
                "api_requests_total",
                "API请求总数"
            )
            
            # 数据库指标
            self.db_duration = self.meter.create_histogram(
                "db_query_duration",
                "ms",
                "数据库查询时间"
            )
            self.db_counter = self.meter.create_counter(
                "db_queries_total",
                "数据库查询总数"
            )
            
            # 外部API指标
            self.external_duration = self.meter.create_histogram(
                "external_api_duration",
                "ms",
                "外部API调用时间"
            )
            self.external_counter = self.meter.create_counter(
                "external_api_calls_total",
                "外部API调用总数"
            )
            
            # 缓存指标
            self.cache_duration = self.meter.create_histogram(
                "cache_operation_duration",
                "ms",
                "缓存操作时间"
            )
            self.cache_counter = self.meter.create_counter(
                "cache_operations_total",
                "缓存操作总数"
            )
            
            # 系统资源指标
            self.memory_usage = self.meter.create_up_down_counter(
                "memory_usage_bytes",
                "内存使用量（字节）"
            )
            self.cpu_usage = self.meter.create_histogram(
                "cpu_usage_percent",
                "percent",
                "CPU使用率"
            )
            
        except Exception as e:
            logger.warning(f"Failed to setup OpenTelemetry metrics: {e}")
    
    def trace_api_request(self, endpoint: str, method: str):
        """
        追踪API请求
        
        Args:
            endpoint: API端点
            method: HTTP方法
        """
        if not self.tracer:
            return trace_span(f"api.{method.lower()}{endpoint}")
        
        return self.tracer.start_as_current_span(f"api.{method.lower()}{endpoint}")
    
    def record_api_metric(self, endpoint: str, method: str, status_code: int, duration_ms: float):
        """
        记录API指标
        
        Args:
            endpoint: API端点
            method: HTTP方法
            status_code: 状态码
            duration_ms: 响应时间
        """
        attributes = {
            "endpoint": endpoint,
            "method": method,
            "status_code": str(status_code)
        }
        
        if self.api_duration:
            self.api_duration.record(duration_ms, attributes)
        if self.api_counter:
            self.api_counter.add(1, attributes)
    
    def record_db_metric(self, table: str, operation: str, duration_ms: float, rows: int = 0):
        """
        记录数据库指标
        
        Args:
            table: 表名
            operation: 操作类型
            duration_ms: 执行时间
            rows: 影响行数
        """
        attributes = {
            "table": table,
            "operation": operation
        }
        
        if self.db_duration:
            self.db_duration.record(duration_ms, attributes)
        if self.db_counter:
            self.db_counter.add(1, attributes)
    
    def record_external_api_metric(self, service: str, endpoint: str, status_code: int, duration_ms: float):
        """
        记录外部API指标
        
        Args:
            service: 服务名
            endpoint: API端点
            status_code: 状态码
            duration_ms: 响应时间
        """
        attributes = {
            "service": service,
            "endpoint": endpoint,
            "status_code": str(status_code)
        }
        
        if self.external_duration:
            self.external_duration.record(duration_ms, attributes)
        if self.external_counter:
            self.external_counter.add(1, attributes)
    
    def record_cache_metric(self, level: str, operation: str, hit: bool, duration_ms: float):
        """
        记录缓存指标
        
        Args:
            level: 缓存级别
            operation: 操作类型
            hit: 是否命中
            duration_ms: 操作时间
        """
        attributes = {
            "level": level,
            "operation": operation,
            "hit": str(hit)
        }
        
        if self.cache_duration:
            self.cache_duration.record(duration_ms, attributes)
        if self.cache_counter:
            self.cache_counter.add(1, attributes)
    
    def record_system_metrics(self, memory_bytes: float, cpu_percent: float):
        """
        记录系统资源指标
        
        Args:
            memory_bytes: 内存使用量（字节）
            cpu_percent: CPU使用率
        """
        if self.memory_usage:
            self.memory_usage.record(memory_bytes, {"component": "web3search"})
        if self.cpu_usage:
            self.cpu_usage.record(cpu_percent, {"component": "web3search"})


# 全局APM实例
otel_apm = OpenTelemetryAPM()
