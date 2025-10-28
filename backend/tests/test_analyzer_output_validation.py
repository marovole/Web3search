"""
Analyzer输出格式验证测试
验证所有analyzer返回的AnalyzerOutput对象格式正确性
"""
import pytest
from datetime import datetime, timezone
from typing import Dict, Any

from app.services.research_engine.analyzers.analyzer_output import (
    AnalyzerOutput,
    AnalyzerMetadata,
    VisualizationHint,
    create_analyzer_output,
    create_error_output,
    create_competitor_table_hint,
    create_price_chart_hint,
    create_sentiment_pie_hint,
)


class TestAnalyzerOutputValidation:
    """测试AnalyzerOutput对象的验证逻辑"""

    def test_create_valid_analyzer_output(self):
        """测试创建有效的AnalyzerOutput对象"""
        # 准备测试数据
        data = {
            "summary": "这是一个测试摘要",
            "confidence": 85,
            "judgment": "BULL"
        }

        visualization_hints = [
            create_competitor_table_hint(
                competitors=[
                    {"项目": "Ethereum", "TVL": "$30B"},
                    {"项目": "Solana", "TVL": "$2B"}
                ],
                metrics=["项目", "TVL"]
            )
        ]

        # 创建AnalyzerOutput
        output = create_analyzer_output(
            data=data,
            analyzer_name="TestAnalyzer",
            model_used="gpt-4",
            confidence=85,
            generation_time_ms=1500,
            data_sources=["TestSource"],
            visualization_hints=visualization_hints
        )

        # 验证基本属性
        assert isinstance(output, AnalyzerOutput)
        assert output.data == data
        assert output.metadata.analyzer_name == "TestAnalyzer"
        assert output.metadata.model_used == "gpt-4"
        assert output.metadata.confidence == 85
        assert output.metadata.generation_time_ms == 1500
        assert output.metadata.data_sources == ["TestSource"]
        assert len(output.visualization_hints) == 1
        assert output.error is None
        assert output.metadata.validation_passed is True

    def test_create_error_analyzer_output(self):
        """测试创建错误AnalyzerOutput对象"""
        output = create_error_output(
            analyzer_name="TestAnalyzer",
            error_msg="测试错误"
        )

        assert isinstance(output, AnalyzerOutput)
        assert output.data == {}
        assert output.metadata.analyzer_name == "TestAnalyzer"
        assert output.metadata.confidence == 0
        assert output.metadata.validation_passed is False
        assert output.error == "测试错误"
        assert len(output.visualization_hints) == 0

    def test_analyzer_metadata_validation(self):
        """测试AnalyzerMetadata的验证"""
        # 测试有效数据
        metadata = AnalyzerMetadata(
            analyzer_name="TestAnalyzer",
            model_used="gpt-4",
            confidence=75.5,
            generation_time_ms=2000,
            data_sources=["Source1", "Source2"]
        )

        assert metadata.analyzer_name == "TestAnalyzer"
        assert metadata.model_used == "gpt-4"
        assert metadata.confidence == 75.5
        assert metadata.generation_time_ms == 2000
        assert metadata.data_sources == ["Source1", "Source2"]
        assert metadata.validation_passed is True  # 默认值
        assert metadata.validation_warnings == []  # 默认值

    def test_confidence_bounds_validation(self):
        """测试置信度边界验证"""
        # 测试有效置信度
        valid_metadata = AnalyzerMetadata(
            analyzer_name="Test",
            model_used="gpt-4",
            confidence=50
        )
        assert valid_metadata.confidence == 50

        # 测试边界值
        metadata_min = AnalyzerMetadata(
            analyzer_name="Test",
            model_used="gpt-4",
            confidence=0
        )
        assert metadata_min.confidence == 0

        metadata_max = AnalyzerMetadata(
            analyzer_name="Test",
            model_used="gpt-4",
            confidence=100
        )
        assert metadata_max.confidence == 100

    def test_visualization_hint_validation(self):
        """测试VisualizationHint的验证"""
        # 测试表格提示
        table_hint = create_competitor_table_hint(
            competitors=[
                {"项目": "A", "价值": "$100"},
                {"项目": "B", "价值": "$200"}
            ],
            metrics=["项目", "价值"]
        )

        assert table_hint.type == "table"
        assert table_hint.table_columns == ["项目", "价值"]
        assert len(table_hint.table_data) == 2
        assert table_hint.chart_type is None
        assert table_hint.chart_data is None

        # 测试图表提示
        chart_hint = create_price_chart_hint(
            dates=["2025-01-01", "2025-01-02"],
            prices=[100, 110],
            title="价格走势"
        )

        assert chart_hint.type == "chart"
        assert chart_hint.chart_type == "line"
        assert chart_hint.chart_title == "价格走势"
        assert chart_hint.chart_data["x"] == ["2025-01-01", "2025-01-02"]
        assert chart_hint.chart_data["y"] == [100, 110]
        assert chart_hint.table_columns is None
        assert chart_hint.table_data is None

    def test_sentiment_pie_hint(self):
        """测试情绪分布饼图提示"""
        hint = create_sentiment_pie_hint(
            positive_pct=60,
            neutral_pct=30,
            negative_pct=10
        )

        assert hint.type == "chart"
        assert hint.chart_type == "pie"
        assert hint.chart_title == "社媒情绪分布"
        assert hint.chart_data["labels"] == ["正面", "中性", "负面"]
        assert hint.chart_data["values"] == [60, 30, 10]
        assert hint.chart_data["colors"] == ["#10b981", "#6b7280", "#ef4444"]

    def test_sentiment_pie_hint_validation(self):
        """测试情绪分布饼图的百分比验证"""
        # 这里我们主要测试创建逻辑，百分比验证应该在应用层处理
        hint = create_sentiment_pie_hint(50, 30, 20)
        assert hint.chart_data["values"] == [50, 30, 20]

        # 即使百分比总和不是100，函数也应该正常工作
        hint_imperfect = create_sentiment_pie_hint(60, 40, 20)
        assert hint_imperfect.chart_data["values"] == [60, 40, 20]

    def test_analyzer_output_json_serialization(self):
        """测试AnalyzerOutput的JSON序列化"""
        data = {"summary": "测试摘要", "score": 85}
        output = create_analyzer_output(
            data=data,
            analyzer_name="TestAnalyzer",
            model_used="gpt-4"
        )

        # 测试序列化
        json_data = output.model_dump()
        assert "data" in json_data
        assert "metadata" in json_data
        assert "visualization_hints" in json_data
        assert json_data["data"]["summary"] == "测试摘要"

        # 测试反序列化
        deserialized = AnalyzerOutput.model_validate(json_data)
        assert deserialized.data == data
        assert deserialized.metadata.analyzer_name == "TestAnalyzer"

    def test_error_output_serialization(self):
        """测试错误输出的序列化"""
        error_output = create_error_output(
            analyzer_name="TestAnalyzer",
            error_msg="连接超时"
        )

        json_data = error_output.model_dump()
        assert json_data["error"] == "连接超时"
        assert json_data["metadata"]["validation_passed"] is False

    def test_complex_visualization_hints(self):
        """测试复杂的可视化提示组合"""
        hints = [
            create_competitor_table_hint(
                competitors=[{"项目": "A", "TVL": "$1B"}],
                metrics=["项目", "TVL"]
            ),
            create_price_chart_hint(
                dates=["2025-01-01"],
                prices=[100]
            ),
            create_sentiment_pie_hint(40, 35, 25)
        ]

        output = create_analyzer_output(
            data={"summary": "复杂分析"},
            analyzer_name="ComplexAnalyzer",
            model_used="gpt-4",
            visualization_hints=hints
        )

        assert len(output.visualization_hints) == 3
        assert output.visualization_hints[0].type == "table"
        assert output.visualization_hints[1].type == "chart"
        assert output.visualization_hints[2].type == "chart"

    def test_metadata_auto_timestamp(self):
        """测试元数据自动时间戳"""
        before = datetime.now(timezone.utc)
        output = create_analyzer_output(
            data={"test": "data"},
            analyzer_name="TestAnalyzer",
            model_used="gpt-4"
        )
        after = datetime.now(timezone.utc)

        # 验证时间戳在合理范围内
        metadata_time = datetime.fromisoformat(output.metadata.updated_at.replace('Z', '+00:00'))
        assert before <= metadata_time <= after

    def test_fallback_model_flag(self):
        """测试fallback模型标志"""
        output_with_fallback = create_analyzer_output(
            data={"summary": "fallback测试"},
            analyzer_name="TestAnalyzer",
            model_used="gpt-3.5-turbo",
            fallback_used=True
        )

        assert output_with_fallback.metadata.fallback_used is True

        output_without_fallback = create_analyzer_output(
            data={"summary": "正常测试"},
            analyzer_name="TestAnalyzer",
            model_used="gpt-4",
            fallback_used=False
        )

        assert output_without_fallback.metadata.fallback_used is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])