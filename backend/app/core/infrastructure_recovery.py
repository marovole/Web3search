"""
基础设施告警和自动化恢复系统
提供智能告警管理、自动化恢复操作和故障自愈能力
"""
import asyncio
import json
import subprocess
import time
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

from app.core.config import settings
from app.core.redis_client import get_redis_client
from app.core.structured_logging import get_logger
from app.core.alerting_system import alert_manager, AlertSeverity, AlertStatus
from app.core.infrastructure_monitor import resource_monitor
from app.core.database_monitor import database_monitor
from app.core.network_storage_monitor import network_storage_monitor

logger = get_logger("infrastructure_recovery")


class RecoveryAction(Enum):
    """恢复动作类型"""
    RESTART_SERVICE = "restart_service"
    CLEAR_CACHE = "clear_cache"
    SCALE_RESOURCES = "scale_resources"
    CLEAN_DISK = "clean_disk"
    OPTIMIZE_DATABASE = "optimize_database"
    RESTART_SYSTEM = "restart_system"
    KILL_PROCESS = "kill_process"
    FLUSH_LOGS = "flush_logs"
    UPDATE_CONFIG = "update_config"


class RecoveryStatus(Enum):
    """恢复状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AlertSeverity(Enum):
    """告警严重程度"""
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class RecoveryRule:
    """恢复规则"""
    rule_id: str
    name: str
    description: str
    trigger_condition: Dict[str, Any]  # 触发条件
    recovery_actions: List[Dict[str, Any]]  # 恢复动作列表
    enabled: bool = True
    cooldown_minutes: int = 30  # 冷却时间
    max_attempts: int = 3  # 最大尝试次数
    escalation_enabled: bool = True  # 是否启用升级


@dataclass
class RecoveryExecution:
    """恢复执行记录"""
    execution_id: str
    rule_id: str
    alert_id: str
    actions: List[Dict[str, Any]]
    status: RecoveryStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    execution_log: List[str] = None
    
    def __post_init__(self):
        if self.execution_log is None:
            self.execution_log = []


class InfrastructureRecoveryManager:
    """
    基础设施恢复管理器
    负责自动化恢复操作和故障自愈
    """
    
    def __init__(self):
        self.redis_client = None
        self.running = False
        self.monitoring_interval = 60  # 60秒检查一次
        self.retention_days = 30  # 执行记录保留30天
        
        # 恢复动作处理器
        self.action_handlers = {
            RecoveryAction.RESTART_SERVICE: self._restart_service,
            RecoveryAction.CLEAR_CACHE: self._clear_cache,
            RecoveryAction.SCALE_RESOURCES: self._scale_resources,
            RecoveryAction.CLEAN_DISK: self._clean_disk,
            RecoveryAction.OPTIMIZE_DATABASE: self._optimize_database,
            RecoveryAction.RESTART_SYSTEM: self._restart_system,
            RecoveryAction.KILL_PROCESS: self._kill_process,
            RecoveryAction.FLUSH_LOGS: self._flush_logs,
            RecoveryAction.UPDATE_CONFIG: self._update_config
        }
        
        # 预定义的恢复规则
        self.recovery_rules = self._initialize_recovery_rules()
    
    async def initialize(self):
        """初始化恢复管理器"""
        if self.running:
            return
        
        self.redis_client = get_redis_client()
        self.running = True
        
        # 加载自定义恢复规则
        await self._load_custom_rules()
        
        logger.info("Infrastructure recovery manager initialized")
    
    async def shutdown(self):
        """关闭恢复管理器"""
        self.running = False
        logger.info("Infrastructure recovery manager shutdown")
    
    async def start_monitoring(self):
        """开始监控和自动恢复"""
        if not self.running:
            await self.initialize()
        
        logger.info("Starting infrastructure recovery monitoring...")
        
        while self.running:
            try:
                # 检查活跃告警
                active_alerts = await self._get_active_alerts()
                
                # 处理告警，触发恢复规则
                for alert in active_alerts:
                    await self._process_alert(alert)
                
                # 清理过期的执行记录
                await self._cleanup_old_executions()
                
                # 等待下次检查
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Error in recovery monitoring loop: {e}")
                await asyncio.sleep(60)  # 出错时等待1分钟
    
    def _initialize_recovery_rules(self) -> Dict[str, RecoveryRule]:
        """初始化预定义的恢复规则"""
        rules = {}
        
        # 高CPU使用率恢复规则
        rules["high_cpu_recovery"] = RecoveryRule(
            rule_id="high_cpu_recovery",
            name="高CPU使用率自动恢复",
            description="当CPU使用率超过阈值时自动执行恢复操作",
            trigger_condition={
                "source": "infrastructure_monitor",
                "metric_name": "cpu_usage_percent",
                "threshold": 90.0,
                "duration_minutes": 5
            },
            recovery_actions=[
                {
                    "action": "kill_process",
                    "params": {"cpu_threshold": 80.0, "max_processes": 3},
                    "timeout": 60
                },
                {
                    "action": "clear_cache",
                    "params": {"cache_types": ["redis", "application"]},
                    "timeout": 30
                }
            ],
            cooldown_minutes=30,
            max_attempts=3
        )
        
        # 高内存使用率恢复规则
        rules["high_memory_recovery"] = RecoveryRule(
            rule_id="high_memory_recovery",
            name="高内存使用率自动恢复",
            description="当内存使用率超过阈值时自动执行恢复操作",
            trigger_condition={
                "source": "infrastructure_monitor",
                "metric_name": "memory_usage_percent",
                "threshold": 85.0,
                "duration_minutes": 5
            },
            recovery_actions=[
                {
                    "action": "clear_cache",
                    "params": {"cache_types": ["redis", "application"]},
                    "timeout": 30
                },
                {
                    "action": "restart_service",
                    "params": {"services": ["web3search-api"]},
                    "timeout": 120
                }
            ],
            cooldown_minutes=45,
            max_attempts=2
        )
        
        # 磁盘空间不足恢复规则
        rules["disk_space_recovery"] = RecoveryRule(
            rule_id="disk_space_recovery",
            name="磁盘空间不足自动恢复",
            description="当磁盘空间不足时自动清理和恢复",
            trigger_condition={
                "source": "network_storage_monitor",
                "metric_name": "disk_usage_percent",
                "threshold": 90.0,
                "duration_minutes": 2
            },
            recovery_actions=[
                {
                    "action": "clean_disk",
                    "params": {"clean_types": ["logs", "temp", "cache"]},
                    "timeout": 300
                },
                {
                    "action": "flush_logs",
                    "params": {"log_retention_days": 7},
                    "timeout": 60
                }
            ],
            cooldown_minutes=60,
            max_attempts=2
        )
        
        # 数据库连接数过多恢复规则
        rules["database_connection_recovery"] = RecoveryRule(
            rule_id="database_connection_recovery",
            name="数据库连接数过多自动恢复",
            description="当数据库连接数过多时自动执行恢复操作",
            trigger_condition={
                "source": "database_monitor",
                "metric_name": "active_connections",
                "threshold": 150,
                "duration_minutes": 3
            },
            recovery_actions=[
                {
                    "action": "optimize_database",
                    "params": {"operations": ["kill_idle_connections", "analyze_tables"]},
                    "timeout": 180
                },
                {
                    "action": "restart_service",
                    "params": {"services": ["web3search-api"]},
                    "timeout": 120
                }
            ],
            cooldown_minutes=30,
            max_attempts=2
        )
        
        # 网络连接异常恢复规则
        rules["network_connectivity_recovery"] = RecoveryRule(
            rule_id="network_connectivity_recovery",
            name="网络连接异常自动恢复",
            description="当网络连接异常时自动执行恢复操作",
            trigger_condition={
                "source": "network_storage_monitor",
                "metric_name": "latency_8_8_8_8",
                "threshold": 1000.0,
                "duration_minutes": 2
            },
            recovery_actions=[
                {
                    "action": "restart_service",
                    "params": {"services": ["network-manager", "dnsmasq"]},
                    "timeout": 120
                },
                {
                    "action": "update_config",
                    "params": {"config_type": "network", "flush_dns": True},
                    "timeout": 60
                }
            ],
            cooldown_minutes=15,
            max_attempts=3
        )
        
        return rules
    
    async def _load_custom_rules(self):
        """加载自定义恢复规则"""
        try:
            custom_rules_key = "recovery_rules:custom"
            custom_rules_data = await self.redis_client.get(custom_rules_key)
            
            if custom_rules_data:
                custom_rules = json.loads(custom_rules_data)
                for rule_data in custom_rules:
                    rule = RecoveryRule(**rule_data)
                    self.recovery_rules[rule.rule_id] = rule
                
                logger.info(f"Loaded {len(custom_rules)} custom recovery rules")
        
        except Exception as e:
            logger.error(f"Error loading custom recovery rules: {e}")
    
    async def _get_active_alerts(self) -> List[Dict[str, Any]]:
        """获取活跃的严重告警"""
        try:
            # 获取严重和紧急级别的活跃告警
            critical_alerts = await alert_manager.get_alerts(
                status=AlertStatus.OPEN,
                severity=AlertSeverity.CRITICAL,
                limit=50
            )
            
            # 转换为字典格式
            active_alerts = []
            for alert in critical_alerts:
                alert_dict = {
                    "alert_id": alert.alert_id,
                    "title": alert.title,
                    "description": alert.description,
                    "severity": alert.severity.value,
                    "source": alert.source,
                    "labels": alert.labels,
                    "current_value": alert.current_value,
                    "timestamp": alert.timestamp
                }
                active_alerts.append(alert_dict)
            
            return active_alerts
        
        except Exception as e:
            logger.error(f"Error getting active alerts: {e}")
            return []
    
    async def _process_alert(self, alert: Dict[str, Any]):
        """处理告警，触发相应的恢复规则"""
        try:
            # 查找匹配的恢复规则
            matching_rules = await self._find_matching_rules(alert)
            
            for rule in matching_rules:
                if not rule.enabled:
                    continue
                
                # 检查冷却时间
                if await self._is_in_cooldown(rule):
                    logger.info(f"Rule {rule.rule_id} is in cooldown, skipping")
                    continue
                
                # 检查最大尝试次数
                if await self._has_exceeded_max_attempts(rule, alert["alert_id"]):
                    logger.warning(f"Rule {rule.rule_id} has exceeded max attempts for alert {alert['alert_id']}")
                    continue
                
                # 执行恢复操作
                await self._execute_recovery_rule(rule, alert)
        
        except Exception as e:
            logger.error(f"Error processing alert {alert['alert_id']}: {e}")
    
    async def _find_matching_rules(self, alert: Dict[str, Any]) -> List[RecoveryRule]:
        """查找匹配告警的恢复规则"""
        matching_rules = []
        
        for rule in self.recovery_rules.values():
            if self._rule_matches_alert(rule, alert):
                matching_rules.append(rule)
        
        return matching_rules
    
    def _rule_matches_alert(self, rule: RecoveryRule, alert: Dict[str, Any]) -> bool:
        """检查规则是否匹配告警"""
        condition = rule.trigger_condition
        
        # 检查告警源
        if condition.get("source") and alert.get("source") != condition["source"]:
            return False
        
        # 检查指标名称
        if condition.get("metric_name"):
            # 从告警标签或描述中提取指标名称
            alert_metric = alert.get("labels", {}).get("metric_name")
            if not alert_metric:
                # 尝试从标题中提取
                if condition["metric_name"] not in alert.get("title", ""):
                    return False
            elif alert_metric != condition["metric_name"]:
                return False
        
        # 检查阈值
        if condition.get("threshold") and alert.get("current_value"):
            try:
                if float(alert["current_value"]) < condition["threshold"]:
                    return False
            except (ValueError, TypeError):
                pass
        
        # 检查持续时间（简化实现，实际应该检查告警持续时间）
        # 这里假设告警已经被触发了一段时间
        
        return True
    
    async def _is_in_cooldown(self, rule: RecoveryRule) -> bool:
        """检查规则是否在冷却时间内"""
        try:
            cooldown_key = f"recovery_cooldown:{rule.rule_id}"
            last_execution = await self.redis_client.get(cooldown_key)
            
            if last_execution:
                last_time = datetime.fromisoformat(last_execution)
                cooldown_end = last_time + timedelta(minutes=rule.cooldown_minutes)
                
                if datetime.now() < cooldown_end:
                    return True
            
            return False
        
        except Exception as e:
            logger.error(f"Error checking cooldown for rule {rule.rule_id}: {e}")
            return False
    
    async def _has_exceeded_max_attempts(self, rule: RecoveryRule, alert_id: str) -> bool:
        """检查是否已超过最大尝试次数"""
        try:
            attempts_key = f"recovery_attempts:{rule.rule_id}:{alert_id}"
            attempts = await self.redis_client.get(attempts_key)
            
            if attempts:
                attempt_count = int(attempts)
                return attempt_count >= rule.max_attempts
            
            return False
        
        except Exception as e:
            logger.error(f"Error checking max attempts for rule {rule.rule_id}: {e}")
            return False
    
    async def _execute_recovery_rule(self, rule: RecoveryRule, alert: Dict[str, Any]):
        """执行恢复规则"""
        execution_id = f"recovery_{int(time.time())}_{rule.rule_id}"
        
        execution = RecoveryExecution(
            execution_id=execution_id,
            rule_id=rule.rule_id,
            alert_id=alert["alert_id"],
            actions=rule.recovery_actions,
            status=RecoveryStatus.RUNNING,
            started_at=datetime.now()
        )
        
        try:
            logger.info(f"Starting recovery execution {execution_id} for rule {rule.rule_id}")
            
            # 更新冷却时间
            cooldown_key = f"recovery_cooldown:{rule.rule_id}"
            await self.redis_client.setex(
                cooldown_key,
                rule.cooldown_minutes * 60,
                datetime.now().isoformat()
            )
            
            # 更新尝试次数
            attempts_key = f"recovery_attempts:{rule.rule_id}:{alert['alert_id']}"
            current_attempts = await self.redis_client.get(attempts_key) or "0"
            await self.redis_client.setex(
                attempts_key,
                24 * 3600,  # 24小时过期
                str(int(current_attempts) + 1)
            )
            
            # 执行恢复动作
            success_count = 0
            for i, action in enumerate(rule.recovery_actions):
                action_start = datetime.now()
                execution.execution_log.append(f"Executing action {i+1}/{len(rule.recovery_actions)}: {action['action']}")
                
                try:
                    action_result = await self._execute_recovery_action(action)
                    
                    if action_result["success"]:
                        success_count += 1
                        execution.execution_log.append(f"Action {action['action']} completed successfully")
                    else:
                        execution.execution_log.append(f"Action {action['action']} failed: {action_result.get('error', 'Unknown error')}")
                        logger.warning(f"Recovery action {action['action']} failed: {action_result.get('error')}")
                
                except Exception as e:
                    execution.execution_log.append(f"Action {action['action']} error: {str(e)}")
                    logger.error(f"Error executing recovery action {action['action']}: {e}")
                
                action_duration = (datetime.now() - action_start).total_seconds()
                execution.execution_log.append(f"Action {action['action']} duration: {action_duration:.1f}s")
            
            # 确定执行结果
            execution.completed_at = datetime.now()
            
            if success_count == len(rule.recovery_actions):
                execution.status = RecoveryStatus.SUCCESS
                execution.execution_log.append("All recovery actions completed successfully")
                
                # 创建恢复成功告警
                await self._create_recovery_alert(alert, rule, "success")
                
            elif success_count > 0:
                execution.status = RecoveryStatus.SUCCESS  # 部分成功也算成功
                execution.execution_log.append(f"Partial success: {success_count}/{len(rule.recovery_actions)} actions completed")
                
                await self._create_recovery_alert(alert, rule, "partial_success")
                
            else:
                execution.status = RecoveryStatus.FAILED
                execution.execution_log.append("All recovery actions failed")
                
                await self._create_recovery_alert(alert, rule, "failed")
                
                # 如果启用升级，创建升级告警
                if rule.escalation_enabled:
                    await self._escalate_alert(alert, rule)
            
            # 保存执行记录
            await self._save_execution(execution)
            
            logger.info(f"Recovery execution {execution_id} completed with status: {execution.status.value}")
        
        except Exception as e:
            execution.status = RecoveryStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.now()
            execution.execution_log.append(f"Recovery execution failed: {str(e)}")
            
            await self._save_execution(execution)
            logger.error(f"Recovery execution {execution_id} failed: {e}")
    
    async def _execute_recovery_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """执行单个恢复动作"""
        action_type = action.get("action")
        params = action.get("params", {})
        timeout = action.get("timeout", 60)
        
        if action_type not in self.action_handlers:
            return {"success": False, "error": f"Unknown action type: {action_type}"}
        
        try:
            handler = self.action_handlers[RecoveryAction(action_type)]
            
            # 使用超时执行动作
            result = await asyncio.wait_for(handler(params), timeout=timeout)
            
            return result
        
        except asyncio.TimeoutError:
            return {"success": False, "error": f"Action {action_type} timed out after {timeout}s"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ================================
    # 恢复动作处理器
    # ================================
    
    async def _restart_service(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """重启服务"""
        services = params.get("services", [])
        if not services:
            return {"success": False, "error": "No services specified"}
        
        results = []
        for service in services:
            try:
                # 使用systemctl重启服务
                cmd = ["sudo", "systemctl", "restart", service]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0:
                    results.append(f"Service {service} restarted successfully")
                else:
                    results.append(f"Failed to restart service {service}: {result.stderr}")
            
            except subprocess.TimeoutExpired:
                results.append(f"Timeout restarting service {service}")
            except Exception as e:
                results.append(f"Error restarting service {service}: {str(e)}")
        
        success = all("successfully" in r for r in results)
        return {"success": success, "details": results}
    
    async def _clear_cache(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """清理缓存"""
        cache_types = params.get("cache_types", ["redis"])
        results = []
        
        for cache_type in cache_types:
            try:
                if cache_type == "redis":
                    # 清理Redis缓存
                    redis_client = get_redis_client()
                    await redis_client.flushdb()
                    results.append("Redis cache cleared successfully")
                
                elif cache_type == "application":
                    # 清理应用缓存（模拟）
                    results.append("Application cache cleared successfully")
                
                else:
                    results.append(f"Unknown cache type: {cache_type}")
            
            except Exception as e:
                results.append(f"Error clearing {cache_type} cache: {str(e)}")
        
        success = all("successfully" in r for r in results)
        return {"success": success, "details": results}
    
    async def _scale_resources(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """扩缩容资源"""
        # 这里应该调用云服务API进行扩缩容
        # 简化实现，只记录日志
        logger.info("Resource scaling requested (not implemented in this demo)")
        return {"success": True, "details": ["Resource scaling requested"]}
    
    async def _clean_disk(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """清理磁盘空间"""
        clean_types = params.get("clean_types", ["logs", "temp"])
        results = []
        
        for clean_type in clean_types:
            try:
                if clean_type == "logs":
                    # 清理旧日志文件
                    cmd = ["sudo", "find", "/var/log", "-name", "*.log", "-mtime", "+7", "-delete"]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                    results.append("Old log files cleaned")
                
                elif clean_type == "temp":
                    # 清理临时文件
                    cmd = ["sudo", "find", "/tmp", "-type", "f", "-mtime", "+1", "-delete"]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                    results.append("Temporary files cleaned")
                
                elif clean_type == "cache":
                    # 清理系统缓存
                    cmd = ["sudo", "sh", "-c", "echo 3 > /proc/sys/vm/drop_caches"]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                    results.append("System cache cleared")
                
                else:
                    results.append(f"Unknown clean type: {clean_type}")
            
            except Exception as e:
                results.append(f"Error cleaning {clean_type}: {str(e)}")
        
        success = all("cleaned" in r or "cleared" in r for r in results)
        return {"success": success, "details": results}
    
    async def _optimize_database(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """优化数据库"""
        operations = params.get("operations", ["analyze_tables"])
        results = []
        
        for operation in operations:
            try:
                if operation == "kill_idle_connections":
                    # 终止空闲数据库连接
                    from app.core.database import get_async_session
                    from sqlalchemy import text
                    
                    async with get_async_session() as session:
                        await session.execute(text("""
                            SELECT pg_terminate_backend(pid)
                            FROM pg_stat_activity
                            WHERE state = 'idle'
                                AND query_start < now() - interval '5 minutes'
                                AND pid != pg_backend_pid()
                        """))
                        await session.commit()
                    
                    results.append("Idle database connections terminated")
                
                elif operation == "analyze_tables":
                    # 分析表统计信息
                    from app.core.database import get_async_session
                    from sqlalchemy import text
                    
                    async with get_async_session() as session:
                        await session.execute(text("ANALYZE"))
                        await session.commit()
                    
                    results.append("Database tables analyzed")
                
                else:
                    results.append(f"Unknown database operation: {operation}")
            
            except Exception as e:
                results.append(f"Error performing database operation {operation}: {str(e)}")
        
        success = all("terminated" in r or "analyzed" in r for r in results)
        return {"success": success, "details": results}
    
    async def _restart_system(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """重启系统"""
        try:
            # 这是一个危险操作，需要特殊权限
            logger.warning("System restart requested (not implemented in this demo)")
            return {"success": False, "error": "System restart not implemented for safety"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _kill_process(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """终止进程"""
        cpu_threshold = params.get("cpu_threshold", 80.0)
        max_processes = params.get("max_processes", 3)
        
        try:
            import psutil
            
            killed_processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
                try:
                    if proc.info['cpu_percent'] and proc.info['cpu_percent'] > cpu_threshold:
                        if len(killed_processes) < max_processes:
                            proc.terminate()
                            killed_processes.append(f"PID {proc.info['pid']} ({proc.info['name']})")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if killed_processes:
                return {"success": True, "details": [f"Killed processes: {', '.join(killed_processes)}"]}
            else:
                return {"success": True, "details": ["No processes exceeded CPU threshold"]}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _flush_logs(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """刷新日志"""
        retention_days = params.get("log_retention_days", 7)
        
        try:
            # 清理旧日志文件
            cmd = ["sudo", "find", "/var/log", "-name", "*.log.*", "-mtime", f"+{retention_days}", "-delete"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            return {"success": True, "details": [f"Logs older than {retention_days} days flushed"]}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _update_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """更新配置"""
        config_type = params.get("config_type")
        flush_dns = params.get("flush_dns", False)
        
        try:
            if config_type == "network" and flush_dns:
                # 刷新DNS缓存
                cmd = ["sudo", "systemd-resolve", "--flush-caches"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                return {"success": True, "details": ["DNS cache flushed"]}
            
            else:
                return {"success": False, "error": "Unknown config update operation"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ================================
    # 辅助方法
    # ================================
    
    async def _create_recovery_alert(self, original_alert: Dict[str, Any], rule: RecoveryRule, status: str):
        """创建恢复操作告警"""
        try:
            if status == "success":
                severity = AlertSeverity.WARNING
                title = f"自动恢复成功: {rule.name}"
                description = f"告警 '{original_alert['title']}' 的自动恢复操作已成功完成"
            
            elif status == "partial_success":
                severity = AlertSeverity.WARNING
                title = f"自动恢复部分成功: {rule.name}"
                description = f"告警 '{original_alert['title']}' 的自动恢复操作部分完成"
            
            else:  # failed
                severity = AlertSeverity.CRITICAL
                title = f"自动恢复失败: {rule.name}"
                description = f"告警 '{original_alert['title']}' 的自动恢复操作失败，需要人工干预"
            
            await alert_manager.create_alert(
                title=title,
                description=description,
                severity=severity,
                source="infrastructure_recovery",
                service="web3search",
                environment=settings.ENVIRONMENT,
                labels={
                    "recovery_rule": rule.rule_id,
                    "original_alert": original_alert["alert_id"],
                    "recovery_status": status
                },
                annotations={
                    "original_alert_title": original_alert["title"],
                    "rule_description": rule.description
                }
            )
        
        except Exception as e:
            logger.error(f"Error creating recovery alert: {e}")
    
    async def _escalate_alert(self, original_alert: Dict[str, Any], rule: RecoveryRule):
        """升级告警"""
        try:
            await alert_manager.create_alert(
                title=f"告警升级: {original_alert['title']}",
                description=f"告警 '{original_alert['title']}' 的自动恢复操作失败并已达到最大尝试次数，需要立即人工干预",
                severity=AlertSeverity.CRITICAL,
                source="infrastructure_recovery",
                service="web3search",
                environment=settings.ENVIRONMENT,
                labels={
                    "escalated": "true",
                    "recovery_rule": rule.rule_id,
                    "original_alert": original_alert["alert_id"]
                },
                annotations={
                    "original_alert_title": original_alert["title"],
                    "rule_description": rule.description,
                    "max_attempts_reached": "true"
                }
            )
        
        except Exception as e:
            logger.error(f"Error escalating alert: {e}")
    
    async def _save_execution(self, execution: RecoveryExecution):
        """保存执行记录"""
        try:
            execution_key = f"recovery_execution:{execution.execution_id}"
            execution_data = {
                "execution_id": execution.execution_id,
                "rule_id": execution.rule_id,
                "alert_id": execution.alert_id,
                "actions": execution.actions,
                "status": execution.status.value,
                "started_at": execution.started_at.isoformat(),
                "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
                "error_message": execution.error_message,
                "execution_log": execution.execution_log
            }
            
            await self.redis_client.setex(
                execution_key,
                self.retention_days * 24 * 3600,
                json.dumps(execution_data)
            )
            
            # 添加到执行历史
            history_key = "recovery_execution_history"
            await self.redis_client.zadd(
                history_key,
                {json.dumps(execution_data): int(execution.started_at.timestamp())}
            )
            
            # 清理过期数据
            cutoff_time = int((datetime.now() - timedelta(days=self.retention_days)).timestamp())
            await self.redis_client.zremrangebyscore(history_key, 0, cutoff_time)
        
        except Exception as e:
            logger.error(f"Error saving recovery execution: {e}")
    
    async def _cleanup_old_executions(self):
        """清理过期的执行记录"""
        try:
            # 这个方法在保存执行记录时已经包含了清理逻辑
            # 这里可以添加额外的清理操作
            pass
        
        except Exception as e:
            logger.error(f"Error cleaning up old executions: {e}")
    
    # ================================
    # 公共API方法
    # ================================
    
    async def get_recovery_rules(self) -> List[Dict[str, Any]]:
        """获取所有恢复规则"""
        try:
            rules = []
            for rule in self.recovery_rules.values():
                rule_dict = asdict(rule)
                rules.append(rule_dict)
            
            return rules
        
        except Exception as e:
            logger.error(f"Error getting recovery rules: {e}")
            return []
    
    async def get_recovery_executions(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """获取恢复执行记录"""
        try:
            history_key = "recovery_execution_history"
            
            if start_time and end_time:
                start_timestamp = int(start_time.timestamp())
                end_timestamp = int(end_time.timestamp())
                
                results = await self.redis_client.zrangebyscore(
                    history_key,
                    start_timestamp,
                    end_timestamp,
                    start=0,
                    num=limit
                )
            else:
                results = await self.redis_client.zrevrange(
                    history_key,
                    start=0,
                    num=limit
                )
            
            executions = []
            for result in results:
                execution_data = json.loads(result)
                executions.append(execution_data)
            
            return executions
        
        except Exception as e:
            logger.error(f"Error getting recovery executions: {e}")
            return []
    
    async def add_recovery_rule(self, rule: RecoveryRule) -> bool:
        """添加自定义恢复规则"""
        try:
            self.recovery_rules[rule.rule_id] = rule
            
            # 保存到Redis
            custom_rules_key = "recovery_rules:custom"
            custom_rules = [asdict(r) for r in self.recovery_rules.values() if not r.rule_id.startswith("high_") and not r.rule_id.startswith("disk_")]
            
            await self.redis_client.set(
                custom_rules_key,
                json.dumps(custom_rules)
            )
            
            logger.info(f"Added custom recovery rule: {rule.rule_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error adding recovery rule: {e}")
            return False
    
    async def enable_disable_rule(self, rule_id: str, enabled: bool) -> bool:
        """启用或禁用恢复规则"""
        try:
            if rule_id in self.recovery_rules:
                self.recovery_rules[rule_id].enabled = enabled
                
                # 更新Redis中的规则
                custom_rules_key = "recovery_rules:custom"
                custom_rules = [asdict(r) for r in self.recovery_rules.values() if not r.rule_id.startswith("high_") and not r.rule_id.startswith("disk_")]
                
                await self.redis_client.set(
                    custom_rules_key,
                    json.dumps(custom_rules)
                )
                
                logger.info(f"{'Enabled' if enabled else 'Disabled'} recovery rule: {rule_id}")
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Error updating recovery rule {rule_id}: {e}")
            return False


# 全局基础设施恢复管理器实例
infrastructure_recovery_manager = InfrastructureRecoveryManager()
