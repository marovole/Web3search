"""
多层次告警机制系统
支持Slack、邮件、短信等多种告警渠道和升级策略
"""
import asyncio
import json
import logging
import smtplib
from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiohttp
import aiofiles
from abc import ABC, abstractmethod

from app.core.config import settings
from app.core.redis_client import get_redis_client
from app.core.log_aggregation import LogLevel, LogSource, log_aggregator

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """告警严重程度"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class AlertStatus(Enum):
    """告警状态"""
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


class NotificationChannel(Enum):
    """通知渠道"""
    SLACK = "slack"
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"
    DINGTALK = "dingtalk"
    WECHAT = "wechat"


@dataclass
class Alert:
    """告警对象"""
    alert_id: str
    title: str
    description: str
    severity: AlertSeverity
    status: AlertStatus
    source: str
    service: str
    environment: str
    timestamp: datetime
    labels: Dict[str, str] = None
    annotations: Dict[str, str] = None
    fingerprint: str = None
    rule_id: str = None
    threshold_value: float = None
    current_value: float = None
    evaluation_time: datetime = None
    resolved_time: datetime = None
    acknowledged_time: datetime = None
    acknowledged_by: str = None
    
    def __post_init__(self):
        if self.labels is None:
            self.labels = {}
        if self.annotations is None:
            self.annotations = {}
        if self.fingerprint is None:
            self.fingerprint = self._generate_fingerprint()
    
    def _generate_fingerprint(self) -> str:
        """生成告警指纹"""
        import hashlib
        content = f"{self.title}:{self.source}:{self.service}"
        return hashlib.md5(content.encode()).hexdigest()


@dataclass
class NotificationRule:
    """通知规则"""
    rule_id: str
    name: str
    severity_filter: List[AlertSeverity]
    source_filter: List[str] = None
    service_filter: List[str] = None
    channels: List[NotificationChannel] = None
    cooldown_minutes: int = 15
    max_notifications_per_hour: int = 10
    escalation_enabled: bool = True
    escalation_delay_minutes: int = 30
    enabled: bool = True
    
    def __post_init__(self):
        if self.source_filter is None:
            self.source_filter = []
        if self.service_filter is None:
            self.service_filter = []
        if self.channels is None:
            self.channels = [NotificationChannel.SLACK]


class NotificationProvider(ABC):
    """通知提供者抽象基类"""
    
    @abstractmethod
    async def send_notification(self, alert: Alert, message: str) -> bool:
        """发送通知"""
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """测试连接"""
        pass


class SlackProvider(NotificationProvider):
    """Slack通知提供者"""
    
    def __init__(self, webhook_url: str, channel: str = "#alerts"):
        self.webhook_url = webhook_url
        self.channel = channel
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def send_notification(self, alert: Alert, message: str) -> bool:
        """发送Slack通知"""
        try:
            # 根据严重程度选择颜色
            color_map = {
                AlertSeverity.INFO: "#36a64f",      # 绿色
                AlertSeverity.WARNING: "#ff9500",   # 橙色
                AlertSeverity.ERROR: "#ff0000",     # 红色
                AlertSeverity.CRITICAL: "#8b0000",  # 深红色
                AlertSeverity.EMERGENCY: "#000000"  # 黑色
            }
            
            color = color_map.get(alert.severity, "#36a64f")
            
            # 构建Slack消息
            payload = {
                "channel": self.channel,
                "username": "Web3search Alert",
                "icon_emoji": ":warning:",
                "attachments": [{
                    "color": color,
                    "title": f"[{alert.severity.value.upper()}] {alert.title}",
                    "text": alert.description,
                    "fields": [
                        {
                            "title": "Service",
                            "value": alert.service,
                            "short": True
                        },
                        {
                            "title": "Source",
                            "value": alert.source,
                            "short": True
                        },
                        {
                            "title": "Environment",
                            "value": alert.environment,
                            "short": True
                        },
                        {
                            "title": "Time",
                            "value": alert.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"),
                            "short": True
                        }
                    ],
                    "footer": "Web3search Monitoring",
                    "ts": int(alert.timestamp.timestamp())
                }]
            }
            
            # 添加标签信息
            if alert.labels:
                labels_text = "\n".join([f"• {k}: {v}" for k, v in alert.labels.items()])
                payload["attachments"][0]["fields"].append({
                    "title": "Labels",
                    "value": labels_text,
                    "short": False
                })
            
            # 发送消息
            async with self.session.post(self.webhook_url, json=payload) as response:
                if response.status == 200:
                    logger.info(f"Slack notification sent for alert {alert.alert_id}")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to send Slack notification: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error sending Slack notification: {e}")
            return False
    
    async def test_connection(self) -> bool:
        """测试Slack连接"""
        try:
            test_payload = {
                "channel": self.channel,
                "username": "Web3search Test",
                "text": "🔔 Slack notification test from Web3search monitoring system"
            }
            
            async with self.session.post(self.webhook_url, json=test_payload) as response:
                return response.status == 200
                
        except Exception as e:
            logger.error(f"Error testing Slack connection: {e}")
            return False


class EmailProvider(NotificationProvider):
    """邮件通知提供者"""
    
    def __init__(
        self, 
        smtp_server: str, 
        smtp_port: int, 
        username: str, 
        password: str,
        from_email: str,
        to_emails: List[str],
        use_tls: bool = True
    ):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.to_emails = to_emails
        self.use_tls = use_tls
    
    async def send_notification(self, alert: Alert, message: str) -> bool:
        """发送邮件通知"""
        try:
            # 创建邮件消息
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = ', '.join(self.to_emails)
            msg['Subject'] = f"[{alert.severity.value.upper()}] {alert.title}"
            
            # 构建邮件内容
            html_content = f"""
            <html>
            <body>
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <div style="background-color: {'#d4edda' if alert.severity == AlertSeverity.INFO else '#fff3cd' if alert.severity == AlertSeverity.WARNING else '#f8d7da' if alert.severity == AlertSeverity.ERROR else '#721c24'}; padding: 20px; border-radius: 5px; margin-bottom: 20px;">
                        <h2 style="color: {'#155724' if alert.severity == AlertSeverity.INFO else '#856404' if alert.severity == AlertSeverity.WARNING else '#721c24'}; margin: 0;">
                            {alert.severity.value.upper()} ALERT
                        </h2>
                        <h3 style="margin: 10px 0;">{alert.title}</h3>
                    </div>
                    
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px;">
                        <h4>Description:</h4>
                        <p>{alert.description}</p>
                    </div>
                    
                    <div style="background-color: #e9ecef; padding: 15px; border-radius: 5px;">
                        <h4>Details:</h4>
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr><td style="padding: 5px;"><strong>Service:</strong></td><td>{alert.service}</td></tr>
                            <tr><td style="padding: 5px;"><strong>Source:</strong></td><td>{alert.source}</td></tr>
                            <tr><td style="padding: 5px;"><strong>Environment:</strong></td><td>{alert.environment}</td></tr>
                            <tr><td style="padding: 5px;"><strong>Time:</strong></td><td>{alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}</td></tr>
                            <tr><td style="padding: 5px;"><strong>Alert ID:</strong></td><td>{alert.alert_id}</td></tr>
                        </table>
                    </div>
                    
                    {f'<div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; margin-top: 20px;"><h4>Current Value:</h4> {alert.current_value}</div>' if alert.current_value else ''}
                    {f'<div style="background-color: #f8d7da; padding: 15px; border-radius: 5px; margin-top: 20px;"><h4>Threshold:</h4> {alert.threshold_value}</div>' if alert.threshold_value else ''}
                    
                    <div style="margin-top: 30px; padding: 20px; background-color: #007bff; color: white; border-radius: 5px; text-align: center;">
                        <p>This alert was generated by Web3search Monitoring System</p>
                        <p style="font-size: 12px; margin-top: 10px;">If you believe this is an error, please contact the DevOps team</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html_content, 'html'))
            
            # 发送邮件
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            logger.info(f"Email notification sent for alert {alert.alert_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
            return False
    
    async def test_connection(self) -> bool:
        """测试邮件连接"""
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.username, self.password)
                return True
                
        except Exception as e:
            logger.error(f"Error testing email connection: {e}")
            return False


