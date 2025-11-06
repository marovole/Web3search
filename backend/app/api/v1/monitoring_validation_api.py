"""
监控体系验证API
提供监控系统验证、健康检查和验证报告查询的REST API接口
"""
from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import json

from app.core.monitoring_validator import (
    monitoring_validator, ValidationStatus
)
from app.core.config import settings
from app.api.deps import get_current_user, require_admin
from app.models.user import User

router = APIRouter(prefix="/monitoring-validation", tags=["Monitoring Validation"])


# ================================
# Pydantic模型定义
# ================================

class ValidationResultResponse(BaseModel):
    """验证结果响应"""
    test_name: str
    status: str
    message: str
    details: Dict[str, Any] = {}
    execution_time: float
    timestamp: str


class ValidationReportResponse(BaseModel):
    """验证报告响应"""
    validation_id: str
    timestamp: str
    overall_status: str
    execution_time: float
    summary: Dict[str, Any]
    results: List[ValidationResultResponse]
    recommendations: List[str]
    next_steps: List[str]


class ValidationHistoryResponse(BaseModel):
    """验证历史响应"""
    validation_id: str
    timestamp: str
    overall_status: str
    execution_time: float
    summary: Dict[str, Any]


class SystemHealthResponse(BaseModel):
    """系统健康响应"""
    overall_health: str
    health_score: float
    component_status: Dict[str, str]
    last_validation: Optional[str] = None
    active_issues: List[str]
    recommendations: List[str]


# ================================
# 验证执行API
# ================================

