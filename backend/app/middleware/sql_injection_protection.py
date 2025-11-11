"""
SQL注入防护中间件
在所有API请求中自动检测和防护SQL注入攻击

功能：
1. 检测URL参数中的SQL注入模式
2. 检测请求体中的恶意内容
3. 记录可疑请求
4. 阻止恶意请求
5. 提供详细的攻击日志
"""

import logging
import time
import json
import re
from typing import Dict, List, Optional
from datetime import datetime
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.input_validation import SecurityValidator

logger = logging.getLogger(__name__)


class SQLInjectionProtectionMiddleware(BaseHTTPMiddleware):
    """SQL注入防护中间件"""

    def __init__(self, app, enabled: bool = True, log_only: bool = False):
        super().__init__(app)
        self.enabled = enabled
        self.log_only = log_only  # 如果为True，只记录不阻止

        # SQL注入检测模式 - 预编译正则表达式
        sql_pattern_strings = [
            # 基础SQL关键字
            r"(?i)\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b",
            # SQL注释
            r"(?i)(--|/\*|\*/|;)",
            # 布尔注入
            r"(?i)(\bOR\b|\bAND\b)\s+\d+\s*=\s*\d+",
            r"(?i)(\bOR\b|\bAND\b)\s+['\"]?\w+['\"]?\s*=\s*['\"]?\w+['\"]?",
            # 时间延迟攻击
            r"(?i)(WAITFOR\s+DELAY|SLEEP\s*\(|BENCHMARK\s*\()",
            # 字符函数
            r"(?i)(CHAR\s*\(|ASCII\s*\(|ORD\s*\()",
            # 系统表访问
            r"(?i)(INFORMATION_SCHEMA|SYS\.|MASTER\.)",
            # 十六进制编码
            r"(?i)(0x[0-9a-fA-F]+|X'[0-9a-fA-F]+')",
            # 特殊字符组合
            r"(?i)['"]?\s*(\||\+|-)\s*['\"]?\d+['\"]?",
        ]
        self.sql_patterns = [re.compile(pattern) for pattern in sql_pattern_strings]

        # 高风险模式（立即阻止） - 预编译正则表达式
        high_risk_pattern_strings = [
            r"(?i)(DROP\s+(TABLE|DATABASE|INDEX))",
            r"(?i)(DELETE\s+FROM\s+\w+)",
            r"(?i)(UPDATE\s+\w+\s+SET)",
            r"(?i)(INSERT\s+INTO\s+\w+)",
            r"(?i)(EXEC\s*\(|EXECUTE\s*\()",
            r"(?i)(xp_cmdshell|sp_oacreate|sp_adduser)",
        ]
        self.high_risk_patterns = [re.compile(pattern) for pattern in high_risk_pattern_strings]

        # 绕过的路径（不需要检查的路径）
        self.skip_paths = [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/favicon.ico",
            "/robots.txt",
            "/static/",
        ]

        # 攻击统计
        self.attack_stats = {
            'total_requests': 0,
            'blocked_requests': 0,
            'suspicious_requests': 0,
            'attack_types': {},
        }

    async def dispatch(self, request: Request, call_next):
        """处理请求并检查SQL注入"""

        if not self.enabled:
            return await call_next(request)

        # 更新请求统计
        self.attack_stats['total_requests'] += 1

        # 检查是否需要跳过
        if self.should_skip_path(request.url.path):
            return await call_next(request)

        # 执行SQL注入检测
        injection_result = await self.detect_sql_injection(request)

        if injection_result.detected:
            await self.handle_sql_injection(request, injection_result)

            if not self.log_only:
                return self.create_block_response(injection_result)

        return await call_next(request)

    def should_skip_path(self, path: str) -> bool:
        """判断是否跳过检查"""
        return any(path.startswith(skip_path) for skip_path in self.skip_paths)

    async def detect_sql_injection(self, request: Request) -> 'SQLInjectionResult':
        """检测SQL注入攻击"""
        result = SQLInjectionResult(detected=False)

        # 检查URL参数
        url_injection = self.check_url_parameters(request)
        if url_injection.detected:
            result.merge(url_injection)

        # 检查查询参数
        query_injection = self.check_query_parameters(request)
        if query_injection.detected:
            result.merge(query_injection)

        # 检查请求头
        header_injection = self.check_headers(request)
        if header_injection.detected:
            result.merge(header_injection)

        # 检查请求体（仅对POST/PUT请求）
        if request.method in ['POST', 'PUT', 'PATCH']:
            body_injection = await self.check_request_body(request)
            if body_injection.detected:
                result.merge(body_injection)

        return result

    def check_url_parameters(self, request: Request) -> 'SQLInjectionResult':
        """检查URL参数中的SQL注入"""
        result = SQLInjectionResult(detected=False)

        # 检查路径参数
        path_parts = request.url.path.split('/')
        for part in path_parts:
            if part and self.check_sql_injection_patterns(part):
                result.add_detection(
                    location="url_path",
                    value=part,
                    patterns=self.matched_patterns(part)
                )

        return result

    def check_query_parameters(self, request: Request) -> 'SQLInjectionResult':
        """检查查询参数中的SQL注入"""
        result = SQLInjectionResult(detected=False)

        for param_name, param_value in request.query_params.items():
            if isinstance(param_value, str) and self.check_sql_injection_patterns(param_value):
                result.add_detection(
                    location="query_param",
                    parameter=param_name,
                    value=param_value,
                    patterns=self.matched_patterns(param_value)
                )

        return result

    def check_headers(self, request: Request) -> 'SQLInjectionResult':
        """检查请求头中的SQL注入"""
        result = SQLInjectionResult(detected=False)

        # 检查常见的可能被利用的头部
        suspicious_headers = [
            'User-Agent', 'Referer', 'X-Forwarded-For',
            'X-Real-IP', 'X-Requested-With', 'Authorization'
        ]

        for header_name in suspicious_headers:
            header_value = request.headers.get(header_name)
            if header_value and isinstance(header_value, str):
                if self.check_sql_injection_patterns(header_value):
                    result.add_detection(
                        location="header",
                        header=header_name,
                        value=header_value,
                        patterns=self.matched_patterns(header_value)
                    )

        return result

    async def check_request_body(self, request: Request) -> 'SQLInjectionResult':
        """检查请求体中的SQL注入"""
        result = SQLInjectionResult(detected=False)

        try:
            # 获取请求体
            body = await request.body()

            if not body:
                return result

            # 解析JSON
            try:
                body_data = json.loads(body.decode('utf-8'))
                if isinstance(body_data, dict):
                    body_injection = self.check_data_dict(body_data, "body")
                    if body_injection.detected:
                        result.merge(body_injection)
            except (json.JSONDecodeError, UnicodeDecodeError):
                # 如果不是JSON，检查原始文本
                text_body = body.decode('utf-8', errors='ignore')
                if self.check_sql_injection_patterns(text_body):
                    result.add_detection(
                        location="body",
                        value=text_body[:100],
                        patterns=self.matched_patterns(text_body)
                    )

        except Exception as e:
            logger.error(f"检查请求体时出错: {e}")

        return result

    def check_data_dict(self, data: dict, location: str) -> 'SQLInjectionResult':
        """递归检查字典数据中的SQL注入"""
        result = SQLInjectionResult(detected=False)

        for key, value in data.items():
            if isinstance(value, str) and self.check_sql_injection_patterns(value):
                result.add_detection(
                    location=location,
                    parameter=key,
                    value=value[:100],
                    patterns=self.matched_patterns(value)
                )
            elif isinstance(value, dict):
                nested_result = self.check_data_dict(value, f"{location}.{key}")
                if nested_result.detected:
                    result.merge(nested_result)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, str) and self.check_sql_injection_patterns(item):
                        result.add_detection(
                            location=location,
                            parameter=f"{key}[{i}]",
                            value=item[:100],
                            patterns=self.matched_patterns(item)
                        )
                    elif isinstance(item, dict):
                        nested_result = self.check_data_dict(item, f"{location}.{key}[{i}]")
                        if nested_result.detected:
                            result.merge(nested_result)

        return result

    def check_sql_injection_patterns(self, text: str) -> bool:
        """检查文本是否匹配SQL注入模式"""
        for pattern in self.sql_patterns:
            if pattern.search(text):
                return True
        return False

    def matched_patterns(self, text: str) -> List[str]:
        """返回匹配的模式"""
        matched = []
        for pattern in self.sql_patterns:
            if pattern.search(text):
                matched.append(pattern.pattern)
        return matched

    def is_high_risk(self, patterns: List[str]) -> bool:
        """检查是否为高风险模式"""
        for pattern in patterns:
            for high_risk_pattern in self.high_risk_patterns:
                if high_risk_pattern.search(pattern):
                    return True
        return False

    async def handle_sql_injection(self, request: Request, injection_result: 'SQLInjectionResult'):
        """处理SQL注入检测"""

        # 更新统计
        self.attack_stats['suspicious_requests'] += 1
        if injection_result.is_high_risk:
            self.attack_stats['blocked_requests'] += 1

        # 更新攻击类型统计
        for detection in injection_result.detections:
            for pattern in detection.patterns:
                self.attack_stats['attack_types'][pattern] = \
                    self.attack_stats['attack_types'].get(pattern, 0) + 1

        # 记录详细信息
        await self.log_attack_attempt(request, injection_result)

    async def log_attack_attempt(self, request: Request, injection_result: 'SQLInjectionResult'):
        """记录攻击尝试"""
        client_ip = self.get_client_ip(request)
        user_agent = request.headers.get('User-Agent', 'Unknown')

        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'client_ip': client_ip,
            'method': request.method,
            'url': str(request.url),
            'user_agent': user_agent,
            'detections': [
                {
                    'location': d.location,
                    'parameter': d.parameter,
                    'value': d.value[:50] + '...' if len(d.value) > 50 else d.value,
                    'patterns': d.patterns
                }
                for d in injection_result.detections
            ],
            'is_high_risk': injection_result.is_high_risk,
            'action': 'blocked' if not self.log_only else 'logged_only'
        }

        logger.warning(f"🚨 SQL注入攻击检测: {json.dumps(log_data, indent=2)}")

    def get_client_ip(self, request: Request) -> str:
        """获取客户端IP地址"""
        # 检查代理头
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        if request.client:
            return request.client.host

        return "unknown"

    def create_block_response(self, injection_result: 'SQLInjectionResult') -> JSONResponse:
        """创建阻止响应"""
        response_data = {
            "error": "Request blocked due to security policy",
            "error_code": "SQL_INJECTION_DETECTED",
            "timestamp": datetime.utcnow().isoformat(),
            "details": "Your request contains potentially malicious content"
        }

        return JSONResponse(
            content=response_data,
            status_code=status.HTTP_403_FORBIDDEN
        )

    def get_statistics(self) -> Dict:
        """获取防护统计信息"""
        total = self.attack_stats['total_requests']
        blocked = self.attack_stats['blocked_requests']

        return {
            **self.attack_stats,
            'block_rate': f"{(blocked/total*100):.2f}%" if total > 0 else "0%",
            'enabled': self.enabled,
            'log_only': self.log_only
        }


