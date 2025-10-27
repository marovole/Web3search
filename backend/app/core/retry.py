"""
重试机制模块
用于数据库连接和外部API调用的智能重试
"""
import asyncio
import logging
import time
from enum import Enum
from functools import wraps
from typing import Callable, Tuple, Type, List, Optional, Dict
from sqlalchemy.exc import OperationalError, DBAPIError
from threading import Lock

logger = logging.getLogger(__name__)

# 可重试的数据库异常类型
RETRIABLE_DB_EXCEPTIONS = (
    OperationalError,  # 操作错误（连接失败、超时等）
    DBAPIError,  # 数据库API错误
)


def retry_on_db_error(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
    exponential_base: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = RETRIABLE_DB_EXCEPTIONS,
):
    """
    数据库连接重试装饰器

    使用指数退避策略重试失败的数据库操作

    Args:
        max_attempts: 最大重试次数
        base_delay: 基础延迟时间（秒）
        max_delay: 最大延迟时间（秒）
        exponential_base: 指数退避基数
        exceptions: 可重试的异常类型

    Example:
        @retry_on_db_error(max_attempts=3, base_delay=1.0)
        async def fetch_data(session):
            result = await session.execute(select(Model))
            return result.scalars().all()
    """

    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts - 1:
                        logger.error(
                            f"Database operation failed after {max_attempts} attempts: {func.__name__}",
                            extra={
                                "function": func.__name__,
                                "attempts": max_attempts,
                                "error": str(e),
                                "error_type": type(e).__name__,
                            },
                        )
                        raise

                    # 计算延迟时间（指数退避）
                    delay = min(base_delay * (exponential_base ** attempt), max_delay)

                    logger.warning(
                        f"Database operation failed (attempt {attempt + 1}/{max_attempts}), retrying in {delay}s: {func.__name__}",
                        extra={
                            "function": func.__name__,
                            "attempt": attempt + 1,
                            "max_attempts": max_attempts,
                            "delay": delay,
                            "error": str(e),
                            "error_type": type(e).__name__,
                        },
                    )

                    await asyncio.sleep(delay)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            import time

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts - 1:
                        logger.error(
                            f"Database operation failed after {max_attempts} attempts: {func.__name__}",
                            extra={
                                "function": func.__name__,
                                "attempts": max_attempts,
                                "error": str(e),
                            },
                        )
                        raise

                    delay = min(base_delay * (exponential_base ** attempt), max_delay)

                    logger.warning(
                        f"Database operation failed (attempt {attempt + 1}/{max_attempts}), retrying in {delay}s",
                        extra={
                            "function": func.__name__,
                            "attempt": attempt + 1,
                            "delay": delay,
                            "error": str(e),
                        },
                    )

                    time.sleep(delay)

        # 判断是异步还是同步函数
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


async def with_retry_session(session_factory: Callable, operation: Callable, *args, **kwargs):
    """
    在重试会话中执行操作

    自动处理会话创建、提交、回滚和重试

    Args:
        session_factory: 会话工厂函数
        operation: 要执行的操作函数
        *args, **kwargs: 传递给操作函数的参数

    Example:
        async def fetch_user(session, user_id):
            result = await session.execute(select(User).where(User.id == user_id))
            return result.scalar_one_or_none()

        user = await with_retry_session(AsyncSessionLocal, fetch_user, user_id=123)
    """
    max_attempts = 3
    base_delay = 1.0

    for attempt in range(max_attempts):
        try:
            async with session_factory() as session:
                result = await operation(session, *args, **kwargs)
                await session.commit()
                return result
        except RETRIABLE_DB_EXCEPTIONS as e:
            if attempt == max_attempts - 1:
                logger.error(f"Session operation failed after {max_attempts} attempts", extra={"error": str(e)})
                raise

            delay = base_delay * (2 ** attempt)
            logger.warning(
                f"Session operation failed (attempt {attempt + 1}/{max_attempts}), retrying in {delay}s",
                extra={"attempt": attempt + 1, "delay": delay, "error": str(e)},
            )
            await asyncio.sleep(delay)


