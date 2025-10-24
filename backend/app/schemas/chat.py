"""
聊天相关的API数据模型
定义Quick Chat和Deep Research的请求/响应结构
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


# ================================
# Quick Chat Schemas
# ================================

class QuickChatRequest(BaseModel):
    """Quick Chat请求"""
    query: str = Field(..., description="用户查询", min_length=1, max_length=500)
    session_id: Optional[str] = Field(None, description="会话ID")
    stream: bool = Field(False, description="是否流式返回")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "BTC现在的价格是多少？",
                "session_id": "abc123",
                "stream": False
            }
        }


class QuickChatResponse(BaseModel):
    """Quick Chat响应"""
    content: str = Field(..., description="AI回复内容")
    symbol: Optional[str] = Field(None, description="识别的币种符号")
    query_type: str = Field(..., description="查询类型")
    response_time: float = Field(..., description="响应时间（秒）")
    model: str = Field(..., description="使用的模型")
    session_id: Optional[str] = Field(None, description="会话ID")

    class Config:
        json_schema_extra = {
            "example": {
                "content": "比特币（BTC）当前价格为 $67,234.56，24小时上涨 2.3%",
                "symbol": "BTC",
                "query_type": "crypto_lookup",
                "response_time": 2.8,
                "model": "qwen/qwen3-30b-a3b:free",
                "session_id": "abc123"
            }
        }


# ================================
# Deep Research Schemas
# ================================

class DeepResearchRequest(BaseModel):
    """Deep Research请求"""
    query: str = Field(..., description="用户查询", min_length=1, max_length=500)
    symbol: Optional[str] = Field(None, description="币种符号（可选，会自动识别）")
    session_id: Optional[str] = Field(None, description="会话ID")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "请帮我深度分析以太坊的当前状况",
                "symbol": "ETH",
                "session_id": "abc123"
            }
        }


class ResearchSection(BaseModel):
    """研究报告章节"""
    overview: str = Field(..., description="项目概览")
    technical_analysis: str = Field(..., description="技术分析")
    market_analysis: str = Field(..., description="市场分析")
    community_analysis: str = Field(..., description="社区分析")
    risk_assessment: str = Field(..., description="风险评估")
    competitor_analysis: str = Field(..., description="竞品分析")


class DeepResearchResponse(BaseModel):
    """Deep Research响应"""
    report_id: int = Field(..., description="报告ID")
    symbol: str = Field(..., description="币种符号")
    query: str = Field(..., description="用户查询")
    tldr: str = Field(..., description="TL;DR摘要")
    sections: ResearchSection = Field(..., description="报告章节")
    conclusion: str = Field(..., description="结论")
    markdown_content: str = Field(..., description="完整Markdown报告")
    data_sources: List[str] = Field(..., description="数据来源")
    models_used: Dict[str, str] = Field(..., description="使用的模型")
    generation_time: float = Field(..., description="生成耗时（秒）")
    quality_score: int = Field(..., description="质量得分（0-100）")
    timestamp: str = Field(..., description="生成时间")
    session_id: Optional[str] = Field(None, description="会话ID")

    class Config:
        json_schema_extra = {
            "example": {
                "report_id": 1,
                "symbol": "ETH",
                "query": "请帮我深度分析以太坊的当前状况",
                "tldr": "以太坊是第二大加密货币，当前价格$3,456，市值排名第2...",
                "sections": {
                    "overview": "## 项目概览\n...",
                    "technical_analysis": "## 技术分析\n...",
                    "market_analysis": "## 市场分析\n...",
                    "community_analysis": "## 社区分析\n...",
                    "risk_assessment": "## 风险评估\n...",
                    "competitor_analysis": "## 竞品分析\n..."
                },
                "conclusion": "## 结论\n...",
                "markdown_content": "# ETH 深度研究报告\n...",
                "data_sources": ["CoinGecko", "Etherscan", "Twitter", "Reddit"],
                "models_used": {
                    "tldr": "qwen/qwen3-235b-a22b:free",
                    "sections": "deepseek/deepseek-r1-0528:free"
                },
                "generation_time": 25.6,
                "quality_score": 85,
                "timestamp": "2025-01-25T10:30:00Z",
                "session_id": "abc123"
            }
        }


# ================================
# 流式响应
# ================================

class StreamChunk(BaseModel):
    """流式响应数据块"""
    content: str = Field(..., description="内容片段")
    done: bool = Field(False, description="是否完成")

    class Config:
        json_schema_extra = {
            "example": {
                "content": "比特币当前价格为",
                "done": False
            }
        }


# ================================
# 错误响应
# ================================

class ErrorResponse(BaseModel):
    """错误响应"""
    error: str = Field(..., description="错误类型")
    message: str = Field(..., description="错误信息")
    detail: Optional[str] = Field(None, description="详细信息")

    class Config:
        json_schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "查询不能为空",
                "detail": None
            }
        }
