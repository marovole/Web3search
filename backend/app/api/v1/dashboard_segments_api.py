"""
实时Dashboard和用户分群API
提供实时业务指标监控、Dashboard可视化和用户分群分析接口
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio

from app.core.real_time_dashboard import (
    real_time_dashboard, 
    DashboardTimeRange, 
    RealTimeMetric,
    DashboardSnapshot
)
from app.core.user_segment_analyzer import (
    user_segment_analyzer,
    UserSegmentType,
    UserBehaviorProfile,
    SegmentAnalysis,
    BehaviorInsight
)
from app.api.deps import get_current_user, require_admin
from app.models.user import User

router = APIRouter(prefix="/dashboard", tags=["Real-time Dashboard & User Segments"])


@router.get("/overview")
async def get_dashboard_overview(
    time_range: DashboardTimeRange = Query(DashboardTimeRange.LAST_24H, description="时间范围"),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取Dashboard概览
    """
    try:
        # 获取Dashboard快照
        snapshot = await real_time_dashboard.get_dashboard_snapshot("main", time_range)
        
        # 获取实时指标
        real_time_metrics = await real_time_dashboard.get_real_time_metrics()
        
        # 获取关键洞察
        key_insights = snapshot.insights[:5]  # 取前5个最重要的洞察
        
        return {
            "time_range": time_range.value,
            "generated_at": snapshot.generated_at.isoformat(),
            "summary": snapshot.summary,
            "real_time_metrics": [
                {
                    "name": metric.name,
                    "value": metric.value,
                    "unit": metric.unit,
                    "trend": metric.trend,
                    "trend_percentage": metric.trend_percentage,
                    "alert_level": metric.alert_level.value,
                    "timestamp": metric.timestamp.isoformat()
                }
                for metric in real_time_metrics
            ],
            "key_insights": [
                {
                    "id": insight.insight_id,
                    "title": insight.title,
                    "description": insight.description,
                    "severity": insight.severity.value,
                    "recommendations": insight.recommendations[:2]  # 只取前2个建议
                }
                for insight in key_insights
            ],
            "health_score": snapshot.summary.get("health_score", 0),
            "widget_count": len(snapshot.widgets)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard overview: {str(e)}")


@router.get("/snapshot")
async def get_dashboard_snapshot(
    dashboard_id: str = Query("main", description="Dashboard ID"),
    time_range: DashboardTimeRange = Query(DashboardTimeRange.LAST_24H, description="时间范围"),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取完整的Dashboard快照
    """
    try:
        snapshot = await real_time_dashboard.get_dashboard_snapshot(dashboard_id, time_range)
        
        # 格式化组件数据
        widgets_data = []
        for widget in snapshot.widgets:
            widgets_data.append({
                "widget_id": widget.widget_id,
                "widget_type": widget.widget_type,
                "title": widget.title,
                "data": widget.data,
                "position": widget.position,
                "refresh_interval": widget.refresh_interval,
                "last_updated": widget.last_updated.isoformat()
            })
        
        # 格式化洞察数据
        insights_data = []
        for insight in snapshot.insights:
            insights_data.append({
                "insight_id": insight.insight_id,
                "title": insight.title,
                "description": insight.description,
                "severity": insight.severity.value,
                "metrics": insight.metrics,
                "recommendations": insight.recommendations,
                "created_at": insight.created_at.isoformat()
            })
        
        return {
            "dashboard_id": snapshot.dashboard_id,
            "time_range": snapshot.time_range.value,
            "generated_at": snapshot.generated_at.isoformat(),
            "widgets": widgets_data,
            "insights": insights_data,
            "summary": snapshot.summary
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard snapshot: {str(e)}")


@router.get("/metrics/real-time")
async def get_real_time_metrics(
    current_user: User = Depends(require_admin)
) -> List[Dict[str, Any]]:
    """
    获取实时指标数据
    """
    try:
        metrics = await real_time_dashboard.get_real_time_metrics()
        
        return [
            {
                "name": metric.name,
                "value": metric.value,
                "unit": metric.unit,
                "timestamp": metric.timestamp.isoformat(),
                "trend": metric.trend,
                "trend_percentage": metric.trend_percentage,
                "previous_value": metric.previous_value,
                "alert_level": metric.alert_level.value
            }
            for metric in metrics
        ]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get real-time metrics: {str(e)}")


@router.get("/metrics/{metric_name}")
async def get_metric_details(
    metric_name: str,
    time_range: DashboardTimeRange = Query(DashboardTimeRange.LAST_24H, description="时间范围"),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取特定指标的详细信息
    """
    try:
        # 这里可以实现获取特定指标历史数据的逻辑
        # 暂时返回模拟数据
        
        if metric_name == "DAU":
            return {
                "metric_name": metric_name,
                "time_range": time_range.value,
                "current_value": 1056,
                "previous_value": 987,
                "trend": "up",
                "trend_percentage": 7.0,
                "historical_data": {
                    "labels": ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00"],
                    "values": [823, 756, 912, 1056, 987, 892]
                },
                "forecast": {
                    "next_period": 1120,
                    "confidence": 0.85
                }
            }
        
        elif metric_name == "Chat Usage":
            return {
                "metric_name": metric_name,
                "time_range": time_range.value,
                "current_value": 2456,
                "previous_value": 2234,
                "trend": "up",
                "trend_percentage": 9.9,
                "historical_data": {
                    "labels": ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00"],
                    "values": [1234, 987, 1876, 2456, 2234, 1987]
                },
                "breakdown": {
                    "quick_chat": 1456,
                    "deep_research": 678,
                    "follow_up": 322
                }
            }
        
        else:
            raise HTTPException(status_code=404, detail=f"Metric {metric_name} not found")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metric details: {str(e)}")


# ================================
# 用户分群API
# ================================

@router.get("/segments/overview")
async def get_segments_overview(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取用户分群概览
    """
    try:
        # 获取所有分群类型的分析
        segment_analyses = {}
        
        for segment_type in UserSegmentType:
            try:
                analysis = await user_segment_analyzer.analyze_user_segments(segment_type)
                
                segment_analyses[segment_type.value] = {
                    "total_users": analysis.total_users,
                    "segment_count": len(analysis.segments),
                    "largest_segment": {
                        "name": max(analysis.segments, key=lambda x: x.user_count).segment_name if analysis.segments else None,
                        "percentage": max(analysis.segments, key=lambda x: x.user_count).percentage if analysis.segments else 0
                    },
                    "insights_count": len(analysis.insights)
                }
                
            except Exception as e:
                segment_analyses[segment_type.value] = {
                    "error": str(e),
                    "total_users": 0,
                    "segment_count": 0
                }
        
        # 计算整体分群健康状况
        total_segment_types = len(segment_analyses)
        healthy_segment_types = len([s for s in segment_analyses.values() if s.get("segment_count", 0) > 0])
        
        return {
            "analysis_date": datetime.now().isoformat(),
            "summary": {
                "total_segment_types": total_segment_types,
                "healthy_segment_types": healthy_segment_types,
                "health_score": (healthy_segment_types / total_segment_types) * 100 if total_segment_types > 0 else 0
            },
            "segments": segment_analyses
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get segments overview: {str(e)}")


@router.get("/segments/{segment_type}")
async def get_segment_analysis(
    segment_type: str,
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取特定分群类型的详细分析
    """
    try:
        # 验证分群类型
        try:
            segment_enum = UserSegmentType(segment_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid segment type: {segment_type}")
        
        # 获取分群分析
        analysis = await user_segment_analyzer.analyze_user_segments(segment_enum)
        
        # 格式化分群数据
        segments_data = []
        for segment in analysis.segments:
            segments_data.append({
                "segment_id": segment.segment_id,
                "segment_name": segment.segment_name,
                "description": segment.description,
                "user_count": segment.user_count,
                "percentage": segment.percentage,
                "criteria": segment.criteria,
                "characteristics": segment.characteristics,
                "created_at": segment.created_at.isoformat()
            })
        
        return {
            "segment_type": segment_type,
            "analysis_date": analysis.analysis_date.isoformat(),
            "total_users": analysis.total_users,
            "segments": segments_data,
            "insights": analysis.insights,
            "recommendations": analysis.recommendations
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get segment analysis: {str(e)}")


@router.get("/segments/compare")
async def compare_segments(
    segment_types: List[str] = Query(..., description="要比较的分群类型列表"),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    比较多个分群类型
    """
    try:
        if len(segment_types) < 2:
            raise HTTPException(status_code=400, detail="At least 2 segment types required for comparison")
        
        # 验证分群类型
        valid_segments = []
        for segment_type in segment_types:
            try:
                valid_segments.append(UserSegmentType(segment_type))
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid segment type: {segment_type}")
        
        # 获取各分群类型的分析
        comparisons = {}
        
        for segment_type in valid_segments:
            analysis = await user_segment_analyzer.analyze_user_segments(segment_type)
            
            # 提取关键比较数据
            segment_comparison = {}
            for segment in analysis.segments:
                segment_comparison[segment.segment_name] = {
                    "user_count": segment.user_count,
                    "percentage": segment.percentage,
                    "characteristics": segment.characteristics[:3]  # 只取前3个特征
                }
            
            comparisons[segment_type.value] = segment_comparison
        
        # 生成交叉分析洞察
        cross_insights = await self._generate_cross_segment_insights(comparisons)
        
        return {
            "compared_segments": [s.value for s in valid_segments],
            "analysis_date": datetime.now().isoformat(),
            "comparisons": comparisons,
            "cross_insights": cross_insights
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compare segments: {str(e)}")


@router.get("/users/{user_id}/profile")
async def get_user_behavior_profile(
    user_id: str,
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取用户行为画像
    """
    try:
        profile = await user_segment_analyzer.get_user_behavior_profile(user_id)
        
        if not profile:
            raise HTTPException(status_code=404, detail=f"User profile not found for {user_id}")
        
        return {
            "user_id": profile.user_id,
            "activity_level": profile.activity_level.value,
            "engagement_level": profile.engagement_level.value,
            "lifecycle_stage": profile.lifecycle_stage.value,
            "behavior_pattern": profile.behavior_pattern.value,
            "preferred_features": profile.preferred_features,
            "usage_frequency": profile.usage_frequency,
            "session_patterns": profile.session_patterns,
            "conversion_propensity": profile.conversion_propensity,
            "churn_risk": profile.churn_risk,
            "last_updated": profile.last_updated.isoformat(),
            "risk_assessment": {
                "churn_risk_level": "high" if profile.churn_risk > 0.7 else "medium" if profile.churn_risk > 0.3 else "low",
                "conversion_potential": "high" if profile.conversion_propensity > 0.6 else "medium" if profile.conversion_propensity > 0.3 else "low"
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user behavior profile: {str(e)}")


@router.get("/insights/behavior")
async def get_behavior_insights(
    segment_types: List[str] = Query(None, description="分群类型过滤"),
    impact_level: str = Query(None, description="影响程度过滤: high, medium, low"),
    actionable_only: bool = Query(False, description="只显示可操作的洞察"),
    current_user: User = Depends(require_admin)
) -> List[Dict[str, Any]]:
    """
    获取行为洞察
    """
    try:
        # 解析分群类型过滤
        segment_filter = None
        if segment_types:
            segment_filter = []
            for segment_type in segment_types:
                try:
                    segment_filter.append(UserSegmentType(segment_type))
                except ValueError:
                    continue
        
        # 获取行为洞察
        insights = await user_segment_analyzer.get_behavior_insights(segment_filter)
        
        # 应用过滤条件
        filtered_insights = []
        for insight in insights:
            # 影响程度过滤
            if impact_level and insight.impact_level != impact_level:
                continue
            
            # 可操作性过滤
            if actionable_only and not insight.actionable:
                continue
            
            filtered_insights.append(insight)
        
        # 格式化返回数据
        return [
            {
                "insight_id": insight.insight_id,
                "title": insight.title,
                "description": insight.description,
                "affected_segments": insight.affected_segments,
                "impact_level": insight.impact_level,
                "actionable": insight.actionable,
                "recommendations": insight.recommendations,
                "created_at": insight.created_at.isoformat()
            }
            for insight in filtered_insights
        ]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get behavior insights: {str(e)}")


@router.get("/recommendations/personalized/{user_id}")
async def get_personalized_recommendations(
    user_id: str,
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取个性化推荐
    """
    try:
        # 获取用户行为画像
        profile = await user_segment_analyzer.get_user_behavior_profile(user_id)
        
        if not profile:
            raise HTTPException(status_code=404, detail=f"User profile not found for {user_id}")
        
        # 基于用户画像生成个性化推荐
        recommendations = await self._generate_personalized_recommendations(profile)
        
        return {
            "user_id": user_id,
            "profile_summary": {
                "activity_level": profile.activity_level.value,
                "behavior_pattern": profile.behavior_pattern.value,
                "churn_risk": profile.churn_risk,
                "conversion_propensity": profile.conversion_propensity
            },
            "recommendations": recommendations,
            "generated_at": datetime.now().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get personalized recommendations: {str(e)}")


@router.post("/segments/refresh")
async def refresh_segments(
    segment_type: str = Query(None, description="要刷新的分群类型，不指定则刷新所有"),
    current_user: User = Depends(require_admin)
) -> Dict[str, str]:
    """
    刷新用户分群数据
    """
    try:
        if segment_type:
            # 验证分群类型
            try:
                segment_enum = UserSegmentType(segment_type)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid segment type: {segment_type}")
            
            # 刷新特定分群
            await user_segment_analyzer.analyze_user_segments(segment_enum)
            return {"status": "success", "message": f"Segment {segment_type} refreshed successfully"}
        else:
            # 刷新所有分群
            await user_segment_analyzer._update_user_segments()
            return {"status": "success", "message": "All segments refreshed successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refresh segments: {str(e)}")


@router.get("/health")
async def get_dashboard_health(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取Dashboard系统健康状态
    """
    try:
        # 检查实时Dashboard状态
        dashboard_status = {
            "running": real_time_dashboard.running,
            "update_interval": real_time_dashboard.update_interval,
            "last_update": "unknown"  # 这里可以添加实际的最后更新时间
        }
        
        # 检查用户分群分析器状态
        segment_analyzer_status = {
            "running": user_segment_analyzer.running,
            "analysis_interval": user_segment_analyzer.analysis_interval,
            "last_analysis": "unknown"  # 这里可以添加实际的分析时间
        }
        
        # 获取系统指标
        real_time_metrics = await real_time_dashboard.get_real_time_metrics()
        
        # 计算健康度评分
        health_score = 100.0
        
        # 检查关键指标
        for metric in real_time_metrics:
            if metric.alert_level.value == "critical":
                health_score -= 20
            elif metric.alert_level.value == "warning":
                health_score -= 10
        
        # 检查服务状态
        if not dashboard_status["running"]:
            health_score -= 30
        if not segment_analyzer_status["running"]:
            health_score -= 20
        
        health_score = max(0.0, health_score)
        
        return {
            "overall_health": "healthy" if health_score >= 80 else "warning" if health_score >= 60 else "critical",
            "health_score": health_score,
            "services": {
                "real_time_dashboard": dashboard_status,
                "user_segment_analyzer": segment_analyzer_status
            },
            "alerts": [
                {
                    "metric": metric.name,
                    "level": metric.alert_level.value,
                    "message": f"{metric.name} is {metric.alert_level.value}"
                }
                for metric in real_time_metrics if metric.alert_level.value != "info"
            ],
            "last_check": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard health: {str(e)}")


# ================================
# 辅助方法
# ================================

async def _generate_cross_segment_insights(comparisons: Dict[str, Dict[str, Any]]) -> List[str]:
    """生成交叉分群洞察"""
    insights = []
    
    try:
        # 分析不同分群类型的相关性
        if len(comparisons) >= 2:
            insights.append("用户在不同分群维度中表现出一定的相关性特征")
            insights.append("建议结合多个分群维度制定更精准的运营策略")
        
        # 识别异常模式
        for segment_type, segments in comparisons.items():
            max_percentage = max([s["percentage"] for s in segments.values()]) if segments else 0
            if max_percentage > 60:
                insights.append(f"{segment_type}分群中存在主导分群(占比>60%)，需要注意用户多样性")
        
    except Exception as e:
        logger.error(f"Error generating cross segment insights: {e}")
    
    return insights


async def _generate_personalized_recommendations(profile: UserBehaviorProfile) -> List[Dict[str, Any]]:
    """生成个性化推荐"""
    recommendations = []
    
    try:
        # 基于活跃度的推荐
        if profile.activity_level.value == "dormant_user":
            recommendations.append({
                "type": "reactivation",
                "title": "重新激活建议",
                "description": "您已经有一段时间没有使用我们的服务了",
                "actions": ["查看新功能", "参与限时活动", "联系客服获取帮助"],
                "priority": "high"
            })
        elif profile.activity_level.value == "power_user":
            recommendations.append({
                "type": "advanced_features",
                "title": "高级功能推荐",
                "description": "作为我们的重度用户，您可能对这些高级功能感兴趣",
                "actions": ["尝试深度研究功能", "使用批量分析", "定制个人工作流"],
                "priority": "medium"
            })
        
        # 基于行为模式的推荐
        if profile.behavior_pattern.value == "research_focused":
            recommendations.append({
                "type": "research_tools",
                "title": "研究工具推荐",
                "description": "基于您的研究偏好，推荐以下工具",
                "actions": ["使用高级搜索过滤器", "创建研究模板", "导出详细报告"],
                "priority": "medium"
            })
        elif profile.behavior_pattern.value == "quick_chat":
            recommendations.append({
                "type": "efficiency_tools",
                "title": "效率工具推荐",
                "description": "提升您的聊天效率",
                "actions": ["使用快捷回复", "保存常用查询", "设置自动提醒"],
                "priority": "low"
            })
        
        # 基于流失风险的推荐
        if profile.churn_risk > 0.7:
            recommendations.append({
                "type": "retention",
                "title": "留存建议",
                "description": "我们注意到您可能遇到一些问题",
                "actions": ["查看使用教程", "联系产品团队", "参与用户调研"],
                "priority": "high"
            })
        
        # 基于转化倾向的推荐
        if profile.conversion_propensity > 0.6:
            recommendations.append({
                "type": "conversion",
                "title": "升级建议",
                "description": "您可能对我们的高级服务感兴趣",
                "actions": ["了解付费功能", "申请免费试用", "查看成功案例"],
                "priority": "medium"
            })
    
    except Exception as e:
        logger.error(f"Error generating personalized recommendations: {e}")
    
    return recommendations
