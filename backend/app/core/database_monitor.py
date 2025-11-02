"""
数据库性能监控系统
监控数据库连接、查询性能、锁等待、慢查询等
"""
import asyncio
import time
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import asyncpg
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_async_session
from app.core.redis_client import get_redis_client
from app.core.structured_logging import get_logger
from app.core.alerting_system import alert_manager, AlertSeverity

logger = get_logger("database_monitor")


class MetricType(Enum):
    """指标类型"""
    CONNECTION = "connection"
    QUERY = "query"
    LOCK = "lock"
    PERFORMANCE = "performance"
    REPLICATION = "replication"


class QueryStatus(Enum):
    """查询状态"""
    ACTIVE = "active"
    IDLE = "idle"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class DatabaseMetric:
    """数据库指标"""
    timestamp: datetime
    metric_type: MetricType
    metric_name: str
    value: float
    unit: str
    threshold_warning: float = 0.0
    threshold_critical: float = 0.0
    status: str = "normal"
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        
        # 根据阈值设置状态
        if self.threshold_critical > 0 and self.value >= self.threshold_critical:
            self.status = "critical"
        elif self.threshold_warning > 0 and self.value >= self.threshold_warning:
            self.status = "warning"
        else:
            self.status = "normal"


@dataclass
class SlowQuery:
    """慢查询记录"""
    timestamp: datetime
    query: str
    duration_ms: float
    database: str
    user: str
    application_name: str
    state: str
    wait_event: Optional[str] = None
    query_hash: Optional[str] = None


@dataclass
class ConnectionInfo:
    """连接信息"""
    timestamp: datetime
    total_connections: int
    active_connections: int
    idle_connections: int
    waiting_connections: int
    max_connections: int
    connection_usage_percent: float


