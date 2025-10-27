"""
请求上下文中间件

提供request_id追踪和上下文信息传播功能
"""
import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.structlog_config import get_logger

logger = get_logger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    请求上下文中间件

    功能：
    - 为每个请求生成唯一的request_id（UUID）
    - 将request_id添加到响应头
    - 记录请求开始和结束日志
    - 计算请求处理时间
    - 捕获和记录异常
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求

        Args:
            request: FastAPI请求对象
            call_next: 下一个中间件/路由处理器

        Returns:
            响应对象
        """
        # 生成或获取request_id
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())

        # 将request_id存储到request.state中，供后续使用
        request.state.request_id = request_id

        # 记录请求开始
        start_time = time.time()

        logger.info(
            "request_started",
            request_id=request_id,
            method=request.method,
            url=str(request.url),
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        try:
            # 执行请求处理
            response = await call_next(request)

            # 计算处理时间
            duration = time.time() - start_time

            # 记录请求完成
            logger.info(
                "request_completed",
                request_id=request_id,
                method=request.method,
                url=str(request.url),
                status_code=response.status_code,
                duration_ms=round(duration * 1000, 2),
            )

            # 添加request_id到响应头
            response.headers["X-Request-ID"] = request_id

            # 添加处理时间到响应头
            response.headers["X-Process-Time"] = f"{duration:.3f}"

            return response

        except Exception as e:
            # 计算处理时间
            duration = time.time() - start_time

            # 记录错误
            logger.error(
                "request_failed",
                request_id=request_id,
                method=request.method,
                url=str(request.url),
                error=str(e),
                error_type=type(e).__name__,
                duration_ms=round(duration * 1000, 2),
                exc_info=True,
            )

            # 重新抛出异常，让FastAPI的异常处理器处理
            raise


def get_request_id(request: Request) -> str:
    """
    从请求中获取request_id

    Args:
        request: FastAPI请求对象

    Returns:
        request_id字符串

    Example:
        >>> from fastapi import Depends
        >>> @app.get("/api/example")
        >>> async def example(request: Request):
        >>>     request_id = get_request_id(request)
        >>>     logger.info("processing", request_id=request_id)
    """
    return getattr(request.state, "request_id", "unknown")
