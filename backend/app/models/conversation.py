"""
对话数据模型
存储用户对话历史和消息
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Integer, DateTime, Boolean, Index, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.core.database import Base


class MessageRole(str, enum.Enum):
    """消息角色枚举"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Conversation(Base):
    """
    对话会话表
    存储用户与AI的对话会话
    """
    __tablename__ = "conversations"

    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 会话标识
    session_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)

    # 会话标题（从第一条消息自动生成）
    title: Mapped[Optional[str]] = mapped_column(String(500))

    # 用户标识（可选，未来支持用户系统）
    user_id: Mapped[Optional[str]] = mapped_column(String(100), index=True)

    # 统计信息
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)

    # 会话元数据
    extra_metadata: Mapped[Optional[dict]] = mapped_column(Text)  # JSON string
    # 例: {"ip": "127.0.0.1", "user_agent": "..."}

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    last_activity: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        index=True
    )

    # 会话状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    # 关系
    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at"
    )
    reports: Mapped[list["Report"]] = relationship(
        "Report",
        back_populates="conversation",
        cascade="all, delete-orphan"
    )

    # 索引
    __table_args__ = (
        Index("ix_conversations_user_created", "user_id", "created_at"),
        Index("ix_conversations_active", "is_active", "last_activity"),
    )

    def __repr__(self):
        return f"<Conversation {self.session_id} - {self.message_count} messages>"


class Message(Base):
    """
    消息表
    存储对话中的每条消息
    """
    __tablename__ = "messages"

    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 外键
    conversation_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # 消息内容
    role: Mapped[MessageRole] = mapped_column(
        SQLEnum(MessageRole, native_enum=False),
        nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # 消息元数据
    model: Mapped[Optional[str]] = mapped_column(String(100))  # 使用的模型
    token_count: Mapped[Optional[int]] = mapped_column(Integer)  # Token数量
    generation_time: Mapped[Optional[float]] = mapped_column(Text)  # 生成时间（秒）

    # 相关报告
    report_id: Mapped[Optional[int]] = mapped_column(Integer, index=True)

    # 消息状态
    is_streaming: Mapped[bool] = mapped_column(Boolean, default=False)  # 是否流式生成
    is_error: Mapped[bool] = mapped_column(Boolean, default=False)  # 是否错误消息

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    # 关系
    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")

    # 索引
    __table_args__ = (
        Index("ix_messages_conversation_created", "conversation_id", "created_at"),
    )

    def __repr__(self):
        preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"<Message {self.role.value}: {preview}>"
