"""
简化的API响应时间监控和告警系统
不依赖外部库，专注核心监控功能
"""

import asyncio
import time
import json
import statistics
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict, deque
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    """告警严重程度"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class MetricType(Enum):
    """指标类型"""
    RESPONSE_TIME = "response_time"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"

@dataclass
class PerformanceMetric:
    """性能指标"""
    endpoint: str
    method: str
    metric_type: MetricType
    value: float
    timestamp: float
    status_code: Optional[int] = None
    extra_info: Dict[str, Any] = None  # Add this line

@dataclass
class AlertRule:
    """告警规则"""
    name: str
    metric_type: MetricType
    endpoint: Optional[str]
    threshold: float
    operator: str
    severity: AlertSeverity
    duration: int
    enabled: bool = True

@dataclass
class Alert:
    """告警"""
    id: str
    rule_name: str
    severity: AlertSeverity
    message: str
    endpoint: Optional[str]
    current_value: float
    threshold: float
    timestamp: float
    resolved: bool = False
    resolved_at: Optional[float] = None

class SimpleMetricsCollector:
    """简化的指标收集器"""
    
    def __init__(self, max_samples: int = 10000):
        self.metrics = deque(maxlen=max_samples)
        self.endpoint_metrics = defaultdict(lambda: deque(maxlen=1000))
        self.real_time_metrics = defaultdict(lambda: deque(maxlen=100))
        
    def collect_metric(self, metric: PerformanceMetric):
        """收集指标"""
        self.metrics.append(metric)
        
        # 按端点分组
        endpoint_key = f"{metric.method} {metric.endpoint}"
        self.endpoint_metrics[endpoint_key].append(metric)
        
        # 实时指标（最近5分钟）
        now = time.time()
        self.real_time_metrics[endpoint_key].append(metric)
        
        # 清理过期的实时指标
        cutoff_time = now - 300  # 5分钟
        while (self.real_time_metrics[endpoint_key] and 
               self.real_time_metrics[endpoint_key][0].timestamp < cutoff_time):
            self.real_time_metrics[endpoint_key].popleft()
    
    def get_real_time_stats(self, endpoint: str, method: str = "GET") -> Dict[str, float]:
        """获取实时统计"""
        key = f"{method} {endpoint}"
        recent_metrics = list(self.real_time_metrics[key])
        
        if not recent_metrics:
            return {}
        
        response_times = [m.value for m in recent_metrics if m.metric_type == MetricType.RESPONSE_TIME]
        error_metrics = [m for m in recent_metrics if m.status_code and m.status_code >= 400]
        
        stats = {}
        
        if response_times:
            stats.update({
                "avg_response_time": statistics.mean(response_times),
                "p95_response_time": self._percentile(response_times, 95),
                "p99_response_time": self._percentile(response_times, 99),
                "min_response_time": min(response_times),
                "max_response_time": max(response_times)
            })
        
        if recent_metrics:
            total_requests = len(recent_metrics)
            error_count = len(error_metrics)
            stats.update({
                "request_count": total_requests,
                "error_rate": error_count / total_requests if total_requests > 0 else 0,
                "throughput": total_requests / 300  # 每秒请求数
            })
        
        return stats
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """计算百分位数"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]

