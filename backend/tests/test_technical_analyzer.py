"""
Technical Analyzer 单元测试
测试TechnicalAnalyzer类的功能
"""
import pytest
import asyncio
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from app.services.research_engine.analyzers.technical_analyzer import TechnicalAnalyzer


@pytest.fixture
def technical_analyzer():
    """创建TechnicalAnalyzer实例"""
    return TechnicalAnalyzer()


@pytest.fixture
def sample_aggregated_data():
    """模拟的聚合数据"""
    return {
        "symbol": "ETH",
        "coingecko_id": "ethereum",
        "project_info": {
            "name": "Ethereum",
            "categories": ["Smart Contract Platform"],
        },
        "market_data": {
            "current_price": 3500,
            "high_24h": 3600,
            "low_24h": 3400,
            "total_volume": 15000000000,
            "price_change_percentage_24h": 2.5,
            "price_change_percentage_7d": 8.0,
            "price_change_percentage_30d": 15.0,
            "ath": {"price": 4800},
            "atl": {"price": 80},
            "ath_change_percentage": -27.1,
            "atl_change_percentage": 4275.0,
        },
        "derivatives_data": {
            "open_interest": {
                "value": 5000000000,
                "change_24h": 5.5,
            },
            "funding_rate": {
                "value": 0.015,
            },
            "liquidations": {
                "long_24h": 50000000,
                "short_24h": 120000000,
            },
        },
    }


@pytest.fixture
def sample_prices():
    """模拟价格序列"""
    # 生成一个上涨趋势的价格序列
    return [3000 + i * 20 for i in range(30)]


