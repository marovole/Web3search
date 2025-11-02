"""
性能回归检测和告警系统
自动检测性能指标回归，发送多渠道告警，生成回归分析报告
"""

import json
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from datetime import datetime, timedelta
import statistics
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import threading

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    """告警严重程度"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class RegressionType(Enum):
    """回归类型"""
    PERFORMANCE_DEGRADATION = "performance_degradation"
    ERROR_RATE_INCREASE = "error_rate_increase"
    THROUGHPUT_DECREASE = "throughput_decrease"
    AVAILABILITY_DROP = "availability_drop"
    BUNDLE_SIZE_INCREASE = "bundle_size_increase"
    CORE_WEB_VITALS_REGRESSION = "core_web_vitals_regression"

class AlertChannel(Enum):
    """告警渠道"""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    DASHBOARD = "dashboard"
    PAGERDUTY = "pagerduty"

@dataclass
class PerformanceThreshold:
    """性能阈值配置"""
    metric_name: str
    warning_threshold: float
    critical_threshold: float
    regression_threshold: float  # 回归检测阈值（百分比变化）
    comparison_window: int  # 比较窗口（小时）
    min_samples: int  # 最小样本数

@dataclass
class RegressionAlert:
    """回归告警"""
    id: str
    regression_type: RegressionType
    severity: AlertSeverity
    title: str
    description: str
    metric_name: str
    current_value: float
    baseline_value: float
    regression_percentage: float
    timestamp: datetime
    affected_endpoints: List[str]
    recommended_actions: List[str]

@dataclass
class AlertNotification:
    """告警通知"""
    alert_id: str
    channel: AlertChannel
    recipient: str
    status: str  # pending, sent, failed
    sent_at: Optional[datetime]
    error_message: Optional[str]

class PerformanceBaselineManager:
    """性能基线管理器"""
    
    def __init__(self):
        self.baselines = {}
        self.baseline_history = {}
        
    def establish_baseline(self, metric_name: str, values: List[float], 
                          timestamp: datetime = None) -> Dict[str, float]:
        """建立性能基线"""
        if not values:
            raise ValueError("Cannot establish baseline with empty values")
            
        if timestamp is None:
            timestamp = datetime.now()
            
        baseline = {
            "metric_name": metric_name,
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "p95": self._percentile(values, 95),
            "p99": self._percentile(values, 99),
            "min": min(values),
            "max": max(values),
            "std_dev": statistics.stdev(values) if len(values) > 1 else 0,
            "sample_count": len(values),
            "established_at": timestamp.isoformat()
        }
        
        self.baselines[metric_name] = baseline
        
        # 记录基线历史
        if metric_name not in self.baseline_history:
            self.baseline_history[metric_name] = []
        self.baseline_history[metric_name].append(baseline)
        
        print(f"📊 Baseline established for {metric_name}:")
        print(f"  • Mean: {baseline['mean']:.2f}")
        print(f"  • P95: {baseline['p95']:.2f}")
        print(f"  • P99: {baseline['p99']:.2f}")
        print(f"  • Samples: {baseline['sample_count']}")
        
        return baseline
    
    def get_baseline(self, metric_name: str) -> Optional[Dict[str, float]]:
        """获取性能基线"""
        return self.baselines.get(metric_name)
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """计算百分位数"""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]

class RegressionDetector:
    """回归检测器"""
    
    def __init__(self, baseline_manager: PerformanceBaselineManager):
        self.baseline_manager = baseline_manager
        self.detection_history = []
        
    def detect_regression(self, metric_name: str, current_values: List[float],
                         threshold: PerformanceThreshold) -> Optional[RegressionAlert]:
        """检测性能回归"""
        if len(current_values) < threshold.min_samples:
            return None
            
        baseline = self.baseline_manager.get_baseline(metric_name)
        if not baseline:
            return None
            
        current_mean = statistics.mean(current_values)
        baseline_mean = baseline["mean"]
        
        # 计算回归百分比
        if baseline_mean == 0:
            regression_percentage = 0
        else:
            regression_percentage = ((current_mean - baseline_mean) / baseline_mean) * 100
        
        # 检查是否超过回归阈值
        if abs(regression_percentage) < threshold.regression_threshold:
            return None
            
        # 确定严重程度
        severity = self._determine_severity(current_mean, threshold, regression_percentage)
        
        # 确定回归类型
        regression_type = self._determine_regression_type(metric_name, regression_percentage)
        
        # 生成告警
        alert = RegressionAlert(
            id=f"regression_{metric_name}_{int(time.time())}",
            regression_type=regression_type,
            severity=severity,
            title=f"Performance Regression Detected: {metric_name}",
            description=self._generate_description(metric_name, regression_percentage, current_mean, baseline_mean),
            metric_name=metric_name,
            current_value=current_mean,
            baseline_value=baseline_mean,
            regression_percentage=regression_percentage,
            timestamp=datetime.now(),
            affected_endpoints=self._get_affected_endpoints(metric_name),
            recommended_actions=self._generate_recommendations(regression_type, regression_percentage)
        )
        
        self.detection_history.append(alert)
        print(f"🚨 Regression detected for {metric_name}: {regression_percentage:+.1f}% ({severity.value})")
        
        return alert
    
    def _determine_severity(self, current_value: float, threshold: PerformanceThreshold, 
                           regression_percentage: float) -> AlertSeverity:
        """确定告警严重程度"""
        if current_value >= threshold.critical_threshold:
            return AlertSeverity.CRITICAL
        elif current_value >= threshold.warning_threshold:
            return AlertSeverity.ERROR
        elif abs(regression_percentage) >= threshold.regression_threshold * 2:
            return AlertSeverity.WARNING
        else:
            return AlertSeverity.INFO
    
    def _determine_regression_type(self, metric_name: str, regression_percentage: float) -> RegressionType:
        """确定回归类型"""
        if "response_time" in metric_name or "load_time" in metric_name:
            return RegressionType.PERFORMANCE_DEGRADATION
        elif "error_rate" in metric_name:
            return RegressionType.ERROR_RATE_INCREASE
        elif "throughput" in metric_name:
            return RegressionType.THROUGHPUT_DECREASE
        elif "uptime" in metric_name or "availability" in metric_name:
            return RegressionType.AVAILABILITY_DROP
        elif "bundle_size" in metric_name:
            return RegressionType.BUNDLE_SIZE_INCREASE
        elif "web_vitals" in metric_name or "cwv" in metric_name:
            return RegressionType.CORE_WEB_VITALS_REGRESSION
        else:
            return RegressionType.PERFORMANCE_DEGRADATION
    
    def _generate_description(self, metric_name: str, regression_percentage: float,
                             current_value: float, baseline_value: float) -> str:
        """生成告警描述"""
        direction = "increased" if regression_percentage > 0 else "decreased"
        return f"{metric_name} has {direction} by {abs(regression_percentage):.1f}% from baseline ({baseline_value:.2f} → {current_value:.2f})"
    
    def _get_affected_endpoints(self, metric_name: str) -> List[str]:
        """获取受影响的端点"""
        endpoint_mapping = {
            "api_response_time": ["/api/search", "/api/chat", "/api/analyze"],
            "page_load_time": ["/", "/search", "/dashboard"],
            "error_rate": ["/api/*"],
            "core_web_vitals_score": ["/*"],
            "throughput": ["/api/*"]
        }
        return endpoint_mapping.get(metric_name, ["unknown"])
    
    def _generate_recommendations(self, regression_type: RegressionType, 
                                 regression_percentage: float) -> List[str]:
        """生成修复建议"""
        recommendations = {
            RegressionType.PERFORMANCE_DEGRADATION: [
                "Check for recent code changes",
                "Review database query performance",
                "Monitor server resource utilization",
                "Analyze network latency"
            ],
            RegressionType.ERROR_RATE_INCREASE: [
                "Review application logs",
                "Check for recent deployment issues",
                "Verify external service dependencies",
                "Monitor system health metrics"
            ],
            RegressionType.THROUGHPUT_DECREASE: [
                "Check server capacity",
                "Review load balancer configuration",
                "Monitor concurrent user limits",
                "Analyze bottleneck resources"
            ],
            RegressionType.AVAILABILITY_DROP: [
                "Check service health endpoints",
                "Review infrastructure status",
                "Monitor network connectivity",
                "Verify deployment pipeline"
            ],
            RegressionType.BUNDLE_SIZE_INCREASE: [
                "Analyze bundle composition",
                "Review recent dependency changes",
                "Check for unused imports",
                "Optimize asset compression"
            ],
            RegressionType.CORE_WEB_VITALS_REGRESSION: [
                "Review recent frontend changes",
                "Check for layout shifts",
                "Optimize image loading",
                "Review JavaScript execution time"
            ]
        }
        
        base_recommendations = recommendations.get(regression_type, ["Investigate performance metrics"])
        
        if abs(regression_percentage) > 50:
            base_recommendations.insert(0, "URGENT: Critical regression detected - immediate attention required")
        elif abs(regression_percentage) > 25:
            base_recommendations.insert(0, "HIGH: Significant regression - prioritize investigation")
        
        return base_recommendations

class AlertNotificationService:
    """告警通知服务"""
    
    def __init__(self):
        self.notification_config = {}
        self.notification_history = []
        
    def configure_channel(self, channel: AlertChannel, config: Dict[str, Any]):
        """配置通知渠道"""
        self.notification_config[channel] = config
        print(f"🔧 Configured {channel.value} notification channel")
    
    def send_alert(self, alert: RegressionAlert, channels: List[AlertChannel]) -> List[AlertNotification]:
        """发送告警到多个渠道"""
        notifications = []
        
        for channel in channels:
            if channel not in self.notification_config:
                print(f"⚠️ Channel {channel.value} not configured")
                continue
                
            notification = AlertNotification(
                alert_id=alert.id,
                channel=channel,
                recipient=self.notification_config[channel].get("recipient", "default"),
                status="pending",
                sent_at=None,
                error_message=None
            )
            
            try:
                if channel == AlertChannel.EMAIL:
                    self._send_email_alert(alert, notification)
                elif channel == AlertChannel.SLACK:
                    self._send_slack_alert(alert, notification)
                elif channel == AlertChannel.WEBHOOK:
                    self._send_webhook_alert(alert, notification)
                elif channel == AlertChannel.DASHBOARD:
                    self._send_dashboard_alert(alert, notification)
                elif channel == AlertChannel.PAGERDUTY:
                    self._send_pagerduty_alert(alert, notification)
                    
                notification.status = "sent"
                notification.sent_at = datetime.now()
                print(f"✅ Alert sent via {channel.value}")
                
            except Exception as e:
                notification.status = "failed"
                notification.error_message = str(e)
                print(f"❌ Failed to send alert via {channel.value}: {e}")
            
            notifications.append(notification)
            self.notification_history.append(notification)
        
        return notifications
    
    def _send_email_alert(self, alert: RegressionAlert, notification: AlertNotification):
        """发送邮件告警"""
        config = self.notification_config[AlertChannel.EMAIL]
        
        subject = f"[{alert.severity.value.upper()}] {alert.title}"
        
        body = f"""
