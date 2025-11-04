"""
转化率监控和分析系统
监控关键业务转化事件，分析转化趋势和影响因素
"""
import asyncio
import json
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import numpy as np

from app.core.redis_client import get_redis_client
from app.core.database import AsyncSessionLocal
from app.core.funnel_analyzer import funnel_analyzer, FunnelType, FunnelStage
from app.models.user import User
from app.models.report import Report
from app.models.conversation import Conversation

logger = logging.getLogger(__name__)


class ConversionEventType(Enum):
    """转化事件类型"""
    USER_REGISTRATION = "user_registration"          # 用户注册
    FIRST_SEARCH = "first_search"                    # 首次搜索
    FIRST_CHAT = "first_chat"                        # 首次聊天
    SEARCH_TO_CHAT = "search_to_chat"                # 搜索到聊天
    CHAT_TO_RESEARCH = "chat_to_research"            # 聊天到研究
    RESEARCH_TO_REPORT = "research_to_report"        # 研究到报告
    REPORT_GENERATION = "report_generation"          # 报告生成
    REPORT_SHARING = "report_sharing"                # 报告分享
    PREMIUM_UPGRADE = "premium_upgrade"              # 付费升级
    FEATURE_ADOPTION = "feature_adoption"            # 功能采用


class ConversionMetricType(Enum):
    """转化指标类型"""
    RATE = "rate"                    # 转化率
    COUNT = "count"                  # 转化数量
    REVENUE = "revenue"              # 收入转化
    TIME_TO_CONVERT = "time_to_convert"  # 转化时间
    RETENTION = "retention"          # 留存转化


@dataclass
class ConversionEvent:
    """转化事件"""
    event_type: ConversionEventType
    user_id: str
    timestamp: datetime
    properties: Dict[str, Any] = None
    conversion_value: float = 0.0
    
    def __post_init__(self):
        if self.properties is None:
            self.properties = {}


@dataclass
class ConversionMetrics:
    """转化指标"""
    event_type: ConversionEventType
    time_period: str
    total_conversions: int
    conversion_rate: float
    conversion_value: float
    avg_time_to_convert: float
    retention_rate: float
    trend_direction: str  # up, down, stable
    trend_percentage: float


@dataclass
class ConversionSegment:
    """转化分群数据"""
    segment_name: str
    segment_size: int
    conversion_rate: float
    conversion_count: int
    lift_vs_baseline: float  # 相对基准的提升


@dataclass
class ConversionAnalysis:
    """转化分析结果"""
    event_type: ConversionEventType
    time_period: str
    overall_metrics: ConversionMetrics
    segments: List[ConversionSegment]
    trends: List[Dict[str, Any]]
    insights: List[str]
    recommendations: List[str]


