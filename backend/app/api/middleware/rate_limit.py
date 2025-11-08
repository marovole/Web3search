"""
速率限制中间件
基于Redis实现IP级别的速率限制
支持内存缓存降级机制
"""
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from typing import Dict, Tuple, Optional
import re
import logging
import time
from collections import defaultdict
from threading import Lock

from app.core.redis_client import rate_limit_check
from app.core.config import settings

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    速率限制中间件

    根据不同的API端点应用不同的速率限制规则
    支持Redis和内存缓存降级机制
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
        
        # 内存缓存降级机制
        self.fallback_mode = True  # 默认启用降级模式，避免Redis不可用导致API失败
        self.fallback_cache: Dict[str, list] = defaultdict(list)  # 内存缓存：{identifier: [(timestamp, count)]}
        self.fallback_lock = Lock()  # 线程锁
        self.redis_failure_count = 0  # Redis失败计数
        self.redis_failure_threshold = 5  # 连续失败5次后启用降级模式
        self.last_fallback_alert_time = 0  # 上次降级告警时间
        self.fallback_alert_interval = 300  # 降级告警间隔（5分钟）

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
        处理请求，应用速率限制 - 修复版本
        
        增强容错机制，确保Redis不可用时API仍能正常运行

        Args:
            request: 请求对象
            call_next: 下一个中间件

        Returns:
            响应对象
        """
        try:
            path = request.url.path

            # 检查是否需要速率限制
            rate_limit = self.match_path(path)

            if rate_limit:
                limit, window = rate_limit
                client_ip = self.get_client_ip(request)

                # 构建Redis键（按路径和IP分组）
                identifier = f"{path}:{client_ip}"

                # 修复：默认使用降级模式，确保API不会因Redis问题而失败
                try:
                    # 只有在Redis明确可用时才尝试使用Redis
                    if not self.fallback_mode:
                        allowed, remaining = await rate_limit_check(
                            identifier=identifier,
                            limit=limit,
                            window=window,
                        )
                        # Redis成功，重置失败计数
                        if self.redis_failure_count > 0:
                            self.redis_failure_count = 0
                            if self.fallback_mode:
                                logger.info("Redis连接恢复，退出降级模式")
                                self.fallback_mode = False
                                self.fallback_cache.clear()
                    else:
                        # Redis不可用或处于降级模式，直接使用内存缓存
                        raise Exception("Redis unavailable, using fallback mode")
                        
                except Exception as e:
                    # 任何Redis相关错误都使用降级机制，不阻止API运行
                    logger.warning(f"Rate limiting using fallback mode due to: {e}")
                    allowed, remaining = self._check_rate_limit_fallback(identifier, limit, window)

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
                            "fallback_mode": self.fallback_mode,  # 指示是否使用降级模式
                        },
                        headers={
                            "X-RateLimit-Limit": str(limit),
                            "X-RateLimit-Remaining": "0",
                            "X-RateLimit-Reset": str(window),
                            "Retry-After": str(window),
                            "X-RateLimit-Fallback": "true" if self.fallback_mode else "false",
                        }
                    )

            # 允许请求，添加速率限制响应头
            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(window)
            if self.fallback_mode:
                response.headers["X-RateLimit-Fallback"] = "true"

            return response

        else:
            # 不需要速率限制，直接通过
            return await call_next(request)
            
        except Exception as e:
            # 任何异常都不应该阻止API运行，记录错误并继续
            logger.error(f"Rate limit middleware error: {e}", exc_info=True)
            return await call_next(request)
    
    def _check_rate_limit_fallback(self, identifier: str, limit: int, window: int) -> Tuple[bool, int]:
        """
        使用内存缓存检查速率限制（降级模式）
        
        Args:
            identifier: 标识符
            limit: 限制次数
            window: 时间窗口（秒）
            
        Returns:
            Tuple[bool, int]: (是否允许, 剩余次数)
        """
        current_time = time.time()
        
        with self.fallback_lock:
            # 清理过期记录
            if identifier in self.fallback_cache:
                self.fallback_cache[identifier] = [
                    (ts, count) for ts, count in self.fallback_cache[identifier]
                    if current_time - ts < window
                ]
            
            # 计算当前窗口内的请求数
            requests_in_window = sum(
                count for ts, count in self.fallback_cache[identifier]
                if current_time - ts < window
            )
            
            if requests_in_window >= limit:
                # 超过限制
                return False, 0
            
            # 未超过限制，添加当前请求
            self.fallback_cache[identifier].append((current_time, 1))
            
            # 清理旧记录（保持缓存大小）
            if len(self.fallback_cache[identifier]) > limit * 2:
                self.fallback_cache[identifier] = self.fallback_cache[identifier][-limit:]
            
            remaining = limit - requests_in_window - 1
            return True, max(0, remaining)
    
    def _send_fallback_alert(self):
        """发送降级模式告警"""
        current_time = time.time()
        
        # 避免过于频繁的告警
        if current_time - self.last_fallback_alert_time < self.fallback_alert_interval:
            return
        
        self.last_fallback_alert_time = current_time
        
        # 发送告警到监控系统
        try:
            from app.core.alerting import alert_manager
            alert_manager.update_metric("rate_limit_fallback_enabled", 1.0)
            logger.critical(
                "速率限制降级模式已启用 - Redis不可用，使用内存缓存",
                extra={
                    "fallback_mode": True,
                    "redis_failure_count": self.redis_failure_count,
                    "alert": True,
                }
            )
        except Exception as e:
            logger.error(f"发送降级告警失败: {e}")


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
