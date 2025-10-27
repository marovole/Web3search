"""
数据库中间件
用于查询性能监控、慢查询日志等
"""
import time
import logging
from typing import Any
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.pool import Pool

from app.core.config import settings

logger = logging.getLogger(__name__)

# 慢查询阈值（秒）
SLOW_QUERY_THRESHOLD = 0.5  # 500ms


def setup_query_monitoring(engine: Engine) -> None:
    """
    设置查询性能监控

    监听SQL执行事件，记录慢查询
    """

    @event.listens_for(engine.sync_engine, "before_cursor_execute")
    def receive_before_cursor_execute(
        conn, cursor, statement, parameters, context, executemany
    ):
        """查询执行前的钩子"""
        conn.info.setdefault("query_start_time", []).append(time.time())

    @event.listens_for(engine.sync_engine, "after_cursor_execute")
    def receive_after_cursor_execute(
        conn, cursor, statement, parameters, context, executemany
    ):
        """查询执行后的钩子"""
        total_time = time.time() - conn.info["query_start_time"].pop()

        # 记录慢查询
        if total_time > SLOW_QUERY_THRESHOLD:
            logger.warning(
                f"Slow query detected ({total_time:.3f}s): {statement[:200]}...",
                extra={
                    "query_time": total_time,
                    "query": statement[:500],
                    "parameters": str(parameters)[:200] if parameters else None,
                    "slow_query": True,
                }
            )

        # 记录所有查询（仅在DEBUG模式）
        if settings.DEBUG:
            logger.debug(
                f"Query executed in {total_time:.3f}s",
                extra={
                    "query_time": total_time,
                    "query": statement[:200],
                }
            )


def setup_pool_monitoring(engine: Engine) -> None:
    """
    设置连接池监控

    监听连接池事件，追踪连接使用情况
    """

    @event.listens_for(Pool, "connect")
    def receive_connect(dbapi_conn, connection_record):
        """新连接创建时的钩子"""
        logger.info("Database connection created", extra={"event": "pool_connect"})

    @event.listens_for(Pool, "checkout")
    def receive_checkout(dbapi_conn, connection_record, connection_proxy):
        """从连接池获取连接时的钩子"""
        if settings.DEBUG:
            logger.debug("Connection checked out from pool", extra={"event": "pool_checkout"})

    @event.listens_for(Pool, "checkin")
    def receive_checkin(dbapi_conn, connection_record):
        """连接归还到连接池时的钩子"""
        if settings.DEBUG:
            logger.debug("Connection checked in to pool", extra={"event": "pool_checkin"})

    @event.listens_for(Pool, "reset")
    def receive_reset(dbapi_conn, connection_record):
        """连接重置时的钩子"""
        logger.debug("Connection reset", extra={"event": "pool_reset"})

    @event.listens_for(Pool, "invalidate")
    def receive_invalidate(dbapi_conn, connection_record, exception):
        """连接失效时的钩子"""
        logger.warning(
            f"Connection invalidated: {exception}",
            extra={
                "event": "pool_invalidate",
                "error": str(exception),
            }
        )


class QueryPerformanceCollector:
    """
    查询性能数据收集器

    收集查询统计信息用于分析
    """

    def __init__(self):
        self.query_stats = []
        self.slow_query_count = 0
        self.total_query_count = 0
        self.total_query_time = 0.0

    def record_query(self, query: str, duration: float, is_slow: bool = False):
        """记录查询执行信息"""
        self.total_query_count += 1
        self.total_query_time += duration

        if is_slow:
            self.slow_query_count += 1
            self.query_stats.append({
                "query": query[:200],
                "duration": duration,
                "timestamp": time.time(),
            })

            # 保留最近100条慢查询
            if len(self.query_stats) > 100:
                self.query_stats.pop(0)

    def get_stats(self) -> dict:
        """获取查询统计信息"""
        avg_query_time = (
            self.total_query_time / self.total_query_count
            if self.total_query_count > 0
            else 0
        )

        return {
            "total_queries": self.total_query_count,
            "slow_queries": self.slow_query_count,
            "slow_query_rate": (
                self.slow_query_count / self.total_query_count
                if self.total_query_count > 0
                else 0
            ),
            "avg_query_time": round(avg_query_time, 4),
            "total_query_time": round(self.total_query_time, 2),
            "recent_slow_queries": self.query_stats[-10:],  # 最近10条慢查询
        }

    def reset_stats(self):
        """重置统计信息"""
        self.query_stats = []
        self.slow_query_count = 0
        self.total_query_count = 0
        self.total_query_time = 0.0


# 全局性能收集器实例
performance_collector = QueryPerformanceCollector()