class SMSProvider(NotificationProvider):
    """短信通知提供者"""
    
    def __init__(self, provider: str, api_key: str, phone_numbers: List[str]):
        self.provider = provider
        self.api_key = api_key
        self.phone_numbers = phone_numbers
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def send_notification(self, alert: Alert, message: str) -> bool:
        """发送短信通知"""
        try:
            # 限制短信长度
            sms_message = f"[{alert.severity.value.upper()}] {alert.title}: {alert.description[:100]}"
            
            # 这里可以集成不同的短信服务商API
            # 示例：使用通用的HTTP API接口
            success_count = 0
            
            for phone_number in self.phone_numbers:
                payload = {
                    "api_key": self.api_key,
                    "phone": phone_number,
                    "message": sms_message
                }
                
                # 模拟短信API调用（实际需要根据具体服务商实现）
                async with self.session.post(f"https://api.{self.provider}.com/sms", json=payload) as response:
                    if response.status == 200:
                        success_count += 1
                        logger.info(f"SMS sent to {phone_number} for alert {alert.alert_id}")
                    else:
                        logger.error(f"Failed to send SMS to {phone_number}: {response.status}")
            
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Error sending SMS notification: {e}")
            return False
    
    async def test_connection(self) -> bool:
        """测试短信连接"""
        try:
            test_message = "Test message from Web3search monitoring system"
            
            for phone_number in self.phone_numbers[:1]:  # 只测试第一个号码
                payload = {
                    "api_key": self.api_key,
                    "phone": phone_number,
                    "message": test_message
                }
                
                async with self.session.post(f"https://api.{self.provider}.com/sms", json=payload) as response:
                    return response.status == 200
            
            return False
            
        except Exception as e:
            logger.error(f"Error testing SMS connection: {e}")
            return False


