"""
告警规则和升级策略系统
提供灵活的告警规则配置、评估和升级策略管理
"""
import asyncio
import json
import logging
import re
from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from abc import ABC, abstractmethod
import statistics
import math

from app.core.alerting_system import (
    Alert, AlertSeverity, AlertStatus,
    alert_manager, NotificationRule
)
from app.core.config import settings
from app.core.redis_client import get_redis_client

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """指标类型"""
    COUNTER = "counter"           # 计数器
    GAUGE = "gauge"              # 仪表盘
    HISTOGRAM = "histogram"      # 直方图
    RATE = "rate"                # 速率
    PERCENTILE = "percentile"    # 百分位数


class ComparisonOperator(Enum):
    """比较操作符"""
    EQUAL = "eq"                 # 等于
    NOT_EQUAL = "ne"             # 不等于
    GREATER_THAN = "gt"          # 大于
    GREATER_EQUAL = "ge"         # 大于等于
    LESS_THAN = "lt"             # 小于
    LESS_EQUAL = "le"            # 小于等于
    CONTAINS = "contains"        # 包含
    NOT_CONTAINS = "not_contains" # 不包含
    REGEX_MATCH = "regex"        # 正则匹配


class AggregationType(Enum):
    """聚合类型"""
    AVG = "avg"                  # 平均值
    SUM = "sum"                  # 求和
    MIN = "min"                  # 最小值
    MAX = "max"                  # 最大值
    COUNT = "count"              # 计数
    RATE = "rate"                # 速率
    INCREASE = "increase"        # 增量
    P50 = "p50"                  # 50百分位
    P90 = "p90"                  # 90百分位
    P95 = "p95"                  # 95百分位
    P99 = "p99"                  # 99百分位


class EvaluationInterval(Enum):
    """评估间隔"""
    MINUTE_1 = "1m"              # 1分钟
    MINUTE_5 = "5m"              # 5分钟
    MINUTE_15 = "15m"            # 15分钟
    HOUR_1 = "1h"                # 1小时
    HOUR_6 = "6h"                # 6小时
    HOUR_12 = "12h"              # 12小时
    DAY_1 = "1d"                 # 1天


@dataclass
class AlertRule:
    """告警规则"""
    rule_id: str
    name: str
    description: str
    enabled: bool = True
    severity: AlertSeverity = AlertSeverity.WARNING
    metric_name: str = ""
    metric_type: MetricType = MetricType.GAUGE
    query: str = ""               # 查询表达式（如PromQL）
    evaluation_interval: EvaluationInterval = EvaluationInterval.MINUTE_5
    for_duration: timedelta = timedelta(minutes=0)  # 持续时间
    operator: ComparisonOperator = ComparisonOperator.GREATER_THAN
    threshold: float = 0.0
    aggregation: AggregationType = AggregationType.AVG
    labels: Dict[str, str] = None
    annotations: Dict[str, str] = None
    source_filter: List[str] = None
    service_filter: List[str] = None
    environment_filter: List[str] = None
    notification_rules: List[str] = None  # 通知规则ID列表
    escalation_enabled: bool = True
    escalation_delay: timedelta = timedelta(minutes=30)
    max_evaluations: int = 1000  # 最大评估次数
    cooldown_period: timedelta = timedelta(minutes=15)
    
    def __post_init__(self):
        if self.labels is None:
            self.labels = {}
        if self.annotations is None:
            self.annotations = {}
        if self.source_filter is None:
            self.source_filter = []
        if self.service_filter is None:
            self.service_filter = []
        if self.environment_filter is None:
            self.environment_filter = []
        if self.notification_rules is None:
            self.notification_rules = []


@dataclass
class EvaluationResult:
    """评估结果"""
    rule_id: str
    timestamp: datetime
    triggered: bool
    current_value: float
    threshold_value: float
    evaluation_time_ms: float
    message: str = ""
    labels: Dict[str, str] = None
    
    def __post_init__(self):
        if self.labels is None:
            self.labels = {}


@dataclass
class EscalationPolicy:
    """升级策略"""
    policy_id: str
    name: str
    description: str
    enabled: bool = True
    severity_levels: List[AlertSeverity] = None
    escalation_steps: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.severity_levels is None:
            self.severity_levels = []
        if self.escalation_steps is None:
            self.escalation_steps = []


