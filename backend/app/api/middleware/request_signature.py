"""
请求签名验证中间件
实现API请求的完整性验证，防止请求篡改
"""
import hashlib
import hmac
import time
from typing import Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings


class RequestSignatureMiddleware(BaseHTTPMiddleware):
    """
    请求签名验证中间件

    验证API请求的签名，确保请求在传输过程中未被篡改
    实现基于HMAC-SHA256的签名机制
    """

    def __init__(self, app, enabled: bool = True):
        super().__init__(app)
        self.enabled = enabled and settings.ENVIRONMENT in ('production', 'prod')

        # 签名相关的配置
        self.signature_header = "X-Signature"
        self.timestamp_header = "X-Timestamp"
        self.api_key_header = "X-API-Key"
        self.max_time_diff = 300  # 5分钟时间窗口

    async def dispatch(self, request: Request, call_next):
        # 如果未启用签名验证，直接继续
        if not self.enabled:
            return await call_next(request)

        # 排除不需要签名验证的路径
        if self._should_skip_signature(request):
            return await call_next(request)

        # 验证签名
        await self._verify_signature(request)

        return await call_next(request)

    def _should_skip_signature(self, request: Request) -> bool:
        """判断是否应该跳过签名验证"""
        skip_paths = [
            "/health",
            "/metrics",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/docs",
            "/redoc",
            "/openapi.json",
        ]

        return any(request.url.path.startswith(path) for path in skip_paths)

    async def _verify_signature(self, request: Request):
        """验证请求签名"""
        # 获取必要的头部
        signature = request.headers.get(self.signature_header)
        timestamp = request.headers.get(self.timestamp_header)
        api_key = request.headers.get(self.api_key_header)

        if not all([signature, timestamp, api_key]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="缺少必要的签名验证头部",
                headers={
                    "X-Required-Headers": f"{self.signature_header}, {self.timestamp_header}, {self.api_key_header}"
                }
            )

        # 验证时间戳（防止重放攻击）
        try:
            request_time = int(timestamp)
            current_time = int(time.time())

            if abs(current_time - request_time) > self.max_time_diff:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"请求时间戳无效，时间差超过{self.max_time_diff}秒"
                )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的时间戳格式"
            )

        # 获取请求体（用于签名计算）
        body = await self._get_request_body(request)

        # 计算预期签名
        expected_signature = self._calculate_signature(
            method=request.method,
            path=str(request.url.path),
            query=request.url.query,
            body=body,
            timestamp=timestamp,
            api_key=api_key
        )

        # 验证签名
        if not hmac.compare_digest(signature, expected_signature):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="请求签名验证失败"
            )

    async def _get_request_body(self, request: Request) -> bytes:
        """获取请求体内容"""
        try:
            # 对于GET请求，body为空
            if request.method in ("GET", "HEAD", "DELETE"):
                return b""

            # 对于其他请求，读取body
            body = await request.body()
            return body
        except Exception:
            # 如果无法读取body，使用空字符串
            return b""

    def _calculate_signature(
        self,
        method: str,
        path: str,
        query: str,
        body: bytes,
        timestamp: str,
        api_key: str
    ) -> str:
        """
        计算请求签名

        签名算法：
        1. 构造签名字符串：METHOD + PATH + QUERY + BODY + TIMESTAMP
        2. 使用HMAC-SHA256和API密钥计算签名
        3. 返回十六进制格式的签名
        """
        # 构造签名字符串
        message_parts = [
            method.upper(),
            path,
            query or "",
            body.decode('utf-8', errors='ignore') if body else "",
            timestamp
        ]

        message = "\n".join(message_parts)

        # 使用API密钥的HMAC-SHA256计算签名
        # 注意：这里应该使用专门的签名密钥，而不是API密钥
        secret_key = self._get_signature_secret(api_key)

        signature = hmac.new(
            secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        return signature

    def _get_signature_secret(self, api_key: str) -> str:
        """
        根据API密钥获取签名密钥

        在实际应用中，这里应该查询数据库或其他存储系统
        获取与API密钥对应的签名密钥
        """
        # 简化实现：使用环境变量中的密钥
        # 实际应用中应该有更复杂的API密钥管理机制
        base_secret = getattr(settings, 'SIGNATURE_SECRET_KEY', None)

        if not base_secret:
            raise ValueError("未配置签名密钥")

        # 使用API密钥和基础密钥生成唯一的签名密钥
        unique_secret = hmac.new(
            base_secret.encode('utf-8'),
            api_key.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        return unique_secret


class APIKeyManager:
    """
    API密钥管理器

    管理API密钥的生成、验证和撤销
    """

    @staticmethod
    def generate_api_key() -> str:
        """生成新的API密钥"""
        import secrets
        return f"web3search_{secrets.token_urlsafe(32)}"

    @staticmethod
    def validate_api_key_format(api_key: str) -> bool:
        """验证API密钥格式"""
        if not api_key:
            return False

        # 检查前缀
        if not api_key.startswith("web3search_"):
            return False

        # 检查长度
        if len(api_key) < 20:
            return False

        return True

    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """对API密钥进行哈希处理"""
        return hashlib.sha256(api_key.encode('utf-8')).hexdigest()