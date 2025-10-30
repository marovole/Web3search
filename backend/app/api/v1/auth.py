"""
认证API端点
提供用户注册、登录、Token刷新和密码重置功能
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.auth import (
    RegisterRequest,
    RegisterResponse,
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
)
from app.services.auth_service import auth_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


def get_client_ip(request: Request) -> str:
    """从请求中提取客户端IP地址"""
    # 检查代理头
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # 回退到直接连接
    if request.client:
        return request.client.host
    
    return "unknown"


# ================================
# 注册端点
# ================================

@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="用户注册",
    description="注册新用户账号",
    tags=["Auth"],
    responses={
        201: {
            "description": "注册成功",
            "content": {
                "application/json": {
                    "example": {
                        "user_id": "550e8400-e29b-41d4-a716-446655440000",
                        "email": "user@example.com",
                        "username": "crypto_trader",
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "refresh_token": "dGhpc2lzYXJlZnJlc2h0b2tlbg...",
                        "token_type": "bearer"
                    }
                }
            }
        },
        400: {"description": "请求参数错误（邮箱已存在、密码不符合要求等）"},
        422: {"description": "请求验证失败"},
    }
)
async def register(
    request_data: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> RegisterResponse:
    """
    用户注册接口

    注册新用户账号，自动创建默认偏好设置。

    **流程:**
    1. 验证邮箱格式和唯一性
    2. 验证密码强度（至少8字符，包含字母和数字）
    3. 创建用户和默认偏好设置
    4. 生成Access Token和Refresh Token
    5. 返回用户信息和Token

    **请求示例:**
    ```bash
    curl -X POST "http://localhost:8000/api/v1/auth/register" \\
      -H "Content-Type: application/json" \\
      -d '{
        "email": "user@example.com",
        "password": "SecurePass123",
        "username": "crypto_trader"
      }'
    ```

    **响应示例:**
    ```json
    {
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com",
      "username": "crypto_trader",
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "refresh_token": "dGhpc2lzYXJlZnJlc2h0b2tlbg...",
      "token_type": "bearer"
    }
    ```
    """
    try:
        # 提取客户端信息
        ip_address = get_client_ip(request)
        user_agent = request.headers.get("User-Agent", "")

        # 注册用户
        user, access_token, _ = await auth_service.register_user(
            db=db,
            email=request_data.email,
            password=request_data.password,
            username=request_data.username,
        )

        # 创建会话（生成refresh_token）
        refresh_token = await auth_service.create_session(
            db=db,
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return RegisterResponse(
            user_id=user.id,
            email=user.email,
            username=user.username,
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注册失败，请稍后重试",
        )


# ================================
# 登录端点
# ================================

@router.post(
    "/login",
    response_model=LoginResponse,
    summary="用户登录",
    description="使用邮箱和密码登录",
    tags=["Auth"],
    responses={
        200: {
            "description": "登录成功",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "refresh_token": "dGhpc2lzYXJlZnJlc2h0b2tlbg...",
                        "token_type": "bearer",
                        "user": {
                            "id": "550e8400-e29b-41d4-a716-446655440000",
                            "email": "user@example.com",
                            "username": "crypto_trader",
                            "email_verified": False
                        }
                    }
                }
            }
        },
        401: {"description": "认证失败（邮箱或密码错误）"},
        422: {"description": "请求验证失败"},
    }
)
async def login(
    request_data: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    """
    用户登录接口

    使用邮箱和密码登录，成功后返回Access Token和Refresh Token。

    **流程:**
    1. 验证邮箱和密码
    2. 检查账户是否激活
    3. 更新最后登录时间
    4. 创建新会话
    5. 返回Token和用户信息

    **请求示例:**
    ```bash
    curl -X POST "http://localhost:8000/api/v1/auth/login" \\
      -H "Content-Type: application/json" \\
      -d '{
        "email": "user@example.com",
        "password": "SecurePass123"
      }'
    ```

    **响应示例:**
    ```json
    {
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "refresh_token": "dGhpc2lzYXJlZnJlc2h0b2tlbg...",
      "token_type": "bearer",
      "user": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "email": "user@example.com",
        "username": "crypto_trader",
        "email_verified": false
      }
    }
    ```
    """
    # 认证用户
    user = await auth_service.authenticate_user(
        db=db,
        email=request_data.email,
        password=request_data.password,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
        )

    # 生成Token
    from app.core.security import create_access_token

    access_token = create_access_token(
        data={"user_id": user.id, "email": user.email}
    )

    # 提取客户端信息
    ip_address = get_client_ip(request)
    user_agent = request.headers.get("User-Agent", "")

    # 创建会话
    refresh_token = await auth_service.create_session(
        db=db,
        user_id=user.id,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user={
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "email_verified": user.email_verified,
        },
    )


# ================================
# Token刷新端点
# ================================

@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
    summary="刷新Access Token",
    description="使用Refresh Token获取新的Access Token",
    tags=["Auth"],
    responses={
        200: {
            "description": "Token刷新成功",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "refresh_token": None,
                        "token_type": "bearer"
                    }
                }
            }
        },
        400: {"description": "Refresh Token无效或已过期"},
        422: {"description": "请求验证失败"},
    }
)
async def refresh_token(
    request_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> RefreshTokenResponse:
    """
    Token刷新接口

    使用Refresh Token获取新的Access Token。初始实现不轮换Refresh Token。

    **流程:**
    1. 验证Refresh Token有效性
    2. 检查会话是否已撤销或过期
    3. 更新会话最后使用时间
    4. 生成新的Access Token
    5. 返回新Token（Refresh Token不轮换）

    **请求示例:**
    ```bash
    curl -X POST "http://localhost:8000/api/v1/auth/refresh" \\
      -H "Content-Type: application/json" \\
      -d '{
        "refresh_token": "dGhpc2lzYXJlZnJlc2h0b2tlbg..."
      }'
    ```

    **响应示例:**
    ```json
    {
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "refresh_token": null,
      "token_type": "bearer"
    }
    ```
    """
    try:
        access_token, new_refresh_token = await auth_service.refresh_access_token(
            db=db,
            refresh_token=request_data.refresh_token,
        )

        return RefreshTokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ================================
# 密码重置端点
# ================================

@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse,
    summary="请求密码重置",
    description="发送密码重置邮件（第一阶段仅记录日志）",
    tags=["Auth"],
    responses={
        200: {
            "description": "请求已处理",
            "content": {
                "application/json": {
                    "example": {
                        "message": "如果该邮箱存在，密码重置链接已发送"
                    }
                }
            }
        },
        422: {"description": "请求验证失败"},
    }
)
async def forgot_password(
    request_data: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> ForgotPasswordResponse:
    """
    忘记密码接口

    请求密码重置。如果邮箱存在，会生成密码重置token。
    
    **注意:** 第一阶段不实际发送邮件，token会在日志中记录。后续阶段会集成邮件服务。

    **流程:**
    1. 验证邮箱是否存在
    2. 生成密码重置token（1小时有效期）
    3. 记录日志（第一阶段）
    4. 返回成功消息（不暴露用户是否存在的信息）

    **请求示例:**
    ```bash
    curl -X POST "http://localhost:8000/api/v1/auth/forgot-password" \\
      -H "Content-Type: application/json" \\
      -d '{
        "email": "user@example.com"
      }'
    ```

    **响应示例:**
    ```json
    {
      "message": "如果该邮箱存在，密码重置链接已发送"
    }
    ```
    """
    # 尝试生成重置token（如果用户存在）
    await auth_service.initiate_password_reset(
        db=db,
        email=request_data.email,
    )

    # 无论用户是否存在，都返回相同的消息（安全考虑）
    return ForgotPasswordResponse(
        message="如果该邮箱存在，密码重置链接已发送"
    )


@router.post(
    "/reset-password",
    response_model=ResetPasswordResponse,
    summary="重置密码",
    description="使用重置token设置新密码",
    tags=["Auth"],
    responses={
        200: {
            "description": "密码重置成功",
            "content": {
                "application/json": {
                    "example": {
                        "message": "密码已成功重置"
                    }
                }
            }
        },
        400: {"description": "Token无效、已过期或密码不符合要求"},
        422: {"description": "请求验证失败"},
    }
)
async def reset_password(
    request_data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> ResetPasswordResponse:
    """
    重置密码接口

    使用密码重置token设置新密码。

    **流程:**
    1. 验证重置token有效性
    2. 验证新密码强度
    3. 更新密码哈希
    4. 清除重置token
    5. 返回成功消息

    **注意:** 初始实现不自动撤销现有会话，后续可优化。

    **请求示例:**
    ```bash
    curl -X POST "http://localhost:8000/api/v1/auth/reset-password" \\
      -H "Content-Type: application/json" \\
      -d '{
        "token": "dGhpc2lzYXBhc3N3b3JkcmVzZXR0b2tlbg...",
        "new_password": "NewSecurePass123"
      }'
    ```

    **响应示例:**
    ```json
    {
      "message": "密码已成功重置"
    }
    ```
    """
    try:
        await auth_service.reset_password(
            db=db,
            token=request_data.token,
            new_password=request_data.new_password,
        )

        return ResetPasswordResponse(
            message="密码已成功重置"
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ================================
# 登出端点
# ================================

@router.post(
    "/logout",
    summary="用户登出",
    description="登出当前用户，撤销Refresh Token",
    tags=["Auth"],
    responses={
        200: {
            "description": "登出成功",
            "content": {
                "application/json": {
                    "example": {
                        "message": "已成功登出"
                    }
                }
            }
        },
        401: {"description": "未认证"},
    }
)
async def logout(
    refresh_token: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
) -> dict:
    """
    用户登出接口

    撤销Refresh Token，清除Cookie，使Token失效。

    **流程:**
    1. 验证用户身份（通过Authorization header或refresh_token参数）
    2. 撤销用户的Refresh Token
    3. 清除Cookie（如果使用）
    4. 返回成功消息

    **注意:** 
    - 可以从Authorization header获取用户信息
    - 也可以从refresh_token参数获取（用于清除Cookie场景）
    - 如果两者都未提供，返回401

    **请求示例:**
    ```bash
    curl -X POST "http://localhost:8000/api/v1/auth/logout" \\
      -H "Authorization: Bearer <access_token>"
    ```
    """
    from app.models.user import Session
    from app.core.security import verify_password
    from sqlalchemy import select
    from datetime import datetime

    user_id = None

    # 优先从current_user获取（如果提供了Authorization header）
    if current_user:
        user_id = current_user.id
    # 或者从refresh_token获取
    elif refresh_token:
        # 查找对应的会话
        stmt = select(Session).where(
            Session.is_revoked == False,
            Session.expires_at > datetime.utcnow(),
        )
        result = await db.execute(stmt)
        sessions = result.scalars().all()

        for session in sessions:
            if verify_password(refresh_token, session.refresh_token_hash):
                user_id = session.user_id
                break

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未认证",
        )

    # 撤销用户的所有会话
    await auth_service.revoke_all_user_sessions(db, user_id)

    logger.info(f"用户登出成功: user_id={user_id}")

    return {"message": "已成功登出"}
