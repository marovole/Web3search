"""
强制API认证中间件
用于实现BREAKING CHANGE：强制所有API端点认证要求
"""
from typing import List
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.config import settings
from app.core.security import verify_token


class RequiredAuthMiddleware(BaseHTTPMiddleware):
    """
    强制API认证中间件

    对所有API端点（除明确排除的路径外）要求认证
    这是为了实现安全加固的BREAKING CHANGE
    """

    def __init__(self, app, exclude_paths: List[str] = None):
        super().__init__(app)
        # 默认排除的路径（不需要认证的公共端点）
        self.exclude_paths = exclude_paths or [
            "/health",
            "/metrics",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/refresh",
            "/api/v1/github/search",
            "/api/v1/chat/quick-chat",  # Quick Chat（公共端点）
            "/api/v1/chat/deep-research",  # Deep Research（公共端点，但有限流）
            "/api/v1/search",  # 搜索API（公共端点）
            "/api/v1/reports",  # 报告API（支持匿名访问）
            "/api/v1/trending",  # 热点API（公共端点）
            "/docs",
            "/redoc",
            "/openapi.json",
            "/favicon.ico",
            "/static",
        ]

        # 开发环境额外排除的路径
        if settings.DEBUG:
            self.exclude_paths.extend([
                "/api/v1/test",
                "/debug",
            ])

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # 检查是否为排除路径
        if self._is_excluded_path(path):
            return await call_next(request)

        # 检查Authorization header
        authorization = request.headers.get("Authorization")
        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="缺少Authorization header",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 验证Bearer token格式
        if not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header格式错误，应为'Bearer <token>'",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = authorization.split(" ", 1)[1]

        # 验证token
        payload = verify_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的访问令牌",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 将用户信息添加到请求状态
        request.state.user_id = payload.get("user_id") or payload.get("sub")
        request.state.user_roles = payload.get("roles", [])

        # 继续处理请求
        response = await call_next(request)

        return response

    def _is_excluded_path(self, path: str) -> bool:
        """检查路径是否为排除路径"""
        # 精确匹配或前缀匹配
        for exclude_path in self.exclude_paths:
            # 精确匹配
            if path == exclude_path:
                return True
            # 前缀匹配（确保是完整路径段）
            if path.startswith(exclude_path):
                # 确保是完整路径段，避免部分匹配
                # 例如：/api/v1/search 应该匹配 /api/v1/search/autocomplete
                # 但不应该匹配 /api/v1/search_other
                if len(path) == len(exclude_path) or path[len(exclude_path)] == '/':
                    return True
        return False


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """
    API速率限制中间件
    防止API滥用和DDoS攻击
    """

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_counts = {}  # 简单的内存存储，生产环境应使用Redis

    async def dispatch(self, request: Request, call_next):
        # 获取客户端IP
        client_ip = request.client.host
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()

        # 简单的速率限制检查（生产环境应使用更复杂的实现）
        current_time = int(time.time())
        minute_key = f"{client_ip}:{current_time // 60}"

        if minute_key in self.request_counts:
            if self.request_counts[minute_key] >= self.requests_per_minute:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="请求过于频繁，请稍后再试",
                    headers={"Retry-After": "60"},
                )
            self.request_counts[minute_key] += 1
        else:
            self.request_counts[minute_key] = 1

        # 清理过期记录
        old_minute = f"{client_ip}:{(current_time // 60) - 1}"
        if old_minute in self.request_counts:
            del self.request_counts[old_minute]

        return await call_next(request)


# 导入time模块
import time