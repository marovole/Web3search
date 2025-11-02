"""
分布式追踪中间件
提供完整的请求链路追踪和性能分析功能
"""
import time
import uuid
from typing import Callable, Dict, Any, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.monitoring import apm_collector, trace_operation
from app.core.opentelemetry_config import trace_span, otel_apm
import logging

logger = logging.getLogger(__name__)


class DistributedTracingMiddleware(BaseHTTPMiddleware):
    """
    分布式追踪中间件
    为每个HTTP请求创建完整的追踪链路
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.apm = otel_apm
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 生成唯一的追踪ID
        trace_id = str(uuid.uuid4())
        span_id = str(uuid.uuid4())[:8]
        
        # 提取或创建追踪上下文
        trace_context = self._extract_trace_context(request)
        trace_context.update({
            'trace_id': trace_id,
            'span_id': span_id,
            'parent_span_id': request.headers.get('x-parent-span-id'),
        })
        
        # 添加追踪头到请求
        request.state.trace_id = trace_id
        request.state.span_id = span_id
        request.state.trace_context = trace_context
        
        # 开始分布式追踪
        start_time = time.time()
        
        # 使用OpenTelemetry追踪
        with trace_span(
            f"http.{request.method.lower()}.{request.url.path.replace('/', '.')}",
            "http.request",
            lambda span: self._enrich_span(span, request, trace_context)
        ) if trace_span else trace_operation(
            f"http_{request.method.lower()}_{request.url.path.replace('/', '_')}",
            {"method": request.method, "path": request.url.path}
        ):
            
            # 记录请求开始
            logger.info(
                f"Request started: {request.method} {request.url.path}",
                extra={
                    "trace_id": trace_id,
                    "span_id": span_id,
                    "method": request.method,
                    "path": request.url.path,
                    "query_params": str(request.query_params),
                    "client_ip": request.client.host if request.client else None,
                }
            )
            
            # 执行请求
            try:
                response = await call_next(request)
                
                # 计算响应时间
                duration_ms = (time.time() - start_time) * 1000
                
                # 记录APM指标
                self._record_apm_metrics(request, response, duration_ms)
                
                # 添加追踪头到响应
                response.headers["x-trace-id"] = trace_id
                response.headers["x-span-id"] = span_id
                
                # 记录请求完成
                logger.info(
                    f"Request completed: {request.method} {request.url.path} - {response.status_code}",
                    extra={
                        "trace_id": trace_id,
                        "span_id": span_id,
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": response.status_code,
                        "duration_ms": round(duration_ms, 2),
                        "response_size": len(response.body) if hasattr(response, 'body') else 0,
                    }
                )
                
                return response
                
            except Exception as e:
                # 记录错误和异常
                duration_ms = (time.time() - start_time) * 1000
                
                logger.error(
                    f"Request failed: {request.method} {request.url.path} - {str(e)}",
                    extra={
                        "trace_id": trace_id,
                        "span_id": span_id,
                        "method": request.method,
                        "path": request.url.path,
                        "error": str(e),
                        "duration_ms": round(duration_ms, 2),
                    },
                    exc_info=True
                )
                
                # 记录错误指标
                apm_collector.record_external_api_call(
                    service_name="web3search_api",
                    endpoint=request.url.path,
                    method=request.method,
                    status_code=500,
                    duration_ms=duration_ms
                )
                
                raise
    
    def _extract_trace_context(self, request: Request) -> Dict[str, Any]:
        """
        从请求头中提取追踪上下文
        """
        headers = request.headers
        
        return {
            'traceparent': headers.get('traceparent'),
            'tracestate': headers.get('tracestate'),
            'x-trace-id': headers.get('x-trace-id'),
            'x-parent-span-id': headers.get('x-parent-span-id'),
            'x-request-id': headers.get('x-request-id'),
            'user_agent': headers.get('user-agent'),
            'forwarded_for': headers.get('x-forwarded-for'),
        }
    
    def _enrich_span(self, span, request: Request, trace_context: Dict[str, Any]):
        """
        丰富Span数据
        """
        if span:
            span.set_attribute('http.method', request.method)
            span.set_attribute('http.url', str(request.url))
            span.set_attribute('http.scheme', request.url.scheme)
            span.set_attribute('http.host', request.url.hostname)
            span.set_attribute('http.target', request.url.path)
            span.set_attribute('trace_id', trace_context['trace_id'])
            span.set_attribute('span_id', trace_context['span_id'])
            
            # 添加用户代理信息
            if 'user_agent' in trace_context:
                span.set_attribute('user_agent', trace_context['user_agent'])
    
    def _record_apm_metrics(self, request: Request, response: Response, duration_ms: float):
        """
        记录APM性能指标
        """
        # 记录API指标
        self.apm.record_api_metric(
            endpoint=request.url.path,
            method=request.method,
            status_code=response.status_code,
            duration_ms=duration_ms
        )
        
        # 记录到传统APM收集器
        apm_collector.record_external_api_call(
            service_name="web3search_api",
            endpoint=request.url.path,
            method=request.method,
            status_code=response.status_code,
            duration_ms=duration_ms,
            response_size_bytes=len(response.body) if hasattr(response, 'body') else 0
        )


class DatabaseTracingMiddleware:
    """
    数据库追踪中间件
    监控数据库操作性能
    """
    
    def __init__(self):
        self.apm = otel_apm
    
    def trace_query(self, table: str, operation: str, query_func: Callable, *args, **kwargs):
        """
        追踪数据库查询
        """
        start_time = time.time()
        
        try:
            # 执行查询
            result = query_func(*args, **kwargs)
            
            # 计算执行时间
            duration_ms = (time.time() - start_time) * 1000
            
            # 记录指标
            self.apm.record_db_metric(
                table=table,
                operation=operation,
                duration_ms=duration_ms,
                rows=getattr(result, 'rowcount', 0) if hasattr(result, 'rowcount') else 0
            )
            
            # 记录到传统APM
            apm_collector.record_database_performance(
                query_type=operation.upper(),
                table_name=table,
                duration_ms=duration_ms,
                rows_affected=getattr(result, 'rowcount', 0) if hasattr(result, 'rowcount') else 0,
                success=True
            )
            
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            # 记录错误指标
            apm_collector.record_database_performance(
                query_type=operation.upper(),
                table_name=table,
                duration_ms=duration_ms,
                success=False
            )
            
            logger.error(
                f"Database query failed: {operation} on {table}",
                extra={
                    "table": table,
                    "operation": operation,
                    "duration_ms": duration_ms,
                    "error": str(e)
                },
                exc_info=True
            )
            
            raise


class ExternalServiceTracingMiddleware:
    """
    外部服务调用追踪中间件
    监控第三方API调用性能
    """
    
    def __init__(self):
        self.apm = otel_apm
    
    def trace_api_call(self, service_name: str, endpoint: str, method: str, api_func: Callable, *args, **kwargs):
        """
        追踪外部API调用
        """
        start_time = time.time()
        
        try:
            # 执行API调用
            response = api_func(*args, **kwargs)
            
            # 计算响应时间
            duration_ms = (time.time() - start_time) * 1000
            
            # 获取状态码
            status_code = getattr(response, 'status_code', 200)
            
            # 获取响应大小
            response_size = 0
            if hasattr(response, 'content'):
                response_size = len(response.content)
            elif hasattr(response, 'text'):
                response_size = len(response.text.encode())
            
            # 记录指标
            self.apm.record_external_api_metric(
                service=service_name,
                endpoint=endpoint,
                status_code=status_code,
                duration_ms=duration_ms
            )
            
            # 记录到传统APM
            apm_collector.record_external_api_call(
                service_name=service_name,
                endpoint=endpoint,
                method=method,
                status_code=status_code,
                duration_ms=duration_ms,
                response_size_bytes=response_size
            )
            
            return response
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            # 记录错误指标
            apm_collector.record_external_api_call(
                service_name=service_name,
                endpoint=endpoint,
                method=method,
                status_code=500,
                duration_ms=duration_ms
            )
            
            logger.error(
                f"External API call failed: {service_name} {method} {endpoint}",
                extra={
                    "service_name": service_name,
                    "endpoint": endpoint,
                    "method": method,
                    "duration_ms": duration_ms,
                    "error": str(e)
                },
                exc_info=True
            )
            
            raise


# 全局实例
db_tracer = DatabaseTracingMiddleware()
external_service_tracer = ExternalServiceTracingMiddleware()


def trace_database_operation(table: str, operation: str):
    """
    数据库操作追踪装饰器
    """
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            return db_tracer.trace_query(table, operation, func, *args, **kwargs)
        return wrapper
    return decorator


def trace_external_api_call(service_name: str, endpoint: str, method: str = "GET"):
    """
    外部API调用追踪装饰器
    """
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            return external_service_tracer.trace_api_call(service_name, endpoint, method, func, *args, **kwargs)
        return wrapper
    return decorator
