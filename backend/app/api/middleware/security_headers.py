"""
安全头部中间件
为所有HTTP响应添加安全头部，防止XSS、点击劫持等攻击
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    安全头部中间件
    
    为所有HTTP响应添加以下安全头部：
    - Strict-Transport-Security (HSTS)
    - X-Frame-Options (防止点击劫持)
    - X-Content-Type-Options (防止MIME嗅探)
    - X-XSS-Protection (XSS过滤器)
    - Referrer-Policy (控制引用信息)
    - Permissions-Policy (控制浏览器功能权限)
    - Content-Security-Policy (CSP，由前端管理但后端也提供基础配置)
    """

    def __init__(self, app):
        super().__init__(app)
        
        # 基础CSP配置（前端会通过meta标签注入更详细的CSP）
        self.base_csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https://web3search-api.onrender.com; "
            "font-src 'self' data: https:; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )

    async def dispatch(self, request: Request, call_next):
        """
        处理请求，添加安全头部
        
        Args:
            request: 请求对象
            call_next: 下一个中间件
            
        Returns:
            响应对象（已添加安全头部）
        """
        response = await call_next(request)
        
        # 只对HTTP响应添加安全头部
        if isinstance(response, Response):
            # HSTS - 强制HTTPS（仅在生产环境且使用HTTPS时）
            if settings.ENVIRONMENT == "production" and request.url.scheme == "https":
                response.headers["Strict-Transport-Security"] = (
                    "max-age=31536000; includeSubDomains; preload"
                )
            
            # X-Frame-Options - 防止点击劫持
            response.headers["X-Frame-Options"] = "DENY"
            
            # X-Content-Type-Options - 防止MIME类型嗅探
            response.headers["X-Content-Type-Options"] = "nosniff"
            
            # X-XSS-Protection - XSS过滤器（已弃用但仍有兼容性价值）
            response.headers["X-XSS-Protection"] = "1; mode=block"
            
            # Referrer-Policy - 控制引用信息泄露
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            
            # Permissions-Policy - 控制浏览器功能权限
            response.headers["Permissions-Policy"] = (
                "geolocation=(), "
                "microphone=(), "
                "camera=(), "
                "payment=(), "
                "usb=(), "
                "magnetometer=(), "
                "gyroscope=()"
            )
            
            # Cross-Origin-Embedder-Policy - 限制跨域嵌入
            response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
            
            # Cross-Origin-Opener-Policy - 限制跨域打开窗口
            response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
            
            # Cross-Origin-Resource-Policy - 限制跨域资源
            response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
            
            # Content-Security-Policy - 基础CSP（前端会通过meta标签注入更详细的）
            # 注意：CSP主要通过前端的meta标签或HTTP头部设置
            # 这里只设置基础策略，前端会覆盖这个头部
            if "Content-Security-Policy" not in response.headers:
                response.headers["Content-Security-Policy"] = self.base_csp
            
            # 添加安全相关的自定义头部
            response.headers["X-Powered-By"] = ""  # 移除X-Powered-By（隐藏技术栈信息）
            
            # 添加安全标志
            response.headers["X-Content-Type-Options"] = "nosniff"
            
        return response

