"""
业务指标收集器
收集和分析用户活跃度、功能使用率等核心业务指标
"""
import asyncio
import json
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import logging

from app.core.redis_client import get_redis_client
from app.core.database import get_db, AsyncSessionLocal
from app.models.user import User
from app.models.report import Report
from sqlalchemy import func, and_, or_
from app.core.monitoring import apm_collector

logger = logging.getLogger(__name__)


class UserActivityLevel(Enum):
    """用户活跃度级别"""
    NEW = "new"           # 新用户（注册7天内）
    ACTIVE = "active"     # 活跃用户（7天内有活动）
    RETURNING = "returning"  # 回访用户（7-30天内有活动）
    DORMANT = "dormant"   # 休眠用户（30-90天内有活动）
    CHURNED = "churned"   # 流失用户（90天以上无活动）


class FeatureType(Enum):
    """功能类型"""
    SEARCH = "search"           # 搜索功能
    CHAT = "chat"              # 聊天功能
    RESEARCH = "research"       # 深度研究
    REPORTS = "reports"         # 报告管理
    WATCHLIST = "watchlist"     # 观察列表
    HISTORY = "history"         # 历史记录
    SHARING = "sharing"         # 分享功能


@dataclass
class UserActivityEvent:
    """用户活动事件"""
    user_id: str
    event_type: str
    feature: FeatureType
    timestamp: datetime
    session_id: str
    properties: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.properties is None:
            self.properties = {}


@dataclass
class FeatureUsageMetrics:
    """功能使用指标"""
    feature: FeatureType
    total_users: int           # 总使用用户数
    active_users: int          # 活跃用户数（24小时）
    usage_count: int           # 使用次数
    avg_session_duration: float # 平均会话时长（秒）
    conversion_rate: float     # 转化率
    error_rate: float         # 错误率


@dataclass
class UserActivityMetrics:
    """用户活跃度指标"""
    date: datetime
    total_users: int
    new_users: int
    active_users: int          # 日活跃用户(DAU)
    weekly_active_users: int   # 周活跃用户(WAU)
    monthly_active_users: int  # 月活跃用户(MAU)
    returning_users: int
    dormant_users: int
    churned_users: int
    retention_rate: float      # 留存率
    engagement_score: float   # 参与度评分


