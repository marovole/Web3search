"""
重试机制模块
用于数据库连接和外部API调用的智能重试
"""
import asyncio
import logging
import time
from functools import wraps
from typing import Callable, Tuple, Type, List, Optional
from sqlalchemy.exc import OperationalError, DBAPIError

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

                    # 成功，记录日志
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

                    logger.warning(
                        f"API call failed (attempt {attempt + 1}/{max_attempts}), retrying in {delay}s: {func.__name__}",
                        extra={
                            "function": func.__name__,
                            "attempt": attempt + 1,
                            "delay": delay,
                            "error": str(e),
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
