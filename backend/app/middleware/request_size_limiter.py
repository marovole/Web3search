"""
请求体大小限制中间件
限制HTTP请求的大小，防止DoS攻击和资源滥用

功能：
1. 根据请求类型设置不同的大小限制
2. 记录超大请求的详细信息
3. 提供可配置的限制策略
4. 支持IP级别的限制
5. 统计和监控功能
"""

import logging
import time
from typing import Dict, Optional
from datetime import datetime, timedelta
from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class RequestSizeLimiterMiddleware(BaseHTTPMiddleware):
    """请求体大小限制中间件"""

    def __init__(
        self,
        app,
        max_size: Optional[int] = None,
        max_upload_size: Optional[int] = None,
        enabled: bool = True,
        ip_block_duration: int = 300,  # 5分钟
        max_violations_per_ip: int = 10,
        max_violations_per_hour: int = 100
    ):
        super().__init__(app)
        self.enabled = enabled

        # 默认大小限制（字节）
        self.default_limits = {
            'GET': 64 * 1024,          # 64KB
            'POST': 10 * 1024 * 1024,   # 10MB
            'PUT': 10 * 1024 * 1024,    # 10MB
            'PATCH': 1 * 1024 * 1024,   # 1MB
            'DELETE': 64 * 1024,       # 64KB
            'HEAD': 64 * 1024,        # 64KB
            'OPTIONS': 64 * 1024,      # 64KB
        }

        # 自定义限制
        if max_size:
            self.default_limits = {method: max_size for method in self.default_limits}

        # 文件上传限制
        self.upload_limits = {
            'application/pdf': 50 * 1024 * 1024,      # 50MB
            'image/jpeg': 20 * 1024 * 1024,       # 20MB
            'image/png': 20 * 1024 * 1024,         # 20MB
            'image/gif': 10 * 1024 * 1024,         # 10MB
            'text/plain': 1 * 1024 * 1024,         # 1MB
            'application/json': 5 * 1024 * 1024,    # 5MB
            'multipart/form-data': max_upload_size or (100 * 1024 * 1024),  # 100MB
        }

        # IP违规记录
        self.ip_violations: Dict[str, Dict] = {}

        # 全局统计
        self.stats = {
            'total_requests': 0,
            'blocked_requests': 0,
            'oversized_requests': 0,  # 超大请求计数
            'total_bytes_processed': 0,
            'largest_request': 0,
            'violations_by_method': {},
            'violations_by_content_type': {},
            'blocked_ips': set(),
            'start_time': datetime.utcnow()
        }

        # 配置
        self.ip_block_duration = ip_block_duration
        self.max_violations_per_ip = max_violations_per_ip
        self.max_violations_per_hour = max_violations_per_hour

    async def dispatch(self, request: Request, call_next):
        """处理请求并检查大小限制"""

        if not self.enabled:
            return await call_next(request)

        # 更新统计
        self.stats['total_requests'] += 1

        # 获取客户端IP
        client_ip = self.get_client_ip(request)

        # 检查IP是否被阻止
        if self.is_ip_blocked(client_ip):
            return self.create_block_response(client_ip, "IP address temporarily blocked due to repeated violations")

        # 获取请求大小（优先 Content-Length，缺失时兜底读取以避免绕过）
        content_length = request.headers.get('content-length')
        if content_length:
            try:
                request_size = int(content_length)
            except (ValueError, TypeError):
                request_size = 0
        else:
            request_size = 0

        # 无 Content-Length 或为 0 且可能有负载时，实际读取一次以获得真实大小
        if request_size == 0 and request.method in {'POST', 'PUT', 'PATCH'}:
            body = await request.body()
            request_size = len(body)

        # 获取内容类型
        content_type = request.headers.get('content-type', '').split(';')[0].strip()

        # 确保IP记录存在（避免KeyError）
        if client_ip not in self.ip_violations:
            self.ip_violations[client_ip] = {
                'violations': [],
                'hourly_violations': [],
                'blocked_until': None,
                'block_count': 0,
            }

        # 确定允许的最大大小
        max_allowed_size = self.get_max_allowed_size(request.method, content_type)

        # 检查请求大小
        if request_size > max_allowed_size:
            # 记录违规
            await self.handle_oversized_request(request, client_ip, request_size, max_allowed_size, content_type)

            # 立即拒绝超大请求（不继续处理）
            self.stats['oversized_requests'] += 1
            return self.create_size_exceeded_response(request_size, max_allowed_size)

        # 处理请求
        response = await call_next(request)

        # 更新统计
        self.stats['total_bytes_processed'] += request_size
        if request_size > self.stats['largest_request']:
            self.stats['largest_request'] = request_size

        return response

    def get_client_ip(self, request: Request) -> str:
        """获取客户端IP地址"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        if request.client:
            return request.client.host

        return "unknown"

    def get_max_allowed_size(self, method: str, content_type: str) -> int:
        """获取允许的最大请求大小"""
        # 根据内容类型确定限制
        if content_type in self.upload_limits:
            return self.upload_limits[content_type]

        # 根据HTTP方法确定限制
        return self.default_limits.get(method.upper(), self.default_limits['POST'])

    def is_ip_blocked(self, client_ip: str) -> bool:
        """检查IP是否被阻止"""
        if client_ip not in self.ip_violations:
            return False

        violations = self.ip_violations[client_ip]

        # 检查是否在阻止期内
        if 'blocked_until' in violations:
            if datetime.utcnow() < violations['blocked_until']:
                return True
            else:
                # 阻止期已过，清除阻止状态
                violations['blocked_until'] = None
                if 'block_count' in violations:
                    violations['block_count'] = max(0, violations['block_count'] - 1)

        # 检查是否超过小时限制
        if 'hourly_violations' in violations:
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            violations['hourly_violations'] = [
                v for v in violations['hourly_violations']
                if v['timestamp'] > one_hour_ago
            ]

            if len(violations['hourly_violations']) >= self.max_violations_per_hour:
                return True

        return False

    def should_block_client(self, client_ip: str) -> bool:
        """判断是否应该阻止客户端"""
        if client_ip not in self.ip_violations:
            self.ip_violations[client_ip] = {
                'violations': [],
                'hourly_violations': [],
                'block_count': 0
            }

        violations = self.ip_violations[client_ip]

        # 检查违规次数
        if len(violations['violations']) >= self.max_violations_per_ip:
            # 设置阻止状态
            violations['blocked_until'] = datetime.utcnow() + timedelta(seconds=self.ip_block_duration)
            violations['block_count'] = violations.get('block_count', 0) + 1

            logger.warning(f"🚫 IP {client_ip} 已被阻止，违规次数: {len(violations['violations'])}")
            self.stats['blocked_ips'].add(client_ip)

            return True

        return False

    async def handle_oversized_request(
        self,
        request: Request,
        client_ip: str,
        request_size: int,
        max_size: int,
        content_type: str
    ):
        """处理超大请求"""
        # 记录违规
        violation = {
            'timestamp': datetime.utcnow(),
            'method': request.method,
            'url': str(request.url),
            'size': request_size,
            'max_size': max_size,
            'content_type': content_type,
            'user_agent': request.headers.get('User-Agent', 'Unknown')
        }

        self.ip_violations[client_ip]['violations'].append(violation)
        self.ip_violations[client_ip]['hourly_violations'].append(violation)

        # 更新统计
        self.stats['blocked_requests'] += 1
        method_key = request.method.upper()
        self.stats['violations_by_method'][method_key] = \
            self.stats['violations_by_method'].get(method_key, 0) + 1

        if content_type:
            self.stats['violations_by_content_type'][content_type] = \
                self.stats['violations_by_content_type'].get(content_type, 0) + 1

        # 记录详细日志
        logger.warning(
            f"📏 超大请求检测 - IP: {client_ip}, "
            f"方法: {request.method}, 大小: {request_size}B, "
            f"限制: {max_size}B, URL: {request.url}"
        )

    def create_block_response(self, client_ip: str, message: str) -> JSONResponse:
        """创建IP阻止响应"""
        response_data = {
            "error": "Request blocked",
            "error_code": "IP_BLOCKED",
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "retry_after": self.ip_block_duration
        }

        return JSONResponse(
            content=response_data,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            headers={"Retry-After": str(self.ip_block_duration)}
        )

    def create_size_exceeded_response(self, request_size: int, max_size: int) -> JSONResponse:
        """创建大小超限响应"""
        response_data = {
            "error": "Request entity too large",
            "error_code": "REQUEST_SIZE_EXCEEDED",
            "message": f"Request size {request_size} bytes exceeds maximum allowed size {max_size} bytes",
            "timestamp": datetime.utcnow().isoformat(),
            "request_size": request_size,
            "max_size": max_size
        }

        return JSONResponse(
            content=response_data,
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
        )

    def get_statistics(self) -> Dict:
        """获取统计信息"""
        runtime = datetime.utcnow() - self.stats['start_time']

        return {
            **self.stats,
            'runtime_hours': runtime.total_seconds() / 3600,
            'blocked_ips_count': len(self.stats['blocked_ips']),
            'average_request_size': (
                self.stats['total_bytes_processed'] / self.stats['total_requests']
                if self.stats['total_requests'] > 0 else 0
            ),
            'enabled': self.enabled,
            'limits': {
                'default': self.default_limits,
                'uploads': self.upload_limits
            },
            'active_blocked_ips': len([
                ip for ip, violations in self.ip_violations.items()
                if violations.get('blocked_until') and
                violations['blocked_until'] > datetime.utcnow()
            ])
        }

    def get_ip_statistics(self, client_ip: str) -> Dict:
        """获取特定IP的统计信息"""
        if client_ip not in self.ip_violations:
            return {'violations': 0, 'blocked': False}

        violations = self.ip_violations[client_ip]
        return {
            'total_violations': len(violations['violations']),
            'hourly_violations': len(violations['hourly_violations']),
            'blocked_until': violations.get('blocked_until'),
            'block_count': violations.get('block_count', 0),
            'is_blocked': self.is_ip_blocked(client_ip),
            'recent_violations': [
                {
                    'timestamp': v['timestamp'].isoformat(),
                    'method': v['method'],
                    'size': v['size'],
                    'url': v['url']
                }
                for v in violations['violations'][-5:]  # 最近5次违规
            ]
        }

    def unblock_ip(self, client_ip: str) -> bool:
        """手动解除IP阻止"""
        if client_ip in self.ip_violations:
            violations = self.ip_violations[client_ip]
            violations['blocked_until'] = None
            violations['violations'].clear()
            violations['hourly_violations'].clear()
            violations['block_count'] = max(0, violations.get('block_count', 0) - 1)

            if client_ip in self.stats['blocked_ips']:
                self.stats['blocked_ips'].discard(client_ip)

            logger.info(f"🔓 IP {client_ip} 已解除阻止")
            return True

        return False

    def clear_old_violations(self):
        """清理旧的违规记录"""
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)

        stale_ips = []
        for client_ip, violations in self.ip_violations.items():
            # 清理小时内的违规记录
            violations['hourly_violations'] = [
                v for v in violations['hourly_violations']
                if v['timestamp'] > one_hour_ago
            ]

            # 如果没有违规记录且不在阻止期内，标记待删除
            if (not violations['violations'] and
                not violations.get('blocked_until') and
                violations.get('block_count', 0) <= 0):
                stale_ips.append(client_ip)

        for ip in stale_ips:
            self.ip_violations.pop(ip, None)

        if stale_ips:
            logger.info("🧹 已清理旧的违规记录: %s", stale_ips)