@router.post("/run-validation")
async def run_monitoring_validation(
    background_tasks: BackgroundTasks,
    full_validation: bool = Query(default=True, description="是否运行完整验证"),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    运行监控系统验证
    """
    try:
        await monitoring_validator.initialize()
        
        if full_validation:
            # 在后台运行完整验证
            validation_id = f"validation_{int(datetime.now().timestamp())}"
            
            background_tasks.add_task(
                _run_full_validation_background,
                validation_id
            )
            
            return {
                "message": "Full monitoring system validation started in background",
                "validation_id": validation_id,
                "estimated_duration": "5-10 minutes",
                "status": "running"
            }
        
        else:
            # 运行快速验证
            quick_report = await _run_quick_validation()
            
            return {
                "message": "Quick validation completed",
                "validation_id": quick_report.get("validation_id"),
                "report": quick_report
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start validation: {str(e)}")


@router.get("/validation-status/{validation_id}")
async def get_validation_status(
    validation_id: str,
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取验证状态
    """
    try:
        from app.core.redis_client import get_redis_client
        
        redis_client = get_redis_client()
        validation_key = f"monitoring_validation:{validation_id}"
        
        validation_data = await redis_client.get(validation_key)
        
        if not validation_data:
            raise HTTPException(status_code=404, detail=f"Validation {validation_id} not found")
        
        report = json.loads(validation_data)
        
        return {
            "validation_id": validation_id,
            "status": report.get("overall_status", "unknown"),
            "timestamp": report.get("timestamp"),
            "execution_time": report.get("execution_time", 0),
            "summary": report.get("summary", {}),
            "is_completed": report.get("overall_status") in ["passed", "failed", "warning"]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get validation status: {str(e)}")


@router.get("/validation-report/{validation_id}")
async def get_validation_report(
    validation_id: str,
    current_user: User = Depends(require_admin)
) -> ValidationReportResponse:
    """
    获取详细的验证报告
    """
    try:
        from app.core.redis_client import get_redis_client
        
        redis_client = get_redis_client()
        validation_key = f"monitoring_validation:{validation_id}"
        
        validation_data = await redis_client.get(validation_key)
        
        if not validation_data:
            raise HTTPException(status_code=404, detail=f"Validation {validation_id} not found")
        
        report = json.loads(validation_data)
        
        # 格式化验证结果
        formatted_results = []
        for result in report.get("results", []):
            formatted_result = ValidationResultResponse(**result)
            formatted_results.append(formatted_result.dict())
        
        return ValidationReportResponse(
            validation_id=report["validation_id"],
            timestamp=report["timestamp"],
            overall_status=report["overall_status"],
            execution_time=report["execution_time"],
            summary=report["summary"],
            results=formatted_results,
            recommendations=report.get("recommendations", []),
            next_steps=report.get("next_steps", [])
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get validation report: {str(e)}")


# ================================
# 验证历史API
# ================================

@router.get("/validation-history")
async def get_validation_history(
    days: int = Query(default=30, ge=1, le=90, description="查询天数"),
    status: Optional[str] = Query(None, pattern="^(passed|failed|warning|all)$", description="状态过滤"),
    limit: int = Query(default=20, ge=1, le=100, description="返回数量限制"),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取验证历史记录
    """
    try:
        history = await monitoring_validator.get_validation_history(limit=100)
        
        # 过滤历史记录
        if status and status != "all":
            history = [h for h in history if h.get("overall_status") == status]
        
        # 时间过滤
        cutoff_date = datetime.now() - timedelta(days=days)
        filtered_history = []
        
        for record in history:
            try:
                record_date = datetime.fromisoformat(record.get("timestamp", "").replace('Z', '+00:00'))
                if record_date >= cutoff_date:
                    filtered_history.append(record)
            except ValueError:
                continue
        
        # 限制返回数量
        filtered_history = filtered_history[:limit]
        
        # 格式化响应
        formatted_history = []
        for record in filtered_history:
            formatted_record = ValidationHistoryResponse(
                validation_id=record["validation_id"],
                timestamp=record["timestamp"],
                overall_status=record["overall_status"],
                execution_time=record["execution_time"],
                summary=record["summary"]
            )
            formatted_history.append(formatted_record.dict())
        
        # 统计信息
        total_records = len(formatted_history)
        passed_count = len([h for h in formatted_history if h["overall_status"] == "passed"])
        failed_count = len([h for h in formatted_history if h["overall_status"] == "failed"])
        warning_count = len([h for h in formatted_history if h["overall_status"] == "warning"])
        
        return {
            "history": formatted_history,
            "statistics": {
                "total_records": total_records,
                "passed": passed_count,
                "failed": failed_count,
                "warnings": warning_count,
                "success_rate": round((passed_count / total_records) * 100, 2) if total_records > 0 else 0
            },
            "filters": {
                "days": days,
                "status": status,
                "limit": limit
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get validation history: {str(e)}")


@router.get("/validation-trends")
async def get_validation_trends(
    days: int = Query(default=30, ge=7, le=90, description="分析天数"),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取验证趋势分析
    """
    try:
        history = await monitoring_validator.get_validation_history(limit=200)
        
        # 时间过滤
        cutoff_date = datetime.now() - timedelta(days=days)
        filtered_history = []
        
        for record in history:
            try:
                record_date = datetime.fromisoformat(record.get("timestamp", "").replace('Z', '+00:00'))
                if record_date >= cutoff_date:
                    filtered_history.append(record)
            except ValueError:
                continue
        
        if not filtered_history:
            return {
                "trends": {},
                "analysis": "No validation data available for the specified period"
            }
        
        # 按日期分组统计
        daily_stats = {}
        
        for record in filtered_history:
            date = record["timestamp"][:10]  # 提取日期部分
            
            if date not in daily_stats:
                daily_stats[date] = {
                    "total": 0,
                    "passed": 0,
                    "failed": 0,
                    "warnings": 0
                }
            
            daily_stats[date]["total"] += 1
            daily_stats[date][record["overall_status"]] += 1
        
        # 计算趋势
        dates = sorted(daily_stats.keys())
        trend_data = []
        
        for date in dates:
            stats = daily_stats[date]
            success_rate = (stats["passed"] / stats["total"]) * 100 if stats["total"] > 0 else 0
            
            trend_data.append({
                "date": date,
                "total_validations": stats["total"],
                "success_rate": round(success_rate, 2),
                "passed": stats["passed"],
                "failed": stats["failed"],
                "warnings": stats["warnings"]
            })
        
        # 计算整体趋势
        if len(trend_data) >= 2:
            recent_success_rate = trend_data[-1]["success_rate"]
            previous_success_rate = trend_data[-2]["success_rate"]
            
            if recent_success_rate > previous_success_rate:
                trend_direction = "improving"
            elif recent_success_rate < previous_success_rate:
                trend_direction = "declining"
            else:
                trend_direction = "stable"
        else:
            trend_direction = "insufficient_data"
        
        # 识别常见问题
        common_failures = {}
        for record in filtered_history:
            if record["overall_status"] == "failed":
                for result in record.get("results", []):
                    if result.get("status") == "failed":
                        test_name = result.get("test_name", "unknown")
                        common_failures[test_name] = common_failures.get(test_name, 0) + 1
        
        top_failures = sorted(common_failures.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "trends": {
                "direction": trend_direction,
                "daily_data": trend_data,
                "period_days": days
            },
            "analysis": {
                "total_validations": len(filtered_history),
                "overall_success_rate": round(sum(d["success_rate"] for d in trend_data) / len(trend_data), 2) if trend_data else 0,
                "most_common_failures": [{"test": test, "count": count} for test, count in top_failures]
            },
            "recommendations": _generate_trend_recommendations(trend_direction, top_failures)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get validation trends: {str(e)}")


# ================================
# 系统健康API
# ================================

@router.get("/system-health")
async def get_system_health(
    include_details: bool = Query(default=False, description="是否包含详细信息"),
    current_user: User = Depends(require_admin)
) -> SystemHealthResponse:
    """
    获取系统健康状态
    """
    try:
        # 获取最近的验证结果
        history = await monitoring_validator.get_validation_history(limit=1)
        
        if not history:
            return SystemHealthResponse(
                overall_health="unknown",
                health_score=0.0,
                component_status={},
                active_issues=["No validation data available"],
                recommendations=["Run initial system validation"]
            )
        
        latest_validation = history[0]
        
        # 计算健康评分
        summary = latest_validation.get("summary", {})
        total_tests = summary.get("total_tests", 0)
        passed_tests = summary.get("passed", 0)
        
        health_score = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # 确定整体健康状态
        if health_score >= 90:
            overall_health = "excellent"
        elif health_score >= 75:
            overall_health = "good"
        elif health_score >= 60:
            overall_health = "warning"
        else:
            overall_health = "critical"
        
        # 组件状态
        component_status = {}
        active_issues = []
        
        for result in latest_validation.get("results", []):
            test_name = result.get("test_name", "unknown")
            status = result.get("status", "unknown")
            
            component_status[test_name] = status
            
            if status == "failed":
                active_issues.append(f"{test_name}: {result.get('message', 'Unknown error')}")
            elif status == "warning":
                active_issues.append(f"{test_name}: {result.get('message', 'Warning condition')}")
        
        # 生成建议
        recommendations = latest_validation.get("recommendations", [])
        
        if not recommendations:
            if overall_health == "excellent":
                recommendations = ["System is operating optimally", "Continue regular monitoring"]
            elif overall_health == "good":
                recommendations = ["System is performing well", "Monitor warning conditions"]
            else:
                recommendations = ["System needs attention", "Address failed components immediately"]
        
        response = SystemHealthResponse(
            overall_health=overall_health,
            health_score=round(health_score, 2),
            component_status=component_status,
            last_validation=latest_validation.get("timestamp"),
            active_issues=active_issues,
            recommendations=recommendations
        )
        
        return response
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system health: {str(e)}")


@router.get("/health-check")
async def quick_health_check(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    快速健康检查
    """
    try:
        health_checks = {
            "infrastructure_monitor": False,
            "database_monitor": False,
            "network_storage_monitor": False,
            "recovery_manager": False,
            "alerting_system": False,
            "data_storage": False
        }
        
        # 检查各个组件状态
        try:
            from app.core.infrastructure_monitor import resource_monitor
            health_checks["infrastructure_monitor"] = resource_monitor.running
        except:
            pass
        
        try:
            from app.core.database_monitor import database_monitor
            health_checks["database_monitor"] = database_monitor.running
        except:
            pass
        
        try:
            from app.core.network_storage_monitor import network_storage_monitor
            health_checks["network_storage_monitor"] = network_storage_monitor.running
        except:
            pass
        
        try:
            from app.core.infrastructure_recovery import infrastructure_recovery_manager
            health_checks["recovery_manager"] = infrastructure_recovery_manager.running
        except:
            pass
        
        try:
            from app.core.redis_client import get_redis_client
            redis_client = get_redis_client()
            await redis_client.ping()
            health_checks["data_storage"] = True
        except:
            pass
        
        try:
            from app.core.alerting_system import alert_manager
            # 简单检查告警系统是否可用
            health_checks["alerting_system"] = True
        except:
            pass
        
        # 计算整体健康状态
        healthy_components = sum(health_checks.values())
        total_components = len(health_checks)
        health_percentage = (healthy_components / total_components) * 100
        
        if health_percentage >= 90:
            status = "healthy"
        elif health_percentage >= 70:
            status = "degraded"
        else:
            status = "unhealthy"
        
        return {
            "status": status,
            "health_percentage": round(health_percentage, 2),
            "components": health_checks,
            "healthy_components": healthy_components,
            "total_components": total_components,
            "timestamp": datetime.now().isoformat(),
            "recommendations": _generate_quick_health_recommendations(health_checks, status)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to perform health check: {str(e)}")


# ================================
# 配置和维护API
# ================================

@router.get("/validation-config")
async def get_validation_config(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取验证配置
    """
    try:
        config = {
            "validation_settings": {
                "timeout_seconds": 300,
                "component_timeout": 60,
                "performance_thresholds": {
                    "api_response_time": 2.0,
                    "metric_collection_time": 5.0,
                    "alert_creation_time": 10.0
                }
            },
            "schedule": {
                "recommended_frequency": "weekly",
                "automatic_validation": False,
                "validation_window": "maintenance_hours"
            },
            "notification": {
                "alert_on_failure": True,
                "alert_on_warning": True,
                "report_recipients": ["admin_team"]
            }
        }
        
        return config
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get validation config: {str(e)}")


@router.post("/schedule-validation")
async def schedule_validation(
    schedule_config: Dict[str, Any] = Body(...),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    调度定期验证（示例实现）
    """
    try:
        # 这里应该实现调度逻辑
        # 为了演示，我们只返回确认信息
        
        return {
            "message": "Validation scheduling request received",
            "schedule": schedule_config,
            "note": "This is a placeholder implementation. In production, integrate with your job scheduler."
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to schedule validation: {str(e)}")


# ================================
# 辅助函数
# ================================

async def _run_full_validation_background(validation_id: str):
    """后台运行完整验证"""
    try:
        await monitoring_validator.initialize()
        report = await monitoring_validator.run_full_validation()
        
        # 更新验证状态
        from app.core.redis_client import get_redis_client
        redis_client = get_redis_client()
        
        status_key = f"monitoring_validation_status:{validation_id}"
        await redis_client.setex(
            status_key,
            3600,  # 1小时过期
            json.dumps({
                "validation_id": validation_id,
                "status": "completed",
                "report_id": report.get("validation_id"),
                "timestamp": datetime.now().isoformat()
            })
        )
        
        logger.info(f"Background validation {validation_id} completed")
    
    except Exception as e:
        logger.error(f"Background validation {validation_id} failed: {e}")
        
        # 更新失败状态
        try:
            from app.core.redis_client import get_redis_client
            redis_client = get_redis_client()
            
            status_key = f"monitoring_validation_status:{validation_id}"
            await redis_client.setex(
                status_key,
                3600,
                json.dumps({
                    "validation_id": validation_id,
                    "status": "failed",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
            )
        except:
            pass


async def _run_quick_validation() -> Dict[str, Any]:
    """运行快速验证"""
    try:
        await monitoring_validator.initialize()
        
        # 只运行关键检查
        quick_checks = []
        
        # 检查基础设施监控
        try:
            from app.core.infrastructure_monitor import resource_monitor
            if resource_monitor.running:
                quick_checks.append({
                    "test_name": "infrastructure_monitor_quick",
                    "status": "passed",
                    "message": "Infrastructure monitor is running"
                })
            else:
                quick_checks.append({
                    "test_name": "infrastructure_monitor_quick",
                    "status": "failed",
                    "message": "Infrastructure monitor is not running"
                })
        except Exception as e:
            quick_checks.append({
                "test_name": "infrastructure_monitor_quick",
                "status": "failed",
                "message": f"Error checking infrastructure monitor: {str(e)}"
            })
        
        # 检查数据存储
        try:
            from app.core.redis_client import get_redis_client
            redis_client = get_redis_client()
            await redis_client.ping()
            quick_checks.append({
                "test_name": "data_storage_quick",
                "status": "passed",
                "message": "Data storage (Redis) is accessible"
            })
        except Exception as e:
            quick_checks.append({
                "test_name": "data_storage_quick",
                "status": "failed",
                "message": f"Data storage not accessible: {str(e)}"
            })
        
        # 生成快速报告
        total_checks = len(quick_checks)
        passed_checks = len([c for c in quick_checks if c["status"] == "passed"])
        
        overall_status = "passed" if passed_checks == total_checks else "failed"
        
        return {
            "validation_id": f"quick_validation_{int(datetime.now().timestamp())}",
            "timestamp": datetime.now().isoformat(),
            "overall_status": overall_status,
            "execution_time": 5.0,  # 估算时间
            "summary": {
                "total_tests": total_checks,
                "passed": passed_checks,
                "failed": total_checks - passed_checks,
                "warnings": 0,
                "success_rate": (passed_checks / total_checks) * 100 if total_checks > 0 else 0
            },
            "results": quick_checks,
            "recommendations": ["Run full validation for detailed analysis"] if overall_status == "passed" else ["Address failed components immediately"]
        }
    
    except Exception as e:
        return {
            "validation_id": f"quick_validation_error_{int(datetime.now().timestamp())}",
            "timestamp": datetime.now().isoformat(),
            "overall_status": "failed",
            "execution_time": 0,
            "error": str(e)
        }


def _generate_trend_recommendations(trend_direction: str, top_failures: List[tuple]) -> List[str]:
    """生成趋势建议"""
    recommendations = []
    
    if trend_direction == "declining":
        recommendations.append("System validation success rate is declining, investigate root causes")
        recommendations.append("Review recent changes that may have affected monitoring components")
    elif trend_direction == "improving":
        recommendations.append("System validation success rate is improving, continue current practices")
    else:
        recommendations.append("System validation success rate is stable, maintain current configuration")
    
    if top_failures:
        recommendations.append(f"Focus on fixing most common failure: {top_failures[0][0]}")
    
    recommendations.append("Schedule regular maintenance to prevent degradation")
    
    return recommendations


def _generate_quick_health_recommendations(health_checks: Dict[str, bool], status: str) -> List[str]:
    """生成快速健康检查建议"""
    recommendations = []
    
    if status == "unhealthy":
        recommendations.append("Multiple components are down, immediate attention required")
        
        for component, is_healthy in health_checks.items():
            if not is_healthy:
                recommendations.append(f"Check and restart {component}")
    
    elif status == "degraded":
        recommendations.append("Some components are not performing optimally")
        
        unhealthy_components = [comp for comp, healthy in health_checks.items() if not healthy]
        if unhealthy_components:
            recommendations.append(f"Review: {', '.join(unhealthy_components)}")
    
    else:
        recommendations.append("All components are healthy")
        recommendations.append("Continue regular monitoring")
    
    return recommendations
