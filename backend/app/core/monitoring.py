"""
监控和追踪
Sentry错误追踪和性能监控
"""
import logging
from typing import Optional, Dict, Any
from contextlib import contextmanager
import time

from app.core.config import settings

logger = logging.getLogger(__name__)


# ================================
# Sentry集成
# ================================


def init_sentry():
    """
    初始化Sentry错误追踪

    需要设置环境变量:
    - SENTRY_DSN: Sentry项目的DSN
    - ENVIRONMENT: 环境名称（development/staging/production）
    """
    sentry_dsn = getattr(settings, "SENTRY_DSN", None)

    if not sentry_dsn:
        logger.info("⚠️ Sentry DSN not configured, skipping initialization")
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        from sentry_sdk.integrations.redis import RedisIntegration
        from sentry_sdk.integrations.celery import CeleryIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration

        # 配置Sentry
        sentry_sdk.init(
            dsn=sentry_dsn,
            environment=settings.ENVIRONMENT,
            release=settings.API_VERSION,
            # 集成
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                SqlalchemyIntegration(),
                RedisIntegration(),
                CeleryIntegration(),
                LoggingIntegration(
                    level=logging.INFO,  # 捕获INFO及以上级别的日志
                    event_level=logging.ERROR,  # 将ERROR及以上级别作为事件发送
                ),
            ],
            # 性能监控 - 扩展APM配置
            traces_sample_rate=get_traces_sample_rate(),
            # 错误采样（生产环境采样以节省配额）
            sample_rate=get_error_sample_rate(),
            # 过滤
            before_send=before_send_filter,
            before_breadcrumb=before_breadcrumb_filter,
            # 配置
            max_breadcrumbs=50,
            attach_stacktrace=True,
            send_default_pii=False,  # 不发送个人身份信息
            # APM性能监控扩展配置
            enable_tracing=True,
            trace_propagation_targets=[
                "openrouter.ai",
                "api.coingecko.com",
                "api.etherscan.io",
                "api.bscscan.com"
            ],
            # 分布式追踪配置
            instrumenter="otel",  # 使用OpenTelemetry作为instrumenter
        )

        logger.info(f"✅ Sentry initialized: environment={settings.ENVIRONMENT}")

    except ImportError:
        logger.warning("⚠️ sentry-sdk not installed, skipping Sentry initialization")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Sentry: {e}")


def get_traces_sample_rate() -> float:
    """
    根据环境和配置动态获取性能追踪采样率
    
    Returns:
        采样率 (0.0-1.0)
    """
    env = settings.ENVIRONMENT.lower()
    
    if env == "production":
        return 0.1  # 生产环境10%采样率
    elif env in ("staging", "stage"):
        return 0.5  # 预发布环境50%采样率
    else:
        return 1.0  # 开发环境100%采样率


def get_error_sample_rate() -> float:
    """
    根据环境和配置动态获取错误采样率
    
    Returns:
        采样率 (0.0-1.0)
    """
    env = settings.ENVIRONMENT.lower()
    
    if env == "production":
        return 0.5  # 生产环境50%错误采样
    elif env in ("staging", "stage"):
        return 0.8  # 预发布环境80%错误采样
    else:
        return 1.0  # 开发环境100%错误采样


