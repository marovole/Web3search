"""
重试机制模块
用于数据库连接和外部API调用的智能重试
"""
import asyncio
import logging
from functools import wraps
from typing import Callable, Tuple, Type
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
