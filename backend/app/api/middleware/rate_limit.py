"""
速率限制中间件
基于Redis实现IP级别的速率限制
"""
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from typing import Dict, Tuple
import re
import logging

from app.core.redis_client import rate_limit_check

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    速率限制中间件

    根据不同的API端点应用不同的速率限制规则
    """

    def __init__(self, app, rate_limit_rules: Dict[str, Tuple[int, int]] = None):
        """
        初始化速率限制中间件

        Args:
            app: FastAPI应用实例
            rate_limit_rules: 速率限制规则
                格式: {"/api/path": (limit, window)}
                例如: {"/api/v1/quick-chat": (10, 60)} 表示每60秒最多10次请求
        """
        super().__init__(app)

        # 默认速率限制规则
        self.rate_limit_rules = rate_limit_rules or {
            "/api/v1/quick-chat": (10, 60),  # Quick Chat: 10次/分钟
            "/api/v1/quick-chat/stream": (10, 60),  # 流式也是10次/分钟
            "/api/v1/deep-research": (3, 3600),  # Deep Research: 3次/小时
            "/api/v1/reports": (30, 60),  # 报告查询: 30次/分钟
        }

    def get_client_ip(self, request: Request) -> str:
        """
        获取客户端IP地址

        Args:
            request: FastAPI请求对象

        Returns:
            str: 客户端IP地址
        """
        # 优先从X-Forwarded-For获取（代理场景）
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        # 从X-Real-IP获取
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # 直接从客户端获取
        if request.client:
            return request.client.host

        return "unknown"

    def match_path(self, path: str) -> Tuple[int, int] | None:
        """
        匹配路径的速率限制规则

        Args:
            path: 请求路径

        Returns:
            Tuple[int, int] | None: (limit, window) 或 None
        """
        # 精确匹配
        if path in self.rate_limit_rules:
            return self.rate_limit_rules[path]

        # 模式匹配（支持通配符）
        for pattern, (limit, window) in self.rate_limit_rules.items():
            if "*" in pattern:
                regex = pattern.replace("*", ".*")
                if re.match(f"^{regex}$", path):
                    return (limit, window)

        return None

    async def dispatch(self, request: Request, call_next):
        """
        处理请求，应用速率限制

        Args:
            request: 请求对象
            call_next: 下一个中间件

        Returns:
            响应对象
        """
        path = request.url.path

        # 检查是否需要速率限制
        rate_limit = self.match_path(path)

        if rate_limit:
            limit, window = rate_limit
            client_ip = self.get_client_ip(request)

            # 构建Redis键（按路径和IP分组）
            identifier = f"{path}:{client_ip}"

            try:
                # 检查速率限制
                allowed, remaining = await rate_limit_check(
                    identifier=identifier,
                    limit=limit,
                    window=window,
                )

                if not allowed:
                    # 超过限制，返回429错误
                    return JSONResponse(
                        status_code=429,
                        content={
                            "error": "Rate Limit Exceeded",
                            "message": f"请求过于频繁，请{window}秒后重试",
                            "limit": limit,
                            "window": window,
                            "retry_after": window,
                        },
                        headers={
                            "X-RateLimit-Limit": str(limit),
                            "X-RateLimit-Remaining": "0",
                            "X-RateLimit-Reset": str(window),
                            "Retry-After": str(window),
                        }
                    )

                # 允许请求，添加速率限制响应头
                response = await call_next(request)
                response.headers["X-RateLimit-Limit"] = str(limit)
                response.headers["X-RateLimit-Remaining"] = str(remaining)
                response.headers["X-RateLimit-Reset"] = str(window)

                return response

            except Exception as e:
                # 速率限制检查失败，记录错误并允许请求通过（降级处理）
                logger.error(f"速率限制检查失败: {e}", exc_info=True)

                # 在生产环境中，可以考虑记录监控指标
                if logger.isEnabledFor(logging.INFO):
                    logger.info(f"速率限制降级 - IP: {client_ip}, 路径: {request.url.path}")

                return await call_next(request)

        else:
            # 不需要速率限制，直接通过
            return await call_next(request)


# ================================
# 装饰器形式的速率限制
# ================================

def rate_limit(limit: int, window: int):
    """
    速率限制装饰器（用于单个端点）

    Args:
        limit: 限制次数
        window: 时间窗口（秒）

    Usage:
        @router.post("/api/endpoint")
        @rate_limit(limit=10, window=60)
        async def my_endpoint():
            ...
    """
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            client_ip = request.client.host if request.client else "unknown"
            identifier = f"{request.url.path}:{client_ip}"

            allowed, remaining = await rate_limit_check(
                identifier=identifier,
                limit=limit,
                window=window,
            )

            if not allowed:
                raise HTTPException(
                    status_code=429,
                    detail=f"请求过于频繁，请{window}秒后重试",
                    headers={
                        "X-RateLimit-Limit": str(limit),
                        "X-RateLimit-Remaining": "0",
                        "Retry-After": str(window),
                    }
                )

            return await func(request, *args, **kwargs)

        return wrapper
    return decorator
