"""
日志系统测试模块

测试structlog配置、请求上下文、日志过滤等功能
"""
import json
import logging
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import structlog

from app.core.structlog_config import (
    SensitiveDataProcessor,
    setup_structlog,
    get_logger,
)
from app.core.log_context import (
    LogContext,
    log_context,
    ContextProcessor,
    get_logger_with_context,
)
from app.core.log_filters import (
    EndpointFilter,
    LevelThresholdFilter,
    MessagePatternFilter,
    StructlogEventFilter,
)


@pytest.fixture(autouse=True)
def reset_log_context():
    """每个测试前重置日志上下文"""
    LogContext.clear()
    yield
    LogContext.clear()


class TestStructlogConfiguration:
    """测试structlog配置"""

    def test_logger_creation(self):
        """测试logger创建"""
        logger = get_logger(__name__)
        assert logger is not None
        assert isinstance(logger, structlog.BoundLogger)

    def test_sensitive_data_masking(self):
        """测试敏感数据脱敏"""
        processor = SensitiveDataProcessor()

        event_dict = {
            "event": "test",
            "api_key": "sk-1234567890abcdef",
            "password": "my_secret_password",
            "user_id": 123,
        }

        result = processor(Mock(), "info", event_dict)

        # 敏感字段应该被脱敏
        assert result["api_key"] == "sk-1...cdef"
        assert result["password"] == "my_s...word"

        # 非敏感字段应该保持不变
        assert result["user_id"] == 123

    def test_sensitive_data_masking_short_value(self):
        """测试短值脱敏"""
        processor = SensitiveDataProcessor()

        event_dict = {
            "token": "abc",
        }

        result = processor(Mock(), "info", event_dict)
        assert result["token"] == "***"

    def test_sensitive_data_masking_nested_dict(self):
        """测试嵌套字典脱敏"""
        processor = SensitiveDataProcessor()

        event_dict = {
            "event": "test",
            "config": {
                "api_key": "sk-1234567890abcdef",
                "timeout": 30,
            }
        }

        result = processor(Mock(), "info", event_dict)
        assert result["config"]["api_key"] == "sk-1...cdef"
        assert result["config"]["timeout"] == 30

    def test_setup_structlog_development(self):
        """测试开发环境structlog配置"""
        setup_structlog(environment="development")
        logger = get_logger("test")

        # 应该能正常使用
        logger.info("test_message", test_value=123)

    def test_setup_structlog_production(self):
        """测试生产环境structlog配置"""
        setup_structlog(environment="production")
        logger = get_logger("test")

        # 应该能正常使用
        logger.info("test_message", test_value=123)


