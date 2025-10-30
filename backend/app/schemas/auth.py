"""
认证相关的API数据模型
定义注册、登录、Token刷新和密码重置的请求/响应结构
"""
from typing import Optional
from pydantic import BaseModel, Field, EmailStr


# ================================
# 注册相关 Schemas
# ================================

class RegisterRequest(BaseModel):
    """用户注册请求"""
    email: EmailStr = Field(..., description="用户邮箱（用于登录）")
    password: str = Field(..., description="用户密码（至少8字符，包含字母和数字）", min_length=8)
    username: Optional[str] = Field(None, description="用户名（可选）", max_length=100)

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123",
                "username": "crypto_trader"
            }
        }


class RegisterResponse(BaseModel):
    """用户注册响应"""
    user_id: str = Field(..., description="用户ID")
    email: str = Field(..., description="用户邮箱")
    username: Optional[str] = Field(None, description="用户名")
    access_token: str = Field(..., description="Access Token（JWT格式）")
    refresh_token: str = Field(..., description="Refresh Token（用于刷新Access Token）")
    token_type: str = Field(default="bearer", description="Token类型")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@example.com",
                "username": "crypto_trader",
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "dGhpc2lzYXJlZnJlc2h0b2tlbg...",
                "token_type": "bearer"
            }
        }


# ================================
# 登录相关 Schemas
# ================================

class LoginRequest(BaseModel):
    """用户登录请求"""
    email: EmailStr = Field(..., description="用户邮箱")
    password: str = Field(..., description="用户密码")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123"
            }
        }


class LoginResponse(BaseModel):
    """用户登录响应"""
    access_token: str = Field(..., description="Access Token（JWT格式）")
    refresh_token: str = Field(..., description="Refresh Token（用于刷新Access Token）")
    token_type: str = Field(default="bearer", description="Token类型")
    user: dict = Field(..., description="用户基本信息")

    class Config:
        json_schema_extra = {
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


# ================================
# Token刷新相关 Schemas
# ================================

class RefreshTokenRequest(BaseModel):
    """Token刷新请求"""
    refresh_token: str = Field(..., description="Refresh Token")

    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "dGhpc2lzYXJlZnJlc2h0b2tlbg..."
            }
        }


class RefreshTokenResponse(BaseModel):
    """Token刷新响应"""
    access_token: str = Field(..., description="新的Access Token（JWT格式）")
    refresh_token: Optional[str] = Field(None, description="新的Refresh Token（如果启用轮换）")
    token_type: str = Field(default="bearer", description="Token类型")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": None,
                "token_type": "bearer"
            }
        }


# ================================
# 密码重置相关 Schemas
# ================================

class ForgotPasswordRequest(BaseModel):
    """忘记密码请求"""
    email: EmailStr = Field(..., description="用户邮箱")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }


class ForgotPasswordResponse(BaseModel):
    """忘记密码响应"""
    message: str = Field(..., description="响应消息")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "如果该邮箱存在，密码重置链接已发送"
            }
        }


class ResetPasswordRequest(BaseModel):
    """重置密码请求"""
    token: str = Field(..., description="密码重置Token")
    new_password: str = Field(..., description="新密码（至少8字符，包含字母和数字）", min_length=8)

    class Config:
        json_schema_extra = {
            "example": {
                "token": "dGhpc2lzYXBhc3N3b3JkcmVzZXR0b2tlbg...",
                "new_password": "NewSecurePass123"
            }
        }


class ResetPasswordResponse(BaseModel):
    """重置密码响应"""
    message: str = Field(..., description="响应消息")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "密码已成功重置"
            }
        }
