"""
业务指标Dashboard API
提供用户活跃度、功能使用率等核心业务指标的可视化接口
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio

from app.core.business_metrics import (
    business_metrics_collector, 
    UserActivityMetrics, 
    FeatureUsageMetrics,
    FeatureType
)
from app.core.business_tracker import tracker
from app.api.deps import get_current_user, require_admin
from app.models.user import User

router = APIRouter(prefix="/business", tags=["Business Metrics"])


@router.get("/dashboard/overview")
async def get_business_dashboard_overview(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取业务Dashboard概览
    包括用户活跃度、功能使用情况、关键趋势等
    """
    try:
        today = datetime.now().date()
        
        # 获取用户活跃度指标
        activity_metrics = await business_metrics_collector.get_user_activity_metrics(today)
        
        # 获取功能使用指标
        feature_metrics = await business_metrics_collector.get_feature_usage_metrics(today)
        
        # 获取历史趋势数据
        trends = await _get_business_trends(today, days=7)
        
        # 计算关键业务指标
        kpis = _calculate_business_kpis(activity_metrics, feature_metrics)
        
        # 热门功能排行
        top_features = _get_top_features(feature_metrics)
        
        return {
            "date": today.isoformat(),
            "summary": {
                "total_users": activity_metrics.total_users,
                "active_users": activity_metrics.active_users,
                "new_users": activity_metrics.new_users,
                "engagement_score": activity_metrics.engagement_score,
                "retention_rate": activity_metrics.retention_rate
            },
            "kpis": kpis,
            "user_activity": {
                "dau": activity_metrics.active_users,
                "wau": activity_metrics.weekly_active_users,
                "mau": activity_metrics.monthly_active_users,
                "user_segments": {
                    "new": activity_metrics.new_users,
                    "active": activity_metrics.active_users - activity_metrics.new_users,
                    "returning": activity_metrics.returning_users,
                    "dormant": activity_metrics.dormant_users,
                    "churned": activity_metrics.churned_users
                }
            },
            "feature_usage": {
                "total_features_used": len([f for f in feature_metrics if f.active_users > 0]),
                "top_features": top_features,
                "feature_details": [
                    {
                        "feature": metric.feature.value,
                        "users": metric.active_users,
                        "usage_count": metric.usage_count,
                        "conversion_rate": metric.conversion_rate,
                        "avg_session_duration": metric.avg_session_duration
                    }
                    for metric in feature_metrics
                ]
            },
            "trends": trends
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get business dashboard: {str(e)}")


@router.get("/metrics/user-activity")
async def get_user_activity_metrics(
    date: str = Query(None, description="日期 (YYYY-MM-DD格式)"),
    period: str = Query("day", description="周期: day, week, month"),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取用户活跃度指标
    """
    try:
        if date:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
        else:
            target_date = datetime.now().date()
        
        if period == "week":
            # 获取一周的数据
            metrics = []
            for i in range(7):
                date = target_date - timedelta(days=6-i)
                daily_metrics = await business_metrics_collector.get_user_activity_metrics(date)
                metrics.append({
                    "date": date.isoformat(),
                    "dau": daily_metrics.active_users,
                    "new_users": daily_metrics.new_users,
                    "retention_rate": daily_metrics.retention_rate,
                    "engagement_score": daily_metrics.engagement_score
                })
        elif period == "month":
            # 获取30天的趋势
            metrics = []
            for i in range(30):
                date = target_date - timedelta(days=29-i)
                daily_metrics = await business_metrics_collector.get_user_activity_metrics(date)
                metrics.append({
                    "date": date.isoformat(),
                    "dau": daily_metrics.active_users,
                    "new_users": daily_metrics.new_users,
                    "retention_rate": daily_metrics.retention_rate
                })
        else:  # day
            daily_metrics = await business_metrics_collector.get_user_activity_metrics(target_date)
            metrics = {
                "date": target_date.isoformat(),
                "total_users": daily_metrics.total_users,
                "new_users": daily_metrics.new_users,
                "active_users": daily_metrics.active_users,
                "weekly_active_users": daily_metrics.weekly_active_users,
                "monthly_active_users": daily_metrics.monthly_active_users,
                "returning_users": daily_metrics.returning_users,
                "dormant_users": daily_metrics.dormant_users,
                "churned_users": daily_metrics.churned_users,
                "retention_rate": daily_metrics.retention_rate,
                "engagement_score": daily_metrics.engagement_score
            }
        
        return {
            "period": period,
            "date": target_date.isoformat(),
            "metrics": metrics
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user activity metrics: {str(e)}")


@router.get("/metrics/feature-usage")
async def get_feature_usage_metrics(
    date: str = Query(None, description="日期 (YYYY-MM-DD格式)"),
    feature: str = Query(None, description="特定功能名称"),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取功能使用指标
    """
    try:
        if date:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
        else:
            target_date = datetime.now().date()
        
        feature_metrics = await business_metrics_collector.get_feature_usage_metrics(target_date)
        
        if feature:
            # 返回特定功能的详细指标
            feature_type = FeatureType(feature)
            target_metric = next((m for m in feature_metrics if m.feature == feature_type), None)
            
            if not target_metric:
                raise HTTPException(status_code=404, detail=f"Feature {feature} not found")
            
            # 获取历史趋势
            trends = await _get_feature_trends(feature_type, target_date, days=7)
            
            return {
                "date": target_date.isoformat(),
                "feature": feature,
                "metrics": {
                    "total_users": target_metric.total_users,
                    "active_users": target_metric.active_users,
                    "usage_count": target_metric.usage_count,
                    "avg_session_duration": target_metric.avg_session_duration,
                    "conversion_rate": target_metric.conversion_rate,
                    "error_rate": target_metric.error_rate
                },
                "trends": trends
            }
        else:
            # 返回所有功能的指标
            return {
                "date": target_date.isoformat(),
                "features": [
                    {
                        "feature": metric.feature.value,
                        "total_users": metric.total_users,
                        "active_users": metric.active_users,
                        "usage_count": metric.usage_count,
                        "avg_session_duration": metric.avg_session_duration,
                        "conversion_rate": metric.conversion_rate,
                        "error_rate": metric.error_rate
                    }
                    for metric in feature_metrics
                ]
            }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid feature name: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get feature usage metrics: {str(e)}")


@router.get("/analytics/user-segments")
async def get_user_segments(
    date: str = Query(None, description="日期 (YYYY-MM-DD格式)"),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取用户分群分析
    """
    try:
        if date:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
        else:
            target_date = datetime.now().date()
        
        activity_metrics = await business_metrics_collector.get_user_activity_metrics(target_date)
        
        # 计算用户分群占比
        total_users = activity_metrics.total_users or 1
        
        segments = {
            "new_users": {
                "count": activity_metrics.new_users,
                "percentage": (activity_metrics.new_users / total_users) * 100
            },
            "active_users": {
                "count": activity_metrics.active_users - activity_metrics.new_users,
                "percentage": ((activity_metrics.active_users - activity_metrics.new_users) / total_users) * 100
            },
            "returning_users": {
                "count": activity_metrics.returning_users,
                "percentage": (activity_metrics.returning_users / total_users) * 100
            },
            "dormant_users": {
                "count": activity_metrics.dormant_users,
                "percentage": (activity_metrics.dormant_users / total_users) * 100
            },
            "churned_users": {
                "count": activity_metrics.churned_users,
                "percentage": (activity_metrics.churned_users / total_users) * 100
            }
        }
        
        # 获取分群趋势
        segment_trends = await _get_user_segment_trends(target_date, days=30)
        
        return {
            "date": target_date.isoformat(),
            "total_users": total_users,
            "segments": segments,
            "trends": segment_trends,
            "insights": _generate_segment_insights(segments, segment_trends)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user segments: {str(e)}")


@router.get("/analytics/feature-correlation")
async def get_feature_correlation(
    date: str = Query(None, description="日期 (YYYY-MM-DD格式)"),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取功能关联性分析
    分析用户使用不同功能的关联性
    """
    try:
        if date:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
        else:
            target_date = datetime.now().date()
        
        # 获取功能使用数据
        feature_metrics = await business_metrics_collector.get_feature_usage_metrics(target_date)
        
        # 计算功能关联性矩阵
        correlation_matrix = await _calculate_feature_correlation(target_date)
        
        # 识别功能使用模式
        usage_patterns = _identify_usage_patterns(feature_metrics)
        
        return {
            "date": target_date.isoformat(),
            "correlation_matrix": correlation_matrix,
            "usage_patterns": usage_patterns,
            "recommendations": _generate_feature_recommendations(usage_patterns)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get feature correlation: {str(e)}")


@router.post("/track/event")
async def track_business_event(
    event_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """
    手动追踪业务事件
    """
    try:
        event_type = event_data.get("event_type")
        feature = event_data.get("feature")
        properties = event_data.get("properties", {})
        
        if not event_type or not feature:
            raise HTTPException(status_code=400, detail="event_type and feature are required")
        
        # 根据事件类型调用相应的追踪函数
        if event_type == "search_query":
            await tracker.track_search_query(
                user_id=current_user.id,
                query=properties.get("query", ""),
                results_count=properties.get("results_count", 0),
                duration_ms=properties.get("duration_ms", 0)
            )
        elif event_type == "chat_message":
            await tracker.track_chat_message(
                user_id=current_user.id,
                message_type=properties.get("message_type", "user"),
                tokens_used=properties.get("tokens_used", 0),
                duration_ms=properties.get("duration_ms", 0)
            )
        elif event_type == "research_request":
            await tracker.track_research_request(
                user_id=current_user.id,
                research_type=properties.get("research_type", "general"),
                complexity_score=properties.get("complexity_score", 0.5),
                duration_ms=properties.get("duration_ms", 0)
            )
        elif event_type == "report_generation":
            await tracker.track_report_generation(
                user_id=current_user.id,
                report_type=properties.get("report_type", "standard"),
                sections_count=properties.get("sections_count", 1),
                duration_ms=properties.get("duration_ms", 0)
            )
        else:
            # 通用事件追踪
            from app.core.business_metrics import UserActivityEvent, FeatureType
            
            event = UserActivityEvent(
                user_id=current_user.id,
                event_type=event_type,
                feature=FeatureType(feature),
                timestamp=datetime.now(),
                session_id=properties.get("session_id", ""),
                properties=properties
            )
            
            await business_metrics_collector.track_user_activity(event)
        
        return {"status": "success", "message": "Event tracked successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to track event: {str(e)}")


async def _get_business_trends(date: datetime, days: int) -> Dict[str, List]:
    """获取业务趋势数据"""
    trends = {
        "dau": [],
        "new_users": [],
        "engagement_score": [],
        "retention_rate": []
    }
    
    for i in range(days):
        current_date = date - timedelta(days=days-1-i)
        metrics = await business_metrics_collector.get_user_activity_metrics(current_date)
        
        trends["dau"].append({
            "date": current_date.isoformat(),
            "value": metrics.active_users
        })
        trends["new_users"].append({
            "date": current_date.isoformat(),
            "value": metrics.new_users
        })
        trends["engagement_score"].append({
            "date": current_date.isoformat(),
            "value": metrics.engagement_score
        })
        trends["retention_rate"].append({
            "date": current_date.isoformat(),
            "value": metrics.retention_rate
        })
    
    return trends


def _calculate_business_kpis(activity_metrics: UserActivityMetrics, feature_metrics: List[FeatureUsageMetrics]) -> Dict[str, Any]:
    """计算关键业务指标"""
    # 日活跃用户增长率（模拟）
    dau_growth_rate = 0.05  # 5%增长
    
    # 功能渗透率（使用至少一个功能的用户占比）
    feature_penetration = len([f for f in feature_metrics if f.active_users > 0]) / len(FeatureType)
    
    # 平均每用户使用功能数
    avg_features_per_user = sum(f.active_users for f in feature_metrics) / max(activity_metrics.active_users, 1)
    
    # 整体转化率
    overall_conversion_rate = sum(f.conversion_rate for f in feature_metrics) / len(feature_metrics)
    
    return {
        "dau_growth_rate": dau_growth_rate,
        "feature_penetration_rate": feature_penetration * 100,
        "avg_features_per_user": round(avg_features_per_user, 2),
        "overall_conversion_rate": overall_conversion_rate * 100,
        "user_satisfaction_score": min(activity_metrics.engagement_score, 100)
    }


def _get_top_features(feature_metrics: List[FeatureUsageMetrics], limit: int = 5) -> List[Dict[str, Any]]:
    """获取热门功能排行"""
    sorted_features = sorted(feature_metrics, key=lambda x: x.usage_count, reverse=True)
    
    return [
        {
            "feature": metric.feature.value,
            "usage_count": metric.usage_count,
            "active_users": metric.active_users,
            "conversion_rate": metric.conversion_rate
        }
        for metric in sorted_features[:limit]
    ]


async def _get_feature_trends(feature: FeatureType, date: datetime, days: int) -> Dict[str, List]:
    """获取功能趋势数据"""
    trends = {
        "usage_count": [],
        "active_users": [],
        "conversion_rate": []
    }
    
    for i in range(days):
        current_date = date - timedelta(days=days-1-i)
        daily_metrics = await business_metrics_collector.get_feature_usage_metrics(current_date)
        target_metric = next((m for m in daily_metrics if m.feature == feature), None)
        
        if target_metric:
            trends["usage_count"].append({
                "date": current_date.isoformat(),
                "value": target_metric.usage_count
            })
            trends["active_users"].append({
                "date": current_date.isoformat(),
                "value": target_metric.active_users
            })
            trends["conversion_rate"].append({
                "date": current_date.isoformat(),
                "value": target_metric.conversion_rate
            })
        else:
            trends["usage_count"].append({"date": current_date.isoformat(), "value": 0})
            trends["active_users"].append({"date": current_date.isoformat(), "value": 0})
            trends["conversion_rate"].append({"date": current_date.isoformat(), "value": 0})
    
    return trends


async def _get_user_segment_trends(date: datetime, days: int) -> Dict[str, List]:
    """获取用户分群趋势"""
    trends = {
        "new_users": [],
        "active_users": [],
        "churned_users": []
    }
    
    for i in range(min(days, 30)):  # 最多30天
        current_date = date - timedelta(days=days-1-i)
        metrics = await business_metrics_collector.get_user_activity_metrics(current_date)
        
        trends["new_users"].append({
            "date": current_date.isoformat(),
            "value": metrics.new_users
        })
        trends["active_users"].append({
            "date": current_date.isoformat(),
            "value": metrics.active_users
        })
        trends["churned_users"].append({
            "date": current_date.isoformat(),
            "value": metrics.churned_users
        })
    
    return trends


def _generate_segment_insights(segments: Dict[str, Any], trends: Dict[str, List]) -> List[str]:
    """生成用户分群洞察"""
    insights = []
    
    # 新用户占比分析
    new_user_percentage = segments["new_users"]["percentage"]
    if new_user_percentage > 20:
        insights.append("新用户增长强劲，建议加强用户引导")
    elif new_user_percentage < 5:
        insights.append("新用户获取不足，建议优化获客策略")
    
    # 流失用户分析
    churned_percentage = segments["churned_users"]["percentage"]
    if churned_percentage > 15:
        insights.append("用户流失率较高，需要改善用户体验")
    
    # 活跃用户分析
    active_percentage = segments["active_users"]["percentage"] + segments["new_users"]["percentage"]
    if active_percentage > 60:
        insights.append("用户活跃度良好，产品粘性较强")
    
    return insights


async def _calculate_feature_correlation(date: datetime) -> Dict[str, Any]:
    """计算功能关联性矩阵"""
    # 这里应该基于实际的用户行为数据计算关联性
    # 暂时返回模拟数据
    features = [f.value for f in FeatureType]
    
    correlation_matrix = {}
    for feature1 in features:
        correlation_matrix[feature1] = {}
        for feature2 in features:
            if feature1 == feature2:
                correlation_matrix[feature1][feature2] = 1.0
            else:
                # 模拟关联性数据
                correlation_matrix[feature1][feature2] = round(hash(f"{feature1}_{feature2}") % 50 / 100, 2)
    
    return correlation_matrix


def _identify_usage_patterns(feature_metrics: List[FeatureUsageMetrics]) -> List[Dict[str, Any]]:
    """识别功能使用模式"""
    patterns = []
    
    # 识别高频使用功能
    high_usage_features = [f for f in feature_metrics if f.usage_count > 100]
    if high_usage_features:
        patterns.append({
            "type": "high_usage",
            "description": "高频使用功能",
            "features": [f.feature.value for f in high_usage_features]
        })
    
    # 识别高转化功能
    high_conversion_features = [f for f in feature_metrics if f.conversion_rate > 0.8]
    if high_conversion_features:
        patterns.append({
            "type": "high_conversion",
            "description": "高转化率功能",
            "features": [f.feature.value for f in high_conversion_features]
        })
    
    # 识别长会话功能
    long_session_features = [f for f in feature_metrics if f.avg_session_duration > 300]
    if long_session_features:
        patterns.append({
            "type": "deep_engagement",
            "description": "深度参与功能",
            "features": [f.feature.value for f in long_session_features]
        })
    
    return patterns


def _generate_feature_recommendations(patterns: List[Dict[str, Any]]) -> List[str]:
    """生成功能优化建议"""
    recommendations = []
    
    for pattern in patterns:
        if pattern["type"] == "high_usage":
            recommendations.append(f"重点优化 {', '.join(pattern['features'])} 的性能和用户体验")
        elif pattern["type"] == "high_conversion":
            recommendations.append(f"推广 {', '.join(pattern['features'])} 功能，提高整体转化率")
        elif pattern["type"] == "deep_engagement":
            recommendations.append(f"增强 {', '.join(pattern['features'])} 功能的粘性设计")
    
    # 通用建议
    recommendations.append("定期分析功能使用数据，持续优化产品策略")
    
    return recommendations
