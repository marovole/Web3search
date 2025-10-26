"""
API降级策略
提供数据源和LLM服务的fallback机制
"""
import logging
from typing import Any, Callable, Dict, List, Optional, TypeVar
from functools import wraps
import asyncio

from app.core.exceptions import (
    DataCollectionError,
    LLMError,
    DataSourceUnavailable,
    APIRateLimitError,
)
from app.core.redis_client import get_async_redis

logger = logging.getLogger(__name__)

T = TypeVar("T")


# ================================
# 数据源降级策略
# ================================


class DataSourceFallback:
    """
    数据源降级策略

    当主数据源失败时，自动切换到备用数据源
    """

    def __init__(self, cache_ttl: int = 3600):
        """
        Args:
            cache_ttl: 缓存过期时间（秒）
        """
        self.cache_ttl = cache_ttl

    async def get_cached_data(self, cache_key: str) -> Optional[Any]:
        """
        从缓存获取数据

        Args:
            cache_key: 缓存键

        Returns:
            缓存的数据，如果不存在返回None
        """
        try:
            import json

            redis = await get_async_redis()
            data = await redis.get(cache_key)
            if data:
                logger.info(f"✅ Cache hit: {cache_key}")
                return json.loads(data)
            return None
        except Exception as e:
            logger.warning(f"Failed to get cache: {e}")
            return None

    async def set_cached_data(self, cache_key: str, data: Any) -> None:
        """
        设置缓存数据

        Args:
            cache_key: 缓存键
            data: 要缓存的数据
        """
        try:
            import json

            redis = await get_async_redis()
            await redis.setex(cache_key, self.cache_ttl, json.dumps(data))
            logger.info(f"✅ Cache set: {cache_key}")
        except Exception as e:
            logger.warning(f"Failed to set cache: {e}")

    async def execute_with_fallback(
        self,
        primary_func: Callable,
        fallback_funcs: List[Callable],
        cache_key: Optional[str] = None,
        use_cache: bool = True,
    ) -> Any:
        """
        执行带降级的数据采集

        尝试顺序:
        1. 从缓存获取（如果启用）
        2. 主数据源
        3. 备用数据源1
        4. 备用数据源2
        5. ...

        Args:
            primary_func: 主数据源函数
            fallback_funcs: 备用数据源函数列表
            cache_key: 缓存键
            use_cache: 是否使用缓存

        Returns:
            数据

        Raises:
            DataCollectionError: 所有数据源都失败
        """
        errors = []

        # 1. 尝试从缓存获取
        if use_cache and cache_key:
            cached_data = await self.get_cached_data(cache_key)
            if cached_data is not None:
                logger.info("✅ Using cached data")
                return cached_data

        # 2. 尝试主数据源
        try:
            logger.info(f"🔄 Trying primary source: {primary_func.__name__}")
            result = await primary_func()

            # 成功：缓存结果
            if use_cache and cache_key:
                await self.set_cached_data(cache_key, result)

            logger.info(f"✅ Primary source succeeded: {primary_func.__name__}")
            return result
        except Exception as e:
            logger.warning(f"⚠️ Primary source failed: {primary_func.__name__} - {e}")
            errors.append({"source": "primary", "function": primary_func.__name__, "error": str(e)})

        # 3. 尝试备用数据源
        for i, fallback_func in enumerate(fallback_funcs, 1):
            try:
                logger.info(f"🔄 Trying fallback #{i}: {fallback_func.__name__}")
                result = await fallback_func()

                # 成功：缓存结果
                if use_cache and cache_key:
                    await self.set_cached_data(cache_key, result)

                logger.info(f"✅ Fallback #{i} succeeded: {fallback_func.__name__}")
                return result
            except Exception as e:
                logger.warning(f"⚠️ Fallback #{i} failed: {fallback_func.__name__} - {e}")
                errors.append({"source": f"fallback_{i}", "function": fallback_func.__name__, "error": str(e)})

        # 4. 所有数据源都失败：抛出异常
        raise DataCollectionError(
            message="所有数据源都失败",
            source="all",
            details={"errors": errors}
        )


# ================================
# LLM降级策略
# ================================


class LLMFallback:
    """
    LLM降级策略

    当主模型失败时，自动切换到备用模型
    """

    def __init__(self, models: List[str]):
        """
        Args:
            models: 模型列表（按优先级排序）
        """
        self.models = models

    async def execute_with_fallback(
        self,
        llm_func: Callable,
        prompt: str,
        **kwargs
    ) -> Any:
        """
        执行带降级的LLM调用

        Args:
            llm_func: LLM调用函数
            prompt: Prompt
            **kwargs: 其他参数

        Returns:
            LLM响应

        Raises:
            LLMError: 所有模型都失败
        """
        errors = []

        for model in self.models:
            try:
                logger.info(f"🔄 Trying LLM model: {model}")
                result = await llm_func(model=model, prompt=prompt, **kwargs)
                logger.info(f"✅ LLM model succeeded: {model}")
                return result
            except Exception as e:
                logger.warning(f"⚠️ LLM model failed: {model} - {e}")
                errors.append({"model": model, "error": str(e)})

        # 所有模型都失败
        raise LLMError(
            message="所有LLM模型都失败",
            model=", ".join(self.models),
            details={"errors": errors}
        )


# ================================
# 装饰器：自动重试
# ================================


def retry_on_failure(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    自动重试装饰器

    Args:
        max_retries: 最大重试次数
        delay: 初始延迟（秒）
        backoff: 延迟倍数（指数退避）
        exceptions: 需要重试的异常类型
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            current_delay = delay

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries:
                        logger.error(f"❌ Failed after {max_retries} retries: {func.__name__} - {e}")
                        raise

                    logger.warning(f"⚠️ Attempt {attempt + 1}/{max_retries + 1} failed: {func.__name__} - {e}")
                    logger.info(f"🔄 Retrying in {current_delay}s...")

                    await asyncio.sleep(current_delay)
                    current_delay *= backoff

        return wrapper
    return decorator


# ================================
# 装饰器：超时处理
# ================================


def timeout(seconds: float):
    """
    超时装饰器

    Args:
        seconds: 超时时间（秒）
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
            except asyncio.TimeoutError:
                logger.error(f"❌ Timeout after {seconds}s: {func.__name__}")
                raise TimeoutError(f"Operation timed out after {seconds}s")

        return wrapper
    return decorator


# ================================
# 全局降级策略实例
# ================================

# 数据源降级策略（缓存1小时）
data_source_fallback = DataSourceFallback(cache_ttl=3600)

# LLM降级策略（按优先级排序）
llm_fallback = LLMFallback(
    models=[
        "meta-llama/llama-3.3-70b-instruct:free",  # 主模型
        "qwen/qwen-2.5-72b-instruct:free",  # 备用模型1
        "google/gemma-2-9b-it:free",  # 备用模型2（快速但质量较低）
    ]
)
