"""
用户相关数据模型
存储用户账号、偏好设置和会话信息
"""
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import String, Text, Integer, DateTime, Boolean, JSON, Index, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid

from app.core.database import Base


class User(Base):
    """
    用户表
    存储用户基本信息和账号状态
    """
    __tablename__ = "users"

    # 主键 - 使用UUID作为用户ID
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True
    )

    # 邮箱（唯一，用于登录）
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)

    # 密码哈希（bcrypt加密）
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # 用户名（可选）
    username: Mapped[Optional[str]] = mapped_column(String(100), index=True)

    # 邮箱验证状态
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # 邮箱验证Token（用于邮箱验证）
    email_verification_token: Mapped[Optional[str]] = mapped_column(String(64), index=True)

    # 密码重置Token
    password_reset_token: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    password_reset_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # 账户状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # 软删除
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, index=True)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # 关系
    preferences: Mapped[Optional["UserPreferences"]] = relationship(
        "UserPreferences",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    sessions: Mapped[list["Session"]] = relationship(
        "Session",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    reports: Mapped[list["Report"]] = relationship(
        "Report",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    roles: Mapped[list["Role"]] = relationship(
        "Role",
        secondary="user_roles",
        back_populates="users"
    )

    # 索引
    __table_args__ = (
        Index("ix_users_email_active", "email", "is_active"),
        Index("ix_users_created_at", "created_at"),
    )

    def __repr__(self):
        return f"<User {self.id} - {self.email}>"

    @property
    def is_deleted(self) -> bool:
        """用户是否已删除"""
        return self.deleted_at is not None

    def soft_delete(self):
        """软删除用户"""
        self.deleted_at = datetime.utcnow()
        self.is_active = False

    def generate_email_verification_token(self) -> str:
        """生成邮箱验证Token"""
        import secrets
        self.email_verification_token = secrets.token_urlsafe(32)
        return self.email_verification_token

    def generate_password_reset_token(self) -> str:
        """生成密码重置Token"""
        import secrets
        self.password_reset_token = secrets.token_urlsafe(32)
        self.password_reset_expires_at = datetime.utcnow() + timedelta(hours=1)
        return self.password_reset_token

    def is_password_reset_token_valid(self) -> bool:
        """检查密码重置Token是否有效"""
        if not self.password_reset_token or not self.password_reset_expires_at:
            return False
        return datetime.utcnow() < self.password_reset_expires_at


class UserPreferences(Base):
    """
    用户偏好设置表
    存储用户的个性化设置，支持跨设备同步
    """
    __tablename__ = "user_preferences"

    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 外键
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )

    # 偏好设置（JSON存储）
    preferences: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    # 结构:
    # {
    #   "theme": "light|dark|system",
    #   "language": "zh-CN|en-US",
    #   "notifications": {
    #     "email": true,
    #     "price_alerts": false
    #   },
    #   "display": {
    #     "compact_mode": false,
    #     "default_timeframe": "7d"
    #   },
    #   "research": {
    #     "default_model": "qwen3-235b",
    #     "auto_export": false
    #   }
    # }

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # 关系
    user: Mapped["User"] = relationship("User", back_populates="preferences")

    def __repr__(self):
        return f"<UserPreferences user_id={self.user_id}>"

    def update_preferences(self, updates: dict):
        """更新偏好设置（合并）"""
        self.preferences = {**self.preferences, **updates}
        self.updated_at = datetime.utcnow()

    def get_preference(self, key: str, default=None):
        """获取偏好设置值"""
        keys = key.split(".")
        value = self.preferences
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default
        return value if value is not None else default


class Session(Base):
    """
    用户会话表
    存储Refresh Token和会话信息
    """
    __tablename__ = "sessions"

    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 外键
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Refresh Token（哈希值）
    refresh_token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)

    # 会话元数据
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))  # IPv6最长45字符
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))
    device_info: Mapped[Optional[dict]] = mapped_column(JSON)

    # Token状态
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # 过期时间
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    last_used_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        index=True
    )

    # 关系
    user: Mapped["User"] = relationship("User", back_populates="sessions")

    # 索引
    __table_args__ = (
        Index("ix_sessions_user_expires", "user_id", "expires_at"),
        Index("ix_sessions_revoked_expires", "is_revoked", "expires_at"),
    )

    def __repr__(self):
        return f"<Session {self.id} - user_id={self.user_id}>"

    @property
    def is_expired(self) -> bool:
        """会话是否已过期"""
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self) -> bool:
        """会话是否有效"""
        return not self.is_revoked and not self.is_expired

    def revoke(self):
        """撤销会话"""
        self.is_revoked = True
        self.revoked_at = datetime.utcnow()

    def extend(self, days: int = 30):
        """延长会话有效期"""
        self.expires_at = datetime.utcnow() + timedelta(days=days)
        self.last_used_at = datetime.utcnow()

