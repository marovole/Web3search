"""
基础设施监控API
提供服务器资源监控的REST API接口
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from app.core.infrastructure_monitor import (
    resource_monitor, ResourceType, AlertLevel,
    ResourceMetric, SystemInfo
)
from app.core.config import settings
from app.api.deps import get_current_user, require_admin
from app.models.user import User

router = APIRouter(prefix="/infrastructure", tags=["Infrastructure Monitoring"])


# ================================
# Pydantic模型定义
# ================================

class ResourceMetricResponse(BaseModel):
    """资源指标响应"""
    timestamp: str
    resource_type: str
    metric_name: str
    value: float
    unit: str
    status: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    threshold_warning: float = 0.0
    threshold_critical: float = 0.0


class SystemInfoResponse(BaseModel):
    """系统信息响应"""
    hostname: str
    platform: str
    platform_version: str
    architecture: str
    cpu_count: int
    cpu_freq: float
    total_memory: int
    boot_time: str
    uptime_hours: float


class ResourceSummaryResponse(BaseModel):
    """资源摘要响应"""
    timestamp: str
    system_info: SystemInfoResponse
    resources: Dict[str, Dict[str, Any]]
    alerts: Dict[str, int]


class MetricHistoryRequest(BaseModel):
    """指标历史请求"""
    resource_type: ResourceType = Field(..., description="资源类型")
    metric_name: str = Field(..., description="指标名称")
    start_time: datetime = Field(..., description="开始时间")
    end_time: datetime = Field(..., description="结束时间")


# ================================
# 基础监控API
# ================================

@router.get("/metrics/current")
async def get_current_metrics(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取当前所有资源指标
    """
    try:
        current_metrics = await resource_monitor.get_current_metrics()
        
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
        raise HTTPException(status_code=500, detail=f"Failed to get current metrics: {str(e)}")


