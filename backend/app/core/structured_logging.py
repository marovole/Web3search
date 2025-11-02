"""
结构化日志配置和索引策略系统
提供统一的日志格式、索引策略和配置管理
"""
import logging
import json
import asyncio
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import yaml
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import structlog
from pythonjsonlogger import jsonlogger

from app.core.log_aggregation import (
    LogEntry, LogLevel, LogSource, 
    log_aggregator, log_index_manager
)
from app.core.config import settings
from app.core.redis_client import get_redis_client


class LogFormat(Enum):
    """日志格式"""
    JSON = "json"
    STRUCTURED = "structured"
    PLAIN = "plain"


class IndexStrategy(Enum):
    """索引策略"""
    TIME_BASED = "time_based"          # 基于时间
    LEVEL_BASED = "level_based"        # 基于级别
    SOURCE_BASED = "source_based"      # 基于来源
    SERVICE_BASED = "service_based"    # 基于服务
    HYBRID = "hybrid"                  # 混合策略


@dataclass
class LogConfig:
    """日志配置"""
    service_name: str
    environment: str
    log_level: LogLevel
    log_format: LogFormat
    enable_console: bool = True
    enable_file: bool = True
    enable_loki: bool = True
    file_path: str = "logs/app.log"
    max_file_size_mb: int = 100
    backup_count: int = 5
    rotation: str = "daily"  # daily, weekly, size
    compression: bool = True
    index_strategy: IndexStrategy = IndexStrategy.TIME_BASED
    retention_days: int = 30
    sensitive_fields: List[str] = None
    
    def __post_init__(self):
        if self.sensitive_fields is None:
            self.sensitive_fields = ["password", "token", "api_key", "secret"]


@dataclass
class IndexRule:
    """索引规则"""
    rule_id: str
    name: str
    strategy: IndexStrategy
    pattern: str
    priority: int
    ttl_days: int
    shard_count: int = 1
    replica_count: int = 1
    enabled: bool = True


