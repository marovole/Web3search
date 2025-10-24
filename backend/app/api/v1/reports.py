"""
报告查询API端点
提供报告列表、详情查询等功能
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, asc
from typing import Optional

from app.core.database import get_db
from app.schemas.report import (
    ReportResponse,
    ReportListResponse,
    ReportSummary,
)
from app.models.report import Report, ReportType, ReportStatus


router = APIRouter()


# ================================
# 报告列表API
# ================================

@router.get(
    "/reports",
    response_model=ReportListResponse,
    summary="获取报告列表",
    description="分页查询报告列表，支持筛选和排序",
    tags=["Reports"],
)
async def get_reports(
    symbol: Optional[str] = Query(None, description="按币种筛选"),
    report_type: Optional[str] = Query(None, description="按类型筛选"),
    status: Optional[str] = Query(None, description="按状态筛选"),
    page: int = Query(1, description="页码", ge=1),
    page_size: int = Query(10, description="每页数量", ge=1, le=100),
    order_by: str = Query("created_at", description="排序字段"),
    order_desc: bool = Query(True, description="是否降序"),
    db: AsyncSession = Depends(get_db),
) -> ReportListResponse:
    """
    获取报告列表

    - 支持分页
    - 支持按币种、类型、状态筛选
    - 支持排序
    """
    try:
        # 构建查询
        query = select(Report)

        # 应用筛选条件
        if symbol:
            query = query.where(Report.symbol == symbol.upper())

        if report_type:
            query = query.where(Report.report_type == report_type)

        if status:
            query = query.where(Report.status == status)

        # 计算总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # 应用排序
        order_column = getattr(Report, order_by, Report.created_at)
        if order_desc:
            query = query.order_by(desc(order_column))
        else:
            query = query.order_by(asc(order_column))

        # 应用分页
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        # 执行查询
        result = await db.execute(query)
        reports = result.scalars().all()

        # 构建摘要列表
        summaries = []
        for report in reports:
            summary = ReportSummary(
                id=report.id,
                title=report.title or f"{report.symbol} 研究报告",
                symbol=report.symbol or "Unknown",
                query=report.query,
                tldr=report.tldr[:200] if report.tldr else "暂无摘要",
                report_type=report.report_type.value,
                status=report.status.value,
                quality_score=report.quality_score,
                generation_time=report.generation_time_seconds,
                created_at=report.created_at.isoformat(),
            )
            summaries.append(summary)

        return ReportListResponse(
            reports=summaries,
            total=total,
            page=page,
            page_size=page_size,
        )

    except Exception as e:
        print(f"❌ 查询报告列表错误: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"查询失败: {str(e)}"
        )


# ================================
# 报告详情API
# ================================

@router.get(
    "/reports/{report_id}",
    response_model=ReportResponse,
    summary="获取报告详情",
    description="获取完整的报告内容",
    tags=["Reports"],
)
async def get_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
) -> ReportResponse:
    """
    获取报告详情

    - 返回完整的Markdown报告
    - 包含所有元数据
    """
    try:
        # 查询报告
        stmt = select(Report).where(Report.id == report_id)
        result = await db.execute(stmt)
        report = result.scalar_one_or_none()

        if not report:
            raise HTTPException(status_code=404, detail="报告不存在")

        # 构建响应
        response = ReportResponse(
            id=report.id,
            symbol=report.symbol or "Unknown",
            query=report.query,
            title=report.title or f"{report.symbol} 研究报告",
            markdown_content=report.content_markdown or "",
            tldr=report.tldr or "",
            report_type=report.report_type.value,
            status=report.status.value,
            quality_score=report.quality_score,
            generation_time=report.generation_time_seconds,
            data_sources=report.data_sources,
            created_at=report.created_at.isoformat(),
            completed_at=report.completed_at.isoformat() if report.completed_at else None,
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 查询报告详情错误: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"查询失败: {str(e)}"
        )


# ================================
# 删除报告API
# ================================

@router.delete(
    "/reports/{report_id}",
    summary="删除报告",
    description="删除指定的报告",
    tags=["Reports"],
)
async def delete_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    删除报告

    - 软删除或硬删除
    - 需要管理员权限（后续添加）
    """
    try:
        # 查询报告
        stmt = select(Report).where(Report.id == report_id)
        result = await db.execute(stmt)
        report = result.scalar_one_or_none()

        if not report:
            raise HTTPException(status_code=404, detail="报告不存在")

        # 删除报告
        await db.delete(report)
        await db.commit()

        return {
            "message": "报告已删除",
            "report_id": report_id
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 删除报告错误: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"删除失败: {str(e)}"
        )


# ================================
# 报告统计API
# ================================

@router.get(
    "/reports/stats/summary",
    summary="报告统计",
    description="获取报告的统计信息",
    tags=["Reports"],
)
async def get_report_stats(
    db: AsyncSession = Depends(get_db),
):
    """
    获取报告统计信息

    - 总报告数
    - 按类型分组统计
    - 按状态分组统计
    """
    try:
        # 总报告数
        total_stmt = select(func.count(Report.id))
        total_result = await db.execute(total_stmt)
        total = total_result.scalar()

        # 按类型统计
        type_stmt = select(
            Report.report_type,
            func.count(Report.id)
        ).group_by(Report.report_type)
        type_result = await db.execute(type_stmt)
        by_type = {row[0].value: row[1] for row in type_result}

        # 按状态统计
        status_stmt = select(
            Report.status,
            func.count(Report.id)
        ).group_by(Report.status)
        status_result = await db.execute(status_stmt)
        by_status = {row[0].value: row[1] for row in status_result}

        # 平均质量得分
        avg_score_stmt = select(func.avg(Report.quality_score)).where(
            Report.quality_score.isnot(None)
        )
        avg_score_result = await db.execute(avg_score_stmt)
        avg_score = avg_score_result.scalar()

        return {
            "total_reports": total,
            "by_type": by_type,
            "by_status": by_status,
            "average_quality_score": round(avg_score, 2) if avg_score else None,
        }

    except Exception as e:
        print(f"❌ 获取统计信息错误: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"查询失败: {str(e)}"
        )
