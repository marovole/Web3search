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
            # 性能监控
            traces_sample_rate=0.1 if settings.ENVIRONMENT == "production" else 1.0,
            # 错误采样（生产环境采样以节省配额）
            sample_rate=0.5 if settings.ENVIRONMENT == "production" else 1.0,
            # 过滤
            before_send=before_send_filter,
            # 配置
            max_breadcrumbs=50,
            attach_stacktrace=True,
            send_default_pii=False,  # 不发送个人身份信息
        )

        logger.info(f"✅ Sentry initialized: environment={settings.ENVIRONMENT}")

    except ImportError:
        logger.warning("⚠️ sentry-sdk not installed, skipping Sentry initialization")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Sentry: {e}")


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


# ================================
# 全局实例
# ================================

# 指标收集器
metrics = MetricsCollector()
