"""
实时指标收集器
收集系统和应用指标，提供给告警系统使用
"""
import time
import psutil
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

from app.core.alerting import alert_manager
from app.core.monitoring import apm_collector
from app.core.redis_client import get_redis_client

logger = logging.getLogger(__name__)


class RealTimeMetricsCollector:
    """
    实时指标收集器
    定期收集系统、应用和业务指标
    """
    
    def __init__(self, collection_interval: int = 30):
        self.collection_interval = collection_interval
        self.running = False
        self.collection_task = None
        
        # 指标缓存
        self.api_metrics = {
            "response_times": [],
            "error_count": 0,
            "total_requests": 0,
            "status_codes": {}
        }
        
        self.db_metrics = {
            "connection_errors": 0,
            "query_times": [],
            "connection_pool_size": 0
        }
        
        self.external_api_metrics = {
            "requests": [],
            "errors": []
        }
        
        self.frontend_metrics = {
            "errors": [],
            "page_loads": []
        }
        
        self.system_metrics = {
            "cpu_usage": [],
            "memory_usage": [],
            "disk_usage": [],
            "network_io": []
        }
    
    async def start_collection(self):
        """开始指标收集"""
        if self.running:
            return
        
        self.running = True
        self.collection_task = asyncio.create_task(self._collection_loop())
        logger.info("Real-time metrics collection started")
    
    async def stop_collection(self):
        """停止指标收集"""
        self.running = False
        if self.collection_task:
            self.collection_task.cancel()
            try:
                await self.collection_task
            except asyncio.CancelledError:
                pass
        logger.info("Real-time metrics collection stopped")
    
    async def _collection_loop(self):
        """指标收集循环"""
        while self.running:
            try:
                await self._collect_all_metrics()
                await self._update_alert_manager()
                await asyncio.sleep(self.collection_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in metrics collection loop: {e}")
                await asyncio.sleep(5)  # 错误后短暂等待
    
    async def _collect_all_metrics(self):
        """收集所有指标"""
        await asyncio.gather(
            self._collect_system_metrics(),
            self._collect_api_metrics(),
            self._collect_database_metrics(),
            self._collect_redis_metrics(),
            self._collect_external_api_metrics(),
            return_exceptions=True
        )
    
    async def _collect_system_metrics(self):
        """收集系统指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            self.system_metrics["cpu_usage"].append(cpu_percent)
            if len(self.system_metrics["cpu_usage"]) > 60:
                self.system_metrics["cpu_usage"] = self.system_metrics["cpu_usage"][-60:]
            
            # 内存使用率
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            self.system_metrics["memory_usage"].append(memory_percent)
            if len(self.system_metrics["memory_usage"]) > 60:
                self.system_metrics["memory_usage"] = self.system_metrics["memory_usage"][-60:]
            
            # 磁盘使用率
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            self.system_metrics["disk_usage"].append(disk_percent)
            if len(self.system_metrics["disk_usage"]) > 60:
                self.system_metrics["disk_usage"] = self.system_metrics["disk_usage"][-60:]
            
            # 网络IO
            network = psutil.net_io_counters()
            network_io = {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv
            }
            self.system_metrics["network_io"].append(network_io)
            if len(self.system_metrics["network_io"]) > 60:
                self.system_metrics["network_io"] = self.system_metrics["network_io"][-60:]
            
            # 更新APM指标
            apm_collector.record_cpu_usage("system", cpu_percent, 1000)
            apm_collector.record_memory_usage("system", memory.total / (1024 * 1024), "total")
            apm_collector.record_memory_usage("system_used", memory.used / (1024 * 1024), "rss")
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
    
    async def _collect_api_metrics(self):
        """收集API指标"""
        try:
            # 这里应该从实际的API监控数据中获取
            # 暂时使用模拟数据
            current_time = time.time()
            
            # 模拟API响应时间数据
            if hasattr(self, '_last_api_response_time'):
                response_time = self._last_api_response_time
            else:
                response_time = 150 + (hash(str(current_time)) % 200)  # 150-350ms
                self._last_api_response_time = response_time
            
            self.api_metrics["response_times"].append(response_time)
            if len(self.api_metrics["response_times"]) > 100:
                self.api_metrics["response_times"] = self.api_metrics["response_times"][-100:]
            
            # 模拟请求数据
            self.api_metrics["total_requests"] += hash(str(current_time)) % 10
            
            # 模拟错误数据
            if hash(str(current_time)) % 50 == 0:  # 2%错误率
                self.api_metrics["error_count"] += 1
            
        except Exception as e:
            logger.error(f"Error collecting API metrics: {e}")
    
    async def _collect_database_metrics(self):
        """收集数据库指标"""
        try:
            # 这里应该从实际的数据库监控中获取
            # 暂时使用模拟数据
            
            # 模拟连接错误
            if hash(str(time.time())) % 200 == 0:  # 0.5%连接错误
                self.db_metrics["connection_errors"] += 1
            
            # 模拟查询时间
            query_time = 10 + (hash(str(time.time())) % 50)  # 10-60ms
            self.db_metrics["query_times"].append(query_time)
            if len(self.db_metrics["query_times"]) > 100:
                self.db_metrics["query_times"] = self.db_metrics["query_times"][-100:]
            
        except Exception as e:
            logger.error(f"Error collecting database metrics: {e}")
    
    async def _collect_redis_metrics(self):
        """收集Redis指标"""
        try:
            redis_client = get_redis_client()
            if redis_client:
                info = await redis_client.info()
                
                # Redis内存使用
                used_memory = info.get('used_memory', 0)
                max_memory = info.get('maxmemory', 0)
                
                if max_memory > 0:
                    memory_percent = (used_memory / max_memory) * 100
                    apm_collector.record_memory_usage("redis", used_memory / (1024 * 1024), "rss")
                
                # 连接数
                connected_clients = info.get('connected_clients', 0)
                
                # 命令统计
                total_commands_processed = info.get('total_commands_processed', 0)
                
                logger.debug(f"Redis metrics: memory={used_memory}, clients={connected_clients}, commands={total_commands_processed}")
                
        except Exception as e:
            logger.error(f"Error collecting Redis metrics: {e}")
    
    async def _collect_external_api_metrics(self):
        """收集外部API指标"""
        try:
            # 这里应该从实际的外部API调用中收集
            # 暂时使用模拟数据
            
            current_time = time.time()
            
            # 模拟外部API请求
            requests_count = hash(str(current_time)) % 20
            self.external_api_metrics["requests"].append(requests_count)
            
            # 模拟外部API错误
            if hash(str(current_time)) % 100 == 0:  # 1%错误率
                errors_count = 1
            else:
                errors_count = 0
            
            self.external_api_metrics["errors"].append(errors_count)
            
            # 保持最近100个数据点
            if len(self.external_api_metrics["requests"]) > 100:
                self.external_api_metrics["requests"] = self.external_api_metrics["requests"][-100:]
                self.external_api_metrics["errors"] = self.external_api_metrics["errors"][-100:]
            
        except Exception as e:
            logger.error(f"Error collecting external API metrics: {e}")
    
    async def _update_alert_manager(self):
        """更新告警管理器的指标"""
        try:
            # API响应时间P95
            if self.api_metrics["response_times"]:
                p95_response_time = self._percentile(self.api_metrics["response_times"], 95)
                alert_manager.update_metric("api_response_time", p95_response_time)
            
            # API错误率
            if self.api_metrics["total_requests"] > 0:
                error_rate = self.api_metrics["error_count"] / self.api_metrics["total_requests"]
                alert_manager.update_metric("api_error_rate", error_rate)
            
            # 数据库连接错误
            alert_manager.update_metric("db_connection_errors", self.db_metrics["connection_errors"])
            
            # 内存使用率
            if self.system_metrics["memory_usage"]:
                memory_usage = self.system_metrics["memory_usage"][-1]
                alert_manager.update_metric("memory_usage_percent", memory_usage)
            
            # CPU使用率
            if self.system_metrics["cpu_usage"]:
                cpu_usage = self.system_metrics["cpu_usage"][-1]
                alert_manager.update_metric("cpu_usage_percent", cpu_usage)
            
            # 外部API错误率
            if self.external_api_metrics["requests"] and sum(self.external_api_metrics["requests"]) > 0:
                total_requests = sum(self.external_api_metrics["requests"][-10:])
                total_errors = sum(self.external_api_metrics["errors"][-10:])
                external_error_rate = total_errors / total_requests if total_requests > 0 else 0
                alert_manager.update_metric("external_api_error_rate", external_error_rate)
            
            # 前端错误率（模拟数据）
            frontend_error_rate = 0.01 + (hash(str(time.time())) % 100) / 10000  # 1-2%
            alert_manager.update_metric("frontend_error_rate", frontend_error_rate)
            
        except Exception as e:
            logger.error(f"Error updating alert manager: {e}")
    
    def _percentile(self, values: List[float], percentile: int) -> float:
        """计算百分位数"""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def record_api_request(self, response_time: float, status_code: int):
        """记录API请求"""
        self.api_metrics["response_times"].append(response_time)
        if len(self.api_metrics["response_times"]) > 100:
            self.api_metrics["response_times"] = self.api_metrics["response_times"][-100:]
        
        self.api_metrics["total_requests"] += 1
        
        if status_code >= 400:
            self.api_metrics["error_count"] += 1
        
        # 记录状态码统计
        status_str = str(status_code)
        if status_str not in self.api_metrics["status_codes"]:
            self.api_metrics["status_codes"][status_str] = 0
        self.api_metrics["status_codes"][status_str] += 1
    
    def record_database_error(self):
        """记录数据库错误"""
        self.db_metrics["connection_errors"] += 1
    
    def record_external_api_request(self, success: bool):
        """记录外部API请求"""
        current_time = time.time()
        self.external_api_metrics["requests"].append(1)
        if not success:
            self.external_api_metrics["errors"].append(1)
        else:
            self.external_api_metrics["errors"].append(0)
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """获取指标摘要"""
        return {
            "api": {
                "avg_response_time": sum(self.api_metrics["response_times"]) / len(self.api_metrics["response_times"]) if self.api_metrics["response_times"] else 0,
                "p95_response_time": self._percentile(self.api_metrics["response_times"], 95),
                "error_rate": self.api_metrics["error_count"] / self.api_metrics["total_requests"] if self.api_metrics["total_requests"] > 0 else 0,
                "total_requests": self.api_metrics["total_requests"],
                "status_codes": self.api_metrics["status_codes"]
            },
            "database": {
                "connection_errors": self.db_metrics["connection_errors"],
                "avg_query_time": sum(self.db_metrics["query_times"]) / len(self.db_metrics["query_times"]) if self.db_metrics["query_times"] else 0
            },
            "system": {
                "cpu_usage": self.system_metrics["cpu_usage"][-1] if self.system_metrics["cpu_usage"] else 0,
                "memory_usage": self.system_metrics["memory_usage"][-1] if self.system_metrics["memory_usage"] else 0,
                "disk_usage": self.system_metrics["disk_usage"][-1] if self.system_metrics["disk_usage"] else 0
            },
            "external_api": {
                "total_requests": sum(self.external_api_metrics["requests"][-10:]),
                "total_errors": sum(self.external_api_metrics["errors"][-10:]),
                "error_rate": sum(self.external_api_metrics["errors"][-10:]) / sum(self.external_api_metrics["requests"][-10:]) if sum(self.external_api_metrics["requests"][-10:]) > 0 else 0
            }
        }


# 全局指标收集器实例
metrics_collector = RealTimeMetricsCollector()
