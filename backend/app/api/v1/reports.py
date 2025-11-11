"""
报告查询API端点
提供报告列表、详情查询、PDF导出等功能
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, asc
from typing import Optional
import os

from app.core.database import get_db
from app.api.middleware.auth import optional_auth, get_current_user
from app.models.user import User
from app.schemas.report import (
    ReportResponse,
    ReportListResponse,
    ReportSummary,
    ShareReportRequest,
    ShareReportResponse,
    SharedReportResponse,
)
from app.models.report import Report, ReportType, ReportStatus
from app.services.report.pdf_exporter import pdf_exporter


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
    responses={
        200: {
            "description": "成功返回报告列表",
            "content": {
                "application/json": {
                    "example": {
                        "reports": [
                            {
                                "id": 123,
                                "title": "Bitcoin 深度研究报告",
                                "symbol": "BTC",
                                "query": "Bitcoin",
                                "tldr": "Bitcoin shows bullish momentum...",
                                "report_type": "deep_research",
                                "status": "completed",
                                "quality_score": 92,
                                "generation_time": 25.3,
                                "created_at": "2025-01-26T10:00:00"
                            }
                        ],
                        "total": 1,
                        "page": 1,
                        "page_size": 10
                    }
                }
            }
        },
        500: {"description": "服务器内部错误"},
    }
)
async def get_reports(
    symbol: Optional[str] = Query(None, description="按币种筛选"),
    report_type: Optional[str] = Query(None, description="按类型筛选"),
    status: Optional[str] = Query(None, description="按状态筛选"),
    page: int = Query(1, description="页码", ge=1),
    page_size: int = Query(10, description="每页数量", ge=1, le=100),
    order_by: str = Query("created_at", description="排序字段", regex="^(created_at|quality_score|generation_time|title|symbol)$"),
    order_desc: bool = Query(True, description="是否降序"),
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(optional_auth),
) -> ReportListResponse:
    """
    获取报告列表 - 分页查询所有研究报告

    该端点返回分页的报告列表,支持多维度筛选和排序。

    **筛选选项:**
    - `symbol`: 按币种筛选（如 BTC, ETH）
    - `report_type`: 按类型筛选（deep_research, quick_analysis）
    - `status`: 按状态筛选（completed, processing, failed）

    **排序选项:**
    - `order_by`: 排序字段（created_at, quality_score, generation_time）
    - `order_desc`: 是否降序（true/false）

    **分页:**
    - `page`: 页码（从1开始）
    - `page_size`: 每页数量（1-100）

    **速率限制:**
    - 30次/分钟（基于IP）

    **请求示例:**
    ```bash
    # 获取所有BTC报告，按创建时间降序
    curl "http://localhost:8000/api/v1/reports?symbol=BTC&page=1&page_size=10&order_by=created_at&order_desc=true"

    # 获取所有已完成的深度研究报告
    curl "http://localhost:8000/api/v1/reports?report_type=deep_research&status=completed"

    # 按质量评分降序获取报告
    curl "http://localhost:8000/api/v1/reports?order_by=quality_score&order_desc=true"
    ```

    **响应示例:**
    ```json
    {
      "reports": [
        {
          "id": 123,
          "title": "Bitcoin 深度研究报告",
          "symbol": "BTC",
          "query": "Bitcoin",
          "tldr": "Bitcoin shows bullish momentum with strong fundamentals...",
          "report_type": "deep_research",
          "status": "completed",
          "quality_score": 92,
          "generation_time": 25.3,
          "created_at": "2025-01-26T10:00:00"
        }
      ],
      "total": 1,
      "page": 1,
      "page_size": 10
    }
    ```
    """
    try:
        # 构建查询
        query = select(Report)

        # 如果用户已登录，只返回该用户的报告
        if current_user:
            query = query.where(Report.user_id == current_user.id)
        else:
            # 匿名用户只能看到没有关联用户的报告（公共报告）
            query = query.where(Report.user_id.is_(None))

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

        # 应用排序 - 使用安全的字段映射防止SQL注入
        ORDER_FIELDS_MAP = {
            'created_at': Report.created_at,
            'quality_score': Report.quality_score,
            'generation_time': Report.generation_time_seconds,
            'title': Report.title,
            'symbol': Report.symbol
        }

        order_column = ORDER_FIELDS_MAP.get(order_by, Report.created_at)
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
    responses={
        200: {
            "description": "成功返回报告详情",
            "content": {
                "application/json": {
                    "example": {
                        "id": 123,
                        "symbol": "BTC",
                        "query": "Bitcoin",
                        "title": "Bitcoin 深度研究报告",
                        "markdown_content": "# Bitcoin Deep Research Report\n\n## TLDR\n...",
                        "tldr": "Bitcoin shows bullish momentum...",
                        "report_type": "deep_research",
                        "status": "completed",
                        "quality_score": 92,
                        "generation_time": 25.3,
                        "data_sources": ["CoinGecko", "Etherscan"],
                        "created_at": "2025-01-26T10:00:00",
                        "completed_at": "2025-01-26T10:00:25"
                    }
                }
            }
        },
        404: {"description": "报告不存在"},
        500: {"description": "服务器内部错误"},
    }
)
async def get_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
) -> ReportResponse:
    """
    获取报告详情 - 获取完整的研究报告内容

    该端点返回指定报告的完整内容,包括Markdown格式的报告正文。

    **返回内容:**
    - 完整的Markdown报告
    - 所有分析维度数据
    - 质量评分和元数据
    - 数据源列表
    - 生成时间戳

    **速率限制:**
    - 30次/分钟（基于IP）

    **请求示例:**
    ```bash
    curl "http://localhost:8000/api/v1/reports/123"
    ```

    **响应示例:**
    ```json
    {
      "id": 123,
      "symbol": "BTC",
      "query": "Bitcoin",
      "title": "Bitcoin 深度研究报告",
      "markdown_content": "# Bitcoin Deep Research Report\\n\\n## TLDR\\nBitcoin shows bullish momentum...",
      "tldr": "Bitcoin shows bullish momentum with strong fundamentals...",
      "report_type": "deep_research",
      "status": "completed",
      "quality_score": 92,
      "generation_time": 25.3,
      "data_sources": ["CoinGecko", "Etherscan", "Twitter"],
      "created_at": "2025-01-26T10:00:00",
      "completed_at": "2025-01-26T10:00:25"
    }
    ```

    **错误响应:**
    ```json
    {
      "detail": "报告不存在"
    }
    ```
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
    description="删除指定的报告（需要认证，仅所有者或管理员可删除）",
    tags=["Reports"],
)
async def delete_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    删除报告

    - 需要用户认证
    - 只有报告所有者或管理员可以删除
    - 软删除或硬删除
    """
    try:
        # 查询报告
        stmt = select(Report).where(Report.id == report_id)
        result = await db.execute(stmt)
        report = result.scalar_one_or_none()

        if not report:
            raise HTTPException(status_code=404, detail="报告不存在")

        # 验证权限：只有所有者或超级用户可以删除
        if report.user_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(
                status_code=403,
                detail="无权限删除该报告"
            )

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


# ================================
# 报告分享API
# ================================

@router.post(
    "/reports/{report_id}/share",
    response_model=ShareReportResponse,
    summary="创建分享链接",
    description="为报告生成分享链接，可设置过期时间（需要认证，仅所有者或管理员可操作）",
    tags=["Reports"],
    responses={
        200: {
            "description": "成功创建分享链接",
            "content": {
                "application/json": {
                    "example": {
                        "share_token": "abc123def456",
                        "share_url": "https://web3search.com/shared/abc123def456",
                        "expires_at": "2025-02-26T10:00:00"
                    }
                }
            }
        },
        400: {"description": "只能分享已完成的报告"},
        403: {"description": "无权限分享该报告"},
        404: {"description": "报告不存在"},
        500: {"description": "服务器内部错误"},
    }
)
async def create_share_link(
    report_id: int,
    request: ShareReportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ShareReportResponse:
    """
    创建报告分享链接 - 生成可公开访问的报告链接

    该端点为已完成的报告生成唯一的分享链接,无需认证即可访问分享的内容。

    **权限要求:**
    - 需要用户认证
    - 只有报告所有者或管理员可以创建分享链接

    **特性:**
    - 🔗 生成唯一的分享令牌
    - ⏰ 可设置过期时间（1-365天）
    - 🔒 只能分享已完成的报告
    - 🚫 可随时禁用分享链接

    **请求参数:**
    - `expires_in_days`: 过期天数（1-365天，默认30天）

    **请求示例:**
    ```bash
    curl -X POST "http://localhost:8000/api/v1/reports/123/share" \\
      -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{
        "expires_in_days": 30
      }'
    ```

    **响应示例:**
    ```json
    {
      "share_token": "abc123def456",
      "share_url": "https://web3search.com/shared/abc123def456",
      "expires_at": "2025-02-26T10:00:00"
    }
    ```

    **使用分享链接:**
    ```bash
    # 任何人都可以通过分享链接访问报告（无需认证）
    curl "http://localhost:8000/api/v1/reports/shared/abc123def456"
    ```

    **错误响应:**
    ```json
    {
      "detail": "只能分享已完成的报告"
    }
    ```
    """
    try:
        # 查询报告
        stmt = select(Report).where(Report.id == report_id)
        result = await db.execute(stmt)
        report = result.scalar_one_or_none()

        if not report:
            raise HTTPException(status_code=404, detail="报告不存在")

        # 验证权限：只有所有者或超级用户可以分享
        if report.user_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(
                status_code=403,
                detail="无权限分享该报告"
            )

        # 只能分享已完成的报告
        if not report.is_completed:
            raise HTTPException(status_code=400, detail="只能分享已完成的报告")

        # 启用分享并生成令牌
        share_token = report.enable_sharing(expires_in_days=request.expires_in_days)

        # 保存到数据库
        await db.commit()
        await db.refresh(report)

        # 构建分享URL（TODO: 从配置获取域名）
        share_url = f"https://web3search.com/shared/{share_token}"

        return ShareReportResponse(
            share_token=share_token,
            share_url=share_url,
            expires_at=report.share_expires_at.isoformat() if report.share_expires_at else None
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 创建分享链接错误: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"创建分享链接失败: {str(e)}"
        )


@router.get(
    "/reports/shared/{share_token}",
    response_model=SharedReportResponse,
    summary="获取分享报告",
    description="通过分享令牌获取报告内容",
    tags=["Reports"],
)
async def get_shared_report(
    share_token: str,
    db: AsyncSession = Depends(get_db),
) -> SharedReportResponse:
    """
    获取分享的报告

    - 通过分享令牌访问
    - 验证过期时间
    - 不需要认证
    """
    try:
        # 查询报告
        stmt = select(Report).where(Report.share_token == share_token)
        result = await db.execute(stmt)
        report = result.scalar_one_or_none()

        if not report:
            raise HTTPException(status_code=404, detail="分享链接不存在")

        # 验证分享链接是否有效
        if not report.is_share_valid:
            raise HTTPException(status_code=403, detail="分享链接已过期或已禁用")

        # 构建响应（不包含敏感信息）
        response = SharedReportResponse(
            title=report.title or f"{report.symbol} 研究报告",
            symbol=report.symbol or "Unknown",
            markdown_content=report.content_markdown or "",
            tldr=report.tldr or "",
            report_type=report.report_type.value,
            quality_score=report.quality_score,
            data_sources=report.data_sources,
            created_at=report.created_at.isoformat(),
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 获取分享报告错误: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"获取分享报告失败: {str(e)}"
        )


@router.delete(
    "/reports/{report_id}/share",
    summary="禁用分享链接",
    description="禁用报告的分享链接",
    tags=["Reports"],
)
async def disable_share_link(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    禁用分享链接

    - 需要用户认证
    - 只有报告所有者或管理员可以禁用分享链接
    - 禁用后分享链接将无法访问
    """
    try:
        # 查询报告
        stmt = select(Report).where(Report.id == report_id)
        result = await db.execute(stmt)
        report = result.scalar_one_or_none()

        if not report:
            raise HTTPException(status_code=404, detail="报告不存在")

        # 验证权限：只有所有者或超级用户可以禁用分享
        if report.user_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(
                status_code=403,
                detail="无权限禁用该分享链接"
            )

        # 禁用分享
        report.disable_sharing()
        await db.commit()

        return {
            "message": "分享链接已禁用",
            "report_id": report_id
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 禁用分享链接错误: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"禁用分享链接失败: {str(e)}"
        )