class SimpleAlertManager:
    """简化的告警管理器"""
    
    def __init__(self, metrics_collector: SimpleMetricsCollector):
        self.metrics_collector = metrics_collector
        self.alert_rules = []
        self.active_alerts = {}
        self.alert_history = deque(maxlen=1000)
        
    def add_alert_rule(self, rule: AlertRule):
        """添加告警规则"""
        self.alert_rules.append(rule)
        logger.info(f"Added alert rule: {rule.name}")
    
    def check_alerts(self):
        """检查告警"""
        for rule in self.alert_rules:
            if not rule.enabled:
                continue
            
            try:
                self._evaluate_rule(rule)
            except Exception as e:
                logger.error(f"Error evaluating alert rule {rule.name}: {e}")
    
    def _evaluate_rule(self, rule: AlertRule):
        """评估告警规则"""
        # 获取当前指标值
        current_value = self._get_current_metric_value(rule)
        if current_value is None:
            return
        
        # 检查阈值
        threshold_breached = self._check_threshold(current_value, rule)
        
        alert_id = f"{rule.name}_{rule.endpoint or 'all'}"
        
        if threshold_breached:
            if alert_id not in self.active_alerts:
                # 创建新告警
                alert = Alert(
                    id=alert_id,
                    rule_name=rule.name,
                    severity=rule.severity,
                    message=self._generate_alert_message(rule, current_value),
                    endpoint=rule.endpoint,
                    current_value=current_value,
                    threshold=rule.threshold,
                    timestamp=time.time()
                )
                
                self.active_alerts[alert_id] = alert
                self.alert_history.append(alert)
                
                logger.warning(f"🚨 Alert triggered: {alert.message}")
        
        else:
            if alert_id in self.active_alerts:
                # 解决告警
                alert = self.active_alerts[alert_id]
                alert.resolved = True
                alert.resolved_at = time.time()
                
                del self.active_alerts[alert_id]
                logger.info(f"✅ Alert resolved: {alert.message}")
    
    def _get_current_metric_value(self, rule: AlertRule) -> Optional[float]:
        """获取当前指标值"""
        if rule.endpoint:
            stats = self.metrics_collector.get_real_time_stats(rule.endpoint)
        else:
            # 全局统计
            stats = self._get_global_stats()
        
        if rule.metric_type == MetricType.RESPONSE_TIME:
            return stats.get("avg_response_time")
        elif rule.metric_type == MetricType.ERROR_RATE:
            return stats.get("error_rate", 0) * 100  # 转换为百分比
        elif rule.metric_type == MetricType.THROUGHPUT:
            return stats.get("throughput", 0)
        
        return None
    
    def _get_global_stats(self) -> Dict[str, float]:
        """获取全局统计"""
        all_metrics = list(self.metrics_collector.metrics)
        recent_metrics = [m for m in all_metrics if time.time() - m.timestamp < 300]
        
        if not recent_metrics:
            return {}
        
        response_times = [m.value for m in recent_metrics if m.metric_type == MetricType.RESPONSE_TIME]
        error_metrics = [m for m in recent_metrics if m.status_code and m.status_code >= 400]
        
        stats = {}
        if response_times:
            stats["avg_response_time"] = statistics.mean(response_times)
        
        if recent_metrics:
            total_requests = len(recent_metrics)
            error_count = len(error_metrics)
            stats["error_rate"] = error_count / total_requests if total_requests > 0 else 0
            stats["throughput"] = total_requests / 300
        
        return stats
    
    def _check_threshold(self, value: float, rule: AlertRule) -> bool:
        """检查阈值"""
        if rule.operator == ">":
            return value > rule.threshold
        elif rule.operator == "<":
            return value < rule.threshold
        elif rule.operator == ">=":
            return value >= rule.threshold
        elif rule.operator == "<=":
            return value <= rule.threshold
        elif rule.operator == "==":
            return abs(value - rule.threshold) < 0.001
        
        return False
    
    def _generate_alert_message(self, rule: AlertRule, current_value: float) -> str:
        """生成告警消息"""
        endpoint_str = f" for {rule.endpoint}" if rule.endpoint else ""
        
        if rule.metric_type == MetricType.RESPONSE_TIME:
            return f"Response time{endpoint_str} is {current_value:.0f}ms (threshold: {rule.threshold:.0f}ms)"
        elif rule.metric_type == MetricType.ERROR_RATE:
            return f"Error rate{endpoint_str} is {current_value:.1f}% (threshold: {rule.threshold:.1f}%)"
        elif rule.metric_type == MetricType.THROUGHPUT:
            return f"Throughput{endpoint_str} is {current_value:.1f} RPS (threshold: {rule.threshold:.1f} RPS)"
        
        return f"Metric {rule.metric_type.value}{endpoint_str} breached threshold: {current_value} {rule.operator} {rule.threshold}"