class TestTechnicalAnalyzer:
    """TechnicalAnalyzer测试类"""

    def test_init(self, technical_analyzer):
        """测试初始化"""
        assert technical_analyzer is not None
        assert technical_analyzer.llm_client is not None
        assert technical_analyzer.system_prompt != ""
        assert technical_analyzer.user_prompt_template != ""

    def test_generate_price_series(self, technical_analyzer):
        """测试生成价格序列"""
        prices = technical_analyzer._generate_price_series(3500, 10, 10)

        assert len(prices) == 10
        assert prices[-1] == 3500  # 最后一个价格应该是当前价格
        assert prices[0] < prices[-1]  # 价格应该是上涨趋势

    def test_calculate_rsi_normal(self, technical_analyzer, sample_prices):
        """测试RSI计算（正常情况）"""
        rsi_data = technical_analyzer._calculate_rsi(sample_prices)

        assert "value" in rsi_data
        assert "signal" in rsi_data
        assert "interpretation" in rsi_data
        assert 0 <= rsi_data["value"] <= 100

    def test_calculate_rsi_insufficient_data(self, technical_analyzer):
        """测试RSI计算（数据不足）"""
        prices = [100, 102, 101]  # 少于14+1个数据点
        rsi_data = technical_analyzer._calculate_rsi(prices)

        assert rsi_data["value"] == 50
        assert rsi_data["signal"] == "中性"
        assert "数据不足" in rsi_data["interpretation"]

    def test_calculate_rsi_overbought(self, technical_analyzer):
        """测试RSI超买信号"""
        # 创建持续上涨的价格序列（应该产生高RSI）
        prices = [1000 + i * 50 for i in range(20)]
        rsi_data = technical_analyzer._calculate_rsi(prices)

        # RSI应该较高（虽然不一定>70，但应该>50）
        assert rsi_data["value"] > 50

    def test_calculate_rsi_oversold(self, technical_analyzer):
        """测试RSI超卖信号"""
        # 创建持续下跌的价格序列
        prices = [2000 - i * 50 for i in range(20)]
        rsi_data = technical_analyzer._calculate_rsi(prices)

        # RSI应该较低
        assert rsi_data["value"] < 50

    def test_calculate_macd(self, technical_analyzer, sample_prices):
        """测试MACD计算"""
        macd_data = technical_analyzer._calculate_macd(sample_prices)

        assert "macd_line" in macd_data
        assert "signal_line" in macd_data
        assert "histogram" in macd_data
        assert "signal" in macd_data
        assert "interpretation" in macd_data

    def test_calculate_macd_insufficient_data(self, technical_analyzer):
        """测试MACD计算（数据不足）"""
        prices = [100, 102, 101, 103]  # 少于26个数据点
        macd_data = technical_analyzer._calculate_macd(prices)

        assert macd_data["macd_line"] == 0
        assert macd_data["signal"] == "中性"
        assert "数据不足" in macd_data["interpretation"]

    def test_calculate_bollinger_bands(self, technical_analyzer, sample_prices):
        """测试布林带计算"""
        bb_data = technical_analyzer._calculate_bollinger_bands(sample_prices)

        assert "upper" in bb_data
        assert "middle" in bb_data
        assert "lower" in bb_data
        assert "current_position" in bb_data
        assert "bandwidth" in bb_data
        assert "interpretation" in bb_data

        # 上轨应该大于中轨，中轨应该大于下轨
        assert bb_data["upper"] > bb_data["middle"]
        assert bb_data["middle"] > bb_data["lower"]

    def test_calculate_bollinger_bands_insufficient_data(self, technical_analyzer):
        """测试布林带计算（数据不足）"""
        prices = [100, 102, 101]
        bb_data = technical_analyzer._calculate_bollinger_bands(prices)

        assert bb_data["current_position"] == "数据不足"
        assert "数据不足" in bb_data["interpretation"]

    def test_identify_support_resistance(self, technical_analyzer, sample_aggregated_data):
        """测试支撑阻力位识别"""
        price_history = {
            "prices_30d": [3000, 3100, 3200, 3300, 3400, 3500]
        }
        market_data = sample_aggregated_data["market_data"]

        sr_data = technical_analyzer._identify_support_resistance(price_history, market_data)

        assert "immediate_support" in sr_data
        assert "immediate_resistance" in sr_data
        assert "strong_support" in sr_data
        assert "strong_resistance" in sr_data
        assert "ath_price" in sr_data
        assert "atl_price" in sr_data

        # 应该有支撑和阻力位
        assert len(sr_data["immediate_support"]) >= 1
        assert len(sr_data["immediate_resistance"]) >= 1

    def test_analyze_derivatives_bullish(self, technical_analyzer):
        """测试衍生品分析（看涨信号）"""
        derivatives_data = {
            "open_interest": {
                "value": 5000000000,
                "change_24h": 10.0,  # OI大幅上升
            },
            "funding_rate": {
                "value": 0.02,  # 正资金费率
            },
            "liquidations": {
                "long_24h": 20000000,
                "short_24h": 100000000,  # 空头清算远超多头
            },
        }

        deriv_analysis = technical_analyzer._analyze_derivatives(derivatives_data)

        assert deriv_analysis["open_interest"]["signal"] == "看涨"
        assert deriv_analysis["liquidation_risk"]["level"] == "低"

    def test_analyze_derivatives_bearish(self, technical_analyzer):
        """测试衍生品分析（看跌信号）"""
        derivatives_data = {
            "open_interest": {
                "value": 3000000000,
                "change_24h": -8.0,  # OI下降
            },
            "funding_rate": {
                "value": -0.025,  # 负资金费率
            },
            "liquidations": {
                "long_24h": 150000000,  # 多头清算远超空头
                "short_24h": 30000000,
            },
        }

        deriv_analysis = technical_analyzer._analyze_derivatives(derivatives_data)

        assert deriv_analysis["open_interest"]["signal"] == "看跌"
        assert deriv_analysis["liquidation_risk"]["level"] == "高"

    def test_extract_price_history(self, technical_analyzer, sample_aggregated_data):
        """测试价格历史提取"""
        price_history = technical_analyzer._extract_price_history(sample_aggregated_data)

        assert "prices_7d" in price_history
        assert "prices_14d" in price_history
        assert "prices_20d" in price_history
        assert "prices_30d" in price_history

        # 应该生成了价格序列
        assert len(price_history["prices_7d"]) > 0
        assert len(price_history["prices_30d"]) > 0

    def test_format_prompt(self, technical_analyzer, sample_aggregated_data):
        """测试提示词格式化"""
        price_history = {"prices_7d": [3400, 3450, 3500], "prices_30d": [3200] * 30}
        rsi_data = {"value": 65, "signal": "中性", "interpretation": "RSI正常"}
        macd_data = {"macd_line": 100, "signal_line": 80, "histogram": 20, "signal": "看涨", "interpretation": "MACD多头"}
        bollinger_data = {"upper": 3800, "middle": 3500, "lower": 3200, "current_position": "中轨", "bandwidth": "正常", "interpretation": "布林带正常"}
        sr_data = {
            "immediate_support": ["$3400", "$3300"],
            "immediate_resistance": ["$3600", "$3700"],
            "strong_support": ["$3000"],
            "strong_resistance": ["$4000"],
            "ath_price": 4800,
            "atl_price": 80,
        }
        derivatives = {
            "open_interest": {"value": 5e9, "change_24h": 5.5, "signal": "看涨", "interpretation": "OI上升"},
            "funding_rate": {"value": 0.015, "interpretation": "多头支付费用"},
            "liquidation_risk": {"level": "低", "long_liquidations_24h": 50e6, "short_liquidations_24h": 120e6, "interpretation": "空头清算多"},
        }

        prompt = technical_analyzer._format_prompt(
            symbol="ETH",
            project_name="Ethereum",
            current_price=3500,
            price_change_24h=2.5,
            market_data=sample_aggregated_data["market_data"],
            price_history=price_history,
            rsi_data=rsi_data,
            macd_data=macd_data,
            bollinger_data=bollinger_data,
            support_resistance=sr_data,
            derivatives=derivatives,
        )

        # 验证关键信息存在
        assert "ETH" in prompt
        assert "Ethereum" in prompt
        assert "3500" in prompt
        assert "65" in prompt  # RSI

    def test_validate_output_valid(self, technical_analyzer):
        """测试有效输出的验证"""
        valid_output = {
            "technical_indicators": {
                "rsi": {"value": 65, "signal": "中性", "interpretation": "RSI正常"},
                "macd": {"macd_line": 100, "signal_line": 80, "histogram": 20, "signal": "看涨", "interpretation": "多头"},
                "bollinger_bands": {"upper": 3800, "middle": 3500, "lower": 3200, "current_position": "中轨", "bandwidth": "正常", "interpretation": "正常"},
            },
            "support_resistance": {
                "immediate_support": ["$3400"],
                "immediate_resistance": ["$3600"],
                "strong_support": ["$3000"],
                "strong_resistance": ["$4000"],
                "key_levels_narrative": "支撑阻力清晰",
            },
            "trend_analysis": {
                "short_term_trend": "上涨",
                "medium_term_trend": "上涨",
                "trend_strength": "强",
                "narrative": "趋势向上",
            },
            "derivatives_analysis": {
                "open_interest": {"value": 5e9, "change_24h": 5, "signal": "看涨", "interpretation": "OI上升"},
                "funding_rate": {"value": 0.01, "interpretation": "多头支付"},
                "liquidation_risk": {"level": "低", "long_liquidations_24h": 50e6, "short_liquidations_24h": 100e6, "interpretation": "风险低"},
            },
            "overall_technical_view": {
                "bias": "看涨",
                "confidence": 80,
                "time_horizon": "短期",
                "narrative": "技术面看涨",
            },
            "data_sources": ["CoinGecko"],
            "updated_at": "2025-10-25T14:30:00Z",
        }

        assert technical_analyzer._validate_output(valid_output) is True

    def test_validate_output_missing_fields(self, technical_analyzer):
        """测试缺少必填字段的验证"""
        invalid_output = {
            "technical_indicators": {
                "rsi": {"value": 65, "signal": "中性", "interpretation": "RSI正常"},
            },
            # 缺少其他必填字段
        }

        assert technical_analyzer._validate_output(invalid_output) is False

    def test_validate_output_invalid_rsi(self, technical_analyzer):
        """测试无效RSI值的验证"""
        invalid_output = {
            "technical_indicators": {
                "rsi": {"value": 150, "signal": "超买", "interpretation": "RSI超买"},  # RSI超出范围
                "macd": {"macd_line": 100, "signal_line": 80, "histogram": 20, "signal": "看涨", "interpretation": "多头"},
                "bollinger_bands": {"upper": 3800, "middle": 3500, "lower": 3200, "current_position": "中轨", "bandwidth": "正常", "interpretation": "正常"},
            },
            "support_resistance": {"immediate_support": [], "immediate_resistance": [], "strong_support": [], "strong_resistance": [], "key_levels_narrative": ""},
            "trend_analysis": {"short_term_trend": "上涨", "medium_term_trend": "上涨", "trend_strength": "强", "narrative": "上涨"},
            "derivatives_analysis": {
                "open_interest": {"value": 5e9, "change_24h": 5, "signal": "看涨", "interpretation": ""},
                "funding_rate": {"value": 0.01, "interpretation": ""},
                "liquidation_risk": {"level": "低", "long_liquidations_24h": 0, "short_liquidations_24h": 0, "interpretation": ""},
            },
            "overall_technical_view": {"bias": "看涨", "confidence": 80, "narrative": "看涨"},
            "data_sources": [],
            "updated_at": "2025-10-25T14:30:00Z",
        }

        assert technical_analyzer._validate_output(invalid_output) is False

    def test_fix_invalid_output(self, technical_analyzer):
        """测试修复无效输出"""
        invalid_output = {
            "technical_indicators": {
                "rsi": {"value": 65},
                # 缺少其他字段
            },
        }

        fixed = technical_analyzer._fix_invalid_output(invalid_output, "ETH")

        # 验证修复后的输出
        assert "technical_indicators" in fixed
        assert "macd" in fixed["technical_indicators"]
        assert "bollinger_bands" in fixed["technical_indicators"]
        assert "support_resistance" in fixed
        assert "trend_analysis" in fixed
        assert "derivatives_analysis" in fixed
        assert "overall_technical_view" in fixed
        assert "ETH" in fixed["trend_analysis"]["narrative"]

    def test_create_error_response(self, technical_analyzer):
        """测试创建错误响应"""
        error_resp = technical_analyzer._create_error_response("ETH", "LLM timeout")

        assert error_resp["overall_technical_view"]["bias"] == "中性"
        assert error_resp["overall_technical_view"]["confidence"] == 30
        assert "error" in error_resp
        assert error_resp["error"] == "LLM timeout"

    @pytest.mark.asyncio
    @patch("app.services.research_engine.analyzers.technical_analyzer.llm_client")
    async def test_analyze_success(
        self, mock_llm_client, technical_analyzer, sample_aggregated_data
    ):
        """测试成功分析技术面"""
        # Mock LLM响应
        mock_llm_client.chat_completion = MagicMock(
            return_value={
                "content": """{
                    "technical_indicators": {
                        "rsi": {"value": 62.5, "signal": "中性", "interpretation": "RSI中性"},
                        "macd": {"macd_line": 850, "signal_line": 720, "histogram": 130, "signal": "看涨", "interpretation": "MACD多头"},
                        "bollinger_bands": {"upper": 3800, "middle": 3500, "lower": 3200, "current_position": "中轨附近", "bandwidth": "正常", "interpretation": "正常"}
                    },
                    "support_resistance": {
                        "immediate_support": ["$3400", "$3300"],
                        "immediate_resistance": ["$3600", "$3700"],
                        "strong_support": ["$3000"],
                        "strong_resistance": ["$4000"],
                        "key_levels_narrative": "支撑阻力清晰"
                    },
                    "trend_analysis": {
                        "short_term_trend": "上涨",
                        "medium_term_trend": "上涨",
                        "long_term_trend": "上涨",
                        "trend_strength": "强",
                        "momentum": "稳定",
                        "narrative": "多周期上涨趋势"
                    },
                    "derivatives_analysis": {
                        "open_interest": {"value": 5000000000, "change_24h": 5.5, "signal": "看涨", "interpretation": "OI上升"},
                        "funding_rate": {"value": 0.015, "interpretation": "多头支付费用"},
                        "liquidation_risk": {"level": "低", "long_liquidations_24h": 50000000, "short_liquidations_24h": 120000000, "interpretation": "空头清算多"}
                    },
                    "overall_technical_view": {
                        "bias": "看涨",
                        "confidence": 80,
                        "time_horizon": "短期（1-2周）",
                        "narrative": "技术面整体看涨"
                    },
                    "data_sources": ["CoinGecko", "Binance"],
                    "updated_at": "2025-10-25T14:30:00Z"
                }"""
            }
        )

        technical_analyzer.llm_client = mock_llm_client

        result = await technical_analyzer.analyze(
            aggregated_data=sample_aggregated_data,
        )

        # 验证结果
        assert result["technical_indicators"]["rsi"]["value"] == 62.5
        assert result["overall_technical_view"]["bias"] == "看涨"
        assert result["overall_technical_view"]["confidence"] == 80

    @pytest.mark.asyncio
    @patch("app.services.research_engine.analyzers.technical_analyzer.llm_client")
    async def test_analyze_llm_failure(
        self, mock_llm_client, technical_analyzer, sample_aggregated_data
    ):
        """测试LLM调用失败时的降级处理"""
        # Mock LLM抛出异常
        mock_llm_client.chat_completion = MagicMock(
            side_effect=Exception("LLM service unavailable")
        )

        technical_analyzer.llm_client = mock_llm_client

        result = await technical_analyzer.analyze(
            aggregated_data=sample_aggregated_data,
        )

        # 验证降级响应
        assert "error" in result
        assert result["overall_technical_view"]["bias"] == "中性"
        assert result["overall_technical_view"]["confidence"] <= 50


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
