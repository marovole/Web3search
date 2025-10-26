"""
Timeframe Analyzer 单元测试
测试TimeframeAnalyzer类的功能
"""
import pytest
import asyncio
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from app.services.research_engine.analyzers.timeframe_analyzer import TimeframeAnalyzer


@pytest.fixture
def timeframe_analyzer():
    """创建TimeframeAnalyzer实例"""
    return TimeframeAnalyzer()


@pytest.fixture
def sample_aggregated_data():
    """模拟的聚合数据"""
    return {
        "symbol": "BTC",
        "coingecko_id": "bitcoin",
        "project_info": {
            "name": "Bitcoin",
            "categories": ["Cryptocurrency", "Store of Value"],
        },
        "market_data": {
            "current_price": 67000,
            "market_cap": 1300000000000,
            "market_cap_rank": 1,
            "price_change_percentage_24h": 2.5,
            "price_change_percentage_7d": 8.2,
            "price_change_percentage_30d": 15.6,
            "market_cap_change_percentage_30d": 14.2,
            "total_volume": 28000000000,
            "volume_change_percentage_24h": 8.5,
            "high_24h": 68000,
            "low_24h": 66000,
            "ath": {"price": 69000},
            "atl": {"price": 3000},
        },
        "social_data": {
            "twitter": {"followers": 5000000, "mentions_7d": 15000},
            "reddit": {"subscribers": 4500000, "posts_7d": 2500},
            "overall_sentiment": "positive",
            "recent_events_24h": [
                "ETF资金净流入$500M",
                "突破$67,000阻力位",
            ],
            "recent_events_7d": [
                "矿工抛售压力降至年内低点",
                "衍生品资金费率转正",
                "链上大额转账增加20%",
            ],
            "recent_events_30d": [
                "现货ETF累计流入$5B",
                "全网算力突破600 EH/s",
                "闪电网络容量增长20%",
            ],
        },
        "onchain_data": {
            "active_addresses": 950000,
            "transactions_24h": 350000,
            "holder_count": 50000000,
            "tvl_change_30d": 25.0,
            "user_growth_30d": 18.5,
            "revenue_change_30d": 22.3,
        },
    }


