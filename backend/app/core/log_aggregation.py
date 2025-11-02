"""
日志聚合系统 (Loki + Grafana)
提供集中式日志收集、存储、查询和可视化功能
"""
import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
import aiofiles
import gzip
import hashlib
from pathlib import Path

from app.core.redis_client import get_redis_client
from app.core.config import settings

logger = logging.getLogger(__name__)


class LogLevel(Enum):
    """日志级别"""
    TRACE = "trace"
    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"
    FATAL = "fatal"


class LogSource(Enum):
    """日志来源"""
    APPLICATION = "application"      # 应用日志
    ACCESS = "access"               # 访问日志
    ERROR = "error"                 # 错误日志
    AUDIT = "audit"                 # 审计日志
    PERFORMANCE = "performance"     # 性能日志
    SECURITY = "security"           # 安全日志
    BUSINESS = "business"           # 业务日志
    SYSTEM = "system"               # 系统日志


@dataclass
class LogEntry:
    """日志条目"""
    timestamp: datetime
    level: LogLevel
    message: str
    source: LogSource
    service: str
    environment: str
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    method: Optional[str] = None
    url: Optional[str] = None
    status_code: Optional[int] = None
    duration_ms: Optional[float] = None
    error_type: Optional[str] = None
    error_stack: Optional[str] = None
    tags: Dict[str, Any] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = {}
        if self.metadata is None:
            self.metadata = {}


