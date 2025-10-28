"""
Analyzer统一输出接口
定义所有analyzer的标准输出格式,支持报告生成器自动生成表格和图表
"""
from typing import Dict, Any, List, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class VisualizationHint(BaseModel):
    """可视化提示 - 用于指导报告生成器生成表格/图表"""

    type: Literal["table", "chart", "none"] = Field(
        description="可视化类型：table(表格)/chart(图表)/none(无需可视化)"
    )

    # 表格相关字段
    table_columns: Optional[List[str]] = Field(
        default=None,
        description="表格列定义，如['协议', '日交易量', 'TVL']"
    )
    table_data: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="表格数据，每行是一个Dict"
    )

    # 图表相关字段
    chart_type: Optional[Literal["line", "bar", "pie", "candlestick"]] = Field(
        default=None,
        description="图表类型：line(折线图)/bar(柱状图)/pie(饼图)/candlestick(K线图)"
    )
    chart_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="图表数据，包含x轴、y轴值等"
    )
    chart_title: Optional[str] = Field(
        default=None,
        description="图表标题"
    )


class AnalyzerMetadata(BaseModel):
    """Analyzer元数据 - 记录分析过程的元信息"""

    analyzer_name: str = Field(
        description="Analyzer名称，如'TldrGenerator'"
    )
    model_used: str = Field(
        description="使用的LLM模型，如'qwen/qwen3-235b-a22b:free'"
    )
    fallback_used: bool = Field(
        default=False,
        description="是否使用了fallback模型"
    )
    generation_time_ms: Optional[int] = Field(
        default=None,
        description="生成耗时（毫秒）"
    )
    confidence: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
        description="输出置信度(0-100)，None表示不适用"
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="生成时间 (ISO 8601格式)"
    )
    data_sources: List[str] = Field(
        default_factory=list,
        description="数据来源列表，如['CoinGecko', 'Etherscan']"
    )
    validation_passed: bool = Field(
        default=True,
        description="输出是否通过格式验证"
    )
    validation_warnings: List[str] = Field(
        default_factory=list,
        description="验证警告列表（非致命错误）"
    )


class AnalyzerOutput(BaseModel):
    """Analyzer统一输出格式"""

    data: Dict[str, Any] = Field(
        description="分析结果数据（Dict类型），由各analyzer自定义结构"
    )
    metadata: AnalyzerMetadata = Field(
        description="元数据（模型名称、生成时间、置信度等）"
    )
    visualization_hints: List[VisualizationHint] = Field(
        default_factory=list,
        description="可视化建议列表（表格结构、图表类型等）"
    )
    error: Optional[str] = Field(
        default=None,
        description="错误信息（如果分析失败）"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "data": {
                    "judgment": "BULL",
                    "confidence": 85,
                    "summary": "项目基本面强劲..."
                },
                "metadata": {
                    "analyzer_name": "TldrGenerator",
                    "model_used": "qwen/qwen3-235b-a22b:free",
                    "fallback_used": False,
                    "generation_time_ms": 2345,
                    "confidence": 85,
                    "updated_at": "2025-10-28T10:30:00Z",
                    "data_sources": ["CoinGecko", "Twitter"],
                    "validation_passed": True,
                    "validation_warnings": []
                },
                "visualization_hints": [
                    {
                        "type": "table",
                        "table_columns": ["指标", "值"],
                        "table_data": [
                            {"指标": "市值", "值": "$1.2B"},
                            {"指标": "TVL", "值": "$850M"}
                        ]
                    }
                ],
                "error": None
            }
        }


def create_analyzer_output(
    data: Dict[str, Any],
    analyzer_name: str,
    model_used: str,
    fallback_used: bool = False,
    generation_time_ms: Optional[int] = None,
    confidence: Optional[float] = None,
    data_sources: Optional[List[str]] = None,
    visualization_hints: Optional[List[VisualizationHint]] = None,
    validation_passed: bool = True,
    validation_warnings: Optional[List[str]] = None,
    error: Optional[str] = None,
) -> AnalyzerOutput:
    """
    便捷函数：创建AnalyzerOutput对象

    Args:
        data: 分析结果数据
        analyzer_name: Analyzer名称
        model_used: 使用的模型
        fallback_used: 是否使用fallback模型
        generation_time_ms: 生成耗时（毫秒）
        confidence: 置信度(0-100)
        data_sources: 数据来源列表
        visualization_hints: 可视化提示列表
        validation_passed: 是否通过验证
        validation_warnings: 验证警告
        error: 错误信息

    Returns:
        AnalyzerOutput对象
    """
    metadata = AnalyzerMetadata(
        analyzer_name=analyzer_name,
        model_used=model_used,
        fallback_used=fallback_used,
        generation_time_ms=generation_time_ms,
        confidence=confidence,
        data_sources=data_sources or [],
        validation_passed=validation_passed,
        validation_warnings=validation_warnings or [],
    )

    return AnalyzerOutput(
        data=data,
        metadata=metadata,
        visualization_hints=visualization_hints or [],
        error=error,
    )


def create_error_output(
    analyzer_name: str,
    error_msg: str,
    model_used: str = "unknown",
) -> AnalyzerOutput:
    """
    便捷函数：创建错误输出

    Args:
        analyzer_name: Analyzer名称
        error_msg: 错误信息
        model_used: 使用的模型（如果已知）

    Returns:
        包含错误的AnalyzerOutput对象
    """
    return create_analyzer_output(
        data={},
        analyzer_name=analyzer_name,
        model_used=model_used,
        confidence=0,
        validation_passed=False,
        error=error_msg,
    )


# 辅助函数：为竞品对比生成表格可视化提示
def create_competitor_table_hint(
    competitors: List[Dict[str, Any]],
    metrics: List[str]
) -> VisualizationHint:
    """
    创建竞品对比表格的可视化提示

    Args:
        competitors: 竞品数据列表
        metrics: 指标列表，如['协议', '日交易量', 'TVL']

    Returns:
        VisualizationHint对象
    """
    return VisualizationHint(
        type="table",
        table_columns=metrics,
        table_data=competitors,
    )


# 辅助函数：为价格趋势生成图表可视化提示
def create_price_chart_hint(
    dates: List[str],
    prices: List[float],
    title: str = "价格走势图"
) -> VisualizationHint:
    """
    创建价格走势图的可视化提示

    Args:
        dates: 日期列表
        prices: 价格列表
        title: 图表标题

    Returns:
        VisualizationHint对象
    """
    return VisualizationHint(
        type="chart",
        chart_type="line",
        chart_data={
            "x": dates,
            "y": prices,
            "x_label": "日期",
            "y_label": "价格 (USD)",
        },
        chart_title=title,
    )


# 辅助函数：为情绪分布生成饼图可视化提示
def create_sentiment_pie_hint(
    positive_pct: float,
    neutral_pct: float,
    negative_pct: float,
) -> VisualizationHint:
    """
    创建情绪分布饼图的可视化提示

    Args:
        positive_pct: 正面情绪百分比
        neutral_pct: 中性情绪百分比
        negative_pct: 负面情绪百分比

    Returns:
        VisualizationHint对象
    """
    return VisualizationHint(
        type="chart",
        chart_type="pie",
        chart_data={
            "labels": ["正面", "中性", "负面"],
            "values": [positive_pct, neutral_pct, negative_pct],
            "colors": ["#10b981", "#6b7280", "#ef4444"],  # 绿/灰/红
        },
        chart_title="社媒情绪分布",
    )
