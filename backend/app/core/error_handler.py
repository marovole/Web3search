"""
全局错误处理器
处理各种异常并返回用户友好的错误响应
"""
import logging
from typing import Dict, Any
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import Web3SearchException
from app.core.config import settings

logger = logging.getLogger(__name__)


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
        message: 错误消息
        status_code: HTTP状态码
        details: 额外详情（仅在DEBUG模式显示）
        request_id: 请求ID

    Returns:
        格式化的错误响应
    """
    response = {
        "error": {
            "code": error_code,
            "message": message,
            "status": status_code,
        }
    }

    # 仅在DEBUG模式显示详细信息
    if settings.DEBUG and details:
        response["error"]["details"] = details

    if request_id:
        response["error"]["request_id"] = request_id

    return response


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
    logger.warning(
        f"Validation error on {request.url.path}: {exc.errors()}",
        extra={"path": request.url.path, "errors": exc.errors()},
    )

    # 格式化验证错误
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append({"field": field, "message": error["msg"], "type": error["type"]})

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

    # 记录详细错误信息
    logger.error(
        f"Unhandled exception on {request.url.path}: {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method,
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

    # 生产环境：返回通用错误消息
    if not settings.DEBUG:
        message = "服务暂时不可用，请稍后重试"
        details = None
    else:
        # 开发环境：返回详细错误信息
        message = str(exc)
        details = {"traceback": traceback.format_exc()}

    response = format_error_response(
        error_code="INTERNAL_ERROR",
        message=message,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        details=details,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=response
    )
