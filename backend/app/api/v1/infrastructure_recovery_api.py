"""
基础设施恢复管理API
提供自动化恢复规则管理和执行记录查询的REST API接口
"""
from fastapi import APIRouter, HTTPException, Query, Depends, Body
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import json

from app.core.infrastructure_recovery import (
    infrastructure_recovery_manager, RecoveryRule, RecoveryAction, RecoveryStatus
)
from app.core.config import settings
from app.api.deps import get_current_user, require_admin
from app.models.user import User

router = APIRouter(prefix="/infrastructure-recovery", tags=["Infrastructure Recovery"])


# ================================
# Pydantic模型定义
# ================================

class RecoveryRuleRequest(BaseModel):
    """恢复规则请求"""
    rule_id: str = Field(..., description="规则ID")
    name: str = Field(..., description="规则名称")
    description: str = Field(..., description="规则描述")
    trigger_condition: Dict[str, Any] = Field(..., description="触发条件")
    recovery_actions: List[Dict[str, Any]] = Field(..., description="恢复动作列表")
    enabled: bool = Field(default=True, description="是否启用")
    cooldown_minutes: int = Field(default=30, ge=1, le=1440, description="冷却时间（分钟）")
    max_attempts: int = Field(default=3, ge=1, le=10, description="最大尝试次数")
    escalation_enabled: bool = Field(default=True, description="是否启用升级")


class RecoveryRuleResponse(BaseModel):
    """恢复规则响应"""
    rule_id: str
    name: str
    description: str
    trigger_condition: Dict[str, Any]
    recovery_actions: List[Dict[str, Any]]
    enabled: bool
    cooldown_minutes: int
    max_attempts: int
    escalation_enabled: bool


class RecoveryExecutionResponse(BaseModel):
    """恢复执行记录响应"""
    execution_id: str
    rule_id: str
    alert_id: str
    actions: List[Dict[str, Any]]
    status: str
    started_at: str
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    execution_log: List[str]
    duration_seconds: Optional[float] = None


class RecoveryStatisticsResponse(BaseModel):
    """恢复统计响应"""
    total_rules: int
    enabled_rules: int
    total_executions: int
    success_executions: int
    failed_executions: int
    success_rate: float
    average_execution_time: float
    most_triggered_rules: List[Dict[str, Any]]


# ================================
# 恢复规则管理API
# ================================

@router.get("/rules")
async def get_recovery_rules(
    enabled_only: bool = Query(default=False, description="仅获取启用的规则"),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取所有恢复规则
    """
    try:
        rules = await infrastructure_recovery_manager.get_recovery_rules()
        
        # 过滤规则
        if enabled_only:
            rules = [rule for rule in rules if rule["enabled"]]
        
        # 格式化响应
        formatted_rules = []
        for rule in rules:
            formatted_rule = RecoveryRuleResponse(**rule)
            formatted_rules.append(formatted_rule.dict())
        
        return {
            "rules": formatted_rules,
            "total_count": len(formatted_rules),
            "enabled_count": len([r for r in formatted_rules if r["enabled"]])
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recovery rules: {str(e)}")


@router.get("/rules/{rule_id}")
async def get_recovery_rule(
    rule_id: str,
    current_user: User = Depends(require_admin)
) -> RecoveryRuleResponse:
    """
    获取特定的恢复规则
    """
    try:
        rules = await infrastructure_recovery_manager.get_recovery_rules()
        
        for rule in rules:
            if rule["rule_id"] == rule_id:
                return RecoveryRuleResponse(**rule)
        
        raise HTTPException(status_code=404, detail=f"Recovery rule {rule_id} not found")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recovery rule: {str(e)}")


@router.post("/rules")
async def create_recovery_rule(
    rule: RecoveryRuleRequest,
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    创建新的恢复规则
    """
    try:
        # 检查规则ID是否已存在
        existing_rules = await infrastructure_recovery_manager.get_recovery_rules()
        for existing_rule in existing_rules:
            if existing_rule["rule_id"] == rule.rule_id:
                raise HTTPException(status_code=400, detail=f"Rule ID {rule.rule_id} already exists")
        
        # 验证恢复动作
        valid_actions = [action.value for action in RecoveryAction]
        for action in rule.recovery_actions:
            if action.get("action") not in valid_actions:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid recovery action: {action.get('action')}. Valid actions: {valid_actions}"
                )
        
        # 创建恢复规则
        recovery_rule = RecoveryRule(
            rule_id=rule.rule_id,
            name=rule.name,
            description=rule.description,
            trigger_condition=rule.trigger_condition,
            recovery_actions=rule.recovery_actions,
            enabled=rule.enabled,
            cooldown_minutes=rule.cooldown_minutes,
            max_attempts=rule.max_attempts,
            escalation_enabled=rule.escalation_enabled
        )
        
        success = await infrastructure_recovery_manager.add_recovery_rule(recovery_rule)
        
        if success:
            return {
                "message": f"Recovery rule {rule.rule_id} created successfully",
                "rule_id": rule.rule_id
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to create recovery rule")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create recovery rule: {str(e)}")


