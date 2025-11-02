"""
漏斗分析和转化率监控API
提供用户行为漏斗分析和转化率监控的可视化接口
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio

from app.core.funnel_analyzer import (
    funnel_analyzer, 
    FunnelType, 
    FunnelStage, 
    FunnelAnalysis
)
from app.core.conversion_monitor import (
    conversion_monitor,
    ConversionEventType,
    ConversionAnalysis
)
from app.api.deps import get_current_user, require_admin
from app.models.user import User

router = APIRouter(prefix="/analytics", tags=["Funnel & Conversion Analytics"])


@router.get("/funnel/overview")
async def get_funnel_overview(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取所有漏斗的概览
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        # 分析所有类型的漏斗
        funnel_analyses = {}
        
        for funnel_type in FunnelType:
            try:
                analysis = await funnel_analyzer.analyze_funnel(
                    funnel_type=funnel_type,
                    start_date=start_date,
                    end_date=end_date
                )
                
                funnel_analyses[funnel_type.value] = {
                    "total_users": analysis.total_users,
                    "overall_conversion_rate": analysis.overall_conversion_rate,
                    "stage_count": len(analysis.stages),
                    "top_dropoff_stage": None,
                    "insights_count": len(analysis.insights)
                }
                
                # 找出最大流失点
                if len(analysis.stages) > 1:
                    max_dropoff = max(analysis.stages[1:], key=lambda x: x.dropoff_rate)
                    funnel_analyses[funnel_type.value]["top_dropoff_stage"] = {
                        "stage": max_dropoff.stage.value,
                        "dropoff_rate": max_dropoff.dropoff_rate
                    }
                
            except Exception as e:
                funnel_analyses[funnel_type.value] = {
                    "error": str(e),
                    "total_users": 0,
                    "overall_conversion_rate": 0.0
                }
        
        # 计算整体健康状况
        total_funnels = len(funnel_analyses)
        healthy_funnels = len([f for f in funnel_analyses.values() if f.get("overall_conversion_rate", 0) > 0.1])
        
        return {
            "time_period": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            "summary": {
                "total_funnels": total_funnels,
                "healthy_funnels": healthy_funnels,
                "health_score": (healthy_funnels / total_funnels) * 100 if total_funnels > 0 else 0
            },
            "funnels": funnel_analyses
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get funnel overview: {str(e)}")


@router.get("/funnel/{funnel_type}")
async def get_funnel_analysis(
    funnel_type: str,
    start_date: str = Query(None, description="开始日期 (YYYY-MM-DD格式)"),
    end_date: str = Query(None, description="结束日期 (YYYY-MM-DD格式)"),
    user_segment: str = Query("all", description="用户分群"),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取特定漏斗的详细分析
    """
    try:
        # 验证漏斗类型
        try:
            funnel_enum = FunnelType(funnel_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid funnel type: {funnel_type}")
        
        # 解析日期
        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        else:
            start_dt = datetime.now() - timedelta(days=7)
        
        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        else:
            end_dt = datetime.now()
        
        # 分析漏斗
        analysis = await funnel_analyzer.analyze_funnel(
            funnel_type=funnel_enum,
            start_date=start_dt,
            end_date=end_dt,
            user_segment=user_segment
        )
        
        # 格式化阶段数据
        stages_data = []
        for stage in analysis.stages:
            stages_data.append({
                "stage": stage.stage.value,
                "users": stage.users,
                "conversion_rate": stage.conversion_rate,
                "dropoff_rate": stage.dropoff_rate,
                "avg_time_to_stage": stage.avg_time_to_stage,
                "stage_completion_rate": stage.stage_completion_rate
            })
        
        # 计算关键指标
        key_metrics = {
            "total_users": analysis.total_users,
            "overall_conversion_rate": analysis.overall_conversion_rate,
            "total_stages": len(analysis.stages),
            "completed_users": analysis.stages[-1].users if analysis.stages else 0,
            "avg_stage_time": sum(s.avg_time_to_stage for s in analysis.stages) / len(analysis.stages) if analysis.stages else 0
        }
        
        return {
            "funnel_type": funnel_type,
            "time_period": analysis.time_period,
            "key_metrics": key_metrics,
            "stages": stages_data,
            "insights": analysis.insights,
            "recommendations": analysis.recommendations
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get funnel analysis: {str(e)}")


@router.get("/funnel/user-progress/{user_id}")
async def get_user_funnel_progress(
    user_id: str,
    funnel_type: str,
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取特定用户在漏斗中的进度
    """
    try:
        # 验证漏斗类型
        try:
            funnel_enum = FunnelType(funnel_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid funnel type: {funnel_type}")
        
        # 获取用户进度
        progress = await funnel_analyzer.get_user_funnel_progress(user_id, funnel_enum)
        
        if not progress:
            raise HTTPException(status_code=404, detail=f"No progress found for user {user_id}")
        
        return progress
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user funnel progress: {str(e)}")


@router.get("/conversion/overview")
async def get_conversion_overview(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取转化率监控概览
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        # 分析所有转化事件
        conversion_analyses = {}
        
        for event_type in ConversionEventType:
            try:
                analysis = await conversion_monitor.analyze_conversion(
                    event_type=event_type,
                    start_date=start_date,
                    end_date=end_date
                )
                
                conversion_analyses[event_type.value] = {
                    "total_conversions": analysis.overall_metrics.total_conversions,
                    "conversion_rate": analysis.overall_metrics.conversion_rate,
                    "conversion_value": analysis.overall_metrics.conversion_value,
                    "trend_direction": analysis.overall_metrics.trend_direction,
                    "trend_percentage": analysis.overall_metrics.trend_percentage
                }
                
            except Exception as e:
                conversion_analyses[event_type.value] = {
                    "error": str(e),
                    "total_conversions": 0,
                    "conversion_rate": 0.0
                }
        
        # 计算整体转化健康状况
        total_events = len(conversion_analyses)
        healthy_events = len([c for c in conversion_analyses.values() if c.get("conversion_rate", 0) > 0.05])
        
        # 找出表现最好和最差的转化事件
        valid_conversions = {k: v for k, v in conversion_analyses.items() if "error" not in v}
        
        best_conversion = None
        worst_conversion = None
        
        if valid_conversions:
            best_conversion = max(valid_conversions.items(), key=lambda x: x[1]["conversion_rate"])
            worst_conversion = min(valid_conversions.items(), key=lambda x: x[1]["conversion_rate"])
        
        return {
            "time_period": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            "summary": {
                "total_events": total_events,
                "healthy_events": healthy_events,
                "health_score": (healthy_events / total_events) * 100 if total_events > 0 else 0,
                "best_conversion": {"event": best_conversion[0], "rate": best_conversion[1]["conversion_rate"]} if best_conversion else None,
                "worst_conversion": {"event": worst_conversion[0], "rate": worst_conversion[1]["conversion_rate"]} if worst_conversion else None
            },
            "conversions": conversion_analyses
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get conversion overview: {str(e)}")


@router.get("/conversion/{event_type}")
async def get_conversion_analysis(
    event_type: str,
    start_date: str = Query(None, description="开始日期 (YYYY-MM-DD格式)"),
    end_date: str = Query(None, description="结束日期 (YYYY-MM-DD格式)"),
    segment_by: str = Query("all", description="分群维度: all, user_type, acquisition_channel"),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取特定转化事件的详细分析
    """
    try:
        # 验证事件类型
        try:
            event_enum = ConversionEventType(event_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid conversion event type: {event_type}")
        
        # 解析日期
        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        else:
            start_dt = datetime.now() - timedelta(days=7)
        
        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        else:
            end_dt = datetime.now()
        
        # 分析转化数据
        analysis = await conversion_monitor.analyze_conversion(
            event_type=event_enum,
            start_date=start_dt,
            end_date=end_dt,
            segment_by=segment_by
        )
        
        # 格式化分群数据
        segments_data = []
        for segment in analysis.segments:
            segments_data.append({
                "segment_name": segment.segment_name,
                "segment_size": segment.segment_size,
                "conversion_rate": segment.conversion_rate,
                "conversion_count": segment.conversion_count,
                "lift_vs_baseline": segment.lift_vs_baseline
            })
        
        return {
            "event_type": event_type,
            "time_period": analysis.time_period,
            "overall_metrics": {
                "total_conversions": analysis.overall_metrics.total_conversions,
                "conversion_rate": analysis.overall_metrics.conversion_rate,
                "conversion_value": analysis.overall_metrics.conversion_value,
                "avg_time_to_convert": analysis.overall_metrics.avg_time_to_convert,
                "retention_rate": analysis.overall_metrics.retention_rate,
                "trend_direction": analysis.overall_metrics.trend_direction,
                "trend_percentage": analysis.overall_metrics.trend_percentage
            },
            "segments": segments_data,
            "trends": analysis.trends,
            "insights": analysis.insights,
            "recommendations": analysis.recommendations
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get conversion analysis: {str(e)}")


@router.get("/conversion/cohort-analysis/{event_type}")
async def get_conversion_cohort_analysis(
    event_type: str,
    cohort_days: int = Query(7, description="队列天数"),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取转化队列分析
    """
    try:
        # 验证事件类型
        try:
            event_enum = ConversionEventType(event_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid conversion event type: {event_type}")
        
        # 获取队列分析
        cohort_data = await conversion_monitor.get_conversion_cohort_analysis(event_enum, cohort_days)
        
        if not cohort_data:
            raise HTTPException(status_code=404, detail=f"No cohort data found for {event_type}")
        
        return cohort_data
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get conversion cohort analysis: {str(e)}")


@router.post("/track/funnel-event")
async def track_funnel_event(
    event_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """
    手动追踪漏斗事件
    """
    try:
        funnel_type = event_data.get("funnel_type")
        stage = event_data.get("stage")
        properties = event_data.get("properties", {})
        
        if not funnel_type or not stage:
            raise HTTPException(status_code=400, detail="funnel_type and stage are required")
        
        # 验证漏斗类型和阶段
        try:
            funnel_enum = FunnelType(funnel_type)
            stage_enum = FunnelStage(stage)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid funnel type or stage: {str(e)}")
        
        # 追踪事件
        await funnel_analyzer.track_funnel_event(
            user_id=current_user.id,
            funnel_type=funnel_enum,
            stage=stage_enum,
            properties=properties
        )
        
        return {"status": "success", "message": "Funnel event tracked successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to track funnel event: {str(e)}")


@router.post("/track/conversion-event")
async def track_conversion_event(
    event_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """
    手动追踪转化事件
    """
    try:
        event_type = event_data.get("event_type")
        properties = event_data.get("properties", {})
        conversion_value = event_data.get("conversion_value", 0.0)
        
        if not event_type:
            raise HTTPException(status_code=400, detail="event_type is required")
        
        # 验证事件类型
        try:
            event_enum = ConversionEventType(event_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid conversion event type: {event_type}")
        
        # 创建转化事件
        from app.core.conversion_monitor import ConversionEvent
        
        event = ConversionEvent(
            event_type=event_enum,
            user_id=current_user.id,
            timestamp=datetime.now(),
            properties=properties,
            conversion_value=conversion_value
        )
        
        # 追踪事件
        await conversion_monitor.track_conversion_event(event)
        
        return {"status": "success", "message": "Conversion event tracked successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to track conversion event: {str(e)}")


@router.get("/dashboard/combined")
async def get_combined_analytics_dashboard(
    start_date: str = Query(None, description="开始日期 (YYYY-MM-DD格式)"),
    end_date: str = Query(None, description="结束日期 (YYYY-MM-DD格式)"),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取综合分析Dashboard（漏斗+转化率）
    """
    try:
        # 解析日期
        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        else:
            start_dt = datetime.now() - timedelta(days=7)
        
        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        else:
            end_dt = datetime.now()
        
        # 并行获取漏斗和转化数据
        funnel_tasks = []
        for funnel_type in [FunnelType.USER_ONBOARDING, FunnelType.SEARCH_TO_CHAT, FunnelType.CHAT_TO_RESEARCH]:
            task = funnel_analyzer.analyze_funnel(funnel_type, start_dt, end_dt)
            funnel_tasks.append(task)
        
        conversion_tasks = []
        for event_type in [ConversionEventType.USER_REGISTRATION, ConversionEventType.FIRST_CHAT, ConversionEventType.REPORT_GENERATION]:
            task = conversion_monitor.analyze_conversion(event_type, start_dt, end_dt)
            conversion_tasks.append(task)
        
        # 等待所有任务完成
        funnel_results = await asyncio.gather(*funnel_tasks, return_exceptions=True)
        conversion_results = await asyncio.gather(*conversion_tasks, return_exceptions=True)
        
        # 处理结果
        funnel_data = {}
        conversion_data = {}
        
        for i, result in enumerate(funnel_results):
            if isinstance(result, Exception):
                continue
            funnel_data[result.funnel_type.value] = {
                "total_users": result.total_users,
                "conversion_rate": result.overall_conversion_rate,
                "insights": result.insights[:2]  # 只取前两个洞察
            }
        
        for i, result in enumerate(conversion_results):
            if isinstance(result, Exception):
                continue
            conversion_data[result.event_type.value] = {
                "total_conversions": result.overall_metrics.total_conversions,
                "conversion_rate": result.overall_metrics.conversion_rate,
                "trend_direction": result.overall_metrics.trend_direction
            }
        
        # 生成综合洞察
        combined_insights = []
        
        # 找出表现最好的漏斗和转化事件
        if funnel_data:
            best_funnel = max(funnel_data.items(), key=lambda x: x[1]["conversion_rate"])
            combined_insights.append(f"表现最好的漏斗：{best_funnel[0]} (转化率 {best_funnel[1]['conversion_rate']:.1%})")
        
        if conversion_data:
            best_conversion = max(conversion_data.items(), key=lambda x: x[1]["conversion_rate"])
            combined_insights.append(f"表现最好的转化事件：{best_conversion[0]} (转化率 {best_conversion[1]['conversion_rate']:.1%})")
        
        return {
            "time_period": f"{start_dt.strftime('%Y-%m-%d')} to {end_dt.strftime('%Y-%m-%d')}",
            "funnels": funnel_data,
            "conversions": conversion_data,
            "combined_insights": combined_insights,
            "summary": {
                "total_funnels_analyzed": len(funnel_data),
                "total_conversions_analyzed": len(conversion_data),
                "data_quality": "good" if len(funnel_data) > 0 and len(conversion_data) > 0 else "limited"
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get combined analytics dashboard: {str(e)}")