class BusinessMetricsCollector:
    """
    业务指标收集器
    负责收集、存储和分析业务相关指标
    """
    
    def __init__(self):
        self.redis_client = None
        self.collection_interval = 300  # 5分钟收集一次
        self.running = False
        self.collection_task = None
        
        # 指标缓存
        self.activity_cache: Dict[str, List[UserActivityEvent]] = {}
        self.feature_usage_cache: Dict[FeatureType, List[Dict]] = {}
        
    async def start_collection(self):
        """开始指标收集"""
        if self.running:
            return
        
        self.running = True
        self.redis_client = get_redis_client()
        self.collection_task = asyncio.create_task(self._collection_loop())
        logger.info("Business metrics collection started")
    
    async def stop_collection(self):
        """停止指标收集"""
        self.running = False
        if self.collection_task:
            self.collection_task.cancel()
            try:
                await self.collection_task
            except asyncio.CancelledError:
                pass
        logger.info("Business metrics collection stopped")
    
    async def _collection_loop(self):
        """指标收集循环"""
        while self.running:
            try:
                await self._collect_daily_metrics()
                await self._collect_feature_metrics()
                await self._cleanup_old_data()
                await asyncio.sleep(self.collection_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in business metrics collection: {e}")
                await asyncio.sleep(60)
    
    async def track_user_activity(self, event: UserActivityEvent):
        """追踪用户活动"""
        try:
            # 存储到Redis用于实时分析
            event_key = f"user_activity:{event.user_id}:{event.timestamp.strftime('%Y%m%d')}"
            event_data = {
                "event_type": event.event_type,
                "feature": event.feature.value,
                "timestamp": event.timestamp.isoformat(),
                "session_id": event.session_id,
                "properties": event.properties
            }
            
            await self.redis_client.hset(event_key, f"{event.timestamp.timestamp()}", json.dumps(event_data))
            await self.redis_client.expire(event_key, 86400 * 30)  # 30天过期
            
            # 更新实时活跃用户集合
            today = datetime.now().strftime('%Y%m%d')
            await self.redis_client.sadd(f"active_users:{today}", event.user_id)
            await self.redis_client.expire(f"active_users:{today}", 86400 * 7)
            
            # 更新功能使用统计
            feature_key = f"feature_usage:{event.feature.value}:{today}"
            await self.redis_client.hincrby(feature_key, "usage_count", 1)
            await self.redis_client.sadd(f"feature_users:{event.feature.value}:{today}", event.user_id)
            await self.redis_client.expire(feature_key, 86400 * 7)
            
            logger.debug(f"Tracked user activity: {event.user_id} - {event.feature.value}")
            
        except Exception as e:
            logger.error(f"Error tracking user activity: {e}")
    
    async def get_user_activity_metrics(self, date: datetime = None) -> UserActivityMetrics:
        """获取用户活跃度指标"""
        if date is None:
            date = datetime.now().date()
        
        try:
            async with AsyncSessionLocal() as session:
                # 总用户数
                total_users_result = await session.execute(func.count(User.id))
                total_users = total_users_result.scalar() or 0
                
                # 新用户数（当天注册）
                new_users_result = await session.execute(
                    func.count(User.id).filter(
                        func.date(User.created_at) == date
                    )
                )
                new_users = new_users_result.scalar() or 0
                
                # 计算活跃用户指标
                dau = await self._get_active_users_count(date, 1)
                wau = await self._get_active_users_count(date, 7)
                mau = await self._get_active_users_count(date, 30)
                
                # 用户分层
                user_segments = await self._segment_users(date)
                
                # 留存率计算
                retention_rate = await self._calculate_retention_rate(date)
                
                # 参与度评分
                engagement_score = await self._calculate_engagement_score(date)
                
                return UserActivityMetrics(
                    date=datetime.combine(date, datetime.min.time()),
                    total_users=total_users,
                    new_users=new_users,
                    active_users=dau,
                    weekly_active_users=wau,
                    monthly_active_users=mau,
                    returning_users=user_segments.get(UserActivityLevel.RETURNING, 0),
                    dormant_users=user_segments.get(UserActivityLevel.DORMANT, 0),
                    churned_users=user_segments.get(UserActivityLevel.CHURNED, 0),
                    retention_rate=retention_rate,
                    engagement_score=engagement_score
                )
                
        except Exception as e:
            logger.error(f"Error getting user activity metrics: {e}")
            return UserActivityMetrics(
                date=datetime.combine(date, datetime.min.time()),
                total_users=0, new_users=0, active_users=0,
                weekly_active_users=0, monthly_active_users=0,
                returning_users=0, dormant_users=0, churned_users=0,
                retention_rate=0.0, engagement_score=0.0
            )
    
    async def get_feature_usage_metrics(self, date: datetime = None) -> List[FeatureUsageMetrics]:
        """获取功能使用指标"""
        if date is None:
            date = datetime.now().date()
        
        date_str = date.strftime('%Y%m%d')
        metrics = []
        
        for feature in FeatureType:
            try:
                # 功能使用次数
                usage_count = int(await self.redis_client.hget(f"feature_usage:{feature.value}:{date_str}", "usage_count") or 0)
                
                # 使用用户数
                feature_users = await self.redis_client.smembers(f"feature_users:{feature.value}:{date_str}")
                total_users = len(feature_users)
                
                # 活跃用户数（24小时内的去重用户）
                active_users = len(set(feature_users))
                
                # 平均会话时长（模拟数据，实际应该从会话数据计算）
                avg_session_duration = await self._get_avg_session_duration(feature, date)
                
                # 转化率（完成核心操作的用户比例）
                conversion_rate = await self._get_feature_conversion_rate(feature, date)
                
                # 错误率
                error_rate = await self._get_feature_error_rate(feature, date)
                
                metrics.append(FeatureUsageMetrics(
                    feature=feature,
                    total_users=total_users,
                    active_users=active_users,
                    usage_count=usage_count,
                    avg_session_duration=avg_session_duration,
                    conversion_rate=conversion_rate,
                    error_rate=error_rate
                ))
                
            except Exception as e:
                logger.error(f"Error getting feature metrics for {feature.value}: {e}")
                metrics.append(FeatureUsageMetrics(
                    feature=feature, total_users=0, active_users=0,
                    usage_count=0, avg_session_duration=0.0,
                    conversion_rate=0.0, error_rate=0.0
                ))
        
        return metrics
    
    async def _collect_daily_metrics(self):
        """收集日常指标"""
        try:
            today = datetime.now().date()
            metrics = await self.get_user_activity_metrics(today)
            
            # 存储到Redis
            metrics_key = f"daily_metrics:{today.strftime('%Y%m%d')}"
            await self.redis_client.set(metrics_key, json.dumps(asdict(metrics)), ex=86400 * 90)
            
            # 记录到APM系统
            apm_collector.record_business_metric("daily_active_users", metrics.active_users)
            apm_collector.record_business_metric("new_users", metrics.new_users)
            apm_collector.record_business_metric("retention_rate", metrics.retention_rate)
            
            logger.info(f"Collected daily metrics for {today}: DAU={metrics.active_users}")
            
        except Exception as e:
            logger.error(f"Error collecting daily metrics: {e}")
    
    async def _collect_feature_metrics(self):
        """收集功能指标"""
        try:
            today = datetime.now().date()
            feature_metrics = await self.get_feature_usage_metrics(today)
            
            # 存储到Redis
            metrics_key = f"feature_metrics:{today.strftime('%Y%m%d')}"
            metrics_data = {metric.feature.value: asdict(metric) for metric in feature_metrics}
            await self.redis_client.set(metrics_key, json.dumps(metrics_data), ex=86400 * 30)
            
            # 记录热门功能到APM
            top_feature = max(feature_metrics, key=lambda x: x.usage_count)
            apm_collector.record_business_metric("top_feature_usage", top_feature.usage_count)
            
            logger.info(f"Collected feature metrics: top feature={top_feature.feature.value}")
            
        except Exception as e:
            logger.error(f"Error collecting feature metrics: {e}")
    
    async def _cleanup_old_data(self):
        """清理过期数据"""
        try:
            # 清理90天前的用户活动数据
            cutoff_date = (datetime.now() - timedelta(days=90)).strftime('%Y%m%d')
            
            # 这里应该实现具体的数据清理逻辑
            # 由于Redis有自动过期，主要是清理数据库中的历史数据
            
            logger.debug("Completed data cleanup")
            
        except Exception as e:
            logger.error(f"Error during data cleanup: {e}")
    
    async def _get_active_users_count(self, date: datetime, days: int) -> int:
        """获取指定天数内的活跃用户数"""
        try:
            active_users = set()
            for i in range(days):
                check_date = date - timedelta(days=i)
                date_str = check_date.strftime('%Y%m%d')
                users = await self.redis_client.smembers(f"active_users:{date_str}")
                active_users.update(users)
            return len(active_users)
        except Exception as e:
            logger.error(f"Error getting active users count: {e}")
            return 0
    
    async def _segment_users(self, date: datetime) -> Dict[UserActivityLevel, int]:
        """用户分层"""
        segments = {level: 0 for level in UserActivityLevel}
        
        try:
            async with AsyncSessionLocal() as session:
                # 获取所有用户最后活动时间
                # 这里需要根据实际的用户活动表来查询
                # 暂时返回模拟数据
                
                # 新用户（7天内注册）
                new_users_result = await session.execute(
                    func.count(User.id).filter(
                        User.created_at >= date - timedelta(days=7)
                    )
                )
                segments[UserActivityLevel.NEW] = new_users_result.scalar() or 0
                
                # 其他分段需要基于活动数据计算
                # 这里简化处理
                segments[UserActivityLevel.ACTIVE] = segments[UserActivityLevel.NEW] + 50
                segments[UserActivityLevel.RETURNING] = 30
                segments[UserActivityLevel.DORMANT] = 20
                segments[UserActivityLevel.CHURNED] = 10
                
        except Exception as e:
            logger.error(f"Error segmenting users: {e}")
        
        return segments
    
    async def _calculate_retention_rate(self, date: datetime) -> float:
        """计算留存率"""
        try:
            # 简化的留存率计算：周活跃用户中的日活跃用户比例
            dau = await self._get_active_users_count(date, 1)
            wau = await self._get_active_users_count(date, 7)
            
            return (dau / wau) if wau > 0 else 0.0
        except Exception as e:
            logger.error(f"Error calculating retention rate: {e}")
            return 0.0
    
    async def _calculate_engagement_score(self, date: datetime) -> float:
        """计算参与度评分"""
        try:
            # 基于多个因素计算参与度评分
            # 1. 活跃用户比例
            async with AsyncSessionLocal() as session:
                total_users_result = await session.execute(func.count(User.id))
                total_users = total_users_result.scalar() or 1
            
            dau = await self._get_active_users_count(date, 1)
            activity_ratio = dau / total_users
            
            # 2. 功能使用多样性
            feature_metrics = await self.get_feature_usage_metrics(date)
            used_features = sum(1 for metric in feature_metrics if metric.active_users > 0)
            feature_diversity = used_features / len(FeatureType)
            
            # 3. 会话时长（模拟）
            avg_session_score = 0.7  # 基于实际会话数据计算
            
            # 综合评分
            engagement_score = (activity_ratio * 0.4 + feature_diversity * 0.3 + avg_session_score * 0.3) * 100
            
            return round(engagement_score, 2)
            
        except Exception as e:
            logger.error(f"Error calculating engagement score: {e}")
            return 0.0
    
    async def _get_avg_session_duration(self, feature: FeatureType, date: datetime) -> float:
        """获取功能平均会话时长"""
        # 这里应该从实际的会话数据中计算
        # 暂时返回模拟数据
        duration_map = {
            FeatureType.SEARCH: 45.0,
            FeatureType.CHAT: 180.0,
            FeatureType.RESEARCH: 600.0,
            FeatureType.REPORTS: 120.0,
            FeatureType.WATCHLIST: 90.0,
            FeatureType.HISTORY: 60.0,
            FeatureType.SHARING: 30.0
        }
        return duration_map.get(feature, 60.0)
    
    async def _get_feature_conversion_rate(self, feature: FeatureType, date: datetime) -> float:
        """获取功能转化率"""
        # 这里应该基于具体的转化目标计算
        # 暂时返回模拟数据
        conversion_map = {
            FeatureType.SEARCH: 0.85,    # 搜索->查看结果
            FeatureType.CHAT: 0.92,      # 聊天->获得回复
            FeatureType.RESEARCH: 0.78,  # 研究->生成报告
            FeatureType.REPORTS: 0.65,   # 报告->分享
            FeatureType.WATCHLIST: 0.45, # 观察列表->创建提醒
            FeatureType.HISTORY: 0.90,   # 历史->重新访问
            FeatureType.SHARING: 0.35    # 分享->被查看
        }
        return conversion_map.get(feature, 0.5)
    
    async def _get_feature_error_rate(self, feature: FeatureType, date: datetime) -> float:
        """获取功能错误率"""
        # 这里应该从错误监控数据中计算
        # 暂时返回模拟数据
        error_map = {
            FeatureType.SEARCH: 0.02,
            FeatureType.CHAT: 0.03,
            FeatureType.RESEARCH: 0.05,
            FeatureType.REPORTS: 0.04,
            FeatureType.WATCHLIST: 0.01,
            FeatureType.HISTORY: 0.01,
            FeatureType.SHARING: 0.06
        }
        return error_map.get(feature, 0.02)


# 全局业务指标收集器实例
business_metrics_collector = BusinessMetricsCollector()
