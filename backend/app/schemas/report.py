"""
报告相关的API数据模型
定义报告查询、列表的响应结构
"""
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


# ================================
# Report Schemas
# ================================

class ReportSummary(BaseModel):
    """报告摘要（用于列表显示）"""
    id: int = Field(..., description="报告ID")
    title: str = Field(..., description="报告标题")
    symbol: str = Field(..., description="币种符号")
    query: str = Field(..., description="用户查询")
    tldr: str = Field(..., description="简短摘要")
    report_type: str = Field(..., description="报告类型")
    status: str = Field(..., description="报告状态")
    quality_score: Optional[int] = Field(None, description="质量得分")
    generation_time: Optional[float] = Field(None, description="生成耗时")
    created_at: str = Field(..., description="创建时间")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "title": "BTC 深度研究报告 - 2025-01-25 10:30",
                "symbol": "BTC",
                "query": "分析比特币",
                "tldr": "比特币是第一大加密货币，当前价格...",
                "report_type": "deep_research",
                "status": "completed",
                "quality_score": 90,
                "generation_time": 28.5,
                "created_at": "2025-01-25T10:30:00Z"
            }
        }


class ReportResponse(BaseModel):
    """完整报告响应"""
    id: int = Field(..., description="报告ID")
    symbol: str = Field(..., description="币种符号")
    query: str = Field(..., description="用户查询")
    title: str = Field(..., description="报告标题")
    markdown_content: str = Field(..., description="Markdown格式报告")
    tldr: str = Field(..., description="TL;DR摘要")
    report_type: str = Field(..., description="报告类型")
    status: str = Field(..., description="报告状态")
    quality_score: Optional[int] = Field(None, description="质量得分")
    generation_time: Optional[float] = Field(None, description="生成耗时（秒）")
    data_sources: Optional[List[str]] = Field(None, description="数据来源")
    created_at: str = Field(..., description="创建时间")
    completed_at: Optional[str] = Field(None, description="完成时间")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "symbol": "BTC",
                "query": "分析比特币",
                "title": "BTC 深度研究报告 - 2025-01-25 10:30",
                "markdown_content": "# BTC 深度研究报告\n\n## TL;DR\n...",
                "tldr": "比特币是第一大加密货币...",
                "report_type": "deep_research",
                "status": "completed",
                "quality_score": 90,
                "generation_time": 28.5,
                "data_sources": ["CoinGecko", "Twitter", "Reddit"],
                "created_at": "2025-01-25T10:30:00Z",
                "completed_at": "2025-01-25T10:30:30Z"
            }
        }


class ReportListResponse(BaseModel):
    """报告列表响应"""
    reports: List[ReportSummary] = Field(..., description="报告列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")

    class Config:
        json_schema_extra = {
            "example": {
                "reports": [
                    {
                        "id": 1,
                        "title": "BTC 深度研究报告",
                        "symbol": "BTC",
                        "query": "分析比特币",
                        "tldr": "比特币是第一大加密货币...",
                        "report_type": "deep_research",
                        "status": "completed",
                        "quality_score": 90,
                        "generation_time": 28.5,
                        "created_at": "2025-01-25T10:30:00Z"
                    }
                ],
                "total": 50,
                "page": 1,
                "page_size": 10
            }
        }


# ================================
# Report Query Params
# ================================

class ReportQueryParams(BaseModel):
    """报告查询参数"""
    symbol: Optional[str] = Field(None, description="按币种筛选")
    report_type: Optional[str] = Field(None, description="按类型筛选")
    status: Optional[str] = Field(None, description="按状态筛选")
    page: int = Field(1, description="页码", ge=1)
    page_size: int = Field(10, description="每页数量", ge=1, le=100)
    order_by: str = Field("created_at", description="排序字段")
    order_desc: bool = Field(True, description="是否降序")

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "BTC",
                "report_type": "deep_research",
                "status": "completed",
                "page": 1,
                "page_size": 10,
                "order_by": "created_at",
                "order_desc": True
            }
        }


# ================================
# Report Sharing Schemas
# ================================

class ShareReportRequest(BaseModel):
    """创建分享链接请求"""
    expires_in_days: Optional[int] = Field(None, description="过期天数（None表示永久）", ge=1, le=365)

    class Config:
        json_schema_extra = {
            "example": {
                "expires_in_days": 30
            }
        }


class ShareReportResponse(BaseModel):
    """分享链接响应"""
    share_token: str = Field(..., description="分享令牌")
    share_url: str = Field(..., description="完整分享URL")
    expires_at: Optional[str] = Field(None, description="过期时间")

    class Config:
        json_schema_extra = {
            "example": {
                "share_token": "abc123xyz789",
                "share_url": "https://web3search.com/shared/abc123xyz789",
                "expires_at": "2025-02-25T10:30:00Z"
            }
        }


class SharedReportResponse(BaseModel):
    """分享报告内容响应"""
    title: str = Field(..., description="报告标题")
    symbol: str = Field(..., description="币种符号")
    markdown_content: str = Field(..., description="Markdown格式报告")
    tldr: str = Field(..., description="TL;DR摘要")
    report_type: str = Field(..., description="报告类型")
    quality_score: Optional[int] = Field(None, description="质量得分")
    data_sources: Optional[List[str]] = Field(None, description="数据来源")
    created_at: str = Field(..., description="创建时间")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "BTC 深度研究报告",
                "symbol": "BTC",
                "markdown_content": "# BTC 深度研究报告\n\n## TL;DR\n...",
                "tldr": "比特币是第一大加密货币...",
                "report_type": "deep_research",
                "quality_score": 90,
                "data_sources": ["CoinGecko", "Twitter", "Reddit"],
                "created_at": "2025-01-25T10:30:00Z"
            }
        }
