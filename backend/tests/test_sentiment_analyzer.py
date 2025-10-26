"""
Sentiment Analyzer 单元测试
测试SentimentAnalyzer类的功能
"""
import pytest
import asyncio
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from app.services.research_engine.analyzers.sentiment_analyzer import SentimentAnalyzer


@pytest.fixture
def sentiment_analyzer():
    """创建SentimentAnalyzer实例"""
    return SentimentAnalyzer()


@pytest.fixture
def sample_aggregated_data():
    """模拟的聚合数据"""
    return {
        "symbol": "ETH",
        "coingecko_id": "ethereum",
        "project_info": {
            "name": "Ethereum",
            "categories": ["Smart Contract Platform", "DeFi"],
        },
        "market_data": {
            "current_price": 3500,
            "price_change_percentage_24h": 3.5,
        },
        "social_data": {
            "twitter": {
                "followers": 3000000,
                "mentions_7d": 25000,
                "engagement_7d": 150000,
                "sentiment_distribution": {
                    "positive": 15000,
                    "neutral": 8000,
                    "negative": 2000,
                },
                "sample_tweets": [
                    {"text": "ETH's Dencun upgrade is a game changer!", "engagement": 5000},
                    {"text": "Staking rewards looking good", "engagement": 3000},
                ],
            },
            "reddit": {
                "subscribers": 1500000,
                "posts_7d": 500,
                "comments_7d": 8000,
                "sentiment_distribution": {
                    "positive": 250,
                    "neutral": 200,
                    "negative": 50,
                },
                "sample_posts": [
                    {"text": "Deep dive into Ethereum's scaling solutions", "score": 1200},
                    {"text": "Why I'm bullish on ETH long term", "score": 800},
                ],
            },
            "news": {
                "count_7d": 45,
                "mainstream_coverage": "Bloomberg, CNBC, CoinDesk",
                "sentiment_distribution": {
                    "positive": 25,
                    "neutral": 15,
                    "negative": 5,
                },
                "sample_headlines": [
                    "Ethereum upgrade successful, gas fees drop 50%",
                    "Institutional interest in ETH staking surges",
                ],
            },
        },
    }


