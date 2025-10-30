"""
认证中间件和依赖项
提供用于保护API端点的认证依赖项
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import verify_token, get_user_id_from_token
from app.models.user import User

# HTTP Bearer Token 安全方案
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    从Access Token中提取当前用户

    用于需要认证的端点，从Authorization header中提取Bearer Token，
    验证Token有效性，并返回对应的用户对象。

    Args:
        credentials: HTTP Bearer Token凭证
        db: 数据库会话

    Returns:
        User: 当前用户对象

    Raises:
        HTTPException: 如果Token无效或用户不存在
    """
    token = credentials.credentials

    # 验证Token
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的访问令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 从Token中提取用户ID
    user_id = payload.get("user_id") or payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token中缺少用户信息",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 查询用户
    stmt = select(User).where(
        User.id == user_id,
        User.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    获取当前活跃用户

    检查用户账户是否激活，用于需要活跃账户的端点。

    Args:
        current_user: 当前用户（来自get_current_user）

    Returns:
        User: 当前活跃用户对象

    Raises:
        HTTPException: 如果账户未激活
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账户未激活",
        )

    return current_user


async def optional_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    可选的认证依赖项

    用于可选登录功能（如匿名用户可以访问，但登录用户可以获取个性化内容）。
    如果提供了有效的Token，返回用户对象；否则返回None。

    Args:
        credentials: HTTP Bearer Token凭证（可选）
        db: 数据库会话

    Returns:
        Optional[User]: 如果提供了有效Token返回用户对象，否则返回None
    """
    if not credentials:
        return None

    try:
        token = credentials.credentials
        payload = verify_token(token)
        if not payload:
            return None

        user_id = payload.get("user_id") or payload.get("sub")
        if not user_id:
            return None

        stmt = select(User).where(
            User.id == user_id,
            User.deleted_at.is_(None),
            User.is_active == True,
        )
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        return user
    except Exception:
        # 如果任何错误发生，返回None（可选认证失败不影响访问）
        return None
