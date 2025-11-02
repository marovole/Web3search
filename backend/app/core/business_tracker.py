"""
业务指标追踪工具
提供装饰器和工具函数来追踪业务指标
"""
import asyncio
import time
from typing import Dict, Any, Optional, Callable
from functools import wraps
from datetime import datetime
import uuid

from app.core.business_metrics import (
    business_metrics_collector, 
    UserActivityEvent, 
    FeatureType
)
from app.core.monitoring import apm_collector
import logging

logger = logging.getLogger(__name__)


def track_feature_usage(feature: FeatureType, event_type: str = "usage"):
    """
    功能使用追踪装饰器
    
    Args:
        feature: 功能类型
        event_type: 事件类型
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            user_id = None
            session_id = None
            
            # 尝试从参数中提取用户信息
            try:
                # 从请求对象中获取用户ID
                if 'request' in kwargs:
                    request = kwargs['request']
                    if hasattr(request.state, 'user'):
                        user_id = request.state.user.id
                    session_id = getattr(request.state, 'session_id', str(uuid.uuid4()))
                
                # 从其他参数中提取用户ID
                if not user_id and args:
                    for arg in args:
                        if hasattr(arg, 'user_id'):
                            user_id = arg.user_id
                        elif hasattr(arg, 'id') and hasattr(arg, 'email'):  # User对象
                            user_id = arg.id
            except Exception as e:
                logger.debug(f"Could not extract user info: {e}")
            
            # 执行原函数
            try:
                result = await func(*args, **kwargs)
                success = True
                error = None
            except Exception as e:
                success = False
                error = str(e)
                raise
            finally:
                # 记录指标
                duration = time.time() - start_time
                
                if user_id:
                    # 创建用户活动事件
                    event = UserActivityEvent(
                        user_id=user_id,
                        event_type=event_type,
                        feature=feature,
                        timestamp=datetime.now(),
                        session_id=session_id or str(uuid.uuid4()),
                        properties={
                            "duration": duration,
                            "success": success,
                            "error": error,
                            "function": func.__name__
                        }
                    )
                    
                    # 异步记录事件
                    asyncio.create_task(business_metrics_collector.track_user_activity(event))
                
                # 记录到APM系统
                apm_collector.record_business_metric(
                    f"feature.{feature.value}.{event_type}",
                    1 if success else 0
                )
                apm_collector.record_business_metric(
                    f"feature.{feature.value}.duration",
                    duration * 1000  # 转换为毫秒
                )
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            user_id = None
            
            # 尝试从参数中提取用户信息
            try:
                if args and hasattr(args[0], 'user_id'):
                    user_id = args[0].user_id
            except Exception as e:
                logger.debug(f"Could not extract user info: {e}")
            
            # 执行原函数
            try:
                result = func(*args, **kwargs)
                success = True
                error = None
            except Exception as e:
                success = False
                error = str(e)
                raise
            finally:
                # 记录指标
                duration = time.time() - start_time
                
                if user_id:
                    # 创建用户活动事件
                    event = UserActivityEvent(
                        user_id=user_id,
                        event_type=event_type,
                        feature=feature,
                        timestamp=datetime.now(),
                        session_id=str(uuid.uuid4()),
                        properties={
                            "duration": duration,
                            "success": success,
                            "error": error,
                            "function": func.__name__
                        }
                    )
                    
                    # 异步记录事件
                    asyncio.create_task(business_metrics_collector.track_user_activity(event))
                
                # 记录到APM系统
                apm_collector.record_business_metric(
                    f"feature.{feature.value}.{event_type}",
                    1 if success else 0
                )
                apm_collector.record_business_metric(
                    f"feature.{feature.value}.duration",
                    duration * 1000
                )
            
            return result
        
        # 根据函数类型返回对应的包装器
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def track_user_action(action: str, feature: FeatureType = None):
    """
    用户行为追踪装饰器
    
    Args:
        action: 行为名称
        feature: 相关功能类型
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            user_id = None
            session_id = None
            
            # 提取用户信息
            try:
                if 'request' in kwargs:
                    request = kwargs['request']
                    if hasattr(request.state, 'user'):
                        user_id = request.state.user.id
                    session_id = getattr(request.state, 'session_id', str(uuid.uuid4()))
            except Exception as e:
                logger.debug(f"Could not extract user info: {e}")
            
            # 执行原函数
            try:
                result = await func(*args, **kwargs)
                success = True
                error = None
            except Exception as e:
                success = False
                error = str(e)
                raise
            finally:
                duration = time.time() - start_time
                
                if user_id and feature:
                    # 创建用户活动事件
                    event = UserActivityEvent(
                        user_id=user_id,
                        event_type=action,
                        feature=feature,
                        timestamp=datetime.now(),
                        session_id=session_id or str(uuid.uuid4()),
                        properties={
                            "duration": duration,
                            "success": success,
                            "error": error,
                            "action": action
                        }
                    )
                    
                    asyncio.create_task(business_metrics_collector.track_user_activity(event))
                
                # 记录到APM系统
                apm_collector.record_business_metric(f"user_action.{action}", 1 if success else 0)
            
            return result
        
        return async_wrapper
    
    return decorator