class ConversionMonitor:
    """
    转化监控器
    监控和分析业务转化事件
    """
    
    def __init__(self):
        self.redis_client = None
        self.monitoring_interval = 300  # 5分钟监控一次
        self.running = False
        self.monitoring_task = None
        
    async def start_monitoring(self):
        """开始转化监控"""
        if self.running:
            return
        
        self.running = True
        self.redis_client = get_redis_client()
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Conversion monitoring started")
    
    async def stop_monitoring(self):
        """停止转化监控"""
        self.running = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Conversion monitoring stopped")
    
    async def _monitoring_loop(self):
        """监控循环"""
        while self.running:
            try:
                await self._collect_conversion_metrics()
                await self._analyze_conversion_trends()
                await asyncio.sleep(self.monitoring_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in conversion monitoring: {e}")
                await asyncio.sleep(60)
    
    async def track_conversion_event(self, event: ConversionEvent):
        """
        追踪转化事件
        
        Args:
            event: 转化事件
        """
        try:
            # 存储转化事件
            event_key = f"conversion_events:{event.event_type.value}:{event.timestamp.strftime('%Y%m%d')}"
            event_data = {
                "user_id": event.user_id,
                "timestamp": event.timestamp.isoformat(),
                "properties": event.properties,
                "conversion_value": event.conversion_value
            }
            
            await self.redis_client.hset(event_key, f"{event.user_id}_{event.timestamp.timestamp()}", json.dumps(event_data))
            await self.redis_client.expire(event_key, 86400 * 90)  # 90天过期
            
            # 更新转化计数
            counter_key = f"conversion_counter:{event.event_type.value}:{event.timestamp.strftime('%Y%m%d')}"
            await self.redis_client.incr(counter_key)
            await self.redis_client.expire(counter_key, 86400 * 90)
            
            # 更新用户转化状态
            user_conversion_key = f"user_conversions:{event.user_id}"
            await self.redis_client.hset(user_conversion_key, event.event_type.value, event.timestamp.isoformat())
            await self.redis_client.expire(user_conversion_key, 86400 * 365)
            
            # 追踪到漏斗分析器
            funnel_stage = self._map_conversion_to_funnel_stage(event.event_type)
            if funnel_stage:
                funnel_type = self._map_conversion_to_funnel_type(event.event_type)
                await funnel_analyzer.track_funnel_event(
                    user_id=event.user_id,
                    funnel_type=funnel_type,
                    stage=funnel_stage,
                    properties=event.properties
                )
            
            logger.debug(f"Tracked conversion event: {event.event_type.value} for user {event.user_id}")
            
        except Exception as e:
            logger.error(f"Error tracking conversion event: {e}")
    
    async def analyze_conversion(
        self, 
        event_type: ConversionEventType,
        start_date: datetime = None,
        end_date: datetime = None,
        segment_by: str = "all"
    ) -> ConversionAnalysis:
        """
        分析转化数据
        
        Args:
            event_type: 转化事件类型
            start_date: 开始日期
            end_date: 结束日期
            segment_by: 分群维度
        """
        if start_date is None:
            start_date = datetime.now() - timedelta(days=7)
        if end_date is None:
            end_date = datetime.now()
        
        time_period = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        
        try:
            # 计算整体指标
            overall_metrics = await self._calculate_overall_metrics(event_type, start_date, end_date)
            
            # 分析分群数据
            segments = await self._analyze_conversion_segments(event_type, start_date, end_date, segment_by)
            
            # 分析趋势
            trends = await self._analyze_conversion_trends(event_type, start_date, end_date)
            
            # 生成洞察和建议
            insights = await self._generate_conversion_insights(event_type, overall_metrics, segments)
            recommendations = await self._generate_conversion_recommendations(event_type, overall_metrics, segments)
            
            return ConversionAnalysis(
                event_type=event_type,
                time_period=time_period,
                overall_metrics=overall_metrics,
                segments=segments,
                trends=trends,
                insights=insights,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Error analyzing conversion {event_type.value}: {e}")
            raise
    
    async def get_conversion_cohort_analysis(self, event_type: ConversionEventType, cohort_days: int = 7) -> Dict[str, Any]:
        """
        转化队列分析
        
        Args:
            event_type: 转化事件类型
            cohort_days: 队列天数
        """
        try:
            cohorts = {}
            current_date = datetime.now().date()
            
            for i in range(cohort_days):
                cohort_date = current_date - timedelta(days=i)
                cohort_key = f"conversion_cohort:{event_type.value}:{cohort_date.strftime('%Y%m%d')}"
                
                # 获取队列转化数据
                cohort_data = await self.redis_client.hgetall(cohort_key)
                
                if cohort_data:
                    cohorts[cohort_date.isoformat()] = {
                        "day_0": int(cohort_data.get("day_0", 0)),
                        "day_1": int(cohort_data.get("day_1", 0)),
                        "day_3": int(cohort_data.get("day_3", 0)),
                        "day_7": int(cohort_data.get("day_7", 0)),
                        "day_14": int(cohort_data.get("day_14", 0)),
                        "day_30": int(cohort_data.get("day_30", 0))
                    }
            
            return {
                "event_type": event_type.value,
                "cohorts": cohorts,
                "analysis_date": current_date.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting conversion cohort analysis: {e}")
            return {}
    
    async def _collect_conversion_metrics(self):
        """收集转化指标"""
        try:
            today = datetime.now().date()
            
            for event_type in ConversionEventType:
                # 收集当日转化数据
                metrics = await self._calculate_overall_metrics(event_type, today, today + timedelta(days=1))
                
                # 存储到Redis
                metrics_key = f"conversion_metrics:{event_type.value}:{today.strftime('%Y%m%d')}"
                await self.redis_client.set(metrics_key, json.dumps(asdict(metrics)), ex=86400 * 90)
                
                logger.debug(f"Collected conversion metrics for {event_type.value}")
            
        except Exception as e:
            logger.error(f"Error collecting conversion metrics: {e}")
    
    async def _analyze_conversion_trends(self):
        """分析转化趋势"""
        try:
            # 这里可以实现趋势分析逻辑
            # 比较不同时间段的转化率变化
            pass
        except Exception as e:
            logger.error(f"Error analyzing conversion trends: {e}")
    
    async def _calculate_overall_metrics(
        self, 
        event_type: ConversionEventType,
        start_date: datetime,
        end_date: datetime
    ) -> ConversionMetrics:
        """计算整体转化指标"""
        
        # 获取转化总数
        total_conversions = await self._get_conversion_count(event_type, start_date, end_date)
        
        # 获取总用户数（用于计算转化率）
        total_users = await self._get_total_users(start_date, end_date)
        conversion_rate = total_conversions / total_users if total_users > 0 else 0.0
        
        # 计算转化价值
        conversion_value = await self._get_conversion_value(event_type, start_date, end_date)
        
        # 计算平均转化时间
        avg_time_to_convert = await self._get_avg_conversion_time(event_type, start_date, end_date)
        
        # 计算留存率
        retention_rate = await self._get_conversion_retention(event_type, start_date, end_date)
        
        # 分析趋势
        trend_direction, trend_percentage = await self._analyze_trend_direction(event_type, start_date, end_date)
        
        return ConversionMetrics(
            event_type=event_type,
            time_period=f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            total_conversions=total_conversions,
            conversion_rate=conversion_rate,
            conversion_value=conversion_value,
            avg_time_to_convert=avg_time_to_convert,
            retention_rate=retention_rate,
            trend_direction=trend_direction,
            trend_percentage=trend_percentage
        )
    
    async def _analyze_conversion_segments(
        self, 
        event_type: ConversionEventType,
        start_date: datetime,
        end_date: datetime,
        segment_by: str
    ) -> List[ConversionSegment]:
        """分析转化分群"""
        segments = []
        
        if segment_by == "user_type":
            # 按用户类型分群
            new_users_rate = await self._get_segment_conversion_rate(event_type, "new_users", start_date, end_date)
            returning_users_rate = await self._get_segment_conversion_rate(event_type, "returning_users", start_date, end_date)
            
            segments.append(ConversionSegment(
                segment_name="新用户",
                segment_size=100,  # 模拟数据
                conversion_rate=new_users_rate,
                conversion_count=int(100 * new_users_rate),
                lift_vs_baseline=-0.1  # 相对基准下降10%
            ))
            
            segments.append(ConversionSegment(
                segment_name="回访用户",
                segment_size=150,  # 模拟数据
                conversion_rate=returning_users_rate,
                conversion_count=int(150 * returning_users_rate),
                lift_vs_baseline=0.2  # 相对基准提升20%
            ))
        
        elif segment_by == "acquisition_channel":
            # 按获客渠道分群
            channels = ["organic", "direct", "referral", "social"]
            for channel in channels:
                rate = await self._get_segment_conversion_rate(event_type, channel, start_date, end_date)
                lift = np.random.uniform(-0.2, 0.3)  # 模拟数据
                
                segments.append(ConversionSegment(
                    segment_name=channel,
                    segment_size=np.random.randint(50, 200),
                    conversion_rate=rate,
                    conversion_count=int(100 * rate),
                    lift_vs_baseline=lift
                ))
        
        return segments
    
    async def _get_conversion_count(
        self, 
        event_type: ConversionEventType,
        start_date: datetime,
        end_date: datetime
    ) -> int:
        """获取转化次数"""
        try:
            total_count = 0
            current_date = start_date.date()
            
            while current_date <= end_date.date():
                counter_key = f"conversion_counter:{event_type.value}:{current_date.strftime('%Y%m%d')}"
                count = await self.redis_client.get(counter_key)
                if count:
                    total_count += int(count)
                current_date += timedelta(days=1)
            
            return total_count
            
        except Exception as e:
            logger.error(f"Error getting conversion count: {e}")
            return 0
    
    async def _get_total_users(self, start_date: datetime, end_date: datetime) -> int:
        """获取总用户数"""
        try:
            async with AsyncSessionLocal() as session:
                from sqlalchemy import func
                result = await session.execute(
                    func.count(User.id).filter(
                        User.created_at.between(start_date, end_date)
                    )
                )
                return result.scalar() or 0
        except Exception as e:
            logger.error(f"Error getting total users: {e}")
            return 1  # 返回1避免除零错误
    
    async def _get_conversion_value(
        self, 
        event_type: ConversionEventType,
        start_date: datetime,
        end_date: datetime
    ) -> float:
        """获取转化价值"""
        # 这里应该基于实际的转化价值计算
        # 暂时返回模拟数据
        value_mapping = {
            ConversionEventType.USER_REGISTRATION: 1.0,
            ConversionEventType.FIRST_SEARCH: 0.5,
            ConversionEventType.FIRST_CHAT: 2.0,
            ConversionEventType.REPORT_GENERATION: 5.0,
            ConversionEventType.REPORT_SHARING: 3.0,
            ConversionEventType.PREMIUM_UPGRADE: 50.0
        }
        return value_mapping.get(event_type, 1.0) * np.random.uniform(0.8, 1.2)
    
    async def _get_avg_conversion_time(
        self, 
        event_type: ConversionEventType,
        start_date: datetime,
        end_date: datetime
    ) -> float:
        """获取平均转化时间"""
        # 这里应该基于实际的时间戳数据计算
        # 暂时返回模拟数据
        time_mapping = {
            ConversionEventType.USER_REGISTRATION: 120.0,  # 2分钟
            ConversionEventType.FIRST_SEARCH: 300.0,      # 5分钟
            ConversionEventType.FIRST_CHAT: 600.0,        # 10分钟
            ConversionEventType.RESEARCH_TO_REPORT: 1800.0,  # 30分钟
            ConversionEventType.REPORT_GENERATION: 900.0,  # 15分钟
        }
        return time_mapping.get(event_type, 300.0)
    
    async def _get_conversion_retention(
        self, 
        event_type: ConversionEventType,
        start_date: datetime,
        end_date: datetime
    ) -> float:
        """获取转化留存率"""
        # 这里应该基于实际的留存数据计算
        # 暂时返回模拟数据
        return np.random.uniform(0.6, 0.9)
    
    async def _analyze_trend_direction(
        self, 
        event_type: ConversionEventType,
        start_date: datetime,
        end_date: datetime
    ) -> Tuple[str, float]:
        """分析趋势方向"""
        # 比较当前周期和上一个周期的转化率
        period_length = (end_date - start_date).days
        previous_start = start_date - timedelta(days=period_length)
        previous_end = start_date
        
        current_rate = await self._get_conversion_rate(event_type, start_date, end_date)
        previous_rate = await self._get_conversion_rate(event_type, previous_start, previous_end)
        
        if previous_rate == 0:
            return "stable", 0.0
        
        change_percentage = ((current_rate - previous_rate) / previous_rate) * 100
        
        if change_percentage > 5:
            return "up", abs(change_percentage)
        elif change_percentage < -5:
            return "down", abs(change_percentage)
        else:
            return "stable", abs(change_percentage)
    
    async def _get_conversion_rate(
        self, 
        event_type: ConversionEventType,
        start_date: datetime,
        end_date: datetime
    ) -> float:
        """获取转化率"""
        conversions = await self._get_conversion_count(event_type, start_date, end_date)
        users = await self._get_total_users(start_date, end_date)
        return conversions / users if users > 0 else 0.0
    
    async def _get_segment_conversion_rate(
        self, 
        event_type: ConversionEventType,
        segment: str,
        start_date: datetime,
        end_date: datetime
    ) -> float:
        """获取分群转化率"""
        # 这里应该基于实际的分群数据计算
        # 暂时返回模拟数据
        base_rate = np.random.uniform(0.1, 0.4)
        
        if segment == "returning_users":
            return base_rate * 1.3
        elif segment == "new_users":
            return base_rate * 0.8
        elif segment == "organic":
            return base_rate * 1.2
        else:
            return base_rate
    
    async def _generate_conversion_insights(
        self, 
        event_type: ConversionEventType,
        metrics: ConversionMetrics,
        segments: List[ConversionSegment]
    ) -> List[str]:
        """生成转化洞察"""
        insights = []
        
        # 整体转化率分析
        if metrics.conversion_rate > 0.3:
            insights.append(f"{event_type.value}转化率表现良好 ({metrics.conversion_rate:.1%})")
        elif metrics.conversion_rate < 0.1:
            insights.append(f"{event_type.value}转化率偏低 ({metrics.conversion_rate:.1%})，需要优化")
        
        # 趋势分析
        if metrics.trend_direction == "up":
            insights.append(f"转化率呈上升趋势，增长{metrics.trend_percentage:.1f}%")
        elif metrics.trend_direction == "down":
            insights.append(f"转化率呈下降趋势，下降{metrics.trend_percentage:.1f}%")
        
        # 分群洞察
        if segments:
            best_segment = max(segments, key=lambda x: x.conversion_rate)
            worst_segment = min(segments, key=lambda x: x.conversion_rate)
            
            insights.append(f"表现最好的分群：{best_segment.segment_name} ({best_segment.conversion_rate:.1%})")
            insights.append(f"需要改进的分群：{worst_segment.segment_name} ({worst_segment.conversion_rate:.1%})")
        
        return insights
    
    async def _generate_conversion_recommendations(
        self, 
        event_type: ConversionEventType,
        metrics: ConversionMetrics,
        segments: List[ConversionSegment]
    ) -> List[str]:
        """生成转化优化建议"""
        recommendations = []
        
        # 基于转化率的建议
        if metrics.conversion_rate < 0.1:
            recommendations.append("简化转化流程，减少用户操作步骤")
            recommendations.append("优化用户引导，提供更清晰的转化路径")
        
        # 基于转化时间的建议
        if metrics.avg_time_to_convert > 1800:  # 30分钟
            recommendations.append("优化页面加载速度和响应时间")
            recommendations.append("提供进度指示，减少用户等待焦虑")
        
        # 基于分群的建议
        if segments:
            low_performing_segments = [s for s in segments if s.conversion_rate < 0.1]
            for segment in low_performing_segments:
                recommendations.append(f"针对{segment.segment_name}分群制定专门的优化策略")
        
        # 通用建议
        recommendations.append("定期进行A/B测试优化转化率")
        recommendations.append("分析用户行为数据，识别转化障碍")
        
        return recommendations
    
    def _map_conversion_to_funnel_stage(self, event_type: ConversionEventType) -> Optional[FunnelStage]:
        """将转化事件映射到漏斗阶段"""
        mapping = {
            ConversionEventType.USER_REGISTRATION: FunnelStage.SIGNUP_COMPLETE,
            ConversionEventType.FIRST_SEARCH: FunnelStage.FIRST_SEARCH,
            ConversionEventType.FIRST_CHAT: FunnelStage.FIRST_CHAT,
            ConversionEventType.SEARCH_TO_CHAT: FunnelStage.CHAT_INITIATED,
            ConversionEventType.CHAT_TO_RESEARCH: FunnelStage.RESEARCH_REQUEST,
            ConversionEventType.RESEARCH_TO_REPORT: FunnelStage.REPORT_GENERATED,
            ConversionEventType.REPORT_GENERATION: FunnelStage.REPORT_GENERATED,
            ConversionEventType.REPORT_SHARING: FunnelStage.SHARE_COMPLETED
        }
        return mapping.get(event_type)
    
    def _map_conversion_to_funnel_type(self, event_type: ConversionEventType) -> Optional[FunnelType]:
        """将转化事件映射到漏斗类型"""
        if event_type in [ConversionEventType.USER_REGISTRATION, ConversionEventType.FIRST_SEARCH, ConversionEventType.FIRST_CHAT]:
            return FunnelType.USER_ONBOARDING
        elif event_type in [ConversionEventType.SEARCH_TO_CHAT]:
            return FunnelType.SEARCH_TO_CHAT
        elif event_type in [ConversionEventType.CHAT_TO_RESEARCH]:
            return FunnelType.CHAT_TO_RESEARCH
        elif event_type in [ConversionEventType.RESEARCH_TO_REPORT, ConversionEventType.REPORT_GENERATION]:
            return FunnelType.RESEARCH_TO_REPORT
        elif event_type in [ConversionEventType.REPORT_SHARING]:
            return FunnelType.REPORT_TO_SHARE
        else:
            return FunnelType.DISCOVERY_TO_USAGE


# 全局转化监控器实例
conversion_monitor = ConversionMonitor()