# ================================
# API重试机制（任务5.1-5.4）
# ================================


def is_retriable_error(exception: Exception) -> bool:
    """
    判断异常是否可重试（任务5.3）

    区分临时错误（可重试）和永久错误（不可重试）

    临时错误（可重试）:
    - HTTP 429 (Too Many Requests)
    - HTTP 503 (Service Unavailable)
    - HTTP 502/504 (Gateway errors)
    - Timeout errors
    - Connection errors

    永久错误（不可重试）:
    - HTTP 401 (Unauthorized)
    - HTTP 404 (Not Found)
    - HTTP 400 (Bad Request)
    - ValidationError

    Args:
        exception: 要检查的异常

    Returns:
        bool: True if retriable, False otherwise
    """
    from app.core.exceptions import (
        APIRateLimitError,
        DataSourceUnavailable,
        ValidationError,
        ResourceNotFound,
        PermissionDenied,
    )

    # 临时错误（可重试）
    retriable_exceptions = (
        APIRateLimitError,           # HTTP 429
        DataSourceUnavailable,       # HTTP 503
        ConnectionError,             # 连接错误
        TimeoutError,                # 超时错误
        asyncio.TimeoutError,        # 异步超时
    )

    # 永久错误（不可重试）
    permanent_exceptions = (
        ValidationError,             # HTTP 400
        ResourceNotFound,            # HTTP 404
        PermissionDenied,            # HTTP 403
    )

    # 检查是否是永久错误
    if isinstance(exception, permanent_exceptions):
        return False

    # 检查是否是临时错误
    if isinstance(exception, retriable_exceptions):
        return True

    # 检查HTTP状态码（如果有）
    if hasattr(exception, 'status_code'):
        status_code = exception.status_code
        # 临时错误状态码
        if status_code in (429, 502, 503, 504):
            return True
        # 永久错误状态码
        if status_code in (400, 401, 403, 404):
            return False

    # 检查异常类名（兼容外部库）
    exception_name = type(exception).__name__.lower()
    if any(name in exception_name for name in ['timeout', 'connection', 'network']):
        return True

    # 默认不重试未知错误
    return False