class BusinessMetricsTracker:
    """
    业务指标追踪器
    提供手动追踪业务指标的方法
    """
    
    @staticmethod
    async def track_search_query(user_id: str, query: str, results_count: int, duration_ms: float):
        """追踪搜索查询"""
        event = UserActivityEvent(
            user_id=user_id,
            event_type="search_query",
            feature=FeatureType.SEARCH,
            timestamp=datetime.now(),
            session_id=str(uuid.uuid4()),
            properties={
                "query_length": len(query),
                "results_count": results_count,
                "duration_ms": duration_ms
            }
        )
        
        await business_metrics_collector.track_user_activity(event)
        apm_collector.record_business_metric("search.queries", 1)
        apm_collector.record_business_metric("search.results_per_query", results_count)
    
    @staticmethod
    async def track_chat_message(user_id: str, message_type: str, tokens_used: int, duration_ms: float):
        """追踪聊天消息"""
        event = UserActivityEvent(
            user_id=user_id,
            event_type="chat_message",
            feature=FeatureType.CHAT,
            timestamp=datetime.now(),
            session_id=str(uuid.uuid4()),
            properties={
                "message_type": message_type,  # user, assistant, system
                "tokens_used": tokens_used,
                "duration_ms": duration_ms
            }
        )
        
        await business_metrics_collector.track_user_activity(event)
        apm_collector.record_business_metric("chat.messages", 1)
        apm_collector.record_business_metric("chat.tokens_used", tokens_used)
    
    @staticmethod
    async def track_research_request(user_id: str, research_type: str, complexity_score: float, duration_ms: float):
        """追踪研究请求"""
        event = UserActivityEvent(
            user_id=user_id,
            event_type="research_request",
            feature=FeatureType.RESEARCH,
            timestamp=datetime.now(),
            session_id=str(uuid.uuid4()),
            properties={
                "research_type": research_type,
                "complexity_score": complexity_score,
                "duration_ms": duration_ms
            }
        )
        
        await business_metrics_collector.track_user_activity(event)
        apm_collector.record_business_metric("research.requests", 1)
        apm_collector.record_business_metric("research.complexity", complexity_score)
    
    @staticmethod
    async def track_report_generation(user_id: str, report_type: str, sections_count: int, duration_ms: float):
        """追踪报告生成"""
        event = UserActivityEvent(
            user_id=user_id,
            event_type="report_generation",
            feature=FeatureType.REPORTS,
            timestamp=datetime.now(),
            session_id=str(uuid.uuid4()),
            properties={
                "report_type": report_type,
                "sections_count": sections_count,
                "duration_ms": duration_ms
            }
        )
        
        await business_metrics_collector.track_user_activity(event)
        apm_collector.record_business_metric("reports.generated", 1)
        apm_collector.record_business_metric("reports.sections", sections_count)
    
    @staticmethod
    async def track_report_sharing(user_id: str, report_id: str, share_type: str, platform: str):
        """追踪报告分享"""
        event = UserActivityEvent(
            user_id=user_id,
            event_type="report_sharing",
            feature=FeatureType.SHARING,
            timestamp=datetime.now(),
            session_id=str(uuid.uuid4()),
            properties={
                "report_id": report_id,
                "share_type": share_type,  # link, embed, export
                "platform": platform
            }
        )
        
        await business_metrics_collector.track_user_activity(event)
        apm_collector.record_business_metric("sharing.reports", 1)
    
    @staticmethod
    async def track_watchlist_action(user_id: str, action: str, symbol: str, price_target: float = None):
        """追踪观察列表操作"""
        event = UserActivityEvent(
            user_id=user_id,
            event_type=f"watchlist_{action}",
            feature=FeatureType.WATCHLIST,
            timestamp=datetime.now(),
            session_id=str(uuid.uuid4()),
            properties={
                "action": action,  # add, remove, update
                "symbol": symbol,
                "price_target": price_target
            }
        )
        
        await business_metrics_collector.track_user_activity(event)
        apm_collector.record_business_metric(f"watchlist.{action}", 1)
    
    @staticmethod
    async def track_user_session(user_id: str, session_start: datetime, session_end: datetime, page_views: int, interactions: int):
        """追踪用户会话"""
        duration = (session_end - session_start).total_seconds()
        
        event = UserActivityEvent(
            user_id=user_id,
            event_type="session_end",
            feature=FeatureType.HISTORY,  # 使用HISTORY作为会话追踪的分类
            timestamp=session_end,
            session_id=str(uuid.uuid4()),
            properties={
                "session_duration_seconds": duration,
                "page_views": page_views,
                "interactions": interactions,
                "session_start": session_start.isoformat()
            }
        )
        
        await business_metrics_collector.track_user_activity(event)
        apm_collector.record_business_metric("sessions.duration", duration)
        apm_collector.record_business_metric("sessions.page_views", page_views)
        apm_collector.record_business_metric("sessions.interactions", interactions)
    
    @staticmethod
    async def track_conversion_event(user_id: str, conversion_type: str, value: float, properties: Dict[str, Any] = None):
        """追踪转化事件"""
        event = UserActivityEvent(
            user_id=user_id,
            event_type="conversion",
            feature=FeatureType.SHARING,  # 使用SHARING作为转化事件的分类
            timestamp=datetime.now(),
            session_id=str(uuid.uuid4()),
            properties={
                "conversion_type": conversion_type,
                "value": value,
                **(properties or {})
            }
        )
        
        await business_metrics_collector.track_user_activity(event)
        apm_collector.record_business_metric(f"conversions.{conversion_type}", 1)
        apm_collector.record_business_metric(f"conversions.value", value)


# 便捷的追踪函数
tracker = BusinessMetricsTracker()
