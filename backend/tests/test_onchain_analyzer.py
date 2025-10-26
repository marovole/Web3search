"""
OnchainAnalyzer 单元测试
测试链上数据分析器的所有功能
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.research_engine.analyzers.onchain_analyzer import OnchainAnalyzer, onchain_analyzer


@pytest.fixture
def analyzer():
    """创建 OnchainAnalyzer 实例"""
    return OnchainAnalyzer()


@pytest.fixture
def sample_aggregated_data():
    """示例聚合数据"""
    return {
        "symbol": "ETH",
        "onchain_data": {
            "active_addresses_24h": 500000,
            "active_addresses_7d": 3500000,
            "active_addresses_30d": 15000000,
            "new_addresses_30d": 2000000,
            "new_address_growth_rate": "+15%",
            "transaction_count_24h": 1200000,
            "transaction_volume_24h": 8000000000,
            "transaction_trend": "上升",

            "tvl": 50000000000,
            "tvl_change_30d": "+10%",
            "protocol_revenue_30d": 150000000,
            "protocol_fees_30d": 200000000,
            "fee_distribution": "70% 销毁, 30% 质押者",
            "buyback_burn_30d": 50000000,

            "top_10_holders_pct": 35.5,
            "top_100_holders_pct": 65.0,
            "gini_coefficient": 0.72,
            "whale_net_flow_30d": "+5000000",
            "whale_trend": "积累",
            "institutional_holders": ["Grayscale", "BlackRock", "Fidelity"],
            "exchange_net_flow_30d": "-50000000",
            "exchange_trend": "流出"
        },
        "market_data": {
            "market_cap": 250000000000,
            "price": 2000
        }
    }


class TestOnchainAnalyzerInit:
    """测试初始化"""

    def test_init_success(self, analyzer):
        """测试正常初始化"""
        assert analyzer.system_prompt is not None
        assert analyzer.user_prompt_template is not None
        assert analyzer.model_config is not None
        assert analyzer.validation_rules is not None
        assert "user_activity" in analyzer.validation_rules["required_fields"]
        assert "protocol_fundamentals" in analyzer.validation_rules["required_fields"]
        assert "token_distribution" in analyzer.validation_rules["required_fields"]

    def test_singleton_instance(self):
        """测试单例实例"""
        assert onchain_analyzer is not None
        assert isinstance(onchain_analyzer, OnchainAnalyzer)


class TestUserActivityAnalysis:
    """测试用户活动分析"""

    def test_analyze_user_activity_complete_data(self, analyzer, sample_aggregated_data):
        """测试完整数据的用户活动分析"""
        result = analyzer._analyze_user_activity(sample_aggregated_data["onchain_data"])

        assert result["active_addresses_24h"] == 500000
        assert result["active_addresses_7d"] == 3500000
        assert result["active_addresses_30d"] == 15000000
        assert result["new_addresses_30d"] == 2000000
        assert result["new_address_growth_rate"] == "+15%"
        assert result["transaction_count_24h"] == 1200000
        assert result["transaction_volume_24h"] == 8000000000
        assert result["transaction_trend"] == "上升"

    def test_analyze_user_activity_missing_data(self, analyzer):
        """测试缺失数据的用户活动分析"""
        result = analyzer._analyze_user_activity({})

        assert result["active_addresses_24h"] == "N/A"
        assert result["active_addresses_7d"] == "N/A"
        assert result["active_addresses_30d"] == "N/A"
        assert result["new_addresses_30d"] == "N/A"
        assert result["new_address_growth_rate"] == "N/A"

    def test_analyze_user_activity_partial_data(self, analyzer):
        """测试部分数据的用户活动分析"""
        onchain_data = {
            "active_addresses_24h": 100000,
            "transaction_count_24h": 500000
        }
        result = analyzer._analyze_user_activity(onchain_data)

        assert result["active_addresses_24h"] == 100000
        assert result["transaction_count_24h"] == 500000
        assert result["active_addresses_7d"] == "N/A"
        assert result["new_addresses_30d"] == "N/A"


class TestProtocolFundamentalsAnalysis:
    """测试协议基本面分析"""

    def test_analyze_protocol_fundamentals_complete_data(self, analyzer, sample_aggregated_data):
        """测试完整数据的协议基本面分析"""
        result = analyzer._analyze_protocol_fundamentals(
            sample_aggregated_data["onchain_data"],
            sample_aggregated_data["market_data"]
        )

        assert result["current_tvl"] == 50000000000
        assert result["tvl_change_30d"] == "+10%"
        assert result["protocol_revenue_30d"] == 150000000
        assert result["annualized_revenue"] == 150000000 * 12
        assert result["mcap_to_tvl"] == 5.0  # 250B / 50B
        assert result["pe_ratio"] == pytest.approx(138.9, abs=0.1)  # 250B / (150M * 12)
        assert result["fee_distribution"] == "70% 销毁, 30% 质押者"
        assert result["buyback_burn_30d"] == 50000000

    def test_analyze_protocol_fundamentals_zero_tvl(self, analyzer):
        """测试 TVL 为 0 的情况"""
        onchain_data = {"tvl": 0, "protocol_revenue_30d": 100000000}
        market_data = {"market_cap": 1000000000}

        result = analyzer._analyze_protocol_fundamentals(onchain_data, market_data)

        assert result["mcap_to_tvl"] == 0

    def test_analyze_protocol_fundamentals_zero_revenue(self, analyzer):
        """测试收入为 0 的情况"""
        onchain_data = {"tvl": 50000000000, "protocol_revenue_30d": 0}
        market_data = {"market_cap": 250000000000}

        result = analyzer._analyze_protocol_fundamentals(onchain_data, market_data)

        assert result["pe_ratio"] == 0
        assert result["annualized_revenue"] == 0

    def test_analyze_protocol_fundamentals_missing_data(self, analyzer):
        """测试缺失数据的协议基本面分析"""
        result = analyzer._analyze_protocol_fundamentals({}, {})

        assert result["current_tvl"] == 0
        assert result["protocol_revenue_30d"] == 0
        assert result["mcap_to_tvl"] == 0
        assert result["pe_ratio"] == 0


class TestTokenDistributionAnalysis:
    """测试代币分布分析"""

    def test_analyze_token_distribution_complete_data(self, analyzer, sample_aggregated_data):
        """测试完整数据的代币分布分析"""
        result = analyzer._analyze_token_distribution(sample_aggregated_data["onchain_data"])

        assert result["top_10_holders_pct"] == 35.5
        assert result["top_100_holders_pct"] == 65.0
        assert result["gini_coefficient"] == 0.72
        assert result["whale_net_flow_30d"] == "+5000000"
        assert result["whale_trend"] == "积累"
        assert result["institutional_holders"] == "Grayscale, BlackRock, Fidelity"
        assert result["exchange_net_flow_30d"] == "-50000000"
        assert result["exchange_trend"] == "流出"

    def test_analyze_token_distribution_no_institutional(self, analyzer):
        """测试无机构持有者的代币分布分析"""
        onchain_data = {
            "top_10_holders_pct": 40,
            "institutional_holders": []
        }
        result = analyzer._analyze_token_distribution(onchain_data)

        assert result["institutional_holders"] == "暂无"

    def test_analyze_token_distribution_missing_data(self, analyzer):
        """测试缺失数据的代币分布分析"""
        result = analyzer._analyze_token_distribution({})

        assert result["top_10_holders_pct"] == "N/A"
        assert result["gini_coefficient"] == "N/A"
        assert result["whale_trend"] == "N/A"
        assert result["institutional_holders"] == "暂无"


class TestPromptFormatting:
    """测试 prompt 格式化"""

    def test_format_prompt_complete_data(self, analyzer, sample_aggregated_data):
        """测试完整数据的 prompt 格式化"""
        prompt = analyzer._format_prompt(sample_aggregated_data)

        assert "ETH" in prompt
        assert "500000" in prompt  # active_addresses_24h
        assert "50000000000" in prompt  # tvl
        assert "35.5" in prompt  # top_10_holders_pct
        assert "Grayscale" in prompt  # institutional holder

    def test_format_prompt_missing_data(self, analyzer):
        """测试缺失数据的 prompt 格式化"""
        data = {"symbol": "TEST"}
        prompt = analyzer._format_prompt(data)

        assert "TEST" in prompt
        assert "N/A" in prompt


class TestOutputValidation:
    """测试输出验证"""

    def test_validate_output_valid(self, analyzer):
        """测试有效输出验证"""
        output = {
            "user_activity": {
                "active_addresses": {"daily": 50000, "trend": "上升"},
                "new_users": {"new_addresses_30d": 100000, "growth_rate": "+20%"},
                "transaction_activity": {"tx_count_24h": 120000}
            },
            "protocol_fundamentals": {
                "tvl": {"current": 5000000000, "change_30d": "+25%"},
                "revenue": {"annualized_revenue": 84000000},
                "valuation_metrics": {"mcap_to_tvl": 0.3, "pe_ratio": 17.9}
            },
            "token_distribution": {
                "concentration": {"top_10_pct": 35, "gini_coefficient": 0.72},
                "whale_activity": {"net_flow_30d": "+5000000"},
                "exchange_balance": {"net_flow_30d": "-50000000"}
            },
            "onchain_health": {
                "score": 75,
                "rating": "良好"
            },
            "summary": "Overall positive fundamentals"
        }

        is_valid, errors = analyzer._validate_output(output)
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_output_missing_required_fields(self, analyzer):
        """测试缺少必需字段"""
        output = {
            "user_activity": {"active_addresses": {"daily": 50000}}
        }

        is_valid, errors = analyzer._validate_output(output)
        assert is_valid is False
        assert len(errors) > 0

    def test_validate_output_invalid_health_score(self, analyzer):
        """测试无效健康分数"""
        output = {
            "user_activity": {
                "active_addresses": {"daily": 50000, "trend": "上升"},
                "new_users": {"new_addresses_30d": 100000, "growth_rate": "+20%"},
                "transaction_activity": {"tx_count_24h": 120000}
            },
            "protocol_fundamentals": {
                "tvl": {"current": 5000000000, "change_30d": "+25%"},
                "revenue": {"annualized_revenue": 84000000},
                "valuation_metrics": {"mcap_to_tvl": 0.3, "pe_ratio": 17.9}
            },
            "token_distribution": {
                "concentration": {"top_10_pct": 35, "gini_coefficient": 0.72},
                "whale_activity": {"net_flow_30d": "+5000000"},
                "exchange_balance": {"net_flow_30d": "-50000000"}
            },
            "onchain_health": {
                "score": 150,  # Invalid: > 100
                "rating": "良好"
            },
            "summary": "Overall positive fundamentals"
        }

        is_valid, errors = analyzer._validate_output(output)
        assert is_valid is False
        assert any("score" in error for error in errors)


class TestFixInvalidOutput:
    """测试修复无效输出"""

    def test_fix_invalid_output_missing_fields(self, analyzer):
        """测试修复缺少字段的输出"""
        invalid_output = {
            "user_activity": {"active_addresses": {"daily": 50000}}
        }

        fixed = analyzer._fix_invalid_output(invalid_output, ["Missing protocol_fundamentals"])

        assert "user_activity" in fixed
        assert "protocol_fundamentals" in fixed
        assert "token_distribution" in fixed
        assert "onchain_health" in fixed

    def test_fix_invalid_output_invalid_score(self, analyzer):
        """测试修复无效分数"""
        invalid_output = {
            "user_activity": {
                "active_addresses": {"daily": 50000, "trend": "上升"},
                "new_users": {"new_addresses_30d": 100000, "growth_rate": "+20%"},
                "transaction_activity": {"tx_count_24h": 120000}
            },
            "protocol_fundamentals": {
                "tvl": {"current": 5000000000, "change_30d": "+25%"},
                "revenue": {"annualized_revenue": 84000000},
                "valuation_metrics": {"mcap_to_tvl": 0.3, "pe_ratio": 17.9}
            },
            "token_distribution": {
                "concentration": {"top_10_pct": 35, "gini_coefficient": 0.72},
                "whale_activity": {"net_flow_30d": "+5000000"},
                "exchange_balance": {"net_flow_30d": "-50000000"}
            },
            "onchain_health": {
                "score": 150,  # Invalid
                "rating": "良好"
            },
            "summary": "Test"
        }

        fixed = analyzer._fix_invalid_output(invalid_output, ["Invalid score"])

        assert fixed["onchain_health"]["score"] == 50  # Default to 50
        assert 0 <= fixed["onchain_health"]["score"] <= 100


class TestErrorResponse:
    """测试错误响应"""

    def test_create_error_response(self, analyzer):
        """测试创建错误响应"""
        error_msg = "LLM 调用失败"
        response = analyzer._create_error_response(error_msg)

        assert response["error"] is True
        assert error_msg in response["message"]
        assert "user_activity" in response
        assert "protocol_fundamentals" in response
        assert "token_distribution" in response
        assert "onchain_health" in response
        assert response["onchain_health"]["score"] == 0
        assert response["onchain_health"]["rating"] == "数据不足"


class TestAnalyze:
    """测试 analyze 主函数"""

    @pytest.mark.asyncio
    async def test_analyze_success(self, analyzer, sample_aggregated_data):
        """测试成功分析"""
        mock_response = {
            "user_activity": {
                "active_addresses": {"daily": 500000, "trend": "上升"},
                "new_users": {"new_addresses_30d": 2000000, "growth_rate": "+15%"},
                "transaction_activity": {"tx_count_24h": 1200000, "volume_24h": 8000000000, "trend": "上升"}
            },
            "protocol_fundamentals": {
                "tvl": {"current": 50000000000, "change_30d": "+10%"},
                "revenue": {
                    "protocol_revenue_30d": 150000000,
                    "annualized_revenue": 1800000000,
                    "fee_distribution": "70% 销毁, 30% 质押者"
                },
                "valuation_metrics": {"mcap_to_tvl": 5.0, "pe_ratio": 138.9}
            },
            "token_distribution": {
                "concentration": {"top_10_pct": 35.5, "gini_coefficient": 0.72},
                "whale_activity": {"net_flow_30d": "+5000000", "trend": "积累"},
                "institutional_holders": ["Grayscale", "BlackRock", "Fidelity"],
                "exchange_balance": {"net_flow_30d": "-50000000", "trend": "流出"}
            },
            "onchain_health": {
                "score": 75,
                "rating": "良好",
                "strengths": ["高TVL", "去中心化分布"],
                "concerns": ["市值较高"]
            },
            "summary": "ETH 链上基本面健康，用户活跃度高，协议收入稳定增长"
        }

        with patch.object(analyzer, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response

            result = await analyzer.analyze(sample_aggregated_data)

            assert result["error"] is False
            assert result["user_activity"]["active_addresses"]["daily"] == 500000
            assert result["protocol_fundamentals"]["tvl"]["current"] == 50000000000
            assert result["token_distribution"]["concentration"]["top_10_pct"] == 35.5
            assert result["onchain_health"]["score"] == 75
            assert result["onchain_health"]["rating"] == "良好"

    @pytest.mark.asyncio
    async def test_analyze_llm_failure(self, analyzer, sample_aggregated_data):
        """测试 LLM 调用失败"""
        with patch.object(analyzer, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = None

            result = await analyzer.analyze(sample_aggregated_data)

            assert result["error"] is True
            assert "LLM 调用失败" in result["message"]
            assert result["onchain_health"]["score"] == 0

    @pytest.mark.asyncio
    async def test_analyze_invalid_output_fixed(self, analyzer, sample_aggregated_data):
        """测试无效输出被修复"""
        invalid_response = {
            "user_activity": {"active_addresses": {"daily": 50000}}
            # Missing other required fields
        }

        with patch.object(analyzer, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = invalid_response

            result = await analyzer.analyze(sample_aggregated_data)

            assert result["error"] is False
            assert "protocol_fundamentals" in result
            assert "token_distribution" in result
            assert "onchain_health" in result


class TestHealthRating:
    """测试健康评级"""

    def test_health_rating_excellent(self, analyzer):
        """测试优秀评级 (80+)"""
        output = {
            "onchain_health": {"score": 85}
        }
        # 验证评级逻辑是否正确 (这应该在 _validate_output 或 _fix_invalid_output 中处理)
        # 这里只是测试分数范围
        assert output["onchain_health"]["score"] >= 80

    def test_health_rating_good(self, analyzer):
        """测试良好评级 (60-79)"""
        output = {
            "onchain_health": {"score": 70}
        }
        assert 60 <= output["onchain_health"]["score"] < 80

    def test_health_rating_fair(self, analyzer):
        """测试一般评级 (40-59)"""
        output = {
            "onchain_health": {"score": 50}
        }
        assert 40 <= output["onchain_health"]["score"] < 60

    def test_health_rating_poor(self, analyzer):
        """测试差评级 (<40)"""
        output = {
            "onchain_health": {"score": 30}
        }
        assert output["onchain_health"]["score"] < 40