class TestTimeframeAnalyzer:
    """TimeframeAnalyzer测试类"""

    def test_init(self, timeframe_analyzer):
        """测试初始化"""
        assert timeframe_analyzer is not None
        assert timeframe_analyzer.llm_client is not None
        assert timeframe_analyzer.system_prompt != ""
        assert timeframe_analyzer.user_prompt_template != ""

    def test_extract_24h_data(self, timeframe_analyzer, sample_aggregated_data):
        """测试24小时数据提取"""
        data_24h = timeframe_analyzer._extract_24h_data(sample_aggregated_data)

        # 验证关键字段存在
        assert "price_change_24h" in data_24h
        assert "current_price" in data_24h
        assert "volume_24h" in data_24h
        assert "events_24h" in data_24h

        # 验证数据值
        assert data_24h["price_change_24h"] == 2.5
        assert data_24h["current_price"] == 67000
        assert data_24h["volume_24h"] == 28000000000
        assert len(data_24h["events_24h"]) == 2

    def test_extract_7d_data(self, timeframe_analyzer, sample_aggregated_data):
        """测试7天数据提取"""
        data_7d = timeframe_analyzer._extract_7d_data(sample_aggregated_data)

        # 验证关键字段存在
        assert "price_change_7d" in data_7d
        assert "twitter_mentions_7d" in data_7d
        assert "reddit_posts_7d" in data_7d
        assert "events_7d" in data_7d

        # 验证数据值
        assert data_7d["price_change_7d"] == 8.2
        assert data_7d["twitter_mentions_7d"] == 15000
        assert data_7d["reddit_posts_7d"] == 2500
        assert len(data_7d["events_7d"]) == 3

    def test_extract_30d_data(self, timeframe_analyzer, sample_aggregated_data):
        """测试30天数据提取"""
        data_30d = timeframe_analyzer._extract_30d_data(sample_aggregated_data)

        # 验证关键字段存在
        assert "price_change_30d" in data_30d
        assert "ath_distance" in data_30d
        assert "atl_distance" in data_30d
        assert "tvl_change_30d" in data_30d
        assert "events_30d" in data_30d

        # 验证数据值
        assert data_30d["price_change_30d"] == 15.6
        assert data_30d["tvl_change_30d"] == 25.0
        assert len(data_30d["events_30d"]) == 3

    def test_extract_30d_ath_atl_calculation(self, timeframe_analyzer, sample_aggregated_data):
        """测试ATH/ATL距离计算"""
        data_30d = timeframe_analyzer._extract_30d_data(sample_aggregated_data)

        # 当前价格: 67000, ATH: 69000
        # 距离ATH: (67000 - 69000) / 69000 * 100 ≈ -2.90%
        ath_distance = float(data_30d["ath_distance"])
        assert -3.0 < ath_distance < -2.5

        # 当前价格: 67000, ATL: 3000
        # 距离ATL: (67000 - 3000) / 3000 * 100 ≈ 2133.33%
        atl_distance = float(data_30d["atl_distance"])
        assert 2100 < atl_distance < 2200

    def test_format_prompt(self, timeframe_analyzer, sample_aggregated_data):
        """测试提示词格式化"""
        data_24h = timeframe_analyzer._extract_24h_data(sample_aggregated_data)
        data_7d = timeframe_analyzer._extract_7d_data(sample_aggregated_data)
        data_30d = timeframe_analyzer._extract_30d_data(sample_aggregated_data)

        prompt = timeframe_analyzer._format_prompt(
            symbol="BTC",
            data_24h=data_24h,
            data_7d=data_7d,
            data_30d=data_30d,
            project_info=sample_aggregated_data["project_info"],
            market_data=sample_aggregated_data["market_data"],
        )

        # 验证关键信息存在
        assert "BTC" in prompt
        assert "Bitcoin" in prompt
        assert "67000" in prompt
        assert "2.5" in prompt  # 24h变化
        assert "8.2" in prompt  # 7d变化
        assert "15.6" in prompt  # 30d变化

    def test_validate_output_valid(self, timeframe_analyzer):
        """测试有效输出的验证"""
        valid_output = {
            "timeframe_24h": {
                "price_change": "+2.5%",
                "volume_change": "+8.5%",
                "key_events": ["事件1", "事件2"],
                "narrative": "过去24小时，BTC价格上涨2.5%，成交量增加8.5%。主要由机构资金流入驱动。",
                "trend": "上涨",
            },
            "timeframe_7d": {
                "price_change": "+8.2%",
                "volume_trend": "持续增长",
                "key_events": ["突破阻力位", "矿工抛压降低"],
                "narrative": "过去7天，BTC累计上涨8.2%，成功突破关键阻力位。矿工抛售压力降至年内低点。",
                "trend": "上涨",
            },
            "timeframe_30d": {
                "price_change": "+15.6%",
                "milestone_events": ["ETF流入新高", "全网算力创新高"],
                "narrative": "过去30天，BTC上涨15.6%，基本面持续改善。ETF资金持续流入，全网算力创新高。",
                "trend": "上涨",
            },
            "cross_timeframe_analysis": {
                "consistency": "高",
                "momentum": "稳定上涨",
                "risk_signal": "无明显风险",
                "summary": "BTC在三个时间窗口均呈现稳定上涨态势，基本面和技术面共振向上。",
            },
            "data_sources": ["CoinGecko", "Etherscan"],
            "updated_at": "2025-10-25T14:30:00Z",
        }

        assert timeframe_analyzer._validate_output(valid_output) is True

    def test_validate_output_missing_timeframe(self, timeframe_analyzer):
        """测试缺少时间窗数据的验证"""
        invalid_output = {
            "timeframe_24h": {
                "price_change": "+2.5%",
                "key_events": [],
                "narrative": "测试",
                "trend": "上涨",
            },
            # 缺少timeframe_7d和timeframe_30d
            "cross_timeframe_analysis": {},
            "data_sources": [],
            "updated_at": "2025-10-25T14:30:00Z",
        }

        # 缺少必填时间窗应该验证失败
        assert timeframe_analyzer._validate_output(invalid_output) is False

    def test_validate_output_missing_required_fields(self, timeframe_analyzer):
        """测试缺少时间窗必填字段的验证"""
        invalid_output = {
            "timeframe_24h": {
                "price_change": "+2.5%",
                # 缺少key_events, narrative, trend
            },
            "timeframe_7d": {
                "price_change": "+8.2%",
                "key_events": [],
                "narrative": "测试",
                "trend": "上涨",
            },
            "timeframe_30d": {
                "price_change": "+15.6%",
                "key_events": [],
                "narrative": "测试",
                "trend": "上涨",
            },
            "cross_timeframe_analysis": {
                "consistency": "高",
                "momentum": "稳定",
                "risk_signal": "无",
                "summary": "测试",
            },
            "data_sources": [],
            "updated_at": "2025-10-25T14:30:00Z",
        }

        assert timeframe_analyzer._validate_output(invalid_output) is False

    def test_fix_invalid_output(self, timeframe_analyzer):
        """测试修复无效输出"""
        invalid_output = {
            "timeframe_24h": {
                "price_change": "+2.5%",
                # 缺少其他字段
            },
        }

        fixed = timeframe_analyzer._fix_invalid_output(invalid_output, "BTC")

        # 验证修复后的输出
        assert "timeframe_24h" in fixed
        assert "timeframe_7d" in fixed
        assert "timeframe_30d" in fixed
        assert "cross_timeframe_analysis" in fixed
        assert "data_sources" in fixed
        assert "updated_at" in fixed

        # 验证每个时间窗有必填字段
        for timeframe in ["timeframe_24h", "timeframe_7d", "timeframe_30d"]:
            assert "price_change" in fixed[timeframe]
            assert "key_events" in fixed[timeframe]
            assert "narrative" in fixed[timeframe]
            assert "trend" in fixed[timeframe]
            assert "BTC" in fixed[timeframe]["narrative"]

    def test_create_error_response(self, timeframe_analyzer):
        """测试创建错误响应"""
        error_resp = timeframe_analyzer._create_error_response(
            "ETH", "API timeout"
        )

        # 验证错误响应结构
        assert "timeframe_24h" in error_resp
        assert "timeframe_7d" in error_resp
        assert "timeframe_30d" in error_resp
        assert "cross_timeframe_analysis" in error_resp
        assert "error" in error_resp
        assert error_resp["error"] == "API timeout"

        # 验证所有时间窗的narrative包含币种符号
        for timeframe in ["timeframe_24h", "timeframe_7d", "timeframe_30d"]:
            assert "ETH" in error_resp[timeframe]["narrative"]

    @pytest.mark.asyncio
    @patch("app.services.research_engine.analyzers.timeframe_analyzer.llm_client")
    async def test_analyze_success(
        self, mock_llm_client, timeframe_analyzer, sample_aggregated_data
    ):
        """测试成功分析时间窗"""
        # Mock LLM响应
        mock_llm_client.chat_completion = MagicMock(
            return_value={
                "content": """{
                    "timeframe_24h": {
                        "price_change": "+2.5%",
                        "volume_change": "+8.5%",
                        "key_events": ["ETF资金流入", "突破阻力位"],
                        "narrative": "过去24小时，BTC价格稳步上涨2.5%，成交量增加8.5%。",
                        "trend": "上涨"
                    },
                    "timeframe_7d": {
                        "price_change": "+8.2%",
                        "volume_trend": "持续增长",
                        "key_events": ["矿工抛压降低"],
                        "narrative": "过去7天，BTC累计上涨8.2%。",
                        "trend": "上涨"
                    },
                    "timeframe_30d": {
                        "price_change": "+15.6%",
                        "milestone_events": ["算力新高"],
                        "narrative": "过去30天，BTC上涨15.6%。",
                        "trend": "上涨"
                    },
                    "cross_timeframe_analysis": {
                        "consistency": "高",
                        "momentum": "稳定上涨",
                        "risk_signal": "无明显风险",
                        "summary": "BTC在三个时间窗口均呈现上涨趋势。"
                    },
                    "data_sources": ["CoinGecko"],
                    "updated_at": "2025-10-25T14:30:00Z"
                }"""
            }
        )

        timeframe_analyzer.llm_client = mock_llm_client

        result = await timeframe_analyzer.analyze(
            aggregated_data=sample_aggregated_data,
        )

        # 验证结果
        assert result["timeframe_24h"]["price_change"] == "+2.5%"
        assert result["timeframe_24h"]["trend"] == "上涨"
        assert result["timeframe_7d"]["price_change"] == "+8.2%"
        assert result["timeframe_30d"]["price_change"] == "+15.6%"
        assert result["cross_timeframe_analysis"]["consistency"] == "高"

    @pytest.mark.asyncio
    @patch("app.services.research_engine.analyzers.timeframe_analyzer.llm_client")
    async def test_analyze_llm_failure(
        self, mock_llm_client, timeframe_analyzer, sample_aggregated_data
    ):
        """测试LLM调用失败时的降级处理"""
        # Mock LLM抛出异常
        mock_llm_client.chat_completion = MagicMock(
            side_effect=Exception("LLM service unavailable")
        )

        timeframe_analyzer.llm_client = mock_llm_client

        result = await timeframe_analyzer.analyze(
            aggregated_data=sample_aggregated_data,
        )

        # 验证降级响应
        assert "error" in result
        assert "timeframe_24h" in result
        assert "timeframe_7d" in result
        assert "timeframe_30d" in result

    def test_trend_values(self, timeframe_analyzer):
        """测试趋势值的有效性"""
        valid_trends = ["上涨", "下跌", "横盘"]

        for trend in valid_trends:
            output = {
                "timeframe_24h": {
                    "price_change": "+5%",
                    "key_events": ["测试"],
                    "narrative": "这是一个足够长的叙事描述，用于测试验证逻辑是否正确工作。",
                    "trend": trend,
                },
                "timeframe_7d": {
                    "price_change": "+5%",
                    "key_events": ["测试"],
                    "narrative": "这是一个足够长的叙事描述，用于测试验证逻辑是否正确工作。",
                    "trend": trend,
                },
                "timeframe_30d": {
                    "price_change": "+5%",
                    "key_events": ["测试"],
                    "narrative": "这是一个足够长的叙事描述，用于测试验证逻辑是否正确工作。",
                    "trend": trend,
                },
                "cross_timeframe_analysis": {
                    "consistency": "高",
                    "momentum": "稳定",
                    "risk_signal": "无",
                    "summary": "综合分析结果",
                },
                "data_sources": ["CoinGecko"],
                "updated_at": "2025-10-25T14:30:00Z",
            }

            # 所有有效趋势值都应该通过验证
            assert timeframe_analyzer._validate_output(output) is True

    def test_key_events_max_count(self, timeframe_analyzer):
        """测试key_events数量限制"""
        # 超过3个事件（虽然会警告，但不应该导致验证失败）
        output = {
            "timeframe_24h": {
                "price_change": "+2%",
                "key_events": ["事件1", "事件2", "事件3", "事件4", "事件5"],  # 超过max_count=3
                "narrative": "这是一个足够长的叙事描述，包含必要的信息和分析内容。",
                "trend": "上涨",
            },
            "timeframe_7d": {
                "price_change": "+5%",
                "key_events": ["事件1"],
                "narrative": "这是一个足够长的叙事描述。",
                "trend": "上涨",
            },
            "timeframe_30d": {
                "price_change": "+10%",
                "key_events": ["事件1"],
                "narrative": "这是一个足够长的叙事描述。",
                "trend": "上涨",
            },
            "cross_timeframe_analysis": {
                "consistency": "高",
                "momentum": "稳定",
                "risk_signal": "无",
                "summary": "综合分析",
            },
            "data_sources": ["CoinGecko"],
            "updated_at": "2025-10-25T14:30:00Z",
        }

        # key_events超过限制只会警告，不会导致验证失败
        assert timeframe_analyzer._validate_output(output) is True


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
