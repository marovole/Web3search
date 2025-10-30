"""
认证服务模块
提供用户注册、登录、Token刷新和密码重置的业务逻辑
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.user import User, UserPreferences, Session
from app.core.security import (
    get_password_hash,
    verify_password,
    validate_password_strength,
    create_access_token,
    create_refresh_token,
    get_password_hash as hash_password,
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class AuthService:
    """认证服务类"""

    @staticmethod
    async def register_user(
        db: AsyncSession,
        email: str,
        password: str,
        username: Optional[str] = None,
    ) -> Tuple[User, str, Optional[str]]:
        """
        注册新用户

        Args:
            db: 数据库会话
            email: 用户邮箱
            password: 用户密码
            username: 用户名（可选）

        Returns:
            Tuple[User, str, str]: (用户对象, access_token, refresh_token)

        Raises:
            ValueError: 如果邮箱已存在或密码不符合要求
        """
        # 验证密码强度
        is_valid, error_msg = validate_password_strength(password)
        if not is_valid:
            raise ValueError(error_msg)

        # 检查邮箱是否已存在
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        existing_user = result.scalar_one_or_none()
        if existing_user:
            raise ValueError("该邮箱已被注册")

        # 创建用户
        password_hash = get_password_hash(password)
        user = User(
            email=email,
            password_hash=password_hash,
            username=username,
            email_verified=False,
            is_active=True,
        )

        try:
            db.add(user)
            await db.flush()  # 刷新以获取user.id

            # 创建默认偏好设置
            preferences = UserPreferences(
                user_id=user.id,
                preferences={
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
                },
            )
            db.add(preferences)

            await db.commit()
            await db.refresh(user)

            logger.info(f"用户注册成功: {user.email} (ID: {user.id})")

            # 生成Token
            access_token = create_access_token(
                data={"user_id": user.id, "email": user.email}
            )
            # Refresh Token将在端点中创建（需要IP和User-Agent信息）

            return user, access_token, None  # refresh_token将在端点中创建

        except IntegrityError as e:
            await db.rollback()
            logger.error(f"用户注册失败（数据库约束）: {email} - {str(e)}")
            raise ValueError("注册失败，请稍后重试")

    @staticmethod
    async def authenticate_user(
        db: AsyncSession, email: str, password: str
    ) -> Optional[User]:
        """
        验证用户凭证

        Args:
            db: 数据库会话
            email: 用户邮箱
            password: 用户密码

        Returns:
            Optional[User]: 如果验证成功返回用户对象，否则返回None
        """
        # 查询用户（排除已删除的用户）
        stmt = select(User).where(
            User.email == email, User.deleted_at.is_(None)
        )
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            logger.warning(f"登录失败: 用户不存在 - {email}")
            return None

        # 检查账户是否激活
        if not user.is_active:
            logger.warning(f"登录失败: 账户未激活 - {email}")
            return None

        # 验证密码
        if not verify_password(password, user.password_hash):
            logger.warning(f"登录失败: 密码错误 - {email}")
            return None

        # 更新最后登录时间
        user.last_login_at = datetime.utcnow()
        await db.commit()
        await db.refresh(user)

        logger.info(f"用户登录成功: {user.email} (ID: {user.id})")
        return user

    @staticmethod
    async def create_session(
        db: AsyncSession,
        user_id: str,
        refresh_token: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        device_info: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        创建用户会话（生成Refresh Token）

        Args:
            db: 数据库会话
            user_id: 用户ID
            refresh_token: 如果提供，使用此token（用于Token刷新），否则生成新的
            ip_address: IP地址（可选）
            user_agent: User Agent（可选）
            device_info: 设备信息（可选）

        Returns:
            str: Refresh Token（明文，用于返回给客户端）
        """
        # 生成或使用提供的Refresh Token
        if refresh_token:
            token = refresh_token
        else:
            token = create_refresh_token(user_id)

        # 哈希存储Refresh Token（使用密码哈希函数，因为需要验证功能）
        token_hash = get_password_hash(token)

        # 创建会话
        expires_at = datetime.utcnow() + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        session = Session(
            user_id=user_id,
            refresh_token_hash=token_hash,
            ip_address=ip_address,
            user_agent=user_agent,
            device_info=device_info,
            expires_at=expires_at,
        )

        db.add(session)
        await db.commit()
        await db.refresh(session)

        logger.debug(f"会话创建成功: user_id={user_id}, session_id={session.id}")
        return token

    @staticmethod
    async def refresh_access_token(
        db: AsyncSession, refresh_token: str
    ) -> Tuple[str, Optional[str]]:
        """
        刷新Access Token

        Args:
            db: 数据库会话
            refresh_token: Refresh Token

        Returns:
            Tuple[str, Optional[str]]: (access_token, new_refresh_token)
                new_refresh_token为None表示不轮换Refresh Token

        Raises:
            ValueError: 如果Refresh Token无效或已过期
        """
        # 查找有效的会话
        # 需要遍历所有会话并验证token哈希
        stmt = select(Session).where(
            Session.is_revoked == False,
            Session.expires_at > datetime.utcnow(),
        )
        result = await db.execute(stmt)
        sessions = result.scalars().all()

        matched_session = None
        for session in sessions:
            if verify_password(refresh_token, session.refresh_token_hash):
                matched_session = session
                break

        if not matched_session:
            logger.warning("Token刷新失败: Refresh Token无效或已过期")
            raise ValueError("Refresh Token无效或已过期")

        # 检查会话是否仍然有效
        if not matched_session.is_valid:
            logger.warning(
                f"Token刷新失败: 会话已失效 - session_id={matched_session.id}"
            )
            raise ValueError("Refresh Token无效或已过期")

        # 更新会话最后使用时间
        matched_session.last_used_at = datetime.utcnow()
        await db.commit()

        # 生成新的Access Token
        user = matched_session.user
        access_token = create_access_token(
            data={"user_id": user.id, "email": user.email}
        )

        logger.info(f"Token刷新成功: user_id={user.id}")

        # 初始实现不轮换Refresh Token，返回None
        return access_token, None

    @staticmethod
    async def initiate_password_reset(
        db: AsyncSession, email: str
    ) -> Optional[str]:
        """
        发起密码重置（生成重置token）

        Args:
            db: 数据库会话
            email: 用户邮箱

        Returns:
            Optional[str]: 密码重置token（如果用户存在），否则返回None
            注意：第一阶段不实际发送邮件，token会在日志中记录
        """
        # 查询用户
        stmt = select(User).where(
            User.email == email, User.deleted_at.is_(None)
        )
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        # 不暴露用户是否存在的信息，但如果用户存在则生成token
        if user:
            reset_token = user.generate_password_reset_token()
            await db.commit()
            await db.refresh(user)

            logger.info(
                f"密码重置token已生成: {user.email} - token={reset_token} "
                "(注意：第一阶段仅记录日志，不发送邮件)"
            )

            # 第一阶段：仅记录日志，不发送邮件
            # TODO: 后续阶段集成邮件服务发送重置链接
            return reset_token

        # 用户不存在，但不暴露此信息
        logger.info(f"密码重置请求: {email} (用户不存在)")
        return None

    @staticmethod
    async def reset_password(
        db: AsyncSession, token: str, new_password: str
    ) -> User:
        """
        重置密码

        Args:
            db: 数据库会话
            token: 密码重置token
            new_password: 新密码

        Returns:
            User: 用户对象

        Raises:
            ValueError: 如果token无效、已过期或密码不符合要求
        """
        # 验证密码强度
        is_valid, error_msg = validate_password_strength(new_password)
        if not is_valid:
            raise ValueError(error_msg)

        # 查找用户（通过密码重置token）
        stmt = select(User).where(User.password_reset_token == token)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("密码重置token无效")

        # 验证token是否有效
        if not user.is_password_reset_token_valid():
            raise ValueError("密码重置token已过期")

        # 更新密码
        user.password_hash = get_password_hash(new_password)
        user.password_reset_token = None
        user.password_reset_expires_at = None
        await db.commit()
        await db.refresh(user)

        logger.info(f"密码重置成功: {user.email} (ID: {user.id})")

        # 可选：撤销所有现有会话（提高安全性）
        # 第一阶段暂不实现，后续可优化
        # await AuthService.revoke_all_user_sessions(db, user.id)

        return user

    @staticmethod
    async def revoke_all_user_sessions(db: AsyncSession, user_id: str) -> int:
        """
        撤销用户的所有会话（用于密码重置等场景）

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            int: 撤销的会话数量
        """
        stmt = select(Session).where(
            Session.user_id == user_id,
            Session.is_revoked == False,
        )
        result = await db.execute(stmt)
        sessions = result.scalars().all()

        revoked_count = 0
        for session in sessions:
            session.revoke()
            revoked_count += 1

        if revoked_count > 0:
            await db.commit()
            logger.info(
                f"已撤销用户所有会话: user_id={user_id}, count={revoked_count}"
            )

        return revoked_count


# 创建全局服务实例
auth_service = AuthService()