class DatabaseMonitor:
    """
    数据库监控器
    负责监控数据库性能和查询统计
    """
    
    def __init__(self):
        self.redis_client = None
        self.running = False
        self.collection_interval = 30  # 30秒收集一次
        self.slow_query_threshold = 1000  # 慢查询阈值（毫秒）
        self.retention_days = 7  # 数据保留7天
        
        # 阈值配置
        self.thresholds = {
            "connection_usage": {
                "warning": 80.0,
                "critical": 95.0
            },
            "active_connections": {
                "warning": 100,
                "critical": 200
            },
            "query_duration": {
                "warning": 500.0,  # 毫秒
                "critical": 2000.0
            },
            "lock_wait_time": {
                "warning": 1000.0,  # 毫秒
                "critical": 5000.0
            },
            "replication_lag": {
                "warning": 60.0,  # 秒
                "critical": 300.0
            }
        }
    
    async def initialize(self):
        """初始化数据库监控器"""
        if self.running:
            return
        
        self.redis_client = get_redis_client()
        self.running = True
        
        logger.info("Database monitor initialized")
    
    async def shutdown(self):
        """关闭数据库监控器"""
        self.running = False
        logger.info("Database monitor shutdown")
    
    async def start_monitoring(self):
        """开始监控"""
        if not self.running:
            await self.initialize()
        
        logger.info("Starting database monitoring...")
        
        while self.running:
            try:
                # 收集所有数据库指标
                metrics = await self.collect_all_metrics()
                
                # 存储指标
                await self.store_metrics(metrics)
                
                # 检查告警
                await self.check_alerts(metrics)
                
                # 收集慢查询
                await self.collect_slow_queries()
                
                # 等待下次收集
                await asyncio.sleep(self.collection_interval)
                
            except Exception as e:
                logger.error(f"Error in database monitoring loop: {e}")
                await asyncio.sleep(60)  # 出错时等待1分钟
    
    async def collect_all_metrics(self) -> List[DatabaseMetric]:
        """收集所有数据库指标"""
        metrics = []
        
        try:
            # 连接指标
            connection_metrics = await self.collect_connection_metrics()
            metrics.extend(connection_metrics)
            
            # 查询性能指标
            query_metrics = await self.collect_query_metrics()
            metrics.extend(query_metrics)
            
            # 锁等待指标
            lock_metrics = await self.collect_lock_metrics()
            metrics.extend(lock_metrics)
            
            # 性能指标
            performance_metrics = await self.collect_performance_metrics()
            metrics.extend(performance_metrics)
            
            # 复制指标（如果配置了主从复制）
            replication_metrics = await self.collect_replication_metrics()
            metrics.extend(replication_metrics)
            
        except Exception as e:
            logger.error(f"Error collecting database metrics: {e}")
        
        return metrics
    
    async def collect_connection_metrics(self) -> List[DatabaseMetric]:
        """收集连接指标"""
        metrics = []
        timestamp = datetime.now()
        
        try:
            async with get_async_session() as session:
                # PostgreSQL连接统计
                if settings.DATABASE_URL.startswith("postgresql"):
                    result = await session.execute(text("""
                        SELECT 
                            count(*) as total_connections,
                            count(*) FILTER (WHERE state = 'active') as active_connections,
                            count(*) FILTER (WHERE state = 'idle') as idle_connections,
                            count(*) FILTER (WHERE wait_event IS NOT NULL) as waiting_connections,
                            (SELECT setting::int FROM pg_settings WHERE name = 'max_connections') as max_connections
                        FROM pg_stat_activity
                        WHERE datname = current_database()
                    """))
                    
                    row = result.fetchone()
                    
                    total_connections = row.total_connections
                    active_connections = row.active_connections
                    idle_connections = row.idle_connections
                    waiting_connections = row.waiting_connections
                    max_connections = row.max_connections
                    connection_usage_percent = (total_connections / max_connections) * 100
                    
                    metrics.append(DatabaseMetric(
                        timestamp=timestamp,
                        metric_type=MetricType.CONNECTION,
                        metric_name="total_connections",
                        value=total_connections,
                        unit="count",
                        metadata={
                            "active": active_connections,
                            "idle": idle_connections,
                            "waiting": waiting_connections,
                            "max": max_connections
                        }
                    ))
                    
                    metrics.append(DatabaseMetric(
                        timestamp=timestamp,
                        metric_type=MetricType.CONNECTION,
                        metric_name="active_connections",
                        value=active_connections,
                        unit="count",
                        threshold_warning=self.thresholds["active_connections"]["warning"],
                        threshold_critical=self.thresholds["active_connections"]["critical"]
                    ))
                    
                    metrics.append(DatabaseMetric(
                        timestamp=timestamp,
                        metric_type=MetricType.CONNECTION,
                        metric_name="connection_usage_percent",
                        value=connection_usage_percent,
                        unit="percent",
                        threshold_warning=self.thresholds["connection_usage"]["warning"],
                        threshold_critical=self.thresholds["connection_usage"]["critical"],
                        metadata={
                            "total": total_connections,
                            "max": max_connections
                        }
                    ))
                    
                    metrics.append(DatabaseMetric(
                        timestamp=timestamp,
                        metric_type=MetricType.CONNECTION,
                        metric_name="waiting_connections",
                        value=waiting_connections,
                        unit="count",
                        threshold_warning=10,
                        threshold_critical=50
                    ))
        
        except Exception as e:
            logger.error(f"Error collecting connection metrics: {e}")
        
        return metrics
    
    async def collect_query_metrics(self) -> List[DatabaseMetric]:
        """收集查询指标"""
        metrics = []
        timestamp = datetime.now()
        
        try:
            async with get_async_session() as session:
                # PostgreSQL查询统计
                if settings.DATABASE_URL.startswith("postgresql"):
                    # 获取当前活跃查询
                    result = await session.execute(text("""
                        SELECT 
                            count(*) as active_queries,
                            avg(EXTRACT(EPOCH FROM (now() - query_start)) * 1000) as avg_duration_ms,
                            max(EXTRACT(EPOCH FROM (now() - query_start)) * 1000) as max_duration_ms
                        FROM pg_stat_activity
                        WHERE state = 'active' AND query_start IS NOT NULL
                    """))
                    
                    row = result.fetchone()
                    
                    active_queries = row.active_queries or 0
                    avg_duration_ms = row.avg_duration_ms or 0
                    max_duration_ms = row.max_duration_ms or 0
                    
                    metrics.append(DatabaseMetric(
                        timestamp=timestamp,
                        metric_type=MetricType.QUERY,
                        metric_name="active_queries",
                        value=active_queries,
                        unit="count",
                        threshold_warning=50,
                        threshold_critical=100
                    ))
                    
                    metrics.append(DatabaseMetric(
                        timestamp=timestamp,
                        metric_type=MetricType.QUERY,
                        metric_name="avg_query_duration_ms",
                        value=avg_duration_ms,
                        unit="ms",
                        threshold_warning=self.thresholds["query_duration"]["warning"],
                        threshold_critical=self.thresholds["query_duration"]["critical"]
                    ))
                    
                    metrics.append(DatabaseMetric(
                        timestamp=timestamp,
                        metric_type=MetricType.QUERY,
                        metric_name="max_query_duration_ms",
                        value=max_duration_ms,
                        unit="ms",
                        threshold_warning=self.thresholds["query_duration"]["warning"],
                        threshold_critical=self.thresholds["query_duration"]["critical"]
                    ))
                    
                    # 获取查询统计
                    result = await session.execute(text("""
                        SELECT 
                            sum(calls) as total_calls,
                            sum(total_exec_time) as total_exec_time,
                            sum(total_exec_time) / sum(calls) as avg_exec_time
                        FROM pg_stat_statements
                        WHERE calls > 0
                    """))
                    
                    row = result.fetchone()
                    
                    if row and row.total_calls:
                        total_calls = row.total_calls
                        total_exec_time = row.total_exec_time
                        avg_exec_time = row.avg_exec_time
                        
                        metrics.append(DatabaseMetric(
                            timestamp=timestamp,
                            metric_type=MetricType.QUERY,
                            metric_name="total_query_calls",
                            value=total_calls,
                            unit="count"
                        ))
                        
                        metrics.append(DatabaseMetric(
                            timestamp=timestamp,
                            metric_type=MetricType.QUERY,
                            metric_name="avg_query_exec_time_ms",
                            value=avg_exec_time,
                            unit="ms",
                            threshold_warning=self.thresholds["query_duration"]["warning"],
                            threshold_critical=self.thresholds["query_duration"]["critical"]
                        ))
        
        except Exception as e:
            logger.error(f"Error collecting query metrics: {e}")
        
        return metrics
    
    async def collect_lock_metrics(self) -> List[DatabaseMetric]:
        """收集锁指标"""
        metrics = []
        timestamp = datetime.now()
        
        try:
            async with get_async_session() as session:
                # PostgreSQL锁统计
                if settings.DATABASE_URL.startswith("postgresql"):
                    result = await session.execute(text("""
                        SELECT 
                            count(*) FILTER (WHERE granted = false) as waiting_locks,
                            count(*) FILTER (WHERE granted = true) as granted_locks,
                            count(*) as total_locks
                        FROM pg_locks
                        WHERE pid IS NOT NULL
                    """))
                    
                    row = result.fetchone()
                    
                    waiting_locks = row.waiting_locks or 0
                    granted_locks = row.granted_locks or 0
                    total_locks = row.total_locks or 0
                    
                    metrics.append(DatabaseMetric(
                        timestamp=timestamp,
                        metric_type=MetricType.LOCK,
                        metric_name="waiting_locks",
                        value=waiting_locks,
                        unit="count",
                        threshold_warning=5,
                        threshold_critical=20
                    ))
                    
                    metrics.append(DatabaseMetric(
                        timestamp=timestamp,
                        metric_type=MetricType.LOCK,
                        metric_name="total_locks",
                        value=total_locks,
                        unit="count",
                        metadata={
                            "granted": granted_locks,
                            "waiting": waiting_locks
                        }
                    ))
                    
                    # 获取锁等待时间
                    result = await session.execute(text("""
                        SELECT 
                            avg(EXTRACT(EPOCH FROM (now() - query_start)) * 1000) as avg_lock_wait_ms
                        FROM pg_stat_activity
                        WHERE wait_event_type = 'Lock' AND query_start IS NOT NULL
                    """))
                    
                    row = result.fetchone()
                    avg_lock_wait_ms = row.avg_lock_wait_ms or 0
                    
                    metrics.append(DatabaseMetric(
                        timestamp=timestamp,
                        metric_type=MetricType.LOCK,
                        metric_name="avg_lock_wait_ms",
                        value=avg_lock_wait_ms,
                        unit="ms",
                        threshold_warning=self.thresholds["lock_wait_time"]["warning"],
                        threshold_critical=self.thresholds["lock_wait_time"]["critical"]
                    ))
        
        except Exception as e:
            logger.error(f"Error collecting lock metrics: {e}")
        
        return metrics
    
    async def collect_performance_metrics(self) -> List[DatabaseMetric]:
        """收集性能指标"""
        metrics = []
        timestamp = datetime.now()
        
        try:
            async with get_async_session() as session:
                # PostgreSQL性能指标
                if settings.DATABASE_URL.startswith("postgresql"):
                    # 缓存命中率
                    result = await session.execute(text("""
                        SELECT 
                            sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) * 100 as cache_hit_ratio
                        FROM pg_stat_database
                        WHERE datname = current_database()
                    """))
                    
                    row = result.fetchone()
                    cache_hit_ratio = row.cache_hit_ratio or 0
                    
                    metrics.append(DatabaseMetric(
                        timestamp=timestamp,
                        metric_type=MetricType.PERFORMANCE,
                        metric_name="cache_hit_ratio_percent",
                        value=cache_hit_ratio,
                        unit="percent",
                        threshold_warning=90.0,  # 缓存命中率应该很高
                        threshold_critical=80.0
                    ))
                    
                    # 数据库大小
                    result = await session.execute(text("""
                        SELECT 
                            pg_database_size(current_database()) / (1024^3) as database_size_gb
                    """))
                    
                    row = result.fetchone()
                    database_size_gb = row.database_size_gb or 0
                    
                    metrics.append(DatabaseMetric(
                        timestamp=timestamp,
                        metric_type=MetricType.PERFORMANCE,
                        metric_name="database_size_gb",
                        value=database_size_gb,
                        unit="GB"
                    ))
                    
                    # 事务统计
                    result = await session.execute(text("""
                        SELECT 
                            xact_commit as commits,
                            xact_rollback as rollbacks,
                            tup_returned as tuples_returned,
                            tup_fetched as tuples_fetched,
                            tup_inserted as tuples_inserted,
                            tup_updated as tuples_updated,
                            tup_deleted as tuples_deleted
                        FROM pg_stat_database
                        WHERE datname = current_database()
                    """))
                    
                    row = result.fetchone()
                    
                    if row:
                        metrics.append(DatabaseMetric(
                            timestamp=timestamp,
                            metric_type=MetricType.PERFORMANCE,
                            metric_name="transaction_commits",
                            value=row.commits,
                            unit="count"
                        ))
                        
                        metrics.append(DatabaseMetric(
                            timestamp=timestamp,
                            metric_type=MetricType.PERFORMANCE,
                            metric_name="transaction_rollbacks",
                            value=row.rollbacks,
                            unit="count",
                            threshold_warning=10,
                            threshold_critical=50
                        ))
                        
                        metrics.append(DatabaseMetric(
                            timestamp=timestamp,
                            metric_type=MetricType.PERFORMANCE,
                            metric_name="tuples_returned",
                            value=row.tuples_returned,
                            unit="count"
                        ))
        
        except Exception as e:
            logger.error(f"Error collecting performance metrics: {e}")
        
        return metrics
    
    async def collect_replication_metrics(self) -> List[DatabaseMetric]:
        """收集复制指标"""
        metrics = []
        timestamp = datetime.now()
        
        try:
            async with get_async_session() as session:
                # PostgreSQL复制统计
                if settings.DATABASE_URL.startswith("postgresql"):
                    # 检查是否是主库
                    result = await session.execute(text("""
                        SELECT pg_is_in_recovery() as is_standby
                    """))
                    
                    row = result.fetchone()
                    is_standby = row.is_standby
                    
                    if not is_standby:
                        # 主库：获取复制延迟
                        result = await session.execute(text("""
                            SELECT 
                                count(*) as standby_count,
                                coalesce(pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lsn), 0) / 1024 / 1024 as replication_lag_mb
                            FROM pg_stat_replication
                        """))
                        
                        row = result.fetchone()
                        standby_count = row.standby_count or 0
                        replication_lag_mb = row.replication_lag_mb or 0
                        
                        metrics.append(DatabaseMetric(
                            timestamp=timestamp,
                            metric_type=MetricType.REPLICATION,
                            metric_name="standby_count",
                            value=standby_count,
                            unit="count"
                        ))
                        
                        metrics.append(DatabaseMetric(
                            timestamp=timestamp,
                            metric_type=MetricType.REPLICATION,
                            metric_name="replication_lag_mb",
                            value=replication_lag_mb,
                            unit="MB",
                            threshold_warning=100,
                            threshold_critical=500
                        ))
                    else:
                        # 备库：获取恢复延迟
                        result = await session.execute(text("""
                            SELECT 
                                pg_wal_lsn_diff(pg_last_wal_receive_lsn(), pg_last_wal_replay_lsn()) / 1024 / 1024 as recovery_lag_mb
                        """))
                        
                        row = result.fetchone()
                        recovery_lag_mb = row.recovery_lag_mb or 0
                        
                        metrics.append(DatabaseMetric(
                            timestamp=timestamp,
                            metric_type=MetricType.REPLICATION,
                            metric_name="recovery_lag_mb",
                            value=recovery_lag_mb,
                            unit="MB",
                            threshold_warning=100,
                            threshold_critical=500
                        ))
        
        except Exception as e:
            logger.error(f"Error collecting replication metrics: {e}")
        
        return metrics
    
    async def collect_slow_queries(self):
        """收集慢查询"""
        try:
            async with get_async_session() as session:
                if settings.DATABASE_URL.startswith("postgresql"):
                    # 获取当前正在执行的慢查询
                    result = await session.execute(text("""
                        SELECT 
                            query,
                            EXTRACT(EPOCH FROM (now() - query_start)) * 1000 as duration_ms,
                            datname as database,
                            usename as user,
                            application_name,
                            state,
                            wait_event
                        FROM pg_stat_activity
                        WHERE state = 'active' 
                            AND query_start IS NOT NULL
                            AND EXTRACT(EPOCH FROM (now() - query_start)) * 1000 > :threshold
                        ORDER BY query_start
                    """), {"threshold": self.slow_query_threshold})
                    
                    slow_queries = []
                    for row in result:
                        slow_query = SlowQuery(
                            timestamp=datetime.now(),
                            query=row.query[:500] + "..." if len(row.query) > 500 else row.query,
                            duration_ms=row.duration_ms,
                            database=row.database,
                            user=row.user,
                            application_name=row.application_name,
                            state=row.state,
                            wait_event=row.wait_event,
                            query_hash=str(hash(row.query))
                        )
                        slow_queries.append(slow_query)
                    
                    # 存储慢查询记录
                    await self.store_slow_queries(slow_queries)
                    
                    # 如果有慢查询，创建告警
                    if slow_queries:
                        await self.create_slow_query_alert(slow_queries)
        
        except Exception as e:
            logger.error(f"Error collecting slow queries: {e}")
    
    async def store_metrics(self, metrics: List[DatabaseMetric]):
        """存储指标到Redis"""
        try:
            for metric in metrics:
                # 存储最新值
                latest_key = f"db_metric:latest:{metric.metric_type.value}:{metric.metric_name}"
                metric_data = {
                    "timestamp": metric.timestamp.isoformat(),
                    "value": metric.value,
                    "unit": metric.unit,
                    "status": metric.status,
                    "metadata": metric.metadata
                }
                
                await self.redis_client.setex(
                    latest_key,
                    self.retention_days * 24 * 3600,
                    json.dumps(metric_data)
                )
                
                # 存储历史数据（时间序列）
                history_key = f"db_metric:history:{metric.metric_type.value}:{metric.metric_name}"
                timestamp_key = int(metric.timestamp.timestamp())
                
                await self.redis_client.zadd(
                    history_key,
                    {json.dumps(metric_data): timestamp_key}
                )
                
                # 清理过期数据
                cutoff_time = int((datetime.now() - timedelta(days=self.retention_days)).timestamp())
                await self.redis_client.zremrangebyscore(history_key, 0, cutoff_time)
                
                # 设置过期时间
                await self.redis_client.expire(history_key, self.retention_days * 24 * 3600)
        
        except Exception as e:
            logger.error(f"Error storing database metrics: {e}")
    
    async def store_slow_queries(self, slow_queries: List[SlowQuery]):
        """存储慢查询记录"""
        try:
            for query in slow_queries:
                # 存储慢查询记录
                query_key = f"db_slow_query:{query.query_hash}"
                query_data = {
                    "timestamp": query.timestamp.isoformat(),
                    "query": query.query,
                    "duration_ms": query.duration_ms,
                    "database": query.database,
                    "user": query.user,
                    "application_name": query.application_name,
                    "state": query.state,
                    "wait_event": query.wait_event
                }
                
                await self.redis_client.setex(
                    query_key,
                    self.retention_days * 24 * 3600,
                    json.dumps(query_data)
                )
                
                # 添加到慢查询时间序列
                slow_query_history_key = "db_slow_query_history"
                await self.redis_client.zadd(
                    slow_query_history_key,
                    {json.dumps(query_data): int(query.timestamp.timestamp())}
                )
                
                # 清理过期数据
                cutoff_time = int((datetime.now() - timedelta(days=self.retention_days)).timestamp())
                await self.redis_client.zremrangebyscore(slow_query_history_key, 0, cutoff_time)
        
        except Exception as e:
            logger.error(f"Error storing slow queries: {e}")
    
    async def check_alerts(self, metrics: List[DatabaseMetric]):
        """检查告警条件"""
        try:
            for metric in metrics:
                if metric.status == "warning":
                    await self.create_alert(
                        metric,
                        AlertSeverity.WARNING,
                        f"Database {metric.metric_name} Warning",
                        f"Database {metric.metric_name} is {metric.value:.1f}{metric.unit}, exceeding warning threshold of {metric.threshold_warning}{metric.unit}"
                    )
                
                elif metric.status == "critical":
                    await self.create_alert(
                        metric,
                        AlertSeverity.CRITICAL,
                        f"Database {metric.metric_name} Critical",
                        f"Database {metric.metric_name} is {metric.value:.1f}{metric.unit}, exceeding critical threshold of {metric.threshold_critical}{metric.unit}"
                    )
        
        except Exception as e:
            logger.error(f"Error checking database alerts: {e}")
    
    async def create_alert(self, metric: DatabaseMetric, severity: AlertSeverity, title: str, description: str):
        """创建告警"""
        try:
            # 检查是否已经存在相同的活跃告警
            alert_key = f"db_alert:{metric.metric_type.value}:{metric.metric_name}"
            existing_alert = await self.redis_client.get(alert_key)
            
            if existing_alert:
                # 告警已存在，更新时间戳
                alert_data = json.loads(existing_alert)
                last_update = datetime.fromisoformat(alert_data["last_update"])
                
                # 如果在冷却时间内，不重复创建告警
                if datetime.now() - last_update < timedelta(minutes=15):
                    return
            
            # 创建新告警
            await alert_manager.create_alert(
                title=title,
                description=description,
                severity=severity,
                source="database_monitor",
                service="web3search",
                environment=settings.ENVIRONMENT,
                labels={
                    "metric_type": metric.metric_type.value,
                    "metric_name": metric.metric_name,
                    "database": settings.DATABASE_URL.split("/")[-1].split("?")[0]
                },
                annotations={
                    "current_value": str(metric.value),
                    "unit": metric.unit,
                    "threshold_warning": str(metric.threshold_warning),
                    "threshold_critical": str(metric.threshold_critical),
                    "metadata": json.dumps(metric.metadata)
                },
                current_value=metric.value,
                threshold_value=metric.threshold_critical if severity == AlertSeverity.CRITICAL else metric.threshold_warning
            )
            
            # 存储告警记录（用于冷却）
            await self.redis_client.setex(
                alert_key,
                3600,  # 1小时冷却
                json.dumps({
                    "metric_name": metric.metric_name,
                    "severity": severity.value,
                    "last_update": datetime.now().isoformat()
                })
            )
            
            logger.warning(f"Created database alert: {title}")
        
        except Exception as e:
            logger.error(f"Error creating database alert: {e}")
    
    async def create_slow_query_alert(self, slow_queries: List[SlowQuery]):
        """创建慢查询告警"""
        try:
            if not slow_queries:
                return
            
            # 取最慢的查询
            slowest_query = max(slow_queries, key=lambda q: q.duration_ms)
            
            await alert_manager.create_alert(
                title="Slow Query Detected",
                description=f"Slow query detected: {slowest_query.duration_ms:.1f}ms execution time",
                severity=AlertSeverity.WARNING,
                source="database_monitor",
                service="web3search",
                environment=settings.ENVIRONMENT,
                labels={
                    "query_type": "slow_query",
                    "database": slowest_query.database,
                    "application": slowest_query.application_name
                },
                annotations={
                    "query": slowest_query.query,
                    "duration_ms": str(slowest_query.duration_ms),
                    "user": slowest_query.user,
                    "state": slowest_query.state,
                    "wait_event": slowest_query.wait_event or "None"
                },
                current_value=slowest_query.duration_ms,
                threshold_value=self.slow_query_threshold
            )
            
            logger.warning(f"Created slow query alert: {slowest_query.duration_ms:.1f}ms")
        
        except Exception as e:
            logger.error(f"Error creating slow query alert: {e}")
    
    async def get_current_metrics(self) -> Dict[str, Any]:
        """获取当前数据库指标"""
        try:
            current_metrics = {}
            
            # 获取所有最新指标
            pattern = "db_metric:latest:*"
            
            async for key in self.redis_client.scan_iter(match=pattern):
                metric_data = await self.redis_client.get(key)
                
                if metric_data:
                    data = json.loads(metric_data)
                    metric_name = key.decode().split(":")[-1]
                    current_metrics[metric_name] = data
            
            return current_metrics
        
        except Exception as e:
            logger.error(f"Error getting current database metrics: {e}")
            return {}
    
    async def get_slow_queries(
        self,
        start_time: datetime,
        end_time: datetime,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """获取慢查询记录"""
        try:
            slow_query_history_key = "db_slow_query_history"
            
            start_timestamp = int(start_time.timestamp())
            end_timestamp = int(end_time.timestamp())
            
            # 获取时间范围内的慢查询
            results = await self.redis_client.zrangebyscore(
                slow_query_history_key,
                start_timestamp,
                end_timestamp,
                start=0,
                num=limit
            )
            
            slow_queries = []
            for result in results:
                data = json.loads(result)
                slow_queries.append(data)
            
            return slow_queries
        
        except Exception as e:
            logger.error(f"Error getting slow queries: {e}")
            return []
    
    async def get_database_summary(self) -> Dict[str, Any]:
        """获取数据库监控摘要"""
        try:
            current_metrics = await self.get_current_metrics()
            
            summary = {
                "timestamp": datetime.now().isoformat(),
                "metrics": {
                    "connection": {},
                    "query": {},
                    "lock": {},
                    "performance": {},
                    "replication": {}
                },
                "alerts": {
                    "warning": 0,
                    "critical": 0
                }
            }
            
            # 分类整理指标
            for metric_name, data in current_metrics.items():
                # 确定指标类型
                if "connection" in metric_name:
                    metric_type = "connection"
                elif "query" in metric_name:
                    metric_type = "query"
                elif "lock" in metric_name:
                    metric_type = "lock"
                elif "replication" in metric_name:
                    metric_type = "replication"
                else:
                    metric_type = "performance"
                
                summary["metrics"][metric_type][metric_name] = data
                
                # 统计告警
                if data.get("status") == "warning":
                    summary["alerts"]["warning"] += 1
                elif data.get("status") == "critical":
                    summary["alerts"]["critical"] += 1
            
            return summary
        
        except Exception as e:
            logger.error(f"Error getting database summary: {e}")
            return {}


# 全局数据库监控器实例
database_monitor = DatabaseMonitor()
