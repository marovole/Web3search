"""
网络和存储监控系统
监控网络连接、带宽使用、存储空间、I/O性能等
"""
import asyncio
import psutil
import socket
import time
import json
import subprocess
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

from app.core.config import settings
from app.core.redis_client import get_redis_client
from app.core.structured_logging import get_logger
from app.core.alerting_system import alert_manager, AlertSeverity

logger = get_logger("network_storage_monitor")


class NetworkMetricType(Enum):
    """网络指标类型"""
    BANDWIDTH = "bandwidth"
    CONNECTION = "connection"
    LATENCY = "latency"
    PACKET_LOSS = "packet_loss"
    DNS = "dns"


class StorageMetricType(Enum):
    """存储指标类型"""
    SPACE = "space"
    IO = "io"
    PERFORMANCE = "performance"
    HEALTH = "health"


class AlertLevel(Enum):
    """告警级别"""
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class NetworkMetric:
    """网络指标"""
    timestamp: datetime
    metric_type: NetworkMetricType
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
class StorageMetric:
    """存储指标"""
    timestamp: datetime
    metric_type: StorageMetricType
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
class NetworkInterface:
    """网络接口信息"""
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


@dataclass
class StorageDevice:
    """存储设备信息"""
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


class NetworkStorageMonitor:
    """
    网络和存储监控器
    负责监控网络性能和存储状态
    """
    
    def __init__(self):
        self.redis_client = None
        self.running = False
        self.collection_interval = 30  # 30秒收集一次
        self.retention_days = 7  # 数据保留7天
        
        # 阈值配置
        self.thresholds = {
            "network": {
                "bandwidth_usage": {
                    "warning": 80.0,  # 带宽使用率%
                    "critical": 95.0
                },
                "connection_count": {
                    "warning": 1000,
                    "critical": 2000
                },
                "packet_loss": {
                    "warning": 1.0,  # 丢包率%
                    "critical": 5.0
                },
                "latency": {
                    "warning": 100.0,  # 毫秒
                    "critical": 500.0
                }
            },
            "storage": {
                "disk_usage": {
                    "warning": 80.0,  # 磁盘使用率%
                    "critical": 95.0
                },
                "io_wait": {
                    "warning": 20.0,  # I/O等待时间%
                    "critical": 50.0
                },
                "read_throughput": {
                    "warning": 100.0,  # MB/s
                    "critical": 50.0  # 低吞吐量告警
                },
                "write_throughput": {
                    "warning": 100.0,  # MB/s
                    "critical": 50.0  # 低吞吐量告警
                }
            }
        }
        
        # 监控目标
        self.monitor_targets = {
            "network": ["8.8.8.8", "1.1.1.1", "github.com"],  # 网络连通性测试目标
            "dns": ["8.8.8.8", "1.1.1.1"]  # DNS服务器
        }
    
    async def initialize(self):
        """初始化网络存储监控器"""
        if self.running:
            return
        
        self.redis_client = get_redis_client()
        self.running = True
        
        logger.info("Network and storage monitor initialized")
    
    async def shutdown(self):
        """关闭网络存储监控器"""
        self.running = False
        logger.info("Network and storage monitor shutdown")
    
    async def start_monitoring(self):
        """开始监控"""
        if not self.running:
            await self.initialize()
        
        logger.info("Starting network and storage monitoring...")
        
        while self.running:
            try:
                # 收集所有网络和存储指标
                network_metrics = await self.collect_network_metrics()
                storage_metrics = await self.collect_storage_metrics()
                
                all_metrics = network_metrics + storage_metrics
                
                # 存储指标
                await self.store_metrics(all_metrics)
                
                # 检查告警
                await self.check_alerts(all_metrics)
                
                # 等待下次收集
                await asyncio.sleep(self.collection_interval)
                
            except Exception as e:
                logger.error(f"Error in network storage monitoring loop: {e}")
                await asyncio.sleep(60)  # 出错时等待1分钟
    
    async def collect_network_metrics(self) -> List[NetworkMetric]:
        """收集网络指标"""
        metrics = []
        timestamp = datetime.now()
        
        try:
            # 网络接口指标
            interface_metrics = await self.collect_network_interface_metrics(timestamp)
            metrics.extend(interface_metrics)
            
            # 网络连接指标
            connection_metrics = await self.collect_network_connection_metrics(timestamp)
            metrics.extend(connection_metrics)
            
            # 网络延迟指标
            latency_metrics = await self.collect_network_latency_metrics(timestamp)
            metrics.extend(latency_metrics)
            
            # DNS解析指标
            dns_metrics = await self.collect_dns_metrics(timestamp)
            metrics.extend(dns_metrics)
            
        except Exception as e:
            logger.error(f"Error collecting network metrics: {e}")
        
        return metrics
    
    async def collect_network_interface_metrics(self, timestamp: datetime) -> List[NetworkMetric]:
        """收集网络接口指标"""
        metrics = []
        
        try:
            net_io = psutil.net_io_counters(pernic=True)
            net_if_addrs = psutil.net_if_addrs()
            net_if_stats = psutil.net_if_stats()
            
            for interface_name, io_stats in net_io.items():
                # 获取接口状态
                if_stats = net_if_stats.get(interface_name)
                if_addrs = net_if_addrs.get(interface_name, [])
                
                # 计算带宽使用（简化实现，基于历史数据）
                bytes_sent_per_sec = io_stats.bytes_sent / self.collection_interval
                bytes_recv_per_sec = io_stats.bytes_recv / self.collection_interval
                
                # 转换为Mbps
                bandwidth_sent_mbps = (bytes_sent_per_sec * 8) / (1024**2)
                bandwidth_recv_mbps = (bytes_recv_per_sec * 8) / (1024**2)
                total_bandwidth_mbps = bandwidth_sent_mbps + bandwidth_recv_mbps
                
                # 接口状态
                is_up = if_stats.isup if if_stats else False
                
                metrics.append(NetworkMetric(
                    timestamp=timestamp,
                    metric_type=NetworkMetricType.BANDWIDTH,
                    metric_name=f"interface_{interface_name}_bandwidth_sent_mbps",
                    value=bandwidth_sent_mbps,
                    unit="Mbps",
                    metadata={
                        "interface": interface_name,
                        "is_up": is_up,
                        "bytes_sent": io_stats.bytes_sent,
                        "packets_sent": io_stats.packets_sent
                    }
                ))
                
                metrics.append(NetworkMetric(
                    timestamp=timestamp,
                    metric_type=NetworkMetricType.BANDWIDTH,
                    metric_name=f"interface_{interface_name}_bandwidth_recv_mbps",
                    value=bandwidth_recv_mbps,
                    unit="Mbps",
                    metadata={
                        "interface": interface_name,
                        "is_up": is_up,
                        "bytes_recv": io_stats.bytes_recv,
                        "packets_recv": io_stats.packets_recv
                    }
                ))
                
                metrics.append(NetworkMetric(
                    timestamp=timestamp,
                    metric_type=NetworkMetricType.BANDWIDTH,
                    metric_name=f"interface_{interface_name}_total_bandwidth_mbps",
                    value=total_bandwidth_mbps,
                    unit="Mbps",
                    threshold_warning=self.thresholds["network"]["bandwidth_usage"]["warning"],
                    threshold_critical=self.thresholds["network"]["bandwidth_usage"]["critical"],
                    metadata={
                        "interface": interface_name,
                        "is_up": is_up,
                        "speed": if_stats.speed if if_stats else 0
                    }
                ))
                
                # 错误和丢包统计
                if io_stats.errin or io_stats.errout or io_stats.dropin or io_stats.dropout:
                    metrics.append(NetworkMetric(
                        timestamp=timestamp,
                        metric_type=NetworkMetricType.PACKET_LOSS,
                        metric_name=f"interface_{interface_name}_packet_errors",
                        value=io_stats.errin + io_stats.errout,
                        unit="count",
                        threshold_warning=10,
                        threshold_critical=100,
                        metadata={
                            "interface": interface_name,
                            "errors_in": io_stats.errin,
                            "errors_out": io_stats.errout
                        }
                    ))
                    
                    metrics.append(NetworkMetric(
                        timestamp=timestamp,
                        metric_type=NetworkMetricType.PACKET_LOSS,
                        metric_name=f"interface_{interface_name}_packet_drops",
                        value=io_stats.dropin + io_stats.dropout,
                        unit="count",
                        threshold_warning=10,
                        threshold_critical=100,
                        metadata={
                            "interface": interface_name,
                            "drops_in": io_stats.dropin,
                            "drops_out": io_stats.dropout
                        }
                    ))
        
        except Exception as e:
            logger.error(f"Error collecting network interface metrics: {e}")
        
        return metrics
    
    async def collect_network_connection_metrics(self, timestamp: datetime) -> List[NetworkMetric]:
        """收集网络连接指标"""
        metrics = []
        
        try:
            connections = psutil.net_connections()
            
            # 统计连接状态
            connection_stats = {
                "ESTABLISHED": 0,
                "LISTEN": 0,
                "TIME_WAIT": 0,
                "CLOSE_WAIT": 0,
                "other": 0
            }
            
            for conn in connections:
                status = conn.status
                if status in connection_stats:
                    connection_stats[status] += 1
                else:
                    connection_stats["other"] += 1
            
            total_connections = len(connections)
            established_connections = connection_stats["ESTABLISHED"]
            
            metrics.append(NetworkMetric(
                timestamp=timestamp,
                metric_type=NetworkMetricType.CONNECTION,
                metric_name="total_connections",
                value=total_connections,
                unit="count",
                threshold_warning=self.thresholds["network"]["connection_count"]["warning"],
                threshold_critical=self.thresholds["network"]["connection_count"]["critical"],
                metadata=connection_stats
            ))
            
            metrics.append(NetworkMetric(
                timestamp=timestamp,
                metric_type=NetworkMetricType.CONNECTION,
                metric_name="established_connections",
                value=established_connections,
                unit="count",
                threshold_warning=500,
                threshold_critical=1000,
                metadata={"total": total_connections}
            ))
        
        except Exception as e:
            logger.error(f"Error collecting network connection metrics: {e}")
        
        return metrics
    
    async def collect_network_latency_metrics(self, timestamp: datetime) -> List[NetworkMetric]:
        """收集网络延迟指标"""
        metrics = []
        
        try:
            # 对多个目标进行ping测试
            for target in self.monitor_targets["network"]:
                try:
                    latency_ms = await self.ping_host(target)
                    
                    metrics.append(NetworkMetric(
                        timestamp=timestamp,
                        metric_type=NetworkMetricType.LATENCY,
                        metric_name=f"latency_{target.replace('.', '_')}",
                        value=latency_ms,
                        unit="ms",
                        threshold_warning=self.thresholds["network"]["latency"]["warning"],
                        threshold_critical=self.thresholds["network"]["latency"]["critical"],
                        metadata={"target": target}
                    ))
                
                except Exception as e:
                    logger.warning(f"Failed to ping {target}: {e}")
                    metrics.append(NetworkMetric(
                        timestamp=timestamp,
                        metric_type=NetworkMetricType.LATENCY,
                        metric_name=f"latency_{target.replace('.', '_')}",
                        value=9999,  # 表示连接失败
                        unit="ms",
                        status=AlertLevel.CRITICAL,
                        metadata={"target": target, "error": str(e)}
                    ))
        
        except Exception as e:
            logger.error(f"Error collecting network latency metrics: {e}")
        
        return metrics
    
    async def collect_dns_metrics(self, timestamp: datetime) -> List[NetworkMetric]:
        """收集DNS解析指标"""
        metrics = []
        
        try:
            import dns.resolver
            
            for dns_server in self.monitor_targets["dns"]:
                try:
                    # 测试DNS解析时间
                    resolver = dns.resolver.Resolver()
                    resolver.nameservers = [dns_server]
                    resolver.timeout = 5
                    
                    start_time = time.time()
                    resolver.resolve('google.com', 'A')
                    dns_resolution_time = (time.time() - start_time) * 1000  # 转换为毫秒
                    
                    metrics.append(NetworkMetric(
                        timestamp=timestamp,
                        metric_type=NetworkMetricType.DNS,
                        metric_name=f"dns_resolution_time_{dns_server.replace('.', '_')}",
                        value=dns_resolution_time,
                        unit="ms",
                        threshold_warning=100,
                        threshold_critical=500,
                        metadata={"dns_server": dns_server}
                    ))
                
                except Exception as e:
                    logger.warning(f"DNS resolution failed for {dns_server}: {e}")
                    metrics.append(NetworkMetric(
                        timestamp=timestamp,
                        metric_type=NetworkMetricType.DNS,
                        metric_name=f"dns_resolution_time_{dns_server.replace('.', '_')}",
                        value=9999,  # 表示解析失败
                        unit="ms",
                        status=AlertLevel.CRITICAL,
                        metadata={"dns_server": dns_server, "error": str(e)}
                    ))
        
        except ImportError:
            logger.warning("dnspython not installed, skipping DNS metrics")
        except Exception as e:
            logger.error(f"Error collecting DNS metrics: {e}")
        
        return metrics
    
    async def collect_storage_metrics(self) -> List[StorageMetric]:
        """收集存储指标"""
        metrics = []
        timestamp = datetime.now()
        
        try:
            # 磁盘空间指标
            space_metrics = await self.collect_storage_space_metrics(timestamp)
            metrics.extend(space_metrics)
            
            # 磁盘I/O指标
            io_metrics = await self.collect_storage_io_metrics(timestamp)
            metrics.extend(io_metrics)
            
            # 存储性能指标
            performance_metrics = await self.collect_storage_performance_metrics(timestamp)
            metrics.extend(performance_metrics)
            
            # 存储健康指标
            health_metrics = await self.collect_storage_health_metrics(timestamp)
            metrics.extend(health_metrics)
            
        except Exception as e:
            logger.error(f"Error collecting storage metrics: {e}")
        
        return metrics
    
    async def collect_storage_space_metrics(self, timestamp: datetime) -> List[StorageMetric]:
        """收集存储空间指标"""
        metrics = []
        
        try:
            disk_partitions = psutil.disk_partitions()
            
            for partition in disk_partitions:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    
                    total_gb = usage.total / (1024**3)
                    used_gb = usage.used / (1024**3)
                    free_gb = usage.free / (1024**3)
                    usage_percent = (usage.used / usage.total) * 100
                    
                    metrics.append(StorageMetric(
                        timestamp=timestamp,
                        metric_type=StorageMetricType.SPACE,
                        metric_name=f"disk_usage_percent_{partition.device.replace('/', '_')}",
                        value=usage_percent,
                        unit="percent",
                        threshold_warning=self.thresholds["storage"]["disk_usage"]["warning"],
                        threshold_critical=self.thresholds["storage"]["disk_usage"]["critical"],
                        metadata={
                            "device": partition.device,
                            "mountpoint": partition.mountpoint,
                            "fstype": partition.fstype,
                            "total_gb": total_gb,
                            "used_gb": used_gb,
                            "free_gb": free_gb
                        }
                    ))
                    
                    metrics.append(StorageMetric(
                        timestamp=timestamp,
                        metric_type=StorageMetricType.SPACE,
                        metric_name=f"disk_free_gb_{partition.device.replace('/', '_')}",
                        value=free_gb,
                        unit="GB",
                        threshold_warning=10,  # 少于10GB警告
                        threshold_critical=5,   # 少于5GB严重
                        metadata={
                            "device": partition.device,
                            "mountpoint": partition.mountpoint,
                            "usage_percent": usage_percent
                        }
                    ))
                
                except Exception as e:
                    logger.warning(f"Error getting disk usage for {partition.mountpoint}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error collecting storage space metrics: {e}")
        
        return metrics
    
    async def collect_storage_io_metrics(self, timestamp: datetime) -> List[StorageMetric]:
        """收集存储I/O指标"""
        metrics = []
        
        try:
            disk_io = psutil.disk_io_counters(perdisk=True)
            
            for device_name, io_stats in disk_io.items():
                # 计算I/O吞吐量
                read_bytes_per_sec = io_stats.read_bytes / self.collection_interval
                write_bytes_per_sec = io_stats.write_bytes / self.collection_interval
                
                read_throughput_mb = read_bytes_per_sec / (1024**2)
                write_throughput_mb = write_bytes_per_sec / (1024**2)
                
                metrics.append(StorageMetric(
                    timestamp=timestamp,
                    metric_type=StorageMetricType.IO,
                    metric_name=f"disk_read_throughput_mb_{device_name}",
                    value=read_throughput_mb,
                    unit="MB/s",
                    threshold_warning=self.thresholds["storage"]["read_throughput"]["warning"],
                    threshold_critical=self.thresholds["storage"]["read_throughput"]["critical"],
                    metadata={
                        "device": device_name,
                        "read_bytes": io_stats.read_bytes,
                        "read_count": io_stats.read_count
                    }
                ))
                
                metrics.append(StorageMetric(
                    timestamp=timestamp,
                    metric_type=StorageMetricType.IO,
                    metric_name=f"disk_write_throughput_mb_{device_name}",
                    value=write_throughput_mb,
                    unit="MB/s",
                    threshold_warning=self.thresholds["storage"]["write_throughput"]["warning"],
                    threshold_critical=self.thresholds["storage"]["write_throughput"]["critical"],
                    metadata={
                        "device": device_name,
                        "write_bytes": io_stats.write_bytes,
                        "write_count": io_stats.write_count
                    }
                ))
                
                # I/O操作数
                metrics.append(StorageMetric(
                    timestamp=timestamp,
                    metric_type=StorageMetricType.IO,
                    metric_name=f"disk_read_ops_{device_name}",
                    value=io_stats.read_count,
                    unit="ops",
                    metadata={
                        "device": device_name,
                        "read_bytes": io_stats.read_bytes
                    }
                ))
                
                metrics.append(StorageMetric(
                    timestamp=timestamp,
                    metric_type=StorageMetricType.IO,
                    metric_name=f"disk_write_ops_{device_name}",
                    value=io_stats.write_count,
                    unit="ops",
                    metadata={
                        "device": device_name,
                        "write_bytes": io_stats.write_bytes
                    }
                ))
        
        except Exception as e:
            logger.error(f"Error collecting storage I/O metrics: {e}")
        
        return metrics
    
    async def collect_storage_performance_metrics(self, timestamp: datetime) -> List[StorageMetric]:
        """收集存储性能指标"""
        metrics = []
        
        try:
            # 系统I/O统计
            io_stats = psutil.disk_io_counters()
            
            if io_stats:
                # 计算I/O等待时间（简化实现）
                total_io_time = time.time()
                
                metrics.append(StorageMetric(
                    timestamp=timestamp,
                    metric_type=StorageMetricType.PERFORMANCE,
                    metric_name="total_disk_read_bytes",
                    value=io_stats.read_bytes,
                    unit="bytes",
                    metadata={
                        "read_count": io_stats.read_count,
                        "write_count": io_stats.write_count
                    }
                ))
                
                metrics.append(StorageMetric(
                    timestamp=timestamp,
                    metric_type=StorageMetricType.PERFORMANCE,
                    metric_name="total_disk_write_bytes",
                    value=io_stats.write_bytes,
                    unit="bytes",
                    metadata={
                        "read_count": io_stats.read_count,
                        "write_count": io_stats.write_count
                    }
                ))
        
        except Exception as e:
            logger.error(f"Error collecting storage performance metrics: {e}")
        
        return metrics
    
    async def collect_storage_health_metrics(self, timestamp: datetime) -> List[StorageMetric]:
        """收集存储健康指标"""
        metrics = []
        
        try:
            # 检查关键目录的可访问性
            critical_paths = ["/", "/tmp", "/var", "/home"]
            
            accessible_paths = 0
            for path in critical_paths:
                if Path(path).exists() and Path(path).is_dir():
                    try:
                        # 测试写入权限
                        test_file = Path(path) / ".monitoring_test"
                        test_file.touch()
                        test_file.unlink()
                        accessible_paths += 1
                    except PermissionError:
                        pass
                    except Exception:
                        pass
            
            accessibility_percent = (accessible_paths / len(critical_paths)) * 100
            
            metrics.append(StorageMetric(
                timestamp=timestamp,
                metric_type=StorageMetricType.HEALTH,
                metric_name="storage_accessibility_percent",
                value=accessibility_percent,
                unit="percent",
                threshold_warning=80,
                threshold_critical=60,
                metadata={
                    "accessible_paths": accessible_paths,
                    "total_paths": len(critical_paths)
                }
            ))
        
        except Exception as e:
            logger.error(f"Error collecting storage health metrics: {e}")
        
        return metrics
    
    async def ping_host(self, host: str, timeout: int = 5) -> float:
        """Ping主机并返回延迟（毫秒）"""
        try:
            # 使用subprocess调用ping命令
            if psutil.OS_NAME == "windows":
                cmd = ["ping", "-n", "1", "-w", str(timeout * 1000), host]
            else:
                cmd = ["ping", "-c", "1", "-W", str(timeout), host]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout + 2
            )
            
            if result.returncode == 0:
                # 解析ping结果获取延迟
                output = result.stdout
                if "time=" in output:
                    # 提取时间值
                    time_part = output.split("time=")[1].split()[0]
                    time_part = time_part.replace("ms", "")
                    return float(time_part)
            
            return 9999  # 表示ping失败
        
        except subprocess.TimeoutExpired:
            return 9999
        except Exception:
            return 9999
    
    async def store_metrics(self, metrics: List[Any]):
        """存储指标到Redis"""
        try:
            for metric in metrics:
                # 确定指标类型前缀
                if isinstance(metric, NetworkMetric):
                    prefix = "network_metric"
                    metric_type = metric.metric_type.value
                elif isinstance(metric, StorageMetric):
                    prefix = "storage_metric"
                    metric_type = metric.metric_type.value
                else:
                    continue
                
                # 存储最新值
                latest_key = f"{prefix}:latest:{metric_type}:{metric.metric_name}"
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
                history_key = f"{prefix}:history:{metric_type}:{metric.metric_name}"
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
            logger.error(f"Error storing network storage metrics: {e}")
    
    async def check_alerts(self, metrics: List[Any]):
        """检查告警条件"""
        try:
            for metric in metrics:
                if metric.status == AlertLevel.WARNING:
                    await self.create_alert(
                        metric,
                        AlertSeverity.WARNING,
                        f"Network/Storage {metric.metric_name} Warning",
                        f"{metric.metric_name} is {metric.value:.1f}{metric.unit}, exceeding warning threshold of {metric.threshold_warning}{metric.unit}"
                    )
                
                elif metric.status == AlertLevel.CRITICAL:
                    await self.create_alert(
                        metric,
                        AlertSeverity.CRITICAL,
                        f"Network/Storage {metric.metric_name} Critical",
                        f"{metric.metric_name} is {metric.value:.1f}{metric.unit}, exceeding critical threshold of {metric.threshold_critical}{metric.unit}"
                    )
        
        except Exception as e:
            logger.error(f"Error checking network storage alerts: {e}")
    
    async def create_alert(self, metric: Any, severity: AlertSeverity, title: str, description: str):
        """创建告警"""
        try:
            # 确定指标类型
            if isinstance(metric, NetworkMetric):
                source = "network_monitor"
                metric_type = metric.metric_type.value
            elif isinstance(metric, StorageMetric):
                source = "storage_monitor"
                metric_type = metric.metric_type.value
            else:
                return
            
            # 检查是否已经存在相同的活跃告警
            alert_key = f"{source}_alert:{metric_type}:{metric.metric_name}"
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
                source=source,
                service="web3search",
                environment=settings.ENVIRONMENT,
                labels={
                    "metric_type": metric_type,
                    "metric_name": metric.metric_name,
                    "hostname": socket.gethostname()
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
            
            logger.warning(f"Created network/storage alert: {title}")
        
        except Exception as e:
            logger.error(f"Error creating network/storage alert: {e}")
    
    async def get_current_metrics(self) -> Dict[str, Any]:
        """获取当前网络存储指标"""
        try:
            current_metrics = {}
            
            # 获取所有最新指标
            patterns = ["network_metric:latest:*", "storage_metric:latest:*"]
            
            for pattern in patterns:
                async for key in self.redis_client.scan_iter(match=pattern):
                    metric_data = await self.redis_client.get(key)
                    
                    if metric_data:
                        data = json.loads(metric_data)
                        metric_name = key.decode().split(":")[-1]
                        current_metrics[metric_name] = data
            
            return current_metrics
        
        except Exception as e:
            logger.error(f"Error getting current network storage metrics: {e}")
            return {}
    
    async def get_network_interfaces(self) -> List[NetworkInterface]:
        """获取网络接口信息"""
        try:
            interfaces = []
            
            net_io = psutil.net_io_counters(pernic=True)
            net_if_addrs = psutil.net_if_addrs()
            net_if_stats = psutil.net_if_stats()
            
            for interface_name, io_stats in net_io.items():
                if_stats = net_if_stats.get(interface_name)
                
                interface = NetworkInterface(
                    name=interface_name,
                    is_up=if_stats.isup if if_stats else False,
                    speed=if_stats.speed if if_stats else 0,
                    mtu=if_stats.mtu if if_stats else 0,
                    bytes_sent=io_stats.bytes_sent,
                    bytes_recv=io_stats.bytes_recv,
                    packets_sent=io_stats.packets_sent,
                    packets_recv=io_stats.packets_recv,
                    errors_in=io_stats.errin,
                    errors_out=io_stats.errout,
                    drops_in=io_stats.dropin,
                    drops_out=io_stats.dropout
                )
                
                interfaces.append(interface)
            
            return interfaces
        
        except Exception as e:
            logger.error(f"Error getting network interfaces: {e}")
            return []
    
    async def get_storage_devices(self) -> List[StorageDevice]:
        """获取存储设备信息"""
        try:
            devices = []
            
            disk_partitions = psutil.disk_partitions()
            disk_io = psutil.disk_io_counters(perdisk=True)
            
            for partition in disk_partitions:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    io_stats = disk_io.get(partition.device.replace('/dev/', ''), psutil.disk_io_counters())
                    
                    device = StorageDevice(
                        device=partition.device,
                        mountpoint=partition.mountpoint,
                        fstype=partition.fstype,
                        total_size=usage.total,
                        used_size=usage.used,
                        free_size=usage.free,
                        usage_percent=(usage.used / usage.total) * 100,
                        read_bytes=io_stats.read_bytes if io_stats else 0,
                        write_bytes=io_stats.write_bytes if io_stats else 0,
                        read_count=io_stats.read_count if io_stats else 0,
                        write_count=io_stats.write_count if io_stats else 0
                    )
                    
                    devices.append(device)
                
                except Exception as e:
                    logger.warning(f"Error getting storage device info for {partition.mountpoint}: {e}")
                    continue
            
            return devices
        
        except Exception as e:
            logger.error(f"Error getting storage devices: {e}")
            return []
    
    async def get_network_storage_summary(self) -> Dict[str, Any]:
        """获取网络存储监控摘要"""
        try:
            current_metrics = await self.get_current_metrics()
            
            summary = {
                "timestamp": datetime.now().isoformat(),
                "network": {
                    "interfaces": await self.get_network_interfaces(),
                    "metrics": {}
                },
                "storage": {
                    "devices": await self.get_storage_devices(),
                    "metrics": {}
                },
                "alerts": {
                    "warning": 0,
                    "critical": 0
                }
            }
            
            # 分类整理指标
            for metric_name, data in current_metrics.items():
                if metric_name.startswith("interface_") or metric_name.startswith("latency_") or metric_name.startswith("dns_"):
                    summary["network"]["metrics"][metric_name] = data
                elif metric_name.startswith("disk_") or metric_name.startswith("storage_"):
                    summary["storage"]["metrics"][metric_name] = data
                
                # 统计告警
                if data.get("status") == "warning":
                    summary["alerts"]["warning"] += 1
                elif data.get("status") == "critical":
                    summary["alerts"]["critical"] += 1
            
            return summary
        
        except Exception as e:
            logger.error(f"Error getting network storage summary: {e}")
            return {}


# 全局网络存储监控器实例
network_storage_monitor = NetworkStorageMonitor()
