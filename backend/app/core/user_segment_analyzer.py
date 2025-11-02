"""
用户分群和行为分析系统
提供用户分群、行为模式分析和个性化洞察
"""
import asyncio
import json
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import numpy as np
from collections import defaultdict, Counter

from app.core.redis_client import get_redis_client
from app.core.database import get_db_session
from app.core.business_metrics import business_metrics_collector
from app.core.funnel_analyzer import funnel_analyzer, FunnelType, FunnelStage
from app.core.conversion_monitor import conversion_monitor, ConversionEventType
from app.models.user import User
from app.models.report import Report
from app.models.conversation import Conversation

logger = logging.getLogger(__name__)


class UserSegmentType(Enum):
    """用户分群类型"""
    ACTIVITY_LEVEL = "activity_level"      # 活跃度分群
    ENGAGEMENT = "engagement"              # 参与度分群
    LIFECYCLE = "lifecycle"                # 生命周期分群
    BEHAVIOR_PATTERN = "behavior_pattern"  # 行为模式分群
    VALUE_BASED = "value_based"            # 价值分群
    ACQUISITION_CHANNEL = "acquisition_channel"  # 获客渠道分群
    FEATURE_ADOPTION = "feature_adoption"  # 功能采用分群
    RISK_LEVEL = "risk_level"              # 风险等级分群


class ActivityLevel(Enum):
    """活跃度等级"""
    POWER_USER = "power_user"      # 重度用户
    ACTIVE_USER = "active_user"    # 活跃用户
    MODERATE_USER = "moderate_user"  # 中度用户
    LIGHT_USER = "light_user"      # 轻度用户
    DORMANT_USER = "dormant_user"  # 休眠用户
    CHURNED_USER = "churned_user"  # 流失用户


class EngagementLevel(Enum):
    """参与度等级"""
    HIGHLY_ENGAGED = "highly_engaged"  # 高参与
    ENGAGED = "engaged"                # 参与中
    LOW_ENGAGED = "low_engaged"        # 低参与
    NOT_ENGAGED = "not_engaged"        # 无参与


class LifecycleStage(Enum):
    """生命周期阶段"""
    NEW_USER = "new_user"              # 新用户
    ONBOARDING = "onboarding"          # 引导期
    ACTIVE_USER = "active_user"        # 活跃期
    LOYAL_USER = "loyal_user"          # 忠诚期
    AT_RISK = "at_risk"                # 流失风险
    CHURNED = "churned"                # 已流失


class BehaviorPattern(Enum):
    """行为模式"""
    RESEARCH_FOCUSED = "research_focused"    # 研究导向
    QUICK_CHAT = "quick_chat"                # 快速聊天
    POWER_SEARCHER = "power_searcher"        # 重度搜索
    SOCIAL_SHARER = "social_sharer"          # 社交分享
    REPORT_GENERATOR = "report_generator"    # 报告生成
    EXPLORER = "explorer"                    # 探索型


@dataclass
class UserSegment:
    """用户分群"""
    segment_id: str
    segment_type: UserSegmentType
    segment_name: str
    description: str
    user_count: int
    percentage: float
    criteria: Dict[str, Any]
    characteristics: List[str]
    created_at: datetime


@dataclass
class UserBehaviorProfile:
    """用户行为画像"""
    user_id: str
    activity_level: ActivityLevel
    engagement_level: EngagementLevel
    lifecycle_stage: LifecycleStage
    behavior_pattern: BehaviorPattern
    preferred_features: List[str]
    usage_frequency: Dict[str, int]
    session_patterns: Dict[str, Any]
    conversion_propensity: float
    churn_risk: float
    last_updated: datetime


@dataclass
class SegmentAnalysis:
    """分群分析结果"""
    segment_type: UserSegmentType
    total_users: int
    segments: List[UserSegment]
    insights: List[str]
    recommendations: List[str]
    analysis_date: datetime


@dataclass
class BehaviorInsight:
    """行为洞察"""
    insight_id: str
    title: str
    description: str
    affected_segments: List[str]
    impact_level: str  # high, medium, low
    actionable: bool
    recommendations: List[str]
    created_at: datetime


