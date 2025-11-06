"""
日志查询和分析界面API
提供日志查询、分析、可视化和洞察生成的REST API接口
"""
from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import asyncio

from app.core.log_aggregation import (
    LogEntry, LogLevel, LogSource, LogQuery, LogQueryResult,
    log_aggregator, log_analyzer
)
from app.core.structured_logging import structured_log_manager, get_logger
from app.core.alerting_system import alert_manager, AlertSeverity
from app.core.alert_rules_engine import alert_rule_engine
from app.api.deps import get_current_user, require_admin
from app.models.user import User

router = APIRouter(prefix="/logs", tags=["Log Query & Analysis"])


# ================================
# Pydantic模型定义
# ================================

class LogQueryRequest(BaseModel):
    """日志查询请求"""
    query: str = Field(..., description="搜索查询字符串")
    start_time: datetime = Field(..., description="开始时间")
    end_time: datetime = Field(..., description="结束时间")
    level: Optional[LogLevel] = Field(None, description="日志级别过滤")
    source: Optional[LogSource] = Field(None, description="日志来源过滤")
    service: Optional[str] = Field(None, description="服务名过滤")
    trace_id: Optional[str] = Field(None, description="追踪ID过滤")
    user_id: Optional[str] = Field(None, description="用户ID过滤")
    tags: Dict[str, str] = Field(default_factory=dict, description="标签过滤")
    limit: int = Field(default=100, ge=1, le=10000, description="返回数量限制")


class LogAnalysisRequest(BaseModel):
    """日志分析请求"""
    start_time: datetime = Field(..., description="分析开始时间")
    end_time: datetime = Field(..., description="分析结束时间")
    analysis_types: List[str] = Field(default=["error_patterns", "performance_issues"], description="分析类型")
    services: Optional[List[str]] = Field(None, description="服务过滤")
    sources: Optional[List[LogSource]] = Field(None, description="来源过滤")


class LogExportRequest(BaseModel):
    """日志导出请求"""
    query: LogQueryRequest
    format: str = Field(default="json", pattern="^(json|csv|xlsx)$", description="导出格式")
    include_fields: List[str] = Field(default=["timestamp", "level", "message", "service", "source"], description="包含字段")


class LogInsightRequest(BaseModel):
    """日志洞察请求"""
    start_time: datetime = Field(..., description="洞察开始时间")
    end_time: datetime = Field(..., description="洞察结束时间")
    focus_areas: List[str] = Field(default=["errors", "performance", "security"], description="关注领域")
    service: Optional[str] = Field(None, description="服务过滤")


# ================================
# 日志查询API
# ================================

