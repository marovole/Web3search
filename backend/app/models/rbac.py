"""
基于角色的访问控制（RBAC）模型
定义用户角色、权限和访问控制逻辑
"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Boolean, DateTime, Text, ForeignKey, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property

from app.core.database import Base


# 用户-角色关联表（多对多关系）
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', String(36), ForeignKey('users.id'), primary_key=True),
    Column('role_id', String(36), ForeignKey('roles.id'), primary_key=True),
    Column('assigned_at', DateTime, default=datetime.utcnow),
    Column('assigned_by', String(36), ForeignKey('users.id')),
)

# 角色-权限关联表（多对多关系）
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', String(36), ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', String(36), ForeignKey('permissions.id'), primary_key=True),
    Column('granted_at', DateTime, default=datetime.utcnow),
    Column('granted_by', String(36), ForeignKey('users.id')),
)


class Role(Base):
    """
    角色表
    定义系统中的各种角色
    """
    __tablename__ = "roles"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )

    display_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    description: Mapped[Optional[str]] = mapped_column(Text)

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    is_system_role: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        description="是否为系统内置角色"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # 关系
    users: Mapped[List["User"]] = relationship(
        "User",
        secondary=user_roles,
        back_populates="roles"
    )

    permissions: Mapped[List["Permission"]] = relationship(
        "Permission",
        secondary=role_permissions,
        back_populates="roles"
    )

    def __repr__(self):
        return f"<Role {self.name}>"


class Permission(Base):
    """
    权限表
    定义系统中的各种权限
    """
    __tablename__ = "permissions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )

    resource: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        description="资源名称，如 'user', 'report', 'search'"
    )

    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        description="操作名称，如 'read', 'write', 'delete', 'admin'"
    )

    description: Mapped[Optional[str]] = mapped_column(Text)

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    # 关系
    roles: Mapped[List["Role"]] = relationship(
        "Role",
        secondary=role_permissions,
        back_populates="permissions"
    )

    def __repr__(self):
        return f"<Permission {self.resource}:{self.action}>"

    @hybrid_property
    def full_name(self) -> str:
        """完整的权限名称"""
        return f"{self.resource}:{self.action}"


class UserRole(Base):
    """
    用户角色表
    记录用户角色的分配信息（包括有效期等）
    """
    __tablename__ = "user_role_assignments"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey('users.id'),
        nullable=False,
        index=True
    )

    role_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey('roles.id'),
        nullable=False,
        index=True
    )

    assigned_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    assigned_by: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey('users.id')
    )

    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        description="角色过期时间，None表示永不过期"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    notes: Mapped[Optional[str]] = mapped_column(Text)


# 导入uuid
import uuid