def retry_with_backoff(
    max_attempts: int = 3,
    delays: Optional[List[float]] = None,
    single_timeout: float = 10.0,
    total_timeout: float = 30.0,
    retriable_checker: Optional[Callable[[Exception], bool]] = None,
):
    """
    通用API重试装饰器（任务5.1-5.4）

    实现指数退避重试策略，支持超时控制和错误分类

    Features:
    - 指数退避重试（默认: 1s, 2s, 4s）
    - 双层超时控制（单次10s，总计30s）
    - 智能错误分类（临时/永久错误）
    - 结构化日志记录
    - 支持async/sync函数

    Args:
        max_attempts: 最大重试次数（默认3次）
        delays: 重试延迟序列，单位秒（默认[1, 2, 4]）
        single_timeout: 单次请求超时时间（秒，默认10s）
        total_timeout: 总计超时时间（秒，默认30s）
        retriable_checker: 自定义错误分类函数（默认使用is_retriable_error）

    Example:
        @retry_with_backoff(max_attempts=3, delays=[1, 2, 4])
        async def fetch_coingecko_price(symbol: str):
            async with httpx.AsyncClient() as client:
                response = await client.get(f"https://api.coingecko.com/...")
                response.raise_for_status()
                return response.json()
    """
    if delays is None:
        delays = [1.0, 2.0, 4.0]

    if retriable_checker is None:
        retriable_checker = is_retriable_error

    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    # 任务5.4: 单次请求超时控制
                    result = await asyncio.wait_for(
                        func(*args, **kwargs),
                        timeout=single_timeout
                    )

                    # 成功，记录日志和metrics（任务5.5）
                    if attempt > 0:
                        logger.info(
                            f"API call succeeded after {attempt + 1} attempts: {func.__name__}",
                            extra={
                                "function": func.__name__,
                                "attempt": attempt + 1,
                                "total_time": time.time() - start_time,
                            }
                        )
                        # 记录Sentry metrics
                        record_retry_metrics(
                            operation=func.__name__,
                            attempt=attempt + 1,
                            success=True
                        )

                    return result

                except Exception as e:
                    last_exception = e

                    # 任务5.4: 总计超时检查
                    elapsed_time = time.time() - start_time
                    if elapsed_time >= total_timeout:
                        logger.error(
                            f"API call total timeout exceeded: {func.__name__}",
                            extra={
                                "function": func.__name__,
                                "total_timeout": total_timeout,
                                "elapsed_time": elapsed_time,
                                "error": str(e),
                                "error_type": type(e).__name__,
                            }
                        )
                        raise TimeoutError(
                            f"Total timeout ({total_timeout}s) exceeded after {elapsed_time:.2f}s"
                        ) from e

                    # 任务5.3: 检查是否可重试
                    is_retriable = retriable_checker(e)

                    # 最后一次尝试或永久错误，不再重试
                    if attempt == max_attempts - 1 or not is_retriable:
                        error_type = "retriable" if is_retriable else "permanent"
                        logger.error(
                            f"API call failed after {attempt + 1} attempts: {func.__name__} ({error_type} error)",
                            extra={
                                "function": func.__name__,
                                "attempts": attempt + 1,
                                "error": str(e),
                                "error_type": type(e).__name__,
                                "is_retriable": is_retriable,
                                "total_time": elapsed_time,
                            }
                        )
                        # 记录Sentry metrics（任务5.5）
                        record_retry_metrics(
                            operation=func.__name__,
                            attempt=attempt + 1,
                            success=False,
                            error_type=type(e).__name__,
                            is_retriable=is_retriable
                        )
                        raise

                    # 计算延迟时间
                    delay = delays[min(attempt, len(delays) - 1)]
                    next_retry_time = time.time() + delay

                    logger.warning(
                        f"API call failed (attempt {attempt + 1}/{max_attempts}), retrying in {delay}s: {func.__name__}",
                        extra={
                            "function": func.__name__,
                            "attempt": attempt + 1,
                            "max_attempts": max_attempts,
                            "delay": delay,
                            "next_retry_time": next_retry_time,
                            "error": str(e),
                            "error_type": type(e).__name__,
                            "is_retriable": is_retriable,
                        }
                    )

                    # 等待后重试
                    await asyncio.sleep(delay)

            # 不应该到达这里，但为了安全
            if last_exception:
                raise last_exception

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    # 同步函数不支持单次超时，只检查总超时
                    result = func(*args, **kwargs)

                    if attempt > 0:
                        logger.info(
                            f"API call succeeded after {attempt + 1} attempts: {func.__name__}",
                            extra={
                                "function": func.__name__,
                                "attempt": attempt + 1,
                                "total_time": time.time() - start_time,
                            }
                        )

                    return result

                except Exception as e:
                    last_exception = e

                    # 总计超时检查
                    elapsed_time = time.time() - start_time
                    if elapsed_time >= total_timeout:
                        logger.error(
                            f"API call total timeout exceeded: {func.__name__}",
                            extra={
                                "function": func.__name__,
                                "total_timeout": total_timeout,
                                "elapsed_time": elapsed_time,
                                "error": str(e),
                            }
                        )
                        raise TimeoutError(
                            f"Total timeout ({total_timeout}s) exceeded after {elapsed_time:.2f}s"
                        ) from e

                    # 检查是否可重试
                    is_retriable = retriable_checker(e)

                    if attempt == max_attempts - 1 or not is_retriable:
                        error_type = "retriable" if is_retriable else "permanent"
                        logger.error(
                            f"API call failed after {attempt + 1} attempts: {func.__name__} ({error_type} error)",
                            extra={
                                "function": func.__name__,
                                "attempts": attempt + 1,
                                "error": str(e),
                                "is_retriable": is_retriable,
                            }
                        )
                        raise

                    delay = delays[min(attempt, len(delays) - 1)]
                    next_retry_time = time.time() + delay

                    logger.warning(
                        f"API call failed (attempt {attempt + 1}/{max_attempts}), retrying in {delay}s: {func.__name__}",
                        extra={
                            "function": func.__name__,
                            "attempt": attempt + 1,
                            "max_attempts": max_attempts,
                            "delay": delay,
                            "next_retry_time": next_retry_time,
                            "error": str(e),
                            "error_type": type(e).__name__,
                            "is_retriable": is_retriable,
                        }
                    )

                    time.sleep(delay)

            if last_exception:
                raise last_exception

        # 判断是异步还是同步函数
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# ================================
# Sentry Metrics记录（任务5.5）
# ================================