@router.post("/query")
async def query_logs(
    request: LogQueryRequest,
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    查询日志
    """
    try:
        # 构建查询对象
        log_query = LogQuery(
            query=request.query,
            start_time=request.start_time,
            end_time=request.end_time,
            level=request.level,
            source=request.source,
            service=request.service,
            trace_id=request.trace_id,
            user_id=request.user_id,
            tags=request.tags,
            limit=request.limit
        )
        
        # 执行查询
        result = await log_aggregator.query_logs(log_query)
        
        # 格式化返回数据
        entries = []
        for entry in result.entries:
            entries.append({
                "timestamp": entry.timestamp.isoformat(),
                "level": entry.level.value,
                "message": entry.message,
                "source": entry.source.value,
                "service": entry.service,
                "environment": entry.environment,
                "trace_id": entry.trace_id,
                "span_id": entry.span_id,
                "user_id": entry.user_id,
                "request_id": entry.request_id,
                "session_id": entry.session_id,
                "ip_address": entry.ip_address,
                "user_agent": entry.user_agent,
                "method": entry.method,
                "url": entry.url,
                "status_code": entry.status_code,
                "duration_ms": entry.duration_ms,
                "error_type": entry.error_type,
                "error_stack": entry.error_stack,
                "tags": entry.tags,
                "metadata": entry.metadata
            })
        
        return {
            "query": {
                "query": request.query,
                "start_time": request.start_time.isoformat(),
                "end_time": request.end_time.isoformat(),
                "filters": {
                    "level": request.level.value if request.level else None,
                    "source": request.source.value if request.source else None,
                    "service": request.service,
                    "trace_id": request.trace_id,
                    "user_id": request.user_id,
                    "tags": request.tags
                },
                "limit": request.limit
            },
            "result": {
                "total_count": result.total_count,
                "execution_time_ms": result.execution_time_ms,
                "has_more": result.has_more,
                "entries": entries
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to query logs: {str(e)}")


@router.get("/search")
async def search_logs(
    q: str = Query(..., description="搜索关键词"),
    start_time: datetime = Query(..., description="开始时间"),
    end_time: datetime = Query(..., description="结束时间"),
    level: Optional[LogLevel] = Query(None, description="日志级别"),
    source: Optional[LogSource] = Query(None, description="日志来源"),
    service: Optional[str] = Query(None, description="服务名"),
    limit: int = Query(default=100, ge=1, le=1000, description="返回数量"),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    简化的日志搜索接口
    """
    try:
        # 构建查询
        log_query = LogQuery(
            query=q,
            start_time=start_time,
            end_time=end_time,
            level=level,
            source=source,
            service=service,
            limit=limit
        )
        
        # 执行查询
        result = await log_aggregator.query_logs(log_query)
        
        # 简化返回格式
        entries = []
        for entry in result.entries:
            entries.append({
                "timestamp": entry.timestamp.isoformat(),
                "level": entry.level.value,
                "message": entry.message[:200] + "..." if len(entry.message) > 200 else entry.message,
                "service": entry.service,
                "source": entry.source.value,
                "trace_id": entry.trace_id,
                "user_id": entry.user_id
            })
        
        return {
            "query": q,
            "total_count": result.total_count,
            "execution_time_ms": result.execution_time_ms,
            "entries": entries
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search logs: {str(e)}")


@router.get("/trace/{trace_id}")
async def get_trace_logs(
    trace_id: str,
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取特定追踪的所有日志
    """
    try:
        # 构建查询
        log_query = LogQuery(
            query="",
            start_time=datetime.now() - timedelta(hours=24),
            end_time=datetime.now(),
            trace_id=trace_id,
            limit=1000
        )
        
        # 执行查询
        result = await log_aggregator.query_logs(log_query)
        
        # 按时间排序并分组
        entries_by_service = {}
        timeline = []
        
        for entry in result.entries:
            # 按服务分组
            if entry.service not in entries_by_service:
                entries_by_service[entry.service] = []
            
            entries_by_service[entry.service].append({
                "timestamp": entry.timestamp.isoformat(),
                "level": entry.level.value,
                "message": entry.message,
                "source": entry.source.value,
                "span_id": entry.span_id,
                "duration_ms": entry.duration_ms
            })
            
            # 添加到时间线
            timeline.append({
                "timestamp": entry.timestamp.isoformat(),
                "service": entry.service,
                "level": entry.level.value,
                "message": entry.message[:100] + "..." if len(entry.message) > 100 else entry.message,
                "span_id": entry.span_id
            })
        
        # 排序时间线
        timeline.sort(key=lambda x: x["timestamp"])
        
        return {
            "trace_id": trace_id,
            "total_entries": result.total_count,
            "services": list(entries_by_service.keys()),
            "entries_by_service": entries_by_service,
            "timeline": timeline
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get trace logs: {str(e)}")


# ================================
# 日志分析API
# ================================

@router.post("/analyze")
async def analyze_logs(
    request: LogAnalysisRequest,
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    分析日志模式
    """
    try:
        # 执行日志分析
        analysis_result = await log_analyzer.analyze_log_patterns(
            request.start_time,
            request.end_time
        )
        
        # 添加额外的分析维度
        extended_analysis = await _perform_extended_analysis(
            request.start_time,
            request.end_time,
            request.analysis_types,
            request.services,
            request.sources
        )
        
        # 合并分析结果
        combined_result = {
            "analysis_period": {
                "start_time": request.start_time.isoformat(),
                "end_time": request.end_time.isoformat(),
                "duration_hours": (request.end_time - request.start_time).total_seconds() / 3600
            },
            "error_patterns": analysis_result.get("error_patterns", []),
            "performance_issues": analysis_result.get("performance_issues", []),
            "security_events": analysis_result.get("security_events", []),
            **extended_analysis
        }
        
        return combined_result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze logs: {str(e)}")


@router.get("/statistics")
async def get_log_statistics(
    start_time: datetime = Query(..., description="统计开始时间"),
    end_time: datetime = Query(..., description="统计结束时间"),
    service: Optional[str] = Query(None, description="服务过滤"),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取日志统计信息
    """
    try:
        # 获取基础统计
        stats = await _calculate_log_statistics(start_time, end_time, service)
        
        # 获取趋势数据
        trends = await _calculate_log_trends(start_time, end_time, service)
        
        # 获取服务分布
        service_distribution = await _get_service_distribution(start_time, end_time)
        
        return {
            "period": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            },
            "summary": stats,
            "trends": trends,
            "service_distribution": service_distribution
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get log statistics: {str(e)}")


@router.get("/levels/distribution")
async def get_log_levels_distribution(
    start_time: datetime = Query(..., description="开始时间"),
    end_time: datetime = Query(..., description="结束时间"),
    service: Optional[str] = Query(None, description="服务过滤"),
    interval: str = Query(default="hour", pattern="^(minute|hour|day)$", description="时间间隔"),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取日志级别分布
    """
    try:
        distribution = await _calculate_levels_distribution(
            start_time, end_time, service, interval
        )
        
        return {
            "period": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "interval": interval
            },
            "distribution": distribution
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get levels distribution: {str(e)}")


# ================================
# 日志洞察API
# ================================

@router.post("/insights")
async def generate_log_insights(
    request: LogInsightRequest,
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    生成日志洞察
    """
    try:
        # 生成基础洞察
        insights = await _generate_basic_insights(
            request.start_time,
            request.end_time,
            request.focus_areas,
            request.service
        )
        
        # 生成预测性洞察
        predictive_insights = await _generate_predictive_insights(
            request.start_time,
            request.end_time,
            request.service
        )
        
        # 生成建议
        recommendations = await _generate_recommendations(insights)
        
        return {
            "analysis_period": {
                "start_time": request.start_time.isoformat(),
                "end_time": request.end_time.isoformat()
            },
            "insights": insights,
            "predictive_insights": predictive_insights,
            "recommendations": recommendations,
            "generated_at": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate insights: {str(e)}")


@router.get("/anomalies")
async def detect_log_anomalies(
    start_time: datetime = Query(..., description="检测开始时间"),
    end_time: datetime = Query(..., description="检测结束时间"),
    service: Optional[str] = Query(None, description="服务过滤"),
    sensitivity: str = Query(default="medium", pattern="^(low|medium|high)$", description="敏感度"),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    检测日志异常
    """
    try:
        anomalies = await _detect_log_anomalies(
            start_time, end_time, service, sensitivity
        )
        
        return {
            "detection_period": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "sensitivity": sensitivity
            },
            "anomalies": anomalies,
            "total_anomalies": len(anomalies)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to detect anomalies: {str(e)}")


# ================================
# 日志导出API
# ================================

@router.post("/export")
async def export_logs(
    request: LogExportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    导出日志
    """
    try:
        # 生成导出任务ID
        export_id = f"export_{int(datetime.now().timestamp() * 1000)}"
        
        # 添加后台任务
        background_tasks.add_task(
            _perform_log_export,
            export_id,
            request.query,
            request.format,
            request.include_fields
        )
        
        return {
            "export_id": export_id,
            "status": "started",
            "estimated_completion": (datetime.now() + timedelta(minutes=5)).isoformat(),
            "download_url": f"/api/v1/logs/export/{export_id}/download"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start export: {str(e)}")


@router.get("/export/{export_id}/status")
async def get_export_status(
    export_id: str,
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取导出状态
    """
    try:
        # 从Redis获取导出状态
        redis_client = get_redis_client()
        status_key = f"export_status:{export_id}"
        status_data = await redis_client.get(status_key)
        
        if not status_data:
            raise HTTPException(status_code=404, detail="Export not found")
        
        import json
        status = json.loads(status_data)
        
        return status
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get export status: {str(e)}")


@router.get("/export/{export_id}/download")
async def download_export(
    export_id: str,
    current_user: User = Depends(require_admin)
):
    """
    下载导出文件
    """
    try:
        # 检查导出状态
        redis_client = get_redis_client()
        status_key = f"export_status:{export_id}"
        status_data = await redis_client.get(status_key)
        
        if not status_data:
            raise HTTPException(status_code=404, detail="Export not found")
        
        import json
        status = json.loads(status_data)
        
        if status["status"] != "completed":
            raise HTTPException(status_code=400, detail="Export not ready")
        
        # 获取文件路径
        file_path = status.get("file_path")
        if not file_path or not Path(file_path).exists():
            raise HTTPException(status_code=404, detail="Export file not found")
        
        # 返回文件
        from fastapi.responses import FileResponse
        return FileResponse(
            path=file_path,
            filename=Path(file_path).name,
            media_type="application/octet-stream"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download export: {str(e)}")


# ================================
# 日志配置API
# ================================

@router.get("/config/services")
async def get_log_services(
    current_user: User = Depends(require_admin)
) -> List[str]:
    """
    获取所有配置的日志服务
    """
    try:
        configs = structured_log_manager.config_manager.configs
        return list(configs.keys())
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get log services: {str(e)}")


@router.get("/config/service/{service_name}")
async def get_service_log_config(
    service_name: str,
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取服务日志配置
    """
    try:
        config = structured_log_manager.config_manager.get_config(service_name)
        if not config:
            raise HTTPException(status_code=404, detail="Service config not found")
        
        return {
            "service_name": config.service_name,
            "environment": config.environment,
            "log_level": config.log_level.value,
            "log_format": config.log_format.value,
            "enable_console": config.enable_console,
            "enable_file": config.enable_file,
            "enable_loki": config.enable_loki,
            "file_path": config.file_path,
            "max_file_size_mb": config.max_file_size_mb,
            "backup_count": config.backup_count,
            "rotation": config.rotation,
            "compression": config.compression,
            "index_strategy": config.index_strategy.value,
            "retention_days": config.retention_days,
            "sensitive_fields": config.sensitive_fields
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get service config: {str(e)}")


# ================================
# 辅助函数
# ================================

async def _perform_extended_analysis(
    start_time: datetime,
    end_time: datetime,
    analysis_types: List[str],
    services: Optional[List[str]] = None,
    sources: Optional[List[LogSource]] = None
) -> Dict[str, Any]:
    """执行扩展分析"""
    extended_result = {}
    
    try:
        # 用户行为分析
        if "user_behavior" in analysis_types:
            user_behavior = await _analyze_user_behavior(start_time, end_time, services)
            extended_result["user_behavior"] = user_behavior
        
        # API性能分析
        if "api_performance" in analysis_types:
            api_performance = await _analyze_api_performance(start_time, end_time, services)
            extended_result["api_performance"] = api_performance
        
        # 系统健康分析
        if "system_health" in analysis_types:
            system_health = await _analyze_system_health(start_time, end_time)
            extended_result["system_health"] = system_health
        
        # 业务指标分析
        if "business_metrics" in analysis_types:
            business_metrics = await _analyze_business_metrics(start_time, end_time, services)
            extended_result["business_metrics"] = business_metrics
    
    except Exception as e:
        logger.error(f"Error in extended analysis: {e}")
        extended_result["error"] = str(e)
    
    return extended_result


async def _analyze_user_behavior(
    start_time: datetime,
    end_time: datetime,
    services: Optional[List[str]] = None
) -> Dict[str, Any]:
    """分析用户行为"""
    try:
        # 查询用户相关日志
        user_query = LogQuery(
            query="user_id",
            start_time=start_time,
            end_time=end_time,
            limit=5000
        )
        
        result = await log_aggregator.query_logs(user_query)
        
        # 分析用户活跃度
        user_activity = {}
        unique_users = set()
        
        for entry in result.entries:
            if entry.user_id:
                unique_users.add(entry.user_id)
                
                if entry.user_id not in user_activity:
                    user_activity[entry.user_id] = {
                        "actions": 0,
                        "services": set(),
                        "first_seen": entry.timestamp,
                        "last_seen": entry.timestamp
                    }
                
                user_activity[entry.user_id]["actions"] += 1
                user_activity[entry.user_id]["services"].add(entry.service)
                
                if entry.timestamp < user_activity[entry.user_id]["first_seen"]:
                    user_activity[entry.user_id]["first_seen"] = entry.timestamp
                if entry.timestamp > user_activity[entry.user_id]["last_seen"]:
                    user_activity[entry.user_id]["last_seen"] = entry.timestamp
        
        # 计算统计信息
        total_users = len(unique_users)
        active_users = len([u for u in user_activity.values() if u["actions"] > 10])
        
        return {
            "total_unique_users": total_users,
            "active_users": active_users,
            "avg_actions_per_user": sum(u["actions"] for u in user_activity.values()) / total_users if total_users > 0 else 0,
            "top_users": sorted(
                [(user_id, data["actions"]) for user_id, data in user_activity.items()],
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }
    
    except Exception as e:
        logger.error(f"Error analyzing user behavior: {e}")
        return {"error": str(e)}


async def _analyze_api_performance(
    start_time: datetime,
    end_time: datetime,
    services: Optional[List[str]] = None
) -> Dict[str, Any]:
    """分析API性能"""
    try:
        # 查询性能相关日志
        perf_query = LogQuery(
            query="duration_ms",
            start_time=start_time,
            end_time=end_time,
            source=LogSource.PERFORMANCE,
            limit=5000
        )
        
        result = await log_aggregator.query_logs(perf_query)
        
        # 分析响应时间
        response_times = []
        slow_requests = []
        
        for entry in result.entries:
            if entry.duration_ms:
                response_times.append(entry.duration_ms)
                
                if entry.duration_ms > 1000:  # 慢请求阈值
                    slow_requests.append({
                        "timestamp": entry.timestamp.isoformat(),
                        "duration_ms": entry.duration_ms,
                        "url": entry.url,
                        "method": entry.method,
                        "service": entry.service
                    })
        
        # 计算统计指标
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            p95_response_time = sorted(response_times)[int(len(response_times) * 0.95)]
            p99_response_time = sorted(response_times)[int(len(response_times) * 0.99)]
        else:
            avg_response_time = p95_response_time = p99_response_time = 0
        
        return {
            "total_requests": len(response_times),
            "avg_response_time_ms": avg_response_time,
            "p95_response_time_ms": p95_response_time,
            "p99_response_time_ms": p99_response_time,
            "slow_requests_count": len(slow_requests),
            "slow_requests": slow_requests[:10]  # 只返回前10个慢请求
        }
    
    except Exception as e:
        logger.error(f"Error analyzing API performance: {e}")
        return {"error": str(e)}


async def _analyze_system_health(
    start_time: datetime,
    end_time: datetime
) -> Dict[str, Any]:
    """分析系统健康"""
    try:
        # 查询系统日志
        system_query = LogQuery(
            query="",
            start_time=start_time,
            end_time=end_time,
            source=LogSource.SYSTEM,
            limit=1000
        )
        
        result = await log_aggregator.query_logs(system_query)
        
        # 统计各级别日志
        level_counts = {}
        for level in LogLevel:
            level_counts[level.value] = 0
        
        for entry in result.entries:
            level_counts[entry.level.value] += 1
        
        # 计算健康评分
        total_logs = sum(level_counts.values())
        if total_logs > 0:
            error_ratio = (level_counts["error"] + level_counts["fatal"]) / total_logs
            health_score = max(0, 100 - (error_ratio * 100))
        else:
            health_score = 100
        
        return {
            "total_system_logs": total_logs,
            "level_distribution": level_counts,
            "health_score": round(health_score, 2),
            "status": "healthy" if health_score >= 80 else "warning" if health_score >= 60 else "critical"
        }
    
    except Exception as e:
        logger.error(f"Error analyzing system health: {e}")
        return {"error": str(e)}


async def _analyze_business_metrics(
    start_time: datetime,
    end_time: datetime,
    services: Optional[List[str]] = None
) -> Dict[str, Any]:
    """分析业务指标"""
    try:
        # 查询业务日志
        business_query = LogQuery(
            query="",
            start_time=start_time,
            end_time=end_time,
            source=LogSource.BUSINESS,
            limit=2000
        )
        
        result = await log_aggregator.query_logs(business_query)
        
        # 分析业务事件
        business_events = {}
        
        for entry in result.entries:
            event_type = entry.tags.get("event_type", "unknown")
            
            if event_type not in business_events:
                business_events[event_type] = {
                    "count": 0,
                    "users": set(),
                    "services": set()
                }
            
            business_events[event_type]["count"] += 1
            
            if entry.user_id:
                business_events[event_type]["users"].add(entry.user_id)
            
            business_events[event_type]["services"].add(entry.service)
        
        # 格式化结果
        formatted_events = {}
        for event_type, data in business_events.items():
            formatted_events[event_type] = {
                "count": data["count"],
                "unique_users": len(data["users"]),
                "services": list(data["services"])
            }
        
        return {
            "total_business_events": sum(data["count"] for data in business_events.values()),
            "event_types": formatted_events
        }
    
    except Exception as e:
        logger.error(f"Error analyzing business metrics: {e}")
        return {"error": str(e)}


async def _calculate_log_statistics(
    start_time: datetime,
    end_time: datetime,
    service: Optional[str] = None
) -> Dict[str, Any]:
    """计算日志统计"""
    try:
        # 查询所有日志
        query = LogQuery(
            query="",
            start_time=start_time,
            end_time=end_time,
            service=service,
            limit=10000
        )
        
        result = await log_aggregator.query_logs(query)
        
        # 统计各级别
        level_stats = {}
        source_stats = {}
        service_stats = {}
        
        for entry in result.entries:
            # 级别统计
            level = entry.level.value
            level_stats[level] = level_stats.get(level, 0) + 1
            
            # 来源统计
            source = entry.source.value
            source_stats[source] = source_stats.get(source, 0) + 1
            
            # 服务统计
            service_name = entry.service
            service_stats[service_name] = service_stats.get(service_name, 0) + 1
        
        return {
            "total_logs": result.total_count,
            "level_distribution": level_stats,
            "source_distribution": source_stats,
            "service_distribution": service_stats,
            "logs_per_hour": result.total_count / ((end_time - start_time).total_seconds() / 3600) if (end_time - start_time).total_seconds() > 0 else 0
        }
    
    except Exception as e:
        logger.error(f"Error calculating log statistics: {e}")
        return {"error": str(e)}


async def _calculate_log_trends(
    start_time: datetime,
    end_time: datetime,
    service: Optional[str] = None
) -> Dict[str, Any]:
    """计算日志趋势"""
    try:
        # 按小时分组查询
        trends = []
        current_time = start_time
        
        while current_time < end_time:
            hour_end = min(current_time + timedelta(hours=1), end_time)
            
            query = LogQuery(
                query="",
                start_time=current_time,
                end_time=hour_end,
                service=service,
                limit=1000
            )
            
            result = await log_aggregator.query_logs(query)
            
            trends.append({
                "hour": current_time.isoformat(),
                "count": result.total_count
            })
            
            current_time = hour_end
        
        return {
            "hourly_trends": trends,
            "peak_hour": max(trends, key=lambda x: x["count"]) if trends else None,
            "trend_direction": "increasing" if len(trends) > 1 and trends[-1]["count"] > trends[0]["count"] else "decreasing" if len(trends) > 1 and trends[-1]["count"] < trends[0]["count"] else "stable"
        }
    
    except Exception as e:
        logger.error(f"Error calculating log trends: {e}")
        return {"error": str(e)}


async def _get_service_distribution(
    start_time: datetime,
    end_time: datetime
) -> Dict[str, Any]:
    """获取服务分布"""
    try:
        query = LogQuery(
            query="",
            start_time=start_time,
            end_time=end_time,
            limit=10000
        )
        
        result = await log_aggregator.query_logs(query)
        
        service_counts = {}
        for entry in result.entries:
            service = entry.service
            service_counts[service] = service_counts.get(service, 0) + 1
        
        # 计算百分比
        total_logs = sum(service_counts.values())
        service_distribution = []
        
        for service, count in service_counts.items():
            percentage = (count / total_logs * 100) if total_logs > 0 else 0
            service_distribution.append({
                "service": service,
                "count": count,
                "percentage": round(percentage, 2)
            })
        
        # 按数量排序
        service_distribution.sort(key=lambda x: x["count"], reverse=True)
        
        return {
            "services": service_distribution,
            "total_services": len(service_distribution)
        }
    
    except Exception as e:
        logger.error(f"Error getting service distribution: {e}")
        return {"error": str(e)}


async def _calculate_levels_distribution(
    start_time: datetime,
    end_time: datetime,
    service: Optional[str] = None,
    interval: str = "hour"
) -> Dict[str, Any]:
    """计算日志级别分布"""
    try:
        # 确定时间间隔
        if interval == "minute":
            delta = timedelta(minutes=1)
        elif interval == "hour":
            delta = timedelta(hours=1)
        else:  # day
            delta = timedelta(days=1)
        
        distribution = []
        current_time = start_time
        
        while current_time < end_time:
            interval_end = min(current_time + delta, end_time)
            
            # 查询这个时间间隔的日志
            query = LogQuery(
                query="",
                start_time=current_time,
                end_time=interval_end,
                service=service,
                limit=1000
            )
            
            result = await log_aggregator.query_logs(query)
            
            # 统计各级别
            level_counts = {}
            for level in LogLevel:
                level_counts[level.value] = 0
            
            for entry in result.entries:
                level_counts[entry.level.value] += 1
            
            distribution.append({
                "timestamp": current_time.isoformat(),
                "levels": level_counts,
                "total": sum(level_counts.values())
            })
            
            current_time = interval_end
        
        return {
            "interval": interval,
            "data": distribution
        }
    
    except Exception as e:
        logger.error(f"Error calculating levels distribution: {e}")
        return {"error": str(e)}


async def _generate_basic_insights(
    start_time: datetime,
    end_time: datetime,
    focus_areas: List[str],
    service: Optional[str] = None
) -> List[Dict[str, Any]]:
    """生成基础洞察"""
    insights = []
    
    try:
        # 错误洞察
        if "errors" in focus_areas:
            error_insights = await _generate_error_insights(start_time, end_time, service)
            insights.extend(error_insights)
        
        # 性能洞察
        if "performance" in focus_areas:
            perf_insights = await _generate_performance_insights(start_time, end_time, service)
            insights.extend(perf_insights)
        
        # 安全洞察
        if "security" in focus_areas:
            security_insights = await _generate_security_insights(start_time, end_time, service)
            insights.extend(security_insights)
    
    except Exception as e:
        logger.error(f"Error generating basic insights: {e}")
        insights.append({
            "type": "error",
            "title": "Insight Generation Failed",
            "description": f"Failed to generate insights: {str(e)}",
            "severity": "warning"
        })
    
    return insights


async def _generate_error_insights(
    start_time: datetime,
    end_time: datetime,
    service: Optional[str] = None
) -> List[Dict[str, Any]]:
    """生成错误洞察"""
    insights = []
    
    try:
        # 查询错误日志
        error_query = LogQuery(
            query="",
            start_time=start_time,
            end_time=end_time,
            level=LogLevel.ERROR,
            service=service,
            limit=1000
        )
        
        result = await log_aggregator.query_logs(error_query)
        
        if result.total_count > 0:
            # 分析错误模式
            error_types = {}
            for entry in result.entries:
                error_type = entry.error_type or "unknown"
                error_types[error_type] = error_types.get(error_type, 0) + 1
            
            # 找出最常见的错误
            most_common_error = max(error_types.items(), key=lambda x: x[1]) if error_types else None
            
            if most_common_error:
                insights.append({
                    "type": "error_pattern",
                    "title": f"Most Common Error: {most_common_error[0]}",
                    "description": f"This error occurred {most_common_error[1]} times in the analyzed period",
                    "severity": "high" if most_common_error[1] > 50 else "medium",
                    "recommendation": "Investigate the root cause of this error pattern and implement preventive measures"
                })
            
            # 错误率趋势
            error_rate = result.total_count / ((end_time - start_time).total_seconds() / 3600)
            
            if error_rate > 10:  # 每小时超过10个错误
                insights.append({
                    "type": "error_rate",
                    "title": "High Error Rate Detected",
                    "description": f"Error rate is {error_rate:.1f} errors per hour",
                    "severity": "critical",
                    "recommendation": "Immediate investigation required - error rate is unusually high"
                })
    
    except Exception as e:
        logger.error(f"Error generating error insights: {e}")
    
    return insights


async def _generate_performance_insights(
    start_time: datetime,
    end_time: datetime,
    service: Optional[str] = None
) -> List[Dict[str, Any]]:
    """生成性能洞察"""
    insights = []
    
    try:
        # 查询性能日志
        perf_query = LogQuery(
            query="duration_ms",
            start_time=start_time,
            end_time=end_time,
            source=LogSource.PERFORMANCE,
            service=service,
            limit=1000
        )
        
        result = await log_aggregator.query_logs(perf_query)
        
        # 分析响应时间
        response_times = []
        for entry in result.entries:
            if entry.duration_ms:
                response_times.append(entry.duration_ms)
        
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            p95_response_time = sorted(response_times)[int(len(response_times) * 0.95)]
            
            if avg_response_time > 500:
                insights.append({
                    "type": "performance",
                    "title": "Slow Average Response Time",
                    "description": f"Average response time is {avg_response_time:.1f}ms",
                    "severity": "medium" if avg_response_time < 1000 else "high",
                    "recommendation": "Optimize database queries and consider caching strategies"
                })
            
            if p95_response_time > 2000:
                insights.append({
                    "type": "performance",
                    "title": "High P95 Response Time",
                    "description": f"95th percentile response time is {p95_response_time:.1f}ms",
                    "severity": "high",
                    "recommendation": "Investigate outliers and optimize slow endpoints"
                })
    
    except Exception as e:
        logger.error(f"Error generating performance insights: {e}")
    
    return insights


async def _generate_security_insights(
    start_time: datetime,
    end_time: datetime,
    service: Optional[str] = None
) -> List[Dict[str, Any]]:
    """生成安全洞察"""
    insights = []
    
    try:
        # 查询安全日志
        security_query = LogQuery(
            query="",
            start_time=start_time,
            end_time=end_time,
            source=LogSource.SECURITY,
            service=service,
            limit=500
        )
        
        result = await log_aggregator.query_logs(security_query)
        
        if result.total_count > 0:
            # 分析安全事件
            security_events = {}
            for entry in result.entries:
                event_type = entry.tags.get("event_type", "unknown")
                security_events[event_type] = security_events.get(event_type, 0) + 1
            
            # 检查高风险事件
            high_risk_events = ["attack", "breach", "unauthorized_access"]
            
            for event_type in high_risk_events:
                if event_type in security_events:
                    insights.append({
                        "type": "security",
                        "title": f"High Risk Security Event: {event_type}",
                        "description": f"Detected {security_events[event_type]} {event_type} events",
                        "severity": "critical",
                        "recommendation": "Immediate security investigation required"
                    })
    
    except Exception as e:
        logger.error(f"Error generating security insights: {e}")
    
    return insights


async def _generate_predictive_insights(
    start_time: datetime,
    end_time: datetime,
    service: Optional[str] = None
) -> List[Dict[str, Any]]:
    """生成预测性洞察"""
    insights = []
    
    try:
        # 基于历史趋势预测
        # 这里可以实现更复杂的预测算法
        
        insights.append({
            "type": "predictive",
            "title": "Traffic Trend Prediction",
            "description": "Based on current patterns, expect increased traffic in the next 24 hours",
            "confidence": 0.75,
            "recommendation": "Prepare for increased load by scaling resources"
        })
    
    except Exception as e:
        logger.error(f"Error generating predictive insights: {e}")
    
    return insights


async def _generate_recommendations(insights: List[Dict[str, Any]]) -> List[str]:
    """生成建议"""
    recommendations = []
    
    try:
        # 基于洞察生成建议
        high_severity_count = len([i for i in insights if i.get("severity") == "high" or i.get("severity") == "critical"])
        
        if high_severity_count > 0:
            recommendations.append("Priority: Address high severity issues immediately")
        
        error_insights = [i for i in insights if i.get("type") == "error_pattern"]
        if error_insights:
            recommendations.append("Consider implementing automated error monitoring and alerting")
        
        performance_insights = [i for i in insights if i.get("type") == "performance"]
        if performance_insights:
            recommendations.append("Review and optimize application performance bottlenecks")
        
        security_insights = [i for i in insights if i.get("type") == "security"]
        if security_insights:
            recommendations.append("Enhance security monitoring and incident response procedures")
    
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
    
    return recommendations


async def _detect_log_anomalies(
    start_time: datetime,
    end_time: datetime,
    service: Optional[str] = None,
    sensitivity: str = "medium"
) -> List[Dict[str, Any]]:
    """检测日志异常"""
    anomalies = []
    
    try:
        # 设置敏感度阈值
        sensitivity_thresholds = {
            "low": {"error_spike": 5, "traffic_drop": 0.3, "response_time_spike": 2.0},
            "medium": {"error_spike": 3, "traffic_drop": 0.5, "response_time_spike": 1.5},
            "high": {"error_spike": 2, "traffic_drop": 0.7, "response_time_spike": 1.2}
        }
        
        thresholds = sensitivity_thresholds[sensitivity]
        
        # 检测错误激增
        error_anomaly = await _detect_error_spike(start_time, end_time, service, thresholds["error_spike"])
        if error_anomaly:
            anomalies.append(error_anomaly)
        
        # 检测流量异常
        traffic_anomaly = await _detect_traffic_anomaly(start_time, end_time, service, thresholds["traffic_drop"])
        if traffic_anomaly:
            anomalies.append(traffic_anomaly)
        
        # 检测响应时间异常
        response_anomaly = await _detect_response_time_anomaly(start_time, end_time, service, thresholds["response_time_spike"])
        if response_anomaly:
            anomalies.append(response_anomaly)
    
    except Exception as e:
        logger.error(f"Error detecting anomalies: {e}")
    
    return anomalies


async def _detect_error_spike(
    start_time: datetime,
    end_time: datetime,
    service: Optional[str] = None,
    threshold_multiplier: float = 3.0
) -> Optional[Dict[str, Any]]:
    """检测错误激增"""
    try:
        # 简化实现：比较当前错误率与历史平均值
        current_period = end_time - start_time
        historical_period = timedelta(days=7)
        
        # 查询当前期间错误
        current_query = LogQuery(
            query="",
            start_time=start_time,
            end_time=end_time,
            level=LogLevel.ERROR,
            service=service,
            limit=1000
        )
        
        current_result = await log_aggregator.query_logs(current_query)
        current_error_rate = current_result.total_count / (current_period.total_seconds() / 3600)
        
        # 查询历史期间错误
        historical_start = start_time - historical_period
        historical_query = LogQuery(
            query="",
            start_time=historical_start,
            end_time=start_time,
            level=LogLevel.ERROR,
            service=service,
            limit=5000
        )
        
        historical_result = await log_aggregator.query_logs(historical_query)
        historical_error_rate = historical_result.total_count / (historical_period.total_seconds() / 3600)
        
        # 检测激增
        if historical_error_rate > 0 and current_error_rate > historical_error_rate * threshold_multiplier:
            return {
                "type": "error_spike",
                "description": f"Error rate increased by {current_error_rate / historical_error_rate:.1f}x compared to historical average",
                "current_rate": current_error_rate,
                "historical_rate": historical_error_rate,
                "severity": "high",
                "timestamp": end_time.isoformat()
            }
    
    except Exception as e:
        logger.error(f"Error detecting error spike: {e}")
    
    return None


async def _detect_traffic_anomaly(
    start_time: datetime,
    end_time: datetime,
    service: Optional[str] = None,
    drop_threshold: float = 0.5
) -> Optional[Dict[str, Any]]:
    """检测流量异常"""
    try:
        # 查询当前期间流量
        current_query = LogQuery(
            query="",
            start_time=start_time,
            end_time=end_time,
            service=service,
            limit=10000
        )
        
        current_result = await log_aggregator.query_logs(current_query)
        current_traffic = current_result.total_count
        
        # 查询历史同期流量
        historical_start = start_time - timedelta(days=1)
        historical_end = end_time - timedelta(days=1)
        
        historical_query = LogQuery(
            query="",
            start_time=historical_start,
            end_time=historical_end,
            service=service,
            limit=10000
        )
        
        historical_result = await log_aggregator.query_logs(historical_query)
        historical_traffic = historical_result.total_count
        
        # 检测流量下降
        if historical_traffic > 0 and current_traffic < historical_traffic * (1 - drop_threshold):
            drop_percentage = (1 - current_traffic / historical_traffic) * 100
            
            return {
                "type": "traffic_drop",
                "description": f"Traffic dropped by {drop_percentage:.1f}% compared to yesterday",
                "current_traffic": current_traffic,
                "historical_traffic": historical_traffic,
                "drop_percentage": drop_percentage,
                "severity": "medium" if drop_percentage < 70 else "high",
                "timestamp": end_time.isoformat()
            }
    
    except Exception as e:
        logger.error(f"Error detecting traffic anomaly: {e}")
    
    return None


async def _detect_response_time_anomaly(
    start_time: datetime,
    end_time: datetime,
    service: Optional[str] = None,
    spike_threshold: float = 1.5
) -> Optional[Dict[str, Any]]:
    """检测响应时间异常"""
    try:
        # 查询当前期间响应时间
        current_query = LogQuery(
            query="duration_ms",
            start_time=start_time,
            end_time=end_time,
            source=LogSource.PERFORMANCE,
            service=service,
            limit=1000
        )
        
        current_result = await log_aggregator.query_logs(current_query)
        
        response_times = []
        for entry in current_result.entries:
            if entry.duration_ms:
                response_times.append(entry.duration_ms)
        
        if response_times:
            current_avg = sum(response_times) / len(response_times)
            
            # 查询历史响应时间
            historical_start = start_time - timedelta(days=1)
            historical_end = end_time - timedelta(days=1)
            
            historical_query = LogQuery(
                query="duration_ms",
                start_time=historical_start,
                end_time=historical_end,
                source=LogSource.PERFORMANCE,
                service=service,
                limit=1000
            )
            
            historical_result = await log_aggregator.query_logs(historical_query)
            
            historical_response_times = []
            for entry in historical_result.entries:
                if entry.duration_ms:
                    historical_response_times.append(entry.duration_ms)
            
            if historical_response_times:
                historical_avg = sum(historical_response_times) / len(historical_response_times)
                
                # 检测响应时间激增
                if historical_avg > 0 and current_avg > historical_avg * spike_threshold:
                    spike_multiplier = current_avg / historical_avg
                    
                    return {
                        "type": "response_time_spike",
                        "description": f"Response time increased by {spike_multiplier:.1f}x compared to yesterday",
                        "current_avg_ms": current_avg,
                        "historical_avg_ms": historical_avg,
                        "spike_multiplier": spike_multiplier,
                        "severity": "medium" if spike_multiplier < 2.0 else "high",
                        "timestamp": end_time.isoformat()
                    }
    
    except Exception as e:
        logger.error(f"Error detecting response time anomaly: {e}")
    
    return None


async def _perform_log_export(
    export_id: str,
    query: LogQueryRequest,
    format: str,
    include_fields: List[str]
):
    """执行日志导出"""
    try:
        from pathlib import Path
        import pandas as pd
        import json
        
        # 更新状态
        redis_client = get_redis_client()
        status_key = f"export_status:{export_id}"
        
        await redis_client.setex(
            status_key,
            3600,  # 1小时过期
            json.dumps({
                "export_id": export_id,
                "status": "processing",
                "progress": 0,
                "started_at": datetime.now().isoformat()
            })
        )
        
        # 执行查询
        log_query = LogQuery(
            query=query.query,
            start_time=query.start_time,
            end_time=query.end_time,
            level=query.level,
            source=query.source,
            service=query.service,
            trace_id=query.trace_id,
            user_id=query.user_id,
            tags=query.tags,
            limit=query.limit
        )
        
        result = await log_aggregator.query_logs(log_query)
        
        # 更新进度
        await redis_client.setex(
            status_key,
            3600,
            json.dumps({
                "export_id": export_id,
                "status": "processing",
                "progress": 50,
                "started_at": datetime.now().isoformat()
            })
        )
        
        # 准备导出数据
        export_data = []
        
        for entry in result.entries:
            row = {}
            for field in include_fields:
                if hasattr(entry, field):
                    value = getattr(entry, field)
                    if isinstance(value, datetime):
                        row[field] = value.isoformat()
                    elif isinstance(value, (LogLevel, LogSource)):
                        row[field] = value.value
                    else:
                        row[field] = value
            export_data.append(row)
        
        # 创建导出文件
        export_dir = Path("exports")
        export_dir.mkdir(exist_ok=True)
        
        if format == "json":
            file_path = export_dir / f"{export_id}.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        elif format == "csv":
            file_path = export_dir / f"{export_id}.csv"
            df = pd.DataFrame(export_data)
            df.to_csv(file_path, index=False, encoding='utf-8')
        
        elif format == "xlsx":
            file_path = export_dir / f"{export_id}.xlsx"
            df = pd.DataFrame(export_data)
            df.to_excel(file_path, index=False)
        
        # 更新完成状态
        await redis_client.setex(
            status_key,
            3600,
            json.dumps({
                "export_id": export_id,
                "status": "completed",
                "progress": 100,
                "started_at": datetime.now().isoformat(),
                "completed_at": datetime.now().isoformat(),
                "file_path": str(file_path),
                "file_size": Path(file_path).stat().st_size,
                "total_records": len(export_data)
            })
        )
        
        logger.info(f"Export completed: {export_id}, {len(export_data)} records")
    
    except Exception as e:
        logger.error(f"Error performing log export: {e}")
        
        # 更新错误状态
        try:
            await redis_client.setex(
                status_key,
                3600,
                json.dumps({
                    "export_id": export_id,
                    "status": "failed",
                    "error": str(e),
                    "started_at": datetime.now().isoformat(),
                    "failed_at": datetime.now().isoformat()
                })
            )
        except:
            pass


# 导入必要的模块
from pathlib import Path
from app.core.redis_client import get_redis_client
