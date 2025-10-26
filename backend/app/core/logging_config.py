"""
日志配置
统一的日志记录和格式化
"""
import logging
import sys
from typing import Optional
from pathlib import Path

from app.core.config import settings


# ================================
# 日志格式化器
# ================================


class ColoredFormatter(logging.Formatter):
    """
    彩色日志格式化器（仅在终端使用）
    """

    # 颜色代码
    COLORS = {
        "DEBUG": "\033[36m",  # 青色
        "INFO": "\033[32m",  # 绿色
        "WARNING": "\033[33m",  # 黄色
        "ERROR": "\033[31m",  # 红色
        "CRITICAL": "\033[35m",  # 紫色
        "RESET": "\033[0m",  # 重置
    }

    def format(self, record):
        # 添加颜色
        if record.levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
            )

        return super().format(record)


# ================================
# 日志配置
# ================================


def setup_logging(
    level: Optional[str] = None,
    log_file: Optional[str] = None,
    colored: bool = True,
) -> logging.Logger:
    """
    配置日志系统

    Args:
        level: 日志级别（DEBUG/INFO/WARNING/ERROR/CRITICAL）
        log_file: 日志文件路径
        colored: 是否使用彩色输出

    Returns:
        logging.Logger: 根日志记录器
    """
    # 确定日志级别
    if level is None:
        level = "DEBUG" if settings.DEBUG else "INFO"

    log_level = getattr(logging, level.upper(), logging.INFO)

    # 获取根日志记录器
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # 清除现有处理器
    logger.handlers.clear()

    # ================================
    # 控制台处理器
    # ================================
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    # 选择格式化器
    if colored and sys.stdout.isatty():
        # 终端环境：使用彩色格式
        console_formatter = ColoredFormatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    else:
        # 非终端环境：使用普通格式
        console_formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # ================================
    # 文件处理器（可选）
    # ================================
    if log_file:
        # 创建日志目录
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # 文件处理器
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(log_level)

        # 文件格式化器（不使用颜色）
        file_formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    # ================================
    # 第三方库日志级别配置
    # ================================
    # 降低httpx日志级别（避免过多HTTP请求日志）
    logging.getLogger("httpx").setLevel(logging.WARNING)

    # 降低uvicorn访问日志级别
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    # 降低sqlalchemy日志级别（避免过多SQL日志）
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    # 降低celery日志级别
    logging.getLogger("celery").setLevel(logging.INFO)

    logger.info(f"✅ Logging configured: level={level}, file={log_file}")
    return logger


# ================================
# 性能日志记录器
# ================================


class PerformanceLogger:
    """
    性能日志记录器
    用于记录API响应时间、数据库查询时间等
    """

    def __init__(self):
        self.logger = logging.getLogger("performance")

    def log_api_request(
        self,
        method: str,
        path: str,
        duration: float,
        status_code: int,
        client_ip: str = None,
    ):
        """
        记录API请求性能

        Args:
            method: HTTP方法
            path: 请求路径
            duration: 响应时间（秒）
            status_code: HTTP状态码
            client_ip: 客户端IP
        """
        extra = {
            "method": method,
            "path": path,
            "duration_ms": round(duration * 1000, 2),
            "status_code": status_code,
            "client_ip": client_ip,
        }

        # 根据响应时间和状态码选择日志级别
        if status_code >= 500:
            self.logger.error(
                f"{method} {path} - {status_code} - {duration*1000:.2f}ms",
                extra=extra,
            )
        elif status_code >= 400:
            self.logger.warning(
                f"{method} {path} - {status_code} - {duration*1000:.2f}ms",
                extra=extra,
            )
        elif duration > 5.0:
            # 响应时间超过5秒，记录警告
            self.logger.warning(
                f"{method} {path} - {status_code} - {duration*1000:.2f}ms (SLOW)",
                extra=extra,
            )
        else:
            self.logger.info(
                f"{method} {path} - {status_code} - {duration*1000:.2f}ms",
                extra=extra,
            )

    def log_db_query(self, query: str, duration: float):
        """
        记录数据库查询性能

        Args:
            query: SQL查询
            duration: 查询时间（秒）
        """
        extra = {
            "query": query[:100],  # 截断长查询
            "duration_ms": round(duration * 1000, 2),
        }

        if duration > 1.0:
            # 慢查询（超过1秒）
            self.logger.warning(
                f"Slow DB query: {duration*1000:.2f}ms - {query[:100]}",
                extra=extra,
            )
        else:
            self.logger.debug(
                f"DB query: {duration*1000:.2f}ms - {query[:100]}",
                extra=extra,
            )

    def log_llm_call(self, model: str, prompt_length: int, duration: float, success: bool = True):
        """
        记录LLM调用性能

        Args:
            model: 模型名称
            prompt_length: Prompt长度
            duration: 调用时间（秒）
            success: 是否成功
        """
        extra = {
            "model": model,
            "prompt_length": prompt_length,
            "duration_ms": round(duration * 1000, 2),
            "success": success,
        }

        if not success:
            self.logger.error(
                f"LLM call failed: {model} - {duration*1000:.2f}ms",
                extra=extra,
            )
        elif duration > 30.0:
            # 调用时间超过30秒
            self.logger.warning(
                f"Slow LLM call: {model} - {duration*1000:.2f}ms (SLOW)",
                extra=extra,
            )
        else:
            self.logger.info(
                f"LLM call: {model} - {duration*1000:.2f}ms",
                extra=extra,
            )


# ================================
# 全局实例
# ================================

# 初始化日志系统
setup_logging()

# 性能日志记录器
perf_logger = PerformanceLogger()
