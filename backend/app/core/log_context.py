"""
日志上下文管理器

使用contextvars实现上下文信息在异步调用链中的传播
"""
from contextvars import ContextVar
from typing import Any, Dict, Optional
from contextlib import contextmanager

import structlog


# 定义context变量
_request_id: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
_user_id: ContextVar[Optional[int]] = ContextVar("user_id", default=None)
_symbol: ContextVar[Optional[str]] = ContextVar("symbol", default=None)
_conversation_id: ContextVar[Optional[str]] = ContextVar("conversation_id", default=None)
_custom_context: ContextVar[Dict[str, Any]] = ContextVar("custom_context", default={})


class LogContext:
    """
    日志上下文管理器

    提供便捷的API来设置和获取日志上下文信息
    """

    @staticmethod
    def set_request_id(request_id: str) -> None:
        """设置request_id"""
        _request_id.set(request_id)

    @staticmethod
    def get_request_id() -> Optional[str]:
        """获取request_id"""
        return _request_id.get()

    @staticmethod
    def set_user_id(user_id: int) -> None:
        """设置user_id"""
        _user_id.set(user_id)

    @staticmethod
    def get_user_id() -> Optional[int]:
        """获取user_id"""
        return _user_id.get()

    @staticmethod
    def set_symbol(symbol: str) -> None:
        """设置加密货币符号"""
        _symbol.set(symbol)

    @staticmethod
    def get_symbol() -> Optional[str]:
        """获取加密货币符号"""
        return _symbol.get()

    @staticmethod
    def set_conversation_id(conversation_id: str) -> None:
        """设置conversation_id"""
        _conversation_id.set(conversation_id)

    @staticmethod
    def get_conversation_id() -> Optional[str]:
        """获取conversation_id"""
        return _conversation_id.get()

    @staticmethod
    def set_custom(key: str, value: Any) -> None:
        """设置自定义上下文信息"""
        context = _custom_context.get().copy()
        context[key] = value
        _custom_context.set(context)

    @staticmethod
    def get_custom(key: str) -> Optional[Any]:
        """获取自定义上下文信息"""
        return _custom_context.get().get(key)

    @staticmethod
    def get_all() -> Dict[str, Any]:
        """
        获取所有上下文信息

        Returns:
            包含所有上下文信息的字典
        """
        context = {}

        request_id = _request_id.get()
        if request_id:
            context["request_id"] = request_id

        user_id = _user_id.get()
        if user_id:
            context["user_id"] = user_id

        symbol = _symbol.get()
        if symbol:
            context["symbol"] = symbol

        conversation_id = _conversation_id.get()
        if conversation_id:
            context["conversation_id"] = conversation_id

        # 添加自定义上下文
        custom = _custom_context.get()
        if custom:
            context.update(custom)

        return context

    @staticmethod
    def clear() -> None:
        """清除所有上下文信息"""
        _request_id.set(None)
        _user_id.set(None)
        _symbol.set(None)
        _conversation_id.set(None)
        _custom_context.set({})

    @staticmethod
    def bind_to_logger(logger: structlog.BoundLogger) -> structlog.BoundLogger:
        """
        将上下文信息绑定到logger

        Args:
            logger: structlog logger实例

        Returns:
            绑定了上下文信息的logger

        Example:
            >>> logger = get_logger(__name__)
            >>> logger = LogContext.bind_to_logger(logger)
            >>> logger.info("processing")  # 自动包含request_id等上下文
        """
        context = LogContext.get_all()
        return logger.bind(**context)


@contextmanager
def log_context(**kwargs):
    """
    日志上下文管理器（context manager）

    Args:
        **kwargs: 要设置的上下文信息
                 支持: request_id, user_id, symbol, conversation_id
                 以及任意自定义键值对

    Example:
        >>> with log_context(request_id="abc-123", user_id=456):
        >>>     logger.info("processing")  # 自动包含request_id和user_id
        >>>
        >>> with log_context(symbol="BTC", analysis_type="technical"):
        >>>     logger.info("analyzing")  # 自动包含symbol和analysis_type
    """
    # 保存旧值
    old_values = {}

    try:
        # 设置新值
        for key, value in kwargs.items():
            if key == "request_id":
                old_values[key] = _request_id.get()
                _request_id.set(value)
            elif key == "user_id":
                old_values[key] = _user_id.get()
                _user_id.set(value)
            elif key == "symbol":
                old_values[key] = _symbol.get()
                _symbol.set(value)
            elif key == "conversation_id":
                old_values[key] = _conversation_id.get()
                _conversation_id.set(value)
            else:
                # 自定义字段
                old_custom = _custom_context.get().copy()
                old_values[f"custom_{key}"] = old_custom.get(key)
                LogContext.set_custom(key, value)

        yield

    finally:
        # 恢复旧值
        for key, value in old_values.items():
            if key == "request_id":
                _request_id.set(value)
            elif key == "user_id":
                _user_id.set(value)
            elif key == "symbol":
                _symbol.set(value)
            elif key == "conversation_id":
                _conversation_id.set(value)
            elif key.startswith("custom_"):
                original_key = key[7:]  # 去掉"custom_"前缀
                if value is None:
                    # 删除自定义字段
                    context = _custom_context.get().copy()
                    context.pop(original_key, None)
                    _custom_context.set(context)
                else:
                    LogContext.set_custom(original_key, value)


class ContextProcessor:
    """
    structlog processor: 自动注入上下文信息到日志

    使用方法：添加到structlog processors列表中
    """

    def __call__(self, logger: Any, name: str, event_dict: Dict) -> Dict:
        """
        将上下文信息注入到event_dict

        Args:
            logger: logger实例
            name: method名称
            event_dict: 事件字典

        Returns:
            注入了上下文信息的事件字典
        """
        context = LogContext.get_all()
        event_dict.update(context)
        return event_dict


# 便捷函数
def get_logger_with_context(name: str) -> structlog.BoundLogger:
    """
    获取带上下文的logger

    Args:
        name: logger名称

    Returns:
        自动包含上下文信息的logger

    Example:
        >>> logger = get_logger_with_context(__name__)
        >>> logger.info("processing")  # 自动包含request_id等上下文
    """
    from app.core.structlog_config import get_logger

    logger = get_logger(name)
    return LogContext.bind_to_logger(logger)
