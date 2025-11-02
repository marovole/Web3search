"""
用户管理相关的API数据模型
定义用户信息、偏好设置和数据迁移的请求/响应结构
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, field_validator
import re
import logging

logger = logging.getLogger(__name__)


# ================================
# 用户信息相关 Schemas
# ================================

class UserInfo(BaseModel):
    """用户信息响应"""
    id: str = Field(..., description="用户ID")
    email: str = Field(..., description="用户邮箱")
    username: Optional[str] = Field(None, description="用户名")
    email_verified: bool = Field(..., description="邮箱是否已验证")
    created_at: datetime = Field(..., description="注册时间")
    last_login_at: Optional[datetime] = Field(None, description="最后登录时间")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@example.com",
                "username": "crypto_trader",
                "email_verified": False,
                "created_at": "2025-01-01T00:00:00Z",
                "last_login_at": "2025-01-01T12:00:00Z"
            }
        }


class UserUpdate(BaseModel):
    """用户信息更新请求"""
    username: Optional[str] = Field(None, description="用户名", max_length=100)

    class Config:
        json_schema_extra = {
            "example": {
                "username": "new_username"
            }
        }


class UserDeleteRequest(BaseModel):
    """删除账户请求（需要密码确认）"""
    password: str = Field(..., description="用户密码（用于确认删除）")

    class Config:
        json_schema_extra = {
            "example": {
                "password": "SecurePass123"
            }
        }


class UserDeleteResponse(BaseModel):
    """删除账户响应"""
    message: str = Field(..., description="响应消息")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "账户已成功删除"
            }
        }


# ================================
# 偏好设置相关 Schemas
# ================================

class PreferencesResponse(BaseModel):
    """偏好设置响应"""
    preferences: Dict[str, Any] = Field(..., description="用户偏好设置")

    class Config:
        json_schema_extra = {
            "example": {
                "preferences": {
                    "theme": "dark",
                    "language": "zh-CN",
                    "notifications": {
                        "email": True,
                        "price_alerts": False
                    },
                    "display": {
                        "compact_mode": False,
                        "default_timeframe": "7d"
                    },
                    "research": {
                        "default_model": "qwen3-235b",
                        "auto_export": False
                    }
                }
            }
        }


class PreferencesUpdate(BaseModel):
    """偏好设置更新请求"""
    preferences: Dict[str, Any] = Field(..., description="要更新的偏好设置（部分更新）")

    class Config:
        json_schema_extra = {
            "example": {
                "preferences": {
                    "theme": "dark",
                    "display": {
                        "compact_mode": True
                    }
                }
            }
        }


# ================================
# 数据导出相关 Schemas
# ================================

class DataExportResponse(BaseModel):
    """数据导出响应"""
    user: Dict[str, Any] = Field(..., description="用户信息")
    preferences: Dict[str, Any] = Field(..., description="偏好设置")
    conversations: List[Dict[str, Any]] = Field(default_factory=list, description="对话历史")
    reports: List[Dict[str, Any]] = Field(default_factory=list, description="报告列表")
    exported_at: datetime = Field(..., description="导出时间")

    class Config:
        json_schema_extra = {
            "example": {
                "user": {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "email": "user@example.com",
                    "created_at": "2025-01-01T00:00:00Z"
                },
                "preferences": {...},
                "conversations": [...],
                "reports": [...],
                "exported_at": "2025-01-01T12:00:00Z"
            }
        }


# ================================
# 数据迁移相关 Schemas
# ================================

class ConversationMigrationData(BaseModel):
    """对话历史迁移数据"""
    session_id: str = Field(..., description="会话ID")
    title: Optional[str] = Field(None, description="对话标题")
    messages: List[Dict[str, Any]] = Field(default_factory=list, description="消息列表")
    created_at: Optional[datetime] = Field(None, description="创建时间")


class ReportMigrationData(BaseModel):
    """报告迁移数据"""
    share_id: Optional[str] = Field(None, description="分享ID")
    symbol: Optional[str] = Field(None, description="代币符号")
    title: Optional[str] = Field(None, description="报告标题")
    content: Optional[str] = Field(None, description="报告内容")
    created_at: Optional[datetime] = Field(None, description="创建时间")


class MigrationRequest(BaseModel):
    """数据迁移请求"""
    conversations: List[ConversationMigrationData] = Field(default_factory=list, description="对话历史", max_items=100)
    reports: List[ReportMigrationData] = Field(default_factory=list, description="报告列表", max_items=50)
    preferences: Optional[Dict[str, Any]] = Field(None, description="偏好设置")
    watchlist: Optional[List[Dict[str, Any]]] = Field(None, description="监控列表（可选）", max_items=20)

    @field_validator('conversations')
    @classmethod
    def validate_conversations(cls, v):
        """验证对话历史数据"""
        if not v:
            return v

        for conv in v:
            # 验证session_id格式
            if not conv.session_id or len(conv.session_id) > 100:
                raise ValueError('对话session_id无效')

            # 验证标题长度
            if conv.title and len(conv.title) > 200:
                raise ValueError('对话标题过长')

            # 验证消息数量
            if conv.messages and len(conv.messages) > 1000:
                raise ValueError('对话消息数量过多')

        return v

    @field_validator('reports')
    @classmethod
    def validate_reports(cls, v):
        """验证报告数据"""
        if not v:
            return v

        for report in v:
            # 验证symbol格式
            if report.symbol and not re.match(r'^[A-Z0-9]{1,10}$', report.symbol):
                raise ValueError(f'报告symbol格式无效: {report.symbol}')

            # 验证标题长度
            if report.title and len(report.title) > 300:
                raise ValueError('报告标题过长')

            # 验证内容长度
            if report.content and len(report.content) > 100000:
                raise ValueError('报告内容过长')

        return v

    @field_validator('preferences')
    @classmethod
    def validate_preferences(cls, v):
        """验证偏好设置数据"""
        if not v:
            return v

        # 限制偏好设置数据大小
        if len(str(v)) > 10000:
            raise ValueError('偏好设置数据过大')

        # 验证已知的偏好设置键
        allowed_keys = {
            'theme', 'language', 'chatMode', 'notifications',
            'privacy', 'display', 'advanced', 'custom'
        }

        for key in v.keys():
            if key not in allowed_keys:
                logger.warning(f"未知的偏好设置键: {key}")

        return v

    class Config:
        json_schema_extra = {
            "example": {
                "conversations": [
                    {
                        "session_id": "uuid",
                        "title": "对话标题",
                        "messages": [...],
                        "created_at": "2025-01-01T00:00:00Z"
                    }
                ],
                "reports": [
                    {
                        "share_id": "uuid",
                        "symbol": "BTC",
                        "title": "报告标题",
                        "content": "...",
                        "created_at": "2025-01-01T00:00:00Z"
                    }
                ],
                "preferences": {
                    "theme": "dark"
                }
            }
        }


class MigrationResult(BaseModel):
    """迁移结果（单个数据类型）"""
    total: int = Field(..., description="总数")
    success: int = Field(..., description="成功数")
    failed: int = Field(..., description="失败数")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="错误列表")


class MigrationResponse(BaseModel):
    """数据迁移响应"""
    success: bool = Field(..., description="是否成功")
    migrated: Dict[str, MigrationResult] = Field(..., description="迁移结果详情")
    message: str = Field(..., description="响应消息")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "migrated": {
                    "conversations": {
                        "total": 10,
                        "success": 9,
                        "failed": 1,
                        "errors": [
                            {
                                "index": 5,
                                "error": "Invalid session_id format"
                            }
                        ]
                    },
                    "reports": {
                        "total": 5,
                        "success": 5,
                        "failed": 0,
                        "errors": []
                    },
                    "preferences": {
                        "total": 1,
                        "success": 1,
                        "failed": 0,
                        "errors": []
                    }
                },
                "message": "Migration completed with 1 error"
            }
        }