# ================================
# PDF导出API
# ================================

@router.get(
    "/reports/{report_id}/export/pdf",
    summary="导出报告为PDF",
    description="将报告导出为PDF文件并下载（需要认证，仅所有者或管理员可导出）",
    tags=["Reports"],
    responses={
        200: {
            "description": "成功生成并返回PDF文件",
            "content": {"application/pdf": {}},
        },
        403: {"description": "无权限导出该报告"},
        404: {"description": "报告不存在"},
        400: {"description": "只能导出已完成的报告"},
        500: {"description": "PDF生成失败"},
    }
)
async def export_report_pdf(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    导出报告为PDF - 生成专业格式的PDF报告文件

    该端点将Markdown格式的报告转换为PDF文件,支持中文字体、表格和图表。

    **权限要求:**
    - 需要用户认证
    - 只有报告所有者或管理员可以导出PDF

    **特性:**
    - 📄 专业的PDF排版（A4页面、页眉页脚）
    - 🎨 自适应表格和图表渲染
    - 🌏 中文字体支持
    - ⏱️ 超时控制（30秒）
    - 🗑️ 自动清理临时文件

    **限制:**
    - 只能导出已完成的报告
    - PDF生成超时时间：30秒
    - 文件大小限制：50MB

    **请求示例:**
    ```bash
    # 下载PDF报告
    curl "http://localhost:8000/api/v1/reports/123/export/pdf" \\
      -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \\
      -o bitcoin_report.pdf
    ```

    **响应:**
    - Content-Type: application/pdf
    - Content-Disposition: attachment; filename="BTC_深度研究报告_20250126.pdf"

    **错误响应:**
    ```json
    {
      "detail": "只能导出已完成的报告"
    }
    ```
    """
    try:
        # 查询报告
        stmt = select(Report).where(Report.id == report_id)
        result = await db.execute(stmt)
        report = result.scalar_one_or_none()

        if not report:
            raise HTTPException(status_code=404, detail="报告不存在")

        # 验证权限：只有所有者或超级用户可以导出
        if report.user_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(
                status_code=403,
                detail="无权限导出该报告"
            )

        # 只能导出已完成的报告
        if not report.is_completed:
            raise HTTPException(status_code=400, detail="只能导出已完成的报告")

        # 检查Markdown内容是否存在
        if not report.content_markdown:
            raise HTTPException(status_code=400, detail="报告内容为空，无法导出")

        print(f"📄 开始为报告 {report_id} 生成PDF...")

        # 生成临时PDF文件路径 - 防止路径遍历攻击
        safe_symbol = "".join(c for c in (report.symbol or "Unknown") if c.isalnum())

        # 验证report_id防止路径遍历
        if not isinstance(report_id, int) or report_id <= 0:
            raise HTTPException(status_code=400, detail="Invalid report ID")

        # 生成安全的文件名
        pdf_filename = f"{safe_symbol}_{report_id}"
        temp_pdf_path = pdf_exporter.generate_temp_pdf_path(pdf_filename)

        # 额外路径安全检查
        import os
        if not os.path.normpath(temp_pdf_path).startswith(pdf_exporter.temp_dir):
            raise HTTPException(status_code=400, detail="Invalid file path")

        # 生成PDF
        title = report.title or f"{report.symbol} 深度研究报告"
        try:
            pdf_path = pdf_exporter.export_to_pdf(
                markdown_content=report.content_markdown,
                output_path=temp_pdf_path,
                title=title,
                timeout=30
            )
        except Exception as pdf_error:
            print(f"❌ PDF生成失败: {pdf_error}")
            raise HTTPException(
                status_code=500,
                detail=f"PDF生成失败: {str(pdf_error)}"
            )

        # 检查文件是否生成成功
        if not os.path.exists(pdf_path):
            raise HTTPException(status_code=500, detail="PDF文件生成失败")

        # 构建下载文件名
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d")
        download_filename = f"{safe_symbol}_深度研究报告_{timestamp}.pdf"

        # 返回PDF文件（FastAPI会自动处理文件传输和清理）
        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            filename=download_filename,
            headers={
                "Content-Disposition": f'attachment; filename="{download_filename}"',
                "Cache-Control": "no-cache",
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 导出PDF错误: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"导出PDF失败: {str(e)}"
        )
