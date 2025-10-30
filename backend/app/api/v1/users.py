"""
用户管理API端点
提供用户信息管理、偏好设置管理和数据导出功能
"""
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.middleware.auth import get_current_active_user
from app.models.user import User, UserPreferences
from app.models.conversation import Conversation, Message, MessageRole
from app.models.report import Report, ReportType, ReportStatus
from app.schemas.user import (
    UserInfo,
    UserUpdate,
    UserDeleteRequest,
    UserDeleteResponse,
    PreferencesResponse,
    PreferencesUpdate,
    DataExportResponse,
    MigrationRequest,
    MigrationResponse,
    MigrationResult,
)
from app.services.user_service import user_service
from app.services.auth_service import auth_service
from app.core.security import verify_password
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# ================================
# 用户信息管理端点
# ================================

@router.get(
    "/me",
    response_model=UserInfo,
    summary="获取当前用户信息",
    description="获取当前登录用户的基本信息",
    tags=["Users"],
    responses={
        200: {"description": "成功返回用户信息"},
        401: {"description": "未认证"},
    }
)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
) -> UserInfo:
    """
    获取当前用户信息

    返回当前登录用户的基本信息，不包括敏感信息如密码哈希。
    """
    return UserInfo(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        email_verified=current_user.email_verified,
        created_at=current_user.created_at,
        last_login_at=current_user.last_login_at,
    )