class WebhookProvider(NotificationProvider):
    """Webhook通知提供者"""
    
    def __init__(self, webhook_url: str, headers: Dict[str, str] = None):
        self.webhook_url = webhook_url
        self.headers = headers or {}
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def send_notification(self, alert: Alert, message: str) -> bool:
        """发送Webhook通知"""
        try:
            payload = {
                "alert_id": alert.alert_id,
                "title": alert.title,
                "description": alert.description,
                "severity": alert.severity.value,
                "status": alert.status.value,
                "source": alert.source,
                "service": alert.service,
                "environment": alert.environment,
                "timestamp": alert.timestamp.isoformat(),
                "labels": alert.labels,
                "annotations": alert.annotations,
                "current_value": alert.current_value,
                "threshold_value": alert.threshold_value
            }
            
            # 设置默认headers
            headers = {"Content-Type": "application/json"}
            headers.update(self.headers)
            
            async with self.session.post(self.webhook_url, json=payload, headers=headers) as response:
                if response.status in [200, 201, 204]:
                    logger.info(f"Webhook notification sent for alert {alert.alert_id}")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to send webhook notification: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error sending webhook notification: {e}")
            return False
    
    async def test_connection(self) -> bool:
        """测试Webhook连接"""
        try:
            test_payload = {
                "test": True,
                "message": "Test webhook from Web3search monitoring system",
                "timestamp": datetime.now().isoformat()
            }
            
            headers = {"Content-Type": "application/json"}
            headers.update(self.headers)
            
            async with self.session.post(self.webhook_url, json=test_payload, headers=headers) as response:
                return response.status in [200, 201, 204]
                
        except Exception as e:
            logger.error(f"Error testing webhook connection: {e}")
            return False