def before_breadcrumb_filter(breadcrumb: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Sentry面包屑过滤器
    用于过滤或 enrich 面包屑数据
    
    Args:
        breadcrumb: Sentry面包屑
        hint: 额外信息
    
    Returns:
        处理后的面包屑，或None（跳过该面包屑）
    """
    # 过滤掉一些不重要的面包屑
    if breadcrumb.get("category") == "http":
        url = breadcrumb.get("data", {}).get("url", "")
        # 过滤健康检查端点
        if "/health" in url or "/metrics" in url:
            return None
    
    # enrich面包屑数据
    if breadcrumb.get("category") == "http":
        # 添加响应时间信息
        if "duration_ms" not in breadcrumb.get("data", {}):
            breadcrumb.setdefault("data", {})["duration_ms"] = "unknown"
    
    return breadcrumb


def before_send_filter(event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Sentry事件过滤器
    用于过滤不需要上报的事件

    Args:
        event: Sentry事件
        hint: 额外信息

    Returns:
        处理后的事件，或None（跳过该事件）
    """
    # 过滤健康检查端点的错误
    if "request" in event:
        url = event.get("request", {}).get("url", "")
        if "/health" in url:
            return None

    # 过滤某些异常类型
    if "exc_info" in hint:
        exc_type, exc_value, tb = hint["exc_info"]
        # 过滤KeyboardInterrupt（用户主动中断）
        if exc_type.__name__ == "KeyboardInterrupt":
            return None

    return event


# ================================
# 性能追踪
# ================================


@contextmanager
def trace_operation(operation_name: str, tags: Optional[Dict[str, Any]] = None):
    """
    追踪操作性能

    Usage:
        with trace_operation("fetch_market_data", {"symbol": "BTC"}):
            data = await fetch_data()

    Args:
        operation_name: 操作名称
        tags: 标签
    """
    start_time = time.time()

    try:
        # Sentry性能追踪
        try:
            import sentry_sdk

            with sentry_sdk.start_span(op=operation_name, description=operation_name) as span:
                if tags:
                    for key, value in tags.items():
                        span.set_tag(key, str(value))
                yield span
        except ImportError:
            yield None

    finally:
        duration = time.time() - start_time
        logger.debug(
            f"Operation '{operation_name}' completed in {duration*1000:.2f}ms",
            extra={"operation": operation_name, "duration_ms": round(duration * 1000, 2), "tags": tags},
        )


def capture_exception(exception: Exception, extra: Optional[Dict[str, Any]] = None):
    """
    手动捕获异常并发送到Sentry

    Args:
        exception: 异常对象
        extra: 额外信息
    """
    try:
        import sentry_sdk

        with sentry_sdk.push_scope() as scope:
            if extra:
                for key, value in extra.items():
                    scope.set_extra(key, value)

            sentry_sdk.capture_exception(exception)
    except ImportError:
        pass

    logger.error(f"Exception captured: {exception}", extra=extra, exc_info=True)


def capture_message(message: str, level: str = "info", extra: Optional[Dict[str, Any]] = None):
    """
    手动发送消息到Sentry

    Args:
        message: 消息内容
        level: 日志级别（debug/info/warning/error/fatal）
        extra: 额外信息
    """
    try:
        import sentry_sdk

        with sentry_sdk.push_scope() as scope:
            if extra:
                for key, value in extra.items():
                    scope.set_extra(key, value)

            sentry_sdk.capture_message(message, level=level)
    except ImportError:
        pass

    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.log(log_level, message, extra=extra)


# ================================
# 指标记录
# ================================


class MetricsCollector:
    """
    指标收集器
    用于收集和记录关键业务指标
    """

    def __init__(self):
        self.logger = logging.getLogger("metrics")

    def record_api_call(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        duration: float,
        user_id: Optional[str] = None,
    ):
        """
        记录API调用指标

        Args:
            endpoint: 端点路径
            method: HTTP方法
            status_code: 状态码
            duration: 响应时间（秒）
            user_id: 用户ID（可选）
        """
        metric = {
            "metric": "api_call",
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "duration_ms": round(duration * 1000, 2),
            "user_id": user_id,
        }

        self.logger.info("API call metric", extra=metric)

        # 发送到Sentry
        try:
            import sentry_sdk

            sentry_sdk.set_measurement(f"api.{endpoint}.duration", duration * 1000, "millisecond")
        except ImportError:
            pass

    def record_error(
        self,
        error_type: str,
        error_message: str,
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        记录错误指标

        Args:
            error_type: 错误类型
            error_message: 错误消息
            context: 上下文信息
        """
        metric = {
            "metric": "error",
            "error_type": error_type,
            "error_message": error_message,
            "context": context or {},
        }

        self.logger.error("Error metric", extra=metric)

    def record_llm_call(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        duration: float,
        success: bool = True,
    ):
        """
        记录LLM调用指标

        Args:
            model: 模型名称
            prompt_tokens: Prompt token数
            completion_tokens: 生成token数
            duration: 调用时间（秒）
            success: 是否成功
        """
        metric = {
            "metric": "llm_call",
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "duration_ms": round(duration * 1000, 2),
            "success": success,
        }

        self.logger.info("LLM call metric", extra=metric)

        # 发送到Sentry
        try:
            import sentry_sdk

            sentry_sdk.set_measurement(f"llm.{model}.duration", duration * 1000, "millisecond")
            sentry_sdk.set_measurement(f"llm.{model}.tokens", prompt_tokens + completion_tokens, "none")
        except ImportError:
            pass

    def record_data_collection(
        self,
        source: str,
        success: bool,
        duration: float,
        records_count: int = 0,
    ):
        """
        记录数据采集指标

        Args:
            source: 数据源名称
            success: 是否成功
            duration: 采集时间（秒）
            records_count: 采集记录数
        """
        metric = {
            "metric": "data_collection",
            "source": source,
            "success": success,
            "duration_ms": round(duration * 1000, 2),
            "records_count": records_count,
        }

        self.logger.info("Data collection metric", extra=metric)

    def record_user_action(
        self,
        action_type: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        记录用户行为（任务13.7）

        Args:
            action_type: 行为类型（search, report_generated, export等）
            user_id: 用户ID
            metadata: 额外元数据
        """
        metric = {
            "metric": "user_action",
            "action_type": action_type,
            "user_id": user_id,
            "metadata": metadata or {},
        }

        self.logger.info("User action metric", extra=metric)

        # 发送自定义事件到Sentry
        try:
            import sentry_sdk
            sentry_sdk.capture_message(
                f"User action: {action_type}",
                level="info",
                extras=metric
            )
        except ImportError:
            pass

    def record_report_generation(
        self,
        symbol: str,
        report_type: str,
        success: bool,
        duration: float,
        sections_count: int = 0,
    ):
        """
        记录报告生成（任务13.7）

        Args:
            symbol: 加密货币符号
            report_type: 报告类型（quick/deep）
            success: 是否成功
            duration: 生成时间（秒）
            sections_count: 章节数
        """
        metric = {
            "metric": "report_generation",
            "symbol": symbol,
            "report_type": report_type,
            "success": success,
            "duration_ms": round(duration * 1000, 2),
            "sections_count": sections_count,
        }

        self.logger.info("Report generation metric", extra=metric)

        # 发送到Sentry
        try:
            import sentry_sdk
            sentry_sdk.set_measurement(f"report.{report_type}.duration", duration * 1000, "millisecond")
            sentry_sdk.set_measurement(f"report.{report_type}.sections", sections_count, "none")
        except ImportError:
            pass

    def record_cache_operation(
        self,
        operation: str,
        hit: bool,
        key: str,
        duration_ms: float = 0.0,
    ):
        """
        记录缓存操作（任务13.7）

        Args:
            operation: 操作类型（get, set, delete）
            hit: 是否命中（对于get操作）
            key: 缓存键
            duration_ms: 操作耗时
        """
        metric = {
            "metric": "cache_operation",
            "operation": operation,
            "hit": hit,
            "key": key,
            "duration_ms": duration_ms,
        }

        self.logger.debug("Cache operation metric", extra=metric)


class APMCollector:
    """
    APM性能指标收集器
    专门用于收集应用性能监控数据
    """
    
    def __init__(self):
        self.logger = logging.getLogger("apm")
    
    def record_database_performance(
        self,
        query_type: str,
        table_name: str,
        duration_ms: float,
        rows_affected: int = 0,
        success: bool = True
    ):
        """
        记录数据库性能指标
        
        Args:
            query_type: 查询类型 (SELECT, INSERT, UPDATE, DELETE)
            table_name: 表名
            duration_ms: 执行时间（毫秒）
            rows_affected: 影响行数
            success: 是否成功
        """
        metric = {
            "metric": "database_performance",
            "query_type": query_type,
            "table_name": table_name,
            "duration_ms": round(duration_ms, 2),
            "rows_affected": rows_affected,
            "success": success
        }
        
        self.logger.info("Database performance metric", extra=metric)
        
        # 发送到Sentry
        try:
            import sentry_sdk
            sentry_sdk.set_measurement(
                f"db.{table_name}.{query_type.lower()}.duration", 
                duration_ms, 
                "millisecond"
            )
            if rows_affected > 0:
                sentry_sdk.set_measurement(
                    f"db.{table_name}.{query_type.lower()}.rows", 
                    rows_affected, 
                    "none"
                )
        except ImportError:
            pass
    
    def record_external_api_call(
        self,
        service_name: str,
        endpoint: str,
        method: str,
        status_code: int,
        duration_ms: float,
        response_size_bytes: int = 0
    ):
        """
        记录外部API调用性能
        
        Args:
            service_name: 服务名称 (OpenRouter, CoinGecko, Etherscan等)
            endpoint: API端点
            method: HTTP方法
            status_code: 响应状态码
            duration_ms: 响应时间（毫秒）
            response_size_bytes: 响应大小（字节）
        """
        metric = {
            "metric": "external_api_call",
            "service_name": service_name,
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "duration_ms": round(duration_ms, 2),
            "response_size_bytes": response_size_bytes
        }
        
        self.logger.info("External API call metric", extra=metric)
        
        # 发送到Sentry
        try:
            import sentry_sdk
            sentry_sdk.set_measurement(
                f"external.{service_name.lower()}.duration", 
                duration_ms, 
                "millisecond"
            )
            sentry_sdk.set_measurement(
                f"external.{service_name.lower()}.response_size", 
                response_size_bytes, 
                "byte"
            )
        except ImportError:
            pass
    
    def record_cache_performance(
        self,
        cache_level: str,  # L1, L2
        operation: str,    # get, set, delete
        hit: bool,
        key_pattern: str,
        duration_ms: float = 0.0
    ):
        """
        记录缓存性能指标
        
        Args:
            cache_level: 缓存级别 (L1, L2)
            operation: 操作类型
            hit: 是否命中（对于get操作）
            key_pattern: 键模式
            duration_ms: 操作耗时
        """
        metric = {
            "metric": "cache_performance",
            "cache_level": cache_level,
            "operation": operation,
            "hit": hit,
            "key_pattern": key_pattern,
            "duration_ms": round(duration_ms, 2)
        }
        
        self.logger.debug("Cache performance metric", extra=metric)
        
        # 发送到Sentry
        try:
            import sentry_sdk
            sentry_sdk.set_measurement(
                f"cache.{cache_level.lower()}.{operation}.duration", 
                duration_ms, 
                "millisecond"
            )
            if operation == "get":
                sentry_sdk.set_measurement(
                    f"cache.{cache_level.lower()}.hit_rate", 
                    1.0 if hit else 0.0, 
                    "ratio"
                )
        except ImportError:
            pass
    
    def record_memory_usage(
        self,
        component: str,
        memory_mb: float,
        memory_type: str = "rss"  # rss, vms, shared
    ):
        """
        记录内存使用情况
        
        Args:
            component: 组件名称
            memory_mb: 内存使用量（MB）
            memory_type: 内存类型
        """
        metric = {
            "metric": "memory_usage",
            "component": component,
            "memory_mb": round(memory_mb, 2),
            "memory_type": memory_type
        }
        
        self.logger.info("Memory usage metric", extra=metric)
        
        # 发送到Sentry
        try:
            import sentry_sdk
            sentry_sdk.set_measurement(
                f"memory.{component}.{memory_type}", 
                memory_mb, 
                "megabyte"
            )
        except ImportError:
            pass
    
    def record_cpu_usage(
        self,
        component: str,
        cpu_percent: float,
        duration_ms: float
    ):
        """
        记录CPU使用情况

        Args:
            component: 组件名称
            cpu_percent: CPU使用率（百分比）
            duration_ms: 监控时长
        """
        metric = {
            "metric": "cpu_usage",
            "component": component,
            "cpu_percent": round(cpu_percent, 2),
            "duration_ms": round(duration_ms, 2)
        }

        self.logger.info("CPU usage metric", extra=metric)

        # 发送到Sentry
        try:
            import sentry_sdk
            sentry_sdk.set_measurement(
                f"cpu.{component}.usage",
                cpu_percent,
                "percent"
            )
        except ImportError:
            pass

    def record_business_metric(self, metric_name: str, value: float):
        """
        记录业务指标

        Args:
            metric_name: 指标名称
            value: 指标值
        """
        metric = {
            "metric": "business",
            "metric_name": metric_name,
            "value": value
        }

        self.logger.info("Business metric", extra=metric)

        # 发送到Sentry
        try:
            import sentry_sdk
            sentry_sdk.set_measurement(
                f"business.{metric_name}",
                value,
                "none"
            )
        except ImportError:
            pass


# ================================
# 全局实例
# ================================

# 指标收集器
metrics = MetricsCollector()

# APM收集器
apm_collector = APMCollector()


# ================================
# Sentry缓存指标上报（Stage 4任务4.5）
# ================================


async def send_cache_metrics_to_sentry():
    """
    定期发送缓存指标到Sentry

    应该由Celery定时任务调用，频率建议：每5分钟

    发送的指标包括：
    - cache.hit_rate: 缓存命中率（L1, L2, 组合）
    - cache.size: L1缓存大小
    - cache.hits: 缓存命中次数
    - cache.misses: 缓存未命中次数
    - cache.latency: 缓存操作延迟
    """
    try:
        import sentry_sdk
        from app.core.cache_manager import get_cache_manager
        from app.services.cache_prewarming import get_prewarming_manager
        from app.core.metrics import metrics_collector

        # 1. 获取缓存统计
        cache_manager = get_cache_manager()
        cache_stats = await cache_manager.get_stats()

        # 2. 获取预热统计
        prewarming_manager = get_prewarming_manager()
        prewarming_stats = prewarming_manager.get_stats()

        # 3. 获取性能指标
        metrics_summary = metrics_collector.get_summary()

        # 4. 发送L1缓存指标
        l1_stats = cache_stats.get("l1", {})
        sentry_sdk.set_measurement("cache.l1.hit_rate", l1_stats.get("hit_rate", 0.0), "ratio")
        sentry_sdk.set_measurement("cache.l1.size", l1_stats.get("size", 0), "none")
        sentry_sdk.set_measurement("cache.l1.hits", l1_stats.get("hits", 0), "none")
        sentry_sdk.set_measurement("cache.l1.misses", l1_stats.get("misses", 0), "none")
        sentry_sdk.set_measurement("cache.l1.evictions", l1_stats.get("evictions", 0), "none")

        # 5. 发送L2缓存指标
        l2_stats = cache_stats.get("l2", {})
        sentry_sdk.set_measurement("cache.l2.hit_rate", l2_stats.get("hit_rate", 0.0), "ratio")
        sentry_sdk.set_measurement("cache.l2.hits", l2_stats.get("total_hits", 0), "none")
        sentry_sdk.set_measurement("cache.l2.misses", l2_stats.get("total_misses", 0), "none")

        # 6. 发送组合缓存指标
        combined_stats = cache_stats.get("combined", {})
        sentry_sdk.set_measurement("cache.combined.hit_rate", combined_stats.get("hit_rate", 0.0), "ratio")
        sentry_sdk.set_measurement("cache.combined.hits", combined_stats.get("total_hits", 0), "none")
        sentry_sdk.set_measurement("cache.combined.misses", combined_stats.get("total_misses", 0), "none")

        # 7. 发送预热统计
        sentry_sdk.set_measurement("cache.prewarming.total", prewarming_stats.get("total_prewarmed", 0), "none")
        sentry_sdk.set_measurement("cache.prewarming.success", prewarming_stats.get("total_success", 0), "none")
        sentry_sdk.set_measurement("cache.prewarming.failed", prewarming_stats.get("total_failed", 0), "none")
        sentry_sdk.set_measurement("cache.prewarming.cached_coins", prewarming_stats.get("cached_coins", 0), "none")

        # 8. 发送响应时间指标
        sentry_sdk.set_measurement(
            "performance.avg_response_time",
            metrics_summary.get("avg_response_time_ms", 0),
            "millisecond"
        )
        sentry_sdk.set_measurement(
            "performance.p95_response_time",
            metrics_summary.get("p95_response_time_ms", 0),
            "millisecond"
        )
        sentry_sdk.set_measurement(
            "performance.p99_response_time",
            metrics_summary.get("p99_response_time_ms", 0),
            "millisecond"
        )

        # 9. 记录日志
        logger.info(
            f"✅ Sent cache metrics to Sentry: "
            f"L1 hit_rate={l1_stats.get('hit_rate', 0):.2%}, "
            f"L2 hit_rate={l2_stats.get('hit_rate', 0):.2%}, "
            f"Combined hit_rate={combined_stats.get('hit_rate', 0):.2%}"
        )

    except ImportError:
        logger.warning("⚠️ sentry-sdk not installed, skipping metrics upload")
    except Exception as e:
        logger.error(f"❌ Failed to send cache metrics to Sentry: {e}", exc_info=True)
