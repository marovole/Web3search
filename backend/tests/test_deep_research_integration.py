"""
Deep Research 引擎集成测试
测试所有9个analyzers的完整集成和错误处理
"""
import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timezone

from app.services.research_engine.deep_research import DeepResearchEngine
from app.services.research_engine.analyzers.analyzer_output import (
    AnalyzerOutput,
    create_analyzer_output,
    create_error_output,
)


class TestDeepResearchIntegration:
    """测试Deep Research引擎的集成功能"""

    @pytest.fixture
    def deep_research_engine(self):
        """创建DeepResearchEngine实例"""
        return DeepResearchEngine()

    @pytest.fixture
    def sample_raw_data(self):
        """模拟的原始数据"""
        return {
            "symbol": "ETH",
            "market_data": {
                "current_price": 3500,
                "price_change_percentage_24h": 3.5,
                "total_supply": 120000000,
                "circulating_supply": 120000000,
                "max_supply": None,
                "market_cap": 420000000000,
                "volume_24h": 15000000000,
            },
            "social_data": {
                "twitter": {
                    "followers": 3000000,
                    "mentions_7d": 25000,
                    "sentiment_distribution": {
                        "positive": 15000,
                        "neutral": 8000,
                        "negative": 2000,
                    }
                },
                "reddit": {
                    "subscribers": 1500000,
                    "posts_7d": 500,
                    "sentiment_score": 0.65
                }
            },
            "onchain_data": {
                "active_addresses": 500000,
                "transaction_count_24h": 1200000,
                "total_value_locked": 30000000000,
                "defi_protocols_count": 350
            },
            "project_info": {
                "name": "Ethereum",
                "categories": ["Smart Contract Platform", "DeFi"],
                "description": "去中心化智能合约平台"
            }
        }

    @pytest.fixture
    def sample_formatted_data(self):
        """模拟的格式化数据"""
        return {
            "symbol": "ETH",
            "project_name": "Ethereum",
            "categories": "Smart Contract Platform, DeFi",
            "current_price": "$3,500.00",
            "price_change_24h": "+3.5%",
            "market_cap": "$420.0B",
            "volume_24h": "$15.0B"
        }

    @pytest.mark.asyncio
    async def test_generate_sections_success(self, deep_research_engine, sample_raw_data, sample_formatted_data):
        """测试_generate_sections成功执行所有8个analyzers"""

        # Mock所有analyzer的analyze方法返回成功结果
        async def mock_analyze_success(*args, **kwargs):
            return create_analyzer_output(
                data={"summary": "测试分析结果", "confidence": 85},
                analyzer_name="TestAnalyzer",
                model_used="gpt-4",
                confidence=85,
                generation_time_ms=1500
            )

        # Mock所有analyzers
        deep_research_engine.timeframe_analyzer.analyze = AsyncMock(side_effect=mock_analyze_success)
        deep_research_engine.sentiment_analyzer.analyze = AsyncMock(side_effect=mock_analyze_success)
        deep_research_engine.technical_analyzer.analyze = AsyncMock(side_effect=mock_analyze_success)
        deep_research_engine.onchain_analyzer.analyze = AsyncMock(side_effect=mock_analyze_success)
        deep_research_engine.competitor_analyzer.analyze = AsyncMock(side_effect=mock_analyze_success)
        deep_research_engine.tokenomics_analyzer.analyze = AsyncMock(side_effect=mock_analyze_success)
        deep_research_engine.risk_assessor.analyze = AsyncMock(side_effect=mock_analyze_success)
        deep_research_engine.conclusion_synthesizer.synthesize = AsyncMock(side_effect=mock_analyze_success)

        # 手试
        result = await deep_research_engine._generate_sections(
            query="ETH analysis",
            symbol="ETH",
            formatted_data=sample_formatted_data,
            raw_data=sample_raw_data
        )

        # 验证结果结构
        assert "analyzer_outputs" in result
        assert "sections" in result
        assert "visualization_hints" in result

        # 验证所有8个analyzers都被调用
        analyzer_outputs = result["analyzer_outputs"]
        expected_analyzers = [
            "timeframe", "sentiment", "technical", "onchain",
            "competitor", "tokenomics", "risk", "conclusion"
        ]

        for analyzer_name in expected_analyzers:
            assert analyzer_name in analyzer_outputs
            assert isinstance(analyzer_outputs[analyzer_name], AnalyzerOutput)
            assert analyzer_outputs[analyzer_name].error is None

        # 验证sections包含所有8个字段
        sections = result["sections"]
        for analyzer_name in expected_analyzers:
            section_name = analyzer_name if analyzer_name != "technical" else "technical_analysis"
            section_name = section_name if analyzer_name != "onchain" else "onchain_analysis"
            section_name = section_name if analyzer_name != "competitor" else "competitor_analysis"
            section_name = section_name if analyzer_name != "tokenomics" else "tokenomics"
            section_name = section_name if analyzer_name != "risk" else "risk_assessment"
            assert section_name in sections

    @pytest.mark.asyncio
    async def test_generate_sections_with_errors(self, deep_research_engine, sample_raw_data, sample_formatted_data):
        """测试analyzer失败时的降级处理"""

        # Mock部分analyzer成功，部分失败
        async def mock_analyze_success(*args, **kwargs):
            return create_analyzer_output(
                data={"summary": "成功结果"},
                analyzer_name="SuccessAnalyzer",
                model_used="gpt-4"
            )

        async def mock_analyze_fail(*args, **kwargs):
            raise Exception("模拟analyzer失败")

        # 设置不同的mock行为
        deep_research_engine.timeframe_analyzer.analyze = AsyncMock(side_effect=mock_analyze_success)
        deep_research_engine.sentiment_analyzer.analyze = AsyncMock(side_effect=mock_analyze_fail)
        deep_research_engine.technical_analyzer.analyze = AsyncMock(side_effect=mock_analyze_success)
        deep_research_engine.onchain_analyzer.analyze = AsyncMock(side_effect=mock_analyze_fail)
        deep_research_engine.competitor_analyzer.analyze = AsyncMock(side_effect=mock_analyze_success)
        deep_research_engine.tokenomics_analyzer.analyze = AsyncMock(side_effect=mock_analyze_fail)
        deep_research_engine.risk_assessor.analyze = AsyncMock(side_effect=mock_analyze_success)
        deep_research_engine.conclusion_synthesizer.synthesize = AsyncMock(side_effect=mock_analyze_fail)

        # 执行测试
        result = await deep_research_engine._generate_sections(
            query="ETH analysis",
            symbol="ETH",
            formatted_data=sample_formatted_data,
            raw_data=sample_raw_data
        )

        # 验证成功和失败都被正确处理
        analyzer_outputs = result["analyzer_outputs"]

        # 成功的analyzers应该返回AnalyzerOutput对象
        success_analyzers = ["timeframe", "technical", "competitor", "risk"]
        for analyzer_name in success_analyzers:
            assert isinstance(analyzer_outputs[analyzer_name], AnalyzerOutput)
            assert analyzer_outputs[analyzer_name].error is None

        # 失败的analyzers应该返回错误输出
        failed_analyzers = ["sentiment", "onchain", "tokenomics", "conclusion"]
        for analyzer_name in failed_analyzers:
            assert isinstance(analyzer_outputs[analyzer_name], AnalyzerOutput)
            assert analyzer_outputs[analyzer_name].error is not None
            assert analyzer_outputs[analyzer_name].metadata.validation_passed is False

        # 验证sections仍然包含所有字段，失败的字段显示错误信息
        sections = result["sections"]
        for analyzer_name in failed_analyzers:
            if analyzer_name == "sentiment":
                assert "sentiment" in sections
                assert "⚠️" in sections["sentiment"] or "失败" in sections["sentiment"]

    @pytest.mark.asyncio
    async def test_extract_summary_with_analyzer_output(self, deep_research_engine):
        """测试_extract_summary方法处理AnalyzerOutput对象"""

        # 测试正常的AnalyzerOutput
        normal_output = create_analyzer_output(
            data={"summary": "测试摘要内容"},
            analyzer_name="TestAnalyzer",
            model_used="gpt-4"
        )

        summary = deep_research_engine._extract_summary(normal_output)
        assert summary == "测试摘要内容"

        # 测试带错误的AnalyzerOutput
        error_output = create_error_output(
            analyzer_name="TestAnalyzer",
            error_msg="连接失败"
        )

        summary = deep_research_engine._extract_summary(error_output)
        assert "⚠️" in summary and "连接失败" in summary

        # 测试没有summary字段的AnalyzerOutput
        no_summary_output = create_analyzer_output(
            data={"judgment": "BULL", "confidence": 85},
            analyzer_name="TestAnalyzer",
            model_used="gpt-4"
        )

        summary = deep_research_engine._extract_summary(no_summary_output)
        assert summary == "BULL"

        # 测试空输出
        summary = deep_research_engine._extract_summary(None)
        assert summary == "⚠️ 分析数据不可用"

    @pytest.mark.asyncio
    async def test_analyzer_call_parameters(self, deep_research_engine, sample_raw_data, sample_formatted_data):
        """测试传递给各个analyzer的参数正确性"""

        # 设置Mock来捕获调用参数
        call_logs = {}

        async def capture_call(analyzer_name):
            async def mock_func(*args, **kwargs):
                call_logs[analyzer_name] = {"args": args, "kwargs": kwargs}
                return create_analyzer_output(
                    data={"summary": f"{analyzer_name} result"},
                    analyzer_name=analyzer_name,
                    model_used="gpt-4"
                )
            return mock_func

        # 为每个analyzer设置参数捕获
        deep_research_engine.timeframe_analyzer.analyze = capture_call("timeframe")
        deep_research_engine.sentiment_analyzer.analyze = capture_call("sentiment")
        deep_research_engine.technical_analyzer.analyze = capture_call("technical")
        deep_research_engine.onchain_analyzer.analyze = capture_call("onchain")
        deep_research_engine.competitor_analyzer.analyze = capture_call("competitor")
        deep_research_engine.tokenomics_analyzer.analyze = capture_call("tokenomics")
        deep_research_engine.risk_assessor.analyze = capture_call("risk")
        deep_research_engine.conclusion_synthesizer.synthesize = capture_call("conclusion")

        # 执行测试
        await deep_research_engine._generate_sections(
            query="ETH analysis",
            symbol="ETH",
            formatted_data=sample_formatted_data,
            raw_data=sample_raw_data
        )

        # 验证调用参数
        assert call_logs["timeframe"]["args"] == ("ETH", "ETH analysis", sample_raw_data["market_data"])
        assert call_logs["sentiment"]["args"] == ("ETH", sample_raw_data["social_data"])
        assert call_logs["technical"]["args"] == ("ETH", sample_raw_data["market_data"])
        assert call_logs["onchain"]["args"] == ("ETH", sample_raw_data["onchain_data"])

        # competitor应该收到competitors字符串
        assert "Smart Contract Platform" in call_logs["competitor"]["args"][1]

        # tokenomics应该收到tokenomics数据
        tokenomics_data = call_logs["tokenomics"]["args"][1]
        assert tokenomics_data["total_supply"] == 120000000

        # risk应该收到完整的raw_data
        assert call_logs["risk"]["args"][1] == sample_raw_data

        # conclusion应该收到symbol, query和raw_data
        conclusion_args = call_logs["conclusion"]["args"]
        assert conclusion_args[0] == "ETH"  # symbol
        assert conclusion_args[1] == "ETH analysis"  # query
        assert conclusion_args[2] == sample_raw_data  # raw_data

    @pytest.mark.asyncio
    async def test_visualization_hints_collection(self, deep_research_engine, sample_raw_data, sample_formatted_data):
        """测试可视化提示的收集功能"""

        from app.services.research_engine.analyzers.analyzer_output import create_competitor_table_hint

        async def mock_analyze_with_hints(*args, **kwargs):
            if "competitor" in str(args):
                # competitor analyzer返回表格提示
                hints = [create_competitor_table_hint(
                    competitors=[{"项目": "A", "TVL": "$1B"}],
                    metrics=["项目", "TVL"]
                )]
            else:
                # 其他analyzers返回空提示
                hints = []

            return create_analyzer_output(
                data={"summary": "测试结果"},
                analyzer_name="TestAnalyzer",
                model_used="gpt-4",
                visualization_hints=hints
            )

        # Mock所有analyzers
        for analyzer_name in [
            "timeframe_analyzer", "sentiment_analyzer", "technical_analyzer",
            "onchain_analyzer", "competitor_analyzer", "tokenomics_analyzer",
            "risk_assessor", "conclusion_synthesizer"
        ]:
            analyzer = getattr(deep_research_engine, analyzer_name)
            if hasattr(analyzer, 'analyze'):
                analyzer.analyze = AsyncMock(side_effect=mock_analyze_with_hints)
            else:
                analyzer.synthesize = AsyncMock(side_effect=mock_analyze_with_hints)

        # 执行测试
        result = await deep_research_engine._generate_sections(
            query="ETH analysis",
            symbol="ETH",
            formatted_data=sample_formatted_data,
            raw_data=sample_raw_data
        )

        # 验证可视化提示被正确收集
        visualization_hints = result["visualization_hints"]
        assert len(visualization_hints) >= 1  # 至少有一个提示

        # 查找competitor的表格提示
        table_hints = [hint for hint in visualization_hints if hint.type == "table"]
        assert len(table_hints) >= 1

        table_hint = table_hints[0]
        assert table_hint.table_columns == ["项目", "TVL"]
        assert len(table_hint.table_data) == 1
        assert table_hint.table_data[0]["项目"] == "A"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])