class AlertEscalationManager:
    """
    告警升级管理器
    负责告警升级策略和执行
    """
    
    def __init__(self):
        self.redis_client = None
        self.escalation_rules: Dict[str, Dict[str, Any]] = {}
        
    async def initialize(self):
        """初始化升级管理器"""
        self.redis_client = get_redis_client()
        await self._load_default_rules()
    
    async def should_escalate(self, alert: Alert) -> bool:
        """判断是否应该升级"""
        try:
            # 检查告警是否已经升级
            escalation_key = f"alert_escalation:{alert.alert_id}"
            escalated = await self.redis_client.get(escalation_key)
            
            if escalated:
                return False
            
            # 检查告警持续时间
            alert_age = datetime.now() - alert.timestamp
            escalation_delay = timedelta(minutes=30)  # 默认30分钟后升级
            
            # 根据严重程度调整升级延迟
            if alert.severity == AlertSeverity.CRITICAL:
                escalation_delay = timedelta(minutes=10)
            elif alert.severity == AlertSeverity.EMERGENCY:
                escalation_delay = timedelta(minutes=5)
            
            return alert_age > escalation_delay
            
        except Exception as e:
            logger.error(f"Error checking escalation: {e}")
            return False
    
    async def escalate_alert(self, alert: Alert) -> bool:
        """升级告警"""
        try:
            # 标记为已升级
            escalation_key = f"alert_escalation:{alert.alert_id}"
            await self.redis_client.setex(
                escalation_key, 
                3600,  # 1小时过期
                datetime.now().isoformat()
            )
            
            # 升级策略：发送到更高级别的通知渠道
            escalation_channels = []
            
            if alert.severity in [AlertSeverity.ERROR, AlertSeverity.WARNING]:
                escalation_channels.extend([NotificationChannel.EMAIL])
            
            if alert.severity in [AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY]:
                escalation_channels.extend([NotificationChannel.SMS, NotificationChannel.WEBHOOK])
            
            # 发送升级通知
            for channel in escalation_channels:
                await alert_manager._send_notification_via_channel(alert, channel, escalated=True)
            
            logger.info(f"Alert {alert.alert_id} escalated to channels: {[c.value for c in escalation_channels]}")
            return True
            
        except Exception as e:
            logger.error(f"Error escalating alert: {e}")
            return False
    
    async def _load_default_rules(self):
        """加载默认升级规则"""
        self.escalation_rules = {
            "default": {
                "delay_minutes": 30,
                "escalation_channels": ["email", "sms"],
                "max_escalations": 3
            },
            "critical": {
                "delay_minutes": 10,
                "escalation_channels": ["sms", "webhook"],
                "max_escalations": 5
            },
            "emergency": {
                "delay_minutes": 5,
                "escalation_channels": ["sms", "webhook", "phone_call"],
                "max_escalations": 10
            }
        }