class TestSentimentAnalyzer:
    """SentimentAnalyzer测试类"""

    def test_init(self, sentiment_analyzer):
        """测试初始化"""
        assert sentiment_analyzer is not None
        assert sentiment_analyzer.llm_client is not None
        assert sentiment_analyzer.system_prompt != ""
        assert sentiment_analyzer.user_prompt_template != ""

    def test_extract_twitter_data(self, sentiment_analyzer, sample_aggregated_data):
        """测试Twitter数据提取"""
        twitter_data = sentiment_analyzer._extract_twitter_data(sample_aggregated_data)

        # 验证关键字段存在
        assert "followers" in twitter_data
        assert "mentions_7d" in twitter_data
        assert "positive_count" in twitter_data
        assert "positive_percent" in twitter_data
        assert "sample_tweets" in twitter_data

        # 验证数据值
        assert twitter_data["followers"] == 3000000
        assert twitter_data["mentions_7d"] == 25000
        assert twitter_data["positive_count"] == 15000
        assert twitter_data["negative_count"] == 2000

        # 验证百分比计算
        assert twitter_data["positive_percent"] == 60.0  # 15000 / 25000
        assert twitter_data["negative_percent"] == 8.0  # 2000 / 25000

    def test_extract_reddit_data(self, sentiment_analyzer, sample_aggregated_data):
        """测试Reddit数据提取"""
        reddit_data = sentiment_analyzer._extract_reddit_data(sample_aggregated_data)

        # 验证关键字段存在
        assert "subscribers" in reddit_data
        assert "posts_7d" in reddit_data
        assert "positive_count" in reddit_data
        assert "sample_posts" in reddit_data

        # 验证数据值
        assert reddit_data["subscribers"] == 1500000
        assert reddit_data["posts_7d"] == 500
        assert reddit_data["positive_count"] == 250
        assert reddit_data["negative_count"] == 50

        # 验证百分比计算
        assert reddit_data["positive_percent"] == 50.0  # 250 / 500
        assert reddit_data["negative_percent"] == 10.0  # 50 / 500

    def test_extract_news_data(self, sentiment_analyzer, sample_aggregated_data):
        """测试新闻数据提取"""
        news_data = sentiment_analyzer._extract_news_data(sample_aggregated_data)

        # 验证关键字段存在
        assert "count_7d" in news_data
        assert "mainstream_media_coverage" in news_data
        assert "positive_count" in news_data
        assert "sample_headlines" in news_data

        # 验证数据值
        assert news_data["count_7d"] == 45
        assert news_data["positive_count"] == 25
        assert news_data["negative_count"] == 5

        # 验证百分比计算
        assert news_data["positive_percent"] == 55.6  # 25 / 45
        assert news_data["negative_percent"] == 11.1  # 5 / 45

    def test_format_sample_content_with_list(self, sentiment_analyzer):
        """测试格式化示例内容（列表形式）"""
        samples = [
            {"text": "Tweet 1", "engagement": 1000},
            {"text": "Tweet 2", "engagement": 500},
        ]

        formatted = sentiment_analyzer._format_sample_content(samples, "推文")

        assert "1. Tweet 1" in formatted
        assert "互动:1000" in formatted
        assert "2. Tweet 2" in formatted

    def test_format_sample_content_empty(self, sentiment_analyzer):
        """测试格式化空内容"""
        formatted = sentiment_analyzer._format_sample_content([], "推文")
        assert "暂无推文示例" in formatted

    def test_format_prompt(self, sentiment_analyzer, sample_aggregated_data):
        """测试提示词格式化"""
        twitter_data = sentiment_analyzer._extract_twitter_data(sample_aggregated_data)
        reddit_data = sentiment_analyzer._extract_reddit_data(sample_aggregated_data)
        news_data = sentiment_analyzer._extract_news_data(sample_aggregated_data)

        prompt = sentiment_analyzer._format_prompt(
            symbol="ETH",
            project_name="Ethereum",
            current_price=3500,
            price_change_24h=3.5,
            twitter_data=twitter_data,
            reddit_data=reddit_data,
            news_data=news_data,
        )

        # 验证关键信息存在
        assert "ETH" in prompt
        assert "Ethereum" in prompt
        assert "3500" in prompt
        assert "3.5" in prompt
        assert "3000000" in prompt  # Twitter followers

    def test_validate_output_valid(self, sentiment_analyzer):
        """测试有效输出的验证"""
        valid_output = {
            "overall_sentiment": {
                "label": "积极",
                "score": 75,
                "confidence": 85,
                "summary": "ETH社区情绪积极，升级成功推动热度上升。",
            },
            "sentiment_breakdown": {
                "positive_percent": 60,
                "neutral_percent": 30,
                "negative_percent": 10,
                "trend": "情绪上升",
            },
            "top_topics": [
                {
                    "topic": "Dencun升级",
                    "mentions": 5000,
                    "sentiment": "积极",
                    "keywords": ["upgrade", "dencun"],
                    "impact": "高",
                },
                {
                    "topic": "Gas费下降",
                    "mentions": 3000,
                    "sentiment": "积极",
                    "keywords": ["gas", "fees"],
                    "impact": "高",
                },
                {
                    "topic": "质押收益",
                    "mentions": 2000,
                    "sentiment": "积极",
                    "keywords": ["staking", "yield"],
                    "impact": "中",
                },
            ],
            "key_influencers": [
                {
                    "name": "@VitalikButerin",
                    "platform": "Twitter",
                    "followers": 5000000,
                    "recent_stance": "看涨",
                    "key_message": "Dencun is live!",
                    "credibility": "高",
                },
                {
                    "name": "u/ethfinance",
                    "platform": "Reddit",
                    "karma": 100000,
                    "recent_stance": "看涨",
                    "key_message": "Long term bullish on scaling",
                    "credibility": "高",
                },
            ],
            "community_health": {
                "activity_level": "高",
                "growth_trend": "快速增长",
                "engagement_quality": "高质量讨论",
                "fud_level": "无明显FUD",
                "fomo_level": "轻度",
                "concerns": ["竞品威胁"],
            },
            "narrative_analysis": {
                "dominant_narrative": "技术升级驱动",
                "narrative_strength": "强",
                "competing_narratives": ["长期价值投资"],
                "narrative_shift": "从炒作转向基本面",
            },
            "risk_signals": [],
            "data_sources": ["Twitter", "Reddit"],
            "updated_at": "2025-10-25T14:30:00Z",
        }

        assert sentiment_analyzer._validate_output(valid_output) is True

    def test_validate_output_missing_required_fields(self, sentiment_analyzer):
        """测试缺少必填字段的验证"""
        invalid_output = {
            "overall_sentiment": {
                "label": "积极",
                "score": 75,
            },
            # 缺少其他必填字段
        }

        assert sentiment_analyzer._validate_output(invalid_output) is False

    def test_validate_output_invalid_score(self, sentiment_analyzer):
        """测试无效分数的验证"""
        invalid_output = {
            "overall_sentiment": {
                "label": "积极",
                "score": 150,  # 超出范围
                "confidence": 85,
                "summary": "测试",
            },
            "sentiment_breakdown": {
                "positive_percent": 60,
                "neutral_percent": 30,
                "negative_percent": 10,
                "trend": "情绪上升",
            },
            "top_topics": [{"topic": "测试", "mentions": 100, "sentiment": "积极", "keywords": [], "impact": "高"}] * 3,
            "key_influencers": [
                {
                    "name": "测试",
                    "platform": "Twitter",
                    "followers": 100,
                    "recent_stance": "中性",
                    "key_message": "测试",
                    "credibility": "中",
                }
            ]
            * 2,
            "community_health": {
                "activity_level": "高",
                "growth_trend": "稳定",
                "engagement_quality": "高",
                "fud_level": "无",
                "fomo_level": "无",
            },
            "narrative_analysis": {
                "dominant_narrative": "测试",
                "narrative_strength": "强",
                "competing_narratives": [],
                "narrative_shift": "无",
            },
            "data_sources": [],
            "updated_at": "2025-10-25T14:30:00Z",
        }

        assert sentiment_analyzer._validate_output(invalid_output) is False

    def test_validate_output_invalid_breakdown(self, sentiment_analyzer):
        """测试无效的情绪分布"""
        # 百分比之和不等于100
        invalid_output = {
            "overall_sentiment": {
                "label": "积极",
                "score": 75,
                "confidence": 85,
                "summary": "测试",
            },
            "sentiment_breakdown": {
                "positive_percent": 50,
                "neutral_percent": 30,
                "negative_percent": 10,  # 总和只有90
                "trend": "情绪上升",
            },
            "top_topics": [{"topic": "测试", "mentions": 100, "sentiment": "积极", "keywords": [], "impact": "高"}] * 3,
            "key_influencers": [
                {
                    "name": "测试",
                    "platform": "Twitter",
                    "followers": 100,
                    "recent_stance": "中性",
                    "key_message": "测试",
                    "credibility": "中",
                }
            ]
            * 2,
            "community_health": {
                "activity_level": "高",
                "growth_trend": "稳定",
                "engagement_quality": "高",
                "fud_level": "无",
                "fomo_level": "无",
            },
            "narrative_analysis": {
                "dominant_narrative": "测试",
                "narrative_strength": "强",
                "competing_narratives": [],
                "narrative_shift": "无",
            },
            "data_sources": [],
            "updated_at": "2025-10-25T14:30:00Z",
        }

        # 应该通过验证但会有警告（百分比和不等于100只警告）
        assert sentiment_analyzer._validate_output(invalid_output) is True

    def test_fix_invalid_output(self, sentiment_analyzer):
        """测试修复无效输出"""
        invalid_output = {
            "overall_sentiment": {
                "score": 75,
                # 缺少其他字段
            },
        }

        fixed = sentiment_analyzer._fix_invalid_output(invalid_output, "ETH")

        # 验证修复后的输出
        assert "overall_sentiment" in fixed
        assert "label" in fixed["overall_sentiment"]
        assert "summary" in fixed["overall_sentiment"]
        assert "ETH" in fixed["overall_sentiment"]["summary"]

        assert "sentiment_breakdown" in fixed
        assert "top_topics" in fixed
        assert len(fixed["top_topics"]) >= 3

        assert "key_influencers" in fixed
        assert len(fixed["key_influencers"]) >= 2

        assert "community_health" in fixed
        assert "narrative_analysis" in fixed

    def test_create_error_response(self, sentiment_analyzer):
        """测试创建错误响应"""
        error_resp = sentiment_analyzer._create_error_response(
            "ETH", "API timeout"
        )

        # 验证错误响应结构
        assert error_resp["overall_sentiment"]["label"] == "中性"
        assert error_resp["overall_sentiment"]["confidence"] == 30
        assert "ETH" in error_resp["overall_sentiment"]["summary"]
        assert "error" in error_resp
        assert error_resp["error"] == "API timeout"

    @pytest.mark.asyncio
    @patch("app.services.research_engine.analyzers.sentiment_analyzer.llm_client")
    async def test_analyze_success(
        self, mock_llm_client, sentiment_analyzer, sample_aggregated_data
    ):
        """测试成功分析情绪"""
        # Mock LLM响应
        mock_llm_client.chat_completion = MagicMock(
            return_value={
                "content": """{
                    "overall_sentiment": {
                        "label": "积极",
                        "score": 75,
                        "confidence": 85,
                        "summary": "ETH社区情绪积极，Dencun升级成功。"
                    },
                    "sentiment_breakdown": {
                        "positive_percent": 60,
                        "neutral_percent": 30,
                        "negative_percent": 10,
                        "trend": "情绪上升"
                    },
                    "top_topics": [
                        {
                            "topic": "Dencun升级",
                            "mentions": 5000,
                            "sentiment": "积极",
                            "keywords": ["upgrade"],
                            "impact": "高"
                        },
                        {
                            "topic": "Gas费下降",
                            "mentions": 3000,
                            "sentiment": "积极",
                            "keywords": ["gas"],
                            "impact": "高"
                        },
                        {
                            "topic": "质押",
                            "mentions": 2000,
                            "sentiment": "积极",
                            "keywords": ["staking"],
                            "impact": "中"
                        }
                    ],
                    "key_influencers": [
                        {
                            "name": "@VitalikButerin",
                            "platform": "Twitter",
                            "followers": 5000000,
                            "recent_stance": "看涨",
                            "key_message": "Upgrade successful",
                            "credibility": "高"
                        },
                        {
                            "name": "u/ethfinance",
                            "platform": "Reddit",
                            "karma": 100000,
                            "recent_stance": "看涨",
                            "key_message": "Bullish long term",
                            "credibility": "高"
                        }
                    ],
                    "community_health": {
                        "activity_level": "高",
                        "growth_trend": "快速增长",
                        "engagement_quality": "高质量讨论",
                        "fud_level": "无明显FUD",
                        "fomo_level": "轻度",
                        "concerns": ["竞品威胁"]
                    },
                    "narrative_analysis": {
                        "dominant_narrative": "技术升级驱动",
                        "narrative_strength": "强",
                        "competing_narratives": ["价值投资"],
                        "narrative_shift": "转向基本面"
                    },
                    "risk_signals": [],
                    "data_sources": ["Twitter", "Reddit"],
                    "updated_at": "2025-10-25T14:30:00Z"
                }"""
            }
        )

        sentiment_analyzer.llm_client = mock_llm_client

        result = await sentiment_analyzer.analyze(
            aggregated_data=sample_aggregated_data,
        )

        # 验证结果
        assert result["overall_sentiment"]["label"] == "积极"
        assert result["overall_sentiment"]["score"] == 75
        assert len(result["top_topics"]) == 3
        assert len(result["key_influencers"]) == 2

    @pytest.mark.asyncio
    @patch("app.services.research_engine.analyzers.sentiment_analyzer.llm_client")
    async def test_analyze_llm_failure(
        self, mock_llm_client, sentiment_analyzer, sample_aggregated_data
    ):
        """测试LLM调用失败时的降级处理"""
        # Mock LLM抛出异常
        mock_llm_client.chat_completion = MagicMock(
            side_effect=Exception("LLM service unavailable")
        )

        sentiment_analyzer.llm_client = mock_llm_client

        result = await sentiment_analyzer.analyze(
            aggregated_data=sample_aggregated_data,
        )

        # 验证降级响应
        assert "error" in result
        assert result["overall_sentiment"]["label"] == "中性"
        assert result["overall_sentiment"]["confidence"] <= 50

    def test_sentiment_label_values(self, sentiment_analyzer):
        """测试情绪标签的有效性"""
        valid_labels = ["积极", "中性", "消极"]

        for label in valid_labels:
            output = {
                "overall_sentiment": {
                    "label": label,
                    "score": 50,
                    "confidence": 80,
                    "summary": "测试摘要，这是一个足够长的摘要内容。",
                },
                "sentiment_breakdown": {
                    "positive_percent": 33,
                    "neutral_percent": 34,
                    "negative_percent": 33,
                    "trend": "情绪稳定",
                },
                "top_topics": [
                    {"topic": f"话题{i}", "mentions": 100, "sentiment": "积极", "keywords": [], "impact": "高"}
                    for i in range(3)
                ],
                "key_influencers": [
                    {
                        "name": f"KOL{i}",
                        "platform": "Twitter",
                        "followers": 1000,
                        "recent_stance": "中性",
                        "key_message": "测试",
                        "credibility": "中",
                    }
                    for i in range(2)
                ],
                "community_health": {
                    "activity_level": "中",
                    "growth_trend": "稳定",
                    "engagement_quality": "一般",
                    "fud_level": "无",
                    "fomo_level": "无",
                },
                "narrative_analysis": {
                    "dominant_narrative": "测试",
                    "narrative_strength": "中",
                    "competing_narratives": [],
                    "narrative_shift": "无",
                },
                "data_sources": ["Twitter"],
                "updated_at": "2025-10-25T14:30:00Z",
            }

            # 所有有效标签都应该通过验证
            assert sentiment_analyzer._validate_output(output) is True


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
