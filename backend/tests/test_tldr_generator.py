"""
TL;DR Generator 单元测试
测试TLDRGenerator类的功能
"""
import pytest
import asyncio
from unittest.mock import patch, MagicMock

from app.services.research_engine.analyzers.tldr_generator import TLDRGenerator


@pytest.fixture
def tldr_generator():
    """创建TLDRGenerator实例"""
    return TLDRGenerator()


@pytest.fixture
def sample_aggregated_data():
    """模拟的聚合数据"""
    return {
        "symbol": "BTC",
        "coingecko_id": "bitcoin",
        "project_info": {
            "name": "Bitcoin",
            "categories": ["Cryptocurrency", "Store of Value"],
            "description": {
                "en": "Bitcoin is the first decentralized cryptocurrency."
            },
        },
        "market_data": {
            "current_price": 67000,
            "market_cap": 1300000000000,
            "market_cap_rank": 1,
            "price_change_percentage_24h": 2.5,
            "price_change_percentage_7d": 8.2,
            "price_change_percentage_30d": 15.6,
            "total_volume": 28000000000,
            "circulating_supply": 19500000,
            "total_supply": 21000000,
        },
        "social_data": {
            "twitter": {"followers": 5000000},
            "reddit": {"subscribers": 4500000},
            "overall_sentiment": "positive",
            "discussion_heat": "high",
        },
        "onchain_data": {
            "active_addresses": 950000,
            "holder_count": 50000000,
            "whale_activity": "moderate",
        },
    }


