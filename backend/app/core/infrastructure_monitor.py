"""
基础设施监控系统
监控服务器资源使用情况，包括CPU、内存、磁盘、网络等
"""
import asyncio
import psutil
import platform
import time
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

from app.core.config import settings
from app.core.redis_client import get_redis_client
from app.core.structured_logging import get_logger
from app.core.alerting_system import alert_manager, AlertSeverity

logger = get_logger("infrastructure_monitor")


class ResourceType(Enum):
    """资源类型"""
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    SYSTEM = "system"


class AlertLevel(Enum):
    """告警级别"""
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class ResourceMetric:
    """资源指标"""
    timestamp: datetime
    resource_type: ResourceType
    metric_name: str
    value: float
    unit: str
    threshold_warning: float = 0.0
    threshold_critical: float = 0.0
    status: AlertLevel = AlertLevel.NORMAL
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        
        # 根据阈值设置状态
        if self.threshold_critical > 0 and self.value >= self.threshold_critical:
            self.status = AlertLevel.CRITICAL
        elif self.threshold_warning > 0 and self.value >= self.threshold_warning:
            self.status = AlertLevel.WARNING
        else:
            self.status = AlertLevel.NORMAL


@dataclass
class SystemInfo:
    """系统信息"""
    hostname: str
    platform: str
    platform_version: str
    architecture: str
    cpu_count: int
    cpu_freq: float
    total_memory: int
    boot_time: datetime
    uptime: timedelta