def record_retry_metrics(
    operation: str,
    attempt: int,
    success: bool,
    error_type: Optional[str] = None,
    is_retriable: Optional[bool] = None,
):
    """
    记录重试指标到Sentry（任务5.5）

    Args:
        operation: 操作名称
        attempt: 重试次数
        success: 是否成功
        error_type: 错误类型
        is_retriable: 是否可重试
    """
    try:
        import sentry_sdk

        # 记录重试次数
        sentry_sdk.set_measurement("retry.attempt.count", attempt)

        # 记录成功/失败状态
        tags = {
            "operation": operation,
            "success": "true" if success else "false",
        }

        if error_type:
            tags["error_type"] = error_type

        if is_retriable is not None:
            tags["is_retriable"] = "true" if is_retriable else "false"

        # 记录事件
        if success and attempt > 1:
            # 重试后成功
            sentry_sdk.capture_message(
                f"Retry succeeded after {attempt} attempts: {operation}",
                level="info",
                tags=tags
            )
        elif not success and attempt > 1:
            # 达到最大重试次数
            sentry_sdk.capture_message(
                f"Max retries exceeded ({attempt} attempts): {operation}",
                level="warning",
                tags=tags
            )
        elif not success and is_retriable is False:
            # 永久错误不重试
            sentry_sdk.capture_message(
                f"Permanent error, no retry: {operation}",
                level="warning",
                tags=tags
            )

    except ImportError:
        # Sentry未安装，跳过
        pass
    except Exception as e:
        logger.debug(f"Failed to record retry metrics: {e}")


# ================================
# 断路器模式（任务5.6）
# ================================


class CircuitBreakerState(Enum):
    """断路器状态"""
    CLOSED = "closed"      # 正常状态
    OPEN = "open"          # 熔断状态
    HALF_OPEN = "half_open"  # 半开状态


