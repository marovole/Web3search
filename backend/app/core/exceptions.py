"""
自定义异常类
定义应用中使用的各种异常类型
"""
from typing import Any, Dict, Optional


class Web3SearchException(Exception):
    """基础异常类"""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


# ================================
# 数据采集异常
# ================================


class DataCollectionError(Web3SearchException):
    """数据采集失败"""

    def __init__(self, message: str, source: str, details: Optional[Dict] = None):
        super().__init__(
            message=f"数据采集失败 ({source}): {message}",
            code="DATA_COLLECTION_ERROR",
            status_code=503,
            details={"source": source, **(details or {})},
        )


class APIRateLimitError(Web3SearchException):
    """API速率限制"""

    def __init__(self, message: str, source: str, retry_after: Optional[int] = None):
        super().__init__(
            message=f"API速率限制 ({source}): {message}",
            code="RATE_LIMIT_ERROR",
            status_code=429,
            details={"source": source, "retry_after": retry_after},
        )


class DataSourceUnavailable(Web3SearchException):
    """数据源不可用"""

    def __init__(self, message: str, source: str):
        super().__init__(
            message=f"数据源不可用 ({source}): {message}",
            code="DATA_SOURCE_UNAVAILABLE",
            status_code=503,
            details={"source": source},
        )


# ================================
# AI/LLM相关异常
# ================================


class LLMError(Web3SearchException):
    """LLM调用失败"""

    def __init__(self, message: str, model: str, details: Optional[Dict] = None):
        super().__init__(
            message=f"LLM调用失败 ({model}): {message}",
            code="LLM_ERROR",
            status_code=503,
            details={"model": model, **(details or {})},
        )


class LLMTimeoutError(Web3SearchException):
    """LLM超时"""

    def __init__(self, message: str, model: str, timeout: int):
        super().__init__(
            message=f"LLM超时 ({model}): {message}",
            code="LLM_TIMEOUT",
            status_code=504,
            details={"model": model, "timeout": timeout},
        )


# ================================
# 业务逻辑异常
# ================================


class ValidationError(Web3SearchException):
    """数据验证失败"""

    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            message=f"数据验证失败: {message}",
            code="VALIDATION_ERROR",
            status_code=400,
            details={"field": field} if field else {},
        )


class ResourceNotFound(Web3SearchException):
    """资源不存在"""

    def __init__(self, message: str, resource_type: str, resource_id: Any):
        super().__init__(
            message=f"{resource_type}不存在: {message}",
            code="RESOURCE_NOT_FOUND",
            status_code=404,
            details={"resource_type": resource_type, "resource_id": str(resource_id)},
        )


class PermissionDenied(Web3SearchException):
    """权限不足"""

    def __init__(self, message: str):
        super().__init__(
            message=f"权限不足: {message}",
            code="PERMISSION_DENIED",
            status_code=403,
        )


# ================================
# 缓存相关异常
# ================================


class CacheError(Web3SearchException):
    """缓存操作失败"""

    def __init__(self, message: str, operation: str):
        super().__init__(
            message=f"缓存操作失败 ({operation}): {message}",
            code="CACHE_ERROR",
            status_code=500,
            details={"operation": operation},
        )


# ================================
# 数据库相关异常
# ================================


class DatabaseError(Web3SearchException):
    """数据库操作失败"""

    def __init__(self, message: str, operation: str):
        super().__init__(
            message=f"数据库操作失败 ({operation}): {message}",
            code="DATABASE_ERROR",
            status_code=500,
            details={"operation": operation},
        )


# ================================
# 重试和断路器相关异常（任务5.6）
# ================================


class CircuitBreakerOpenError(Web3SearchException):
    """断路器熔断错误"""

    def __init__(self, message: str, service_name: str, retry_after: Optional[int] = None):
        super().__init__(
            message=f"服务断路器已熔断 ({service_name}): {message}",
            code="CIRCUIT_BREAKER_OPEN",
            status_code=503,
            details={"service_name": service_name, "retry_after": retry_after},
        )


class RetryExhaustedError(Web3SearchException):
    """重试次数耗尽"""

    def __init__(self, message: str, attempts: int, last_error: Optional[str] = None):
        super().__init__(
            message=f"重试次数已耗尽 ({attempts}次): {message}",
            code="RETRY_EXHAUSTED",
            status_code=503,
            details={"attempts": attempts, "last_error": last_error},
        )
