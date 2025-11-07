"""
全局错误处理器
处理各种异常并返回用户友好的错误响应
确保生产环境不泄露敏感信息
"""
import logging
import re
from typing import Dict, Any, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import Web3SearchException
from app.core.config import settings

logger = logging.getLogger(__name__)

# 敏感信息模式（用于过滤错误消息）
SENSITIVE_PATTERNS = [
    r'password["\']?\s*[:=]\s*["\']?[^"\']+',  # password: xxx
    r'secret["\']?\s*[:=]\s*["\']?[^"\']+',  # secret: xxx
    r'api[_-]?key["\']?\s*[:=]\s*["\']?[^"\']+',  # api_key: xxx
    r'token["\']?\s*[:=]\s*["\']?[^"\']+',  # token: xxx
    r'authorization["\']?\s*[:=]\s*["\']?[^"\']+',  # authorization: xxx
    r'/home/[^/]+/',  # 文件路径
    r'/Users/[^/]+/',  # macOS用户路径
    r'/root/',  # root路径
    r'C:\\Users\\[^\\]+\\',  # Windows用户路径
]


def sanitize_error_message(message: str) -> str:
    """
    清理错误消息中的敏感信息
    
    Args:
        message: 原始错误消息
        
    Returns:
        清理后的错误消息
    """
    sanitized = message
    
    # 在生产环境中，过滤敏感信息
    if not settings.DEBUG:
        for pattern in SENSITIVE_PATTERNS:
            sanitized = re.sub(pattern, '[REDACTED]', sanitized, flags=re.IGNORECASE)
        
        # 移除文件路径中的用户名部分
        sanitized = re.sub(r'/[^/]+/[^/]+/', '/***/', sanitized)
    
    return sanitized


def format_error_response(
    error_code: str,
    message: str,
    status_code: int,
    details: Dict[str, Any] = None,
    request_id: str = None,
) -> Dict[str, Any]:
    """
    格式化错误响应

    Args:
        error_code: 错误代码
        message: 错误消息（会自动清理敏感信息）
        status_code: HTTP状态码
        details: 额外详情（仅在DEBUG模式显示，且会清理敏感信息）
        request_id: 请求ID

    Returns:
        格式化的错误响应
    """
    # 清理错误消息
    safe_message = sanitize_error_message(message)
    
    response = {
        "error": {
            "code": error_code,
            "message": safe_message,
            "status": status_code,
        }
    }

    # 仅在DEBUG模式显示详细信息，且清理敏感信息
    if settings.DEBUG and details:
        safe_details = sanitize_details(details)
        response["error"]["details"] = safe_details
    elif not settings.DEBUG:
        # 生产环境：不返回任何详细信息，避免泄露内部实现
        pass

    if request_id:
        response["error"]["request_id"] = request_id

    return response


def sanitize_details(details: Dict[str, Any]) -> Dict[str, Any]:
    """
    清理详细信息中的敏感信息
    
    Args:
        details: 原始详细信息
        
    Returns:
        清理后的详细信息
    """
    if not isinstance(details, dict):
        return details
    
    safe_details = {}
    sensitive_keys = ['password', 'secret', 'token', 'api_key', 'authorization', 'key']
    
    for key, value in details.items():
        # 检查键名是否包含敏感词
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            safe_details[key] = '[REDACTED]'
        elif isinstance(value, str):
            safe_details[key] = sanitize_error_message(value)
        elif isinstance(value, dict):
            safe_details[key] = sanitize_details(value)
        elif isinstance(value, list):
            safe_details[key] = [
                sanitize_details(item) if isinstance(item, dict) else 
                sanitize_error_message(item) if isinstance(item, str) else item
                for item in value
            ]
        else:
            safe_details[key] = value
    
    return safe_details


async def web3search_exception_handler(
    request: Request, exc: Web3SearchException
) -> JSONResponse:
    """
    处理自定义异常

    Args:
        request: 请求对象
        exc: 自定义异常

    Returns:
        JSON响应
    """
    # 记录错误日志
    logger.error(
        f"Web3SearchException: {exc.code} - {exc.message}",
        extra={
            "error_code": exc.code,
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method,
            "details": exc.details,
        },
    )

    # 根据错误类型决定是否发送到Sentry
    if exc.status_code >= 500:
        # 服务器错误才发送到Sentry
        try:
            import sentry_sdk
            sentry_sdk.capture_exception(exc)
        except ImportError:
            pass  # Sentry未安装

    response = format_error_response(
        error_code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details if settings.DEBUG else None,
    )

    return JSONResponse(status_code=exc.status_code, content=response)


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    处理Pydantic验证异常

    Args:
        request: 请求对象
        exc: 验证异常

    Returns:
        JSON响应
    """
    # 记录验证错误（不记录敏感字段的值）
    logger.warning(
        f"Validation error on {request.url.path}",
        extra={"path": request.url.path, "error_count": len(exc.errors())},
    )

    # 格式化验证错误
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        # 清理错误消息中的敏感信息
        safe_message = sanitize_error_message(error["msg"])
        errors.append({
            "field": field, 
            "message": safe_message, 
            "type": error["type"]
        })

    # 生产环境：只返回字段名和类型，不返回具体错误值
    if not settings.DEBUG:
        errors = [
            {"field": e["field"], "type": e["type"]} 
            for e in errors
        ]

    response = format_error_response(
        error_code="VALIDATION_ERROR",
        message="请求参数验证失败",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details={"errors": errors} if settings.DEBUG else None,
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=response
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """
    处理HTTP异常

    Args:
        request: 请求对象
        exc: HTTP异常

    Returns:
        JSON响应
    """
    logger.warning(
        f"HTTP {exc.status_code} on {request.url.path}: {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "path": request.url.path,
            "detail": exc.detail,
        },
    )

    response = format_error_response(
        error_code=f"HTTP_{exc.status_code}",
        message=exc.detail if isinstance(exc.detail, str) else "请求处理失败",
        status_code=exc.status_code,
    )

    return JSONResponse(status_code=exc.status_code, content=response)


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    处理未捕获的异常

    Args:
        request: 请求对象
        exc: 异常对象

    Returns:
        JSON响应
    """
    import traceback

    # 记录详细错误信息（日志中保留完整信息）
    error_message = str(exc)
    logger.error(
        f"Unhandled exception on {request.url.path}: {error_message}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "exception_type": type(exc).__name__,
            "traceback": traceback.format_exc(),
        },
        exc_info=True,
    )

    # 发送到Sentry
    try:
        import sentry_sdk
        sentry_sdk.capture_exception(exc)
    except ImportError:
        pass

    # 生产环境：返回通用错误消息，不泄露任何内部信息
    if not settings.DEBUG:
        message = "服务暂时不可用，请稍后重试"
        details = None
    else:
        # 开发环境：返回详细错误信息（但也要清理敏感信息）
        message = sanitize_error_message(error_message)
        traceback_str = traceback.format_exc()
        # 清理traceback中的文件路径
        if not settings.DEBUG:
            traceback_str = sanitize_error_message(traceback_str)
        details = {"traceback": traceback_str, "exception_type": type(exc).__name__}

    response = format_error_response(
        error_code="INTERNAL_ERROR",
        message=message,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        details=details,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=response
    )