class SimplePerformanceMonitor:
    """简化的性能监控器"""
    
    def __init__(self):
        self.metrics_collector = SimpleMetricsCollector()
        self.alert_manager = SimpleAlertManager(self.metrics_collector)
        self.monitoring_enabled = False
        self.monitoring_task = None
        self.endpoints = self._define_monitored_endpoints()
        
    def _define_monitored_endpoints(self) -> List[Dict[str, Any]]:
        """定义监控的端点"""
        return [
            {
                "path": "/api/v1/chat/quick-chat",
                "method": "POST",
                "target_response_time": 3000,  # 3秒
                "target_error_rate": 1.0,      # 1%
                "target_throughput": 10        # 10 RPS
            },
            {
                "path": "/api/v1/chat/deep-research", 
                "method": "POST",
                "target_response_time": 60000, # 60秒
                "target_error_rate": 5.0,      # 5%
                "target_throughput": 2         # 2 RPS
            },
            {
                "path": "/api/v1/search/autocomplete",
                "method": "GET",
                "target_response_time": 500,   # 0.5秒
                "target_error_rate": 0.5,      # 0.5%
                "target_throughput": 50        # 50 RPS
            },
            {
                "path": "/api/v1/trending/hotspots",
                "method": "GET", 
                "target_response_time": 1000,  # 1秒
                "target_error_rate": 1.0,      # 1%
                "target_throughput": 20        # 20 RPS
            }
        ]
    
    def setup_default_alert_rules(self):
        """设置默认告警规则"""
        for endpoint in self.endpoints:
            # 响应时间告警
            self.alert_manager.add_alert_rule(AlertRule(
                name=f"{endpoint['path']} response time",
                metric_type=MetricType.RESPONSE_TIME,
                endpoint=endpoint['path'],
                threshold=endpoint['target_response_time'],
                operator=">",
                severity=AlertSeverity.WARNING,
                duration=300
            ))
            
            # 错误率告警
            self.alert_manager.add_alert_rule(AlertRule(
                name=f"{endpoint['path']} error rate",
                metric_type=MetricType.ERROR_RATE,
                endpoint=endpoint['path'],
                threshold=endpoint['target_error_rate'],
                operator=">",
                severity=AlertSeverity.CRITICAL,
                duration=60
            ))
            
            # 吞吐量告警
            self.alert_manager.add_alert_rule(AlertRule(
                name=f"{endpoint['path']} low throughput",
                metric_type=MetricType.THROUGHPUT,
                endpoint=endpoint['path'],
                threshold=endpoint['target_throughput'] * 0.5,
                operator="<",
                severity=AlertSeverity.WARNING,
                duration=600
            ))
    
    async def start_monitoring(self):
        """启动监控"""
        if self.monitoring_enabled:
            logger.warning("Monitoring is already enabled")
            return
        
        self.monitoring_enabled = True
        self.setup_default_alert_rules()
        
        # 启动监控任务
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        logger.info("✅ Performance monitoring started")
    
    async def stop_monitoring(self):
        """停止监控"""
        self.monitoring_enabled = False
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("⏹️ Performance monitoring stopped")
    
    async def _monitoring_loop(self):
        """监控循环"""
        while self.monitoring_enabled:
            try:
                # 检查告警
                self.alert_manager.check_alerts()
                
                # 等待下次检查
                await asyncio.sleep(10)  # 10秒检查一次
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)
    
    def record_api_call(self, endpoint: str, method: str, response_time: float, 
                       status_code: int):
        """记录API调用"""
        metric = PerformanceMetric(
            endpoint=endpoint,
            method=method,
            metric_type=MetricType.RESPONSE_TIME,
            value=response_time,
            timestamp=time.time(),
            status_code=status_code
        )
        
        self.metrics_collector.collect_metric(metric)
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """获取仪表板数据"""
        dashboard_data = {
            "timestamp": time.time(),
            "endpoints": [],
            "active_alerts": len(self.alert_manager.active_alerts),
            "recent_alerts": [asdict(alert) for alert in list(self.alert_manager.alert_history)[-10:]],
            "system_health": self._calculate_system_health()
        }
        
        for endpoint in self.endpoints:
            stats = self.metrics_collector.get_real_time_stats(endpoint['path'], endpoint['method'])
            
            endpoint_data = {
                "path": endpoint['path'],
                "method": endpoint['method'],
                "targets": {
                    "response_time": endpoint['target_response_time'],
                    "error_rate": endpoint['target_error_rate'],
                    "throughput": endpoint['target_throughput']
                },
                "current_stats": stats,
                "status": self._calculate_endpoint_status(stats, endpoint)
            }
            
            dashboard_data["endpoints"].append(endpoint_data)
        
        return dashboard_data
    
    def _calculate_endpoint_status(self, stats: Dict[str, float], endpoint: Dict[str, Any]) -> str:
        """计算端点状态"""
        if not stats:
            return "unknown"
        
        # 检查响应时间
        avg_time = stats.get("avg_response_time", 0)
        if avg_time > endpoint['target_response_time'] * 2:
            return "critical"
        elif avg_time > endpoint['target_response_time']:
            return "warning"
        
        # 检查错误率
        error_rate = stats.get("error_rate", 0) * 100
        if error_rate > endpoint['target_error_rate'] * 2:
            return "critical"
        elif error_rate > endpoint['target_error_rate']:
            return "warning"
        
        # 检查吞吐量
        throughput = stats.get("throughput", 0)
        if throughput < endpoint['target_throughput'] * 0.25:
            return "warning"
        
        return "healthy"
    
    def _calculate_system_health(self) -> str:
        """计算系统健康状态"""
        if not self.alert_manager.active_alerts:
            return "healthy"
        
        critical_alerts = [
            alert for alert in self.alert_manager.active_alerts.values()
            if alert.severity in [AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY]
        ]
        
        if critical_alerts:
            return "critical"
        
        warning_alerts = [
            alert for alert in self.alert_manager.active_alerts.values()
            if alert.severity == AlertSeverity.WARNING
        ]
        
        if warning_alerts:
            return "warning"
        
        return "degraded"