class CircuitBreaker:
    """
    断路器实现（任务5.6）

    防止级联故障，当服务连续失败达到阈值时自动熔断

    状态转换：
    - CLOSED → OPEN: 连续失败达到阈值
    - OPEN → HALF_OPEN: 熔断时间结束后
    - HALF_OPEN → CLOSED: 测试请求成功
    - HALF_OPEN → OPEN: 测试请求失败

    Example:
        cb = CircuitBreaker("coingecko_api", failure_threshold=5, timeout=600)

        @cb.protect
        async def fetch_data():
            return await api_call()
    """

    # 全局断路器实例字典
    _instances: Dict[str, "CircuitBreaker"] = {}
    _lock = Lock()

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        timeout: float = 600.0,  # 10分钟
        half_open_max_calls: int = 1,
    ):
        """
        初始化断路器

        Args:
            name: 服务名称（唯一标识）
            failure_threshold: 失败阈值（连续失败次数）
            timeout: 熔断时间（秒）
            half_open_max_calls: 半开状态允许的测试请求数
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.half_open_max_calls = half_open_max_calls

        # 状态
        self._state = CircuitBreakerState.CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._half_open_calls = 0

    @classmethod
    def get_instance(cls, name: str, **kwargs) -> "CircuitBreaker":
        """获取或创建断路器实例"""
        with cls._lock:
            if name not in cls._instances:
                cls._instances[name] = cls(name, **kwargs)
            return cls._instances[name]

    @property
    def state(self) -> CircuitBreakerState:
        """获取当前状态"""
        # 检查是否需要从OPEN转换到HALF_OPEN
        if self._state == CircuitBreakerState.OPEN:
            if self._last_failure_time and (time.time() - self._last_failure_time) >= self.timeout:
                self._transition_to_half_open()
        return self._state

    def _transition_to_half_open(self):
        """转换到半开状态"""
        logger.info(
            f"Circuit breaker transitioning to HALF_OPEN: {self.name}",
            extra={"circuit_breaker": self.name, "previous_state": self._state.value}
        )
        self._state = CircuitBreakerState.HALF_OPEN
        self._half_open_calls = 0

    def _transition_to_open(self):
        """转换到熔断状态"""
        logger.error(
            f"Circuit breaker OPENED: {self.name}",
            extra={
                "circuit_breaker": self.name,
                "failure_count": self._failure_count,
                "threshold": self.failure_threshold,
            }
        )
        self._state = CircuitBreakerState.OPEN
        self._last_failure_time = time.time()

        # 发送Sentry告警
        try:
            import sentry_sdk
            sentry_sdk.capture_message(
                f"Circuit breaker opened: {self.name}",
                level="error",
                tags={"circuit_breaker": self.name, "failure_count": self._failure_count}
            )
        except ImportError:
            pass

    def _transition_to_closed(self):
        """转换到正常状态"""
        logger.info(
            f"Circuit breaker CLOSED: {self.name}",
            extra={"circuit_breaker": self.name, "previous_state": self._state.value}
        )
        self._state = CircuitBreakerState.CLOSED
        self._failure_count = 0
        self._half_open_calls = 0

    def record_success(self):
        """记录成功"""
        if self._state == CircuitBreakerState.HALF_OPEN:
            # 半开状态成功，恢复正常
            self._transition_to_closed()
        elif self._state == CircuitBreakerState.CLOSED:
            # 正常状态，重置失败计数
            self._failure_count = 0

    def record_failure(self):
        """记录失败"""
        self._failure_count += 1

        if self._state == CircuitBreakerState.HALF_OPEN:
            # 半开状态失败，重新熔断
            self._transition_to_open()
        elif self._state == CircuitBreakerState.CLOSED:
            # 正常状态，检查是否达到阈值
            if self._failure_count >= self.failure_threshold:
                self._transition_to_open()

    def is_available(self) -> bool:
        """检查服务是否可用"""
        current_state = self.state  # 触发状态检查

        if current_state == CircuitBreakerState.CLOSED:
            return True
        elif current_state == CircuitBreakerState.HALF_OPEN:
            # 半开状态限制请求数
            if self._half_open_calls < self.half_open_max_calls:
                self._half_open_calls += 1
                return True
            return False
        else:  # OPEN
            return False

    def protect(self, func: Callable):
        """
        断路器装饰器

        Example:
            cb = CircuitBreaker("my_service")

            @cb.protect
            async def my_api_call():
                return await http_client.get("...")
        """
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            from app.core.exceptions import CircuitBreakerOpenError

            # 检查断路器状态
            if not self.is_available():
                retry_after = int(self.timeout - (time.time() - (self._last_failure_time or 0)))
                raise CircuitBreakerOpenError(
                    f"Service {self.name} is currently unavailable",
                    service_name=self.name,
                    retry_after=max(0, retry_after)
                )

            # 执行请求
            try:
                result = await func(*args, **kwargs)
                self.record_success()
                return result
            except Exception as e:
                self.record_failure()
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            from app.core.exceptions import CircuitBreakerOpenError

            if not self.is_available():
                retry_after = int(self.timeout - (time.time() - (self._last_failure_time or 0)))
                raise CircuitBreakerOpenError(
                    f"Service {self.name} is currently unavailable",
                    service_name=self.name,
                    retry_after=max(0, retry_after)
                )

            try:
                result = func(*args, **kwargs)
                self.record_success()
                return result
            except Exception as e:
                self.record_failure()
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