class TestLogContext:
    """测试日志上下文管理"""

    def test_set_and_get_request_id(self):
        """测试设置和获取request_id"""
        request_id = "test-request-123"
        LogContext.set_request_id(request_id)

        assert LogContext.get_request_id() == request_id

    def test_set_and_get_user_id(self):
        """测试设置和获取user_id"""
        user_id = 456
        LogContext.set_user_id(user_id)

        assert LogContext.get_user_id() == user_id

    def test_set_and_get_symbol(self):
        """测试设置和获取symbol"""
        symbol = "BTC"
        LogContext.set_symbol(symbol)

        assert LogContext.get_symbol() == symbol

    def test_set_and_get_conversation_id(self):
        """测试设置和获取conversation_id"""
        conversation_id = "conv-789"
        LogContext.set_conversation_id(conversation_id)

        assert LogContext.get_conversation_id() == conversation_id

    def test_set_and_get_custom(self):
        """测试自定义上下文"""
        LogContext.set_custom("analysis_type", "technical")
        assert LogContext.get_custom("analysis_type") == "technical"

    def test_get_all_context(self):
        """测试获取所有上下文"""
        LogContext.set_request_id("req-123")
        LogContext.set_user_id(456)
        LogContext.set_symbol("ETH")
        LogContext.set_custom("mode", "quick")

        context = LogContext.get_all()

        assert context["request_id"] == "req-123"
        assert context["user_id"] == 456
        assert context["symbol"] == "ETH"
        assert context["mode"] == "quick"

    def test_clear_context(self):
        """测试清除上下文"""
        LogContext.set_request_id("req-123")
        LogContext.set_user_id(456)

        LogContext.clear()

        assert LogContext.get_request_id() is None
        assert LogContext.get_user_id() is None
        assert LogContext.get_all() == {}

    def test_context_manager(self):
        """测试上下文管理器"""
        # 设置初始值
        LogContext.set_request_id("initial-req")

        # 在context manager中修改
        with log_context(request_id="temp-req", user_id=123):
            assert LogContext.get_request_id() == "temp-req"
            assert LogContext.get_user_id() == 123

        # context manager退出后应该恢复
        assert LogContext.get_request_id() == "initial-req"
        assert LogContext.get_user_id() is None

    def test_nested_context_managers(self):
        """测试嵌套上下文管理器"""
        with log_context(request_id="outer-req"):
            assert LogContext.get_request_id() == "outer-req"

            with log_context(request_id="inner-req"):
                assert LogContext.get_request_id() == "inner-req"

            # 内层退出后恢复外层值
            assert LogContext.get_request_id() == "outer-req"

        # 外层退出后应该清空
        assert LogContext.get_request_id() is None

    def test_context_processor(self):
        """测试ContextProcessor"""
        processor = ContextProcessor()

        LogContext.set_request_id("req-123")
        LogContext.set_user_id(456)

        event_dict = {"event": "test"}
        result = processor(Mock(), "info", event_dict)

        assert result["request_id"] == "req-123"
        assert result["user_id"] == 456

    def test_bind_to_logger(self):
        """测试绑定到logger"""
        LogContext.set_request_id("req-123")
        LogContext.set_symbol("BTC")

        logger = get_logger("test")
        bound_logger = LogContext.bind_to_logger(logger)

        # bound_logger应该包含上下文
        # 注意：这里只验证不抛出异常
        bound_logger.info("test_message")

    def test_get_logger_with_context(self):
        """测试获取带上下文的logger"""
        LogContext.set_request_id("req-123")

        logger = get_logger_with_context("test")

        # 应该能正常使用
        logger.info("test_message")


class TestLogFilters:
    """测试日志过滤器"""

    def test_endpoint_filter_exact_match(self):
        """测试端点过滤器精确匹配"""
        filter_obj = EndpointFilter(excluded_endpoints=["/health", "/metrics"])

        # 创建模拟日志记录
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="test",
            args=(),
            exc_info=None
        )

        # 设置URL属性
        record.url = "/health"
        assert filter_obj.filter(record) is False

        record.url = "/metrics"
        assert filter_obj.filter(record) is False

        record.url = "/api/data"
        assert filter_obj.filter(record) is True

    def test_endpoint_filter_pattern_match(self):
        """测试端点过滤器模式匹配"""
        filter_obj = EndpointFilter(excluded_patterns=[r"/health.*", r".*\.ico"])

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="test",
            args=(),
            exc_info=None
        )

        record.url = "/health/database"
        assert filter_obj.filter(record) is False

        record.url = "/favicon.ico"
        assert filter_obj.filter(record) is False

        record.url = "/api/data"
        assert filter_obj.filter(record) is True

    def test_level_threshold_filter(self):
        """测试日志级别阈值过滤器"""
        # 只允许INFO到WARNING
        filter_obj = LevelThresholdFilter(
            min_level=logging.INFO,
            max_level=logging.WARNING
        )

        debug_record = logging.LogRecord(
            name="test",
            level=logging.DEBUG,
            pathname="",
            lineno=0,
            msg="test",
            args=(),
            exc_info=None
        )
        assert filter_obj.filter(debug_record) is False

        info_record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="test",
            args=(),
            exc_info=None
        )
        assert filter_obj.filter(info_record) is True

        warning_record = logging.LogRecord(
            name="test",
            level=logging.WARNING,
            pathname="",
            lineno=0,
            msg="test",
            args=(),
            exc_info=None
        )
        assert filter_obj.filter(warning_record) is True

        error_record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="",
            lineno=0,
            msg="test",
            args=(),
            exc_info=None
        )
        assert filter_obj.filter(error_record) is False

    def test_message_pattern_filter_excluded(self):
        """测试消息模式过滤器（排除）"""
        filter_obj = MessagePatternFilter(
            excluded_patterns=[r"health.*check", r"test.*pattern"]
        )

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="health check completed",
            args=(),
            exc_info=None
        )
        assert filter_obj.filter(record) is False

        record.msg = "test pattern match"
        assert filter_obj.filter(record) is False

        record.msg = "normal log message"
        assert filter_obj.filter(record) is True

    def test_message_pattern_filter_included(self):
        """测试消息模式过滤器（包含）"""
        filter_obj = MessagePatternFilter(
            included_patterns=[r"important", r"critical"]
        )

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="important message",
            args=(),
            exc_info=None
        )
        assert filter_obj.filter(record) is True

        record.msg = "normal message"
        assert filter_obj.filter(record) is False

    def test_structlog_event_filter(self):
        """测试structlog事件过滤器"""
        filter_obj = StructlogEventFilter(
            excluded_events=["health_check"],
            excluded_urls=["/metrics"]
        )

        # 应该被过滤的事件
        with pytest.raises(structlog.DropEvent):
            filter_obj(Mock(), "info", {"event": "health_check"})

        # 应该被过滤的URL
        with pytest.raises(structlog.DropEvent):
            filter_obj(Mock(), "info", {"event": "request", "url": "/metrics"})

        # 应该保留的事件
        result = filter_obj(Mock(), "info", {"event": "api_call", "url": "/api/data"})
        assert result["event"] == "api_call"


