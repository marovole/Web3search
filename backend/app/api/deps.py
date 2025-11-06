"""
API依赖项
提供用于API端点的通用依赖项
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.api.middleware.auth import get_current_user, get_current_active_user, optional_auth


async def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    要求当前用户必须是管理员

    用于需要管理员权限的端点。

    Args:
        current_user: 当前用户（来自get_current_user）

    Returns:
        User: 当前管理员用户对象

    Raises:
        HTTPException: 如果用户不是管理员
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账户未激活",
        )

    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限",
        )

    return current_user


# 重新导出常用的认证依赖项
__all__ = [
    "get_current_user",
    "get_current_active_user",
    "optional_auth",
    "require_admin",
]
