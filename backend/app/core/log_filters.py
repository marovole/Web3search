"""
日志过滤器

提供各种日志过滤功能，用于减少日志噪音
"""
import logging
import re
from typing import Any, Dict, List, Optional, Set


class EndpointFilter(logging.Filter):
    """
    端点过滤器

    过滤掉指定端点的日志（例如健康检查）
    """

    def __init__(
        self,
        excluded_endpoints: Optional[List[str]] = None,
        excluded_patterns: Optional[List[str]] = None
    ):
        """
        初始化端点过滤器

        Args:
            excluded_endpoints: 要排除的端点列表（精确匹配）
            excluded_patterns: 要排除的端点模式列表（正则表达式）
        """
        super().__init__()
        self.excluded_endpoints: Set[str] = set(excluded_endpoints or [])
        self.excluded_patterns: List[re.Pattern] = [
            re.compile(pattern) for pattern in (excluded_patterns or [])
        ]

    def filter(self, record: logging.LogRecord) -> bool:
        """
        过滤日志记录

        Args:
            record: 日志记录

        Returns:
            True表示保留，False表示过滤掉
        """
        # 获取URL（如果存在）
        url = getattr(record, "url", None)
        if not url:
            return True

        # 转换为字符串
        url_str = str(url)

        # 精确匹配检查
        for endpoint in self.excluded_endpoints:
            if endpoint in url_str:
                return False

        # 模式匹配检查
        for pattern in self.excluded_patterns:
            if pattern.search(url_str):
                return False

        return True


class LevelThresholdFilter(logging.Filter):
    """
    日志级别阈值过滤器

    只允许特定级别范围内的日志通过
    """

    def __init__(self, min_level: int = logging.DEBUG, max_level: int = logging.CRITICAL):
        """
        初始化级别过滤器

        Args:
            min_level: 最小日志级别
            max_level: 最大日志级别
        """
        super().__init__()
        self.min_level = min_level
        self.max_level = max_level

    def filter(self, record: logging.LogRecord) -> bool:
        """
        过滤日志记录

        Args:
            record: 日志记录

        Returns:
            True表示保留，False表示过滤掉
        """
        return self.min_level <= record.levelno <= self.max_level


class MessagePatternFilter(logging.Filter):
    """
    消息模式过滤器

    根据消息内容过滤日志
    """

    def __init__(
        self,
        excluded_patterns: Optional[List[str]] = None,
        included_patterns: Optional[List[str]] = None
    ):
        """
        初始化消息模式过滤器

        Args:
            excluded_patterns: 要排除的消息模式（正则表达式）
            included_patterns: 要包含的消息模式（正则表达式）
                             如果指定，只有匹配的消息才会保留
        """
        super().__init__()
        self.excluded_patterns: List[re.Pattern] = [
            re.compile(pattern) for pattern in (excluded_patterns or [])
        ]
        self.included_patterns: Optional[List[re.Pattern]] = None
        if included_patterns:
            self.included_patterns = [
                re.compile(pattern) for pattern in included_patterns
            ]

    def filter(self, record: logging.LogRecord) -> bool:
        """
        过滤日志记录

        Args:
            record: 日志记录

        Returns:
            True表示保留，False表示过滤掉
        """
        message = record.getMessage()

        # 检查包含模式（如果指定）
        if self.included_patterns:
            if not any(pattern.search(message) for pattern in self.included_patterns):
                return False

        # 检查排除模式
        if any(pattern.search(message) for pattern in self.excluded_patterns):
            return False

        return True


class StructlogEventFilter:
    """
    structlog事件过滤器

    用作structlog processor，根据事件内容过滤日志
    """

    def __init__(
        self,
        excluded_events: Optional[List[str]] = None,
        excluded_urls: Optional[List[str]] = None
    ):
        """
        初始化事件过滤器

        Args:
            excluded_events: 要排除的事件名称列表
            excluded_urls: 要排除的URL列表
        """
        self.excluded_events: Set[str] = set(excluded_events or [])
        self.excluded_urls: Set[str] = set(excluded_urls or [])

    def __call__(self, logger: Any, name: str, event_dict: Dict) -> Dict:
        """
        过滤事件

        Args:
            logger: logger实例
            name: method名称
            event_dict: 事件字典

        Returns:
            处理后的事件字典

        Raises:
            structlog.DropEvent: 如果事件应该被过滤掉
        """
        import structlog

        # 检查事件名称
        event = event_dict.get("event")
        if event in self.excluded_events:
            raise structlog.DropEvent

        # 检查URL
        url = event_dict.get("url")
        if url:
            url_str = str(url)
            for excluded in self.excluded_urls:
                if excluded in url_str:
                    raise structlog.DropEvent

        return event_dict


# 预定义的常用过滤器配置
DEFAULT_HEALTH_CHECK_FILTER = EndpointFilter(
    excluded_endpoints=[
        "/health",
        "/health/",
        "/healthz",
        "/healthz/",
        "/health/database",
        "/health/database/",
        "/metrics",
        "/metrics/",
    ],
    excluded_patterns=[
        r"/health.*",
        r"/metrics.*",
        r".*favicon\.ico",
    ]
)


DEFAULT_STRUCTLOG_EVENT_FILTER = StructlogEventFilter(
    excluded_events=[
        "health_check",
        "metrics_request",
    ],
    excluded_urls=[
        "/health",
        "/healthz",
        "/metrics",
        "/favicon.ico",
    ]
)


def setup_log_filters(
    logger: logging.Logger,
    exclude_health_checks: bool = True,
    min_level: Optional[int] = None,
    max_level: Optional[int] = None,
    excluded_patterns: Optional[List[str]] = None,
) -> None:
    """
    为logger配置过滤器

    Args:
        logger: 要配置的logger
        exclude_health_checks: 是否排除健康检查日志
        min_level: 最小日志级别
        max_level: 最大日志级别
        excluded_patterns: 要排除的消息模式
    """
    # 健康检查过滤器
    if exclude_health_checks:
        logger.addFilter(DEFAULT_HEALTH_CHECK_FILTER)

    # 级别过滤器
    if min_level is not None or max_level is not None:
        min_lvl = min_level or logging.DEBUG
        max_lvl = max_level or logging.CRITICAL
        logger.addFilter(LevelThresholdFilter(min_lvl, max_lvl))

    # 消息模式过滤器
    if excluded_patterns:
        logger.addFilter(MessagePatternFilter(excluded_patterns=excluded_patterns))


def get_structlog_event_filter(
    exclude_health_checks: bool = True,
    custom_excluded_events: Optional[List[str]] = None,
    custom_excluded_urls: Optional[List[str]] = None,
) -> StructlogEventFilter:
    """
    获取structlog事件过滤器

    Args:
        exclude_health_checks: 是否使用默认健康检查过滤
        custom_excluded_events: 自定义要排除的事件
        custom_excluded_urls: 自定义要排除的URL

    Returns:
        配置好的事件过滤器
    """
    if exclude_health_checks:
        return DEFAULT_STRUCTLOG_EVENT_FILTER

    return StructlogEventFilter(
        excluded_events=custom_excluded_events,
        excluded_urls=custom_excluded_urls
    )