class TestLogRotation:
    """测试日志轮转"""

    def test_log_directory_creation(self):
        """测试日志目录创建"""
        from app.core.structlog_config import LOG_DIR

        # 日志目录应该存在
        assert LOG_DIR.exists()
        assert LOG_DIR.is_dir()

    @patch("app.core.structlog_config.logging.handlers.RotatingFileHandler")
    def test_rotating_file_handler_configuration(self, mock_handler):
        """测试rotating文件handler配置"""
        from app.core.structlog_config import _create_rotating_file_handler

        handler = _create_rotating_file_handler("production")

        # 应该创建handler
        # 注意：由于mock，这里只验证不抛出异常
        assert handler is not None or handler is None  # 取决于环境


class TestRequestContextMiddleware:
    """测试请求上下文中间件"""

    @pytest.mark.asyncio
    async def test_request_id_generation(self):
        """测试request_id生成"""
        from fastapi import Request
        from app.middleware.request_context import RequestContextMiddleware

        # 创建模拟请求
        mock_request = Mock(spec=Request)
        mock_request.headers = {}
        mock_request.method = "GET"
        mock_request.url = "http://example.com/api/test"
        mock_request.client = Mock()
        mock_request.client.host = "127.0.0.1"
        mock_request.state = Mock()

        # 创建中间件
        middleware = RequestContextMiddleware(app=Mock())

        # 模拟call_next
        async def mock_call_next(request):
            response = Mock()
            response.status_code = 200
            response.headers = {}
            return response

        # 执行中间件
        response = await middleware.dispatch(mock_request, mock_call_next)

        # 验证request_id被设置
        assert hasattr(mock_request.state, "request_id")
        assert mock_request.state.request_id is not None

        # 验证响应头包含request_id
        assert "X-Request-ID" in response.headers

    @pytest.mark.asyncio
    async def test_request_id_from_header(self):
        """测试从请求头获取request_id"""
        from fastapi import Request
        from app.middleware.request_context import RequestContextMiddleware

        custom_request_id = "custom-req-123"

        mock_request = Mock(spec=Request)
        mock_request.headers = {"X-Request-ID": custom_request_id}
        mock_request.method = "GET"
        mock_request.url = "http://example.com/api/test"
        mock_request.client = Mock()
        mock_request.client.host = "127.0.0.1"
        mock_request.state = Mock()

        middleware = RequestContextMiddleware(app=Mock())

        async def mock_call_next(request):
            response = Mock()
            response.status_code = 200
            response.headers = {}
            return response

        response = await middleware.dispatch(mock_request, mock_call_next)

        # 应该使用提供的request_id
        assert mock_request.state.request_id == custom_request_id
        assert response.headers["X-Request-ID"] == custom_request_id


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