# 监控中间件示例
class SimpleMonitoringMiddleware:
    """简化的监控中间件"""
    
    def __init__(self, monitor: SimplePerformanceMonitor):
        self.monitor = monitor
    
    async def process_request(self, endpoint: str, method: str, response_time: float, status_code: int):
        """处理请求监控"""
        self.monitor.record_api_call(endpoint, method, response_time, status_code)

async def main():
    """主函数 - 演示性能监控系统"""
    print("🚀 Starting Simple API Response Time Monitoring and Alerting System...")
    
    # 创建性能监控器
    monitor = SimplePerformanceMonitor()
    
    # 启动监控
    await monitor.start_monitoring()
    
    # 模拟API调用数据
    print("\n📊 Simulating API calls...")
    
    endpoints = [
        ("/api/v1/chat/quick-chat", "POST"),
        ("/api/v1/chat/deep-research", "POST"),
        ("/api/v1/search/autocomplete", "GET"),
        ("/api/v1/trending/hotspots", "GET")
    ]
    
    # 模拟正常的API调用
    for i in range(100):
        for endpoint, method in endpoints:
            # 模拟不同的响应时间
            if "quick-chat" in endpoint:
                response_time = 2000 + (hash(endpoint + str(i)) % 3000)  # 2-5秒
            elif "deep-research" in endpoint:
                response_time = 30000 + (hash(endpoint + str(i)) % 40000)  # 30-70秒
            elif "autocomplete" in endpoint:
                response_time = 200 + (hash(endpoint + str(i)) % 400)  # 200-600ms
            else:
                response_time = 500 + (hash(endpoint + str(i)) % 1000)  # 500-1500ms
            
            status_code = 200 if hash(endpoint + str(i)) % 20 != 0 else 500  # 5%错误率
            
            monitor.record_api_call(endpoint, method, response_time, status_code)
        
        await asyncio.sleep(0.05)
    
    # 模拟一些性能问题触发告警
    print("\n⚠️ Simulating performance issues...")
    
    # 模拟响应时间过长
    for _ in range(10):
        monitor.record_api_call("/api/v1/chat/quick-chat", "POST", 5000, 200)
        await asyncio.sleep(0.1)
    
    # 模拟高错误率
    for _ in range(8):
        monitor.record_api_call("/api/v1/search/autocomplete", "GET", 300, 500)
        await asyncio.sleep(0.1)
    
    # 模拟低吞吐量
    for _ in range(3):
        monitor.record_api_call("/api/v1/trending/hotspots", "GET", 800, 200)
        await asyncio.sleep(2)
    
    # 等待告警检测
    await asyncio.sleep(5)
    
    # 获取仪表板数据
    dashboard_data = monitor.get_dashboard_data()
    
    print("\n📈 Performance Dashboard:")
    print(f"System Health: {dashboard_data['system_health']}")
    print(f"Active Alerts: {dashboard_data['active_alerts']}")
    
    for endpoint_data in dashboard_data["endpoints"]:
        print(f"\n{endpoint_data['method']} {endpoint_data['path']}:")
        print(f"  Status: {endpoint_data['status']}")
        print(f"  Response Time: {endpoint_data['current_stats'].get('avg_response_time', 0):.0f}ms")
        print(f"  Error Rate: {endpoint_data['current_stats'].get('error_rate', 0)*100:.1f}%")
        print(f"  Throughput: {endpoint_data['current_stats'].get('throughput', 0):.1f} RPS")
        
        # 显示目标对比
        targets = endpoint_data['targets']
        current = endpoint_data['current_stats']
        print(f"  Targets vs Current:")
        print(f"    Response Time: ≤{targets['response_time']}ms vs {current.get('avg_response_time', 0):.0f}ms")
        print(f"    Error Rate: ≤{targets['error_rate']}% vs {current.get('error_rate', 0)*100:.1f}%")
        print(f"    Throughput: ≥{targets['throughput']} RPS vs {current.get('throughput', 0):.1f} RPS")
    
    if dashboard_data["recent_alerts"]:
        print("\n🚨 Recent Alerts:")
        for alert in dashboard_data["recent_alerts"][-5:]:
            status = "RESOLVED" if alert['resolved'] else "ACTIVE"
            severity = alert['severity'].value.upper() if hasattr(alert['severity'], 'value') else str(alert['severity']).upper()
            print(f"  • [{status}] {severity}: {alert['message']}")
    
    # 生成监控报告
    monitoring_report = {
        "monitoring_summary": {
            "monitored_endpoints": len(monitor.endpoints),
            "active_alerts": dashboard_data['active_alerts'],
            "system_health": dashboard_data['system_health'],
            "monitoring_duration": "5 minutes simulation"
        },
        "endpoint_performance": dashboard_data["endpoints"],
        "alert_rules_config": [
            {
                "name": rule.name,
                "metric_type": rule.metric_type.value,
                "endpoint": rule.endpoint,
                "threshold": rule.threshold,
                "severity": rule.severity.value
            }
            for rule in monitor.alert_manager.alert_rules
        ],
        "recommendations": [
            "Investigate Quick Chat response time issues",
            "Fix Autocomplete error rate spikes", 
            "Optimize Trending endpoint throughput",
            "Set up automated alert notifications"
        ]
    }
    
    # 保存监控配置
    with open("api_monitoring_report.json", "w") as f:
        json.dump(monitoring_report, f, indent=2, default=str)
    
    # 停止监控
    await monitor.stop_monitoring()
    
    print(f"\n✅ Simple API Response Time Monitoring and Alerting System completed!")
    print("📁 Monitoring report saved to: api_monitoring_report.json")
    
    return monitor

if __name__ == "__main__":
    asyncio.run(main())
