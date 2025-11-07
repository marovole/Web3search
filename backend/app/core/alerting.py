"""
告警系统
提供错误监控和性能告警功能
支持多种通知渠道：Slack、邮件、短信等
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json
import aiohttp
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.core.config import settings

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertChannel(Enum):
    """告警渠道"""
    SLACK = "slack"
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"


@dataclass
class AlertRule:
    """告警规则"""
    name: str
    condition: str  # 告警条件表达式
    level: AlertLevel
    channels: List[AlertChannel]
    threshold: float
    duration: int  # 持续时间（秒）
    enabled: bool = True
    description: str = ""
    tags: Dict[str, str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = {}


@dataclass
class Alert:
    """告警事件"""
    id: str
    rule_name: str
    level: AlertLevel
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "rule_name": self.rule_name,
            "level": self.level.value,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "resolved": self.resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None
        }


class AlertManager:
    """
    告警管理器
    负责告警规则的评估、发送和状态管理
    """
    
    def __init__(self):
        self.rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.metrics_cache: Dict[str, List[float]] = {}
        self.last_evaluation: Dict[str, datetime] = {}
        
        # 初始化默认告警规则
        self._init_default_rules()
    
    def _init_default_rules(self):
        """初始化默认告警规则"""
        default_rules = [
            # API响应时间告警
            AlertRule(
                name="api_response_time_high",
                condition="api_response_time_p95 > 3000",
                level=AlertLevel.WARNING,
                channels=[AlertChannel.SLACK, AlertChannel.EMAIL],
                threshold=3000.0,
                duration=300,  # 5分钟
                description="API响应时间P95超过3秒",
                tags={"category": "performance", "service": "api"}
            ),
            
            # API错误率告警
            AlertRule(
                name="api_error_rate_high",
                condition="api_error_rate > 0.05",
                level=AlertLevel.ERROR,
                channels=[AlertChannel.SLACK, AlertChannel.EMAIL, AlertChannel.SMS],
                threshold=0.05,
                duration=180,  # 3分钟
                description="API错误率超过5%",
                tags={"category": "availability", "service": "api"}
            ),
            
            # 数据库连接告警
            AlertRule(
                name="db_connection_failures",
                condition="db_connection_errors > 10",
                level=AlertLevel.CRITICAL,
                channels=[AlertChannel.SLACK, AlertChannel.EMAIL, AlertChannel.SMS],
                threshold=10.0,
                duration=60,  # 1分钟
                description="数据库连接失败次数过多",
                tags={"category": "infrastructure", "service": "database"}
            ),
            
            # 内存使用率告警
            AlertRule(
                name="memory_usage_high",
                condition="memory_usage_percent > 85",
                level=AlertLevel.WARNING,
                channels=[AlertChannel.SLACK],
                threshold=85.0,
                duration=600,  # 10分钟
                description="内存使用率超过85%",
                tags={"category": "infrastructure", "service": "system"}
            ),
            
            # CPU使用率告警
            AlertRule(
                name="cpu_usage_high",
                condition="cpu_usage_percent > 90",
                level=AlertLevel.ERROR,
                channels=[AlertChannel.SLACK, AlertChannel.EMAIL],
                threshold=90.0,
                duration=300,  # 5分钟
                description="CPU使用率超过90%",
                tags={"category": "infrastructure", "service": "system"}
            ),
            
            # 外部API失败告警
            AlertRule(
                name="external_api_failures",
                condition="external_api_error_rate > 0.1",
                level=AlertLevel.WARNING,
                channels=[AlertChannel.SLACK],
                threshold=0.1,
                duration=300,  # 5分钟
                description="外部API调用失败率超过10%",
                tags={"category": "external", "service": "api"}
            ),
            
            # 前端错误告警
            AlertRule(
                name="frontend_errors_high",
                condition="frontend_error_rate > 0.02",
                level=AlertLevel.ERROR,
                channels=[AlertChannel.SLACK, AlertChannel.EMAIL],
                threshold=0.02,
                duration=240,  # 4分钟
                description="前端错误率超过2%",
                tags={"category": "frontend", "service": "web"}
            ),
        ]
        
        for rule in default_rules:
            self.rules[rule.name] = rule
    
    def add_rule(self, rule: AlertRule):
        """添加告警规则"""
        self.rules[rule.name] = rule
        logger.info(f"Added alert rule: {rule.name}")
    
    def remove_rule(self, rule_name: str):
        """移除告警规则"""
        if rule_name in self.rules:
            del self.rules[rule_name]
            logger.info(f"Removed alert rule: {rule_name}")
    
    def update_metric(self, metric_name: str, value: float):
        """更新指标值"""
        if metric_name not in self.metrics_cache:
            self.metrics_cache[metric_name] = []
        
        # 添加最新值，保留最近100个数据点
        self.metrics_cache[metric_name].append(value)
        if len(self.metrics_cache[metric_name]) > 100:
            self.metrics_cache[metric_name] = self.metrics_cache[metric_name][-100:]
        
        # 触发规则评估
        asyncio.create_task(self._evaluate_rules())
    
    async def _evaluate_rules(self):
        """评估所有告警规则"""
        current_time = datetime.now()
        
        for rule_name, rule in self.rules.items():
            if not rule.enabled:
                continue
            
            # 检查评估频率（避免过于频繁的评估）
            if rule_name in self.last_evaluation:
                if (current_time - self.last_evaluation[rule_name]).seconds < 30:
                    continue
            
            self.last_evaluation[rule_name] = current_time
            
            try:
                # 评估规则条件
                should_alert = await self._evaluate_condition(rule.condition)
                
                if should_alert:
                    await self._trigger_alert(rule)
                else:
                    await self._resolve_alert(rule_name)
                    
            except Exception as e:
                logger.error(f"Error evaluating alert rule {rule_name}: {e}")
    
    async def _evaluate_condition(self, condition: str) -> bool:
        """评估告警条件"""
        # 构建评估上下文
        context = self._build_evaluation_context()
        
        try:
            # 简单的条件评估（实际应用中可能需要更复杂的表达式解析器）
            return self._evaluate_simple_condition(condition, context)
        except Exception as e:
            logger.error(f"Error evaluating condition '{condition}': {e}")
            return False
    
    def _build_evaluation_context(self) -> Dict[str, float]:
        """构建规则评估上下文"""
        context = {}
        
        # API指标
        api_times = self.metrics_cache.get("api_response_time", [])
        if api_times:
            context["api_response_time_p95"] = self._percentile(api_times, 95)
            context["api_response_time_avg"] = sum(api_times) / len(api_times)
        
        # 错误率指标
        api_errors = self.metrics_cache.get("api_errors", [])
        api_requests = self.metrics_cache.get("api_requests", [])
        if api_requests and api_errors:
            context["api_error_rate"] = sum(api_errors) / sum(api_requests)
        
        # 数据库指标
        db_errors = self.metrics_cache.get("db_connection_errors", [])
        if db_errors:
            context["db_connection_errors"] = sum(db_errors[-10:])  # 最近10次
        
        # 系统指标
        memory_usage = self.metrics_cache.get("memory_usage_percent", [])
        if memory_usage:
            context["memory_usage_percent"] = memory_usage[-1]
        
        cpu_usage = self.metrics_cache.get("cpu_usage_percent", [])
        if cpu_usage:
            context["cpu_usage_percent"] = cpu_usage[-1]
        
        # 外部API指标
        external_errors = self.metrics_cache.get("external_api_errors", [])
        external_requests = self.metrics_cache.get("external_api_requests", [])
        if external_requests and external_errors:
            context["external_api_error_rate"] = sum(external_errors) / sum(external_requests)
        
        # 前端指标
        frontend_errors = self.metrics_cache.get("frontend_errors", [])
        frontend_requests = self.metrics_cache.get("frontend_requests", [])
        if frontend_requests and frontend_errors:
            context["frontend_error_rate"] = sum(frontend_errors) / sum(frontend_requests)
        
        return context
    
    def _evaluate_simple_condition(self, condition: str, context: Dict[str, float]) -> bool:
        """评估简单条件"""
        # 替换变量
        for var_name, value in context.items():
            condition = condition.replace(var_name, str(value))
        
        # 安全的表达式评估（仅支持基本比较操作）
        try:
            # 使用更安全的表达式评估方法
            # 只允许数字、运算符和比较符号，不允许函数调用
            import re
            import operator
            
            # 验证条件只包含安全的字符（数字、运算符、空格、括号）
            safe_pattern = re.compile(r'^[\d\s+\-*/().><=!&|]+$')
            if not safe_pattern.match(condition):
                logger.warning(f"不安全的条件表达式被拒绝: {condition}")
                return False
            
            # 使用 operator 模块进行安全的比较操作
            # 解析简单的比较表达式，如 "value > 3000"
            # 支持的操作符: >, <, >=, <=, ==, !=
            operators = {
                '>': operator.gt,
                '<': operator.lt,
                '>=': operator.ge,
                '<=': operator.le,
                '==': operator.eq,
                '!=': operator.ne,
            }
            
            # 尝试匹配比较表达式
            for op_symbol, op_func in operators.items():
                if op_symbol in condition:
                    parts = condition.split(op_symbol, 1)
                    if len(parts) == 2:
                        try:
                            left = float(parts[0].strip())
                            right = float(parts[1].strip())
                            return op_func(left, right)
                        except (ValueError, TypeError):
                            # 如果无法解析为数字，尝试使用 ast.literal_eval
                            import ast
                            try:
                                left = ast.literal_eval(parts[0].strip())
                                right = ast.literal_eval(parts[1].strip())
                                return op_func(left, right)
                            except (ValueError, SyntaxError):
                                logger.warning(f"无法解析条件表达式: {condition}")
                                return False
            
            # 如果没有匹配到比较操作符，尝试作为布尔表达式评估
            # 但只允许简单的数字表达式
            import ast
            try:
                # 使用 ast.literal_eval 评估简单的数字表达式
                result = ast.literal_eval(condition)
                return bool(result)
            except (ValueError, SyntaxError):
                logger.warning(f"无法解析条件表达式: {condition}")
                return False
                
        except Exception as e:
            logger.error(f"评估条件时出错: {condition}, 错误: {e}")
            return False
    
    def _percentile(self, values: List[float], percentile: int) -> float:
        """计算百分位数"""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    async def _trigger_alert(self, rule: AlertRule):
        """触发告警"""
        if rule.name in self.active_alerts:
            return  # 告警已经激活
        
        alert_id = f"alert_{rule.name}_{int(datetime.now().timestamp())}"
        alert = Alert(
            id=alert_id,
            rule_name=rule.name,
            level=rule.level,
            message=f"告警触发: {rule.description}",
            details={
                "rule": rule.name,
                "threshold": rule.threshold,
                "condition": rule.condition,
                "tags": rule.tags
            },
            timestamp=datetime.now()
        )
        
        self.active_alerts[rule.name] = alert
        self.alert_history.append(alert)
        
        # 发送告警通知
        await self._send_notifications(alert, rule.channels)
        
        logger.warning(f"Alert triggered: {rule.name} - {rule.description}")
    
    async def _resolve_alert(self, rule_name: str):
        """解决告警"""
        if rule_name in self.active_alerts:
            alert = self.active_alerts[rule_name]
            alert.resolved = True
            alert.resolved_at = datetime.now()
            
            del self.active_alerts[rule_name]
            
            logger.info(f"Alert resolved: {rule_name}")
    
    async def _send_notifications(self, alert: Alert, channels: List[AlertChannel]):
        """发送告警通知"""
        for channel in channels:
            try:
                if channel == AlertChannel.SLACK:
                    await self._send_slack_notification(alert)
                elif channel == AlertChannel.EMAIL:
                    await self._send_email_notification(alert)
                elif channel == AlertChannel.SMS:
                    await self._send_sms_notification(alert)
                elif channel == AlertChannel.WEBHOOK:
                    await self._send_webhook_notification(alert)
            except Exception as e:
                logger.error(f"Failed to send {channel.value} notification: {e}")
    
    async def _send_slack_notification(self, alert: Alert):
        """发送Slack通知"""
        webhook_url = getattr(settings, "SLACK_WEBHOOK_URL", None)
        if not webhook_url:
            return
        
        color = {
            AlertLevel.INFO: "good",
            AlertLevel.WARNING: "warning",
            AlertLevel.ERROR: "danger",
            AlertLevel.CRITICAL: "#ff0000"
        }.get(alert.level, "warning")
        
        payload = {
            "attachments": [
                {
                    "color": color,
                    "title": f"🚨 {alert.level.value.upper()}: {alert.rule_name}",
                    "text": alert.message,
                    "fields": [
                        {"title": "时间", "value": alert.timestamp.strftime("%Y-%m-%d %H:%M:%S"), "short": True},
                        {"title": "级别", "value": alert.level.value.upper(), "short": True},
                        {"title": "详情", "value": json.dumps(alert.details, indent=2, ensure_ascii=False), "short": False}
                    ],
                    "footer": "Web3Search Alert System",
                    "ts": int(alert.timestamp.timestamp())
                }
            ]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload) as response:
                if response.status != 200:
                    logger.error(f"Slack notification failed: {response.status}")
    
    async def _send_email_notification(self, alert: Alert):
        """发送邮件通知"""
        smtp_server = getattr(settings, "SMTP_SERVER", None)
        smtp_port = getattr(settings, "SMTP_PORT", 587)
        smtp_username = getattr(settings, "SMTP_USERNAME", None)
        smtp_password = getattr(settings, "SMTP_PASSWORD", None)
        recipient_emails = getattr(settings, "ALERT_EMAIL_RECIPIENTS", [])
        
        if not all([smtp_server, smtp_username, smtp_password, recipient_emails]):
            return
        
        msg = MIMEMultipart()
        msg['From'] = smtp_username
        msg['To'] = ', '.join(recipient_emails)
        msg['Subject'] = f"[{alert.level.value.upper()}] Web3Search Alert: {alert.rule_name}"
        
        body = f"""
        告警详情:
        
        规则名称: {alert.rule_name}
        告警级别: {alert.level.value.upper()}
        触发时间: {alert.timestamp.strftime("%Y-%m-%d %H:%M:%S")}
        告警消息: {alert.message}
        
        详细信息:
        {json.dumps(alert.details, indent=2, ensure_ascii=False)}
        """
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        try:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
            server.quit()
        except Exception as e:
            logger.error(f"Email notification failed: {e}")
    
    async def _send_sms_notification(self, alert: Alert):
        """发送短信通知（需要集成短信服务商）"""
        # 这里需要集成具体的短信服务商API
        # 例如：阿里云短信、腾讯云短信等
        logger.info(f"SMS notification would be sent for alert: {alert.rule_name}")
    
    async def _send_webhook_notification(self, alert: Alert):
        """发送Webhook通知"""
        webhook_url = getattr(settings, "ALERT_WEBHOOK_URL", None)
        if not webhook_url:
            return
        
        payload = {
            "alert": alert.to_dict(),
            "timestamp": datetime.now().isoformat()
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload) as response:
                if response.status != 200:
                    logger.error(f"Webhook notification failed: {response.status}")
    
    def get_active_alerts(self) -> List[Alert]:
        """获取活跃告警"""
        return list(self.active_alerts.values())
    
    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """获取告警历史"""
        return self.alert_history[-limit:]


# 全局告警管理器实例
alert_manager = AlertManager()
