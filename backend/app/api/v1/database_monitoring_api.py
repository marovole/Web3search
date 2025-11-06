"""
数据库监控API
提供数据库性能监控的REST API接口
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import json

from app.core.database_monitor import (
    database_monitor, MetricType, QueryStatus,
    DatabaseMetric, SlowQuery, ConnectionInfo
)
from app.core.config import settings
from app.core.alerting_system import alert_manager, AlertSeverity
from app.api.deps import get_current_user, require_admin
from app.models.user import User

router = APIRouter(prefix="/database", tags=["Database Monitoring"])


# ================================
# Pydantic模型定义
# ================================

class DatabaseMetricResponse(BaseModel):
    """数据库指标响应"""
    timestamp: str
    metric_type: str
    metric_name: str
    value: float
    unit: str
    status: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    threshold_warning: float = 0.0
    threshold_critical: float = 0.0


class SlowQueryResponse(BaseModel):
    """慢查询响应"""
    timestamp: str
    query: str
    duration_ms: float
    database: str
    user: str
    application_name: str
    state: str
    wait_event: Optional[str] = None
    query_hash: Optional[str] = None


class DatabaseSummaryResponse(BaseModel):
    """数据库监控摘要响应"""
    timestamp: str
    metrics: Dict[str, Dict[str, Any]]
    alerts: Dict[str, int]


# ================================
# 基础监控API
# ================================

@router.get("/metrics/current")
async def get_current_database_metrics(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取当前所有数据库指标
    """
    try:
        current_metrics = await database_monitor.get_current_metrics()
        
        # 格式化响应数据
        formatted_metrics = {}
        
        for metric_name, data in current_metrics.items():
            formatted_metrics[metric_name] = {
                "timestamp": data["timestamp"],
                "value": data["value"],
                "unit": data["unit"],
                "status": data["status"],
                "metadata": data.get("metadata", {}),
                "threshold_warning": data.get("threshold_warning", 0.0),
                "threshold_critical": data.get("threshold_critical", 0.0)
            }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "metrics": formatted_metrics,
            "total_metrics": len(formatted_metrics)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get current database metrics: {str(e)}")