class StructuredLogger:
    """
    结构化日志器
    提供统一的日志记录接口
    """
    
    def __init__(self, config: LogConfig):
        self.config = config
        self.logger = None
        self._setup_logger()
    
    def _setup_logger(self):
        """设置日志器"""
        # 创建logger
        self.logger = logging.getLogger(self.config.service_name)
        self.logger.setLevel(getattr(logging, self.config.log_level.value.upper()))
        
        # 清除现有处理器
        self.logger.handlers.clear()
        
        # 设置格式化器
        formatter = self._create_formatter()
        
        # 控制台处理器
        if self.config.enable_console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # 文件处理器
        if self.config.enable_file:
            file_handler = self._create_file_handler()
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        
        # Loki处理器（自定义）
        if self.config.enable_loki:
            loki_handler = LokiHandler(self.config)
            self.logger.addHandler(loki_handler)
    
    def _create_formatter(self) -> logging.Formatter:
        """创建格式化器"""
        if self.config.log_format == LogFormat.JSON:
            return jsonlogger.JsonFormatter(
                '%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(lineno)d'
            )
        elif self.config.log_format == LogFormat.STRUCTURED:
            return structlog.stdlib.ProcessorFormatter(
                processor=structlog.dev.ConsoleRenderer(colors=False),
            )
        else:
            return logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
    
    def _create_file_handler(self) -> logging.Handler:
        """创建文件处理器"""
        # 确保日志目录存在
        log_dir = Path(self.config.file_path).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        if self.config.rotation == "size":
            handler = RotatingFileHandler(
                self.config.file_path,
                maxBytes=self.config.max_file_size_mb * 1024 * 1024,
                backupCount=self.config.backup_count
            )
        else:  # time-based rotation
            when = "midnight" if self.config.rotation == "daily" else "W0"
            handler = TimedRotatingFileHandler(
                self.config.file_path,
                when=when,
                backupCount=self.config.backup_count
            )
        
        return handler
    
    def log(
        self, 
        level: LogLevel, 
        message: str, 
        source: LogSource = LogSource.APPLICATION,
        **kwargs
    ):
        """
        记录日志
        
        Args:
            level: 日志级别
            message: 日志消息
            source: 日志来源
            **kwargs: 额外的日志字段
        """
        # 过滤敏感字段
        filtered_kwargs = self._filter_sensitive_data(kwargs)
        
        # 创建日志条目
        log_entry = LogEntry(
            timestamp=datetime.now(),
            level=level,
            message=message,
            source=source,
            service=self.config.service_name,
            environment=self.config.environment,
            **filtered_kwargs
        )
        
        # 记录到标准日志
        log_level = getattr(logging, level.value.upper())
        self.logger.log(log_level, message, extra={"log_entry": log_entry})
        
        # 发送到Loki（异步）
        if self.config.enable_loki:
            asyncio.create_task(log_aggregator.add_log(log_entry))
    
    def debug(self, message: str, **kwargs):
        """记录调试日志"""
        self.log(LogLevel.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """记录信息日志"""
        self.log(LogLevel.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """记录警告日志"""
        self.log(LogLevel.WARN, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """记录错误日志"""
        self.log(LogLevel.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """记录严重错误日志"""
        self.log(LogLevel.FATAL, message, **kwargs)
    
    def _filter_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """过滤敏感数据"""
        filtered = {}
        
        for key, value in data.items():
            # 检查是否为敏感字段
            if any(sensitive in key.lower() for sensitive in self.config.sensitive_fields):
                filtered[key] = "***REDACTED***"
            else:
                # 递归过滤嵌套字典
                if isinstance(value, dict):
                    filtered[key] = self._filter_sensitive_data(value)
                else:
                    filtered[key] = value
        
        return filtered


class LokiHandler(logging.Handler):
    """
    Loki日志处理器
    将日志发送到Loki
    """
    
    def __init__(self, config: LogConfig):
        super().__init__()
        self.config = config
    
    def emit(self, record):
        """发送日志记录"""
        try:
            # 从记录中获取LogEntry
            log_entry = getattr(record, "log_entry", None)
            
            if log_entry:
                # 异步发送到Loki
                asyncio.create_task(log_aggregator.add_log(log_entry))
            
        except Exception as e:
            logging.error(f"Error in LokiHandler: {e}")


class IndexStrategyManager:
    """
    索引策略管理器
    负责日志索引策略的配置和管理
    """
    
    def __init__(self):
        self.redis_client = None
        self.index_rules: Dict[str, IndexRule] = {}
        
    async def initialize(self):
        """初始化索引策略管理器"""
        self.redis_client = get_redis_client()
        await self._load_default_rules()
    
    async def add_index_rule(self, rule: IndexRule) -> bool:
        """
        添加索引规则
        
        Args:
            rule: 索引规则
        """
        try:
            # 存储到Redis
            rule_key = f"index_rule:{rule.rule_id}"
            rule_data = asdict(rule)
            rule_data["strategy"] = rule.strategy.value
            
            await self.redis_client.hset(rule_key, mapping={
                "rule_id": rule.rule_id,
                "name": rule.name,
                "strategy": rule.strategy.value,
                "pattern": rule.pattern,
                "priority": str(rule.priority),
                "ttl_days": str(rule.ttl_days),
                "shard_count": str(rule.shard_count),
                "replica_count": str(rule.replica_count),
                "enabled": str(rule.enabled),
                "created_at": datetime.now().isoformat()
            })
            
            self.index_rules[rule.rule_id] = rule
            logger.info(f"Added index rule: {rule.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding index rule {rule.rule_id}: {e}")
            return False
    
    async def get_index_rules(self, enabled_only: bool = True) -> List[IndexRule]:
        """
        获取索引规则
        
        Args:
            enabled_only: 是否只返回启用的规则
        """
        try:
            rules = []
            
            async for key in self.redis_client.scan_iter(match="index_rule:*"):
                rule_data = await self.redis_client.hgetall(key)
                
                if rule_data:
                    enabled = rule_data.get("enabled", b"true").decode() == "true"
                    
                    if not enabled_only or enabled:
                        rule = IndexRule(
                            rule_id=rule_data.get("rule_id").decode(),
                            name=rule_data.get("name").decode(),
                            strategy=IndexStrategy(rule_data.get("strategy").decode()),
                            pattern=rule_data.get("pattern").decode(),
                            priority=int(rule_data.get("priority").decode()),
                            ttl_days=int(rule_data.get("ttl_days").decode()),
                            shard_count=int(rule_data.get("shard_count").decode()),
                            replica_count=int(rule_data.get("replica_count").decode()),
                            enabled=enabled
                        )
                        rules.append(rule)
            
            # 按优先级排序
            rules.sort(key=lambda x: x.priority)
            return rules
            
        except Exception as e:
            logger.error(f"Error getting index rules: {e}")
            return []
    
    async def apply_index_strategy(self, log_entry: LogEntry) -> str:
        """
        应用索引策略
        
        Args:
            log_entry: 日志条目
            
        Returns:
            索引名称
        """
        try:
            # 获取适用的索引规则
            applicable_rules = []
            
            for rule in self.index_rules.values():
                if rule.enabled and self._matches_rule(log_entry, rule):
                    applicable_rules.append(rule)
            
            # 选择优先级最高的规则
            if applicable_rules:
                rule = max(applicable_rules, key=lambda x: x.priority)
                return self._generate_index_name(log_entry, rule)
            
            # 默认索引策略
            return self._generate_default_index(log_entry)
            
        except Exception as e:
            logger.error(f"Error applying index strategy: {e}")
            return self._generate_default_index(log_entry)
    
    def _matches_rule(self, log_entry: LogEntry, rule: IndexRule) -> bool:
        """检查日志条目是否匹配规则"""
        try:
            # 简单的模式匹配（可以扩展为更复杂的逻辑）
            if rule.strategy == IndexStrategy.LEVEL_BASED:
                return log_entry.level.value in rule.pattern
            elif rule.strategy == IndexStrategy.SOURCE_BASED:
                return log_entry.source.value in rule.pattern
            elif rule.strategy == IndexStrategy.SERVICE_BASED:
                return log_entry.service in rule.pattern
            elif rule.strategy == IndexStrategy.TIME_BASED:
                # 基于时间的模式匹配
                return True  # 时间策略总是匹配
            else:
                return True
                
        except Exception as e:
            logger.error(f"Error matching rule: {e}")
            return False
    
    def _generate_index_name(self, log_entry: LogEntry, rule: IndexRule) -> str:
        """生成索引名称"""
        if rule.strategy == IndexStrategy.TIME_BASED:
            # 基于时间的索引名称
            if rule.pattern == "daily":
                return f"logs-{log_entry.service}-{log_entry.timestamp.strftime('%Y.%m.%d')}"
            elif rule.pattern == "weekly":
                week_start = log_entry.timestamp - timedelta(days=log_entry.timestamp.weekday())
                return f"logs-{log_entry.service}-{week_start.strftime('%Y.%W')}"
            elif rule.pattern == "monthly":
                return f"logs-{log_entry.service}-{log_entry.timestamp.strftime('%Y.%m')}"
        
        elif rule.strategy == IndexStrategy.LEVEL_BASED:
            return f"logs-{log_entry.service}-{log_entry.level.value}"
        
        elif rule.strategy == IndexStrategy.SOURCE_BASED:
            return f"logs-{log_entry.service}-{log_entry.source.value}"
        
        else:
            return f"logs-{log_entry.service}-default"
    
    def _generate_default_index(self, log_entry: LogEntry) -> str:
        """生成默认索引名称"""
        return f"logs-{log_entry.service}-{log_entry.timestamp.strftime('%Y.%m.%d')}"
    
    async def _load_default_rules(self):
        """加载默认索引规则"""
        default_rules = [
            IndexRule(
                rule_id="daily_time_based",
                name="Daily Time Based Index",
                strategy=IndexStrategy.TIME_BASED,
                pattern="daily",
                priority=1,
                ttl_days=30
            ),
            IndexRule(
                rule_id="error_level_based",
                name="Error Level Based Index",
                strategy=IndexStrategy.LEVEL_BASED,
                pattern="error,fatal",
                priority=10,
                ttl_days=90
            ),
            IndexRule(
                rule_id="security_source_based",
                name="Security Source Based Index",
                strategy=IndexStrategy.SOURCE_BASED,
                pattern="security",
                priority=20,
                ttl_days=365
            )
        ]
        
        for rule in default_rules:
            await self.add_index_rule(rule)


class LogConfigManager:
    """
    日志配置管理器
    负责日志配置的加载、保存和管理
    """
    
    def __init__(self):
        self.configs: Dict[str, LogConfig] = {}
        self.config_file = "logging_config.yaml"
        
    async def load_configs(self) -> bool:
        """加载日志配置"""
        try:
            config_path = Path(self.config_file)
            
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
                
                for service_name, service_config in config_data.get("services", {}).items():
                    config = LogConfig(
                        service_name=service_name,
                        environment=service_config.get("environment", "development"),
                        log_level=LogLevel(service_config.get("log_level", "info")),
                        log_format=LogFormat(service_config.get("log_format", "json")),
                        enable_console=service_config.get("enable_console", True),
                        enable_file=service_config.get("enable_file", True),
                        enable_loki=service_config.get("enable_loki", True),
                        file_path=service_config.get("file_path", f"logs/{service_name}.log"),
                        max_file_size_mb=service_config.get("max_file_size_mb", 100),
                        backup_count=service_config.get("backup_count", 5),
                        rotation=service_config.get("rotation", "daily"),
                        compression=service_config.get("compression", True),
                        index_strategy=IndexStrategy(service_config.get("index_strategy", "time_based")),
                        retention_days=service_config.get("retention_days", 30),
                        sensitive_fields=service_config.get("sensitive_fields", [])
                    )
                    
                    self.configs[service_name] = config
                
                logger.info(f"Loaded {len(self.configs)} log configurations")
                return True
            else:
                # 创建默认配置
                await self._create_default_config()
                return True
                
        except Exception as e:
            logger.error(f"Error loading log configurations: {e}")
            return False
    
    async def save_configs(self) -> bool:
        """保存日志配置"""
        try:
            config_data = {
                "services": {}
            }
            
            for service_name, config in self.configs.items():
                config_data["services"][service_name] = {
                    "environment": config.environment,
                    "log_level": config.log_level.value,
                    "log_format": config.log_format.value,
                    "enable_console": config.enable_console,
                    "enable_file": config.enable_file,
                    "enable_loki": config.enable_loki,
                    "file_path": config.file_path,
                    "max_file_size_mb": config.max_file_size_mb,
                    "backup_count": config.backup_count,
                    "rotation": config.rotation,
                    "compression": config.compression,
                    "index_strategy": config.index_strategy.value,
                    "retention_days": config.retention_days,
                    "sensitive_fields": config.sensitive_fields
                }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
            
            logger.info(f"Saved {len(self.configs)} log configurations")
            return True
            
        except Exception as e:
            logger.error(f"Error saving log configurations: {e}")
            return False
    
    def get_config(self, service_name: str) -> Optional[LogConfig]:
        """获取服务配置"""
        return self.configs.get(service_name)
    
    async def add_config(self, config: LogConfig) -> bool:
        """添加日志配置"""
        try:
            self.configs[config.service_name] = config
            await self.save_configs()
            logger.info(f"Added log configuration for service: {config.service_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding log configuration: {e}")
            return False
    
    async def _create_default_config(self):
        """创建默认配置"""
        default_config = LogConfig(
            service_name="web3search",
            environment=settings.ENVIRONMENT,
            log_level=LogLevel.INFO,
            log_format=LogFormat.JSON,
            enable_console=True,
            enable_file=True,
            enable_loki=True,
            file_path="logs/web3search.log",
            max_file_size_mb=100,
            backup_count=5,
            rotation="daily",
            compression=True,
            index_strategy=IndexStrategy.TIME_BASED,
            retention_days=30,
            sensitive_fields=["password", "token", "api_key", "secret"]
        )
        
        await self.add_config(default_config)


class StructuredLogManager:
    """
    结构化日志管理器
    统一管理结构化日志系统
    """
    
    def __init__(self):
        self.config_manager = LogConfigManager()
        self.index_strategy_manager = IndexStrategyManager()
        self.loggers: Dict[str, StructuredLogger] = {}
        self.running = False
        
    async def initialize(self):
        """初始化结构化日志系统"""
        if self.running:
            return
        
        # 加载配置
        await self.config_manager.load_configs()
        await self.index_strategy_manager.initialize()
        
        # 为每个服务创建日志器
        for service_name, config in self.config_manager.configs.items():
            self.loggers[service_name] = StructuredLogger(config)
        
        self.running = True
        logger.info("Structured log system initialized")
    
    async def shutdown(self):
        """关闭结构化日志系统"""
        self.running = False
        logger.info("Structured log system shutdown")
    
    def get_logger(self, service_name: str) -> Optional[StructuredLogger]:
        """获取结构化日志器"""
        return self.loggers.get(service_name)
    
    async def update_config(self, service_name: str, config: LogConfig) -> bool:
        """更新服务配置"""
        try:
            # 保存配置
            await self.config_manager.add_config(config)
            
            # 重新创建日志器
            self.loggers[service_name] = StructuredLogger(config)
            
            logger.info(f"Updated log configuration for service: {service_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating log configuration: {e}")
            return False
    
    async def get_log_statistics(self) -> Dict[str, Any]:
        """获取日志统计信息"""
        try:
            stats = {
                "total_services": len(self.loggers),
                "active_loggers": len([logger for logger in self.loggers.values() if logger.logger.handlers]),
                "index_rules": len(await self.index_strategy_manager.get_index_rules()),
                "configurations": len(self.config_manager.configs)
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting log statistics: {e}")
            return {}


# 全局结构化日志管理器实例
structured_log_manager = StructuredLogManager()

# 获取默认日志器的便捷函数
def get_logger(service_name: str = "web3search") -> Optional[StructuredLogger]:
    """获取结构化日志器"""
    return structured_log_manager.get_logger(service_name)
