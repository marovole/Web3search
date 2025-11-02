"""
用户行为漏斗分析系统
分析用户在关键业务流程中的转化情况和流失点
"""
import asyncio
import json
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import logging

from app.core.redis_client import get_redis_client
from app.core.database import get_db_session
from app.core.business_metrics import business_metrics_collector
from app.core.business_tracker import tracker
from app.models.user import User
from app.models.conversation import Conversation, Message
from app.models.report import Report
import numpy as np

logger = logging.getLogger(__name__)


class FunnelType(Enum):
    """漏斗类型"""
    USER_ONBOARDING = "user_onboarding"          # 用户引导漏斗
    SEARCH_TO_CHAT = "search_to_chat"            # 搜索到聊天漏斗
    CHAT_TO_RESEARCH = "chat_to_research"        # 聊天到研究漏斗
    RESEARCH_TO_REPORT = "research_to_report"    # 研究到报告漏斗
    REPORT_TO_SHARE = "report_to_share"          # 报告到分享漏斗
    DISCOVERY_TO_USAGE = "discovery_to_usage"    # 发现到使用漏斗


class FunnelStage(Enum):
    """漏斗阶段"""
    # 用户引导漏斗
    VISIT_LANDING = "visit_landing"              # 访问落地页
    SIGNUP_START = "signup_start"                # 开始注册
    SIGNUP_COMPLETE = "signup_complete"          # 完成注册
    FIRST_SEARCH = "first_search"                # 首次搜索
    FIRST_CHAT = "first_chat"                    # 首次聊天
    
    # 搜索到聊天漏斗
    SEARCH_INITIATED = "search_initiated"        # 发起搜索
    SEARCH_RESULTS_VIEWED = "search_results_viewed"  # 查看搜索结果
    CHAT_INITIATED = "chat_initiated"            # 发起聊天
    CHAT_COMPLETED = "chat_completed"            # 完成聊天
    
    # 聊天到研究漏斗
    CHAT_START = "chat_start"                    # 开始聊天
    MULTIPLE_MESSAGES = "multiple_messages"      # 多轮对话
    RESEARCH_REQUEST = "research_request"        # 请求深度研究
    RESEARCH_COMPLETED = "research_completed"    # 完成研究
    
    # 研究到报告漏斗
    RESEARCH_START = "research_start"            # 开始研究
    DATA_COLLECTED = "data_collected"            # 数据收集完成
    REPORT_GENERATED = "report_generated"        # 报告生成完成
    REPORT_SAVED = "report_saved"                # 报告保存
    
    # 报告到分享漏斗
    REPORT_VIEWED = "report_viewed"              # 查看报告
    REPORT_EDITED = "report_edited"              # 编辑报告
    SHARE_INITIATED = "share_initiated"          # 发起分享
    SHARE_COMPLETED = "share_completed"          # 完成分享
    
    # 发现到使用漏斗
    FEATURE_DISCOVERED = "feature_discovered"    # 发现功能
    FEATURE_CLICKED = "feature_clicked"          # 点击功能
    FEATURE_USED = "feature_used"                # 使用功能
    FEATURE_RETURNED = "feature_returned"        # 回访功能


@dataclass
class FunnelStageMetrics:
    """漏斗阶段指标"""
    stage: FunnelStage
    users: int                    # 到达该阶段的用户数
    conversion_rate: float        # 从上一阶段的转化率
    dropoff_rate: float          # 从上一阶段的流失率
    avg_time_to_stage: float     # 平均到达该阶段的时间（秒）
    stage_completion_rate: float # 阶段内完成率


@dataclass
class FunnelAnalysis:
    """漏斗分析结果"""
    funnel_type: FunnelType
    time_period: str
    total_users: int
    stages: List[FunnelStageMetrics]
    overall_conversion_rate: float
    insights: List[str]
    recommendations: List[str]


