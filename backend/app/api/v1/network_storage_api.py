"""
网络和存储监控API
提供网络和存储监控的REST API接口
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import json

from app.core.network_storage_monitor import (
    network_storage_monitor, NetworkMetricType, StorageMetricType,
    NetworkMetric, StorageMetric, NetworkInterface, StorageDevice
)
from app.core.config import settings
from app.core.alerting_system import alert_manager, AlertSeverity
from app.api.deps import get_current_user, require_admin
from app.models.user import User

router = APIRouter(prefix="/network-storage", tags=["Network & Storage Monitoring"])


# ================================
# Pydantic模型定义
# ================================

class NetworkInterfaceResponse(BaseModel):
    """网络接口响应"""
    name: str
    is_up: bool
    speed: int
    mtu: int
    bytes_sent: int
    bytes_recv: int
    packets_sent: int
    packets_recv: int
    errors_in: int
    errors_out: int
    drops_in: int
    drops_out: int


class StorageDeviceResponse(BaseModel):
    """存储设备响应"""
    device: str
    mountpoint: str
    fstype: str
    total_size: int
    used_size: int
    free_size: int
    usage_percent: float
    read_bytes: int
    write_bytes: int
    read_count: int
    write_count: int


class NetworkStorageSummaryResponse(BaseModel):
    """网络存储监控摘要响应"""
    timestamp: str
    network: Dict[str, Any]
    storage: Dict[str, Any]
    alerts: Dict[str, int]


# ================================
# 基础监控API
# ================================

@router.get("/metrics/current")
async def get_current_network_storage_metrics(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取当前所有网络存储指标
    """
    try:
        current_metrics = await network_storage_monitor.get_current_metrics()
        
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
        raise HTTPException(status_code=500, detail=f"Failed to get current network storage metrics: {str(e)}")