@router.put("/rules/{rule_id}/enable")
async def enable_recovery_rule(
    rule_id: str,
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    启用恢复规则
    """
    try:
        success = await infrastructure_recovery_manager.enable_disable_rule(rule_id, True)
        
        if success:
            return {"message": f"Recovery rule {rule_id} enabled successfully"}
        else:
            raise HTTPException(status_code=404, detail=f"Recovery rule {rule_id} not found")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to enable recovery rule: {str(e)}")


@router.put("/rules/{rule_id}/disable")
async def disable_recovery_rule(
    rule_id: str,
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    禁用恢复规则
    """
    try:
        success = await infrastructure_recovery_manager.enable_disable_rule(rule_id, False)
        
        if success:
            return {"message": f"Recovery rule {rule_id} disabled successfully"}
        else:
            raise HTTPException(status_code=404, detail=f"Recovery rule {rule_id} not found")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to disable recovery rule: {str(e)}")


# ================================
# 执行记录查询API
# ================================

@router.get("/executions")
async def get_recovery_executions(
    start_time: Optional[str] = Query(None, description="开始时间 (ISO格式)"),
    end_time: Optional[str] = Query(None, description="结束时间 (ISO格式)"),
    status: Optional[str] = Query(None, pattern="^(pending|running|success|failed|cancelled)$", description="状态过滤"),
    rule_id: Optional[str] = Query(None, description="规则ID过滤"),
    limit: int = Query(default=50, ge=1, le=200, description="返回数量限制"),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取恢复执行记录
    """
    try:
        # 解析时间参数
        start_dt = None
        end_dt = None
        
        if start_time:
            try:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_time format")
        
        if end_time:
            try:
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_time format")
        
        executions = await infrastructure_recovery_manager.get_recovery_executions(
            start_time=start_dt,
            end_time=end_dt,
            limit=limit
        )
        
        # 过滤执行记录
        if status:
            executions = [e for e in executions if e["status"] == status]
        
        if rule_id:
            executions = [e for e in executions if e["rule_id"] == rule_id]
        
        # 计算执行时间
        formatted_executions = []
        for execution in executions:
            if execution["started_at"] and execution["completed_at"]:
                start_dt = datetime.fromisoformat(execution["started_at"])
                end_dt = datetime.fromisoformat(execution["completed_at"])
                execution["duration_seconds"] = (end_dt - start_dt).total_seconds()
            
            formatted_execution = RecoveryExecutionResponse(**execution)
            formatted_executions.append(formatted_execution.dict())
        
        return {
            "executions": formatted_executions,
            "total_count": len(formatted_executions),
            "filters": {
                "start_time": start_time,
                "end_time": end_time,
                "status": status,
                "rule_id": rule_id
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recovery executions: {str(e)}")


@router.get("/executions/{execution_id}")
async def get_recovery_execution(
    execution_id: str,
    current_user: User = Depends(require_admin)
) -> RecoveryExecutionResponse:
    """
    获取特定的恢复执行记录
    """
    try:
        executions = await infrastructure_recovery_manager.get_recovery_executions(limit=1000)
        
        for execution in executions:
            if execution["execution_id"] == execution_id:
                # 计算执行时间
                if execution["started_at"] and execution["completed_at"]:
                    start_dt = datetime.fromisoformat(execution["started_at"])
                    end_dt = datetime.fromisoformat(execution["completed_at"])
                    execution["duration_seconds"] = (end_dt - start_dt).total_seconds()
                
                return RecoveryExecutionResponse(**execution)
        
        raise HTTPException(status_code=404, detail=f"Recovery execution {execution_id} not found")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recovery execution: {str(e)}")


# ================================
# 统计和分析API
# ================================

@router.get("/statistics")
async def get_recovery_statistics(
    days: int = Query(default=7, ge=1, le=90, description="统计天数"),
    current_user: User = Depends(require_admin)
) -> RecoveryStatisticsResponse:
    """
    获取恢复统计信息
    """
    try:
        # 获取时间范围内的执行记录
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        executions = await infrastructure_recovery_manager.get_recovery_executions(
            start_time=start_time,
            end_time=end_time,
            limit=1000
        )
        
        # 获取所有规则
        rules = await infrastructure_recovery_manager.get_recovery_rules()
        
        # 计算统计数据
        total_rules = len(rules)
        enabled_rules = len([r for r in rules if r["enabled"]])
        total_executions = len(executions)
        success_executions = len([e for e in executions if e["status"] == "success"])
        failed_executions = len([e for e in executions if e["status"] == "failed"])
        
        success_rate = (success_executions / total_executions * 100) if total_executions > 0 else 0
        
        # 计算平均执行时间
        execution_times = []
        for execution in executions:
            if execution["started_at"] and execution["completed_at"]:
                start_dt = datetime.fromisoformat(execution["started_at"])
                end_dt = datetime.fromisoformat(execution["completed_at"])
                execution_times.append((end_dt - start_dt).total_seconds())
        
        average_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
        
        # 统计最常触发的规则
        rule_counts = {}
        for execution in executions:
            rule_id = execution["rule_id"]
            rule_counts[rule_id] = rule_counts.get(rule_id, 0) + 1
        
        most_triggered_rules = []
        for rule_id, count in sorted(rule_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            rule_name = next((r["name"] for r in rules if r["rule_id"] == rule_id), rule_id)
            most_triggered_rules.append({
                "rule_id": rule_id,
                "rule_name": rule_name,
                "trigger_count": count
            })
        
        return RecoveryStatisticsResponse(
            total_rules=total_rules,
            enabled_rules=enabled_rules,
            total_executions=total_executions,
            success_executions=success_executions,
            failed_executions=failed_executions,
            success_rate=round(success_rate, 2),
            average_execution_time=round(average_execution_time, 2),
            most_triggered_rules=most_triggered_rules
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recovery statistics: {str(e)}")


@router.get("/health")
async def get_recovery_system_health(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取恢复系统健康状态
    """
    try:
        # 获取系统状态
        rules = await infrastructure_recovery_manager.get_recovery_rules()
        
        # 获取最近的执行记录
        recent_executions = await infrastructure_recovery_manager.get_recovery_executions(limit=10)
        
        # 计算健康指标
        total_rules = len(rules)
        enabled_rules = len([r for r in rules if r["enabled"]])
        
        # 最近执行成功率
        if recent_executions:
            recent_success = len([e for e in recent_executions if e["status"] == "success"])
            recent_success_rate = (recent_success / len(recent_executions)) * 100
        else:
            recent_success_rate = 100  # 没有执行记录认为是健康的
        
        # 系统状态
        if recent_success_rate >= 90 and enabled_rules > 0:
            system_status = "healthy"
        elif recent_success_rate >= 70:
            system_status = "warning"
        else:
            system_status = "critical"
        
        # 检查最近失败的操作
        recent_failures = [e for e in recent_executions if e["status"] == "failed"]
        
        return {
            "system_status": system_status,
            "rules": {
                "total": total_rules,
                "enabled": enabled_rules,
                "disabled": total_rules - enabled_rules
            },
            "executions": {
                "recent_success_rate": round(recent_success_rate, 2),
                "recent_executions": len(recent_executions),
                "recent_failures": len(recent_failures)
            },
            "health_checks": {
                "rules_configured": total_rules > 0,
                "rules_enabled": enabled_rules > 0,
                "recent_executions_successful": recent_success_rate >= 80
            },
            "recommendations": _generate_health_recommendations(system_status, rules, recent_executions),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recovery system health: {str(e)}")


# ================================
# 手动触发API
# ================================

@router.post("/rules/{rule_id}/trigger")
async def trigger_recovery_rule(
    rule_id: str,
    alert_data: Optional[Dict[str, Any]] = Body(None, description="模拟告警数据"),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    手动触发恢复规则（用于测试）
    """
    try:
        # 检查规则是否存在
        rules = await infrastructure_recovery_manager.get_recovery_rules()
        target_rule = None
        
        for rule in rules:
            if rule["rule_id"] == rule_id:
                target_rule = rule
                break
        
        if not target_rule:
            raise HTTPException(status_code=404, detail=f"Recovery rule {rule_id} not found")
        
        # 创建模拟告警数据
        if not alert_data:
            alert_data = {
                "alert_id": f"manual_test_{int(datetime.now().timestamp())}",
                "title": f"Manual test trigger for rule {rule_id}",
                "description": "Manually triggered recovery rule for testing",
                "severity": "critical",
                "source": target_rule["trigger_condition"].get("source", "manual_test"),
                "labels": {
                    "metric_name": target_rule["trigger_condition"].get("metric_name", "test_metric")
                },
                "current_value": target_rule["trigger_condition"].get("threshold", 100) + 10,
                "timestamp": datetime.now()
            }
        
        # 执行恢复规则
        from app.core.infrastructure_recovery import RecoveryRule
        
        recovery_rule = RecoveryRule(**target_rule)
        
        # 这里需要调用内部方法来执行规则
        # 为了安全，我们只记录测试请求而不实际执行
        logger.info(f"Manual trigger requested for rule {rule_id} (test mode)")
        
        return {
            "message": f"Recovery rule {rule_id} trigger request received (test mode)",
            "alert_data": alert_data,
            "rule": target_rule,
            "note": "This is a test trigger. In production, the recovery actions would be executed."
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger recovery rule: {str(e)}")


# ================================
# 配置和模板API
# ================================

@router.get("/templates")
async def get_recovery_rule_templates(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取恢复规则模板
    """
    try:
        templates = {
            "high_cpu_template": {
                "name": "高CPU使用率恢复模板",
                "description": "当CPU使用率过高时的恢复操作模板",
                "trigger_condition": {
                    "source": "infrastructure_monitor",
                    "metric_name": "cpu_usage_percent",
                    "threshold": 90.0,
                    "duration_minutes": 5
                },
                "recovery_actions": [
                    {
                        "action": "kill_process",
                        "params": {"cpu_threshold": 80.0, "max_processes": 3},
                        "timeout": 60
                    },
                    {
                        "action": "clear_cache",
                        "params": {"cache_types": ["redis", "application"]},
                        "timeout": 30
                    }
                ],
                "cooldown_minutes": 30,
                "max_attempts": 3
            },
            "high_memory_template": {
                "name": "高内存使用率恢复模板",
                "description": "当内存使用率过高时的恢复操作模板",
                "trigger_condition": {
                    "source": "infrastructure_monitor",
                    "metric_name": "memory_usage_percent",
                    "threshold": 85.0,
                    "duration_minutes": 5
                },
                "recovery_actions": [
                    {
                        "action": "clear_cache",
                        "params": {"cache_types": ["redis", "application"]},
                        "timeout": 30
                    },
                    {
                        "action": "restart_service",
                        "params": {"services": ["web3search-api"]},
                        "timeout": 120
                    }
                ],
                "cooldown_minutes": 45,
                "max_attempts": 2
            },
            "disk_space_template": {
                "name": "磁盘空间不足恢复模板",
                "description": "当磁盘空间不足时的恢复操作模板",
                "trigger_condition": {
                    "source": "network_storage_monitor",
                    "metric_name": "disk_usage_percent",
                    "threshold": 90.0,
                    "duration_minutes": 2
                },
                "recovery_actions": [
                    {
                        "action": "clean_disk",
                        "params": {"clean_types": ["logs", "temp", "cache"]},
                        "timeout": 300
                    },
                    {
                        "action": "flush_logs",
                        "params": {"log_retention_days": 7},
                        "timeout": 60
                    }
                ],
                "cooldown_minutes": 60,
                "max_attempts": 2
            },
            "database_connection_template": {
                "name": "数据库连接异常恢复模板",
                "description": "当数据库连接数过多时的恢复操作模板",
                "trigger_condition": {
                    "source": "database_monitor",
                    "metric_name": "active_connections",
                    "threshold": 150,
                    "duration_minutes": 3
                },
                "recovery_actions": [
                    {
                        "action": "optimize_database",
                        "params": {"operations": ["kill_idle_connections", "analyze_tables"]},
                        "timeout": 180
                    },
                    {
                        "action": "restart_service",
                        "params": {"services": ["web3search-api"]},
                        "timeout": 120
                    }
                ],
                "cooldown_minutes": 30,
                "max_attempts": 2
            }
        }
        
        # 获取可用的恢复动作
        available_actions = [
            {
                "action": action.value,
                "description": _get_action_description(action),
                "required_params": _get_action_required_params(action)
            }
            for action in RecoveryAction
        ]
        
        return {
            "templates": templates,
            "available_actions": available_actions,
            "usage_notes": [
                "使用模板创建规则时，请根据实际环境调整阈值和参数",
                "确保恢复操作的安全性，避免造成数据丢失",
                "建议先在测试环境验证恢复规则的有效性"
            ]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recovery rule templates: {str(e)}")


# ================================
# 辅助函数
# ================================

def _generate_health_recommendations(system_status: str, rules: List[Dict[str, Any]], executions: List[Dict[str, Any]]) -> List[str]:
    """生成健康建议"""
    recommendations = []
    
    try:
        if system_status == "critical":
            recommendations.append("恢复系统状态严重，需要立即检查恢复规则配置")
            recommendations.append("检查最近的失败执行记录，调整恢复动作参数")
        
        elif system_status == "warning":
            recommendations.append("恢复系统性能需要关注，建议优化恢复规则")
        
        # 规则配置建议
        enabled_rules = len([r for r in rules if r["enabled"]])
        if enabled_rules == 0:
            recommendations.append("没有启用的恢复规则，建议启用关键基础设施的自动恢复")
        elif enabled_rules < 3:
            recommendations.append("启用的恢复规则较少，建议配置更多关键场景的自动恢复")
        
        # 执行成功率建议
        if executions:
            success_count = len([e for e in executions if e["status"] == "success"])
            success_rate = (success_count / len(executions)) * 100
            
            if success_rate < 70:
                recommendations.append("最近恢复操作成功率较低，建议检查和优化恢复动作")
            elif success_rate < 90:
                recommendations.append("恢复操作成功率有提升空间，建议调整参数或增加备用方案")
        
        # 规则覆盖建议
        rule_sources = set(r["trigger_condition"].get("source", "") for r in rules)
        expected_sources = {"infrastructure_monitor", "database_monitor", "network_storage_monitor"}
        missing_sources = expected_sources - rule_sources
        
        if missing_sources:
            recommendations.append(f"建议为以下监控源配置恢复规则: {', '.join(missing_sources)}")
    
    except Exception as e:
        recommendations.append(f"生成建议时出错: {str(e)}")
    
    return recommendations


def _get_action_description(action: RecoveryAction) -> str:
    """获取恢复动作描述"""
    descriptions = {
        RecoveryAction.RESTART_SERVICE: "重启指定的系统服务",
        RecoveryAction.CLEAR_CACHE: "清理各种缓存（Redis、应用缓存等）",
        RecoveryAction.SCALE_RESOURCES: "扩缩容计算资源（需要云服务支持）",
        RecoveryAction.CLEAN_DISK: "清理磁盘空间（日志、临时文件等）",
        RecoveryAction.OPTIMIZE_DATABASE: "优化数据库性能（清理连接、分析表等）",
        RecoveryAction.RESTART_SYSTEM: "重启整个系统（高风险操作）",
        RecoveryAction.KILL_PROCESS: "终止占用资源过多的进程",
        RecoveryAction.FLUSH_LOGS: "清理和轮转日志文件",
        RecoveryAction.UPDATE_CONFIG: "更新系统配置文件"
    }
    return descriptions.get(action, "未知恢复动作")


def _get_action_required_params(action: RecoveryAction) -> List[str]:
    """获取恢复动作所需参数"""
    params = {
        RecoveryAction.RESTART_SERVICE: ["services"],
        RecoveryAction.CLEAR_CACHE: ["cache_types"],
        RecoveryAction.SCALE_RESOURCES: ["resource_type", "target_size"],
        RecoveryAction.CLEAN_DISK: ["clean_types"],
        RecoveryAction.OPTIMIZE_DATABASE: ["operations"],
        RecoveryAction.RESTART_SYSTEM: [],
        RecoveryAction.KILL_PROCESS: ["cpu_threshold"],
        RecoveryAction.FLUSH_LOGS: ["log_retention_days"],
        RecoveryAction.UPDATE_CONFIG: ["config_type"]
    }
    return params.get(action, [])
