"""
性能预算监控和预警系统
实时监控前端性能指标，设置预算阈值，自动预警和报告
"""

import json
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from datetime import datetime, timedelta

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BudgetType(Enum):
    """预算类型"""
    BUNDLE_SIZE = "bundle_size"
    LOAD_TIME = "load_time"
    CORE_WEB_VITALS = "core_web_vitals"
    API_RESPONSE = "api_response"
    MEMORY_USAGE = "memory_usage"
    NETWORK_REQUESTS = "network_requests"

class AlertLevel(Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class MonitoringFrequency(Enum):
    """监控频率"""
    REAL_TIME = "real_time"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    ON_DEPLOY = "on_deploy"

@dataclass
class PerformanceBudget:
    """性能预算"""
    budget_type: BudgetType
    metric_name: str
    budget_value: float
    current_value: float
    threshold_warning: float
    threshold_error: float
    unit: str
    description: str

@dataclass
class BudgetAlert:
    """预算告警"""
    budget_type: BudgetType
    metric_name: str
    current_value: float
    budget_value: float
    threshold_level: AlertLevel
    percentage_over: float
    timestamp: datetime
    message: str
    recommendations: List[str]

@dataclass
class MonitoringRule:
    """监控规则"""
    rule_id: str
    budget_type: BudgetType
    metric_name: str
    frequency: MonitoringFrequency
    alert_thresholds: Dict[AlertLevel, float]
    enabled: bool
    notification_channels: List[str]

class PerformanceBudgetManager:
    """性能预算管理器"""
    
    def __init__(self):
        self.budgets = {}
        self.alerts = []
        self.monitoring_rules = {}
        self.historical_data = {}
        
    def define_performance_budgets(self) -> Dict[str, PerformanceBudget]:
        """定义性能预算"""
        print("💰 Defining performance budgets...")
        
        budgets = {
            # Bundle Size Budgets
            "main_bundle_size": PerformanceBudget(
                budget_type=BudgetType.BUNDLE_SIZE,
                metric_name="main_bundle_size",
                budget_value=500000,  # 500KB
                current_value=0,
                threshold_warning=450000,  # 450KB
                threshold_error=600000,    # 600KB
                unit="bytes",
                description="Main JavaScript bundle size"
            ),
            
            "vendor_bundle_size": PerformanceBudget(
                budget_type=BudgetType.BUNDLE_SIZE,
                metric_name="vendor_bundle_size",
                budget_value=300000,  # 300KB
                current_value=0,
                threshold_warning=270000,  # 270KB
                threshold_error=400000,    # 400KB
                unit="bytes",
                description="Third-party vendor bundle size"
            ),
            
            "css_bundle_size": PerformanceBudget(
                budget_type=BudgetType.BUNDLE_SIZE,
                metric_name="css_bundle_size",
                budget_value=100000,  # 100KB
                current_value=0,
                threshold_warning=90000,   # 90KB
                threshold_error=150000,   # 150KB
                unit="bytes",
                description="CSS bundle size"
            ),
            
            # Load Time Budgets
            "first_contentful_paint": PerformanceBudget(
                budget_type=BudgetType.LOAD_TIME,
                metric_name="first_contentful_paint",
                budget_value=1500,  # 1.5s
                current_value=0,
                threshold_warning=2000,  # 2s
                threshold_error=3000,    # 3s
                unit="milliseconds",
                description="First Contentful Paint time"
            ),
            
            "largest_contentful_paint": PerformanceBudget(
                budget_type=BudgetType.LOAD_TIME,
                metric_name="largest_contentful_paint",
                budget_value=2500,  # 2.5s
                current_value=0,
                threshold_warning=3000,  # 3s
                threshold_error=4000,    # 4s
                unit="milliseconds",
                description="Largest Contentful Paint time"
            ),
            
            "time_to_interactive": PerformanceBudget(
                budget_type=BudgetType.LOAD_TIME,
                metric_name="time_to_interactive",
                budget_value=3000,  # 3s
                current_value=0,
                threshold_warning=4000,  # 4s
                threshold_error=5000,    # 5s
                unit="milliseconds",
                description="Time to Interactive"
            ),
            
            # Core Web Vitals Budgets
            "cumulative_layout_shift": PerformanceBudget(
                budget_type=BudgetType.CORE_WEB_VITALS,
                metric_name="cumulative_layout_shift",
                budget_value=0.1,
                current_value=0,
                threshold_warning=0.15,
                threshold_error=0.25,
                unit="score",
                description="Cumulative Layout Shift score"
            ),
            
            "first_input_delay": PerformanceBudget(
                budget_type=BudgetType.CORE_WEB_VITALS,
                metric_name="first_input_delay",
                budget_value=100,  # 100ms
                current_value=0,
                threshold_warning=150,  # 150ms
                threshold_error=300,    # 300ms
                unit="milliseconds",
                description="First Input Delay"
            ),
            
            # API Response Budgets
            "api_response_time": PerformanceBudget(
                budget_type=BudgetType.API_RESPONSE,
                metric_name="api_response_time",
                budget_value=1000,  # 1s
                current_value=0,
                threshold_warning=1500,  # 1.5s
                threshold_error=2000,    # 2s
                unit="milliseconds",
                description="Average API response time"
            ),
            
            # Memory Usage Budgets
            "memory_usage": PerformanceBudget(
                budget_type=BudgetType.MEMORY_USAGE,
                metric_name="memory_usage",
                budget_value=50000000,  # 50MB
                current_value=0,
                threshold_warning=75000000,  # 75MB
                threshold_error=100000000,  # 100MB
                unit="bytes",
                description="JavaScript memory usage"
            ),
            
            # Network Requests Budgets
            "total_requests": PerformanceBudget(
                budget_type=BudgetType.NETWORK_REQUESTS,
                metric_name="total_requests",
                budget_value=50,
                current_value=0,
                threshold_warning=75,
                threshold_error=100,
                unit="count",
                description="Total number of network requests"
            )
        }
        
        self.budgets = budgets
        return budgets
    
    def create_monitoring_rules(self) -> Dict[str, MonitoringRule]:
        """创建监控规则"""
        print("📋 Creating monitoring rules...")
        
        rules = {
            "bundle_size_monitoring": MonitoringRule(
                rule_id="bundle_size_monitoring",
                budget_type=BudgetType.BUNDLE_SIZE,
                metric_name="main_bundle_size",
                frequency=MonitoringFrequency.ON_DEPLOY,
                alert_thresholds={
                    AlertLevel.WARNING: 90.0,  # 90% of budget
                    AlertLevel.ERROR: 110.0,   # 110% of budget
                    AlertLevel.CRITICAL: 130.0 # 130% of budget
                },
                enabled=True,
                notification_channels=["slack", "email", "dashboard"]
            ),
            
            "core_web_vitals_monitoring": MonitoringRule(
                rule_id="core_web_vitals_monitoring",
                budget_type=BudgetType.CORE_WEB_VITALS,
                metric_name="largest_contentful_paint",
                frequency=MonitoringFrequency.DAILY,
                alert_thresholds={
                    AlertLevel.WARNING: 120.0,  # 120% of budget
                    AlertLevel.ERROR: 140.0,    # 140% of budget
                    AlertLevel.CRITICAL: 160.0  # 160% of budget
                },
                enabled=True,
                notification_channels=["slack", "dashboard"]
            ),
            
            "api_performance_monitoring": MonitoringRule(
                rule_id="api_performance_monitoring",
                budget_type=BudgetType.API_RESPONSE,
                metric_name="api_response_time",
                frequency=MonitoringFrequency.REAL_TIME,
                alert_thresholds={
                    AlertLevel.WARNING: 150.0,  # 150% of budget
                    AlertLevel.ERROR: 200.0,    # 200% of budget
                    AlertLevel.CRITICAL: 300.0  # 300% of budget
                },
                enabled=True,
                notification_channels=["slack", "pagerduty", "dashboard"]
            ),
            
            "memory_usage_monitoring": MonitoringRule(
                rule_id="memory_usage_monitoring",
                budget_type=BudgetType.MEMORY_USAGE,
                metric_name="memory_usage",
                frequency=MonitoringFrequency.HOURLY,
                alert_thresholds={
                    AlertLevel.WARNING: 150.0,  # 150% of budget
                    AlertLevel.ERROR: 180.0,    # 180% of budget
                    AlertLevel.CRITICAL: 200.0  # 200% of budget
                },
                enabled=True,
                notification_channels=["email", "dashboard"]
            ),
            
            "load_time_monitoring": MonitoringRule(
                rule_id="load_time_monitoring",
                budget_type=BudgetType.LOAD_TIME,
                metric_name="first_contentful_paint",
                frequency=MonitoringFrequency.DAILY,
                alert_thresholds={
                    AlertLevel.WARNING: 130.0,  # 130% of budget
                    AlertLevel.ERROR: 160.0,    # 160% of budget
                    AlertLevel.CRITICAL: 200.0  # 200% of budget
                },
                enabled=True,
                notification_channels=["slack", "email", "dashboard"]
            )
        }
        
        self.monitoring_rules = rules
        return rules

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, budget_manager: PerformanceBudgetManager):
        self.budget_manager = budget_manager
        self.current_metrics = {}
        self.monitoring_active = False
        
    def collect_performance_metrics(self) -> Dict[str, float]:
        """收集性能指标"""
        print("📊 Collecting performance metrics...")
        
        # 模拟收集的性能指标
        metrics = {
            "main_bundle_size": 520000,      # 520KB - 超出预算
            "vendor_bundle_size": 280000,    # 280KB - 在预算内
            "css_bundle_size": 95000,        # 95KB - 在预算内
            "first_contentful_paint": 1800,  # 1.8s - 超出预算
            "largest_contentful_paint": 2800, # 2.8s - 超出预算
            "time_to_interactive": 3500,     # 3.5s - 超出预算
            "cumulative_layout_shift": 0.12, # 0.12 - 超出预算
            "first_input_delay": 120,        # 120ms - 超出预算
            "api_response_time": 1200,       # 1.2s - 超出预算
            "memory_usage": 60000000,        # 60MB - 超出预算
            "total_requests": 55             # 55 - 超出预算
        }
        
        self.current_metrics = metrics
        
        # 更新预算管理器中的当前值
        for metric_name, value in metrics.items():
            if metric_name in self.budget_manager.budgets:
                self.budget_manager.budgets[metric_name].current_value = value
        
        return metrics
    
    def check_budget_compliance(self, metrics: Dict[str, float]) -> List[BudgetAlert]:
        """检查预算合规性"""
        print("🔍 Checking budget compliance...")
        
        alerts = []
        
        for metric_name, current_value in metrics.items():
            if metric_name in self.budget_manager.budgets:
                budget = self.budget_manager.budgets[metric_name]
                
                # 计算超出预算的百分比
                percentage_over = ((current_value - budget.budget_value) / budget.budget_value) * 100
                
                # 确定告警级别
                if current_value > budget.threshold_error:
                    alert_level = AlertLevel.ERROR
                elif current_value > budget.threshold_warning:
                    alert_level = AlertLevel.WARNING
                elif percentage_over > 0:
                    alert_level = AlertLevel.INFO
                else:
                    continue  # 在预算内，无告警
                
                # 生成告警
                alert = BudgetAlert(
                    budget_type=budget.budget_type,
                    metric_name=metric_name,
                    current_value=current_value,
                    budget_value=budget.budget_value,
                    threshold_level=alert_level,
                    percentage_over=percentage_over,
                    timestamp=datetime.now(),
                    message=self._generate_alert_message(budget, current_value, percentage_over, alert_level),
                    recommendations=self._generate_recommendations(budget, current_value)
                )
                
                alerts.append(alert)
        
        self.budget_manager.alerts = alerts
        return alerts
    
    def _generate_alert_message(self, budget: PerformanceBudget, current_value: float, 
                              percentage_over: float, alert_level: AlertLevel) -> str:
        """生成告警消息"""
        status_emoji = {
            AlertLevel.INFO: "ℹ️",
            AlertLevel.WARNING: "⚠️",
            AlertLevel.ERROR: "❌",
            AlertLevel.CRITICAL: "🚨"
        }
        
        emoji = status_emoji.get(alert_level, "📊")
        
        if percentage_over > 0:
            return f"{emoji} {budget.metric_name} exceeded budget by {percentage_over:.1f}% ({current_value:.0f} {budget.unit} vs {budget.budget_value:.0f} {budget.unit})"
        else:
            return f"{emoji} {budget.metric_name} is approaching budget limit ({current_value:.0f} {budget.unit} vs {budget.budget_value:.0f} {budget.unit})"
    
    def _generate_recommendations(self, budget: PerformanceBudget, current_value: float) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        if budget.budget_type == BudgetType.BUNDLE_SIZE:
            recommendations.extend([
                "Implement code splitting and lazy loading",
                "Remove unused dependencies and code",
                "Enable tree shaking and dead code elimination",
                "Compress and minify bundles"
            ])
        elif budget.budget_type == BudgetType.LOAD_TIME:
            recommendations.extend([
                "Optimize critical rendering path",
                "Implement resource preloading and hints",
                "Enable server-side rendering or streaming",
                "Optimize images and assets"
            ])
        elif budget.budget_type == BudgetType.CORE_WEB_VITALS:
            recommendations.extend([
                "Optimize layout stability (CLS)",
                "Reduce JavaScript execution time (FID)",
                "Improve server response time (LCP)",
                "Optimize resource loading"
            ])
        elif budget.budget_type == BudgetType.API_RESPONSE:
            recommendations.extend([
                "Implement API response caching",
                "Optimize database queries and indexing",
                "Add CDN for static assets",
                "Implement request batching"
            ])
        elif budget.budget_type == BudgetType.MEMORY_USAGE:
            recommendations.extend([
                "Fix memory leaks in JavaScript",
                "Optimize data structures and algorithms",
                "Implement object pooling for frequently created objects",
                "Monitor and clean up event listeners"
            ])
        elif budget.budget_type == BudgetType.NETWORK_REQUESTS:
            recommendations.extend([
                "Bundle multiple requests into batch calls",
                "Implement client-side caching",
                "Use resource bundling and concatenation",
                "Optimize API design to reduce round trips"
            ])
        
        return recommendations

