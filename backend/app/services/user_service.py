"""
用户服务模块
提供用户信息管理、偏好设置管理和数据导出功能
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User, UserPreferences
from app.models.conversation import Conversation, Message, MessageRole
from app.models.report import Report, ReportType, ReportStatus
from app.core.security import verify_password

logger = logging.getLogger(__name__)


class UserService:
    """用户服务类"""

    @staticmethod
    async def get_user_info(db: AsyncSession, user_id: str) -> Optional[User]:
        """
        获取用户信息

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            Optional[User]: 用户对象，如果不存在返回None
        """
        stmt = select(User).where(
            User.id == user_id,
            User.deleted_at.is_(None)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_user_info(
        db: AsyncSession,
        user: User,
        username: Optional[str] = None,
    ) -> User:
        """
        更新用户信息

        Args:
            db: 数据库会话
            user: 用户对象
            username: 新用户名（可选）

        Returns:
            User: 更新后的用户对象
        """
        if username is not None:
            user.username = username

        user.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(user)

        logger.info(f"用户信息已更新: {user.email} (ID: {user.id})")
        return user

    @staticmethod
    async def delete_user(
        db: AsyncSession,
        user: User,
        password: str,
    ) -> bool:
        """
        删除用户账户（软删除）

        Args:
            db: 数据库会话
            user: 用户对象
            password: 用户密码（用于确认）

        Returns:
            bool: 是否成功删除

        Raises:
            ValueError: 如果密码错误
        """
        # 验证密码
        if not verify_password(password, user.password_hash):
            raise ValueError("密码错误")

        # 软删除用户
        user.soft_delete()
        await db.commit()

        logger.info(f"用户账户已删除: {user.email} (ID: {user.id})")
        return True

    @staticmethod
    async def get_user_preferences(
        db: AsyncSession,
        user_id: str,
    ) -> Dict[str, Any]:
        """
        获取用户偏好设置

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            Dict[str, Any]: 偏好设置字典
        """
        stmt = select(UserPreferences).where(UserPreferences.user_id == user_id)
        result = await db.execute(stmt)
        preferences_obj = result.scalar_one_or_none()

        if preferences_obj:
            return preferences_obj.preferences

        # 如果不存在，返回默认偏好设置
        default_preferences = {
            "theme": "system",
            "language": "zh-CN",
            "notifications": {
                "email": True,
                "price_alerts": False,
            },
            "display": {
                "compact_mode": False,
                "default_timeframe": "7d",
            },
            "research": {
                "default_model": "qwen3-235b",
                "auto_export": False,
            },
        }
        return default_preferences

    @staticmethod
    async def update_user_preferences(
        db: AsyncSession,
        user_id: str,
        updates: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        更新用户偏好设置（合并更新）

        Args:
            db: 数据库会话
            user_id: 用户ID
            updates: 要更新的偏好设置

        Returns:
            Dict[str, Any]: 更新后的偏好设置
        """
        stmt = select(UserPreferences).where(UserPreferences.user_id == user_id)
        result = await db.execute(stmt)
        preferences_obj = result.scalar_one_or_none()

        if preferences_obj:
            # 合并更新
            preferences_obj.update_preferences(updates)
            await db.commit()
            await db.refresh(preferences_obj)
            return preferences_obj.preferences
        else:
            # 创建新的偏好设置
            default_preferences = {
                "theme": "system",
                "language": "zh-CN",
                "notifications": {
                    "email": True,
                    "price_alerts": False,
                },
                "display": {
                    "compact_mode": False,
                    "default_timeframe": "7d",
                },
                "research": {
                    "default_model": "qwen3-235b",
                    "auto_export": False,
                },
            }
            # 合并默认值和更新值
            merged_preferences = {**default_preferences, **updates}

            preferences_obj = UserPreferences(
                user_id=user_id,
                preferences=merged_preferences,
            )
            db.add(preferences_obj)
            await db.commit()
            await db.refresh(preferences_obj)
            return preferences_obj.preferences

    @staticmethod
    async def export_user_data(
        db: AsyncSession,
        user_id: str,
    ) -> Dict[str, Any]:
        """
        导出用户数据（GDPR合规）

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            Dict[str, Any]: 用户数据字典
        """
        # 获取用户信息
        user = await UserService.get_user_info(db, user_id)
        if not user:
            raise ValueError("用户不存在")

        # 获取偏好设置
        preferences = await UserService.get_user_preferences(db, user_id)

        # 获取对话历史
        stmt = select(Conversation).where(Conversation.user_id == user_id)
        result = await db.execute(stmt)
        conversations = result.scalars().all()

        conversations_data = []
        for conv in conversations:
            # 获取消息
            msg_stmt = select(Message).where(Message.conversation_id == conv.id)
            msg_result = await db.execute(msg_stmt)
            messages = msg_result.scalars().all()

            conversations_data.append({
                "id": conv.id,
                "session_id": conv.session_id,
                "title": conv.title,
                "message_count": conv.message_count,
                "messages": [
                    {
                        "role": msg.role.value,
                        "content": msg.content,
                        "created_at": msg.created_at.isoformat() if msg.created_at else None,
                    }
                    for msg in messages
                ],
                "created_at": conv.created_at.isoformat() if conv.created_at else None,
                "last_activity": conv.last_activity.isoformat() if conv.last_activity else None,
            })

        # 获取报告列表
        report_stmt = select(Report).where(Report.user_id == user_id)
        report_result = await db.execute(report_stmt)
        reports = report_result.scalars().all()

        reports_data = [
            {
                "id": report.id,
                "report_type": report.report_type.value,
                "status": report.status.value,
                "query": report.query,
                "title": report.title,
                "symbol": report.symbol,
                "created_at": report.created_at.isoformat() if report.created_at else None,
                "completed_at": report.completed_at.isoformat() if report.completed_at else None,
            }
            for report in reports
        ]

        return {
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "email_verified": user.email_verified,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
            },
            "preferences": preferences,
            "conversations": conversations_data,
            "reports": reports_data,
            "exported_at": datetime.utcnow().isoformat(),
        }


# 创建全局服务实例
user_service = UserService()

