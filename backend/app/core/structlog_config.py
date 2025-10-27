"""
结构化日志配置模块

使用structlog实现JSON格式的结构化日志，支持：
- 开发环境：彩色控制台输出
- 生产环境：JSON格式输出
- 请求追踪：request_id自动注入
- 上下文信息：user_id、symbol、conversation_id等
- 敏感信息脱敏
"""
import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import structlog
from pythonjsonlogger import jsonlogger

from app.core.config import settings


# 日志目录配置
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)


class SensitiveDataProcessor:
    """敏感数据脱敏处理器"""

    SENSITIVE_KEYS = {
        "password", "token", "secret", "api_key", "apikey",
        "authorization", "auth", "key", "dsn", "DATABASE_URL"
    }

    def __call__(self, logger: Any, name: str, event_dict: Dict) -> Dict:
        """
        脱敏处理日志中的敏感信息

        Args:
            logger: logger实例
            name: method名称
            event_dict: 事件字典

        Returns:
            处理后的事件字典
        """
        # 遍历所有键值对，检查敏感信息
        for key, value in list(event_dict.items()):
            if self._is_sensitive_key(key):
                event_dict[key] = self._mask_value(value)
            elif isinstance(value, dict):
                event_dict[key] = self._mask_dict(value)

        return event_dict

    def _is_sensitive_key(self, key: str) -> bool:
        """检查键是否为敏感信息"""
        key_lower = key.lower()
        return any(sensitive in key_lower for sensitive in self.SENSITIVE_KEYS)

    def _mask_value(self, value: Any) -> str:
        """脱敏处理值"""
        if not value or not isinstance(value, str):
            return "***"
        if len(value) <= 8:
            return "***"
        return f"{value[:4]}...{value[-4:]}"

    def _mask_dict(self, data: Dict) -> Dict:
        """递归脱敏字典"""
        result = {}
        for key, value in data.items():
            if self._is_sensitive_key(key):
                result[key] = self._mask_value(value)
            elif isinstance(value, dict):
                result[key] = self._mask_dict(value)
            else:
                result[key] = value
        return result


def add_logger_name(logger: Any, name: str, event_dict: Dict) -> Dict:
    """
    添加logger名称到事件字典

    Args:
        logger: logger实例
        name: method名称
        event_dict: 事件字典

    Returns:
        添加了logger_name的事件字典
    """
    event_dict["logger_name"] = logger.name
    return event_dict


def add_log_level(logger: Any, name: str, event_dict: Dict) -> Dict:
    """
    添加日志级别到事件字典

    Args:
        logger: logger实例
        name: method名称
        event_dict: 事件字典

    Returns:
        添加了log_level的事件字典
    """
    event_dict["log_level"] = name
    return event_dict


def setup_structlog(environment: Optional[str] = None) -> None:
    """
    配置structlog结构化日志

    Args:
        environment: 运行环境（development/staging/production）
                    如果为None，从settings获取
    """
    if environment is None:
        environment = settings.ENVIRONMENT

    # 配置标准库logging
    _configure_stdlib_logging(environment)

    # 根据环境选择processors
    processors = _get_processors(environment)

    # 配置structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(settings.LOG_LEVEL)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def _configure_stdlib_logging(environment: str) -> None:
    """
    配置标准库logging

    Args:
        environment: 运行环境
    """
    # 创建root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.getLevelName(settings.LOG_LEVEL))

    # 清除现有handlers
    root_logger.handlers.clear()

    # 控制台handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.getLevelName(settings.LOG_LEVEL))

    if environment in ["production", "prod"]:
        # 生产环境：JSON格式
        formatter = jsonlogger.JsonFormatter(
            fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    else:
        # 开发环境：可读格式
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 文件handler（带rotation）
    file_handler = _create_rotating_file_handler(environment)
    if file_handler:
        root_logger.addHandler(file_handler)


def _create_rotating_file_handler(environment: str) -> Optional[logging.Handler]:
    """
    创建rotating文件handler

    Args:
        environment: 运行环境

    Returns:
        配置好的handler或None
    """
    try:
        log_file = LOG_DIR / f"web3search_{environment}.log"

        # RotatingFileHandler: 按大小轮转（100MB）
        handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=100 * 1024 * 1024,  # 100MB
            backupCount=10,  # 保留10个备份
            encoding="utf-8"
        )

        handler.setLevel(logging.getLevelName(settings.LOG_LEVEL))

        # 文件始终使用JSON格式
        formatter = jsonlogger.JsonFormatter(
            fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)

        return handler

    except Exception as e:
        logging.error(f"Failed to create rotating file handler: {e}")
        return None


def _get_processors(environment: str) -> list:
    """
    根据环境获取structlog processors

    Args:
        environment: 运行环境

    Returns:
        processor列表
    """
    # 通用processors
    common_processors = [
        # 添加log level
        add_log_level,
        # 添加logger name
        add_logger_name,
        # 添加时间戳
        structlog.processors.TimeStamper(fmt="iso"),
        # 添加调用信息（文件名、行号、函数名）
        structlog.processors.CallsiteParameterAdder(
            parameters=[
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.LINENO,
                structlog.processors.CallsiteParameter.FUNC_NAME,
            ]
        ),
        # 堆栈信息（仅错误级别）
        structlog.processors.StackInfoRenderer(),
        # 格式化异常
        structlog.processors.format_exc_info,
        # 脱敏处理
        SensitiveDataProcessor(),
    ]

    if environment in ["development", "dev"]:
        # 开发环境：彩色控制台输出
        processors = common_processors + [
            # 彩色输出
            structlog.dev.ConsoleRenderer(
                colors=True,
                exception_formatter=structlog.dev.plain_traceback,
            )
        ]
    else:
        # 生产/预发布环境：JSON格式
        processors = common_processors + [
            # JSON渲染器
            structlog.processors.JSONRenderer()
        ]

    return processors


def get_logger(name: str) -> structlog.BoundLogger:
    """
    获取structlog logger实例

    Args:
        name: logger名称（通常是模块名 __name__）

    Returns:
        配置好的logger实例

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("user_login", user_id=123, ip="1.2.3.4")
        >>> logger.error("api_error", error="connection timeout", retry_count=3)
    """
    return structlog.get_logger(name)


# 初始化structlog（导入时自动执行）
setup_structlog()


# 导出常用logger
logger = get_logger(__name__)