class MetricEvaluator(ABC):
    """指标评估器抽象基类"""
    
    @abstractmethod
    async def evaluate_metric(self, rule: AlertRule) -> EvaluationResult:
        """评估指标"""
        pass


class PrometheusEvaluator(MetricEvaluator):
    """Prometheus指标评估器"""
    
    def __init__(self, prometheus_url: str):
        self.prometheus_url = prometheus_url
        self.session = None
    
    async def __aenter__(self):
        import aiohttp
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def evaluate_metric(self, rule: AlertRule) -> EvaluationResult:
        """评估Prometheus指标"""
        try:
            start_time = datetime.now()
            
            # 构建查询
            query = self._build_query(rule)
            
            # 执行查询
            url = f"{self.prometheus_url}/api/v1/query"
            params = {
                "query": query,
                "time": datetime.now().timestamp()
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # 解析结果
                    result = self._parse_prometheus_response(data, rule)
                    
                    evaluation_time = (datetime.now() - start_time).total_seconds() * 1000
                    result.evaluation_time_ms = evaluation_time
                    
                    return result
                else:
                    error_text = await response.text()
                    raise Exception(f"Prometheus query failed: {response.status} - {error_text}")
        
        except Exception as e:
            logger.error(f"Error evaluating Prometheus metric: {e}")
            return EvaluationResult(
                rule_id=rule.rule_id,
                timestamp=datetime.now(),
                triggered=False,
                current_value=0.0,
                threshold_value=rule.threshold,
                evaluation_time_ms=0.0,
                message=f"Evaluation error: {str(e)}"
            )
    
    def _build_query(self, rule: AlertRule) -> str:
        """构建Prometheus查询"""
        if rule.query:
            return rule.query
        
        # 基础查询构建
        query = rule.metric_name
        
        # 添加标签过滤
        label_filters = []
        
        if rule.service_filter:
            service_filter = "|".join(rule.service_filter)
            label_filters.append(f'service=~"{service_filter}"')
        
        if rule.source_filter:
            source_filter = "|".join(rule.source_filter)
            label_filters.append(f'source=~"{source_filter}"')
        
        if rule.environment_filter:
            env_filter = "|".join(rule.environment_filter)
            label_filters.append(f'environment=~"{env_filter}"')
        
        if label_filters:
            query += "{" + ",".join(label_filters) + "}"
        
        # 添加聚合函数
        if rule.aggregation != AggregationType.AVG:
            aggregation_map = {
                AggregationType.SUM: "sum",
                AggregationType.MIN: "min",
                AggregationType.MAX: "max",
                AggregationType.COUNT: "count",
                AggregationType.RATE: "rate",
                AggregationType.INCREASE: "increase",
                AggregationType.P50: "quantile",
                AggregationType.P90: "quantile",
                AggregationType.P95: "quantile",
                AggregationType.P99: "quantile"
            }
            
            agg_func = aggregation_map.get(rule.aggregation, "avg")
            
            if rule.aggregation in [AggregationType.P50, AggregationType.P90, AggregationType.P95, AggregationType.P99]:
                quantile_value = {
                    AggregationType.P50: 0.5,
                    AggregationType.P90: 0.9,
                    AggregationType.P95: 0.95,
                    AggregationType.P99: 0.99
                }[rule.aggregation]
                query = f'{agg_func}({quantile_value}, {query})'
            else:
                query = f'{agg_func}({query})'
        
        # 添加时间范围
        if rule.evaluation_interval != EvaluationInterval.MINUTE_1:
            duration_map = {
                EvaluationInterval.MINUTE_5: "5m",
                EvaluationInterval.MINUTE_15: "15m",
                EvaluationInterval.HOUR_1: "1h",
                EvaluationInterval.HOUR_6: "6h",
                EvaluationInterval.HOUR_12: "12h",
                EvaluationInterval.DAY_1: "1d"
            }
            duration = duration_map.get(rule.evaluation_interval, "5m")
            
            if rule.aggregation in [AggregationType.RATE]:
                query = f'{query}[{duration}]'
            elif rule.aggregation == AggregationType.INCREASE:
                query = f'increase({query}[{duration}])'
        
        return query
    
    def _parse_prometheus_response(self, data: Dict[str, Any], rule: AlertRule) -> EvaluationResult:
        """解析Prometheus响应"""
        try:
            result_data = data.get("data", {})
            result_type = result_data.get("resultType", "vector")
            results = result_data.get("result", [])
            
            if not results:
                return EvaluationResult(
                    rule_id=rule.rule_id,
                    timestamp=datetime.now(),
                    triggered=False,
                    current_value=0.0,
                    threshold_value=rule.threshold,
                    evaluation_time_ms=0.0,
                    message="No data returned"
                )
            
            # 获取第一个结果
            first_result = results[0]
            value = first_result.get("value", [])
            
            if len(value) >= 2:
                current_value = float(value[1])
            else:
                current_value = 0.0
            
            # 评估阈值
            triggered = self._evaluate_threshold(current_value, rule.operator, rule.threshold)
            
            # 构建标签
            labels = first_result.get("metric", {})
            
            return EvaluationResult(
                rule_id=rule.rule_id,
                timestamp=datetime.now(),
                triggered=triggered,
                current_value=current_value,
                threshold_value=rule.threshold,
                evaluation_time_ms=0.0,
                message=f"Value: {current_value}, Threshold: {rule.threshold}",
                labels=labels
            )
            
        except Exception as e:
            logger.error(f"Error parsing Prometheus response: {e}")
            return EvaluationResult(
                rule_id=rule.rule_id,
                timestamp=datetime.now(),
                triggered=False,
                current_value=0.0,
                threshold_value=rule.threshold,
                evaluation_time_ms=0.0,
                message=f"Parse error: {str(e)}"
            )
    
    def _evaluate_threshold(self, value: float, operator: ComparisonOperator, threshold: float) -> bool:
        """评估阈值"""
        if operator == ComparisonOperator.EQUAL:
            return value == threshold
        elif operator == ComparisonOperator.NOT_EQUAL:
            return value != threshold
        elif operator == ComparisonOperator.GREATER_THAN:
            return value > threshold
        elif operator == ComparisonOperator.GREATER_EQUAL:
            return value >= threshold
        elif operator == ComparisonOperator.LESS_THAN:
            return value < threshold
        elif operator == ComparisonOperator.LESS_EQUAL:
            return value <= threshold
        else:
            return False


class CustomEvaluator(MetricEvaluator):
    """自定义指标评估器"""
    
    def __init__(self):
        self.custom_functions: Dict[str, Callable] = {}
        self._register_default_functions()
    
    def register_function(self, name: str, func: Callable):
        """注册自定义评估函数"""
        self.custom_functions[name] = func
    
    async def evaluate_metric(self, rule: AlertRule) -> EvaluationResult:
        """评估自定义指标"""
        try:
            start_time = datetime.now()
            
            # 查找自定义函数
            func = self.custom_functions.get(rule.metric_name)
            if not func:
                raise Exception(f"No custom function found for metric: {rule.metric_name}")
            
            # 执行自定义函数
            if asyncio.iscoroutinefunction(func):
                result_value = await func(rule)
            else:
                result_value = func(rule)
            
            evaluation_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # 评估阈值
            triggered = self._evaluate_threshold(result_value, rule.operator, rule.threshold)
            
            return EvaluationResult(
                rule_id=rule.rule_id,
                timestamp=datetime.now(),
                triggered=triggered,
                current_value=result_value,
                threshold_value=rule.threshold,
                evaluation_time_ms=evaluation_time,
                message=f"Custom evaluation result: {result_value}"
            )
            
        except Exception as e:
            logger.error(f"Error evaluating custom metric: {e}")
            return EvaluationResult(
                rule_id=rule.rule_id,
                timestamp=datetime.now(),
                triggered=False,
                current_value=0.0,
                threshold_value=rule.threshold,
                evaluation_time_ms=0.0,
                message=f"Custom evaluation error: {str(e)}"
            )
    
    def _evaluate_threshold(self, value: float, operator: ComparisonOperator, threshold: float) -> bool:
        """评估阈值"""
        if operator == ComparisonOperator.EQUAL:
            return value == threshold
        elif operator == ComparisonOperator.NOT_EQUAL:
            return value != threshold
        elif operator == ComparisonOperator.GREATER_THAN:
            return value > threshold
        elif operator == ComparisonOperator.GREATER_EQUAL:
            return value >= threshold
        elif operator == ComparisonOperator.LESS_THAN:
            return value < threshold
        elif operator == ComparisonOperator.LESS_EQUAL:
            return value <= threshold
        else:
            return False
    
    def _register_default_functions(self):
        """注册默认自定义函数"""
        
        async def error_rate_function(rule: AlertRule) -> float:
            """错误率评估函数"""
            try:
                # 从日志系统获取错误率
                from app.core.log_aggregation import log_aggregator, LogQuery, LogLevel
                
                # 查询最近5分钟的日志
                end_time = datetime.now()
                start_time = end_time - timedelta(minutes=5)
                
                error_query = LogQuery(
                    query="",
                    start_time=start_time,
                    end_time=end_time,
                    level=LogLevel.ERROR,
                    limit=1000
                )
                
                error_results = await log_aggregator.query_logs(error_query)
                
                # 查询总日志数
                total_query = LogQuery(
                    query="",
                    start_time=start_time,
                    end_time=end_time,
                    limit=1000
                )
                
                total_results = await log_aggregator.query_logs(total_query)
                
                if total_results.total_count > 0:
                    error_rate = (error_results.total_count / total_results.total_count) * 100
                else:
                    error_rate = 0.0
                
                return error_rate
                
            except Exception as e:
                logger.error(f"Error calculating error rate: {e}")
                return 0.0
        
        async def response_time_function(rule: AlertRule) -> float:
            """响应时间评估函数"""
            try:
                # 从监控系统获取平均响应时间
                # 这里返回模拟数据
                import random
                return random.uniform(100, 500)  # 毫秒
                
            except Exception as e:
                logger.error(f"Error calculating response time: {e}")
                return 0.0
        
        async def memory_usage_function(rule: AlertRule) -> float:
            """内存使用率评估函数"""
            try:
                import psutil
                memory = psutil.virtual_memory()
                return memory.percent
                
            except Exception as e:
                logger.error(f"Error calculating memory usage: {e}")
                return 0.0
        
        # 注册自定义函数
        self.register_function("error_rate", error_rate_function)
        self.register_function("response_time", response_time_function)
        self.register_function("memory_usage", memory_usage_function)


class AlertRuleEngine:
    """
    告警规则引擎
    负责规则的执行、评估和管理
    """
    
    def __init__(self):
        self.redis_client = None
        self.rules: Dict[str, AlertRule] = {}
        self.evaluators: Dict[str, MetricEvaluator] = {}
        self.running = False
        self.evaluation_tasks: Dict[str, asyncio.Task] = {}
        
    async def initialize(self):
        """初始化规则引擎"""
        if self.running:
            return
        
        self.redis_client = get_redis_client()
        
        # 初始化评估器
        await self._initialize_evaluators()
        
        # 加载默认规则
        await self._load_default_rules()
        
        self.running = True
        logger.info("Alert rule engine initialized")
    
    async def shutdown(self):
        """关闭规则引擎"""
        self.running = False
        
        # 取消所有评估任务
        for task in self.evaluation_tasks.values():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        self.evaluation_tasks.clear()
        logger.info("Alert rule engine shutdown")
    
    async def add_rule(self, rule: AlertRule) -> bool:
        """添加告警规则"""
        try:
            # 验证规则
            if not await self._validate_rule(rule):
                return False
            
            # 存储规则
            self.rules[rule.rule_id] = rule
            await self._store_rule(rule)
            
            # 启动规则评估
            if rule.enabled:
                await self._start_rule_evaluation(rule)
            
            logger.info(f"Added alert rule: {rule.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding alert rule: {e}")
            return False
    
    async def update_rule(self, rule: AlertRule) -> bool:
        """更新告警规则"""
        try:
            # 停止现有评估
            if rule.rule_id in self.evaluation_tasks:
                self.evaluation_tasks[rule.rule_id].cancel()
                del self.evaluation_tasks[rule.rule_id]
            
            # 更新规则
            self.rules[rule.rule_id] = rule
            await self._store_rule(rule)
            
            # 重新启动评估
            if rule.enabled:
                await self._start_rule_evaluation(rule)
            
            logger.info(f"Updated alert rule: {rule.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating alert rule: {e}")
            return False
    
    async def remove_rule(self, rule_id: str) -> bool:
        """删除告警规则"""
        try:
            # 停止评估
            if rule_id in self.evaluation_tasks:
                self.evaluation_tasks[rule_id].cancel()
                del self.evaluation_tasks[rule_id]
            
            # 删除规则
            if rule_id in self.rules:
                del self.rules[rule_id]
            
            # 从存储中删除
            await self._remove_rule_from_storage(rule_id)
            
            logger.info(f"Removed alert rule: {rule_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing alert rule: {e}")
            return False
    
    async def get_rules(self, enabled_only: bool = False) -> List[AlertRule]:
        """获取告警规则"""
        rules = list(self.rules.values())
        
        if enabled_only:
            rules = [rule for rule in rules if rule.enabled]
        
        return rules
    
    async def evaluate_rule_now(self, rule_id: str) -> EvaluationResult:
        """立即评估规则"""
        try:
            rule = self.rules.get(rule_id)
            if not rule:
                raise Exception(f"Rule not found: {rule_id}")
            
            # 选择评估器
            evaluator = self._select_evaluator(rule)
            if not evaluator:
                raise Exception(f"No evaluator available for rule: {rule_id}")
            
            # 执行评估
            result = await evaluator.evaluate_metric(rule)
            
            # 处理评估结果
            await self._handle_evaluation_result(rule, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error evaluating rule {rule_id}: {e}")
            raise
    
    async def _initialize_evaluators(self):
        """初始化评估器"""
        # Prometheus评估器
        if settings.PROMETHEUS_URL:
            self.evaluators["prometheus"] = PrometheusEvaluator(settings.PROMETHEUS_URL)
        
        # 自定义评估器
        self.evaluators["custom"] = CustomEvaluator()
    
    async def _load_default_rules(self):
        """加载默认规则"""
        default_rules = [
            # 错误率告警
            AlertRule(
                rule_id="error_rate_high",
                name="High Error Rate",
                description="Error rate is above 5%",
                severity=AlertSeverity.ERROR,
                metric_name="error_rate",
                metric_type=MetricType.RATE,
                evaluation_interval=EvaluationInterval.MINUTE_5,
                for_duration=timedelta(minutes=2),
                operator=ComparisonOperator.GREATER_THAN,
                threshold=5.0,
                aggregation=AggregationType.AVG,
                escalation_enabled=True,
                escalation_delay=timedelta(minutes=15)
            ),
            
            # 响应时间告警
            AlertRule(
                rule_id="response_time_high",
                name="High Response Time",
                description="Response time is above 1000ms",
                severity=AlertSeverity.WARNING,
                metric_name="response_time",
                metric_type=MetricType.GAUGE,
                evaluation_interval=EvaluationInterval.MINUTE_5,
                for_duration=timedelta(minutes=5),
                operator=ComparisonOperator.GREATER_THAN,
                threshold=1000.0,
                aggregation=AggregationType.P95,
                escalation_enabled=True,
                escalation_delay=timedelta(minutes=20)
            ),
            
            # 内存使用率告警
            AlertRule(
                rule_id="memory_usage_high",
                name="High Memory Usage",
                description="Memory usage is above 80%",
                severity=AlertSeverity.WARNING,
                metric_name="memory_usage",
                metric_type=MetricType.GAUGE,
                evaluation_interval=EvaluationInterval.MINUTE_1,
                for_duration=timedelta(minutes=3),
                operator=ComparisonOperator.GREATER_THAN,
                threshold=80.0,
                aggregation=AggregationType.AVG,
                escalation_enabled=True,
                escalation_delay=timedelta(minutes=10)
            ),
            
            # CPU使用率告警
            AlertRule(
                rule_id="cpu_usage_high",
                name="High CPU Usage",
                description="CPU usage is above 90%",
                severity=AlertSeverity.CRITICAL,
                metric_name="cpu_usage",
                metric_type=MetricType.GAUGE,
                evaluation_interval=EvaluationInterval.MINUTE_2,
                for_duration=timedelta(minutes=5),
                operator=ComparisonOperator.GREATER_THAN,
                threshold=90.0,
                aggregation=AggregationType.AVG,
                escalation_enabled=True,
                escalation_delay=timedelta(minutes=5)
            ),
            
            # 磁盘空间告警
            AlertRule(
                rule_id="disk_space_low",
                name="Low Disk Space",
                description="Disk space is below 10%",
                severity=AlertSeverity.CRITICAL,
                metric_name="disk_usage",
                metric_type=MetricType.GAUGE,
                evaluation_interval=EvaluationInterval.MINUTE_10,
                for_duration=timedelta(minutes=1),
                operator=ComparisonOperator.GREATER_THAN,
                threshold=90.0,
                aggregation=AggregationType.AVG,
                escalation_enabled=True,
                escalation_delay=timedelta(minutes=5)
            )
        ]
        
        for rule in default_rules:
            await self.add_rule(rule)
    
    async def _validate_rule(self, rule: AlertRule) -> bool:
        """验证规则"""
        try:
            # 基本验证
            if not rule.rule_id or not rule.name:
                logger.error("Rule ID and name are required")
                return False
            
            if rule.threshold < 0:
                logger.error("Threshold must be non-negative")
                return False
            
            # 检查评估器可用性
            evaluator = self._select_evaluator(rule)
            if not evaluator:
                logger.error(f"No evaluator available for rule: {rule.rule_id}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating rule: {e}")
            return False
    
    def _select_evaluator(self, rule: AlertRule) -> Optional[MetricEvaluator]:
        """选择评估器"""
        if rule.query or rule.metric_name.startswith("prometheus_"):
            return self.evaluators.get("prometheus")
        else:
            return self.evaluators.get("custom")
    
    async def _start_rule_evaluation(self, rule: AlertRule):
        """启动规则评估"""
        try:
            # 获取评估间隔
            interval_map = {
                EvaluationInterval.MINUTE_1: 60,
                EvaluationInterval.MINUTE_5: 300,
                EvaluationInterval.MINUTE_15: 900,
                EvaluationInterval.HOUR_1: 3600,
                EvaluationInterval.HOUR_6: 21600,
                EvaluationInterval.HOUR_12: 43200,
                EvaluationInterval.DAY_1: 86400
            }
            
            interval_seconds = interval_map.get(rule.evaluation_interval, 300)
            
            # 创建评估任务
            task = asyncio.create_task(self._rule_evaluation_loop(rule, interval_seconds))
            self.evaluation_tasks[rule.rule_id] = task
            
        except Exception as e:
            logger.error(f"Error starting rule evaluation: {e}")
    
    async def _rule_evaluation_loop(self, rule: AlertRule, interval_seconds: int):
        """规则评估循环"""
        consecutive_failures = 0
        max_failures = 5
        
        while self.running and rule.enabled:
            try:
                # 执行评估
                await self.evaluate_rule_now(rule.rule_id)
                
                consecutive_failures = 0
                
                # 等待下次评估
                await asyncio.sleep(interval_seconds)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                consecutive_failures += 1
                logger.error(f"Error in rule evaluation loop for {rule.rule_id}: {e}")
                
                # 如果连续失败次数过多，暂停评估
                if consecutive_failures >= max_failures:
                    logger.warning(f"Pausing evaluation for rule {rule.rule_id} due to consecutive failures")
                    await asyncio.sleep(interval_seconds * 2)  # 延长等待时间
                    consecutive_failures = 0
                else:
                    await asyncio.sleep(min(interval_seconds, 60))  # 最多等待1分钟
    
    async def _handle_evaluation_result(self, rule: AlertRule, result: EvaluationResult):
        """处理评估结果"""
        try:
            # 存储评估结果
            await self._store_evaluation_result(result)
            
            # 如果触发告警
            if result.triggered:
                await self._handle_triggered_rule(rule, result)
            else:
                await self._handle_resolved_rule(rule, result)
                
        except Exception as e:
            logger.error(f"Error handling evaluation result: {e}")
    
    async def _handle_triggered_rule(self, rule: AlertRule, result: EvaluationResult):
        """处理触发的规则"""
        try:
            # 检查是否已经存在活跃告警
            alert_key = f"active_alert:{rule.rule_id}"
            existing_alert = await self.redis_client.get(alert_key)
            
            if existing_alert:
                # 告警已存在，检查是否需要更新
                alert_data = json.loads(existing_alert)
                last_update = datetime.fromisoformat(alert_data["last_update"])
                
                # 如果在持续时间内，不重复创建告警
                if datetime.now() - last_update < rule.for_duration:
                    logger.debug(f"Alert for rule {rule.rule_id} already active and within duration")
                    return
            
            # 创建新告警
            alert = await alert_manager.create_alert(
                title=rule.name,
                description=rule.description,
                severity=rule.severity,
                source="alert_engine",
                service=rule.labels.get("service", "unknown"),
                environment=rule.labels.get("environment", "production"),
                labels=rule.labels,
                annotations=rule.annotations,
                current_value=result.current_value,
                threshold_value=result.threshold_value
            )
            
            # 存储活跃告警
            await self.redis_client.setex(
                alert_key,
                int(rule.for_duration.total_seconds()) + 3600,  # 额外1小时缓冲
                json.dumps({
                    "alert_id": alert.alert_id,
                    "rule_id": rule.rule_id,
                    "last_update": datetime.now().isoformat()
                })
            )
            
            logger.info(f"Created alert for triggered rule {rule.rule_id}: {alert.alert_id}")
            
        except Exception as e:
            logger.error(f"Error handling triggered rule: {e}")
    
    async def _handle_resolved_rule(self, rule: AlertRule, result: EvaluationResult):
        """处理解决的规则"""
        try:
            # 检查是否存在活跃告警
            alert_key = f"active_alert:{rule.rule_id}"
            existing_alert = await self.redis_client.get(alert_key)
            
            if existing_alert:
                alert_data = json.loads(existing_alert)
                alert_id = alert_data["alert_id"]
                
                # 解决告警
                await alert_manager.resolve_alert(alert_id)
                
                # 删除活跃告警记录
                await self.redis_client.delete(alert_key)
                
                logger.info(f"Resolved alert for rule {rule.rule_id}: {alert_id}")
                
        except Exception as e:
            logger.error(f"Error handling resolved rule: {e}")
    
    async def _store_rule(self, rule: AlertRule):
        """存储规则"""
        try:
            rule_key = f"alert_rule:{rule.rule_id}"
            rule_data = self._serialize_rule(rule)
            
            await self.redis_client.set(rule_key, rule_data)
            
        except Exception as e:
            logger.error(f"Error storing rule: {e}")
    
    async def _remove_rule_from_storage(self, rule_id: str):
        """从存储中删除规则"""
        try:
            rule_key = f"alert_rule:{rule_id}"
            await self.redis_client.delete(rule_key)
            
        except Exception as e:
            logger.error(f"Error removing rule from storage: {e}")
    
    async def _store_evaluation_result(self, result: EvaluationResult):
        """存储评估结果"""
        try:
            result_key = f"evaluation_result:{result.rule_id}:{int(result.timestamp.timestamp())}"
            result_data = self._serialize_evaluation_result(result)
            
            # 保存24小时
            await self.redis_client.setex(result_key, 24 * 3600, result_data)
            
        except Exception as e:
            logger.error(f"Error storing evaluation result: {e}")
    
    def _serialize_rule(self, rule: AlertRule) -> str:
        """序列化规则"""
        rule_dict = asdict(rule)
        rule_dict["severity"] = rule.severity.value
        rule_dict["metric_type"] = rule.metric_type.value
        rule_dict["evaluation_interval"] = rule.evaluation_interval.value
        rule_dict["for_duration"] = rule.for_duration.total_seconds()
        rule_dict["operator"] = rule.operator.value
        rule_dict["aggregation"] = rule.aggregation.value
        rule_dict["escalation_delay"] = rule.escalation_delay.total_seconds()
        rule_dict["cooldown_period"] = rule.cooldown_period.total_seconds()
        
        return json.dumps(rule_dict)
    
    def _serialize_evaluation_result(self, result: EvaluationResult) -> str:
        """序列化评估结果"""
        result_dict = asdict(result)
        result_dict["timestamp"] = result.timestamp.isoformat()
        
        return json.dumps(result_dict)


# 全局告警规则引擎实例
alert_rule_engine = AlertRuleEngine()