Performance Regression Alert

Severity: {alert.severity.value.upper()}
Metric: {alert.metric_name}
Regression: {alert.regression_percentage:+.1f}%
Current Value: {alert.current_value:.2f}
Baseline Value: {alert.baseline_value:.2f}
Timestamp: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

Description:
{alert.description}

Affected Endpoints:
{chr(10).join(f"• {endpoint}" for endpoint in alert.affected_endpoints)}

Recommended Actions:
{chr(10).join(f"• {action}" for action in alert.recommended_actions)}

---
This is an automated alert from Web3search Performance Monitoring System
        """
        
        # 模拟邮件发送（实际实现需要真实的SMTP配置）
        print(f"📧 Email alert prepared: {subject}")
        print(f"   Recipient: {config.get('recipient', 'N/A')}")
        print(f"   Body length: {len(body)} characters")
    
    def _send_slack_alert(self, alert: RegressionAlert, notification: AlertNotification):
        """发送Slack告警"""
        config = self.notification_config[AlertChannel.SLACK]
        
        color = {
            AlertSeverity.INFO: "good",
            AlertSeverity.WARNING: "warning",
            AlertSeverity.ERROR: "danger",
            AlertSeverity.CRITICAL: "#8B0000"
        }.get(alert.severity, "good")
        
        payload = {
            "attachments": [
                {
                    "color": color,
                    "title": alert.title,
                    "text": alert.description,
                    "fields": [
                        {
                            "title": "Metric",
                            "value": alert.metric_name,
                            "short": True
                        },
                        {
                            "title": "Regression",
                            "value": f"{alert.regression_percentage:+.1f}%",
                            "short": True
                        },
                        {
                            "title": "Current Value",
                            "value": f"{alert.current_value:.2f}",
                            "short": True
                        },
                        {
                            "title": "Baseline Value",
                            "value": f"{alert.baseline_value:.2f}",
                            "short": True
                        }
                    ],
                    "footer": "Web3search Performance Monitor",
                    "ts": int(alert.timestamp.timestamp())
                }
            ]
        }
        
        # 模拟Slack发送（实际实现需要真实的Webhook URL）
        print(f"💬 Slack alert prepared for {config.get('webhook_url', 'N/A')}")
        print(f"   Color: {color}, Severity: {alert.severity.value}")
    
    def _send_webhook_alert(self, alert: RegressionAlert, notification: AlertNotification):
        """发送Webhook告警"""
        config = self.notification_config[AlertChannel.WEBHOOK]
        
        payload = {
            "alert_id": alert.id,
            "type": "performance_regression",
            "severity": alert.severity.value,
            "title": alert.title,
            "description": alert.description,
            "metric": alert.metric_name,
            "regression_percentage": alert.regression_percentage,
            "current_value": alert.current_value,
            "baseline_value": alert.baseline_value,
            "timestamp": alert.timestamp.isoformat(),
            "affected_endpoints": alert.affected_endpoints,
            "recommended_actions": alert.recommended_actions
        }
        
        # 模拟Webhook发送（实际实现需要真实的URL）
        print(f"🔗 Webhook alert prepared for {config.get('url', 'N/A')}")
        print(f"   Payload size: {len(json.dumps(payload))} bytes")
    
    def _send_dashboard_alert(self, alert: RegressionAlert, notification: AlertNotification):
        """发送Dashboard告警"""
        # Dashboard告警通常是内部状态更新
        print(f"📊 Dashboard alert updated for alert {alert.id}")
        print(f"   Severity: {alert.severity.value}, Regression: {alert.regression_percentage:+.1f}%")
    
    def _send_pagerDuty_alert(self, alert: RegressionAlert, notification: AlertNotification):
        """发送PagerDuty告警"""
        config = self.notification_config[AlertChannel.PAGERDUTY]
        
        if alert.severity in [AlertSeverity.ERROR, AlertSeverity.CRITICAL]:
            payload = {
                "routing_key": config.get("integration_key", "dummy_key"),
                "event_action": "trigger",
                "payload": {
                    "summary": alert.title,
                    "source": "web3search-performance-monitor",
                    "severity": "critical" if alert.severity == AlertSeverity.CRITICAL else "error",
                    "timestamp": alert.timestamp.isoformat(),
                    "component": alert.metric_name,
                    "custom_details": {
                        "regression_percentage": alert.regression_percentage,
                        "current_value": alert.current_value,
                        "baseline_value": alert.baseline_value,
                        "description": alert.description
                    }
                }
            }
            
            # 模拟PagerDuty发送（实际实现需要真实的集成密钥）
            print(f"🚨 PagerDuty alert prepared for {alert.metric_name}")
            print(f"   Severity: {alert.severity.value}, Integration: {config.get('integration_key', 'N/A')[:8]}...")

class PerformanceRegressionMonitor:
    """性能回归监控主系统"""
    
    def __init__(self):
        self.baseline_manager = PerformanceBaselineManager()
        self.regression_detector = RegressionDetector(self.baseline_manager)
        self.alert_service = AlertNotificationService()
        self.thresholds = {}
        self.monitoring_active = False
        self.monitoring_thread = None
        
        # 初始化默认阈值
        self._initialize_default_thresholds()
        
        # 配置默认通知渠道
        self._configure_default_channels()
    
    def _initialize_default_thresholds(self):
        """初始化默认性能阈值"""
        self.thresholds = {
            "page_load_time": PerformanceThreshold(
                metric_name="page_load_time",
                warning_threshold=3.0,
                critical_threshold=5.0,
                regression_threshold=15.0,
                comparison_window=24,
                min_samples=10
            ),
            "api_response_time": PerformanceThreshold(
                metric_name="api_response_time",
                warning_threshold=1000,
                critical_threshold=2000,
                regression_threshold=20.0,
                comparison_window=12,
                min_samples=20
            ),
            "error_rate": PerformanceThreshold(
                metric_name="error_rate",
                warning_threshold=1.0,
                critical_threshold=5.0,
                regression_threshold=50.0,
                comparison_window=6,
                min_samples=50
            ),
            "throughput": PerformanceThreshold(
                metric_name="throughput",
                warning_threshold=500,
                critical_threshold=200,
                regression_threshold=25.0,
                comparison_window=12,
                min_samples=30
            ),
            "uptime": PerformanceThreshold(
                metric_name="uptime",
                warning_threshold=99.0,
                critical_threshold=95.0,
                regression_threshold=2.0,
                comparison_window=24,
                min_samples=100
            ),
            "core_web_vitals_score": PerformanceThreshold(
                metric_name="core_web_vitals_score",
                warning_threshold=70,
                critical_threshold=50,
                regression_threshold=10.0,
                comparison_window=24,
                min_samples=20
            ),
            "bundle_size": PerformanceThreshold(
                metric_name="bundle_size",
                warning_threshold=1000,
                critical_threshold=2000,
                regression_threshold=15.0,
                comparison_window=48,
                min_samples=5
            )
        }
        
        print("📊 Performance thresholds initialized")
    
    def _configure_default_channels(self):
        """配置默认通知渠道"""
        # 邮件配置
        self.alert_service.configure_channel(AlertChannel.EMAIL, {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "username": "alerts@web3search.com",
            "password": "app_password",
            "recipient": "team@web3search.com"
        })
        
        # Slack配置
        self.alert_service.configure_channel(AlertChannel.SLACK, {
            "webhook_url": "https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX",
            "channel": "#performance-alerts"
        })
        
        # Webhook配置
        self.alert_service.configure_channel(AlertChannel.WEBHOOK, {
            "url": "https://api.web3search.com/webhooks/performance-alerts",
            "headers": {"Authorization": "Bearer webhook_token"}
        })
        
        # PagerDuty配置
        self.alert_service.configure_channel(AlertChannel.PAGERDUTY, {
            "integration_key": "integration_key_1234567890abcdef"
        })
        
        print("📢 Notification channels configured")
    
    def establish_baselines_from_historical_data(self, historical_data: Dict[str, List[float]]):
        """从历史数据建立基线"""
        print("📊 Establishing performance baselines from historical data...")
        
        for metric_name, values in historical_data.items():
            if metric_name in self.thresholds:
                threshold = self.thresholds[metric_name]
                if len(values) >= threshold.min_samples:
                    self.baseline_manager.establish_baseline(metric_name, values)
                else:
                    print(f"⚠️ Insufficient data for {metric_name}: {len(values)} < {threshold.min_samples}")
    
    def check_current_performance(self, current_metrics: Dict[str, List[float]]) -> List[RegressionAlert]:
        """检查当前性能并检测回归"""
        print("🔍 Checking current performance for regressions...")
        
        detected_regressions = []
        
        for metric_name, values in current_metrics.items():
            if metric_name in self.thresholds:
                threshold = self.thresholds[metric_name]
                regression = self.regression_detector.detect_regression(metric_name, values, threshold)
                
                if regression:
                    detected_regressions.append(regression)
                    
                    # 发送告警
                    channels = self._determine_notification_channels(regression)
                    self.alert_service.send_alert(regression, channels)
        
        if detected_regressions:
            print(f"🚨 Detected {len(detected_regressions)} performance regressions")
        else:
            print("✅ No performance regressions detected")
        
        return detected_regressions
    
    def _determine_notification_channels(self, alert: RegressionAlert) -> List[AlertChannel]:
        """根据严重程度确定通知渠道"""
        if alert.severity == AlertSeverity.CRITICAL:
            return [AlertChannel.EMAIL, AlertChannel.SLACK, AlertChannel.PAGERDUTY, AlertChannel.WEBHOOK]
        elif alert.severity == AlertSeverity.ERROR:
            return [AlertChannel.EMAIL, AlertChannel.SLACK, AlertChannel.WEBHOOK]
        elif alert.severity == AlertSeverity.WARNING:
            return [AlertChannel.SLACK, AlertChannel.WEBHOOK]
        else:
            return [AlertChannel.WEBHOOK]
    
    def start_continuous_monitoring(self, check_interval_minutes: int = 5):
        """启动持续监控"""
        if self.monitoring_active:
            print("⚠️ Monitoring is already active")
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(check_interval_minutes,),
            daemon=True
        )
        self.monitoring_thread.start()
        
        print(f"🔄 Started continuous monitoring (interval: {check_interval_minutes} minutes)")
    
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=10)
        print("⏹️ Stopped continuous monitoring")
    
    def _monitoring_loop(self, check_interval_minutes: int):
        """监控循环"""
        while self.monitoring_active:
            try:
                # 模拟获取当前性能指标
                current_metrics = self._simulate_current_metrics()
                
                # 检查回归
                self.check_current_performance(current_metrics)
                
                # 等待下次检查
                time.sleep(check_interval_minutes * 60)
                
            except Exception as e:
                print(f"❌ Error in monitoring loop: {e}")
                time.sleep(60)  # 出错时等待1分钟再重试
    
    def _simulate_current_metrics(self) -> Dict[str, List[float]]:
        """模拟当前性能指标"""
        # 生成带有一些随机波动的性能数据
        base_metrics = {
            "page_load_time": [2.5 + random.uniform(-0.5, 1.0) for _ in range(15)],
            "api_response_time": [800 + random.uniform(-200, 400) for _ in range(25)],
            "error_rate": [0.5 + random.uniform(-0.3, 0.8) for _ in range(60)],
            "throughput": [1200 + random.uniform(-300, 200) for _ in range(30)],
            "uptime": [99.8 + random.uniform(-0.5, 0.2) for _ in range(100)],
            "core_web_vitals_score": [75 + random.uniform(-10, 5) for _ in range(25)],
            "bundle_size": [850 + random.uniform(-50, 150) for _ in range(8)]
        }
        
        # 偶尔引入一些回归来测试检测
        if random.random() < 0.1:  # 10%概率产生回归
            regression_metric = random.choice(list(base_metrics.keys()))
            if "response_time" in regression_metric or "load_time" in regression_metric:
                base_metrics[regression_metric] = [v * random.uniform(1.2, 1.8) for v in base_metrics[regression_metric]]
            elif "error_rate" in regression_metric:
                base_metrics[regression_metric] = [v * random.uniform(1.5, 3.0) for v in base_metrics[regression_metric]]
            elif "throughput" in regression_metric:
                base_metrics[regression_metric] = [v * random.uniform(0.5, 0.8) for v in base_metrics[regression_metric]]
        
        return base_metrics
    
    def generate_regression_report(self) -> Dict[str, Any]:
        """生成回归检测报告"""
        print("📋 Generating regression detection report...")
        
        recent_alerts = [
            alert for alert in self.regression_detector.detection_history
            if alert.timestamp > datetime.now() - timedelta(days=7)
        ]
        
        # 按严重程度统计
        severity_counts = {}
        regression_type_counts = {}
        
        for alert in recent_alerts:
            severity_counts[alert.severity.value] = severity_counts.get(alert.severity.value, 0) + 1
            regression_type_counts[alert.regression_type.value] = regression_type_counts.get(alert.regression_type.value, 0) + 1
        
        # 按指标统计
        metric_regression_counts = {}
        for alert in recent_alerts:
            metric_regression_counts[alert.metric_name] = metric_regression_counts.get(alert.metric_name, 0) + 1
        
        # 通知统计
        recent_notifications = [
            notif for notif in self.alert_service.notification_history
            if notif.sent_at and notif.sent_at > datetime.now() - timedelta(days=7)
        ]
        
        notification_stats = {}
        for notif in recent_notifications:
            channel = notif.channel.value
            status = notif.status
            if channel not in notification_stats:
                notification_stats[channel] = {"sent": 0, "failed": 0}
            notification_stats[channel][status] += 1
        
        report = {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "report_period_days": 7,
                "total_regressions": len(recent_alerts),
                "monitoring_active": self.monitoring_active
            },
            "regression_summary": {
                "by_severity": severity_counts,
                "by_regression_type": regression_type_counts,
                "by_metric": metric_regression_counts
            },
            "recent_regressions": [
                {
                    "id": alert.id,
                    "metric": alert.metric_name,
                    "type": alert.regression_type.value,
                    "severity": alert.severity.value,
                    "regression_percentage": alert.regression_percentage,
                    "timestamp": alert.timestamp.isoformat(),
                    "description": alert.description
                }
                for alert in recent_alerts
            ],
            "notification_summary": notification_stats,
            "baseline_status": {
                "established_baselines": list(self.baseline_manager.baselines.keys()),
                "total_baselines": len(self.baseline_manager.baselines)
            },
            "threshold_configuration": {
                name: {
                    "warning_threshold": threshold.warning_threshold,
                    "critical_threshold": threshold.critical_threshold,
                    "regression_threshold": threshold.regression_threshold
                }
                for name, threshold in self.thresholds.items()
            }
        }
        
        return report

def main():
    """主函数 - 性能回归检测和告警系统"""
    print("🚀 Starting Performance Regression Detection and Alert System...")
    
    # 创建回归监控系统
    monitor = PerformanceRegressionMonitor()
    
    # 模拟历史数据用于建立基线
    print("\n📊 Generating historical baseline data...")
    historical_data = {
        "page_load_time": [2.1 + random.uniform(-0.3, 0.4) for _ in range(100)],
        "api_response_time": [750 + random.uniform(-150, 200) for _ in range(200)],
        "error_rate": [0.4 + random.uniform(-0.2, 0.3) for _ in range(500)],
        "throughput": [1100 + random.uniform(-200, 250) for _ in range(150)],
        "uptime": [99.9 + random.uniform(-0.3, 0.1) for _ in range(1000)],
        "core_web_vitals_score": [78 + random.uniform(-8, 6) for _ in range(100)],
        "bundle_size": [800 + random.uniform(-50, 100) for _ in range(20)]
    }
    
    # 建立性能基线
    monitor.establish_baselines_from_historical_data(historical_data)
    
    # 模拟当前性能数据
    print("\n📈 Generating current performance data...")
    current_metrics = {
        "page_load_time": [3.2 + random.uniform(-0.5, 0.8) for _ in range(15)],  # 模拟回归
        "api_response_time": [920 + random.uniform(-200, 300) for _ in range(25)],  # 模拟回归
        "error_rate": [0.6 + random.uniform(-0.3, 0.5) for _ in range(60)],
        "throughput": [1050 + random.uniform(-250, 150) for _ in range(30)],  # 模拟轻微回归
        "uptime": [99.7 + random.uniform(-0.4, 0.2) for _ in range(100)],
        "core_web_vitals_score": [72 + random.uniform(-10, 8) for _ in range(25)],  # 模拟回归
        "bundle_size": [920 + random.uniform(-80, 120) for _ in range(8)]
    }
    
    # 检查性能回归
    print("\n🔍 Checking for performance regressions...")
    detected_regressions = monitor.check_current_performance(current_metrics)
    
    # 显示检测结果
    print(f"\n📊 Regression Detection Results:")
    print(f"  • Total regressions detected: {len(detected_regressions)}")
    
    if detected_regressions:
        print(f"\n🚨 Detected Regressions:")
        for i, alert in enumerate(detected_regressions, 1):
            severity_emoji = {
                "critical": "🚨",
                "error": "❌", 
                "warning": "⚠️",
                "info": "ℹ️"
            }.get(alert.severity.value, "📢")
            
            print(f"  {i}. {alert.title} {severity_emoji}")
            print(f"     Metric: {alert.metric_name}")
            print(f"     Regression: {alert.regression_percentage:+.1f}%")
            print(f"     Severity: {alert.severity.value.upper()}")
            print(f"     Current: {alert.current_value:.2f}, Baseline: {alert.baseline_value:.2f}")
            print(f"     Affected endpoints: {', '.join(alert.affected_endpoints[:2])}")
            print(f"     Top recommendations: {alert.recommended_actions[0]}")
            print()
    
    # 生成回归检测报告
    print("\n📋 Generating comprehensive regression report...")
    regression_report = monitor.generate_regression_report()
    
    # 保存报告
    with open("performance_regression_report.json", "w") as f:
        json.dump(regression_report, f, indent=2, default=str)
    
    # 显示报告摘要
    print(f"\n📊 Regression Report Summary:")
    print(f"  • Report period: Last 7 days")
    print(f"  • Total regressions: {regression_report['report_metadata']['total_regressions']}")
    print(f"  • Monitoring status: {'Active' if regression_report['report_metadata']['monitoring_active'] else 'Inactive'}")
    
    severity_summary = regression_report['regression_summary']['by_severity']
    if severity_summary:
        print(f"  • By severity:")
        for severity, count in severity_summary.items():
            emoji = {"critical": "🚨", "error": "❌", "warning": "⚠️", "info": "ℹ️"}.get(severity, "📢")
            print(f"    - {severity.title()}: {count} {emoji}")
    
    metric_summary = regression_report['regression_summary']['by_metric']
    if metric_summary:
        print(f"  • By metric:")
        for metric, count in sorted(metric_summary.items(), key=lambda x: x[1], reverse=True)[:3]:
            print(f"    - {metric}: {count} regressions")
    
    notification_summary = regression_report['notification_summary']
    if notification_summary:
        print(f"  • Notifications sent:")
        for channel, stats in notification_summary.items():
            print(f"    - {channel}: {stats.get('sent', 0)} sent, {stats.get('failed', 0)} failed")
    
    # 启动持续监控（演示）
    print(f"\n🔄 Starting continuous monitoring for demonstration...")
    monitor.start_continuous_monitoring(check_interval_minutes=1)
    
    # 运行一段时间来演示监控
    print("⏳ Monitoring running for 2 minutes to demonstrate detection...")
    time.sleep(120)
    
    # 停止监控
    monitor.stop_monitoring()
    
    print(f"\n✅ Performance Regression Detection and Alert System completed successfully!")
    print("📁 Generated files:")
    print("  • performance_regression_report.json - Comprehensive regression analysis report")
    
    print(f"\n🎯 System Features:")
    print("  • Automated baseline establishment from historical data")
    print("  • Real-time regression detection with configurable thresholds")
    print("  • Multi-channel alert notifications (Email, Slack, Webhook, PagerDuty)")
    print("  • Continuous monitoring with configurable intervals")
    print("  • Comprehensive regression reporting and analytics")
    print("  • Intelligent severity assessment and recommendation engine")
    
    return regression_report

if __name__ == "__main__":
    main()