class SQLInjectionResult:
    """SQL注入检测结果"""

    def __init__(self, detected: bool = False):
        self.detected = detected
        self.detections: List[Dict] = []

    def add_detection(self, location: str, value: str, patterns: List[str],
                      parameter: Optional[str] = None, header: Optional[str] = None):
        """添加检测结果"""
        detection = {
            'location': location,
            'value': value,
            'patterns': patterns,
            'timestamp': datetime.utcnow().isoformat()
        }

        if parameter:
            detection['parameter'] = parameter
        if header:
            detection['header'] = header

        self.detections.append(detection)
        self.detected = True

    def merge(self, other: 'SQLInjectionResult'):
        """合并检测结果"""
        self.detected = self.detected or other.detected
        self.detections.extend(other.detections)

    @property
    def is_high_risk(self) -> bool:
        """检查是否为高风险攻击"""
        for detection in self.detections:
            for pattern in detection['patterns']:
                # 检查高风险模式
                high_risk_patterns = [
                    r'DROP\s+TABLE',
                    r'DELETE\s+FROM',
                    r'UPDATE\s+SET',
                    r'INSERT\s+INTO',
                    r'EXEC\s*\(',
                    r'xp_cmdshell'
                ]
                for high_risk in high_risk_patterns:
                    if re.search(high_risk, pattern, re.IGNORECASE):
                        return True
        return False