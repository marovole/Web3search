"""
聊天API端点
提供Quick Chat和Deep Research功能
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator
import uuid
import json

from app.core.database import get_db
from app.schemas.chat import (
    QuickChatRequest,
    QuickChatResponse,
    DeepResearchRequest,
    DeepResearchResponse,
    ErrorResponse,
)
from app.services.research_engine import quick_chat_engine, deep_research_engine
from app.services.report import report_generator
from app.models.report import Report, ReportType, ReportStatus
from app.models.conversation import Conversation, Message, MessageRole


router = APIRouter()


# ================================
# Quick Chat API
# ================================

@router.post(
    "/quick-chat",
    response_model=QuickChatResponse,
    summary="快速对话",
    description="3秒内快速回答加密货币相关问题",
    tags=["Chat"],
)
async def quick_chat(
    request: QuickChatRequest,
    db: AsyncSession = Depends(get_db),
) -> QuickChatResponse:
    """
    快速对话接口

    - 3秒内响应
    - 支持加密货币查询、市场概览等
    - 简洁准确的回答
    """
    try:
        # 生成或使用现有session_id
        session_id = request.session_id or str(uuid.uuid4())

        # 调用Quick Chat引擎（非流式）
        result = await quick_chat_engine.chat(
            query=request.query,
            stream=False,
        )

        # 构建响应
        response = QuickChatResponse(
            content=result["content"],
            symbol=result.get("symbol"),
            query_type=result["metadata"]["query_type"],
            response_time=result["metadata"]["response_time"],
            model=result["metadata"]["model"],
            session_id=session_id,
        )

        # TODO: 保存到数据库（对话历史）
        # 这里可以保存Conversation和Message记录

        return response

    except Exception as e:
        print(f"❌ Quick Chat错误: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Quick Chat处理失败: {str(e)}"
        )


@router.post(
    "/quick-chat/stream",
    summary="快速对话（流式）",
    description="流式返回Quick Chat响应",
    tags=["Chat"],
)
async def quick_chat_stream(
    request: QuickChatRequest,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """
    快速对话流式接口

    - Server-Sent Events (SSE)格式
    - 逐字返回，提升用户体验
    """
    async def generate() -> AsyncGenerator[str, None]:
        try:
            # 调用Quick Chat引擎（流式）
            stream_generator = await quick_chat_engine.chat(
                query=request.query,
                stream=True,
            )

            # 流式返回
            async for chunk in stream_generator:
                data = json.dumps({"content": chunk, "done": False}, ensure_ascii=False)
                yield f"data: {data}\n\n"

            # 发送完成信号
            data = json.dumps({"content": "", "done": True}, ensure_ascii=False)
            yield f"data: {data}\n\n"

        except Exception as e:
            print(f"❌ Quick Chat Stream错误: {e}")
            error_data = json.dumps({"error": str(e)}, ensure_ascii=False)
            yield f"data: {error_data}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


# ================================
# Deep Research API
# ================================

@router.post(
    "/deep-research",
    response_model=DeepResearchResponse,
    summary="深度研究",
    description="生成15-30秒的全面深度研究报告",
    tags=["Research"],
)
async def deep_research(
    request: DeepResearchRequest,
    db: AsyncSession = Depends(get_db),
) -> DeepResearchResponse:
    """
    深度研究接口

    - 15-30秒生成时间
    - 六维度全面分析
    - 生成结构化Markdown报告
    """
    try:
        # 生成或使用现有session_id
        session_id = request.session_id or str(uuid.uuid4())

        print(f"🔍 开始Deep Research: {request.query}")

        # 调用Deep Research引擎
        research_result = await deep_research_engine.research(
            query=request.query,
            symbol=request.symbol,
        )

        # 检查是否有错误
        if "error" in research_result:
            raise HTTPException(
                status_code=404,
                detail=research_result["error"]
            )

        # 生成Markdown报告
        markdown_content = report_generator.generate_markdown(research_result)

        # 生成标题
        title = report_generator.generate_title(research_result)

        # 计算质量得分
        quality_score = report_generator.calculate_quality_score(research_result)

        # 保存到数据库
        report = Report(
            symbol=research_result["symbol"],
            query=request.query,
            title=title,
            report_type=ReportType.DEEP_RESEARCH,
            status=ReportStatus.COMPLETED,
            content_markdown=markdown_content,
            tldr=research_result["tldr"],
            sections=research_result["sections"],
            data_sources=research_result["data_sources"],
            models_used=research_result["models_used"],
            generation_time_seconds=research_result["generation_time"],
            quality_score=quality_score,
        )

        db.add(report)
        await db.commit()
        await db.refresh(report)

        print(f"✅ Deep Research完成，报告ID: {report.id}")

        # 构建响应
        response = DeepResearchResponse(
            report_id=report.id,
            symbol=research_result["symbol"],
            query=request.query,
            tldr=research_result["tldr"],
            sections=research_result["sections"],
            conclusion=research_result["conclusion"],
            markdown_content=markdown_content,
            data_sources=research_result["data_sources"],
            models_used=research_result["models_used"],
            generation_time=research_result["generation_time"],
            quality_score=quality_score,
            timestamp=research_result["timestamp"],
            session_id=session_id,
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Deep Research错误: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Deep Research处理失败: {str(e)}"
        )


@router.get(
    "/deep-research/status/{report_id}",
    summary="查询研究状态",
    description="查询Deep Research报告的生成状态",
    tags=["Research"],
)
async def get_research_status(
    report_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    查询报告生成状态

    - 用于轮询检查报告是否完成
    - 返回当前状态和进度
    """
    from sqlalchemy import select

    try:
        # 查询报告
        stmt = select(Report).where(Report.id == report_id)
        result = await db.execute(stmt)
        report = result.scalar_one_or_none()

        if not report:
            raise HTTPException(status_code=404, detail="报告不存在")

        return {
            "report_id": report.id,
            "status": report.status.value,
            "generation_time": report.generation_time_seconds,
            "quality_score": report.quality_score,
            "created_at": report.created_at.isoformat(),
            "completed_at": report.completed_at.isoformat() if report.completed_at else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 查询状态错误: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"查询失败: {str(e)}"
        )