@router.get("/metrics/summary")
async def get_database_summary(
    current_user: User = Depends(require_admin)
) -> DatabaseSummaryResponse:
    """
    获取数据库监控摘要
    """
    try:
        summary = await database_monitor.get_database_summary()
        
        return DatabaseSummaryResponse(
            timestamp=summary["timestamp"],
            metrics=summary["metrics"],
            alerts=summary["alerts"]
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get database summary: {str(e)}")


# ================================
# 连接监控API
# ================================

@router.get("/connections")
async def get_database_connections(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取数据库连接信息
    """
    try:
        current_metrics = await database_monitor.get_current_metrics()
        
        connection_metrics = {}
        connection_keys = [
            "total_connections",
            "active_connections",
            "idle_connections",
            "waiting_connections",
            "connection_usage_percent"
        ]
        
        for key in connection_keys:
            if key in current_metrics:
                data = current_metrics[key]
                connection_metrics[key] = {
                    "value": data["value"],
                    "unit": data["unit"],
                    "status": data.get("status", "normal"),
                    "timestamp": data["timestamp"],
                    "metadata": data.get("metadata", {})
                }
        
        # 计算连接健康状态
        total_connections = connection_metrics.get("total_connections", {}).get("value", 0)
        active_connections = connection_metrics.get("active_connections", {}).get("value", 0)
        connection_usage = connection_metrics.get("connection_usage_percent", {}).get("value", 0)
        
        if connection_usage >= 95:
            connection_health = "critical"
        elif connection_usage >= 80:
            connection_health = "warning"
        else:
            connection_health = "healthy"
        
        return {
            "connections": connection_metrics,
            "health": {
                "status": connection_health,
                "usage_percent": connection_usage,
                "active_ratio": (active_connections / total_connections * 100) if total_connections > 0 else 0
            },
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get database connections: {str(e)}")


@router.get("/connections/history")
async def get_connection_history(
    hours: int = Query(default=1, ge=1, le=24, description="查询时间范围（小时）"),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取连接历史数据
    """
    try:
        from app.core.redis_client import get_redis_client
        
        redis_client = get_redis_client()
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        # 获取连接使用率历史
        history_key = "db_metric:history:connection:connection_usage_percent"
        start_timestamp = int(start_time.timestamp())
        end_timestamp = int(end_time.timestamp())
        
        results = await redis_client.zrangebyscore(
            history_key,
            start_timestamp,
            end_timestamp
        )
        
        history = []
        for result in results:
            data = json.loads(result)
            history.append(data)
        
        return {
            "history": history,
            "period": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "hours": hours
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get connection history: {str(e)}")


# ================================
# 查询监控API
# ================================

@router.get("/queries/performance")
async def get_query_performance(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取查询性能指标
    """
    try:
        current_metrics = await database_monitor.get_current_metrics()
        
        query_metrics = {}
        query_keys = [
            "active_queries",
            "avg_query_duration_ms",
            "max_query_duration_ms",
            "total_query_calls",
            "avg_query_exec_time_ms"
        ]
        
        for key in query_keys:
            if key in current_metrics:
                data = current_metrics[key]
                query_metrics[key] = {
                    "value": data["value"],
                    "unit": data["unit"],
                    "status": data.get("status", "normal"),
                    "timestamp": data["timestamp"],
                    "metadata": data.get("metadata", {})
                }
        
        # 计算查询性能评分
        avg_duration = query_metrics.get("avg_query_duration_ms", {}).get("value", 0)
        max_duration = query_metrics.get("max_query_duration_ms", {}).get("value", 0)
        active_count = query_metrics.get("active_queries", {}).get("value", 0)
        
        # 性能评分（0-100）
        performance_score = 100
        if avg_duration > 2000:
            performance_score -= 30
        elif avg_duration > 1000:
            performance_score -= 20
        elif avg_duration > 500:
            performance_score -= 10
        
        if max_duration > 5000:
            performance_score -= 20
        elif max_duration > 2000:
            performance_score -= 10
        
        if active_count > 100:
            performance_score -= 20
        elif active_count > 50:
            performance_score -= 10
        
        performance_score = max(0, performance_score)
        
        return {
            "performance": query_metrics,
            "score": {
                "value": performance_score,
                "status": "excellent" if performance_score >= 90 else "good" if performance_score >= 70 else "poor" if performance_score >= 50 else "critical"
            },
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get query performance: {str(e)}")


@router.get("/queries/slow")
async def get_slow_queries(
    hours: int = Query(default=1, ge=1, le=24, description="查询时间范围（小时）"),
    limit: int = Query(default=20, ge=1, le=100, description="返回数量限制"),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取慢查询记录
    """
    try:
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        slow_queries = await database_monitor.get_slow_queries(
            start_time,
            end_time,
            limit
        )
        
        # 格式化慢查询数据
        formatted_queries = []
        for query in slow_queries:
            formatted_queries.append({
                "timestamp": query["timestamp"],
                "query": query["query"],
                "duration_ms": query["duration_ms"],
                "database": query["database"],
                "user": query["user"],
                "application_name": query["application_name"],
                "state": query["state"],
                "wait_event": query.get("wait_event"),
                "query_hash": query.get("query_hash")
            })
        
        # 统计信息
        if formatted_queries:
            avg_duration = sum(q["duration_ms"] for q in formatted_queries) / len(formatted_queries)
            max_duration = max(q["duration_ms"] for q in formatted_queries)
            
            # 按应用分组
            by_application = {}
            for query in formatted_queries:
                app = query["application_name"]
                if app not in by_application:
                    by_application[app] = 0
                by_application[app] += 1
        else:
            avg_duration = max_duration = 0
            by_application = {}
        
        return {
            "slow_queries": formatted_queries,
            "statistics": {
                "total_count": len(formatted_queries),
                "avg_duration_ms": round(avg_duration, 2),
                "max_duration_ms": round(max_duration, 2),
                "by_application": by_application
            },
            "period": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "hours": hours
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get slow queries: {str(e)}")


@router.get("/queries/active")
async def get_active_queries(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取当前活跃查询
    """
    try:
        from app.core.database import get_async_session
        from sqlalchemy import text
        
        async with get_async_session() as session:
            if settings.DATABASE_URL.startswith("postgresql"):
                result = await session.execute(text("""
                    SELECT 
                        pid,
                        query,
                        EXTRACT(EPOCH FROM (now() - query_start)) * 1000 as duration_ms,
                        datname as database,
                        usename as user,
                        application_name,
                        state,
                        wait_event,
                        client_addr
                    FROM pg_stat_activity
                    WHERE state = 'active' AND query_start IS NOT NULL
                    ORDER BY query_start
                """))
                
                active_queries = []
                for row in result:
                    active_queries.append({
                        "pid": row.pid,
                        "query": row.query[:200] + "..." if len(row.query) > 200 else row.query,
                        "duration_ms": row.duration_ms,
                        "database": row.database,
                        "user": row.user,
                        "application_name": row.application_name,
                        "state": row.state,
                        "wait_event": row.wait_event,
                        "client_addr": row.client_addr
                    })
                
                return {
                    "active_queries": active_queries,
                    "total_count": len(active_queries),
                    "timestamp": datetime.now().isoformat()
                }
        
        return {"active_queries": [], "total_count": 0}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get active queries: {str(e)}")


# ================================
# 锁监控API
# ================================

@router.get("/locks")
async def get_database_locks(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取数据库锁信息
    """
    try:
        current_metrics = await database_monitor.get_current_metrics()
        
        lock_metrics = {}
        lock_keys = [
            "waiting_locks",
            "total_locks",
            "avg_lock_wait_ms"
        ]
        
        for key in lock_keys:
            if key in current_metrics:
                data = current_metrics[key]
                lock_metrics[key] = {
                    "value": data["value"],
                    "unit": data["unit"],
                    "status": data.get("status", "normal"),
                    "timestamp": data["timestamp"],
                    "metadata": data.get("metadata", {})
                }
        
        # 获取详细锁信息
        from app.core.database import get_async_session
        from sqlalchemy import text
        
        async with get_async_session() as session:
            if settings.DATABASE_URL.startswith("postgresql"):
                result = await session.execute(text("""
                    SELECT 
                        pg_class.relname as table_name,
                        pg_locks.locktype,
                        pg_locks.mode,
                        pg_locks.granted,
                        pg_stat_activity.pid,
                        pg_stat_activity.query,
                        pg_stat_activity.usename as user,
                        EXTRACT(EPOCH FROM (now() - pg_stat_activity.query_start)) * 1000 as duration_ms
                    FROM pg_locks
                    JOIN pg_class ON pg_locks.relation = pg_class.oid
                    JOIN pg_stat_activity ON pg_locks.pid = pg_stat_activity.pid
                    WHERE pg_locks.granted = false
                    ORDER BY pg_stat_activity.query_start
                    LIMIT 20
                """))
                
                waiting_locks = []
                for row in result:
                    waiting_locks.append({
                        "table_name": row.table_name,
                        "lock_type": row.locktype,
                        "mode": row.mode,
                        "granted": row.granted,
                        "pid": row.pid,
                        "query": row.query[:100] + "..." if len(row.query) > 100 else row.query,
                        "user": row.user,
                        "duration_ms": row.duration_ms
                    })
                
                return {
                    "metrics": lock_metrics,
                    "waiting_locks": waiting_locks,
                    "timestamp": datetime.now().isoformat()
                }
        
        return {"metrics": lock_metrics, "waiting_locks": []}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get database locks: {str(e)}")


# ================================
# 性能监控API
# ================================

@router.get("/performance")
async def get_database_performance(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取数据库性能指标
    """
    try:
        current_metrics = await database_monitor.get_current_metrics()
        
        performance_metrics = {}
        performance_keys = [
            "cache_hit_ratio_percent",
            "database_size_gb",
            "transaction_commits",
            "transaction_rollbacks",
            "tuples_returned"
        ]
        
        for key in performance_keys:
            if key in current_metrics:
                data = current_metrics[key]
                performance_metrics[key] = {
                    "value": data["value"],
                    "unit": data["unit"],
                    "status": data.get("status", "normal"),
                    "timestamp": data["timestamp"],
                    "metadata": data.get("metadata", {})
                }
        
        # 计算性能评分
        cache_hit_ratio = performance_metrics.get("cache_hit_ratio_percent", {}).get("value", 0)
        rollback_ratio = 0
        
        commits = performance_metrics.get("transaction_commits", {}).get("value", 0)
        rollbacks = performance_metrics.get("transaction_rollbacks", {}).get("value", 0)
        
        if commits + rollbacks > 0:
            rollback_ratio = (rollbacks / (commits + rollbacks)) * 100
        
        # 性能评分
        performance_score = 100
        if cache_hit_ratio < 80:
            performance_score -= 30
        elif cache_hit_ratio < 90:
            performance_score -= 15
        
        if rollback_ratio > 10:
            performance_score -= 20
        elif rollback_ratio > 5:
            performance_score -= 10
        
        performance_score = max(0, performance_score)
        
        return {
            "performance": performance_metrics,
            "score": {
                "value": performance_score,
                "status": "excellent" if performance_score >= 90 else "good" if performance_score >= 70 else "poor" if performance_score >= 50 else "critical"
            },
            "rollback_ratio_percent": round(rollback_ratio, 2),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get database performance: {str(e)}")


@router.get("/performance/history")
async def get_performance_history(
    hours: int = Query(default=24, ge=1, le=168, description="查询时间范围（小时）"),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取性能历史数据
    """
    try:
        from app.core.redis_client import get_redis_client
        
        redis_client = get_redis_client()
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        # 获取关键性能指标历史
        key_metrics = [
            "cache_hit_ratio_percent",
            "avg_query_duration_ms",
            "connection_usage_percent"
        ]
        
        history = {}
        
        for metric_name in key_metrics:
            history_key = f"db_metric:history:performance:{metric_name}"
            start_timestamp = int(start_time.timestamp())
            end_timestamp = int(end_time.timestamp())
            
            results = await redis_client.zrangebyscore(
                history_key,
                start_timestamp,
                end_timestamp
            )
            
            metric_history = []
            for result in results:
                data = json.loads(result)
                metric_history.append(data)
            
            history[metric_name] = metric_history
        
        return {
            "history": history,
            "period": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "hours": hours
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance history: {str(e)}")


# ================================
# 复制监控API
# ================================

@router.get("/replication")
async def get_database_replication(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取数据库复制状态
    """
    try:
        current_metrics = await database_monitor.get_current_metrics()
        
        replication_metrics = {}
        replication_keys = [
            "standby_count",
            "replication_lag_mb",
            "recovery_lag_mb"
        ]
        
        for key in replication_keys:
            if key in current_metrics:
                data = current_metrics[key]
                replication_metrics[key] = {
                    "value": data["value"],
                    "unit": data["unit"],
                    "status": data.get("status", "normal"),
                    "timestamp": data["timestamp"],
                    "metadata": data.get("metadata", {})
                }
        
        # 获取详细复制信息
        from app.core.database import get_async_session
        from sqlalchemy import text
        
        async with get_async_session() as session:
            if settings.DATABASE_URL.startswith("postgresql"):
                # 检查是否是主库
                result = await session.execute(text("""
                    SELECT pg_is_in_recovery() as is_standby
                """))
                
                row = result.fetchone()
                is_standby = row.is_standby
                
                replication_info = {
                    "role": "standby" if is_standby else "primary",
                    "detailed_info": {}
                }
                
                if not is_standby:
                    # 主库信息
                    result = await session.execute(text("""
                        SELECT 
                            application_name,
                            client_addr,
                            state,
                            sent_lsn,
                            write_lsn,
                            flush_lsn,
                            replay_lsn,
                            pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lsn) / 1024 / 1024 as lag_mb
                        FROM pg_stat_replication
                    """))
                    
                    replicas = []
                    for row in result:
                        replicas.append({
                            "application_name": row.application_name,
                            "client_addr": row.client_addr,
                            "state": row.state,
                            "lag_mb": row.lag_mb
                        })
                    
                    replication_info["detailed_info"]["replicas"] = replicas
                else:
                    # 备库信息
                    result = await session.execute(text("""
                        SELECT 
                            pg_last_wal_receive_lsn(),
                            pg_last_wal_replay_lsn(),
                            pg_is_wal_replay_paused() as replay_paused,
                            pg_wal_lsn_diff(pg_last_wal_receive_lsn(), pg_last_wal_replay_lsn()) / 1024 / 1024 as recovery_lag_mb
                    """))
                    
                    row = result.fetchone()
                    replication_info["detailed_info"] = {
                        "replay_paused": row.replay_paused,
                        "recovery_lag_mb": row.recovery_lag_mb
                    }
                
                return {
                    "metrics": replication_metrics,
                    "replication_info": replication_info,
                    "timestamp": datetime.now().isoformat()
                }
        
        return {"metrics": replication_metrics, "replication_info": {"role": "unknown"}}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get database replication: {str(e)}")


# ================================
# 告警和健康API
# ================================

@router.get("/alerts")
async def get_database_alerts(
    status: Optional[str] = Query(None, pattern="^(active|resolved|all)$", description="告警状态过滤"),
    severity: Optional[str] = Query(None, pattern="^(warning|critical|all)$", description="严重程度过滤"),
    limit: int = Query(default=50, ge=1, le=100, description="返回数量限制"),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取数据库告警
    """
    try:
        from app.core.alerting_system import AlertStatus
        
        # 转换过滤条件
        alert_status = None
        if status == "active":
            alert_status = AlertStatus.OPEN
        elif status == "resolved":
            alert_status = AlertStatus.RESOLVED
        
        alert_severity = None
        if severity == "warning":
            alert_severity = AlertSeverity.WARNING
        elif severity == "critical":
            alert_severity = AlertSeverity.CRITICAL
        
        # 获取告警
        alerts = await alert_manager.get_alerts(
            status=alert_status,
            severity=alert_severity,
            source="database_monitor",
            limit=limit
        )
        
        # 格式化告警数据
        formatted_alerts = []
        for alert in alerts:
            formatted_alerts.append({
                "alert_id": alert.alert_id,
                "title": alert.title,
                "description": alert.description,
                "severity": alert.severity.value,
                "status": alert.status.value,
                "source": alert.source,
                "service": alert.service,
                "timestamp": alert.timestamp.isoformat(),
                "labels": alert.labels,
                "current_value": alert.current_value,
                "threshold_value": alert.threshold_value
            })
        
        return {
            "alerts": formatted_alerts,
            "total_count": len(formatted_alerts),
            "filters": {
                "status": status,
                "severity": severity
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get database alerts: {str(e)}")


@router.get("/health")
async def get_database_health(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取数据库健康状态
    """
    try:
        summary = await database_monitor.get_database_summary()
        
        # 计算健康评分
        total_metrics = 0
        warning_metrics = 0
        critical_metrics = 0
        
        for metric_data in summary["metrics"].values():
            for metric_name, data in metric_data.items():
                total_metrics += 1
                if data.get("status") == "warning":
                    warning_metrics += 1
                elif data.get("status") == "critical":
                    critical_metrics += 1
        
        # 健康评分计算
        if total_metrics > 0:
            health_score = max(0, 100 - (warning_metrics * 15) - (critical_metrics * 30))
        else:
            health_score = 100
        
        # 健康状态
        if health_score >= 90:
            health_status = "excellent"
        elif health_score >= 75:
            health_status = "good"
        elif health_score >= 60:
            health_status = "warning"
        else:
            health_status = "critical"
        
        # 数据库特定的健康检查
        health_checks = await _perform_database_health_checks()
        
        return {
            "health_score": round(health_score, 2),
            "health_status": health_status,
            "total_metrics": total_metrics,
            "warning_metrics": warning_metrics,
            "critical_metrics": critical_metrics,
            "active_alerts": summary["alerts"]["warning"] + summary["alerts"]["critical"],
            "health_checks": health_checks,
            "timestamp": datetime.now().isoformat(),
            "recommendations": _generate_database_health_recommendations(health_status, summary, health_checks)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get database health: {str(e)}")


# ================================
# 辅助函数
# ================================

async def _perform_database_health_checks() -> Dict[str, Any]:
    """执行数据库健康检查"""
    health_checks = {
        "connection_test": {"status": "unknown", "message": ""},
        "query_test": {"status": "unknown", "message": ""},
        "write_test": {"status": "unknown", "message": ""},
        "replication_test": {"status": "unknown", "message": ""}
    }
    
    try:
        from app.core.database import get_async_session
        from sqlalchemy import text
        
        # 连接测试
        try:
            async with get_async_session() as session:
                await session.execute(text("SELECT 1"))
                health_checks["connection_test"] = {"status": "healthy", "message": "Database connection successful"}
        except Exception as e:
            health_checks["connection_test"] = {"status": "critical", "message": f"Connection failed: {str(e)}"}
        
        # 查询测试
        try:
            async with get_async_session() as session:
                result = await session.execute(text("SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()"))
                row = result.fetchone()
                health_checks["query_test"] = {"status": "healthy", "message": f"Query successful, {row[0]} active connections"}
        except Exception as e:
            health_checks["query_test"] = {"status": "critical", "message": f"Query failed: {str(e)}"}
        
        # 写入测试（创建临时表）
        try:
            async with get_async_session() as session:
                await session.execute(text("""
                    CREATE TEMPORARY TABLE IF NOT EXISTS health_check_test (
                        id SERIAL PRIMARY KEY,
                        test_time TIMESTAMP DEFAULT NOW()
                    )
                """))
                await session.execute(text("INSERT INTO health_check_test DEFAULT VALUES"))
                await session.commit()
                health_checks["write_test"] = {"status": "healthy", "message": "Write operation successful"}
        except Exception as e:
            health_checks["write_test"] = {"status": "critical", "message": f"Write test failed: {str(e)}"}
        
        # 复制测试
        try:
            async with get_async_session() as session:
                result = await session.execute(text("SELECT pg_is_in_recovery()"))
                row = result.fetchone()
                is_standby = row[0]
                
                if not is_standby:
                    result = await session.execute(text("SELECT count(*) FROM pg_stat_replication"))
                    row = result.fetchone()
                    replica_count = row[0]
                    health_checks["replication_test"] = {"status": "healthy", "message": f"Primary server with {replica_count} replicas"}
                else:
                    health_checks["replication_test"] = {"status": "healthy", "message": "Standby server"}
        except Exception as e:
            health_checks["replication_test"] = {"status": "warning", "message": f"Replication check failed: {str(e)}"}
    
    except Exception as e:
        logger.error(f"Error performing database health checks: {e}")
    
    return health_checks


def _generate_database_health_recommendations(health_status: str, summary: Dict[str, Any], health_checks: Dict[str, Any]) -> List[str]:
    """生成数据库健康建议"""
    recommendations = []
    
    try:
        if health_status == "critical":
            recommendations.append("数据库状态严重，需要立即检查和处理")
            recommendations.append("检查连接数、查询性能和锁等待情况")
        elif health_status == "warning":
            recommendations.append("数据库性能需要关注，建议优化查询和索引")
        
        # 基于健康检查的建议
        for check_name, check_result in health_checks.items():
            if check_result["status"] == "critical":
                recommendations.append(f"紧急处理 {check_name} 问题: {check_result['message']}")
            elif check_result["status"] == "warning":
                recommendations.append(f"关注 {check_name}: {check_result['message']}")
        
        # 基于指标的建议
        if summary["alerts"]["critical"] > 0:
            recommendations.append("存在严重告警，需要立即处理数据库问题")
        
        if summary["alerts"]["warning"] > 3:
            recommendations.append("警告告警较多，建议进行数据库优化")
        
        # 检查具体的指标问题
        for metric_type, metrics in summary["metrics"].items():
            for metric_name, metric_data in metrics.items():
                if metric_data.get("status") == "critical":
                    if "connection" in metric_name:
                        recommendations.append("数据库连接数过高，考虑优化连接池或增加连接限制")
                    elif "query" in metric_name:
                        recommendations.append("查询性能问题，建议优化慢查询和索引")
                    elif "lock" in metric_name:
                        recommendations.append("存在锁等待，检查长时间运行的事务")
                    elif "cache" in metric_name:
                        recommendations.append("缓存命中率低，考虑调整shared_buffers配置")
    
    except Exception as e:
        recommendations.append(f"生成建议时出错: {str(e)}")
    
    return recommendations