class FunnelAnalyzer:
    """
    漏斗分析器
    分析用户在关键业务流程中的行为模式
    """
    
    def __init__(self):
        self.redis_client = None
        
    async def initialize(self):
        """初始化分析器"""
        self.redis_client = get_redis_client()
    
    async def analyze_funnel(
        self, 
        funnel_type: FunnelType, 
        start_date: datetime = None,
        end_date: datetime = None,
        user_segment: str = "all"
    ) -> FunnelAnalysis:
        """
        分析指定类型的漏斗
        
        Args:
            funnel_type: 漏斗类型
            start_date: 开始日期
            end_date: 结束日期
            user_segment: 用户分群
        """
        if not self.redis_client:
            await self.initialize()
        
        if start_date is None:
            start_date = datetime.now() - timedelta(days=7)
        if end_date is None:
            end_date = datetime.now()
        
        time_period = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        
        try:
            # 获取漏斗阶段定义
            stages = self._get_funnel_stages(funnel_type)
            
            # 分析每个阶段
            stage_metrics = []
            previous_users = 0
            
            for i, stage in enumerate(stages):
                metrics = await self._analyze_stage(
                    stage, funnel_type, start_date, end_date, user_segment
                )
                
                # 计算转化率和流失率
                if i == 0:
                    metrics.conversion_rate = 1.0  # 第一阶段转化率为100%
                    metrics.dropoff_rate = 0.0
                else:
                    if previous_users > 0:
                        metrics.conversion_rate = metrics.users / previous_users
                        metrics.dropoff_rate = 1.0 - metrics.conversion_rate
                    else:
                        metrics.conversion_rate = 0.0
                        metrics.dropoff_rate = 0.0
                
                stage_metrics.append(metrics)
                previous_users = metrics.users
            
            # 计算整体转化率
            overall_conversion_rate = self._calculate_overall_conversion(stage_metrics)
            
            # 生成洞察和建议
            insights = await self._generate_funnel_insights(funnel_type, stage_metrics)
            recommendations = await self._generate_funnel_recommendations(funnel_type, stage_metrics)
            
            return FunnelAnalysis(
                funnel_type=funnel_type,
                time_period=time_period,
                total_users=stage_metrics[0].users if stage_metrics else 0,
                stages=stage_metrics,
                overall_conversion_rate=overall_conversion_rate,
                insights=insights,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Error analyzing funnel {funnel_type.value}: {e}")
            raise
    
    async def track_funnel_event(
        self, 
        user_id: str, 
        funnel_type: FunnelType, 
        stage: FunnelStage,
        properties: Dict[str, Any] = None
    ):
        """
        追踪漏斗事件
        
        Args:
            user_id: 用户ID
            funnel_type: 漏斗类型
            stage: 漏斗阶段
            properties: 事件属性
        """
        if not self.redis_client:
            await self.initialize()
        
        try:
            event_data = {
                "user_id": user_id,
                "funnel_type": funnel_type.value,
                "stage": stage.value,
                "timestamp": datetime.now().isoformat(),
                "properties": properties or {}
            }
            
            # 存储到Redis
            key = f"funnel_events:{funnel_type.value}:{stage.value}:{datetime.now().strftime('%Y%m%d')}"
            await self.redis_client.hset(key, user_id, json.dumps(event_data))
            await self.redis_client.expire(key, 86400 * 30)  # 30天过期
            
            # 更新用户漏斗状态
            user_funnel_key = f"user_funnel:{user_id}:{funnel_type.value}"
            current_stage = await self.redis_client.get(user_funnel_key)
            
            # 只有当用户进入新阶段时才更新
            if not current_stage or self._compare_stages(stage.value, current_stage.decode()) > 0:
                await self.redis_client.set(user_funnel_key, stage.value, ex=86400 * 7)
            
            logger.debug(f"Tracked funnel event: {user_id} -> {funnel_type.value}:{stage.value}")
            
        except Exception as e:
            logger.error(f"Error tracking funnel event: {e}")
    
    async def get_user_funnel_progress(self, user_id: str, funnel_type: FunnelType) -> Dict[str, Any]:
        """
        获取用户在特定漏斗中的进度
        
        Args:
            user_id: 用户ID
            funnel_type: 漏斗类型
        """
        if not self.redis_client:
            await self.initialize()
        
        try:
            user_funnel_key = f"user_funnel:{user_id}:{funnel_type.value}"
            current_stage = await self.redis_client.get(user_funnel_key)
            
            if not current_stage:
                return {
                    "user_id": user_id,
                    "funnel_type": funnel_type.value,
                    "current_stage": None,
                    "progress_percentage": 0.0,
                    "completed_stages": [],
                    "next_stage": None
                }
            
            stages = self._get_funnel_stages(funnel_type)
            current_stage_value = current_stage.decode()
            
            completed_stages = []
            current_stage_index = -1
            
            for i, stage in enumerate(stages):
                if self._compare_stages(stage.value, current_stage_value) <= 0:
                    completed_stages.append(stage.value)
                    if stage.value == current_stage_value:
                        current_stage_index = i
            
            progress_percentage = (len(completed_stages) / len(stages)) * 100
            next_stage = stages[current_stage_index + 1].value if current_stage_index < len(stages) - 1 else None
            
            return {
                "user_id": user_id,
                "funnel_type": funnel_type.value,
                "current_stage": current_stage_value,
                "progress_percentage": round(progress_percentage, 2),
                "completed_stages": completed_stages,
                "next_stage": next_stage
            }
            
        except Exception as e:
            logger.error(f"Error getting user funnel progress: {e}")
            return {}
    
    def _get_funnel_stages(self, funnel_type: FunnelType) -> List[FunnelStage]:
        """获取漏斗的阶段定义"""
        stage_mapping = {
            FunnelType.USER_ONBOARDING: [
                FunnelStage.VISIT_LANDING,
                FunnelStage.SIGNUP_START,
                FunnelStage.SIGNUP_COMPLETE,
                FunnelStage.FIRST_SEARCH,
                FunnelStage.FIRST_CHAT
            ],
            FunnelType.SEARCH_TO_CHAT: [
                FunnelStage.SEARCH_INITIATED,
                FunnelStage.SEARCH_RESULTS_VIEWED,
                FunnelStage.CHAT_INITIATED,
                FunnelStage.CHAT_COMPLETED
            ],
            FunnelType.CHAT_TO_RESEARCH: [
                FunnelStage.CHAT_START,
                FunnelStage.MULTIPLE_MESSAGES,
                FunnelStage.RESEARCH_REQUEST,
                FunnelStage.RESEARCH_COMPLETED
            ],
            FunnelType.RESEARCH_TO_REPORT: [
                FunnelStage.RESEARCH_START,
                FunnelStage.DATA_COLLECTED,
                FunnelStage.REPORT_GENERATED,
                FunnelStage.REPORT_SAVED
            ],
            FunnelType.REPORT_TO_SHARE: [
                FunnelStage.REPORT_VIEWED,
                FunnelStage.REPORT_EDITED,
                FunnelStage.SHARE_INITIATED,
                FunnelStage.SHARE_COMPLETED
            ],
            FunnelType.DISCOVERY_TO_USAGE: [
                FunnelStage.FEATURE_DISCOVERED,
                FunnelStage.FEATURE_CLICKED,
                FunnelStage.FEATURE_USED,
                FunnelStage.FEATURE_RETURNED
            ]
        }
        
        return stage_mapping.get(funnel_type, [])
    
    async def _analyze_stage(
        self, 
        stage: FunnelStage, 
        funnel_type: FunnelType,
        start_date: datetime,
        end_date: datetime,
        user_segment: str
    ) -> FunnelStageMetrics:
        """分析单个漏斗阶段"""
        
        # 获取到达该阶段的用户数
        users = await self._get_stage_users(stage, funnel_type, start_date, end_date)
        
        # 计算平均到达时间
        avg_time = await self._calculate_avg_time_to_stage(stage, funnel_type, start_date, end_date)
        
        # 计算阶段完成率
        completion_rate = await self._calculate_stage_completion_rate(stage, funnel_type, start_date, end_date)
        
        return FunnelStageMetrics(
            stage=stage,
            users=users,
            conversion_rate=0.0,  # 将在上级函数中计算
            dropoff_rate=0.0,     # 将在上级函数中计算
            avg_time_to_stage=avg_time,
            stage_completion_rate=completion_rate
        )
    
    async def _get_stage_users(
        self, 
        stage: FunnelStage, 
        funnel_type: FunnelType,
        start_date: datetime,
        end_date: datetime
    ) -> int:
        """获取到达特定阶段的用户数"""
        try:
            users = set()
            current_date = start_date
            
            while current_date <= end_date:
                key = f"funnel_events:{funnel_type.value}:{stage.value}:{current_date.strftime('%Y%m%d')}"
                stage_users = await self.redis_client.hkeys(key)
                users.update(stage_users)
                current_date += timedelta(days=1)
            
            return len(users)
            
        except Exception as e:
            logger.error(f"Error getting stage users: {e}")
            return 0
    
    async def _calculate_avg_time_to_stage(
        self, 
        stage: FunnelStage, 
        funnel_type: FunnelType,
        start_date: datetime,
        end_date: datetime
    ) -> float:
        """计算到达阶段的平均时间"""
        # 这里应该基于实际的时间戳数据计算
        # 暂时返回模拟数据
        time_mapping = {
            FunnelStage.VISIT_LANDING: 0.0,
            FunnelStage.SIGNUP_START: 30.0,
            FunnelStage.SIGNUP_COMPLETE: 120.0,
            FunnelStage.FIRST_SEARCH: 300.0,
            FunnelStage.FIRST_CHAT: 600.0,
            FunnelStage.SEARCH_INITIATED: 10.0,
            FunnelStage.SEARCH_RESULTS_VIEWED: 15.0,
            FunnelStage.CHAT_INITIATED: 45.0,
            FunnelStage.CHAT_COMPLETED: 180.0
        }
        
        return time_mapping.get(stage, 60.0)
    
    async def _calculate_stage_completion_rate(
        self, 
        stage: FunnelStage, 
        funnel_type: FunnelType,
        start_date: datetime,
        end_date: datetime
    ) -> float:
        """计算阶段完成率"""
        # 这里应该基于实际的完成事件计算
        # 暂时返回模拟数据
        return np.random.uniform(0.6, 0.95)
    
    def _calculate_overall_conversion(self, stage_metrics: List[FunnelStageMetrics]) -> float:
        """计算整体转化率"""
        if not stage_metrics:
            return 0.0
        
        first_stage_users = stage_metrics[0].users
        last_stage_users = stage_metrics[-1].users
        
        if first_stage_users == 0:
            return 0.0
        
        return last_stage_users / first_stage_users
    
    async def _generate_funnel_insights(
        self, 
        funnel_type: FunnelType, 
        stage_metrics: List[FunnelStageMetrics]
    ) -> List[str]:
        """生成漏斗洞察"""
        insights = []
        
        if not stage_metrics:
            return insights
        
        # 找出最大流失点
        max_dropoff_stage = max(stage_metrics[1:], key=lambda x: x.dropoff_rate)
        if max_dropoff_stage.dropoff_rate > 0.5:
            insights.append(f"最大流失点在 {max_dropoff_stage.stage.value}，流失率 {max_dropoff_stage.dropoff_rate:.1%}")
        
        # 分析整体转化率
        overall_rate = stage_metrics[-1].users / stage_metrics[0].users if stage_metrics[0].users > 0 else 0
        if overall_rate < 0.1:
            insights.append("整体转化率偏低，需要优化用户体验")
        elif overall_rate > 0.5:
            insights.append("整体转化率表现良好")
        
        # 分析时间效率
        slow_stages = [s for s in stage_metrics if s.avg_time_to_stage > 300]
        if slow_stages:
            insights.append(f"以下阶段耗时较长：{', '.join(s.stage.value for s in slow_stages)}")
        
        return insights
    
    async def _generate_funnel_recommendations(
        self, 
        funnel_type: FunnelType, 
        stage_metrics: List[FunnelStageMetrics]
    ) -> List[str]:
        """生成漏斗优化建议"""
        recommendations = []
        
        if not stage_metrics:
            return recommendations
        
        # 针对高流失率的建议
        high_dropoff_stages = [s for s in stage_metrics if s.dropoff_rate > 0.4]
        for stage in high_dropoff_stages:
            if "signup" in stage.stage.value:
                recommendations.append("简化注册流程，减少必填字段")
            elif "search" in stage.stage.value:
                recommendations.append("优化搜索体验，提供更好的搜索建议")
            elif "chat" in stage.stage.value:
                recommendations.append("改善聊天界面，提供更清晰的引导")
            elif "research" in stage.stage.value:
                recommendations.append("简化研究流程，提供模板和示例")
        
        # 针对低完成率的建议
        low_completion_stages = [s for s in stage_metrics if s.stage_completion_rate < 0.7]
        if low_completion_stages:
            recommendations.append("加强用户引导，提供操作提示和帮助文档")
        
        # 通用建议
        recommendations.append("定期监控漏斗数据，及时发现异常")
        recommendations.append("进行A/B测试优化关键转化点")
        
        return recommendations
    
    def _compare_stages(self, stage1: str, stage2: str) -> int:
        """比较两个阶段的顺序，返回1, 0, -1"""
        stage_order = [
            "visit_landing", "signup_start", "signup_complete", "first_search", "first_chat",
            "search_initiated", "search_results_viewed", "chat_initiated", "chat_completed",
            "chat_start", "multiple_messages", "research_request", "research_completed",
            "research_start", "data_collected", "report_generated", "report_saved",
            "report_viewed", "report_edited", "share_initiated", "share_completed",
            "feature_discovered", "feature_clicked", "feature_used", "feature_returned"
        ]
        
        try:
            index1 = stage_order.index(stage1)
            index2 = stage_order.index(stage2)
            
            if index1 > index2:
                return 1
            elif index1 < index2:
                return -1
            else:
                return 0
        except ValueError:
            return 0


# 全局漏斗分析器实例
funnel_analyzer = FunnelAnalyzer()
