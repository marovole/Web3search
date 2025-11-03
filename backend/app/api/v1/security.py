"""
安全检查API端点
提供安全状态监控和验证功能
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security_validator import security_validator
from app.api.middleware.auth import get_current_user
from app.models.user import User
from app.api.middleware.permission_auth import Permissions, get_user_with_permission

router = APIRouter()


@router.get("/security/health", summary="安全状态检查")
async def security_health_check(
    db: AsyncSession = Depends(get_db)
):
    """
    获取系统安全状态概览

    Returns:
        Dict: 安全状态摘要
    """
    try:
        # 快速安全检查
        quick_check = await security_validator.quick_security_check()

        return {
            "status": "healthy" if quick_check["status"] == "PASS" else "unhealthy",
            "critical_issues": quick_check["critical_issues"],
            "timestamp": quick_check["timestamp"],
            "environment": quick_check.get("environment", "unknown"),
            "details": quick_check
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"安全检查失败：{str(e)}"
        )


@router.get("/security/full-scan", summary="全面安全扫描")
async def full_security_scan(
    current_user: User = Depends(get_user_with_permission(Permissions.SYSTEM_READ)),
    db: AsyncSession = Depends(get_db)
):
    """
    执行全面的安全扫描

    需要系统读取权限。

    Returns:
        Dict: 完整的安全扫描报告
    """
    try:
        # 全面安全检查
        security_report = await security_validator.validate_all()

        return security_report

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"安全扫描失败：{str(e)}"
        )


@router.get("/security/config", summary="安全配置信息")
async def get_security_config(
    current_user: User = Depends(get_user_with_permission(Permissions.SYSTEM_READ)),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前安全配置信息

    需要系统读取权限。

    Returns:
        Dict: 安全配置信息
    """
    from app.core.config import settings

    # 返回脱敏的安全配置信息
    security_config = {
        "environment": settings.ENVIRONMENT,
        "debug_mode": settings.DEBUG,
        "cors_origins_count": len(settings.cors_origins_list),
        "cors_origins": settings.cors_origins_list,
        "jwt_algorithm": settings.JWT_ALGORITHM,
        "jwt_expire_hours": settings.ACCESS_TOKEN_EXPIRE_HOURS,
        "signature_verification_enabled": settings.ENABLE_SIGNATURE_VERIFICATION,
        "database_ssl_configured": "ssl=" in getattr(settings, 'DATABASE_URL', '').lower(),
        "security_headers_configured": True,  # 通过render.yaml配置
    }

    return {
        "timestamp": security_validator.results[0]["timestamp"] if security_validator.results else None,
        "config": security_config,
        "status": "configured"
    }


@router.post("/security/validate-config", summary="验证安全配置")
async def validate_security_config(
    current_user: User = Depends(get_user_with_permission(Permissions.SYSTEM_ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    """
    手动触发安全配置验证

    需要系统管理员权限。

    Returns:
        Dict: 验证结果
    """
    try:
        # 执行完整验证
        security_report = await security_validator.validate_all()

        # 根据验证结果返回状态
        if security_report["overall_status"] == "PASS":
            return {
                "status": "success",
                "message": "所有安全配置验证通过",
                "report": security_report
            }
        else:
            critical_failures = [
                check for check in security_report["checks"]
                if check["status"] == "fail" and check["severity"] == "critical"
            ]

            return {
                "status": "warning" if not critical_failures else "error",
                "message": f"发现 {security_report['summary']['failed']} 个安全问题",
                "critical_issues": len(critical_failures),
                "report": security_report
            }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"安全配置验证失败：{str(e)}"
        )


@router.get("/security/permissions/{user_id}", summary="获取用户权限")
async def get_user_permissions(
    user_id: str,
    current_user: User = Depends(get_user_with_permission(Permissions.USER_READ)),
    db: AsyncSession = Depends(get_db)
):
    """
    获取指定用户的权限信息

    需要用户读取权限。

    Args:
        user_id: 用户ID

    Returns:
        Dict: 用户权限信息
    """
    try:
        from app.services.rbac_service import RBACService

        rbac_service = RBACService(db)

        # 获取用户权限和角色
        permissions = await rbac_service.get_user_permissions(user_id)
        roles = await rbac_service.get_user_roles(user_id)

        return {
            "user_id": user_id,
            "permissions": list(permissions),
            "roles": [{"id": role.id, "name": role.name, "display_name": role.display_name} for role in roles],
            "total_permissions": len(permissions),
            "total_roles": len(roles)
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户权限失败：{str(e)}"
        )


@router.get("/security/audit-log", summary="安全审计日志")
async def get_security_audit_log(
    current_user: User = Depends(get_user_with_permission(Permissions.SYSTEM_READ)),
    db: AsyncSession = Depends(get_db)
):
    """
    获取安全相关的审计日志

    需要系统读取权限。

    Returns:
        Dict: 安全审计日志摘要
    """
    try:
        # 这里应该查询实际的审计日志表
        # 目前返回模拟数据
        return {
            "timestamp": "2024-01-01T00:00:00Z",
            "total_events": 0,
            "recent_events": [
                # 这里应该从数据库查询实际的安全事件
            ],
            "security_score": 100.0,
            "status": "no_issues_detected"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取安全审计日志失败：{str(e)}"
        )