class AlertNotificationSystem:
    """告警通知系统"""
    
    def __init__(self):
        self.notification_channels = {
            "slack": SlackNotifier(),
            "email": EmailNotifier(),
            "dashboard": DashboardNotifier(),
            "pagerduty": PagerDutyNotifier()
        }
    
    def send_alerts(self, alerts: List[BudgetAlert], channels: List[str]) -> Dict[str, bool]:
        """发送告警通知"""
        print("📢 Sending alert notifications...")
        
        results = {}
        
        for channel_name in channels:
            if channel_name in self.notification_channels:
                notifier = self.notification_channels[channel_name]
                success = notifier.send_notifications(alerts)
                results[channel_name] = success
                print(f"  {channel_name}: {'✅ Sent' if success else '❌ Failed'}")
            else:
                results[channel_name] = False
                print(f"  {channel_name}: ❌ Unknown channel")
        
        return results

class SlackNotifier:
    """Slack通知器"""
    
    def send_notifications(self, alerts: List[BudgetAlert]) -> bool:
        """发送Slack通知"""
        print(f"    Sending {len(alerts)} alerts to Slack...")
        
        # 模拟Slack API调用
        for alert in alerts:
            slack_message = self._format_slack_message(alert)
            print(f"      📱 {alert.metric_name}: {alert.message}")
        
        return True
    
    def _format_slack_message(self, alert: BudgetAlert) -> str:
        """格式化Slack消息"""
        color = {
            AlertLevel.INFO: "#36a64f",
            AlertLevel.WARNING: "#ff9500",
            AlertLevel.ERROR: "#ff0000",
            AlertLevel.CRITICAL: "#8b0000"
        }.get(alert.threshold_level, "#36a64f")
        
        return f"""
🚨 *Performance Budget Alert* 🚨

*Metric*: {alert.metric_name}
*Current Value*: {alert.current_value:.0f} {alert.unit}
*Budget Value*: {alert.budget_value:.0f} {alert.unit}
*Over Budget*: {alert.percentage_over:.1f}%
*Severity*: {alert.threshold_level.value.upper()}

*Recommendations*:
{chr(10).join(f"• {rec}" for rec in alert.recommendations[:3])}

*Timestamp*: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
        """.strip()