class AlertManager:
    """
    告警管理器
    统一管理告警的创建、发送、升级和状态管理
    """
    
    def __init__(self):
        self.redis_client = None
        self.providers: Dict[NotificationChannel, NotificationProvider] = {}
        self.notification_rules: Dict[str, NotificationRule] = {}
        self.escalation_manager = AlertEscalationManager()
        self.running = False
        self.escalation_task = None
        
    async def initialize(self):
        """初始化告警管理器"""
        if self.running:
            return
        
        self.redis_client = get_redis_client()
        await self.escalation_manager.initialize()
        
        # 初始化通知提供者
        await self._initialize_providers()
        
        # 加载通知规则
        await self._load_notification_rules()
        
        # 启动升级检查任务
        self.running = True
        self.escalation_task = asyncio.create_task(self._escalation_check_loop())
        
        logger.info("Alert manager initialized")
    
    async def shutdown(self):
        """关闭告警管理器"""
        self.running = False
        if self.escalation_task:
            self.escalation_task.cancel()
            try:
                await self.escalation_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Alert manager shutdown")
    
    async def create_alert(
        self,
        title: str,
        description: str,
        severity: AlertSeverity,
        source: str,
        service: str,
        environment: str = "production",
        labels: Dict[str, str] = None,
        annotations: Dict[str, str] = None,
        current_value: float = None,
        threshold_value: float = None
    ) -> Alert:
        """
        创建告警
        
        Args:
            title: 告警标题
            description: 告警描述
            severity: 严重程度
            source: 告警来源
            service: 服务名称
            environment: 环境
            labels: 标签
            annotations: 注释
            current_value: 当前值
            threshold_value: 阈值
        """
        try:
            # 生成告警ID
            alert_id = f"alert_{int(datetime.now().timestamp() * 1000)}"
            
            # 创建告警对象
            alert = Alert(
                alert_id=alert_id,
                title=title,
                description=description,
                severity=severity,
                status=AlertStatus.OPEN,
                source=source,
                service=service,
                environment=environment,
                timestamp=datetime.now(),
                labels=labels or {},
                annotations=annotations or {},
                current_value=current_value,
                threshold_value=threshold_value,
                evaluation_time=datetime.now()
            )
            
            # 存储告警
            await self._store_alert(alert)
            
            # 发送通知
            await self._send_notifications(alert)
            
            logger.info(f"Created alert {alert_id}: {title}")
            return alert
            
        except Exception as e:
            logger.error(f"Error creating alert: {e}")
            raise
    
    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """确认告警"""
        try:
            alert = await self._get_alert(alert_id)
            if not alert:
                return False
            
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_time = datetime.now()
            alert.acknowledged_by = acknowledged_by
            
            await self._store_alert(alert)
            
            logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")
            return True
            
        except Exception as e:
            logger.error(f"Error acknowledging alert: {e}")
            return False
    
    async def resolve_alert(self, alert_id: str) -> bool:
        """解决告警"""
        try:
            alert = await self._get_alert(alert_id)
            if not alert:
                return False
            
            alert.status = AlertStatus.RESOLVED
            alert.resolved_time = datetime.now()
            
            await self._store_alert(alert)
            
            # 发送解决通知
            await self._send_resolution_notification(alert)
            
            logger.info(f"Alert {alert_id} resolved")
            return True
            
        except Exception as e:
            logger.error(f"Error resolving alert: {e}")
            return False
    
    async def get_alerts(
        self, 
        status: AlertStatus = None,
        severity: AlertSeverity = None,
        service: str = None,
        limit: int = 100
    ) -> List[Alert]:
        """获取告警列表"""
        try:
            alerts = []
            
            # 从Redis获取告警
            async for key in self.redis_client.scan_iter(match="alert:*"):
                alert_data = await self.redis_client.get(key)
                if alert_data:
                    alert = self._deserialize_alert(alert_data)
                    
                    # 应用过滤条件
                    if status and alert.status != status:
                        continue
                    if severity and alert.severity != severity:
                        continue
                    if service and alert.service != service:
                        continue
                    
                    alerts.append(alert)
            
            # 按时间戳排序
            alerts.sort(key=lambda x: x.timestamp, reverse=True)
            
            return alerts[:limit]
            
        except Exception as e:
            logger.error(f"Error getting alerts: {e}")
            return []
    
    async def _initialize_providers(self):
        """初始化通知提供者"""
        # Slack提供者
        if settings.SLACK_WEBHOOK_URL:
            self.providers[NotificationChannel.SLACK] = SlackProvider(
                webhook_url=settings.SLACK_WEBHOOK_URL,
                channel=settings.SLACK_CHANNEL or "#alerts"
            )
        
        # 邮件提供者
        if all([
            settings.SMTP_SERVER,
            settings.SMTP_PORT,
            settings.SMTP_USERNAME,
            settings.SMTP_PASSWORD,
            settings.SMTP_FROM_EMAIL,
            settings.SMTP_TO_EMAILS
        ]):
            self.providers[NotificationChannel.EMAIL] = EmailProvider(
                smtp_server=settings.SMTP_SERVER,
                smtp_port=settings.SMTP_PORT,
                username=settings.SMTP_USERNAME,
                password=settings.SMTP_PASSWORD,
                from_email=settings.SMTP_FROM_EMAIL,
                to_emails=settings.SMTP_TO_EMAILS.split(","),
                use_tls=settings.SMTP_USE_TLS
            )
        
        # SMS提供者
        if settings.SMS_PROVIDER and settings.SMS_API_KEY and settings.SMS_PHONE_NUMBERS:
            self.providers[NotificationChannel.SMS] = SMSProvider(
                provider=settings.SMS_PROVIDER,
                api_key=settings.SMS_API_KEY,
                phone_numbers=settings.SMS_PHONE_NUMBERS.split(",")
            )
        
        # Webhook提供者
        if settings.ALERT_WEBHOOK_URL:
            self.providers[NotificationChannel.WEBHOOK] = WebhookProvider(
                webhook_url=settings.ALERT_WEBHOOK_URL,
                headers=settings.ALERT_WEBHOOK_HEADERS or {}
            )
    
    async def _load_notification_rules(self):
        """加载通知规则"""
        # 默认规则
        default_rule = NotificationRule(
            rule_id="default",
            name="Default Notification Rule",
            severity_filter=[AlertSeverity.WARNING, AlertSeverity.ERROR, AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY],
            channels=[NotificationChannel.SLACK],
            cooldown_minutes=15,
            max_notifications_per_hour=10,
            escalation_enabled=True
        )
        
        critical_rule = NotificationRule(
            rule_id="critical",
            name="Critical Alert Rule",
            severity_filter=[AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY],
            channels=[NotificationChannel.SLACK, NotificationChannel.EMAIL, NotificationChannel.SMS],
            cooldown_minutes=5,
            max_notifications_per_hour=20,
            escalation_enabled=True,
            escalation_delay_minutes=10
        )
        
        self.notification_rules = {
            "default": default_rule,
            "critical": critical_rule
        }
    
    async def _send_notifications(self, alert: Alert):
        """发送告警通知"""
        try:
            # 查找适用的通知规则
            applicable_rules = []
            
            for rule in self.notification_rules.values():
                if not rule.enabled:
                    continue
                
                if alert.severity in rule.severity_filter:
                    # 检查服务过滤
                    if rule.service_filter and alert.service not in rule.service_filter:
                        continue
                    
                    # 检查来源过滤
                    if rule.source_filter and alert.source not in rule.source_filter:
                        continue
                    
                    applicable_rules.append(rule)
            
            # 发送通知
            for rule in applicable_rules:
                if await self._check_cooldown(alert, rule):
                    for channel in rule.channels:
                        await self._send_notification_via_channel(alert, channel)
                    
                    # 设置冷却时间
                    await self._set_cooldown(alert, rule)
            
        except Exception as e:
            logger.error(f"Error sending notifications: {e}")
    
    async def _send_notification_via_channel(
        self, 
        alert: Alert, 
        channel: NotificationChannel,
        escalated: bool = False
    ):
        """通过指定渠道发送通知"""
        try:
            provider = self.providers.get(channel)
            if not provider:
                logger.warning(f"No provider configured for channel {channel.value}")
                return
            
            # 构建通知消息
            message = self._build_notification_message(alert, escalated)
            
            # 发送通知
            if channel in [NotificationChannel.SLACK, NotificationChannel.WEBHOOK]:
                async with provider as p:
                    await p.send_notification(alert, message)
            else:
                await provider.send_notification(alert, message)
            
        except Exception as e:
            logger.error(f"Error sending notification via {channel.value}: {e}")
    
    def _build_notification_message(self, alert: Alert, escalated: bool = False) -> str:
        """构建通知消息"""
        escalation_text = "🔥 ESCALATED ALERT 🔥\n" if escalated else ""
        
        message = f"""
{escalation_text}[{alert.severity.value.upper()}] {alert.title}

Description: {alert.description}

Service: {alert.service}
Source: {alert.source}
Environment: {alert.environment}
Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}
Alert ID: {alert.alert_id}
        """
        
        if alert.current_value is not None and alert.threshold_value is not None:
            message += f"\nCurrent Value: {alert.current_value}\nThreshold: {alert.threshold_value}"
        
        if alert.labels:
            labels_text = "\n".join([f"• {k}: {v}" for k, v in alert.labels.items()])
            message += f"\n\nLabels:\n{labels_text}"
        
        return message.strip()
    
    async def _check_cooldown(self, alert: Alert, rule: NotificationRule) -> bool:
        """检查冷却时间"""
        try:
            cooldown_key = f"alert_cooldown:{alert.fingerprint}:{rule.rule_id}"
            last_sent = await self.redis_client.get(cooldown_key)
            
            if last_sent:
                last_sent_time = datetime.fromisoformat(last_sent.decode())
                if datetime.now() - last_sent_time < timedelta(minutes=rule.cooldown_minutes):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking cooldown: {e}")
            return True
    
    async def _set_cooldown(self, alert: Alert, rule: NotificationRule):
        """设置冷却时间"""
        try:
            cooldown_key = f"alert_cooldown:{alert.fingerprint}:{rule.rule_id}"
            await self.redis_client.setex(
                cooldown_key,
                rule.cooldown_minutes * 60,
                datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error setting cooldown: {e}")
    
    async def _store_alert(self, alert: Alert):
        """存储告警"""
        try:
            alert_key = f"alert:{alert.alert_id}"
            alert_data = self._serialize_alert(alert)
            
            await self.redis_client.setex(
                alert_key,
                7 * 24 * 3600,  # 7天过期
                alert_data
            )
            
        except Exception as e:
            logger.error(f"Error storing alert: {e}")
    
    async def _get_alert(self, alert_id: str) -> Optional[Alert]:
        """获取告警"""
        try:
            alert_key = f"alert:{alert_id}"
            alert_data = await self.redis_client.get(alert_key)
            
            if alert_data:
                return self._deserialize_alert(alert_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting alert: {e}")
            return None
    
    def _serialize_alert(self, alert: Alert) -> str:
        """序列化告警"""
        alert_dict = asdict(alert)
        alert_dict["severity"] = alert.severity.value
        alert_dict["status"] = alert.status.value
        alert_dict["timestamp"] = alert.timestamp.isoformat()
        
        if alert.evaluation_time:
            alert_dict["evaluation_time"] = alert.evaluation_time.isoformat()
        if alert.resolved_time:
            alert_dict["resolved_time"] = alert.resolved_time.isoformat()
        if alert.acknowledged_time:
            alert_dict["acknowledged_time"] = alert.acknowledged_time.isoformat()
        
        return json.dumps(alert_dict)
    
    def _deserialize_alert(self, alert_data: str) -> Alert:
        """反序列化告警"""
        alert_dict = json.loads(alert_data)
        
        # 转换枚举类型
        alert_dict["severity"] = AlertSeverity(alert_dict["severity"])
        alert_dict["status"] = AlertStatus(alert_dict["status"])
        alert_dict["timestamp"] = datetime.fromisoformat(alert_dict["timestamp"])
        
        if alert_dict.get("evaluation_time"):
            alert_dict["evaluation_time"] = datetime.fromisoformat(alert_dict["evaluation_time"])
        if alert_dict.get("resolved_time"):
            alert_dict["resolved_time"] = datetime.fromisoformat(alert_dict["resolved_time"])
        if alert_dict.get("acknowledged_time"):
            alert_dict["acknowledged_time"] = datetime.fromisoformat(alert_dict["acknowledged_time"])
        
        return Alert(**alert_dict)
    
    async def _send_resolution_notification(self, alert: Alert):
        """发送解决通知"""
        try:
            resolution_message = f"""
✅ RESOLVED ALERT

Original Alert: {alert.title}
Service: {alert.service}
Source: {alert.source}
Resolved At: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
Alert ID: {alert.alert_id}
            """
            
            # 只发送到已确认的渠道
            for channel in [NotificationChannel.SLACK]:
                await self._send_notification_via_channel(alert, channel)
            
        except Exception as e:
            logger.error(f"Error sending resolution notification: {e}")
    
    async def _escalation_check_loop(self):
        """升级检查循环"""
        while self.running:
            try:
                await asyncio.sleep(60)  # 每分钟检查一次
                
                # 获取所有活跃告警
                active_alerts = await self.get_alerts(status=AlertStatus.OPEN)
                
                for alert in active_alerts:
                    if await self.escalation_manager.should_escalate(alert):
                        await self.escalation_manager.escalate_alert(alert)
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in escalation check loop: {e}")


# 全局告警管理器实例
alert_manager = AlertManager()