@router.get("/metrics/summary")
async def get_network_storage_summary(
    current_user: User = Depends(require_admin)
) -> NetworkStorageSummaryResponse:
    """
    获取网络存储监控摘要
    """
    try:
        summary = await network_storage_monitor.get_network_storage_summary()
        
        return NetworkStorageSummaryResponse(
            timestamp=summary["timestamp"],
            network=summary["network"],
            storage=summary["storage"],
            alerts=summary["alerts"]
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get network storage summary: {str(e)}")


# ================================
# 网络监控API
# ================================

@router.get("/network/interfaces")
async def get_network_interfaces(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取网络接口信息
    """
    try:
        interfaces = await network_storage_monitor.get_network_interfaces()
        
        # 格式化接口数据
        formatted_interfaces = []
        for interface in interfaces:
            formatted_interfaces.append({
                "name": interface.name,
                "is_up": interface.is_up,
                "speed": interface.speed,
                "mtu": interface.mtu,
                "bytes_sent": interface.bytes_sent,
                "bytes_recv": interface.bytes_recv,
                "packets_sent": interface.packets_sent,
                "packets_recv": interface.packets_recv,
                "errors_in": interface.errors_in,
                "errors_out": interface.errors_out,
                "drops_in": interface.drops_in,
                "drops_out": interface.drops_out,
                "bandwidth_sent_mb": interface.bytes_sent / (1024**2),
                "bandwidth_recv_mb": interface.bytes_recv / (1024**2)
            })
        
        # 统计信息
        total_interfaces = len(formatted_interfaces)
        active_interfaces = len([i for i in formatted_interfaces if i["is_up"]])
        total_errors = sum(i["errors_in"] + i["errors_out"] for i in formatted_interfaces)
        total_drops = sum(i["drops_in"] + i["drops_out"] for i in formatted_interfaces)
        
        return {
            "interfaces": formatted_interfaces,
            "statistics": {
                "total_interfaces": total_interfaces,
                "active_interfaces": active_interfaces,
                "total_errors": total_errors,
                "total_drops": total_drops
            },
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get network interfaces: {str(e)}")


@router.get("/network/bandwidth")
async def get_network_bandwidth(
    interface: Optional[str] = Query(None, description="指定网络接口"),
    hours: int = Query(default=1, ge=1, le=24, description="查询时间范围（小时）"),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取网络带宽使用情况
    """
    try:
        from app.core.redis_client import get_redis_client
        
        redis_client = get_redis_client()
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        # 获取带宽历史数据
        bandwidth_metrics = {}
        
        if interface:
            # 获取特定接口的带宽数据
            pattern = f"network_metric:history:bandwidth:interface_{interface}_*"
        else:
            # 获取所有接口的带宽数据
            pattern = "network_metric:history:bandwidth:interface_*"
        
        async for key in redis_client.scan_iter(match=pattern):
            metric_name = key.decode().split(":")[-1]
            start_timestamp = int(start_time.timestamp())
            end_timestamp = int(end_time.timestamp())
            
            results = await redis_client.zrangebyscore(
                key,
                start_timestamp,
                end_timestamp
            )
            
            history = []
            for result in results:
                data = json.loads(result)
                history.append(data)
            
            bandwidth_metrics[metric_name] = history
        
        # 计算当前带宽使用率
        current_metrics = await network_storage_monitor.get_current_metrics()
        current_bandwidth = {}
        
        for metric_name, data in current_metrics.items():
            if "bandwidth" in metric_name:
                current_bandwidth[metric_name] = data
        
        return {
            "current_bandwidth": current_bandwidth,
            "bandwidth_history": bandwidth_metrics,
            "period": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "hours": hours
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get network bandwidth: {str(e)}")


@router.get("/network/connections")
async def get_network_connections(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取网络连接统计
    """
    try:
        current_metrics = await network_storage_monitor.get_current_metrics()
        
        connection_metrics = {}
        connection_keys = ["total_connections", "established_connections"]
        
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
        
        # 获取连接状态分布
        total_connections = connection_metrics.get("total_connections", {}).get("value", 0)
        metadata = connection_metrics.get("total_connections", {}).get("metadata", {})
        
        connection_distribution = {
            "ESTABLISHED": metadata.get("ESTABLISHED", 0),
            "LISTEN": metadata.get("LISTEN", 0),
            "TIME_WAIT": metadata.get("TIME_WAIT", 0),
            "CLOSE_WAIT": metadata.get("CLOSE_WAIT", 0),
            "other": metadata.get("other", 0)
        }
        
        return {
            "connections": connection_metrics,
            "distribution": connection_distribution,
            "health": {
                "total_connections": total_connections,
                "established_ratio": (connection_distribution["ESTABLISHED"] / total_connections * 100) if total_connections > 0 else 0
            },
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get network connections: {str(e)}")


@router.get("/network/latency")
async def get_network_latency(
    hours: int = Query(default=1, ge=1, le=24, description="查询时间范围（小时）"),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取网络延迟指标
    """
    try:
        from app.core.redis_client import get_redis_client
        
        redis_client = get_redis_client()
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        # 获取延迟历史数据
        latency_history = {}
        pattern = "network_metric:history:latency:latency_*"
        
        async for key in redis_client.scan_iter(match=pattern):
            metric_name = key.decode().split(":")[-1]
            start_timestamp = int(start_time.timestamp())
            end_timestamp = int(end_time.timestamp())
            
            results = await redis_client.zrangebyscore(
                key,
                start_timestamp,
                end_timestamp
            )
            
            history = []
            for result in results:
                data = json.loads(result)
                history.append(data)
            
            latency_history[metric_name] = history
        
        # 获取当前延迟数据
        current_metrics = await network_storage_monitor.get_current_metrics()
        current_latency = {}
        
        for metric_name, data in current_metrics.items():
            if "latency" in metric_name:
                current_latency[metric_name] = data
        
        # 计算延迟统计
        latency_stats = {}
        for target, history in latency_history.items():
            if history:
                values = [point["value"] for point in history if point["value"] < 9999]  # 排除失败的ping
                if values:
                    latency_stats[target] = {
                        "avg": sum(values) / len(values),
                        "min": min(values),
                        "max": max(values),
                        "success_rate": len(values) / len(history) * 100
                    }
                else:
                    latency_stats[target] = {
                        "avg": 0,
                        "min": 0,
                        "max": 0,
                        "success_rate": 0
                    }
        
        return {
            "current_latency": current_latency,
            "latency_history": latency_history,
            "latency_statistics": latency_stats,
            "period": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "hours": hours
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get network latency: {str(e)}")


@router.get("/network/dns")
async def get_dns_performance(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取DNS解析性能
    """
    try:
        current_metrics = await network_storage_monitor.get_current_metrics()
        
        dns_metrics = {}
        
        for metric_name, data in current_metrics.items():
            if "dns" in metric_name:
                dns_metrics[metric_name] = {
                    "value": data["value"],
                    "unit": data["unit"],
                    "status": data.get("status", "normal"),
                    "timestamp": data["timestamp"],
                    "metadata": data.get("metadata", {})
                }
        
        # 计算DNS健康状态
        healthy_dns = len([m for m in dns_metrics.values() if m["value"] < 9999])
        total_dns = len(dns_metrics)
        
        if total_dns > 0:
            dns_health_percent = (healthy_dns / total_dns) * 100
        else:
            dns_health_percent = 0
        
        return {
            "dns_metrics": dns_metrics,
            "health": {
                "healthy_dns": healthy_dns,
                "total_dns": total_dns,
                "health_percent": dns_health_percent
            },
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get DNS performance: {str(e)}")


# ================================
# 存储监控API
# ================================

@router.get("/storage/devices")
async def get_storage_devices(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取存储设备信息
    """
    try:
        devices = await network_storage_monitor.get_storage_devices()
        
        # 格式化设备数据
        formatted_devices = []
        for device in devices:
            formatted_devices.append({
                "device": device.device,
                "mountpoint": device.mountpoint,
                "fstype": device.fstype,
                "total_size_gb": device.total_size / (1024**3),
                "used_size_gb": device.used_size / (1024**3),
                "free_size_gb": device.free_size / (1024**3),
                "usage_percent": device.usage_percent,
                "read_bytes_mb": device.read_bytes / (1024**2),
                "write_bytes_mb": device.write_bytes / (1024**2),
                "read_count": device.read_count,
                "write_count": device.write_count,
                "read_throughput_mb": (device.read_bytes / (1024**2)) / 60,  # 假设1分钟的数据
                "write_throughput_mb": (device.write_bytes / (1024**2)) / 60
            })
        
        # 统计信息
        total_devices = len(formatted_devices)
        total_storage_gb = sum(d["total_size_gb"] for d in formatted_devices)
        used_storage_gb = sum(d["used_size_gb"] for d in formatted_devices)
        free_storage_gb = sum(d["free_size_gb"] for d in formatted_devices)
        
        if total_storage_gb > 0:
            overall_usage_percent = (used_storage_gb / total_storage_gb) * 100
        else:
            overall_usage_percent = 0
        
        # 检查存储健康状态
        critical_devices = [d for d in formatted_devices if d["usage_percent"] >= 95]
        warning_devices = [d for d in formatted_devices if 80 <= d["usage_percent"] < 95]
        
        return {
            "devices": formatted_devices,
            "statistics": {
                "total_devices": total_devices,
                "total_storage_gb": round(total_storage_gb, 2),
                "used_storage_gb": round(used_storage_gb, 2),
                "free_storage_gb": round(free_storage_gb, 2),
                "overall_usage_percent": round(overall_usage_percent, 2),
                "critical_devices": len(critical_devices),
                "warning_devices": len(warning_devices)
            },
            "health": {
                "status": "critical" if critical_devices else "warning" if warning_devices else "healthy",
                "critical_devices": [d["device"] for d in critical_devices],
                "warning_devices": [d["device"] for d in warning_devices]
            },
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get storage devices: {str(e)}")


@router.get("/storage/space")
async def get_storage_space(
    device: Optional[str] = Query(None, description="指定存储设备"),
    hours: int = Query(default=1, ge=1, le=24, description="查询时间范围（小时）"),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取存储空间使用情况
    """
    try:
        from app.core.redis_client import get_redis_client
        
        redis_client = get_redis_client()
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        # 获取存储空间历史数据
        space_history = {}
        
        if device:
            pattern = f"storage_metric:history:space:disk_usage_percent_{device.replace('/', '_')}"
        else:
            pattern = "storage_metric:history:space:disk_usage_percent_*"
        
        async for key in redis_client.scan_iter(match=pattern):
            metric_name = key.decode().split(":")[-1]
            start_timestamp = int(start_time.timestamp())
            end_timestamp = int(end_time.timestamp())
            
            results = await redis_client.zrangebyscore(
                key,
                start_timestamp,
                end_timestamp
            )
            
            history = []
            for result in results:
                data = json.loads(result)
                history.append(data)
            
            space_history[metric_name] = history
        
        # 获取当前存储空间数据
        current_metrics = await network_storage_monitor.get_current_metrics()
        current_space = {}
        
        for metric_name, data in current_metrics.items():
            if "disk_usage_percent" in metric_name or "disk_free_gb" in metric_name:
                current_space[metric_name] = data
        
        return {
            "current_space": current_space,
            "space_history": space_history,
            "period": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "hours": hours
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get storage space: {str(e)}")


@router.get("/storage/io")
async def get_storage_io(
    device: Optional[str] = Query(None, description="指定存储设备"),
    hours: int = Query(default=1, ge=1, le=24, description="查询时间范围（小时）"),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取存储I/O性能
    """
    try:
        from app.core.redis_client import get_redis_client
        
        redis_client = get_redis_client()
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        # 获取I/O历史数据
        io_history = {}
        
        if device:
            patterns = [
                f"storage_metric:history:io:disk_read_throughput_mb_{device}*",
                f"storage_metric:history:io:disk_write_throughput_mb_{device}*"
            ]
        else:
            patterns = [
                "storage_metric:history:io:disk_read_throughput_mb_*",
                "storage_metric:history:io:disk_write_throughput_mb_*"
            ]
        
        for pattern in patterns:
            async for key in redis_client.scan_iter(match=pattern):
                metric_name = key.decode().split(":")[-1]
                start_timestamp = int(start_time.timestamp())
                end_timestamp = int(end_time.timestamp())
                
                results = await redis_client.zrangebyscore(
                    key,
                    start_timestamp,
                    end_timestamp
                )
                
                history = []
                for result in results:
                    data = json.loads(result)
                    history.append(data)
                
                io_history[metric_name] = history
        
        # 获取当前I/O数据
        current_metrics = await network_storage_monitor.get_current_metrics()
        current_io = {}
        
        for metric_name, data in current_metrics.items():
            if "disk_" in metric_name and ("throughput" in metric_name or "_ops" in metric_name):
                current_io[metric_name] = data
        
        # 计算I/O统计
        io_stats = {}
        for metric_name, history in io_history.items():
            if history:
                values = [point["value"] for point in history]
                if values:
                    io_stats[metric_name] = {
                        "avg": sum(values) / len(values),
                        "min": min(values),
                        "max": max(values),
                        "latest": values[-1]
                    }
        
        return {
            "current_io": current_io,
            "io_history": io_history,
            "io_statistics": io_stats,
            "period": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "hours": hours
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get storage I/O: {str(e)}")


@router.get("/storage/performance")
async def get_storage_performance(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取存储性能指标
    """
    try:
        current_metrics = await network_storage_monitor.get_current_metrics()
        
        performance_metrics = {}
        
        for metric_name, data in current_metrics.items():
            if "total_disk" in metric_name or "storage_accessibility" in metric_name:
                performance_metrics[metric_name] = {
                    "value": data["value"],
                    "unit": data["unit"],
                    "status": data.get("status", "normal"),
                    "timestamp": data["timestamp"],
                    "metadata": data.get("metadata", {})
                }
        
        # 计算性能评分
        accessibility = performance_metrics.get("storage_accessibility_percent", {}).get("value", 0)
        
        performance_score = accessibility  # 基于可访问性评分
        
        if performance_score >= 95:
            performance_status = "excellent"
        elif performance_score >= 85:
            performance_status = "good"
        elif performance_score >= 70:
            performance_status = "warning"
        else:
            performance_status = "critical"
        
        return {
            "performance": performance_metrics,
            "score": {
                "value": round(performance_score, 2),
                "status": performance_status
            },
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get storage performance: {str(e)}")


# ================================
# 告警和健康API
# ================================

@router.get("/alerts")
async def get_network_storage_alerts(
    status: Optional[str] = Query(None, pattern="^(active|resolved|all)$", description="告警状态过滤"),
    severity: Optional[str] = Query(None, pattern="^(warning|critical|all)$", description="严重程度过滤"),
    limit: int = Query(default=50, ge=1, le=100, description="返回数量限制"),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取网络存储告警
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
        
        # 获取网络和存储告警
        sources = ["network_monitor", "storage_monitor"]
        all_alerts = []
        
        for source in sources:
            alerts = await alert_manager.get_alerts(
                status=alert_status,
                severity=alert_severity,
                source=source,
                limit=limit
            )
            all_alerts.extend(alerts)
        
        # 格式化告警数据
        formatted_alerts = []
        for alert in all_alerts:
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
        raise HTTPException(status_code=500, detail=f"Failed to get network storage alerts: {str(e)}")


@router.get("/health")
async def get_network_storage_health(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取网络存储健康状态
    """
    try:
        summary = await network_storage_monitor.get_network_storage_summary()
        
        # 计算健康评分
        total_metrics = len(summary["network"]["metrics"]) + len(summary["storage"]["metrics"])
        warning_metrics = summary["alerts"]["warning"]
        critical_metrics = summary["alerts"]["critical"]
        
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
        
        # 网络和存储特定的健康检查
        health_checks = await _perform_network_storage_health_checks()
        
        return {
            "health_score": round(health_score, 2),
            "health_status": health_status,
            "total_metrics": total_metrics,
            "warning_metrics": warning_metrics,
            "critical_metrics": critical_metrics,
            "active_alerts": summary["alerts"]["warning"] + summary["alerts"]["critical"],
            "health_checks": health_checks,
            "timestamp": datetime.now().isoformat(),
            "recommendations": _generate_network_storage_health_recommendations(health_status, summary, health_checks)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get network storage health: {str(e)}")


# ================================
# 辅助函数
# ================================

async def _perform_network_storage_health_checks() -> Dict[str, Any]:
    """执行网络存储健康检查"""
    health_checks = {
        "network_connectivity": {"status": "unknown", "message": ""},
        "dns_resolution": {"status": "unknown", "message": ""},
        "disk_accessibility": {"status": "unknown", "message": ""},
        "io_performance": {"status": "unknown", "message": ""}
    }
    
    try:
        # 网络连通性检查
        try:
            import socket
            test_hosts = ["8.8.8.8", "1.1.1.1"]
            connected_hosts = 0
            
            for host in test_hosts:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(5)
                    result = sock.connect_ex((host, 53))
                    sock.close()
                    if result == 0:
                        connected_hosts += 1
                except:
                    pass
            
            if connected_hosts >= 2:
                health_checks["network_connectivity"] = {"status": "healthy", "message": f"All {len(test_hosts)} test hosts reachable"}
            elif connected_hosts >= 1:
                health_checks["network_connectivity"] = {"status": "warning", "message": f"Only {connected_hosts}/{len(test_hosts)} test hosts reachable"}
            else:
                health_checks["network_connectivity"] = {"status": "critical", "message": "No test hosts reachable"}
        
        except Exception as e:
            health_checks["network_connectivity"] = {"status": "critical", "message": f"Network connectivity check failed: {str(e)}"}
        
        # DNS解析检查
        try:
            import socket
            test_domains = ["google.com", "github.com"]
            resolved_domains = 0
            
            for domain in test_domains:
                try:
                    socket.gethostbyname(domain)
                    resolved_domains += 1
                except:
                    pass
            
            if resolved_domains >= 2:
                health_checks["dns_resolution"] = {"status": "healthy", "message": f"All {len(test_domains)} test domains resolved"}
            elif resolved_domains >= 1:
                health_checks["dns_resolution"] = {"status": "warning", "message": f"Only {resolved_domains}/{len(test_domains)} test domains resolved"}
            else:
                health_checks["dns_resolution"] = {"status": "critical", "message": "No test domains resolved"}
        
        except Exception as e:
            health_checks["dns_resolution"] = {"status": "critical", "message": f"DNS resolution check failed: {str(e)}"}
        
        # 磁盘可访问性检查
        try:
            from pathlib import Path
            critical_paths = ["/", "/tmp", "/var"]
            accessible_paths = 0
            
            for path in critical_paths:
                if Path(path).exists() and Path(path).is_dir():
                    try:
                        test_file = Path(path) / ".health_check_test"
                        test_file.touch()
                        test_file.unlink()
                        accessible_paths += 1
                    except:
                        pass
            
            if accessible_paths >= 3:
                health_checks["disk_accessibility"] = {"status": "healthy", "message": f"All {len(critical_paths)} critical paths accessible"}
            elif accessible_paths >= 2:
                health_checks["disk_accessibility"] = {"status": "warning", "message": f"Only {accessible_paths}/{len(critical_paths)} critical paths accessible"}
            else:
                health_checks["disk_accessibility"] = {"status": "critical", "message": f"Only {accessible_paths}/{len(critical_paths)} critical paths accessible"}
        
        except Exception as e:
            health_checks["disk_accessibility"] = {"status": "critical", "message": f"Disk accessibility check failed: {str(e)}"}
        
        # I/O性能检查
        try:
            import time
            from pathlib import Path
            
            # 测试文件写入性能
            test_file = Path("/tmp") / "io_performance_test"
            test_data = b"x" * (1024 * 1024)  # 1MB测试数据
            
            start_time = time.time()
            with open(test_file, "wb") as f:
                f.write(test_data)
            write_time = time.time() - start_time
            
            start_time = time.time()
            with open(test_file, "rb") as f:
                f.read()
            read_time = time.time() - start_time
            
            test_file.unlink()
            
            write_throughput = (1 / write_time) if write_time > 0 else 0  # MB/s
            read_throughput = (1 / read_time) if read_time > 0 else 0    # MB/s
            
            if write_throughput >= 10 and read_throughput >= 50:
                health_checks["io_performance"] = {"status": "healthy", "message": f"Good I/O performance: Write {write_throughput:.1f}MB/s, Read {read_throughput:.1f}MB/s"}
            elif write_throughput >= 5 and read_throughput >= 20:
                health_checks["io_performance"] = {"status": "warning", "message": f"Moderate I/O performance: Write {write_throughput:.1f}MB/s, Read {read_throughput:.1f}MB/s"}
            else:
                health_checks["io_performance"] = {"status": "critical", "message": f"Poor I/O performance: Write {write_throughput:.1f}MB/s, Read {read_throughput:.1f}MB/s"}
        
        except Exception as e:
            health_checks["io_performance"] = {"status": "critical", "message": f"I/O performance check failed: {str(e)}"}
    
    except Exception as e:
        logger.error(f"Error performing network storage health checks: {e}")
    
    return health_checks


def _generate_network_storage_health_recommendations(health_status: str, summary: Dict[str, Any], health_checks: Dict[str, Any]) -> List[str]:
    """生成网络存储健康建议"""
    recommendations = []
    
    try:
        if health_status == "critical":
            recommendations.append("网络存储状态严重，需要立即检查和处理")
            recommendations.append("检查网络连接、磁盘空间和I/O性能")
        elif health_status == "warning":
            recommendations.append("网络存储性能需要关注，建议优化配置")
        
        # 基于健康检查的建议
        for check_name, check_result in health_checks.items():
            if check_result["status"] == "critical":
                recommendations.append(f"紧急处理 {check_name} 问题: {check_result['message']}")
            elif check_result["status"] == "warning":
                recommendations.append(f"关注 {check_name}: {check_result['message']}")
        
        # 基于告警的建议
        if summary["alerts"]["critical"] > 0:
            recommendations.append("存在严重告警，需要立即处理网络存储问题")
        
        if summary["alerts"]["warning"] > 5:
            recommendations.append("警告告警较多，建议进行网络存储优化")
        
        # 检查具体的网络问题
        network_metrics = summary["network"]["metrics"]
        for metric_name, metric_data in network_metrics.items():
            if metric_data.get("status") == "critical":
                if "bandwidth" in metric_name:
                    recommendations.append("网络带宽使用率过高，检查网络流量和优化带宽配置")
                elif "latency" in metric_name:
                    recommendations.append("网络延迟过高，检查网络连接质量和路由配置")
                elif "connection" in metric_name:
                    recommendations.append("网络连接数过多，检查应用程序连接池配置")
        
        # 检查具体的存储问题
        storage_metrics = summary["storage"]["metrics"]
        for metric_name, metric_data in storage_metrics.items():
            if metric_data.get("status") == "critical":
                if "disk_usage" in metric_name:
                    recommendations.append("磁盘空间不足，清理无用文件或扩容存储")
                elif "throughput" in metric_name:
                    recommendations.append("磁盘I/O性能差，优化存储配置或升级硬件")
    
    except Exception as e:
        recommendations.append(f"生成建议时出错: {str(e)}")
    
    return recommendations