class EmailNotifier:
    """邮件通知器"""
    
    def send_notifications(self, alerts: List[BudgetAlert]) -> bool:
        """发送邮件通知"""
        print(f"    📧 Sending email notification for {len(alerts)} alerts...")
        
        # 模拟邮件发送
        for alert in alerts:
            print(f"      📨 Email sent for {alert.metric_name}")
        
        return True

class DashboardNotifier:
    """Dashboard通知器"""
    
    def send_notifications(self, alerts: List[BudgetAlert]) -> bool:
        """更新Dashboard"""
        print(f"    📊 Updating dashboard with {len(alerts)} alerts...")
        
        # 模拟Dashboard更新
        for alert in alerts:
            print(f"      📈 Dashboard updated for {alert.metric_name}")
        
        return True

class PagerDutyNotifier:
    """PagerDuty通知器"""
    
    def send_notifications(self, alerts: List[BudgetAlert]) -> bool:
        """发送PagerDuty告警"""
        critical_alerts = [alert for alert in alerts if alert.threshold_level == AlertLevel.CRITICAL]
        
        if critical_alerts:
            print(f"    🚨 Sending PagerDuty alert for {len(critical_alerts)} critical issues...")
            for alert in critical_alerts:
                print(f"      📟 PagerDuty incident created for {alert.metric_name}")
        
        return len(critical_alerts) > 0

