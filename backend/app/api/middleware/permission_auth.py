"""
权限认证装饰器和依赖项
提供基于角色的访问控制功能
"""
from typing import List, Optional
from functools import wraps
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.middleware.auth import get_current_user
from app.services.rbac_service import RBACService
from app.models.user import User


def require_permissions(permissions: List[str]):
    """
    权限检查装饰器

    Args:
        permissions: 需要的权限列表，格式：['resource:action', ...]

    Usage:
        @require_permissions(['user:read', 'user:write'])
        async def some_endpoint():
            pass
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从kwargs中获取db和current_user
            db = kwargs.get('db')
            current_user = kwargs.get('current_user')

            if not db or not current_user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="权限检查失败：缺少必要的参数"
                )

            # 检查权限
            rbac_service = RBACService(db)

            if len(permissions) == 1:
                # 单个权限检查
                resource, action = RBACService.parse_permission_name(permissions[0])
                has_permission = await rbac_service.check_permission(
                    current_user.id, resource, action
                )
            else:
                # 多个权限检查（需要所有权限）
                has_permission = await rbac_service.has_all_permissions(
                    current_user.id, permissions
                )

            if not has_permission:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"权限不足，需要权限：{', '.join(permissions)}"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_any_permission(permissions: List[str]):
    """
    任意权限检查装饰器

    Args:
        permissions: 需要的权限列表，格式：['resource:action', ...]
                    用户只需要拥有其中任意一个权限即可

    Usage:
        @require_any_permission(['admin:read', 'user:read'])
        async def some_endpoint():
            pass
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            db = kwargs.get('db')
            current_user = kwargs.get('current_user')

            if not db or not current_user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="权限检查失败：缺少必要的参数"
                )

            # 检查是否有任意权限
            rbac_service = RBACService(db)
            has_permission = await rbac_service.has_any_permission(
                current_user.id, permissions
            )

            if not has_permission:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"权限不足，需要以下任意权限：{', '.join(permissions)}"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


async def get_user_with_permission(
    resource: str,
    action: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    权限检查依赖项

    Args:
        resource: 资源名称
        action: 操作名称
        current_user: 当前用户
        db: 数据库会话

    Returns:
        User: 通过权限检查的用户

    Raises:
        HTTPException: 如果权限不足
    """
    rbac_service = RBACService(db)

    has_permission = await rbac_service.check_permission(
        current_user.id, resource, action
    )

    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"权限不足，需要权限：{resource}:{action}"
        )

    return current_user


async def get_user_with_any_permission(
    permissions: List[str],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    任意权限检查依赖项

    Args:
        permissions: 权限列表
        current_user: 当前用户
        db: 数据库会话

    Returns:
        User: 通过权限检查的用户

    Raises:
        HTTPException: 如果权限不足
    """
    rbac_service = RBACService(db)

    has_permission = await rbac_service.has_any_permission(
        current_user.id, permissions
    )

    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"权限不足，需要以下任意权限：{', '.join(permissions)}"
        )

    return current_user


class PermissionChecker:
    """
    权限检查器类

    提供更灵活的权限检查方式
    """

    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id
        self.rbac_service = RBACService(db)

    async def can(self, resource: str, action: str) -> bool:
        """检查是否可以执行指定操作"""
        return await self.rbac_service.check_permission(
            self.user_id, resource, action
        )

    async def can_any(self, permissions: List[str]) -> bool:
        """检查是否可以执行任意操作"""
        return await self.rbac_service.has_any_permission(
            self.user_id, permissions
        )

    async def can_all(self, permissions: List[str]) -> bool:
        """检查是否可以执行所有操作"""
        return await self.rbac_service.has_all_permissions(
            self.user_id, permissions
        )

    async def get_permissions(self) -> List[str]:
        """获取所有权限"""
        return list(await self.rbac_service.get_user_permissions(self.user_id))

    async def get_roles(self) -> List[str]:
        """获取所有角色"""
        roles = await self.rbac_service.get_user_roles(self.user_id)
        return [role.name for role in roles]


async def get_permission_checker(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> PermissionChecker:
    """
    获取权限检查器

    Args:
        current_user: 当前用户
        db: 数据库会话

    Returns:
        PermissionChecker: 权限检查器实例
    """
    return PermissionChecker(db, current_user.id)


# 常用权限常量
class Permissions:
    """常用权限常量"""

    # 用户管理权限
    USER_READ = "user:read"
    USER_WRITE = "user:write"
    USER_DELETE = "user:delete"
    USER_ADMIN = "user:admin"

    # 报告权限
    REPORT_READ = "report:read"
    REPORT_WRITE = "report:write"
    REPORT_DELETE = "report:delete"
    REPORT_ADMIN = "report:admin"

    # 搜索权限
    SEARCH_READ = "search:read"
    SEARCH_WRITE = "search:write"
    SEARCH_ADMIN = "search:admin"

    # 聊天权限
    CHAT_READ = "chat:read"
    CHAT_WRITE = "chat:write"
    CHAT_DELETE = "chat:delete"
    CHAT_ADMIN = "chat:admin"

    # 系统管理权限
    SYSTEM_READ = "system:read"
    SYSTEM_WRITE = "system:write"
    SYSTEM_ADMIN = "system:admin"

    # 分析权限
    ANALYTICS_READ = "analytics:read"
    ANALYTICS_WRITE = "analytics:write"
    ANALYTICS_ADMIN = "analytics:admin"


class Roles:
    """常用角色常量"""

    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    ANALYST = "analyst"
    USER = "user"
    GUEST = "guest"