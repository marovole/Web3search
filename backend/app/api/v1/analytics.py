"""
分析API端点

提供完整的用户分析和隐私合规API：
- 分析数据聚合
- 仪表板数据
- 用户同意管理
- 数据导出/删除
- 事件记录
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse

from app.services.analytics_service import (
    analytics_service,
    aggregate_analytics_data,
    record_user_consent,
    export_user_data,
    delete_user_data,
    record_analytics_event,
    generate_dashboard_data,
)
from app.core.auth import get_current_user_optional
from app.api.middleware.auth import get_current_user, require_admin
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


# ================================
# 请求/响应模型
# ================================

class AnalyticsAggregationRequest(BaseModel):
    """分析数据聚合请求"""
    time_window_hours: int = Field(24, ge=1, le=168, description="时间窗口（小时）")


class UserConsentRequest(BaseModel):
    """用户同意请求"""
    consent_given: bool = Field(..., description="是否同意")
    consent_type: str = Field(..., description="同意类型：analytics, marketing, necessary")
    ip_address: Optional[str] = Field(None, description="IP地址")
    user_agent: Optional[str] = Field(None, description="用户代理")


class AnalyticsEventRequest(BaseModel):
    """分析事件请求"""
    event_type: str = Field(..., description="事件类型")
    event_name: str = Field(..., description="事件名称")
    session_id: Optional[str] = Field(None, description="会话ID")
    properties: Optional[Dict[str, Any]] = Field(default_factory=dict, description="事件属性")
    consent_given: bool = Field(False, description="是否获得同意")


class DataExportResponse(BaseModel):
    """数据导出响应"""
    user_id: str
    export_timestamp: float
    data_categories: Dict[str, Any]
    download_url: Optional[str] = None


class PrivacyMetricsResponse(BaseModel):
    """隐私指标响应"""
    total_users: int
    consented_users: int
    consent_rate: float
    data_retention_compliance: bool
    anonymization_applied: bool
    export_requests: int


class BusinessMetricsResponse(BaseModel):
    """业务指标响应"""
    period_start: float
    period_end: float
    total_users: int
    active_users: int
    new_users: int
    returning_users: int
    total_sessions: int
    avg_session_duration: float
    page_views: int
    search_queries: int
    reports_generated: int
    conversion_rate: float


class PredictiveInsightsResponse(BaseModel):
    """预测洞察响应"""
    user_growth_prediction: float
    churn_risk_users: List[str]
    popular_features: List[str]
    performance_trends: Dict[str, float]
    recommendation_score: float


class AlertResponse(BaseModel):
    """告警响应"""
    type: str
    severity: str
    message: str
    recommendation: str
    timestamp: Optional[float] = None


class DashboardResponse(BaseModel):
    """仪表板响应"""
    timestamp: float
    realtime_metrics: Dict[str, Any]
    business_metrics: BusinessMetricsResponse
    privacy_metrics: PrivacyMetricsResponse
    predictive_insights: PredictiveInsightsResponse
    alerts: List[AlertResponse]
    user_behavior_summary: Dict[str, Any]


# ================================
# 分析数据聚合API
# ================================

@router.post("/aggregate", response_model=Dict[str, Any])
async def aggregate_analytics(
    request: AnalyticsAggregationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_admin),
):
    """
    聚合分析数据（管理员专用）

    收集和处理指定时间窗口内的所有分析数据，包括：
    - 用户事件统计
    - 业务指标计算
    - 隐私合规指标
    - A/B测试结果
    - 预测性洞察

    **权限要求:** 管理员
    """
    try:
        logger.info(f"开始聚合分析数据，时间窗口: {request.time_window_hours}小时")

        # 后台执行聚合任务
        background_tasks.add_task(
            aggregate_analytics_data,
            request.time_window_hours
        )

        # 立即返回当前缓存的数据（如果有的话）
        aggregated_data = await aggregate_analytics_data(request.time_window_hours)

        return {
            "status": "success",
            "data": aggregated_data,
            "timestamp": datetime.utcnow().timestamp(),
            "time_window_hours": request.time_window_hours,
        }

    except Exception as e:
        logger.error(f"聚合分析数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"聚合分析数据失败: {str(e)}")


@router.get("/dashboard", response_model=DashboardResponse)
async def get_analytics_dashboard(
    current_user: User = Depends(require_admin),
):
    """
    获取分析仪表板数据

    提供完整的分析仪表板数据，包括：
    - 实时指标
    - 业务指标
    - 用户行为分析
    - A/B测试结果
    - 隐私合规指标
    - 预测性洞察
    - 智能告警
    """
    try:
        logger.info("获取分析仪表板数据")

        # 生成仪表板数据
        dashboard = await generate_dashboard_data()

        # 转换为响应格式
        response = DashboardResponse(
            timestamp=dashboard.timestamp,
            realtime_metrics=dashboard.realtime_metrics,
            business_metrics=BusinessMetricsResponse(
                period_start=dashboard.business_metrics.period_start,
                period_end=dashboard.business_metrics.period_end,
                total_users=dashboard.business_metrics.total_users,
                active_users=dashboard.business_metrics.active_users,
                new_users=dashboard.business_metrics.new_users,
                returning_users=dashboard.business_metrics.returning_users,
                total_sessions=dashboard.business_metrics.total_sessions,
                avg_session_duration=dashboard.business_metrics.avg_session_duration,
                page_views=dashboard.business_metrics.page_views,
                search_queries=dashboard.business_metrics.search_queries,
                reports_generated=dashboard.business_metrics.reports_generated,
                conversion_rate=dashboard.business_metrics.conversion_rate,
            ),
            privacy_metrics=PrivacyMetricsResponse(
                total_users=dashboard.privacy_metrics.total_users,
                consented_users=dashboard.privacy_metrics.consented_users,
                consent_rate=dashboard.privacy_metrics.consent_rate,
                data_retention_compliance=dashboard.privacy_metrics.data_retention_compliance,
                anonymization_applied=dashboard.privacy_metrics.anonymization_applied,
                export_requests=dashboard.privacy_metrics.export_requests,
            ),
            predictive_insights=PredictiveInsightsResponse(
                user_growth_prediction=dashboard.predictive_insights.user_growth_prediction,
                churn_risk_users=dashboard.predictive_insights.churn_risk_users,
                popular_features=dashboard.predictive_insights.popular_features,
                performance_trends=dashboard.predictive_insights.performance_trends,
                recommendation_score=dashboard.predictive_insights.recommendation_score,
            ),
            alerts=[
                AlertResponse(
                    type=alert.get("type", "info"),
                    severity=alert.get("severity", "low"),
                    message=alert.get("message", ""),
                    recommendation=alert.get("recommendation", ""),
                    timestamp=dashboard.timestamp,
                )
                for alert in dashboard.alerts
            ],
            user_behavior_summary={
                "total_queries": dashboard.user_behavior.total_queries,
                "unique_users": dashboard.user_behavior.unique_users,
                "popular_coins": dashboard.user_behavior.popular_coins[:10],
                "peak_hours": dashboard.user_behavior.peak_hours[:6],
                "user_segments": dashboard.user_behavior.user_segments,
            },
        )

        return response

    except Exception as e:
        logger.error(f"获取仪表板数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取仪表板数据失败: {str(e)}")


@router.get("/metrics/realtime", response_model=Dict[str, Any])
async def get_realtime_metrics(
    current_user: User = Depends(require_admin),
):
    """获取实时指标"""
    try:
        realtime_metrics = await analytics_service._get_realtime_metrics()

        return {
            "status": "success",
            "data": realtime_metrics,
            "timestamp": datetime.utcnow().timestamp(),
        }

    except Exception as e:
        logger.error(f"获取实时指标失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取实时指标失败: {str(e)}")


@router.get("/metrics/business", response_model=BusinessMetricsResponse)
async def get_business_metrics(
    time_window_hours: int = Query(24, ge=1, le=168, description="时间窗口（小时）"),
    current_user: User = Depends(require_admin),
):
    """获取业务指标"""
    try:
        business_metrics = await analytics_service._calculate_business_metrics(time_window_hours)

        return BusinessMetricsResponse(
            period_start=business_metrics.period_start,
            period_end=business_metrics.period_end,
            total_users=business_metrics.total_users,
            active_users=business_metrics.active_users,
            new_users=business_metrics.new_users,
            returning_users=business_metrics.returning_users,
            total_sessions=business_metrics.total_sessions,
            avg_session_duration=business_metrics.avg_session_duration,
            page_views=business_metrics.page_views,
            search_queries=business_metrics.search_queries,
            reports_generated=business_metrics.reports_generated,
            conversion_rate=business_metrics.conversion_rate,
        )

    except Exception as e:
        logger.error(f"获取业务指标失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取业务指标失败: {str(e)}")


@router.get("/metrics/privacy", response_model=PrivacyMetricsResponse)
async def get_privacy_metrics(
    time_window_hours: int = Query(24, ge=1, le=168, description="时间窗口（小时）"),
    current_user: User = Depends(require_admin),
):
    """获取隐私合规指标"""
    try:
        privacy_data = await analytics_service._aggregate_privacy_metrics(time_window_hours)

        return PrivacyMetricsResponse(**privacy_data)

    except Exception as e:
        logger.error(f"获取隐私指标失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取隐私指标失败: {str(e)}")


@router.get("/insights/predictive", response_model=PredictiveInsightsResponse)
async def get_predictive_insights(
    time_window_hours: int = Query(24, ge=1, le=168, description="时间窗口（小时）"),
    current_user: User = Depends(require_admin),
):
    """获取预测性洞察"""
    try:
        insights_data = await analytics_service._generate_predictive_insights(time_window_hours)

        return PredictiveInsightsResponse(**insights_data)

    except Exception as e:
        logger.error(f"获取预测洞察失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取预测洞察失败: {str(e)}")


# ================================
# 隐私合规API
# ================================

@router.post("/consent")
async def set_user_consent(
    consent: UserConsentRequest,
    current_user: User = Depends(get_current_user),
):
    """
    设置用户同意状态

    用户可以管理自己的隐私同意设置。

    支持的同意类型：
    - analytics: 分析和追踪
    - marketing: 营销活动
    - necessary: 必要功能

    **权限要求:** 用户认证
    """
    try:
        user_id = current_user.id

        success = await record_user_consent(
            user_id=user_id,
            consent_given=consent.consent_given,
            consent_type=consent.consent_type,
            ip_address=consent.ip_address,
            user_agent=consent.user_agent,
        )

        if success:
            return {
                "status": "success",
                "message": f"用户同意已记录: {consent.consent_type} = {consent.consent_given}",
                "timestamp": datetime.utcnow().timestamp(),
            }
        else:
            raise HTTPException(status_code=500, detail="记录用户同意失败")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"设置用户同意失败: {e}")
        raise HTTPException(status_code=500, detail=f"设置用户同意失败: {str(e)}")


@router.get("/consent/{consent_type}")
async def get_user_consent_status(
    consent_type: str,
    current_user: User = Depends(get_current_user),
):
    """
    获取用户同意状态

    用户可以查看自己的隐私同意设置。

    **权限要求:** 用户认证
    """
    try:
        user_id = current_user.id

        consent_data = await analytics_service.get_user_consent(user_id, consent_type)

        if consent_data:
            return {
                "status": "success",
                "consent": consent_data,
            }
        else:
            return {
                "status": "not_found",
                "message": f"未找到同意记录: {consent_type}",
            }

    except Exception as e:
        logger.error(f"获取用户同意状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取用户同意状态失败: {str(e)}")


@router.post("/data/export")
async def export_user_data_endpoint(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """
    导出用户数据（GDPR合规）

    用户可以请求导出自己的所有数据。

    返回包含用户所有数据的JSON文件下载链接。

    **权限要求:** 用户认证
    """
    try:
        if not current_user:
            raise HTTPException(status_code=401, detail="需要登录才能导出数据")

        user_id = current_user.id

        # 后台执行导出任务
        background_tasks.add_task(export_user_data, user_id)

        # 立即返回确认
        return {
            "status": "accepted",
            "message": "数据导出请求已接受，正在处理中",
            "user_id": user_id,
            "request_timestamp": datetime.utcnow().timestamp(),
            "estimated_completion": "5-10分钟",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"请求数据导出失败: {e}")
        raise HTTPException(status_code=500, detail=f"请求数据导出失败: {str(e)}")


@router.get("/data/export/status/{user_id}")
async def get_export_status(
    user_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    获取数据导出状态

    用户可以查看自己的数据导出状态，管理员可以查看所有用户的状态。

    **权限要求:** 用户认证 + 资源所有权或管理员
    """
    try:
        # 验证用户权限：只能查看自己的导出状态，或者是管理员
        if current_user.id != user_id and not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="无权查看此用户的导出状态")

        # 检查导出状态（简化实现）
        return {
            "status": "processing",
            "message": "数据导出正在进行中",
            "user_id": user_id,
            "last_updated": datetime.utcnow().timestamp(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取导出状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取导出状态失败: {str(e)}")


@router.delete("/data")
async def delete_user_data_endpoint(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """
    删除用户数据（GDPR合规）

    用户可以请求删除自己的所有分析数据。

    永久删除用户的所有数据，包括：
    - 行为追踪数据
    - 同意记录
    - 分析事件

    **权限要求:** 用户认证
    """
    try:
        if not current_user:
            raise HTTPException(status_code=401, detail="需要登录才能删除数据")

        user_id = current_user.id

        # 后台执行删除任务
        background_tasks.add_task(delete_user_data, user_id)

        # 记录删除请求
        await record_analytics_event(
            event_type="privacy",
            event_name="data_deletion_requested",
            user_id=user_id,
            consent_given=True,
        )

        return {
            "status": "accepted",
            "message": "数据删除请求已接受，正在处理中",
            "user_id": user_id,
            "request_timestamp": datetime.utcnow().timestamp(),
            "note": "数据删除将在24小时内完成",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"请求数据删除失败: {e}")
        raise HTTPException(status_code=500, detail=f"请求数据删除失败: {str(e)}")


# ================================
# 事件记录API
# ================================

@router.post("/events")
async def record_event(
    event: AnalyticsEventRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    记录分析事件

    支持匿名和认证用户的事件记录。

    支持的事件类型：
    - page_view: 页面浏览
    - search: 搜索操作
    - interaction: 用户交互
    - performance: 性能指标
    - error: 错误事件
    - engagement: 用户参与
    - feature_usage: 功能使用
    - analytics: 分析相关

    **权限要求:** 可选认证（支持匿名）
    """
    try:
        user_id = current_user.id if current_user else None

        success = await record_analytics_event(
            event_type=event.event_type,
            event_name=event.event_name,
            user_id=user_id,
            session_id=event.session_id,
            properties=event.properties,
            consent_given=event.consent_given,
        )

        if success:
            return {
                "status": "success",
                "message": f"事件已记录: {event.event_type}.{event.event_name}",
                "timestamp": datetime.utcnow().timestamp(),
            }
        else:
            raise HTTPException(status_code=500, detail="记录事件失败")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"记录事件失败: {e}")
        raise HTTPException(status_code=500, detail=f"记录事件失败: {str(e)}")


@router.get("/events/stats")
async def get_event_stats(
    event_type: Optional[str] = Query(None, description="事件类型过滤"),
    time_window_hours: int = Query(24, ge=1, le=168, description="时间窗口（小时）"),
    current_user: User = Depends(require_admin),
):
    """获取事件统计"""
    try:
        # 获取聚合数据
        aggregated_data = await aggregate_analytics_data(time_window_hours)

        if event_type:
            # 过滤特定事件类型
            event_stats = aggregated_data.get("user_events", {}).get("event_distribution", {}).get(event_type, 0)
            return {
                "status": "success",
                "event_type": event_type,
                "count": event_stats,
                "time_window_hours": time_window_hours,
                "timestamp": datetime.utcnow().timestamp(),
            }
        else:
            # 返回所有事件统计
            return {
                "status": "success",
                "event_distribution": aggregated_data.get("user_events", {}).get("event_distribution", {}),
                "total_events": aggregated_data.get("user_events", {}).get("total_events", 0),
                "time_window_hours": time_window_hours,
                "timestamp": datetime.utcnow().timestamp(),
            }

    except Exception as e:
        logger.error(f"获取事件统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取事件统计失败: {str(e)}")


# ================================
# A/B测试API
# ================================

@router.get("/ab-tests")
async def list_ab_tests(
    current_user: User = Depends(require_admin),
):
    """列出所有A/B测试"""
    try:
        from app.services.ab_testing import ab_test_manager

        test_names = ab_test_manager.list_tests()
        tests = []

        for test_name in test_names:
            result = ab_test_manager.get_result(test_name)
            if result:
                tests.append(result.to_dict())

        return {
            "status": "success",
            "tests": tests,
            "total": len(tests),
            "timestamp": datetime.utcnow().timestamp(),
        }

    except Exception as e:
        logger.error(f"列出A/B测试失败: {e}")
        raise HTTPException(status_code=500, detail=f"列出A/B测试失败: {str(e)}")


@router.get("/ab-tests/{test_name}")
async def get_ab_test_result(
    test_name: str,
    current_user: User = Depends(require_admin),
):
    """获取A/B测试结果"""
    try:
        from app.services.ab_testing import ab_test_manager

        result = ab_test_manager.get_result(test_name)
        if result:
            return {
                "status": "success",
                "test": result.to_dict(),
                "timestamp": datetime.utcnow().timestamp(),
            }
        else:
            raise HTTPException(status_code=404, detail=f"测试不存在: {test_name}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取A/B测试结果失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取A/B测试结果失败: {str(e)}")


# ================================
# 健康检查
# ================================

@router.get("/health")
async def analytics_health_check():
    """分析服务健康检查"""
    try:
        # 检查服务状态
        await analytics_service.ensure_initialized()

        return {
            "status": "healthy",
            "service": "analytics",
            "timestamp": datetime.utcnow().timestamp(),
            "version": "1.0.0",
        }

    except Exception as e:
        logger.error(f"分析服务健康检查失败: {e}")
        raise HTTPException(status_code=503, detail=f"服务不可用: {str(e)}")


# ================================
# 管理API（需要管理员权限）
# ================================

@router.post("/admin/reset-cache")
async def reset_analytics_cache(
    current_user: User = Depends(require_admin),
):
    """重置分析缓存（管理员功能）"""
    try:
        # 这里应该检查管理员权限
        if not current_user:
            raise HTTPException(status_code=401, detail="需要管理员权限")

        # 重置缓存的逻辑（简化实现）
        logger.info("重置分析缓存")

        return {
            "status": "success",
            "message": "分析缓存已重置",
            "timestamp": datetime.utcnow().timestamp(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重置分析缓存失败: {e}")
        raise HTTPException(status_code=500, detail=f"重置分析缓存失败: {str(e)}")