class UserSegmentAnalyzer:
    """
    用户分群分析器
    负责用户分群和行为分析
    """
    
    def __init__(self):
        self.redis_client = None
        self.analysis_interval = 3600  # 1小时分析一次
        self.running = False
        self.analysis_task = None
        
    async def start_analysis(self):
        """开始用户分群分析"""
        if self.running:
            return
        
        self.running = True
        self.redis_client = get_redis_client()
        self.analysis_task = asyncio.create_task(self._analysis_loop())
        logger.info("User segment analysis started")
    
    async def stop_analysis(self):
        """停止用户分群分析"""
        self.running = False
        if self.analysis_task:
            self.analysis_task.cancel()
            try:
                await self.analysis_task
            except asyncio.CancelledError:
                pass
        logger.info("User segment analysis stopped")
    
    async def _analysis_loop(self):
        """分析循环"""
        while self.running:
            try:
                await self._update_user_segments()
                await self._analyze_behavior_patterns()
                await asyncio.sleep(self.analysis_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in user segment analysis: {e}")
                await asyncio.sleep(300)
    
    async def analyze_user_segments(
        self, 
        segment_type: UserSegmentType,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> SegmentAnalysis:
        """
        分析用户分群
        
        Args:
            segment_type: 分群类型
            start_date: 开始日期
            end_date: 结束日期
        """
        if start_date is None:
            start_date = datetime.now() - timedelta(days=30)
        if end_date is None:
            end_date = datetime.now()
        
        try:
            # 获取总用户数
            total_users = await self._get_total_users(start_date, end_date)
            
            # 根据分群类型进行分析
            if segment_type == UserSegmentType.ACTIVITY_LEVEL:
                segments = await self._analyze_activity_segments(start_date, end_date)
            elif segment_type == UserSegmentType.ENGAGEMENT:
                segments = await self._analyze_engagement_segments(start_date, end_date)
            elif segment_type == UserSegmentType.LIFECYCLE:
                segments = await self._analyze_lifecycle_segments(start_date, end_date)
            elif segment_type == UserSegmentType.BEHAVIOR_PATTERN:
                segments = await self._analyze_behavior_pattern_segments(start_date, end_date)
            elif segment_type == UserSegmentType.VALUE_BASED:
                segments = await self._analyze_value_based_segments(start_date, end_date)
            elif segment_type == UserSegmentType.FEATURE_ADOPTION:
                segments = await self._analyze_feature_adoption_segments(start_date, end_date)
            else:
                segments = []
            
            # 生成洞察和建议
            insights = await self._generate_segment_insights(segment_type, segments)
            recommendations = await self._generate_segment_recommendations(segment_type, segments)
            
            return SegmentAnalysis(
                segment_type=segment_type,
                total_users=total_users,
                segments=segments,
                insights=insights,
                recommendations=recommendations,
                analysis_date=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error analyzing user segments {segment_type.value}: {e}")
            raise
    
    async def get_user_behavior_profile(self, user_id: str) -> Optional[UserBehaviorProfile]:
        """
        获取用户行为画像
        
        Args:
            user_id: 用户ID
        """
        try:
            # 从缓存获取或重新计算
            cache_key = f"user_profile:{user_id}"
            cached_profile = await self.redis_client.get(cache_key)
            
            if cached_profile:
                profile_data = json.loads(cached_profile)
                return UserBehaviorProfile(
                    user_id=profile_data["user_id"],
                    activity_level=ActivityLevel(profile_data["activity_level"]),
                    engagement_level=EngagementLevel(profile_data["engagement_level"]),
                    lifecycle_stage=LifecycleStage(profile_data["lifecycle_stage"]),
                    behavior_pattern=BehaviorPattern(profile_data["behavior_pattern"]),
                    preferred_features=profile_data["preferred_features"],
                    usage_frequency=profile_data["usage_frequency"],
                    session_patterns=profile_data["session_patterns"],
                    conversion_propensity=profile_data["conversion_propensity"],
                    churn_risk=profile_data["churn_risk"],
                    last_updated=datetime.fromisoformat(profile_data["last_updated"])
                )
            
            # 计算用户行为画像
            profile = await self._calculate_user_behavior_profile(user_id)
            
            if profile:
                # 缓存画像数据
                await self.redis_client.setex(
                    cache_key,
                    3600,  # 1小时过期
                    json.dumps(asdict(profile), default=str)
                )
            
            return profile
            
        except Exception as e:
            logger.error(f"Error getting user behavior profile for {user_id}: {e}")
            return None
    
    async def get_behavior_insights(
        self, 
        segment_types: List[UserSegmentType] = None
    ) -> List[BehaviorInsight]:
        """
        获取行为洞察
        
        Args:
            segment_types: 分群类型列表
        """
        if segment_types is None:
            segment_types = list(UserSegmentType)
        
        try:
            insights = []
            
            for segment_type in segment_types:
                segment_insights = await self._generate_behavior_insights(segment_type)
                insights.extend(segment_insights)
            
            # 按影响程度排序
            insights.sort(key=lambda x: {"high": 3, "medium": 2, "low": 1}.get(x.impact_level, 0), reverse=True)
            
            return insights[:20]  # 返回前20个洞察
            
        except Exception as e:
            logger.error(f"Error getting behavior insights: {e}")
            return []
    
    async def _update_user_segments(self):
        """更新用户分群数据"""
        try:
            for segment_type in UserSegmentType:
                analysis = await self.analyze_user_segments(segment_type)
                
                # 缓存分析结果
                cache_key = f"segment_analysis:{segment_type.value}"
                await self.redis_client.setex(
                    cache_key,
                    7200,  # 2小时过期
                    json.dumps(asdict(analysis), default=str)
                )
                
                logger.debug(f"Updated user segments for {segment_type.value}")
                
        except Exception as e:
            logger.error(f"Error updating user segments: {e}")
    
    async def _analyze_behavior_patterns(self):
        """分析行为模式"""
        try:
            # 这里可以实现行为模式分析逻辑
            pass
        except Exception as e:
            logger.error(f"Error analyzing behavior patterns: {e}")
    
    async def _analyze_activity_segments(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[UserSegment]:
        """分析活跃度分群"""
        segments = []
        
        try:
            # 获取用户活跃度数据
            activity_data = await self._get_user_activity_data(start_date, end_date)
            
            # 定义活跃度分群标准
            segment_criteria = {
                ActivityLevel.POWER_USER: {"min_days": 25, "min_sessions": 50},
                ActivityLevel.ACTIVE_USER: {"min_days": 15, "min_sessions": 20},
                ActivityLevel.MODERATE_USER: {"min_days": 7, "min_sessions": 5},
                ActivityLevel.LIGHT_USER: {"min_days": 1, "min_sessions": 1},
                ActivityLevel.DORMANT_USER: {"min_days": 0, "min_sessions": 0, "last_login_days": 7},
                ActivityLevel.CHURNED_USER: {"min_days": 0, "min_sessions": 0, "last_login_days": 30}
            }
            
            for activity_level, criteria in segment_criteria.items():
                segment_users = self._filter_users_by_activity(activity_data, criteria)
                user_count = len(segment_users)
                
                if user_count > 0:
                    segments.append(UserSegment(
                        segment_id=f"activity_{activity_level.value}",
                        segment_type=UserSegmentType.ACTIVITY_LEVEL,
                        segment_name=activity_level.value.replace("_", " ").title(),
                        description=self._get_activity_level_description(activity_level),
                        user_count=user_count,
                        percentage=user_count / len(activity_data) * 100 if activity_data else 0,
                        criteria=criteria,
                        characteristics=self._get_activity_level_characteristics(activity_level),
                        created_at=datetime.now()
                    ))
            
        except Exception as e:
            logger.error(f"Error analyzing activity segments: {e}")
        
        return segments
    
    async def _analyze_engagement_segments(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[UserSegment]:
        """分析参与度分群"""
        segments = []
        
        try:
            # 获取用户参与度数据
            engagement_data = await self._get_user_engagement_data(start_date, end_date)
            
            # 定义参与度分群标准
            segment_criteria = {
                EngagementLevel.HIGHLY_ENGAGED: {"min_actions": 100, "min_features": 5},
                EngagementLevel.ENGAGED: {"min_actions": 50, "min_features": 3},
                EngagementLevel.LOW_ENGAGED: {"min_actions": 10, "min_features": 1},
                EngagementLevel.NOT_ENGAGED: {"min_actions": 0, "min_features": 0}
            }
            
            for engagement_level, criteria in segment_criteria.items():
                segment_users = self._filter_users_by_engagement(engagement_data, criteria)
                user_count = len(segment_users)
                
                if user_count > 0:
                    segments.append(UserSegment(
                        segment_id=f"engagement_{engagement_level.value}",
                        segment_type=UserSegmentType.ENGAGEMENT,
                        segment_name=engagement_level.value.replace("_", " ").title(),
                        description=self._get_engagement_level_description(engagement_level),
                        user_count=user_count,
                        percentage=user_count / len(engagement_data) * 100 if engagement_data else 0,
                        criteria=criteria,
                        characteristics=self._get_engagement_level_characteristics(engagement_level),
                        created_at=datetime.now()
                    ))
            
        except Exception as e:
            logger.error(f"Error analyzing engagement segments: {e}")
        
        return segments
    
    async def _analyze_lifecycle_segments(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[UserSegment]:
        """分析生命周期分群"""
        segments = []
        
        try:
            # 获取用户生命周期数据
            lifecycle_data = await self._get_user_lifecycle_data(start_date, end_date)
            
            # 定义生命周期分群标准
            segment_criteria = {
                LifecycleStage.NEW_USER: {"max_age_days": 7},
                LifecycleStage.ONBOARDING: {"min_age_days": 7, "max_age_days": 30, "min_actions": 5},
                LifecycleStage.ACTIVE_USER: {"min_age_days": 30, "last_login_days": 7, "min_actions": 20},
                LifecycleStage.LOYAL_USER: {"min_age_days": 90, "last_login_days": 3, "min_actions": 100},
                LifecycleStage.AT_RISK: {"last_login_days": 14, "min_age_days": 30},
                LifecycleStage.CHURNED: {"last_login_days": 30}
            }
            
            for lifecycle_stage, criteria in segment_criteria.items():
                segment_users = self._filter_users_by_lifecycle(lifecycle_data, criteria)
                user_count = len(segment_users)
                
                if user_count > 0:
                    segments.append(UserSegment(
                        segment_id=f"lifecycle_{lifecycle_stage.value}",
                        segment_type=UserSegmentType.LIFECYCLE,
                        segment_name=lifecycle_stage.value.replace("_", " ").title(),
                        description=self._get_lifecycle_stage_description(lifecycle_stage),
                        user_count=user_count,
                        percentage=user_count / len(lifecycle_data) * 100 if lifecycle_data else 0,
                        criteria=criteria,
                        characteristics=self._get_lifecycle_stage_characteristics(lifecycle_stage),
                        created_at=datetime.now()
                    ))
            
        except Exception as e:
            logger.error(f"Error analyzing lifecycle segments: {e}")
        
        return segments
    
    async def _analyze_behavior_pattern_segments(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[UserSegment]:
        """分析行为模式分群"""
        segments = []
        
        try:
            # 获取用户行为模式数据
            behavior_data = await self._get_user_behavior_pattern_data(start_date, end_date)
            
            # 定义行为模式分群标准
            segment_criteria = {
                BehaviorPattern.RESEARCH_FOCUSED: {"min_research_actions": 10, "research_ratio": 0.6},
                BehaviorPattern.QUICK_CHAT: {"min_chat_actions": 20, "chat_ratio": 0.7},
                BehaviorPattern.POWER_SEARCHER: {"min_search_actions": 30, "search_ratio": 0.5},
                BehaviorPattern.SOCIAL_SHARER: {"min_share_actions": 5, "share_ratio": 0.3},
                BehaviorPattern.REPORT_GENERATOR: {"min_report_actions": 5, "report_ratio": 0.4},
                BehaviorPattern.EXPLORER: {"feature_diversity": 4, "min_actions": 15}
            }
            
            for behavior_pattern, criteria in segment_criteria.items():
                segment_users = self._filter_users_by_behavior_pattern(behavior_data, criteria)
                user_count = len(segment_users)
                
                if user_count > 0:
                    segments.append(UserSegment(
                        segment_id=f"behavior_{behavior_pattern.value}",
                        segment_type=UserSegmentType.BEHAVIOR_PATTERN,
                        segment_name=behavior_pattern.value.replace("_", " ").title(),
                        description=self._get_behavior_pattern_description(behavior_pattern),
                        user_count=user_count,
                        percentage=user_count / len(behavior_data) * 100 if behavior_data else 0,
                        criteria=criteria,
                        characteristics=self._get_behavior_pattern_characteristics(behavior_pattern),
                        created_at=datetime.now()
                    ))
            
        except Exception as e:
            logger.error(f"Error analyzing behavior pattern segments: {e}")
        
        return segments
    
    async def _analyze_value_based_segments(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[UserSegment]:
        """分析价值分群"""
        segments = []
        
        try:
            # 获取用户价值数据
            value_data = await self._get_user_value_data(start_date, end_date)
            
            # 定义价值分群标准
            segment_criteria = {
                "high_value": {"min_conversion_value": 50, "min_sessions": 20},
                "medium_value": {"min_conversion_value": 20, "min_sessions": 10},
                "low_value": {"min_conversion_value": 5, "min_sessions": 3},
                "no_value": {"min_conversion_value": 0, "min_sessions": 0}
            }
            
            for value_level, criteria in segment_criteria.items():
                segment_users = self._filter_users_by_value(value_data, criteria)
                user_count = len(segment_users)
                
                if user_count > 0:
                    segments.append(UserSegment(
                        segment_id=f"value_{value_level}",
                        segment_type=UserSegmentType.VALUE_BASED,
                        segment_name=value_level.replace("_", " ").title(),
                        description=f"用户基于转化价值的{value_level}分群",
                        user_count=user_count,
                        percentage=user_count / len(value_data) * 100 if value_data else 0,
                        criteria=criteria,
                        characteristics=[f"转化价值范围: {criteria.get('min_conversion_value', 0)}+"],
                        created_at=datetime.now()
                    ))
            
        except Exception as e:
            logger.error(f"Error analyzing value based segments: {e}")
        
        return segments
    
    async def _analyze_feature_adoption_segments(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[UserSegment]:
        """分析功能采用分群"""
        segments = []
        
        try:
            # 获取功能采用数据
            adoption_data = await self._get_feature_adoption_data(start_date, end_date)
            
            # 定义功能采用分群标准
            segment_criteria = {
                "early_adopter": {"feature_count": 5, "adoption_speed": "fast"},
                "mainstream_user": {"feature_count": 3, "adoption_speed": "normal"},
                "late_adopter": {"feature_count": 1, "adoption_speed": "slow"},
                "non_adopter": {"feature_count": 0}
            }
            
            for adoption_level, criteria in segment_criteria.items():
                segment_users = self._filter_users_by_feature_adoption(adoption_data, criteria)
                user_count = len(segment_users)
                
                if user_count > 0:
                    segments.append(UserSegment(
                        segment_id=f"adoption_{adoption_level}",
                        segment_type=UserSegmentType.FEATURE_ADOPTION,
                        segment_name=adoption_level.replace("_", " ").title(),
                        description=f"用户基于功能采用的{adoption_level}分群",
                        user_count=user_count,
                        percentage=user_count / len(adoption_data) * 100 if adoption_data else 0,
                        criteria=criteria,
                        characteristics=[f"采用功能数: {criteria.get('feature_count', 0)}+"],
                        created_at=datetime.now()
                    ))
            
        except Exception as e:
            logger.error(f"Error analyzing feature adoption segments: {e}")
        
        return segments
    
    async def _calculate_user_behavior_profile(self, user_id: str) -> Optional[UserBehaviorProfile]:
        """计算用户行为画像"""
        try:
            # 获取用户行为数据
            user_data = await self._get_user_behavior_data(user_id)
            
            if not user_data:
                return None
            
            # 分析活跃度
            activity_level = self._determine_activity_level(user_data)
            
            # 分析参与度
            engagement_level = self._determine_engagement_level(user_data)
            
            # 分析生命周期
            lifecycle_stage = self._determine_lifecycle_stage(user_data)
            
            # 分析行为模式
            behavior_pattern = self._determine_behavior_pattern(user_data)
            
            # 分析偏好功能
            preferred_features = self._determine_preferred_features(user_data)
            
            # 计算使用频率
            usage_frequency = self._calculate_usage_frequency(user_data)
            
            # 分析会话模式
            session_patterns = self._analyze_session_patterns(user_data)
            
            # 计算转化倾向
            conversion_propensity = self._calculate_conversion_propensity(user_data)
            
            # 计算流失风险
            churn_risk = self._calculate_churn_risk(user_data)
            
            return UserBehaviorProfile(
                user_id=user_id,
                activity_level=activity_level,
                engagement_level=engagement_level,
                lifecycle_stage=lifecycle_stage,
                behavior_pattern=behavior_pattern,
                preferred_features=preferred_features,
                usage_frequency=usage_frequency,
                session_patterns=session_patterns,
                conversion_propensity=conversion_propensity,
                churn_risk=churn_risk,
                last_updated=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error calculating user behavior profile for {user_id}: {e}")
            return None
    
    # 以下是辅助方法（模拟实现）
    
    async def _get_total_users(self, start_date: datetime, end_date: datetime) -> int:
        """获取总用户数"""
        try:
            async with get_db_session() as session:
                from sqlalchemy import func
                result = await session.execute(
                    func.count(User.id).filter(
                        User.created_at.between(start_date, end_date)
                    )
                )
                return result.scalar() or 0
        except Exception as e:
            logger.error(f"Error getting total users: {e}")
            return 1000  # 返回模拟数据
    
    async def _get_user_activity_data(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """获取用户活跃度数据"""
        # 模拟数据
        return {
            f"user_{i}": {
                "active_days": np.random.randint(0, 30),
                "total_sessions": np.random.randint(0, 100),
                "last_login_days": np.random.randint(0, 60)
            }
            for i in range(1000)
        }
    
    async def _get_user_engagement_data(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """获取用户参与度数据"""
        return {
            f"user_{i}": {
                "total_actions": np.random.randint(0, 200),
                "unique_features": np.random.randint(0, 6),
                "session_duration": np.random.randint(0, 3600)
            }
            for i in range(1000)
        }
    
    async def _get_user_lifecycle_data(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """获取用户生命周期数据"""
        return {
            f"user_{i}": {
                "account_age_days": np.random.randint(0, 365),
                "last_login_days": np.random.randint(0, 90),
                "total_actions": np.random.randint(0, 200)
            }
            for i in range(1000)
        }
    
    async def _get_user_behavior_pattern_data(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """获取用户行为模式数据"""
        return {
            f"user_{i}": {
                "search_actions": np.random.randint(0, 50),
                "chat_actions": np.random.randint(0, 100),
                "research_actions": np.random.randint(0, 30),
                "share_actions": np.random.randint(0, 10),
                "report_actions": np.random.randint(0, 15)
            }
            for i in range(1000)
        }
    
    async def _get_user_value_data(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """获取用户价值数据"""
        return {
            f"user_{i}": {
                "conversion_value": np.random.uniform(0, 100),
                "total_sessions": np.random.randint(0, 50),
                "premium_features": np.random.randint(0, 3)
            }
            for i in range(1000)
        }
    
    async def _get_feature_adoption_data(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """获取功能采用数据"""
        return {
            f"user_{i}": {
                "adopted_features": np.random.randint(0, 6),
                "adoption_speed": np.random.choice(["fast", "normal", "slow"]),
                "feature_usage": {
                    "search": np.random.randint(0, 50),
                    "chat": np.random.randint(0, 100),
                    "research": np.random.randint(0, 30),
                    "reports": np.random.randint(0, 15),
                    "share": np.random.randint(0, 10)
                }
            }
            for i in range(1000)
        }
    
    async def _get_user_behavior_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户行为数据"""
        # 模拟用户行为数据
        return {
            "active_days": np.random.randint(0, 30),
            "total_sessions": np.random.randint(0, 100),
            "last_login_days": np.random.randint(0, 30),
            "total_actions": np.random.randint(0, 200),
            "unique_features": np.random.randint(0, 6),
            "search_actions": np.random.randint(0, 50),
            "chat_actions": np.random.randint(0, 100),
            "research_actions": np.random.randint(0, 30),
            "account_age_days": np.random.randint(0, 365),
            "session_duration": np.random.randint(0, 3600)
        }
    
    def _filter_users_by_activity(self, activity_data: Dict[str, Any], criteria: Dict[str, Any]) -> List[str]:
        """根据活跃度筛选用户"""
        filtered_users = []
        
        for user_id, data in activity_data.items():
            if (data["active_days"] >= criteria.get("min_days", 0) and 
                data["total_sessions"] >= criteria.get("min_sessions", 0)):
                
                # 检查最后登录时间
                if "last_login_days" in criteria:
                    if data["last_login_days"] <= criteria["last_login_days"]:
                        filtered_users.append(user_id)
                else:
                    filtered_users.append(user_id)
        
        return filtered_users
    
    def _filter_users_by_engagement(self, engagement_data: Dict[str, Any], criteria: Dict[str, Any]) -> List[str]:
        """根据参与度筛选用户"""
        filtered_users = []
        
        for user_id, data in engagement_data.items():
            if (data["total_actions"] >= criteria.get("min_actions", 0) and 
                data["unique_features"] >= criteria.get("min_features", 0)):
                filtered_users.append(user_id)
        
        return filtered_users
    
    def _filter_users_by_lifecycle(self, lifecycle_data: Dict[str, Any], criteria: Dict[str, Any]) -> List[str]:
        """根据生命周期筛选用户"""
        filtered_users = []
        
        for user_id, data in lifecycle_data.items():
            age_ok = True
            login_ok = True
            actions_ok = True
            
            # 检查账户年龄
            if "min_age_days" in criteria and data["account_age_days"] < criteria["min_age_days"]:
                age_ok = False
            if "max_age_days" in criteria and data["account_age_days"] > criteria["max_age_days"]:
                age_ok = False
            
            # 检查最后登录时间
            if "last_login_days" in criteria and data["last_login_days"] > criteria["last_login_days"]:
                login_ok = False
            
            # 检查操作数量
            if "min_actions" in criteria and data["total_actions"] < criteria["min_actions"]:
                actions_ok = False
            
            if age_ok and login_ok and actions_ok:
                filtered_users.append(user_id)
        
        return filtered_users
    
    def _filter_users_by_behavior_pattern(self, behavior_data: Dict[str, Any], criteria: Dict[str, Any]) -> List[str]:
        """根据行为模式筛选用户"""
        filtered_users = []
        
        for user_id, data in behavior_data.items():
            total_actions = sum(data.values())
            
            if total_actions == 0:
                if criteria.get("min_actions", 0) == 0:
                    filtered_users.append(user_id)
                continue
            
            # 检查特定行为比例
            if "research_ratio" in criteria:
                research_ratio = data.get("research_actions", 0) / total_actions
                if (data.get("research_actions", 0) >= criteria.get("min_research_actions", 0) and
                    research_ratio >= criteria["research_ratio"]):
                    filtered_users.append(user_id)
            
            elif "chat_ratio" in criteria:
                chat_ratio = data.get("chat_actions", 0) / total_actions
                if (data.get("chat_actions", 0) >= criteria.get("min_chat_actions", 0) and
                    chat_ratio >= criteria["chat_ratio"]):
                    filtered_users.append(user_id)
            
            elif "search_ratio" in criteria:
                search_ratio = data.get("search_actions", 0) / total_actions
                if (data.get("search_actions", 0) >= criteria.get("min_search_actions", 0) and
                    search_ratio >= criteria["search_ratio"]):
                    filtered_users.append(user_id)
            
            elif "feature_diversity" in criteria:
                feature_count = len([v for v in data.values() if v > 0])
                if (feature_count >= criteria["feature_diversity"] and
                    total_actions >= criteria.get("min_actions", 0)):
                    filtered_users.append(user_id)
        
        return filtered_users
    
    def _filter_users_by_value(self, value_data: Dict[str, Any], criteria: Dict[str, Any]) -> List[str]:
        """根据价值筛选用户"""
        filtered_users = []
        
        for user_id, data in value_data.items():
            if (data["conversion_value"] >= criteria.get("min_conversion_value", 0) and 
                data["total_sessions"] >= criteria.get("min_sessions", 0)):
                filtered_users.append(user_id)
        
        return filtered_users
    
    def _filter_users_by_feature_adoption(self, adoption_data: Dict[str, Any], criteria: Dict[str, Any]) -> List[str]:
        """根据功能采用筛选用户"""
        filtered_users = []
        
        for user_id, data in adoption_data.items():
            if data["adopted_features"] >= criteria.get("feature_count", 0):
                if "adoption_speed" not in criteria or data["adoption_speed"] == criteria["adoption_speed"]:
                    filtered_users.append(user_id)
        
        return filtered_users
    
    def _determine_activity_level(self, user_data: Dict[str, Any]) -> ActivityLevel:
        """确定活跃度等级"""
        active_days = user_data.get("active_days", 0)
        sessions = user_data.get("total_sessions", 0)
        last_login = user_data.get("last_login_days", 0)
        
        if active_days >= 25 and sessions >= 50:
            return ActivityLevel.POWER_USER
        elif active_days >= 15 and sessions >= 20:
            return ActivityLevel.ACTIVE_USER
        elif active_days >= 7 and sessions >= 5:
            return ActivityLevel.MODERATE_USER
        elif active_days >= 1 and sessions >= 1:
            return ActivityLevel.LIGHT_USER
        elif last_login <= 7:
            return ActivityLevel.DORMANT_USER
        else:
            return ActivityLevel.CHURNED_USER
    
    def _determine_engagement_level(self, user_data: Dict[str, Any]) -> EngagementLevel:
        """确定参与度等级"""
        actions = user_data.get("total_actions", 0)
        features = user_data.get("unique_features", 0)
        
        if actions >= 100 and features >= 5:
            return EngagementLevel.HIGHLY_ENGAGED
        elif actions >= 50 and features >= 3:
            return EngagementLevel.ENGAGED
        elif actions >= 10 and features >= 1:
            return EngagementLevel.LOW_ENGAGED
        else:
            return EngagementLevel.NOT_ENGAGED
    
    def _determine_lifecycle_stage(self, user_data: Dict[str, Any]) -> LifecycleStage:
        """确定生命周期阶段"""
        age = user_data.get("account_age_days", 0)
        last_login = user_data.get("last_login_days", 0)
        actions = user_data.get("total_actions", 0)
        
        if age <= 7:
            return LifecycleStage.NEW_USER
        elif age <= 30 and actions >= 5:
            return LifecycleStage.ONBOARDING
        elif age >= 30 and last_login <= 7 and actions >= 20:
            return LifecycleStage.ACTIVE_USER
        elif age >= 90 and last_login <= 3 and actions >= 100:
            return LifecycleStage.LOYAL_USER
        elif last_login >= 30:
            return LifecycleStage.CHURNED
        elif last_login >= 14 and age >= 30:
            return LifecycleStage.AT_RISK
        else:
            return LifecycleStage.ACTIVE_USER
    
    def _determine_behavior_pattern(self, user_data: Dict[str, Any]) -> BehaviorPattern:
        """确定行为模式"""
        search = user_data.get("search_actions", 0)
        chat = user_data.get("chat_actions", 0)
        research = user_data.get("research_actions", 0)
        
        total = search + chat + research
        
        if total == 0:
            return BehaviorPattern.EXPLORER
        
        search_ratio = search / total
        chat_ratio = chat / total
        research_ratio = research / total
        
        if research_ratio >= 0.6:
            return BehaviorPattern.RESEARCH_FOCUSED
        elif chat_ratio >= 0.7:
            return BehaviorPattern.QUICK_CHAT
        elif search_ratio >= 0.5:
            return BehaviorPattern.POWER_SEARCHER
        else:
            return BehaviorPattern.EXPLORER
    
    def _determine_preferred_features(self, user_data: Dict[str, Any]) -> List[str]:
        """确定偏好功能"""
        features = []
        
        if user_data.get("search_actions", 0) > 10:
            features.append("搜索")
        if user_data.get("chat_actions", 0) > 20:
            features.append("聊天")
        if user_data.get("research_actions", 0) > 5:
            features.append("研究")
        
        return features[:3]  # 返回前3个偏好功能
    
    def _calculate_usage_frequency(self, user_data: Dict[str, Any]) -> Dict[str, int]:
        """计算使用频率"""
        return {
            "daily": user_data.get("total_sessions", 0) // max(user_data.get("active_days", 1), 1),
            "weekly": user_data.get("total_sessions", 0) // max(user_data.get("active_days", 1) // 7, 1),
            "monthly": user_data.get("total_sessions", 0) // max(user_data.get("active_days", 1) // 30, 1)
        }
    
    def _analyze_session_patterns(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析会话模式"""
        return {
            "avg_duration": user_data.get("session_duration", 0),
            "peak_hour": np.random.randint(9, 21),  # 模拟峰值时间
            "preferred_days": np.random.choice(["工作日", "周末"], p=[0.7, 0.3])
        }
    
    def _calculate_conversion_propensity(self, user_data: Dict[str, Any]) -> float:
        """计算转化倾向"""
        # 基于用户行为数据计算转化倾向
        actions = user_data.get("total_actions", 0)
        features = user_data.get("unique_features", 0)
        
        base_propensity = 0.1
        action_boost = min(actions / 100, 0.3)
        feature_boost = min(features / 5, 0.2)
        
        return min(base_propensity + action_boost + feature_boost, 0.9)
    
    def _calculate_churn_risk(self, user_data: Dict[str, Any]) -> float:
        """计算流失风险"""
        last_login = user_data.get("last_login_days", 0)
        actions = user_data.get("total_actions", 0)
        
        base_risk = 0.1
        login_risk = min(last_login / 30, 0.5)
        action_risk = max(0, (20 - actions) / 100)
        
        return min(base_risk + login_risk + action_risk, 0.9)
    
    # 描述和特征方法
    
    def _get_activity_level_description(self, level: ActivityLevel) -> str:
        """获取活跃度等级描述"""
        descriptions = {
            ActivityLevel.POWER_USER: "每天活跃，使用频率极高的重度用户",
            ActivityLevel.ACTIVE_USER: "每周多次活跃，使用频率较高的活跃用户",
            ActivityLevel.MODERATE_USER: "每周活跃，使用频率中等的中度用户",
            ActivityLevel.LIGHT_USER: "偶尔活跃，使用频率较低的轻度用户",
            ActivityLevel.DORMANT_USER: "曾经活跃但近期不活跃的休眠用户",
            ActivityLevel.CHURNED_USER: "长期不活跃的流失用户"
        }
        return descriptions.get(level, "")
    
    def _get_activity_level_characteristics(self, level: ActivityLevel) -> List[str]:
        """获取活跃度等级特征"""
        characteristics = {
            ActivityLevel.POWER_USER: ["高粘性", "高价值", "品牌忠诚"],
            ActivityLevel.ACTIVE_USER: ["稳定使用", "良好体验", "潜在价值"],
            ActivityLevel.MODERATE_USER: ["规律使用", "提升空间", "需要激励"],
            ActivityLevel.LIGHT_USER: ["低频使用", "功能探索", "需要引导"],
            ActivityLevel.DORMANT_USER: ["流失风险", "重新激活", "体验问题"],
            ActivityLevel.CHURNED_USER: ["已流失", "挽回困难", "需要分析"]
        }
        return characteristics.get(level, [])
    
    def _get_engagement_level_description(self, level: EngagementLevel) -> str:
        """获取参与度等级描述"""
        descriptions = {
            EngagementLevel.HIGHLY_ENGAGED: "深度参与多种功能，互动频繁的高参与用户",
            EngagementLevel.ENGAGED: "积极参与核心功能，互动良好的参与用户",
            EngagementLevel.LOW_ENGAGED: "偶尔使用基础功能，互动较少的低参与用户",
            EngagementLevel.NOT_ENGAGED: "几乎不使用功能，无互动参与的用户"
        }
        return descriptions.get(level, "")
    
    def _get_engagement_level_characteristics(self, level: EngagementLevel) -> List[str]:
        """获取参与度等级特征"""
        characteristics = {
            EngagementLevel.HIGHLY_ENGAGED: ["功能探索", "社区活跃", "内容创造"],
            EngagementLevel.ENGAGED: ["核心使用", "稳定互动", "价值认可"],
            EngagementLevel.LOW_ENGAGED: ["基础使用", "被动互动", "价值感知低"],
            EngagementLevel.NOT_ENGAGED: ["功能未激活", "无互动", "流失风险高"]
        }
        return characteristics.get(level, [])
    
    def _get_lifecycle_stage_description(self, stage: LifecycleStage) -> str:
        """获取生命周期阶段描述"""
        descriptions = {
            LifecycleStage.NEW_USER: "刚注册的新用户，处于产品探索期",
            LifecycleStage.ONBOARDING: "完成注册但仍在学习产品功能",
            LifecycleStage.ACTIVE_USER: "熟悉产品并稳定使用的活跃用户",
            LifecycleStage.LOYAL_USER: "长期使用且高度忠诚的核心用户",
            LifecycleStage.AT_RISK: "使用频率下降，有流失风险的用户",
            LifecycleStage.CHURNED: "已停止使用产品的流失用户"
        }
        return descriptions.get(stage, "")
    
    def _get_lifecycle_stage_characteristics(self, stage: LifecycleStage) -> List[str]:
        """获取生命周期阶段特征"""
        characteristics = {
            LifecycleStage.NEW_USER: ["学习期", "高流失风险", "需要引导"],
            LifecycleStage.ONBOARDING: ["适应期", "功能探索", "体验关键期"],
            LifecycleStage.ACTIVE_USER: ["稳定期", "价值实现", "成长潜力"],
            LifecycleStage.LOYAL_USER: ["忠诚期", "高价值", "品牌传播"],
            LifecycleStage.AT_RISK: ["衰退期", "体验问题", "需要干预"],
            LifecycleStage.CHURNED: ["流失期", "挽回困难", "需要分析"]
        }
        return characteristics.get(stage, [])
    
    def _get_behavior_pattern_description(self, pattern: BehaviorPattern) -> str:
        """获取行为模式描述"""
        descriptions = {
            BehaviorPattern.RESEARCH_FOCUSED: "专注于深度研究功能，喜欢详细分析的用户",
            BehaviorPattern.QUICK_CHAT: "偏好快速聊天交互，追求即时反馈的用户",
            BehaviorPattern.POWER_SEARCHER: "频繁使用搜索功能，信息获取需求强的用户",
            BehaviorPattern.SOCIAL_SHARER: "喜欢分享内容，社交属性强的用户",
            BehaviorPattern.REPORT_GENERATOR: "经常生成报告，注重结果输出的用户",
            BehaviorPattern.EXPLORER: "喜欢尝试各种功能，探索性强的用户"
        }
        return descriptions.get(pattern, "")
    
    def _get_behavior_pattern_characteristics(self, pattern: BehaviorPattern) -> List[str]:
        """获取行为模式特征"""
        characteristics = {
            BehaviorPattern.RESEARCH_FOCUSED: ["深度思考", "专业需求", "高质量输出"],
            BehaviorPattern.QUICK_CHAT: ["效率导向", "即时满足", "轻量使用"],
            BehaviorPattern.POWER_SEARCHER: ["信息驱动", "比较分析", "决策支持"],
            BehaviorPattern.SOCIAL_SHARER: ["社交活跃", "影响力", "内容传播"],
            BehaviorPattern.REPORT_GENERATOR: ["结果导向", "专业性强", "商业价值"],
            BehaviorPattern.EXPLORER: ["好奇心强", "功能探索", "潜在价值"]
        }
        return characteristics.get(pattern, [])
    
    async def _generate_segment_insights(
        self, 
        segment_type: UserSegmentType, 
        segments: List[UserSegment]
    ) -> List[str]:
        """生成分群洞察"""
        insights = []
        
        try:
            # 分析分群分布
            if segments:
                largest_segment = max(segments, key=lambda x: x.user_count)
                smallest_segment = min(segments, key=lambda x: x.user_count)
                
                insights.append(f"最大的{segment_type.value}分群是'{largest_segment.segment_name}'，占比{largest_segment.percentage:.1f}%")
                
                if smallest_segment.percentage < 5:
                    insights.append(f"'{smallest_segment.segment_name}'分群占比过小({smallest_segment.percentage:.1f}%)，值得关注")
            
            # 生成特定分群类型的洞察
            if segment_type == UserSegmentType.ACTIVITY_LEVEL:
                dormant_users = next((s for s in segments if "休眠" in s.segment_name or "流失" in s.segment_name), None)
                if dormant_users and dormant_users.percentage > 20:
                    insights.append(f"休眠和流失用户占比过高({dormant_users.percentage:.1f}%)，需要激活策略")
            
            elif segment_type == UserSegmentType.ENGAGEMENT:
                low_engaged = next((s for s in segments if "低参与" in s.segment_name or "无参与" in s.segment_name), None)
                if low_engaged and low_engaged.percentage > 30:
                    insights.append(f"低参与用户比例较高({low_engaged.percentage:.1f}%)，需要提升用户参与度")
            
            elif segment_type == UserSegmentType.LIFECYCLE:
                new_users = next((s for s in segments if "新用户" in s.segment_name), None)
                if new_users and new_users.percentage < 10:
                    insights.append(f"新用户占比偏低({new_users.percentage:.1f}%)，需要加强获客")
            
        except Exception as e:
            logger.error(f"Error generating segment insights: {e}")
        
        return insights
    
    async def _generate_segment_recommendations(
        self, 
        segment_type: UserSegmentType, 
        segments: List[UserSegment]
    ) -> List[str]:
        """生成分群建议"""
        recommendations = []
        
        try:
            # 生成通用建议
            recommendations.append("定期监控分群变化，及时调整运营策略")
            recommendations.append("针对不同分群制定个性化的产品体验和营销策略")
            
            # 生成特定分群类型的建议
            if segment_type == UserSegmentType.ACTIVITY_LEVEL:
                recommendations.append("为重度用户提供高级功能和专属权益")
                recommendations.append("针对休眠用户制定重新激活计划")
                recommendations.append("优化新用户引导流程，提升活跃度")
            
            elif segment_type == UserSegmentType.ENGAGEMENT:
                recommendations.append("设计激励机制提升用户参与度")
                recommendations.append("丰富产品功能，增加用户使用场景")
                recommendations.append("建立用户社区，促进用户互动")
            
            elif segment_type == UserSegmentType.LIFECYCLE:
                recommendations.append("完善新用户引导，降低早期流失")
                recommendations.append("为忠诚用户提供增值服务和奖励")
                recommendations.append("建立流失预警机制，及时干预")
            
            elif segment_type == UserSegmentType.BEHAVIOR_PATTERN:
                recommendations.append("针对不同行为模式优化产品功能")
                recommendations.append("提供个性化的功能推荐和使用引导")
                recommendations.append("分析行为模式变化，预测用户需求")
            
        except Exception as e:
            logger.error(f"Error generating segment recommendations: {e}")
        
        return recommendations
    
    async def _generate_behavior_insights(self, segment_type: UserSegmentType) -> List[BehaviorInsight]:
        """生成行为洞察"""
        insights = []
        
        try:
            # 这里可以实现更复杂的行为洞察生成逻辑
            # 暂时返回模拟数据
            insights.append(BehaviorInsight(
                insight_id=f"behavior_insight_{segment_type.value}",
                title=f"{segment_type.value}行为模式分析",
                description=f"基于{segment_type.value}的用户行为模式显示特定趋势",
                affected_segments=[segment_type.value],
                impact_level="medium",
                actionable=True,
                recommendations=[
                    "深入分析用户行为数据",
                    "制定针对性的优化策略"
                ],
                created_at=datetime.now()
            ))
            
        except Exception as e:
            logger.error(f"Error generating behavior insights: {e}")
        
        return insights


# 全局用户分群分析器实例
user_segment_analyzer = UserSegmentAnalyzer()
