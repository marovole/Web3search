"""
基于角色的访问控制（RBAC）服务
提供权限检查、角色管理等功能
"""
from typing import List, Optional, Set
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.models.rbac import Role, Permission, UserRole, user_roles, role_permissions


class RBACService:
    """
    RBAC服务类

    提供基于角色的访问控制功能，包括：
    - 权限检查
    - 角色分配
    - 权限管理
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_permission(
        self,
        user_id: str,
        resource: str,
        action: str,
        *,
        check_cache: bool = True
    ) -> bool:
        """
        检查用户是否具有指定权限

        Args:
            user_id: 用户ID
            resource: 资源名称（如 'user', 'report', 'search'）
            action: 操作名称（如 'read', 'write', 'delete', 'admin'）
            check_cache: 是否检查缓存（用于性能优化）

        Returns:
            bool: 是否有权限
        """
        # 超级用户拥有所有权限
        if await self._is_superuser(user_id):
            return True

        # 检查用户是否拥有该权限
        permission_name = f"{resource}:{action}"

        # 查询用户的所有角色及其权限
        query = (
            select(Permission)
            .join(role_permissions, Permission.id == role_permissions.c.permission_id)
            .join(Role, role_permissions.c.role_id == Role.id)
            .join(user_roles, Role.id == user_roles.c.role_id)
            .where(
                and_(
                    user_roles.c.user_id == user_id,
                    Permission.name == permission_name,
                    Permission.is_active == True,
                    Role.is_active == True,
                    user_roles.c.is_active == True,
                    or_(
                        UserRole.expires_at.is_(None),
                        UserRole.expires_at > datetime.utcnow()
                    )
                )
            )
            .limit(1)
        )

        result = await self.db.execute(query)
        permission = result.scalar_one_or_none()

        return permission is not None

    async def get_user_permissions(self, user_id: str) -> Set[str]:
        """
        获取用户的所有权限

        Args:
            user_id: 用户ID

        Returns:
            Set[str]: 权限名称集合
        """
        # 超级用户拥有所有权限
        if await self._is_superuser(user_id):
            # 返回所有激活的权限
            query = select(Permission.name).where(Permission.is_active == True)
            result = await self.db.execute(query)
            return set(result.scalars().all())

        # 查询用户的权限
        query = (
            select(Permission.name)
            .join(role_permissions, Permission.id == role_permissions.c.permission_id)
            .join(Role, role_permissions.c.role_id == Role.id)
            .join(user_roles, Role.id == user_roles.c.role_id)
            .where(
                and_(
                    user_roles.c.user_id == user_id,
                    Permission.is_active == True,
                    Role.is_active == True,
                    user_roles.c.is_active == True,
                    or_(
                        UserRole.expires_at.is_(None),
                        UserRole.expires_at > datetime.utcnow()
                    )
                )
            )
        )

        result = await self.db.execute(query)
        return set(result.scalars().all())

    async def get_user_roles(self, user_id: str) -> List[Role]:
        """
        获取用户的所有角色

        Args:
            user_id: 用户ID

        Returns:
            List[Role]: 角色列表
        """
        query = (
            select(Role)
            .join(user_roles, Role.id == user_roles.c.role_id)
            .where(
                and_(
                    user_roles.c.user_id == user_id,
                    Role.is_active == True,
                    user_roles.c.is_active == True,
                    or_(
                        UserRole.expires_at.is_(None),
                        UserRole.expires_at > datetime.utcnow()
                    )
                )
            )
        )

        result = await self.db.execute(query)
        return result.scalars().all()

    async def assign_role(
        self,
        user_id: str,
        role_name: str,
        assigned_by: str,
        *,
        expires_at: Optional[datetime] = None,
        notes: Optional[str] = None
    ) -> bool:
        """
        为用户分配角色

        Args:
            user_id: 用户ID
            role_name: 角色名称
            assigned_by: 分配者用户ID
            expires_at: 过期时间（可选）
            notes: 备注（可选）

        Returns:
            bool: 是否分配成功
        """
        # 查询角色
        role_query = select(Role).where(Role.name == role_name, Role.is_active == True)
        role_result = await self.db.execute(role_query)
        role = role_result.scalar_one_or_none()

        if not role:
            return False

        # 检查是否已经分配
        existing_query = select(UserRole).where(
            and_(
                UserRole.user_id == user_id,
                UserRole.role_id == role.id,
                UserRole.is_active == True
            )
        )
        existing_result = await self.db.execute(existing_query)
        existing_assignment = existing_result.scalar_one_or_none()

        if existing_assignment:
            # 更新现有分配
            existing_assignment.assigned_by = assigned_by
            existing_assignment.expires_at = expires_at
            existing_assignment.notes = notes
        else:
            # 创建新分配
            user_role = UserRole(
                user_id=user_id,
                role_id=role.id,
                assigned_by=assigned_by,
                expires_at=expires_at,
                notes=notes
            )
            self.db.add(user_role)

        await self.db.commit()
        return True

    async def revoke_role(
        self,
        user_id: str,
        role_name: str,
        revoked_by: str
    ) -> bool:
        """
        撤销用户角色

        Args:
            user_id: 用户ID
            role_name: 角色名称
            revoked_by: 撤销者用户ID

        Returns:
            bool: 是否撤销成功
        """
        # 查询角色分配
        query = (
            select(UserRole)
            .join(Role, UserRole.role_id == Role.id)
            .where(
                and_(
                    UserRole.user_id == user_id,
                    Role.name == role_name,
                    UserRole.is_active == True
                )
            )
        )

        result = await self.db.execute(query)
        user_role = result.scalar_one_or_none()

        if not user_role:
            return False

        # 撤销角色（软删除）
        user_role.is_active = False
        user_role.notes = f"Revoked by {revoked_by} at {datetime.utcnow()}"

        await self.db.commit()
        return True

    async def has_any_permission(
        self,
        user_id: str,
        permissions: List[str]
    ) -> bool:
        """
        检查用户是否具有任意一个权限

        Args:
            user_id: 用户ID
            permissions: 权限列表（格式：['resource:action', ...]）

        Returns:
            bool: 是否具有任意权限
        """
        user_permissions = await self.get_user_permissions(user_id)
        return any(perm in user_permissions for perm in permissions)

    async def has_all_permissions(
        self,
        user_id: str,
        permissions: List[str]
    ) -> bool:
        """
        检查用户是否具有所有权限

        Args:
            user_id: 用户ID
            permissions: 权限列表（格式：['resource:action', ...]）

        Returns:
            bool: 是否具有所有权限
        """
        user_permissions = await self.get_user_permissions(user_id)
        return all(perm in user_permissions for perm in permissions)

    async def _is_superuser(self, user_id: str) -> bool:
        """检查用户是否为超级用户"""
        query = select(User.is_superuser).where(
            and_(
                User.id == user_id,
                User.is_active == True,
                User.deleted_at.is_(None)
            )
        )
        result = await self.db.execute(query)
        is_superuser = result.scalar()
        return bool(is_superuser)

    @staticmethod
    def create_permission_name(resource: str, action: str) -> str:
        """创建权限名称"""
        return f"{resource}:{action}"

    @staticmethod
    def parse_permission_name(permission_name: str) -> tuple[str, str]:
        """解析权限名称"""
        if ":" not in permission_name:
            raise ValueError(f"Invalid permission name format: {permission_name}")

        resource, action = permission_name.split(":", 1)
        return resource.strip(), action.strip()


# 导入datetime
from datetime import datetime