class TestTLDRGenerator:
    """TLDRGenerator测试类"""

    def test_init(self, tldr_generator):
        """测试初始化"""
        assert tldr_generator is not None
        assert tldr_generator.llm_client is not None
        assert tldr_generator.system_prompt != ""
        assert tldr_generator.user_prompt_template != ""

    def test_format_prompt(self, tldr_generator, sample_aggregated_data):
        """测试提示词格式化"""
        prompt = tldr_generator._format_prompt(
            query="Analyze Bitcoin",
            symbol="BTC",
            project_info=sample_aggregated_data["project_info"],
            market_data=sample_aggregated_data["market_data"],
            social_data=sample_aggregated_data["social_data"],
            onchain_data=sample_aggregated_data["onchain_data"],
        )

        # 验证关键信息存在
        assert "BTC" in prompt
        assert "Bitcoin" in prompt
        assert "67000" in prompt
        assert "2.5" in prompt

    def test_validate_output_valid(self, tldr_generator):
        """测试有效输出的验证"""
        valid_output = {
            "judgment": "BULL",
            "judgment_emoji": "🟢",
            "confidence": 85,
            "confidence_level": "高",
            "summary": "Bitcoin价格上涨2.5%，市值稳居第一，社区讨论热度高。",
            "key_metrics": {
                "price": "$67,000",
                "market_cap_rank": 1,
                "24h_change": "+2.5%",
                "social_heat": "高",
            },
            "reasoning": "价格稳定上涨，社区活跃度高，技术基本面强劲。",
        }

        assert tldr_generator._validate_output(valid_output) is True

    def test_validate_output_invalid_judgment(self, tldr_generator):
        """测试无效judgment值的验证"""
        invalid_output = {
            "judgment": "INVALID",  # 无效值
            "judgment_emoji": "❓",
            "confidence": 50,
            "confidence_level": "中等",
            "summary": "Test summary",
            "key_metrics": {},
            "reasoning": "Test reasoning",
        }

        assert tldr_generator._validate_output(invalid_output) is False

    def test_validate_output_missing_fields(self, tldr_generator):
        """测试缺少必填字段的验证"""
        incomplete_output = {
            "judgment": "NEUTRAL",
            # 缺少其他必填字段
        }

        assert tldr_generator._validate_output(incomplete_output) is False

    def test_validate_output_invalid_confidence(self, tldr_generator):
        """测试超出范围的置信度"""
        invalid_output = {
            "judgment": "BULL",
            "judgment_emoji": "🟢",
            "confidence": 150,  # 超出范围
            "confidence_level": "超高",
            "summary": "Test summary",
            "key_metrics": {},
            "reasoning": "Test reasoning",
        }

        assert tldr_generator._validate_output(invalid_output) is False

    def test_fix_invalid_output(self, tldr_generator):
        """测试修复无效输出"""
        invalid_output = {
            "judgment": "INVALID_JUDGMENT",
            "confidence": 150,  # 超出范围
        }

        fixed = tldr_generator._fix_invalid_output(invalid_output, "BTC")

        # 验证修复后的输出
        assert fixed["judgment"] == "NEUTRAL"
        assert fixed["judgment_emoji"] == "🟡"
        assert 0 <= fixed["confidence"] <= 100
        assert "BTC" in fixed["summary"]

    def test_create_error_response(self, tldr_generator):
        """测试创建错误响应"""
        error_resp = tldr_generator._create_error_response(
            "ETH", "API timeout"
        )

        assert error_resp["judgment"] == "NEUTRAL"
        assert error_resp["confidence"] == 30
        assert "ETH" in error_resp["summary"]
        assert "error" in error_resp
        assert error_resp["error"] == "API timeout"

    @pytest.mark.asyncio
    @patch("app.services.research_engine.analyzers.tldr_generator.llm_client")
    async def test_generate_tldr_success(
        self, mock_llm_client, tldr_generator, sample_aggregated_data
    ):
        """测试成功生成TL;DR"""
        # Mock LLM响应
        mock_llm_client.chat_completion = MagicMock(
            return_value={
                "content": '{"judgment": "BULL", "judgment_emoji": "🟢", "confidence": 85, "confidence_level": "高", "summary": "Bitcoin价格上涨2.5%，市值稳居第一。", "key_metrics": {"price": "$67,000"}, "reasoning": "价格上涨，社区活跃。"}'
            }
        )

        tldr_generator.llm_client = mock_llm_client

        result = await tldr_generator.generate_tldr(
            query="Analyze Bitcoin",
            aggregated_data=sample_aggregated_data,
        )

        # 验证结果
        assert result["judgment"] == "BULL"
        assert result["confidence"] == 85
        assert "Bitcoin" in result["summary"]

    @pytest.mark.asyncio
    @patch("app.services.research_engine.analyzers.tldr_generator.llm_client")
    async def test_generate_tldr_llm_failure(
        self, mock_llm_client, tldr_generator, sample_aggregated_data
    ):
        """测试LLM调用失败时的降级处理"""
        # Mock LLM抛出异常
        mock_llm_client.chat_completion = MagicMock(
            side_effect=Exception("LLM service unavailable")
        )

        tldr_generator.llm_client = mock_llm_client

        result = await tldr_generator.generate_tldr(
            query="Analyze Bitcoin",
            aggregated_data=sample_aggregated_data,
        )

        # 验证降级响应
        assert result["judgment"] == "NEUTRAL"
        assert result["confidence"] <= 50
        assert "error" in result

    def test_confidence_ranges(self, tldr_generator):
        """测试不同置信度等级"""
        test_cases = [
            (95, "BULL", True),  # 极高置信度
            (75, "NEUTRAL", True),  # 高置信度
            (55, "BEAR", True),  # 中等置信度
            (35, "BULL", True),  # 低置信度
            (0, "NEUTRAL", True),  # 最低置信度
            (-10, "BULL", False),  # 无效：负数
            (105, "BEAR", False),  # 无效：超出范围
        ]

        for confidence, judgment, should_be_valid in test_cases:
            output = {
                "judgment": judgment,
                "judgment_emoji": "🟢" if judgment == "BULL" else "🔴" if judgment == "BEAR" else "🟡",
                "confidence": confidence,
                "confidence_level": "测试",
                "summary": "Test summary with sufficient length",
                "key_metrics": {},
                "reasoning": "Test reasoning with some detail",
            }

            result = tldr_generator._validate_output(output)
            assert result == should_be_valid, f"Confidence {confidence} should be {'valid' if should_be_valid else 'invalid'}"


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