@router.put(
    "/me",
    response_model=UserInfo,
    summary="更新用户信息",
    description="更新当前用户的基本信息（用户名等）",
    tags=["Users"],
    responses={
        200: {"description": "成功更新用户信息"},
        401: {"description": "未认证"},
    }
)
async def update_current_user_info(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> UserInfo:
    """
    更新用户信息

    允许用户更新自己的基本信息，如用户名。不允许修改邮箱和密码。
    """
    updated_user = await user_service.update_user_info(
        db=db,
        user=current_user,
        username=user_update.username,
    )

    return UserInfo(
        id=updated_user.id,
        email=updated_user.email,
        username=updated_user.username,
        email_verified=updated_user.email_verified,
        created_at=updated_user.created_at,
        last_login_at=updated_user.last_login_at,
    )


@router.delete(
    "/me",
    response_model=UserDeleteResponse,
    summary="删除账户",
    description="删除当前用户账户（需要密码确认）",
    tags=["Users"],
    responses={
        200: {"description": "账户已成功删除"},
        400: {"description": "密码错误"},
        401: {"description": "未认证"},
    }
)
async def delete_current_user(
    delete_request: UserDeleteRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> UserDeleteResponse:
    """
    删除用户账户

    需要提供密码进行确认。执行软删除，保留数据30天以便恢复。
    """
    try:
        await user_service.delete_user(
            db=db,
            user=current_user,
            password=delete_request.password,
        )
        return UserDeleteResponse(message="账户已成功删除")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ================================
# 偏好设置管理端点
# ================================

@router.get(
    "/me/preferences",
    response_model=PreferencesResponse,
    summary="获取用户偏好设置",
    description="获取当前用户的偏好设置",
    tags=["Users"],
    responses={
        200: {"description": "成功返回偏好设置"},
        401: {"description": "未认证"},
    }
)
async def get_user_preferences(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PreferencesResponse:
    """
    获取用户偏好设置

    返回当前用户的完整偏好设置。如果用户没有设置过偏好，返回默认值。
    """
    preferences = await user_service.get_user_preferences(
        db=db,
        user_id=current_user.id,
    )
    return PreferencesResponse(preferences=preferences)


@router.put(
    "/me/preferences",
    response_model=PreferencesResponse,
    summary="更新用户偏好设置",
    description="更新当前用户的偏好设置（支持部分更新）",
    tags=["Users"],
    responses={
        200: {"description": "成功更新偏好设置"},
        401: {"description": "未认证"},
    }
)
async def update_user_preferences(
    preferences_update: PreferencesUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PreferencesResponse:
    """
    更新用户偏好设置

    支持部分更新，只更新提供的字段，其他字段保持不变。
    """
    updated_preferences = await user_service.update_user_preferences(
        db=db,
        user_id=current_user.id,
        updates=preferences_update.preferences,
    )
    return PreferencesResponse(preferences=updated_preferences)


# ================================
# 数据导出端点
# ================================

@router.post(
    "/me/export-data",
    response_model=DataExportResponse,
    summary="导出用户数据",
    description="导出当前用户的所有数据（GDPR合规）",
    tags=["Users"],
    responses={
        200: {"description": "成功导出用户数据"},
        401: {"description": "未认证"},
    }
)
async def export_user_data(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> DataExportResponse:
    """
    导出用户数据

    导出当前用户的所有数据，包括用户信息、偏好设置、对话历史和报告列表。
    用于GDPR合规性，用户有权导出自己的数据。
    """
    data = await user_service.export_user_data(
        db=db,
        user_id=current_user.id,
    )

    return DataExportResponse(
        user=data["user"],
        preferences=data["preferences"],
        conversations=data["conversations"],
        reports=data["reports"],
        exported_at=datetime.fromisoformat(data["exported_at"]),
    )


# ================================
# 数据迁移端点
# ================================

@router.post(
    "/me/migrate-data",
    response_model=MigrationResponse,
    summary="迁移localStorage数据",
    description="将localStorage中的数据迁移到用户账号",
    tags=["Users"],
    responses={
        200: {"description": "数据迁移完成"},
        400: {"description": "迁移数据格式错误"},
        401: {"description": "未认证"},
    }
)
async def migrate_user_data(
    migration_request: MigrationRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> MigrationResponse:
    """
    迁移localStorage数据

    将用户浏览器localStorage中的对话历史、报告和偏好设置迁移到数据库中。
    支持部分数据迁移，会自动跳过无效数据。
    """
    from datetime import datetime
    import uuid

    results = {
        "conversations": {"total": 0, "success": 0, "failed": 0, "errors": []},
        "reports": {"total": 0, "success": 0, "failed": 0, "errors": []},
        "preferences": {"total": 0, "success": 0, "failed": 0, "errors": []},
    }

    # 迁移对话历史
    if migration_request.conversations:
        results["conversations"]["total"] = len(migration_request.conversations)
        for idx, conv_data in enumerate(migration_request.conversations):
            try:
                # 检查是否已存在
                from sqlalchemy import select
                stmt = select(Conversation).where(
                    Conversation.session_id == conv_data.session_id
                )
                result = await db.execute(stmt)
                existing_conv = result.scalar_one_or_none()

                if existing_conv:
                    # 如果已存在，更新user_id（如果未关联）
                    if not existing_conv.user_id:
                        existing_conv.user_id = current_user.id
                        await db.commit()
                    results["conversations"]["success"] += 1
                else:
                    # 创建新对话
                    conversation = Conversation(
                        session_id=conv_data.session_id,
                        title=conv_data.title,
                        user_id=current_user.id,
                        message_count=len(conv_data.messages),
                    )
                    db.add(conversation)
                    await db.flush()

                    # 创建消息
                    for msg_data in conv_data.messages:
                        message = Message(
                            conversation_id=conversation.id,
                            role=MessageRole(msg_data.get("role", "user")),
                            content=msg_data.get("content", ""),
                            created_at=conv_data.created_at if conv_data.created_at else datetime.utcnow(),
                        )
                        db.add(message)

                    await db.commit()
                    results["conversations"]["success"] += 1
            except Exception as e:
                logger.error(f"迁移对话失败: {str(e)}")
                results["conversations"]["failed"] += 1
                results["conversations"]["errors"].append({
                    "index": idx,
                    "error": str(e),
                })
                await db.rollback()

    # 迁移报告
    if migration_request.reports:
        results["reports"]["total"] = len(migration_request.reports)
        for idx, report_data in enumerate(migration_request.reports):
            try:
                # 检查是否已存在（通过share_id）
                if report_data.share_id:
                    from sqlalchemy import select
                    stmt = select(Report).where(Report.share_token == report_data.share_id)
                    result = await db.execute(stmt)
                    existing_report = result.scalar_one_or_none()

                    if existing_report:
                        # 如果已存在，更新user_id（如果未关联）
                        if not existing_report.user_id:
                            existing_report.user_id = current_user.id
                            await db.commit()
                        results["reports"]["success"] += 1
                        continue

                # 创建新报告
                report = Report(
                    user_id=current_user.id,
                    report_type=ReportType.DEEP_RESEARCH,  # 默认类型
                    status=ReportStatus.COMPLETED,
                    query=report_data.query if hasattr(report_data, 'query') else "",
                    title=report_data.title,
                    content_markdown=report_data.content,
                    symbol=report_data.symbol,
                    share_token=report_data.share_id,
                    created_at=report_data.created_at if report_data.created_at else datetime.utcnow(),
                )
                db.add(report)
                await db.commit()
                results["reports"]["success"] += 1
            except Exception as e:
                logger.error(f"迁移报告失败: {str(e)}")
                results["reports"]["failed"] += 1
                results["reports"]["errors"].append({
                    "index": idx,
                    "error": str(e),
                })
                await db.rollback()

    # 迁移偏好设置
    if migration_request.preferences:
        try:
            results["preferences"]["total"] = 1
            await user_service.update_user_preferences(
                db=db,
                user_id=current_user.id,
                updates=migration_request.preferences,
            )
            results["preferences"]["success"] = 1
        except Exception as e:
            logger.error(f"迁移偏好设置失败: {str(e)}")
            results["preferences"]["failed"] = 1
            results["preferences"]["errors"].append({
                "error": str(e),
            })

    # 构建响应
    total_failed = (
        results["conversations"]["failed"] +
        results["reports"]["failed"] +
        results["preferences"]["failed"]
    )

    return MigrationResponse(
        success=total_failed == 0,
        migrated={
            "conversations": MigrationResult(**results["conversations"]),
            "reports": MigrationResult(**results["reports"]),
            "preferences": MigrationResult(**results["preferences"]),
        },
        message=f"数据迁移完成，共{total_failed}个错误" if total_failed > 0 else "数据迁移成功完成",
    )