class PerformanceBudgetReporter:
    """性能预算报告器"""
    
    def __init__(self, budget_manager: PerformanceBudgetManager):
        self.budget_manager = budget_manager
        
    def generate_budget_report(self) -> Dict[str, Any]:
        """生成预算报告"""
        print("📋 Generating comprehensive budget report...")
        
        # 计算预算合规性统计
        compliance_stats = self._calculate_compliance_stats()
        
        # 生成趋势分析
        trend_analysis = self._generate_trend_analysis()
        
        # 创建优化建议
        optimization_recommendations = self._create_optimization_recommendations()
        
        # 生成预算执行摘要
        budget_summary = self._generate_budget_summary()
        
        report = {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "report_period": "last_30_days",
                "total_budgets": len(self.budget_manager.budgets),
                "active_alerts": len(self.budget_manager.alerts)
            },
            "budget_summary": budget_summary,
            "compliance_statistics": compliance_stats,
            "current_alerts": [asdict(alert) for alert in self.budget_manager.alerts],
            "trend_analysis": trend_analysis,
            "optimization_recommendations": optimization_recommendations,
            "action_items": self._generate_action_items(),
            "budget_forecast": self._generate_budget_forecast()
        }
        
        return report
    
    def _calculate_compliance_stats(self) -> Dict[str, Any]:
        """计算预算合规性统计"""
        total_budgets = len(self.budget_manager.budgets)
        within_budget = 0
        warning_level = 0
        error_level = 0
        critical_level = 0
        
        for budget in self.budget_manager.budgets.values():
            if budget.current_value == 0:
                continue  # 没有数据
            
            if budget.current_value <= budget.budget_value:
                within_budget += 1
            elif budget.current_value <= budget.threshold_warning:
                warning_level += 1
            elif budget.current_value <= budget.threshold_error:
                error_level += 1
            else:
                critical_level += 1
        
        return {
            "total_budgets": total_budgets,
            "within_budget": within_budget,
            "warning_level": warning_level,
            "error_level": error_level,
            "critical_level": critical_level,
            "compliance_rate": (within_budget / total_budgets * 100) if total_budgets > 0 else 0
        }
    
    def _generate_trend_analysis(self) -> Dict[str, Any]:
        """生成趋势分析"""
        # 模拟历史数据趋势
        return {
            "bundle_size_trend": {
                "direction": "increasing",
                "change_percent": 15.2,
                "period": "30_days",
                "status": "concerning"
            },
            "load_time_trend": {
                "direction": "decreasing",
                "change_percent": -8.5,
                "period": "30_days", 
                "status": "improving"
            },
            "core_web_vitals_trend": {
                "direction": "stable",
                "change_percent": 2.1,
                "period": "30_days",
                "status": "stable"
            },
            "api_performance_trend": {
                "direction": "increasing",
                "change_percent": 12.8,
                "period": "30_days",
                "status": "concerning"
            }
        }
    
    def _create_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """创建优化建议"""
        recommendations = []
        
        # 基于当前告警生成建议
        for alert in self.budget_manager.alerts:
            if alert.threshold_level in [AlertLevel.ERROR, AlertLevel.CRITICAL]:
                recommendation = {
                    "priority": "high" if alert.threshold_level == AlertLevel.CRITICAL else "medium",
                    "category": alert.budget_type.value,
                    "metric": alert.metric_name,
                    "current_issue": f"{alert.metric_name} is {alert.percentage_over:.1f}% over budget",
                    "recommendations": alert.recommendations,
                    "estimated_impact": f"Could reduce {alert.metric_name} by 20-40%",
                    "effort": "medium",
                    "timeline": "2-4 weeks"
                }
                recommendations.append(recommendation)
        
        # 添加通用建议
        recommendations.extend([
            {
                "priority": "medium",
                "category": "proactive",
                "metric": "performance_monitoring",
                "current_issue": "Need better performance monitoring",
                "recommendations": [
                    "Set up automated performance testing in CI/CD",
                    "Implement real-user monitoring (RUM)",
                    "Create performance budgets for new features",
                    "Regular performance reviews and optimization"
                ],
                "estimated_impact": "Prevent performance regressions",
                "effort": "high",
                "timeline": "4-6 weeks"
            }
        ])
        
        return recommendations
    
    def _generate_budget_summary(self) -> Dict[str, Any]:
        """生成预算摘要"""
        budget_categories = {}
        
        for budget_name, budget in self.budget_manager.budgets.items():
            category = budget.budget_type.value
            
            if category not in budget_categories:
                budget_categories[category] = {
                    "total_budget": 0,
                    "current_usage": 0,
                    "budgets": []
                }
            
            budget_categories[category]["total_budget"] += budget.budget_value
            budget_categories[category]["current_usage"] += budget.current_value
            budget_categories[category]["budgets"].append({
                "name": budget.metric_name,
                "budget": budget.budget_value,
                "current": budget.current_value,
                "percentage": (budget.current_value / budget.budget_value * 100) if budget.budget_value > 0 else 0,
                "status": "within_budget" if budget.current_value <= budget.budget_value else "over_budget"
            })
        
        # 计算每个类别的总体状态
        for category, data in budget_categories.items():
            data["percentage_used"] = (data["current_usage"] / data["total_budget"] * 100) if data["total_budget"] > 0 else 0
            data["status"] = "within_budget" if data["current_usage"] <= data["total_budget"] else "over_budget"
        
        return budget_categories
    
    def _generate_action_items(self) -> List[Dict[str, Any]]:
        """生成行动项"""
        action_items = []
        
        # 基于告警级别生成行动项
        critical_alerts = [alert for alert in self.budget_manager.alerts if alert.threshold_level == AlertLevel.CRITICAL]
        error_alerts = [alert for alert in self.budget_manager.alerts if alert.threshold_level == AlertLevel.ERROR]
        
        if critical_alerts:
            action_items.append({
                "priority": "critical",
                "title": "Address critical performance budget violations",
                "description": f"{len(critical_alerts)} metrics are critically over budget",
                "assignee": "Performance Team",
                "due_date": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
                "actions": ["Immediate investigation", "Implement hotfixes", "Schedule emergency optimization"]
            })
        
        if error_alerts:
            action_items.append({
                "priority": "high",
                "title": "Resolve performance budget errors",
                "description": f"{len(error_alerts)} metrics are over error threshold",
                "assignee": "Development Team",
                "due_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
                "actions": ["Root cause analysis", "Plan optimization work", "Update monitoring rules"]
            })
        
        # 添加预防性行动项
        action_items.append({
            "priority": "medium",
            "title": "Enhance performance monitoring",
            "description": "Improve monitoring and alerting capabilities",
            "assignee": "DevOps Team",
            "due_date": (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d"),
            "actions": ["Add more granular alerts", "Implement automated reporting", "Set up performance dashboards"]
        })
        
        return action_items
    
    def _generate_budget_forecast(self) -> Dict[str, Any]:
        """生成预算预测"""
        # 基于当前趋势预测未来预算使用情况
        return {
            "forecast_period": "next_30_days",
            "predictions": {
                "bundle_size": {
                    "current_trend": "increasing",
                    "predicted_increase": "+18%",
                    "risk_level": "high",
                    "recommended_action": "Implement bundle optimization soon"
                },
                "load_time": {
                    "current_trend": "stable",
                    "predicted_change": "+5%",
                    "risk_level": "medium",
                    "recommended_action": "Continue monitoring and optimize as needed"
                },
                "api_performance": {
                    "current_trend": "decreasing",
                    "predicted_change": "-12%",
                    "risk_level": "low",
                    "recommended_action": "Maintain current optimization efforts"
                }
            }
        }

def main():
    """主函数 - 性能预算监控和预警"""
    print("🚀 Starting Performance Budget Monitoring and Alerting System...")
    
    # 创建预算管理器
    budget_manager = PerformanceBudgetManager()
    
    # 定义性能预算
    budgets = budget_manager.define_performance_budgets()
    
    # 创建监控规则
    monitoring_rules = budget_manager.create_monitoring_rules()
    
    # 创建性能监控器
    monitor = PerformanceMonitor(budget_manager)
    
    # 收集性能指标
    current_metrics = monitor.collect_performance_metrics()
    
    # 检查预算合规性
    alerts = monitor.check_budget_compliance(current_metrics)
    
    # 显示当前指标状态
    print(f"\n📊 Current Performance Metrics:")
    for metric_name, value in current_metrics.items():
        if metric_name in budgets:
            budget = budgets[metric_name]
            percentage = (value / budget.budget_value * 100) if budget.budget_value > 0 else 0
            status = "✅" if value <= budget.budget_value else "❌"
            print(f"  • {metric_name}: {value:.0f} {budget.unit} ({percentage:.1f}% of budget) {status}")
    
    # 显示告警信息
    if alerts:
        print(f"\n🚨 Performance Budget Alerts ({len(alerts)}):")
        
        # 按严重程度分组
        alerts_by_level = {}
        for alert in alerts:
            level = alert.threshold_level.value
            if level not in alerts_by_level:
                alerts_by_level[level] = []
            alerts_by_level[level].append(alert)
        
        for level in ["critical", "error", "warning", "info"]:
            if level in alerts_by_level:
                print(f"\n  {level.upper()} ({len(alerts_by_level[level])}):")
                for alert in alerts_by_level[level]:
                    print(f"    • {alert.message}")
                    print(f"      Recommendations: {', '.join(alert.recommendations[:2])}")
    else:
        print(f"\n✅ All performance budgets are within limits!")
    
    # 发送告警通知
    if alerts:
        notification_system = AlertNotificationSystem()
        
        # 确定需要发送的渠道
        critical_alerts = [alert for alert in alerts if alert.threshold_level == AlertLevel.CRITICAL]
        error_alerts = [alert for alert in alerts if alert.threshold_level == AlertLevel.ERROR]
        
        channels = ["dashboard"]
        if critical_alerts or error_alerts:
            channels.extend(["slack", "email"])
        if critical_alerts:
            channels.append("pagerduty")
        
        notification_results = notification_system.send_alerts(alerts, channels)
        
        print(f"\n📢 Notification Results:")
        for channel, success in notification_results.items():
            status = "✅ Sent" if success else "❌ Failed"
            print(f"  • {channel}: {status}")
    
    # 生成预算报告
    reporter = PerformanceBudgetReporter(budget_manager)
    budget_report = reporter.generate_budget_report()
    
    # 显示报告摘要
    summary = budget_report["budget_summary"]
    compliance_stats = budget_report["compliance_statistics"]
    
    print(f"\n📈 Budget Summary:")
    for category, data in summary.items():
        status_emoji = "✅" if data["status"] == "within_budget" else "❌"
        print(f"  • {category.replace('_', ' ').title()}: {data['percentage_used']:.1f}% used {status_emoji}")
    
    print(f"\n📊 Compliance Statistics:")
    print(f"  • Total Budgets: {compliance_stats['total_budgets']}")
    print(f"  • Within Budget: {compliance_stats['within_budget']} ({compliance_stats['compliance_rate']:.1f}%)")
    print(f"  • Warning Level: {compliance_stats['warning_level']}")
    print(f"  • Error Level: {compliance_stats['error_level']}")
    print(f"  • Critical Level: {compliance_stats['critical_level']}")
    
    # 显示优化建议
    recommendations = budget_report["optimization_recommendations"]
    if recommendations:
        print(f"\n💡 Optimization Recommendations ({len(recommendations)}):")
        for i, rec in enumerate(recommendations[:3], 1):
            print(f"  {i}. {rec['current_issue']}")
            print(f"     Priority: {rec['priority']}, Effort: {rec['effort']}, Timeline: {rec['timeline']}")
            print(f"     Top recommendation: {rec['recommendations'][0]}")
    
    # 显示行动项
    action_items = budget_report["action_items"]
    if action_items:
        print(f"\n🎯 Action Items ({len(action_items)}):")
        for i, item in enumerate(action_items, 1):
            print(f"  {i}. [{item['priority'].upper()}] {item['title']}")
            print(f"     Assignee: {item['assignee']}, Due: {item['due_date']}")
            print(f"     Actions: {', '.join(item['actions'])}")
    
    # 保存报告
    with open("performance_budget_monitoring_report.json", "w") as f:
        json.dump(budget_report, f, indent=2, default=str)
    
    print(f"\n✅ Performance Budget Monitoring and Alerting completed!")
    print("📁 Budget report saved to: performance_budget_monitoring_report.json")
    
    return budget_report

if __name__ == "__main__":
    main()