@dataclass
class LogQuery:
    """日志查询"""
    query: str
    start_time: datetime
    end_time: datetime
    limit: int = 100
    level: Optional[LogLevel] = None
    source: Optional[LogSource] = None
    service: Optional[str] = None
    trace_id: Optional[str] = None
    user_id: Optional[str] = None
    tags: Dict[str, str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = {}


@dataclass
class LogQueryResult:
    """日志查询结果"""
    query: LogQuery
    total_count: int
    entries: List[LogEntry]
    execution_time_ms: float
    has_more: bool


class LokiClient:
    """
    Loki客户端
    负责与Loki API交互
    """
    
    def __init__(self, base_url: str, username: str = None, password: str = None):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _get_auth(self) -> Optional[aiohttp.BasicAuth]:
        """获取认证信息"""
        if self.username and self.password:
            return aiohttp.BasicAuth(self.username, self.password)
        return None
    
    async def push_logs(self, logs: List[LogEntry]) -> bool:
        """
        推送日志到Loki
        
        Args:
            logs: 日志条目列表
        """
        try:
            # 按stream分组日志
            streams = {}
            
            for log in logs:
                # 创建stream标签
                stream_labels = {
                    "level": log.level.value,
                    "source": log.source.value,
                    "service": log.service,
                    "environment": log.environment
                }
                
                # 添加可选标签
                if log.trace_id:
                    stream_labels["trace_id"] = log.trace_id
                if log.user_id:
                    stream_labels["user_id"] = log.user_id
                if log.method:
                    stream_labels["method"] = log.method
                
                # 创建stream key
                stream_key = json.dumps(stream_labels, sort_keys=True)
                
                if stream_key not in streams:
                    streams[stream_key] = {
                        "stream": stream_labels,
                        "values": []
                    }
                
                # 添加日志条目
                log_data = {
                    "timestamp": str(int(log.timestamp.timestamp() * 1e9)),  # 纳秒时间戳
                    "message": json.dumps({
                        "message": log.message,
                        "service": log.service,
                        "trace_id": log.trace_id,
                        "span_id": log.span_id,
                        "user_id": log.user_id,
                        "request_id": log.request_id,
                        "session_id": log.session_id,
                        "ip_address": log.ip_address,
                        "user_agent": log.user_agent,
                        "url": log.url,
                        "status_code": log.status_code,
                        "duration_ms": log.duration_ms,
                        "error_type": log.error_type,
                        "error_stack": log.error_stack,
                        "tags": log.tags,
                        "metadata": log.metadata
                    }, ensure_ascii=False)
                }
                
                streams[stream_key]["values"].append([
                    log_data["timestamp"],
                    log_data["message"]
                ])
            
            # 构建Loki推送请求
            payload = {
                "streams": list(streams.values())
            }
            
            # 发送到Loki
            url = f"{self.base_url}/loki/api/v1/push"
            headers = {"Content-Type": "application/json"}
            auth = self._get_auth()
            
            async with self.session.post(url, json=payload, headers=headers, auth=auth) as response:
                if response.status == 204:
                    logger.debug(f"Successfully pushed {len(logs)} logs to Loki")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to push logs to Loki: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error pushing logs to Loki: {e}")
            return False
    
    async def query_logs(self, query: LogQuery) -> LogQueryResult:
        """
        从Loki查询日志
        
        Args:
            query: 日志查询对象
        """
        try:
            # 构建LogQL查询
            logql_query = self._build_logql_query(query)
            
            # 构建查询参数
            params = {
                "query": logql_query,
                "limit": query.limit,
                "start": query.start_time.isoformat(),
                "end": query.end_time.isoformat()
            }
            
            # 执行查询
            url = f"{self.base_url}/loki/api/v1/query_range"
            headers = {"Accept": "application/json"}
            auth = self._get_auth()
            
            start_time = datetime.now()
            
            async with self.session.get(url, params=params, headers=headers, auth=auth) as response:
                if response.status == 200:
                    data = await response.json()
                    execution_time = (datetime.now() - start_time).total_seconds() * 1000
                    
                    # 解析查询结果
                    entries = self._parse_query_response(data)
                    total_count = len(entries)
                    has_more = total_count >= query.limit
                    
                    return LogQueryResult(
                        query=query,
                        total_count=total_count,
                        entries=entries,
                        execution_time_ms=execution_time,
                        has_more=has_more
                    )
                else:
                    error_text = await response.text()
                    raise Exception(f"Loki query failed: {response.status} - {error_text}")
                    
        except Exception as e:
            logger.error(f"Error querying logs from Loki: {e}")
            raise
    
    def _build_logql_query(self, query: LogQuery) -> str:
        """构建LogQL查询语句"""
        # 基础标签选择器
        selectors = []
        
        if query.level:
            selectors.append(f'level="{query.level.value}"')
        if query.source:
            selectors.append(f'source="{query.source.value}"')
        if query.service:
            selectors.append(f'service="{query.service}"')
        if query.trace_id:
            selectors.append(f'trace_id="{query.trace_id}"')
        if query.user_id:
            selectors.append(f'user_id="{query.user_id}"')
        
        # 添加标签过滤
        for key, value in query.tags.items():
            selectors.append(f'{key}="{value}"')
        
        # 构建基础查询
        base_query = "{" + ",".join(selectors) + "}" if selectors else "{}"
        
        # 添加文本搜索
        if query.query:
            base_query += f' =~ ".*{query.query}.*"'
        
        return base_query
    
    def _parse_query_response(self, data: Dict[str, Any]) -> List[LogEntry]:
        """解析Loki查询响应"""
        entries = []
        
        try:
            result_data = data.get("data", {}).get("result", [])
            
            for result in result_data:
                stream = result.get("stream", {})
                values = result.get("values", [])
                
                for value_pair in values:
                    timestamp_ns, log_message = value_pair
                    
                    # 解析时间戳
                    timestamp = datetime.fromtimestamp(int(timestamp_ns) / 1e9)
                    
                    # 解析日志消息
                    try:
                        message_data = json.loads(log_message)
                        message = message_data.get("message", log_message)
                        
                        # 创建日志条目
                        entry = LogEntry(
                            timestamp=timestamp,
                            level=LogLevel(stream.get("level", "info")),
                            message=message,
                            source=LogSource(stream.get("source", "application")),
                            service=stream.get("service", "unknown"),
                            environment=stream.get("environment", "unknown"),
                            trace_id=stream.get("trace_id"),
                            span_id=message_data.get("span_id"),
                            user_id=stream.get("user_id") or message_data.get("user_id"),
                            request_id=message_data.get("request_id"),
                            session_id=message_data.get("session_id"),
                            ip_address=message_data.get("ip_address"),
                            user_agent=message_data.get("user_agent"),
                            method=stream.get("method"),
                            url=message_data.get("url"),
                            status_code=message_data.get("status_code"),
                            duration_ms=message_data.get("duration_ms"),
                            error_type=message_data.get("error_type"),
                            error_stack=message_data.get("error_stack"),
                            tags=message_data.get("tags", {}),
                            metadata=message_data.get("metadata", {})
                        )
                        
                        entries.append(entry)
                        
                    except json.JSONDecodeError:
                        # 如果无法解析JSON，使用原始消息
                        entry = LogEntry(
                            timestamp=timestamp,
                            level=LogLevel(stream.get("level", "info")),
                            message=log_message,
                            source=LogSource(stream.get("source", "application")),
                            service=stream.get("service", "unknown"),
                            environment=stream.get("environment", "unknown"),
                            trace_id=stream.get("trace_id")
                        )
                        entries.append(entry)
            
            # 按时间戳排序
            entries.sort(key=lambda x: x.timestamp, reverse=True)
            
        except Exception as e:
            logger.error(f"Error parsing Loki response: {e}")
        
        return entries


class LogAggregator:
    """
    日志聚合器
    负责收集、处理和转发日志到Loki
    """
    
    def __init__(self, loki_client: LokiClient):
        self.loki_client = loki_client
        self.redis_client = None
        self.buffer: List[LogEntry] = []
        self.buffer_size = 1000  # 缓冲区大小
        self.flush_interval = 30  # 刷新间隔（秒）
        self.running = False
        self.flush_task = None
        
    async def start_aggregation(self):
        """启动日志聚合"""
        if self.running:
            return
        
        self.running = True
        self.redis_client = get_redis_client()
        self.flush_task = asyncio.create_task(self._flush_loop())
        logger.info("Log aggregation started")
    
    async def stop_aggregation(self):
        """停止日志聚合"""
        self.running = False
        if self.flush_task:
            self.flush_task.cancel()
            try:
                await self.flush_task
            except asyncio.CancelledError:
                pass
        
        # 刷新剩余日志
        if self.buffer:
            await self._flush_logs()
        
        logger.info("Log aggregation stopped")
    
    async def add_log(self, log_entry: LogEntry):
        """
        添加日志条目到缓冲区
        
        Args:
            log_entry: 日志条目
        """
        self.buffer.append(log_entry)
        
        # 如果缓冲区满了，立即刷新
        if len(self.buffer) >= self.buffer_size:
            await self._flush_logs()
    
    async def add_logs(self, log_entries: List[LogEntry]):
        """
        批量添加日志条目
        
        Args:
            log_entries: 日志条目列表
        """
        self.buffer.extend(log_entries)
        
        # 如果缓冲区满了，立即刷新
        if len(self.buffer) >= self.buffer_size:
            await self._flush_logs()
    
    async def query_logs(self, query: LogQuery) -> LogQueryResult:
        """
        查询日志
        
        Args:
            query: 日志查询
        """
        try:
            async with self.loki_client as client:
                return await client.query_logs(query)
        except Exception as e:
            logger.error(f"Error querying logs: {e}")
            raise
    
    async def _flush_loop(self):
        """刷新循环"""
        while self.running:
            try:
                await asyncio.sleep(self.flush_interval)
                if self.buffer:
                    await self._flush_logs()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in flush loop: {e}")
    
    async def _flush_logs(self):
        """刷新日志到Loki"""
        if not self.buffer:
            return
        
        try:
            logs_to_flush = self.buffer.copy()
            self.buffer.clear()
            
            # 发送到Loki
            async with self.loki_client as client:
                success = await client.push_logs(logs_to_flush)
                
                if success:
                    logger.debug(f"Flushed {len(logs_to_flush)} logs to Loki")
                else:
                    # 如果发送失败，重新加入缓冲区（但限制重试次数）
                    for log in logs_to_flush:
                        retry_count = log.metadata.get("retry_count", 0)
                        if retry_count < 3:
                            log.metadata["retry_count"] = retry_count + 1
                            self.buffer.append(log)
                    
                    logger.warning(f"Failed to flush logs, re-queued {len(self.buffer)} logs for retry")
            
        except Exception as e:
            logger.error(f"Error flushing logs: {e}")
            # 重新加入缓冲区
            self.buffer.extend(logs_to_flush)


class LogIndexManager:
    """
    日志索引管理器
    负责日志索引策略和优化
    """
    
    def __init__(self, redis_client):
        self.redis_client = redis_client
        
    async def create_log_index(self, index_name: str, config: Dict[str, Any]) -> bool:
        """
        创建日志索引
        
        Args:
            index_name: 索引名称
            config: 索引配置
        """
        try:
            index_key = f"log_index:{index_name}"
            
            # 存储索引配置
            await self.redis_client.hset(index_key, mapping={
                "name": index_name,
                "config": json.dumps(config),
                "created_at": datetime.now().isoformat(),
                "status": "active"
            })
            
            logger.info(f"Created log index: {index_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating log index {index_name}: {e}")
            return False
    
    async def get_log_indices(self) -> List[Dict[str, Any]]:
        """获取所有日志索引"""
        try:
            indices = []
            
            # 扫描所有索引
            async for key in self.redis_client.scan_iter(match="log_index:*"):
                index_data = await self.redis_client.hgetall(key)
                if index_data:
                    indices.append({
                        "name": index_data.get("name", "").decode(),
                        "config": json.loads(index_data.get("config", "{}").decode()),
                        "created_at": index_data.get("created_at", "").decode(),
                        "status": index_data.get("status", "").decode()
                    })
            
            return indices
            
        except Exception as e:
            logger.error(f"Error getting log indices: {e}")
            return []
    
    async def optimize_log_storage(self) -> Dict[str, Any]:
        """
        优化日志存储
        """
        try:
            optimization_result = {
                "compressed_files": 0,
                "freed_space_mb": 0,
                "archived_indices": 0
            }
            
            # 这里可以实现日志压缩、归档等优化逻辑
            # 暂时返回模拟结果
            
            logger.info("Log storage optimization completed")
            return optimization_result
            
        except Exception as e:
            logger.error(f"Error optimizing log storage: {e}")
            return {}


class LogAnalyzer:
    """
    日志分析器
    负责日志数据分析和洞察生成
    """
    
    def __init__(self, log_aggregator: LogAggregator):
        self.log_aggregator = log_aggregator
        
    async def analyze_log_patterns(
        self, 
        start_time: datetime, 
        end_time: datetime
    ) -> Dict[str, Any]:
        """
        分析日志模式
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
        """
        try:
            analysis_result = {
                "error_patterns": [],
                "performance_issues": [],
                "security_events": [],
                "usage_trends": {}
            }
            
            # 分析错误模式
            error_query = LogQuery(
                query="error OR exception OR failed",
                start_time=start_time,
                end_time=end_time,
                level=LogLevel.ERROR,
                limit=500
            )
            
            error_results = await self.log_aggregator.query_logs(error_query)
            analysis_result["error_patterns"] = self._analyze_error_patterns(error_results.entries)
            
            # 分析性能问题
            perf_query = LogQuery(
                query="slow OR timeout OR performance",
                start_time=start_time,
                end_time=end_time,
                source=LogSource.PERFORMANCE,
                limit=200
            )
            
            perf_results = await self.log_aggregator.query_logs(perf_query)
            analysis_result["performance_issues"] = self._analyze_performance_issues(perf_results.entries)
            
            # 分析安全事件
            security_query = LogQuery(
                query="security OR unauthorized OR attack",
                start_time=start_time,
                end_time=end_time,
                source=LogSource.SECURITY,
                limit=100
            )
            
            security_results = await self.log_aggregator.query_logs(security_query)
            analysis_result["security_events"] = self._analyze_security_events(security_results.entries)
            
            logger.info("Log pattern analysis completed")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error analyzing log patterns: {e}")
            return {}
    
    def _analyze_error_patterns(self, error_logs: List[LogEntry]) -> List[Dict[str, Any]]:
        """分析错误模式"""
        patterns = []
        
        # 统计错误类型
        error_types = Counter([log.error_type or "unknown" for log in error_logs])
        
        for error_type, count in error_types.most_common(10):
            patterns.append({
                "error_type": error_type,
                "count": count,
                "percentage": count / len(error_logs) * 100 if error_logs else 0,
                "severity": "high" if count > 50 else "medium" if count > 10 else "low"
            })
        
        return patterns
    
    def _analyze_performance_issues(self, perf_logs: List[LogEntry]) -> List[Dict[str, Any]]:
        """分析性能问题"""
        issues = []
        
        # 分析慢请求
        slow_requests = [log for log in perf_logs if log.duration_ms and log.duration_ms > 1000]
        
        if slow_requests:
            avg_duration = sum(log.duration_ms for log in slow_requests) / len(slow_requests)
            issues.append({
                "type": "slow_requests",
                "count": len(slow_requests),
                "avg_duration_ms": avg_duration,
                "max_duration_ms": max(log.duration_ms for log in slow_requests),
                "severity": "high" if avg_duration > 5000 else "medium"
            })
        
        return issues
    
    def _analyze_security_events(self, security_logs: List[LogEntry]) -> List[Dict[str, Any]]:
        """分析安全事件"""
        events = []
        
        # 统计安全事件类型
        event_types = Counter([log.tags.get("event_type", "unknown") for log in security_logs])
        
        for event_type, count in event_types.most_common(5):
            events.append({
                "event_type": event_type,
                "count": count,
                "severity": "critical" if event_type in ["attack", "breach"] else "high"
            })
        
        return events


# 全局日志聚合系统实例
loki_client = LokiClient(
    base_url=settings.LOKI_URL or "http://localhost:3100",
    username=settings.LOKI_USERNAME,
    password=settings.LOKI_PASSWORD
)

log_aggregator = LogAggregator(loki_client)
log_index_manager = LogIndexManager(get_redis_client())
log_analyzer = LogAnalyzer(log_aggregator)


# 导入Counter用于统计分析
from collections import Counter