class ResourceMonitor:
    """
    资源监控器
    负责收集各种系统资源指标
    """
    
    def __init__(self):
        self.redis_client = None
        self.running = False
        self.collection_interval = 30  # 30秒收集一次
        self.retention_days = 7  # 数据保留7天
        
        # 阈值配置
        self.thresholds = {
            "cpu": {
                "warning": 70.0,
                "critical": 90.0
            },
            "memory": {
                "warning": 80.0,
                "critical": 95.0
            },
            "disk": {
                "warning": 80.0,
                "critical": 95.0
            },
            "network": {
                "warning": 1000.0,  # MB/s
                "critical": 2000.0
            }
        }
    
    async def initialize(self):
        """初始化资源监控器"""
        if self.running:
            return
        
        self.redis_client = get_redis_client()
        self.running = True
        
        logger.info("Resource monitor initialized")
    
    async def shutdown(self):
        """关闭资源监控器"""
        self.running = False
        logger.info("Resource monitor shutdown")
    
    async def start_monitoring(self):
        """开始监控"""
        if not self.running:
            await self.initialize()
        
        logger.info("Starting resource monitoring...")
        
        while self.running:
            try:
                # 收集所有资源指标
                metrics = await self.collect_all_metrics()
                
                # 存储指标
                await self.store_metrics(metrics)
                
                # 检查告警
                await self.check_alerts(metrics)
                
                # 等待下次收集
                await asyncio.sleep(self.collection_interval)
                
            except Exception as e:
                logger.error(f"Error in resource monitoring loop: {e}")
                await asyncio.sleep(60)  # 出错时等待1分钟
    
    async def collect_all_metrics(self) -> List[ResourceMetric]:
        """收集所有资源指标"""
        metrics = []
        
        try:
            # CPU指标
            cpu_metrics = await self.collect_cpu_metrics()
            metrics.extend(cpu_metrics)
            
            # 内存指标
            memory_metrics = await self.collect_memory_metrics()
            metrics.extend(memory_metrics)
            
            # 磁盘指标
            disk_metrics = await self.collect_disk_metrics()
            metrics.extend(disk_metrics)
            
            # 网络指标
            network_metrics = await self.collect_network_metrics()
            metrics.extend(network_metrics)
            
            # 系统指标
            system_metrics = await self.collect_system_metrics()
            metrics.extend(system_metrics)
            
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
        
        return metrics
    
    async def collect_cpu_metrics(self) -> List[ResourceMetric]:
        """收集CPU指标"""
        metrics = []
        timestamp = datetime.now()
        
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            metrics.append(ResourceMetric(
                timestamp=timestamp,
                resource_type=ResourceType.CPU,
                metric_name="cpu_usage_percent",
                value=cpu_percent,
                unit="percent",
                threshold_warning=self.thresholds["cpu"]["warning"],
                threshold_critical=self.thresholds["cpu"]["critical"],
                metadata={"cores": psutil.cpu_count()}
            ))
            
            # CPU负载（Linux/Unix）
            if hasattr(psutil, 'getloadavg'):
                load_avg = psutil.getloadavg()
                metrics.append(ResourceMetric(
                    timestamp=timestamp,
                    resource_type=ResourceType.CPU,
                    metric_name="cpu_load_1min",
                    value=load_avg[0],
                    unit="load",
                    threshold_warning=psutil.cpu_count() * 0.7,
                    threshold_critical=psutil.cpu_count() * 0.9
                ))
                
                metrics.append(ResourceMetric(
                    timestamp=timestamp,
                    resource_type=ResourceType.CPU,
                    metric_name="cpu_load_5min",
                    value=load_avg[1],
                    unit="load"
                ))
                
                metrics.append(ResourceMetric(
                    timestamp=timestamp,
                    resource_type=ResourceType.CPU,
                    metric_name="cpu_load_15min",
                    value=load_avg[2],
                    unit="load"
                ))
            
            # 每核心CPU使用率
            cpu_per_core = psutil.cpu_percent(interval=1, percpu=True)
            for i, core_percent in enumerate(cpu_per_core):
                metrics.append(ResourceMetric(
                    timestamp=timestamp,
                    resource_type=ResourceType.CPU,
                    metric_name=f"cpu_core_{i}_usage_percent",
                    value=core_percent,
                    unit="percent",
                    threshold_warning=self.thresholds["cpu"]["warning"],
                    threshold_critical=self.thresholds["cpu"]["critical"],
                    metadata={"core_id": i}
                ))
            
        except Exception as e:
            logger.error(f"Error collecting CPU metrics: {e}")
        
        return metrics
    
    async def collect_memory_metrics(self) -> List[ResourceMetric]:
        """收集内存指标"""
        metrics = []
        timestamp = datetime.now()
        
        try:
            # 虚拟内存
            virtual_memory = psutil.virtual_memory()
            
            metrics.append(ResourceMetric(
                timestamp=timestamp,
                resource_type=ResourceType.MEMORY,
                metric_name="memory_usage_percent",
                value=virtual_memory.percent,
                unit="percent",
                threshold_warning=self.thresholds["memory"]["warning"],
                threshold_critical=self.thresholds["memory"]["critical"],
                metadata={
                    "total_gb": virtual_memory.total / (1024**3),
                    "available_gb": virtual_memory.available / (1024**3),
                    "used_gb": virtual_memory.used / (1024**3)
                }
            ))
            
            metrics.append(ResourceMetric(
                timestamp=timestamp,
                resource_type=ResourceType.MEMORY,
                metric_name="memory_used_gb",
                value=virtual_memory.used / (1024**3),
                unit="GB"
            ))
            
            metrics.append(ResourceMetric(
                timestamp=timestamp,
                resource_type=ResourceType.MEMORY,
                metric_name="memory_available_gb",
                value=virtual_memory.available / (1024**3),
                unit="GB"
            ))
            
            # 交换内存
            swap_memory = psutil.swap_memory()
            
            metrics.append(ResourceMetric(
                timestamp=timestamp,
                resource_type=ResourceType.MEMORY,
                metric_name="swap_usage_percent",
                value=swap_memory.percent,
                unit="percent",
                threshold_warning=50.0,
                threshold_critical=80.0,
                metadata={
                    "total_gb": swap_memory.total / (1024**3),
                    "used_gb": swap_memory.used / (1024**3)
                }
            ))
            
        except Exception as e:
            logger.error(f"Error collecting memory metrics: {e}")
        
        return metrics
    
    async def collect_disk_metrics(self) -> List[ResourceMetric]:
        """收集磁盘指标"""
        metrics = []
        timestamp = datetime.now()
        
        try:
            # 磁盘分区信息
            disk_partitions = psutil.disk_partitions()
            
            for partition in disk_partitions:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    
                    usage_percent = (usage.used / usage.total) * 100
                    
                    metrics.append(ResourceMetric(
                        timestamp=timestamp,
                        resource_type=ResourceType.DISK,
                        metric_name=f"disk_usage_percent_{partition.device}",
                        value=usage_percent,
                        unit="percent",
                        threshold_warning=self.thresholds["disk"]["warning"],
                        threshold_critical=self.thresholds["disk"]["critical"],
                        metadata={
                            "device": partition.device,
                            "mountpoint": partition.mountpoint,
                            "fstype": partition.fstype,
                            "total_gb": usage.total / (1024**3),
                            "used_gb": usage.used / (1024**3),
                            "free_gb": usage.free / (1024**3)
                        }
                    ))
                    
                    metrics.append(ResourceMetric(
                        timestamp=timestamp,
                        resource_type=ResourceType.DISK,
                        metric_name=f"disk_free_gb_{partition.device}",
                        value=usage.free / (1024**3),
                        unit="GB",
                        metadata={
                            "device": partition.device,
                            "mountpoint": partition.mountpoint
                        }
                    ))
                    
                except Exception as e:
                    logger.warning(f"Error getting disk usage for {partition.mountpoint}: {e}")
                    continue
            
            # 磁盘I/O统计
            disk_io = psutil.disk_io_counters()
            
            if disk_io:
                metrics.append(ResourceMetric(
                    timestamp=timestamp,
                    resource_type=ResourceType.DISK,
                    metric_name="disk_read_bytes_per_sec",
                    value=disk_io.read_bytes / self.collection_interval,
                    unit="bytes/sec",
                    metadata={
                        "read_count": disk_io.read_count,
                        "write_count": disk_io.write_count
                    }
                ))
                
                metrics.append(ResourceMetric(
                    timestamp=timestamp,
                    resource_type=ResourceType.DISK,
                    metric_name="disk_write_bytes_per_sec",
                    value=disk_io.write_bytes / self.collection_interval,
                    unit="bytes/sec"
                ))
                
        except Exception as e:
            logger.error(f"Error collecting disk metrics: {e}")
        
        return metrics
    
    async def collect_network_metrics(self) -> List[ResourceMetric]:
        """收集网络指标"""
        metrics = []
        timestamp = datetime.now()
        
        try:
            # 网络I/O统计
            network_io = psutil.net_io_counters()
            
            if network_io:
                metrics.append(ResourceMetric(
                    timestamp=timestamp,
                    resource_type=ResourceType.NETWORK,
                    metric_name="network_bytes_sent_per_sec",
                    value=network_io.bytes_sent / self.collection_interval,
                    unit="bytes/sec",
                    metadata={
                        "packets_sent": network_io.packets_sent,
                        "packets_recv": network_io.packets_recv
                    }
                ))
                
                metrics.append(ResourceMetric(
                    timestamp=timestamp,
                    resource_type=ResourceType.NETWORK,
                    metric_name="network_bytes_recv_per_sec",
                    value=network_io.bytes_recv / self.collection_interval,
                    unit="bytes/sec"
                ))
                
                # 转换为MB/s
                metrics.append(ResourceMetric(
                    timestamp=timestamp,
                    resource_type=ResourceType.NETWORK,
                    metric_name="network_mbps_sent",
                    value=(network_io.bytes_sent / self.collection_interval) * 8 / (1024**2),
                    unit="Mbps",
                    threshold_warning=self.thresholds["network"]["warning"],
                    threshold_critical=self.thresholds["network"]["critical"]
                ))
                
                metrics.append(ResourceMetric(
                    timestamp=timestamp,
                    resource_type=ResourceType.NETWORK,
                    metric_name="network_mbps_recv",
                    value=(network_io.bytes_recv / self.collection_interval) * 8 / (1024**2),
                    unit="Mbps",
                    threshold_warning=self.thresholds["network"]["warning"],
                    threshold_critical=self.thresholds["network"]["critical"]
                ))
            
            # 网络连接数
            connections = psutil.net_connections()
            active_connections = len([conn for conn in connections if conn.status == 'ESTABLISHED'])
            
            metrics.append(ResourceMetric(
                timestamp=timestamp,
                resource_type=ResourceType.NETWORK,
                metric_name="network_active_connections",
                value=active_connections,
                unit="count",
                threshold_warning=1000,
                threshold_critical=2000,
                metadata={
                    "total_connections": len(connections)
                }
            ))
            
        except Exception as e:
            logger.error(f"Error collecting network metrics: {e}")
        
        return metrics
    
    async def collect_system_metrics(self) -> List[ResourceMetric]:
        """收集系统指标"""
        metrics = []
        timestamp = datetime.now()
        
        try:
            # 系统负载
            process_count = len(psutil.pids())
            
            metrics.append(ResourceMetric(
                timestamp=timestamp,
                resource_type=ResourceType.SYSTEM,
                metric_name="system_process_count",
                value=process_count,
                unit="count",
                threshold_warning=500,
                threshold_critical=1000
            ))
            
            # 系统运行时间
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            
            metrics.append(ResourceMetric(
                timestamp=timestamp,
                resource_type=ResourceType.SYSTEM,
                metric_name="system_uptime_hours",
                value=uptime.total_seconds() / 3600,
                unit="hours",
                metadata={
                    "boot_time": boot_time.isoformat(),
                    "uptime_days": uptime.days
                }
            ))
            
            # 当前进程的资源使用
            current_process = psutil.Process()
            
            metrics.append(ResourceMetric(
                timestamp=timestamp,
                resource_type=ResourceType.SYSTEM,
                metric_name="app_cpu_usage_percent",
                value=current_process.cpu_percent(),
                unit="percent",
                metadata={"pid": current_process.pid}
            ))
            
            metrics.append(ResourceMetric(
                timestamp=timestamp,
                resource_type=ResourceType.SYSTEM,
                metric_name="app_memory_usage_mb",
                value=current_process.memory_info().rss / (1024**2),
                unit="MB",
                threshold_warning=1000,
                threshold_critical=2000,
                metadata={"pid": current_process.pid}
            ))
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
        
        return metrics
    
    async def store_metrics(self, metrics: List[ResourceMetric]):
        """存储指标到Redis"""
        try:
            for metric in metrics:
                # 存储最新值
                latest_key = f"metric:latest:{metric.resource_type.value}:{metric.metric_name}"
                metric_data = {
                    "timestamp": metric.timestamp.isoformat(),
                    "value": metric.value,
                    "unit": metric.unit,
                    "status": metric.status.value,
                    "metadata": metric.metadata
                }
                
                await self.redis_client.setex(
                    latest_key,
                    self.retention_days * 24 * 3600,
                    json.dumps(metric_data)
                )
                
                # 存储历史数据（时间序列）
                history_key = f"metric:history:{metric.resource_type.value}:{metric.metric_name}"
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
            logger.error(f"Error storing metrics: {e}")
    
    async def check_alerts(self, metrics: List[ResourceMetric]):
        """检查告警条件"""
        try:
            for metric in metrics:
                if metric.status == AlertLevel.WARNING:
                    await self.create_alert(
                        metric,
                        AlertSeverity.WARNING,
                        f"High {metric.metric_name}",
                        f"{metric.resource_type.value.title()} usage is {metric.value:.1f}{metric.unit}, exceeding warning threshold of {metric.threshold_warning}{metric.unit}"
                    )
                
                elif metric.status == AlertLevel.CRITICAL:
                    await self.create_alert(
                        metric,
                        AlertSeverity.CRITICAL,
                        f"Critical {metric.metric_name}",
                        f"{metric.resource_type.value.title()} usage is {metric.value:.1f}{metric.unit}, exceeding critical threshold of {metric.threshold_critical}{metric.unit}"
                    )
        
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")
    
    async def create_alert(self, metric: ResourceMetric, severity: AlertSeverity, title: str, description: str):
        """创建告警"""
        try:
            # 检查是否已经存在相同的活跃告警
            alert_key = f"infrastructure_alert:{metric.resource_type.value}:{metric.metric_name}"
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
                source="infrastructure_monitor",
                service="web3search",
                environment=settings.ENVIRONMENT,
                labels={
                    "resource_type": metric.resource_type.value,
                    "metric_name": metric.metric_name,
                    "hostname": platform.node()
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
            
            logger.warning(f"Created infrastructure alert: {title}")
        
        except Exception as e:
            logger.error(f"Error creating alert: {e}")
    
    async def get_current_metrics(self) -> Dict[str, Any]:
        """获取当前指标"""
        try:
            current_metrics = {}
            
            # 获取所有最新指标
            pattern = "metric:latest:*"
            
            async for key in self.redis_client.scan_iter(match=pattern):
                metric_data = await self.redis_client.get(key)
                
                if metric_data:
                    data = json.loads(metric_data)
                    metric_name = key.decode().split(":")[-1]
                    current_metrics[metric_name] = data
            
            return current_metrics
        
        except Exception as e:
            logger.error(f"Error getting current metrics: {e}")
            return {}
    
    async def get_metric_history(
        self, 
        resource_type: ResourceType, 
        metric_name: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict[str, Any]]:
        """获取指标历史数据"""
        try:
            history_key = f"metric:history:{resource_type.value}:{metric_name}"
            
            start_timestamp = int(start_time.timestamp())
            end_timestamp = int(end_time.timestamp())
            
            # 获取时间范围内的数据
            results = await self.redis_client.zrangebyscore(
                history_key,
                start_timestamp,
                end_timestamp
            )
            
            history = []
            for result in results:
                data = json.loads(result)
                history.append(data)
            
            return history
        
        except Exception as e:
            logger.error(f"Error getting metric history: {e}")
            return []
    
    async def get_system_info(self) -> SystemInfo:
        """获取系统信息"""
        try:
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            
            return SystemInfo(
                hostname=platform.node(),
                platform=platform.system(),
                platform_version=platform.release(),
                architecture=platform.machine(),
                cpu_count=psutil.cpu_count(),
                cpu_freq=psutil.cpu_freq().current if psutil.cpu_freq() else 0.0,
                total_memory=psutil.virtual_memory().total,
                boot_time=boot_time,
                uptime=uptime
            )
        
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            raise
    
    async def get_resource_summary(self) -> Dict[str, Any]:
        """获取资源使用摘要"""
        try:
            current_metrics = await self.get_current_metrics()
            
            summary = {
                "timestamp": datetime.now().isoformat(),
                "system_info": asdict(await self.get_system_info()),
                "resources": {
                    "cpu": {},
                    "memory": {},
                    "disk": {},
                    "network": {},
                    "system": {}
                },
                "alerts": {
                    "warning": 0,
                    "critical": 0
                }
            }
            
            # 分类整理指标
            for metric_name, data in current_metrics.items():
                # 确定资源类型
                if "cpu" in metric_name:
                    resource_type = "cpu"
                elif "memory" in metric_name or "swap" in metric_name:
                    resource_type = "memory"
                elif "disk" in metric_name:
                    resource_type = "disk"
                elif "network" in metric_name:
                    resource_type = "network"
                else:
                    resource_type = "system"
                
                summary["resources"][resource_type][metric_name] = data
                
                # 统计告警
                if data.get("status") == "warning":
                    summary["alerts"]["warning"] += 1
                elif data.get("status") == "critical":
                    summary["alerts"]["critical"] += 1
            
            return summary
        
        except Exception as e:
            logger.error(f"Error getting resource summary: {e}")
            return {}


# 全局资源监控器实例
resource_monitor = ResourceMonitor()