@router.get("/metrics/summary")
async def get_resource_summary(
    current_user: User = Depends(require_admin)
) -> ResourceSummaryResponse:
    """
    获取资源使用摘要
    """
    try:
        summary = await resource_monitor.get_resource_summary()
        
        # 转换系统信息格式
        system_info = SystemInfoResponse(
            hostname=summary["system_info"]["hostname"],
            platform=summary["system_info"]["platform"],
            platform_version=summary["system_info"]["platform_version"],
            architecture=summary["system_info"]["architecture"],
            cpu_count=summary["system_info"]["cpu_count"],
            cpu_freq=summary["system_info"]["cpu_freq"],
            total_memory=summary["system_info"]["total_memory"],
            boot_time=summary["system_info"]["boot_time"],
            uptime_hours=summary["system_info"]["uptime_hours"]
        )
        
        return ResourceSummaryResponse(
            timestamp=summary["timestamp"],
            system_info=system_info,
            resources=summary["resources"],
            alerts=summary["alerts"]
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get resource summary: {str(e)}")


@router.get("/system/info")
async def get_system_info(
    current_user: User = Depends(require_admin)
) -> SystemInfoResponse:
    """
    获取系统信息
    """
    try:
        system_info = await resource_monitor.get_system_info()
        
        return SystemInfoResponse(
            hostname=system_info.hostname,
            platform=system_info.platform,
            platform_version=system_info.platform_version,
            architecture=system_info.architecture,
            cpu_count=system_info.cpu_count,
            cpu_freq=system_info.cpu_freq,
            total_memory=system_info.total_memory,
            boot_time=system_info.boot_time.isoformat(),
            uptime_hours=system_info.uptime.total_seconds() / 3600
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system info: {str(e)}")


# ================================
# CPU监控API
# ================================

@router.get("/cpu/usage")
async def get_cpu_usage(
    hours: int = Query(default=1, ge=1, le=24, description="查询时间范围（小时）"),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取CPU使用率历史数据
    """
    try:
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        # 获取CPU使用率历史
        history = await resource_monitor.get_metric_history(
            ResourceType.CPU,
            "cpu_usage_percent",
            start_time,
            end_time
        )
        
        # 获取当前CPU使用率
        current_metrics = await resource_monitor.get_current_metrics()
        current_cpu = current_metrics.get("cpu_usage_percent", {})
        
        return {
            "current": {
                "value": current_cpu.get("value", 0),
                "unit": current_cpu.get("unit", "percent"),
                "status": current_cpu.get("status", "normal"),
                "timestamp": current_cpu.get("timestamp", datetime.now().isoformat())
            },
            "history": history,
            "period": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "hours": hours
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get CPU usage: {str(e)}")


@router.get("/cpu/cores")
async def get_cpu_cores_usage(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取各CPU核心使用率
    """
    try:
        current_metrics = await resource_monitor.get_current_metrics()
        
        core_metrics = {}
        for metric_name, data in current_metrics.items():
            if metric_name.startswith("cpu_core_") and metric_name.endswith("_usage_percent"):
                core_id = metric_name.split("_")[2]
                core_metrics[f"core_{core_id}"] = {
                    "value": data["value"],
                    "unit": data["unit"],
                    "status": data["status"],
                    "timestamp": data["timestamp"]
                }
        
        return {
            "cores": core_metrics,
            "total_cores": len(core_metrics),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get CPU cores usage: {str(e)}")


@router.get("/cpu/load")
async def get_cpu_load(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取CPU负载
    """
    try:
        current_metrics = await resource_monitor.get_current_metrics()
        
        load_metrics = {}
        for metric_name in ["cpu_load_1min", "cpu_load_5min", "cpu_load_15min"]:
            if metric_name in current_metrics:
                data = current_metrics[metric_name]
                load_metrics[metric_name] = {
                    "value": data["value"],
                    "unit": data["unit"],
                    "timestamp": data["timestamp"]
                }
        
        return {
            "load": load_metrics,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get CPU load: {str(e)}")


# ================================
# 内存监控API
# ================================

@router.get("/memory/usage")
async def get_memory_usage(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取内存使用情况
    """
    try:
        current_metrics = await resource_monitor.get_current_metrics()
        
        memory_metrics = {}
        for metric_name in ["memory_usage_percent", "memory_used_gb", "memory_available_gb"]:
            if metric_name in current_metrics:
                data = current_metrics[metric_name]
                memory_metrics[metric_name] = {
                    "value": data["value"],
                    "unit": data["unit"],
                    "status": data.get("status", "normal"),
                    "timestamp": data["timestamp"],
                    "metadata": data.get("metadata", {})
                }
        
        # 交换内存
        swap_metrics = {}
        for metric_name, data in current_metrics.items():
            if metric_name.startswith("swap_"):
                swap_metrics[metric_name] = {
                    "value": data["value"],
                    "unit": data["unit"],
                    "status": data.get("status", "normal"),
                    "timestamp": data["timestamp"],
                    "metadata": data.get("metadata", {})
                }
        
        return {
            "memory": memory_metrics,
            "swap": swap_metrics,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get memory usage: {str(e)}")


@router.get("/memory/history")
async def get_memory_history(
    hours: int = Query(default=1, ge=1, le=24, description="查询时间范围（小时）"),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取内存使用率历史数据
    """
    try:
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        history = await resource_monitor.get_metric_history(
            ResourceType.MEMORY,
            "memory_usage_percent",
            start_time,
            end_time
        )
        
        return {
            "history": history,
            "period": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "hours": hours
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get memory history: {str(e)}")


# ================================
# 磁盘监控API
# ================================

@router.get("/disk/usage")
async def get_disk_usage(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取磁盘使用情况
    """
    try:
        current_metrics = await resource_monitor.get_current_metrics()
        
        disk_metrics = {}
        for metric_name, data in current_metrics.items():
            if metric_name.startswith("disk_"):
                disk_metrics[metric_name] = {
                    "value": data["value"],
                    "unit": data["unit"],
                    "status": data.get("status", "normal"),
                    "timestamp": data["timestamp"],
                    "metadata": data.get("metadata", {})
                }
        
        # 按设备分组
        devices = {}
        for metric_name, data in disk_metrics.items():
            if "usage_percent" in metric_name:
                device = data["metadata"].get("device", "unknown")
                if device not in devices:
                    devices[device] = {}
                devices[device]["usage_percent"] = data
            elif "free_gb" in metric_name:
                device = data["metadata"].get("device", "unknown")
                if device not in devices:
                    devices[device] = {}
                devices[device]["free_gb"] = data
        
        return {
            "devices": devices,
            "all_metrics": disk_metrics,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get disk usage: {str(e)}")


@router.get("/disk/io")
async def get_disk_io(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取磁盘I/O统计
    """
    try:
        current_metrics = await resource_monitor.get_current_metrics()
        
        io_metrics = {}
        for metric_name in ["disk_read_bytes_per_sec", "disk_write_bytes_per_sec"]:
            if metric_name in current_metrics:
                data = current_metrics[metric_name]
                io_metrics[metric_name] = {
                    "value": data["value"],
                    "unit": data["unit"],
                    "timestamp": data["timestamp"],
                    "metadata": data.get("metadata", {})
                }
        
        return {
            "io": io_metrics,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get disk I/O: {str(e)}")


# ================================
# 网络监控API
# ================================

@router.get("/network/usage")
async def get_network_usage(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取网络使用情况
    """
    try:
        current_metrics = await resource_monitor.get_current_metrics()
        
        network_metrics = {}
        for metric_name, data in current_metrics.items():
            if metric_name.startswith("network_"):
                network_metrics[metric_name] = {
                    "value": data["value"],
                    "unit": data["unit"],
                    "status": data.get("status", "normal"),
                    "timestamp": data["timestamp"],
                    "metadata": data.get("metadata", {})
                }
        
        return {
            "network": network_metrics,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get network usage: {str(e)}")


@router.get("/network/connections")
async def get_network_connections(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取网络连接统计
    """
    try:
        current_metrics = await resource_monitor.get_current_metrics()
        
        connections_metric = current_metrics.get("network_active_connections", {})
        
        return {
            "active_connections": {
                "value": connections_metric.get("value", 0),
                "unit": connections_metric.get("unit", "count"),
                "status": connections_metric.get("status", "normal"),
                "timestamp": connections_metric.get("timestamp", datetime.now().isoformat()),
                "metadata": connections_metric.get("metadata", {})
            },
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get network connections: {str(e)}")


# ================================
# 系统监控API
# ================================

@router.get("/system/processes")
async def get_system_processes(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取系统进程统计
    """
    try:
        current_metrics = await resource_monitor.get_current_metrics()
        
        process_metric = current_metrics.get("system_process_count", {})
        uptime_metric = current_metrics.get("system_uptime_hours", {})
        
        return {
            "process_count": {
                "value": process_metric.get("value", 0),
                "unit": process_metric.get("unit", "count"),
                "status": process_metric.get("status", "normal"),
                "timestamp": process_metric.get("timestamp", datetime.now().isoformat())
            },
            "uptime": {
                "value": uptime_metric.get("value", 0),
                "unit": uptime_metric.get("unit", "hours"),
                "timestamp": uptime_metric.get("timestamp", datetime.now().isoformat()),
                "metadata": uptime_metric.get("metadata", {})
            },
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system processes: {str(e)}")


@router.get("/system/app")
async def get_app_metrics(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取应用程序资源使用情况
    """
    try:
        current_metrics = await resource_monitor.get_current_metrics()
        
        app_metrics = {}
        for metric_name in ["app_cpu_usage_percent", "app_memory_usage_mb"]:
            if metric_name in current_metrics:
                data = current_metrics[metric_name]
                app_metrics[metric_name] = {
                    "value": data["value"],
                    "unit": data["unit"],
                    "status": data.get("status", "normal"),
                    "timestamp": data["timestamp"],
                    "metadata": data.get("metadata", {})
                }
        
        return {
            "application": app_metrics,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get app metrics: {str(e)}")


# ================================
# 告警和状态API
# ================================

@router.get("/alerts")
async def get_infrastructure_alerts(
    status: Optional[str] = Query(None, pattern="^(active|resolved|all)$", description="告警状态过滤"),
    severity: Optional[str] = Query(None, pattern="^(warning|critical|all)$", description="严重程度过滤"),
    limit: int = Query(default=50, ge=1, le=100, description="返回数量限制"),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取基础设施告警
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
            service="web3search",
            limit=limit
        )
        
        # 过滤基础设施相关告警
        infrastructure_alerts = []
        for alert in alerts:
            if alert.source == "infrastructure_monitor":
                infrastructure_alerts.append({
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
            "alerts": infrastructure_alerts,
            "total_count": len(infrastructure_alerts),
            "filters": {
                "status": status,
                "severity": severity
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get infrastructure alerts: {str(e)}")


@router.get("/health")
async def get_infrastructure_health(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取基础设施健康状态
    """
    try:
        summary = await resource_monitor.get_resource_summary()
        
        # 计算健康评分
        total_metrics = 0
        warning_metrics = 0
        critical_metrics = 0
        
        for resource_data in summary["resources"].values():
            for metric_data in resource_data.values():
                total_metrics += 1
                if metric_data.get("status") == "warning":
                    warning_metrics += 1
                elif metric_data.get("status") == "critical":
                    critical_metrics += 1
        
        # 健康评分计算
        if total_metrics > 0:
            health_score = max(0, 100 - (warning_metrics * 10) - (critical_metrics * 25))
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
        
        return {
            "health_score": round(health_score, 2),
            "health_status": health_status,
            "total_metrics": total_metrics,
            "warning_metrics": warning_metrics,
            "critical_metrics": critical_metrics,
            "active_alerts": summary["alerts"]["warning"] + summary["alerts"]["critical"],
            "timestamp": datetime.now().isoformat(),
            "recommendations": _generate_health_recommendations(health_status, summary)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get infrastructure health: {str(e)}")


# ================================
# 历史数据API
# ================================

@router.post("/metrics/history")
async def get_metric_history(
    request: MetricHistoryRequest,
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取指标历史数据
    """
    try:
        history = await resource_monitor.get_metric_history(
            request.resource_type,
            request.metric_name,
            request.start_time,
            request.end_time
        )
        
        return {
            "resource_type": request.resource_type.value,
            "metric_name": request.metric_name,
            "history": history,
            "period": {
                "start_time": request.start_time.isoformat(),
                "end_time": request.end_time.isoformat()
            },
            "total_points": len(history)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metric history: {str(e)}")


@router.get("/metrics/trends")
async def get_resource_trends(
    hours: int = Query(default=24, ge=1, le=168, description="分析时间范围（小时）"),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取资源使用趋势
    """
    try:
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        # 获取主要指标的历史数据
        key_metrics = [
            (ResourceType.CPU, "cpu_usage_percent"),
            (ResourceType.MEMORY, "memory_usage_percent"),
            (ResourceType.NETWORK, "network_mbps_sent"),
            (ResourceType.NETWORK, "network_mbps_recv")
        ]
        
        trends = {}
        
        for resource_type, metric_name in key_metrics:
            history = await resource_monitor.get_metric_history(
                resource_type,
                metric_name,
                start_time,
                end_time
            )
            
            if history:
                # 计算趋势统计
                values = [point["value"] for point in history]
                avg_value = sum(values) / len(values)
                max_value = max(values)
                min_value = min(values)
                
                # 简单趋势分析
                if len(values) >= 2:
                    recent_avg = sum(values[-10:]) / min(10, len(values))
                    early_avg = sum(values[:10]) / min(10, len(values))
                    
                    if recent_avg > early_avg * 1.1:
                        trend_direction = "increasing"
                    elif recent_avg < early_avg * 0.9:
                        trend_direction = "decreasing"
                    else:
                        trend_direction = "stable"
                else:
                    trend_direction = "unknown"
                
                trends[f"{resource_type.value}_{metric_name}"] = {
                    "avg": round(avg_value, 2),
                    "max": round(max_value, 2),
                    "min": round(min_value, 2),
                    "trend": trend_direction,
                    "data_points": len(history)
                }
        
        return {
            "trends": trends,
            "period": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "hours": hours
            },
            "generated_at": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get resource trends: {str(e)}")


# ================================
# 辅助函数
# ================================

def _generate_health_recommendations(health_status: str, summary: Dict[str, Any]) -> List[str]:
    """生成健康建议"""
    recommendations = []
    
    try:
        if health_status == "critical":
            recommendations.append("立即检查系统资源使用情况，可能存在严重性能问题")
            recommendations.append("考虑重启服务或扩容资源")
        elif health_status == "warning":
            recommendations.append("监控系统资源使用趋势，准备优化措施")
            
            # 检查具体问题
            for resource_type, metrics in summary["resources"].items():
                for metric_name, metric_data in metrics.items():
                    if metric_data.get("status") == "critical":
                        recommendations.append(f"紧急处理 {resource_type} 资源问题: {metric_name}")
                    elif metric_data.get("status") == "warning":
                        recommendations.append(f"关注 {resource_type} 资源使用: {metric_name}")
        elif health_status == "good":
            recommendations.append("系统运行良好，继续保持监控")
        elif health_status == "excellent":
            recommendations.append("系统运行状态优秀，考虑优化资源配置以降低成本")
        
        # 通用建议
        if summary["alerts"]["critical"] > 0:
            recommendations.append("存在严重告警，需要立即处理")
        
        if summary["alerts"]["warning"] > 5:
            recommendations.append("警告告警较多，建议进行系统优化")
    
    except Exception as e:
        recommendations.append(f"生成建议时出错: {str(e)}")
    
    return recommendations
