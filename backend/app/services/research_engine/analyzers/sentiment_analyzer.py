"""
社媒情绪分析器
分析Twitter、Reddit、新闻等社交媒体数据，识别情绪倾向和热门话题
"""
import json
import time
from typing import Dict, Any, Optional, List
from pathlib import Path
import yaml

from app.services.llm import llm_client, ModelConfig
from app.core.config import settings
from app.services.research_engine.analyzers.analyzer_output import (
    AnalyzerOutput,
    create_analyzer_output,
    create_error_output,
    create_sentiment_pie_hint,
)


class SentimentAnalyzer:
    """
    社媒情绪分析器
    参考：openspec/changes/add-crypto-ai-search-platform/specs/ai-analysis/spec.md
    Scenario: 社媒情绪分析
    """

    def __init__(self):
        """初始化社媒情绪分析器"""
        self.llm_client = llm_client
        self._load_prompts()

    def _load_prompts(self):
        """加载提示词模板"""
        prompts_dir = Path(settings.BASE_DIR) / "prompts" / "deep_research"
        sentiment_yaml_path = prompts_dir / "sentiment.yaml"

        if not sentiment_yaml_path.exists():
            raise FileNotFoundError(f"情绪分析提示词文件不存在: {sentiment_yaml_path}")

        with open(sentiment_yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        self.system_prompt = data.get("system_prompt", "")
        self.user_prompt_template = data.get("user_prompt_template", "")
        self.model_config = data.get("model_config", {})
        self.output_validation = data.get("output_validation", {})

    async def analyze(
        self,
        aggregated_data: Dict[str, Any],
    ) -> AnalyzerOutput:
        """
        分析社交媒体情绪

        Args:
            aggregated_data: 聚合后的项目数据（来自DataAggregator）

        Returns:
            AnalyzerOutput: 包含情绪分析数据、元数据和可视化提示
            data格式：
            {
                "overall_sentiment": {
                    "label": "积极 | 中性 | 消极",
                    "score": 75,
                    "confidence": 85,
                    "summary": "..."
                },
                "sentiment_breakdown": {
                    "positive_percent": 60,
                    "neutral_percent": 30,
                    "negative_percent": 10,
                    "trend": "情绪上升 | 情绪稳定 | 情绪下降"
                },
                "top_topics": [...],
                "key_influencers": [...],
                "community_health": {...},
                "narrative_analysis": {...},
                "risk_signals": [...],
                "data_sources": [...],
                "updated_at": "..."
            }
        """
        start_time = time.time()

        # 提取必要数据
        symbol = aggregated_data.get("symbol", "Unknown")
        project_info = aggregated_data.get("project_info", {})
        market_data = aggregated_data.get("market_data", {})

        # 提取社交媒体数据
        twitter_data = self._extract_twitter_data(aggregated_data)
        reddit_data = self._extract_reddit_data(aggregated_data)
        news_data = self._extract_news_data(aggregated_data)

        # 增强分析各个数据源
        twitter_analysis = self._analyze_twitter_sentiment(twitter_data, symbol)
        reddit_analysis = self._analyze_reddit_sentiment(reddit_data, symbol)
        news_analysis = self._analyze_news_sentiment(news_data, symbol)

        # 综合情绪评分
        comprehensive_sentiment = self._calculate_comprehensive_sentiment(
            twitter_analysis, reddit_analysis, news_analysis, market_data
        )

        # 格式化提示词
        user_prompt = self._format_prompt(
            symbol=symbol,
            project_name=project_info.get("name", symbol),
            current_price=market_data.get("current_price", "N/A"),
            price_change_24h=market_data.get("price_change_percentage_24h", "N/A"),
            twitter_data=twitter_data,
            reddit_data=reddit_data,
            news_data=news_data,
            twitter_analysis=twitter_analysis,
            reddit_analysis=reddit_analysis,
            news_analysis=news_analysis,
            comprehensive_sentiment=comprehensive_sentiment,
        )

        # 调用LLM生成
        model_used = self.model_config.get("primary_model", ModelConfig.DEEP_RESEARCH_SUMMARY)
        fallback_used = False

        try:
            # 使用qwen3-30b模型（情绪分析专用）
            result = await self._call_llm(user_prompt, use_fallback=False)
        except Exception as e:
            print(f"⚠️ 主模型调用失败: {e}，尝试fallback模型")
            try:
                # Fallback到qwen3-30b（情绪分析用同一个模型）
                result = await self._call_llm(user_prompt, use_fallback=True)
                model_used = self.model_config.get("fallback_model", ModelConfig.QUICK_CHAT)
                fallback_used = True
            except Exception as fallback_error:
                # 如果两个模型都失败，返回默认响应
                print(f"❌ Fallback模型也失败: {fallback_error}")
                return self._create_error_response(symbol, str(fallback_error), model_used)

        # 验证输出格式
        validation_warnings = []
        if not self._validate_output(result):
            print("⚠️ 输出格式验证失败，使用默认值补全")
            validation_warnings.append("输出格式验证失败，已使用默认值补全")
            result = self._fix_invalid_output(result, symbol)

        # 计算生成时间
        generation_time_ms = int((time.time() - start_time) * 1000)

        # 提取情绪百分比用于可视化
        sentiment_breakdown = result.get("sentiment_breakdown", {})
        positive_pct = sentiment_breakdown.get("positive_percent", 0)
        neutral_pct = sentiment_breakdown.get("neutral_percent", 0)
        negative_pct = sentiment_breakdown.get("negative_percent", 0)

        # 创建情绪饼图可视化提示
        visualization_hints = []
        if positive_pct or neutral_pct or negative_pct:
            visualization_hints.append(
                create_sentiment_pie_hint(positive_pct, neutral_pct, negative_pct)
            )

        # 包装为AnalyzerOutput
        return create_analyzer_output(
            data=result,
            analyzer_name="SentimentAnalyzer",
            model_used=model_used,
            fallback_used=fallback_used,
            generation_time_ms=generation_time_ms,
            confidence=result.get("overall_sentiment", {}).get("confidence"),
            data_sources=["Twitter", "Reddit", "News"],
            visualization_hints=visualization_hints,
            validation_passed=len(validation_warnings) == 0,
            validation_warnings=validation_warnings,
        )

    def _extract_twitter_data(self, aggregated_data: Dict) -> Dict:
        """
        提取Twitter数据

        Args:
            aggregated_data: 聚合数据

        Returns:
            Dict: Twitter数据
        """
        social_data = aggregated_data.get("social_data", {})
        twitter = social_data.get("twitter", {})

        # 计算情绪占比（如果数据中有sentiment_distribution）
        sentiment_dist = twitter.get("sentiment_distribution", {})
        total_tweets = twitter.get("mentions_7d", 0) or 1  # 避免除零

        positive_count = sentiment_dist.get("positive", 0)
        neutral_count = sentiment_dist.get("neutral", 0)
        negative_count = sentiment_dist.get("negative", 0)

        # 如果没有具体数字，使用百分比估算
        if positive_count == 0 and neutral_count == 0 and negative_count == 0:
            positive_pct = sentiment_dist.get("positive_percent", 50)
            neutral_pct = sentiment_dist.get("neutral_percent", 40)
            negative_pct = sentiment_dist.get("negative_percent", 10)
            positive_count = int(total_tweets * positive_pct / 100)
            neutral_count = int(total_tweets * neutral_pct / 100)
            negative_count = int(total_tweets * negative_pct / 100)
        else:
            # 计算百分比
            total = positive_count + neutral_count + negative_count or 1
            positive_pct = round(positive_count / total * 100, 1)
            neutral_pct = round(neutral_count / total * 100, 1)
            negative_pct = round(negative_count / total * 100, 1)

        # 格式化示例推文
        sample_tweets = twitter.get("sample_tweets", [])
        formatted_tweets = self._format_sample_content(sample_tweets, "推文")

        return {
            "followers": twitter.get("followers", "N/A"),
            "mentions_7d": twitter.get("mentions_7d", "N/A"),
            "engagement_7d": twitter.get("engagement_7d", "N/A"),
            "positive_count": positive_count,
            "positive_percent": positive_pct,
            "neutral_count": neutral_count,
            "neutral_percent": neutral_pct,
            "negative_count": negative_count,
            "negative_percent": negative_pct,
            "sample_tweets": formatted_tweets,
        }

    def _extract_reddit_data(self, aggregated_data: Dict) -> Dict:
        """
        提取Reddit数据

        Args:
            aggregated_data: 聚合数据

        Returns:
            Dict: Reddit数据
        """
        social_data = aggregated_data.get("social_data", {})
        reddit = social_data.get("reddit", {})

        # 计算情绪占比
        sentiment_dist = reddit.get("sentiment_distribution", {})
        total_posts = reddit.get("posts_7d", 0) or 1

        positive_count = sentiment_dist.get("positive", 0)
        neutral_count = sentiment_dist.get("neutral", 0)
        negative_count = sentiment_dist.get("negative", 0)

        # 如果没有具体数字，使用百分比估算
        if positive_count == 0 and neutral_count == 0 and negative_count == 0:
            positive_pct = sentiment_dist.get("positive_percent", 45)
            neutral_pct = sentiment_dist.get("neutral_percent", 45)
            negative_pct = sentiment_dist.get("negative_percent", 10)
            positive_count = int(total_posts * positive_pct / 100)
            neutral_count = int(total_posts * neutral_pct / 100)
            negative_count = int(total_posts * negative_pct / 100)
        else:
            total = positive_count + neutral_count + negative_count or 1
            positive_pct = round(positive_count / total * 100, 1)
            neutral_pct = round(neutral_count / total * 100, 1)
            negative_pct = round(negative_count / total * 100, 1)

        # 格式化示例帖子
        sample_posts = reddit.get("sample_posts", [])
        formatted_posts = self._format_sample_content(sample_posts, "帖子")

        return {
            "subscribers": reddit.get("subscribers", "N/A"),
            "posts_7d": reddit.get("posts_7d", "N/A"),
            "comments_7d": reddit.get("comments_7d", "N/A"),
            "positive_count": positive_count,
            "positive_percent": positive_pct,
            "neutral_count": neutral_count,
            "neutral_percent": neutral_pct,
            "negative_count": negative_count,
            "negative_percent": negative_pct,
            "sample_posts": formatted_posts,
        }

    def _extract_news_data(self, aggregated_data: Dict) -> Dict:
        """
        提取新闻数据

        Args:
            aggregated_data: 聚合数据

        Returns:
            Dict: 新闻数据
        """
        social_data = aggregated_data.get("social_data", {})
        news = social_data.get("news", {})

        # 计算情绪占比
        sentiment_dist = news.get("sentiment_distribution", {})
        total_news = news.get("count_7d", 0) or 1

        positive_count = sentiment_dist.get("positive", 0)
        neutral_count = sentiment_dist.get("neutral", 0)
        negative_count = sentiment_dist.get("negative", 0)

        if positive_count == 0 and neutral_count == 0 and negative_count == 0:
            positive_pct = sentiment_dist.get("positive_percent", 40)
            neutral_pct = sentiment_dist.get("neutral_percent", 50)
            negative_pct = sentiment_dist.get("negative_percent", 10)
            positive_count = int(total_news * positive_pct / 100)
            neutral_count = int(total_news * neutral_pct / 100)
            negative_count = int(total_news * negative_pct / 100)
        else:
            total = positive_count + neutral_count + negative_count or 1
            positive_pct = round(positive_count / total * 100, 1)
            neutral_pct = round(neutral_count / total * 100, 1)
            negative_pct = round(negative_count / total * 100, 1)

        # 格式化示例标题
        sample_headlines = news.get("sample_headlines", [])
        formatted_headlines = self._format_sample_content(sample_headlines, "新闻")

        return {
            "count_7d": news.get("count_7d", "N/A"),
            "mainstream_media_coverage": news.get("mainstream_coverage", "N/A"),
            "positive_count": positive_count,
            "positive_percent": positive_pct,
            "neutral_count": neutral_count,
            "neutral_percent": neutral_pct,
            "negative_count": negative_count,
            "negative_percent": negative_pct,
            "sample_headlines": formatted_headlines,
        }

    def _analyze_twitter_sentiment(self, twitter_data: Dict, symbol: str) -> Dict:
        """
        深入分析Twitter情绪数据

        Args:
            twitter_data: Twitter原始数据
            symbol: 代币符号

        Returns:
            Dict: Twitter情绪分析结果
        """
        # 基础情绪统计
        positive_count = twitter_data.get("positive_count", 0)
        neutral_count = twitter_data.get("neutral_count", 0)
        negative_count = twitter_data.get("negative_count", 0)
        total_tweets = positive_count + neutral_count + negative_count

        if total_tweets == 0:
            return {
                "sentiment_score": 50,
                "sentiment_label": "中性",
                "engagement_level": "低",
                "influencer_mentions": 0,
                "trend_direction": "稳定",
                "key_topics": [],
                "risk_signals": [],
                "assessment": "Twitter数据不足"
            }

        # 计算情绪得分 (0-100, 100为最积极)
        positive_ratio = positive_count / total_tweets
        negative_ratio = negative_count / total_tweets
        sentiment_score = 50 + (positive_ratio - negative_ratio) * 50

        # 确定情绪标签
        if sentiment_score >= 70:
            sentiment_label = "积极"
        elif sentiment_score <= 30:
            sentiment_label = "消极"
        else:
            sentiment_label = "中性"

        # 分析参与度
        tweet_count_24h = twitter_data.get("count_24h", 0)
        if tweet_count_24h > 1000:
            engagement_level = "高"
        elif tweet_count_24h > 100:
            engagement_level = "中等"
        else:
            engagement_level = "低"

        # 趋势分析（简化版）
        trend_direction = "稳定"  # 可以基于历史数据计算

        # 风险信号检测
        risk_signals = []
        if negative_ratio > 0.3:
            risk_signals.append("负面情绪过高")
        if tweet_count_24h < 10:
            risk_signals.append("讨论热度不足")

        return {
            "sentiment_score": round(sentiment_score, 1),
            "sentiment_label": sentiment_label,
            "engagement_level": engagement_level,
            "total_tweets": total_tweets,
            "trend_direction": trend_direction,
            "key_topics": twitter_data.get("top_hashtags", [])[:5],
            "risk_signals": risk_signals,
            "assessment": f"Twitter情绪{sentiment_label}，参与度{engagement_level}",
        }

    def _analyze_reddit_sentiment(self, reddit_data: Dict, symbol: str) -> Dict:
        """
        深入分析Reddit情绪数据

        Args:
            reddit_data: Reddit原始数据
            symbol: 代币符号

        Returns:
            Dict: Reddit情绪分析结果
        """
        # 基础情绪统计
        positive_count = reddit_data.get("positive_count", 0)
        neutral_count = reddit_data.get("neutral_count", 0)
        negative_count = reddit_data.get("negative_count", 0)
        total_posts = positive_count + neutral_count + negative_count

        if total_posts == 0:
            return {
                "sentiment_score": 50,
                "sentiment_label": "中性",
                "community_size": "小",
                "discussion_quality": "一般",
                "trend_direction": "稳定",
                "subreddits": [],
                "risk_signals": [],
                "assessment": "Reddit数据不足"
            }

        # 计算情绪得分
        positive_ratio = positive_count / total_posts
        negative_ratio = negative_count / total_posts
        sentiment_score = 50 + (positive_ratio - negative_ratio) * 50

        # 确定情绪标签
        if sentiment_score >= 70:
            sentiment_label = "积极"
        elif sentiment_score <= 30:
            sentiment_label = "消极"
        else:
            sentiment_label = "中性"

        # 社区规模分析
        subscribers = reddit_data.get("total_subscribers", 0)
        if subscribers > 100000:
            community_size = "大"
        elif subscribers > 10000:
            community_size = "中等"
        else:
            community_size = "小"

        # 讨论质量分析（基于帖子数量和参与度）
        posts_24h = reddit_data.get("posts_24h", 0)
        comments_avg = reddit_data.get("avg_comments_per_post", 0)

        if posts_24h > 50 and comments_avg > 10:
            discussion_quality = "高"
        elif posts_24h > 10 and comments_avg > 3:
            discussion_quality = "中等"
        else:
            discussion_quality = "低"

        # 风险信号检测
        risk_signals = []
        if negative_ratio > 0.4:
            risk_signals.append("社区情绪过于负面")
        if posts_24h < 5:
            risk_signals.append("社区活跃度不足")

        return {
            "sentiment_score": round(sentiment_score, 1),
            "sentiment_label": sentiment_label,
            "community_size": community_size,
            "discussion_quality": discussion_quality,
            "total_posts": total_posts,
            "trend_direction": "稳定",
            "subreddits": reddit_data.get("active_subreddits", [])[:3],
            "risk_signals": risk_signals,
            "assessment": f"Reddit情绪{sentiment_label}，社区{community_size}，讨论质量{discussion_quality}",
        }

    def _analyze_news_sentiment(self, news_data: Dict, symbol: str) -> Dict:
        """
        深入分析新闻情绪数据

        Args:
            news_data: 新闻原始数据
            symbol: 代币符号

        Returns:
            Dict: 新闻情绪分析结果
        """
        positive_count = news_data.get("positive_count", 0)
        neutral_count = news_data.get("neutral_count", 0)
        negative_count = news_data.get("negative_count", 0)
        total_news = positive_count + neutral_count + negative_count

        if total_news == 0:
            return {
                "sentiment_score": 50,
                "sentiment_label": "中性",
                "media_coverage": "低",
                "credibility_weight": "中",
                "trend_direction": "稳定",
                "key_publications": [],
                "risk_signals": [],
                "assessment": "新闻数据不足"
            }

        # 计算情绪得分
        positive_ratio = positive_count / total_news
        negative_ratio = negative_count / total_news
        sentiment_score = 50 + (positive_ratio - negative_ratio) * 50

        # 确定情绪标签
        if sentiment_score >= 70:
            sentiment_label = "积极"
        elif sentiment_score <= 30:
            sentiment_label = "消极"
        else:
            sentiment_label = "中性"

        # 媒体覆盖度分析
        news_count_7d = news_data.get("count_7d", 0)
        if news_count_7d > 20:
            media_coverage = "高"
        elif news_count_7d > 5:
            media_coverage = "中等"
        else:
            media_coverage = "低"

        # 可信度权重分析
        mainstream_coverage = news_data.get("mainstream_media_coverage", "低")
        if mainstream_coverage == "高":
            credibility_weight = "高"
        elif mainstream_coverage == "中等":
            credibility_weight = "中"
        else:
            credibility_weight = "低"

        # 风险信号检测
        risk_signals = []
        if negative_ratio > 0.5:
            risk_signals.append("负面新闻过多")
        if news_count_7d == 0:
            risk_signals.append("缺乏媒体关注")

        return {
            "sentiment_score": round(sentiment_score, 1),
            "sentiment_label": sentiment_label,
            "media_coverage": media_coverage,
            "credibility_weight": credibility_weight,
            "total_news": total_news,
            "trend_direction": "稳定",
            "key_publications": news_data.get("top_sources", [])[:3],
            "risk_signals": risk_signals,
            "assessment": f"新闻情绪{sentiment_label}，媒体覆盖度{media_coverage}，可信度{credibility_weight}",
        }

    def _calculate_comprehensive_sentiment(
        self,
        twitter_analysis: Dict,
        reddit_analysis: Dict,
        news_analysis: Dict,
        market_data: Dict
    ) -> Dict:
        """
        计算综合情绪评分

        Args:
            twitter_analysis: Twitter分析结果
            reddit_analysis: Reddit分析结果
            news_analysis: 新闻分析结果
            market_data: 市场数据

        Returns:
            Dict: 综合情绪评分
        """
        # 为不同数据源设置权重
        weights = {
            "twitter": 0.3,  # Twitter较实时，但噪声大
            "reddit": 0.4,   # Reddit社区深入，但偏技术用户
            "news": 0.3,     # 新闻权威，但更新慢
        }

        # 获取各数据源情绪得分
        twitter_score = twitter_analysis.get("sentiment_score", 50)
        reddit_score = reddit_analysis.get("sentiment_score", 50)
        news_score = news_analysis.get("sentiment_score", 50)

        # 计算加权综合得分
        comprehensive_score = (
            twitter_score * weights["twitter"] +
            reddit_score * weights["reddit"] +
            news_score * weights["news"]
        )

        # 确定综合情绪标签
        if comprehensive_score >= 70:
            overall_sentiment = "积极"
            confidence = min(90, comprehensive_score)
        elif comprehensive_score <= 30:
            overall_sentiment = "消极"
            confidence = min(90, 100 - comprehensive_score)
        else:
            overall_sentiment = "中性"
            confidence = 60

        # 收集所有风险信号
        all_risk_signals = []
        all_risk_signals.extend(twitter_analysis.get("risk_signals", []))
        all_risk_signals.extend(reddit_analysis.get("risk_signals", []))
        all_risk_signals.extend(news_analysis.get("risk_signals", []))

        # 确定风险等级
        if len(all_risk_signals) >= 3:
            risk_level = "高"
        elif len(all_risk_signals) >= 1:
            risk_level = "中"
        else:
            risk_level = "低"

        # 与市场表现的相关性分析
        price_change_24h = market_data.get("price_change_percentage_24h", 0)
        sentiment_market_alignment = "未知"

        if abs(price_change_24h) > 1:  # 价格有显著变化
            if (comprehensive_score > 50 and price_change_24h > 0) or (comprehensive_score < 50 and price_change_24h < 0):
                sentiment_market_alignment = "一致"
            else:
                sentiment_market_alignment = "背离"

        return {
            "comprehensive_score": round(comprehensive_score, 1),
            "overall_sentiment": overall_sentiment,
            "confidence": round(confidence, 1),
            "data_sources": {
                "twitter": twitter_analysis,
                "reddit": reddit_analysis,
                "news": news_analysis,
            },
            "weights": weights,
            "risk_signals": list(set(all_risk_signals)),  # 去重
            "risk_level": risk_level,
            "sentiment_market_alignment": sentiment_market_alignment,
            "assessment": f"综合情绪{overall_sentiment}（{comprehensive_score:.1f}分），可信度{confidence:.1f}%，风险等级{risk_level}",
        }

    def _format_sample_content(self, samples: List, content_type: str) -> str:
        """
        格式化示例内容（推文/帖子/新闻）

        Args:
            samples: 示例列表
            content_type: 内容类型（推文/帖子/新闻）

        Returns:
            str: 格式化后的文本
        """
        if not samples or samples == "N/A":
            return f"暂无{content_type}示例"

        if isinstance(samples, list):
            formatted = []
            for i, item in enumerate(samples[:5], 1):  # 最多5个示例
                if isinstance(item, dict):
                    text = item.get("text", item.get("title", ""))
                    engagement = item.get("engagement", item.get("score", ""))
                    if engagement:
                        formatted.append(f"{i}. {text} (互动:{engagement})")
                    else:
                        formatted.append(f"{i}. {text}")
                else:
                    formatted.append(f"{i}. {item}")
            return "\n".join(formatted)

        return str(samples)

    def _format_prompt(
        self,
        symbol: str,
        project_name: str,
        current_price: Any,
        price_change_24h: Any,
        twitter_data: Dict,
        reddit_data: Dict,
        news_data: Dict,
        twitter_analysis: Dict,
        reddit_analysis: Dict,
        news_analysis: Dict,
        comprehensive_sentiment: Dict,
    ) -> str:
        """格式化用户提示词"""
        # 替换模板占位符
        prompt = self.user_prompt_template.format(
            symbol=symbol,
            project_name=project_name,
            current_price=current_price,
            price_change_24h=price_change_24h,
            # Twitter数据
            twitter_followers=twitter_data.get("followers", "N/A"),
            twitter_mentions_7d=twitter_data.get("mentions_7d", "N/A"),
            twitter_engagement_7d=twitter_data.get("engagement_7d", "N/A"),
            twitter_positive_count=twitter_data.get("positive_count", 0),
            twitter_positive_percent=twitter_data.get("positive_percent", 0),
            twitter_neutral_count=twitter_data.get("neutral_count", 0),
            twitter_neutral_percent=twitter_data.get("neutral_percent", 0),
            twitter_negative_count=twitter_data.get("negative_count", 0),
            twitter_negative_percent=twitter_data.get("negative_percent", 0),
            twitter_sample_tweets=twitter_data.get("sample_tweets", "暂无推文示例"),
            # Reddit数据
            reddit_subscribers=reddit_data.get("subscribers", "N/A"),
            reddit_posts_7d=reddit_data.get("posts_7d", "N/A"),
            reddit_comments_7d=reddit_data.get("comments_7d", "N/A"),
            reddit_positive_count=reddit_data.get("positive_count", 0),
            reddit_positive_percent=reddit_data.get("positive_percent", 0),
            reddit_neutral_count=reddit_data.get("neutral_count", 0),
            reddit_neutral_percent=reddit_data.get("neutral_percent", 0),
            reddit_negative_count=reddit_data.get("negative_count", 0),
            reddit_negative_percent=reddit_data.get("negative_percent", 0),
            reddit_sample_posts=reddit_data.get("sample_posts", "暂无帖子示例"),
            # 新闻数据
            news_count_7d=news_data.get("count_7d", "N/A"),
            mainstream_media_coverage=news_data.get("mainstream_media_coverage", "N/A"),
            news_positive_count=news_data.get("positive_count", 0),
            news_positive_percent=news_data.get("positive_percent", 0),
            news_neutral_count=news_data.get("neutral_count", 0),
            news_neutral_percent=news_data.get("neutral_percent", 0),
            news_negative_count=news_data.get("negative_count", 0),
            news_negative_percent=news_data.get("negative_percent", 0),
            news_sample_headlines=news_data.get("sample_headlines", "暂无新闻标题"),
            # Twitter增强分析
            twitter_sentiment_score=twitter_analysis.get("sentiment_score", 50),
            twitter_sentiment_label=twitter_analysis.get("sentiment_label", "中性"),
            twitter_engagement_level=twitter_analysis.get("engagement_level", "低"),
            twitter_risk_signals=", ".join(twitter_analysis.get("risk_signals", [])) or "无风险信号",
            # Reddit增强分析
            reddit_sentiment_score=reddit_analysis.get("sentiment_score", 50),
            reddit_sentiment_label=reddit_analysis.get("sentiment_label", "中性"),
            reddit_community_size=reddit_analysis.get("community_size", "小"),
            reddit_discussion_quality=reddit_analysis.get("discussion_quality", "一般"),
            reddit_risk_signals=", ".join(reddit_analysis.get("risk_signals", [])) or "无风险信号",
            # 新闻增强分析
            news_sentiment_score=news_analysis.get("sentiment_score", 50),
            news_sentiment_label=news_analysis.get("sentiment_label", "中性"),
            news_media_coverage=news_analysis.get("media_coverage", "低"),
            news_credibility_weight=news_analysis.get("credibility_weight", "中"),
            news_risk_signals=", ".join(news_analysis.get("risk_signals", [])) or "无风险信号",
            # 综合情绪评分
            comprehensive_score=comprehensive_sentiment.get("comprehensive_score", 50),
            overall_sentiment=comprehensive_sentiment.get("overall_sentiment", "中性"),
            sentiment_confidence=comprehensive_sentiment.get("confidence", 60),
            sentiment_risk_level=comprehensive_sentiment.get("risk_level", "低"),
            all_risk_signals=", ".join(comprehensive_sentiment.get("risk_signals", [])) or "无风险信号",
            sentiment_market_alignment=comprehensive_sentiment.get("sentiment_market_alignment", "未知"),
        )

        return prompt

    async def _call_llm(self, user_prompt: str, use_fallback: bool = False) -> Dict[str, Any]:
        """
        调用LLM生成情绪分析

        Args:
            user_prompt: 用户提示词
            use_fallback: 是否使用fallback模型

        Returns:
            Dict: 解析后的JSON响应
        """
        model = (
            self.model_config.get("fallback_model", ModelConfig.QUICK_CHAT)
            if use_fallback
            else self.model_config.get("primary_model", ModelConfig.QUICK_CHAT)
        )

        temperature = self.model_config.get("temperature", 0.4)
        max_tokens = self.model_config.get("max_tokens", 2000)

        # 调用LLM
        response = await self.llm_client.chat_completion(
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        content = response.get("content", "")

        # 尝试解析JSON
        try:
            # 移除可能的markdown代码块标记
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            result = json.loads(content)
            return result
        except json.JSONDecodeError as e:
            print(f"❌ JSON解析失败: {e}\n原始内容:\n{content}")
            raise ValueError(f"LLM返回了无效的JSON: {str(e)}")

    def _validate_output(self, result: Dict[str, Any]) -> bool:
        """
        验证输出格式

        Args:
            result: LLM生成的结果

        Returns:
            bool: 是否符合格式要求
        """
        required_fields = self.output_validation.get("required_fields", [])

        # 检查必填字段
        for field in required_fields:
            if field not in result:
                print(f"❌ 缺少必填字段: {field}")
                return False

        # 验证overall_sentiment结构
        if "overall_sentiment" in result:
            overall = result["overall_sentiment"]
            overall_required = self.output_validation.get("overall_sentiment_structure", {}).get("required_fields", [])
            for field in overall_required:
                if field not in overall:
                    print(f"❌ overall_sentiment缺少字段: {field}")
                    return False

            # 验证label值
            label = overall.get("label", "")
            valid_labels = self.output_validation.get("overall_sentiment_structure", {}).get("label_values", [])
            if label not in valid_labels:
                print(f"⚠️ overall_sentiment.label值无效: {label}")

            # 验证score和confidence范围
            score = overall.get("score", -1)
            confidence = overall.get("confidence", -1)
            score_range = self.output_validation.get("overall_sentiment_structure", {}).get("score_range", {})
            conf_range = self.output_validation.get("overall_sentiment_structure", {}).get("confidence_range", {})

            if not (score_range.get("min", 0) <= score <= score_range.get("max", 100)):
                print(f"❌ overall_sentiment.score超出范围: {score}")
                return False

            if not (conf_range.get("min", 0) <= confidence <= conf_range.get("max", 100)):
                print(f"❌ overall_sentiment.confidence超出范围: {confidence}")
                return False

        # 验证sentiment_breakdown
        if "sentiment_breakdown" in result:
            breakdown = result["sentiment_breakdown"]
            pos = breakdown.get("positive_percent", 0)
            neu = breakdown.get("neutral_percent", 0)
            neg = breakdown.get("negative_percent", 0)
            total = pos + neu + neg

            # 三个百分比相加应约等于100（允许±2的误差）
            if not (98 <= total <= 102):
                print(f"⚠️ sentiment_breakdown百分比之和不等于100: {total}")

        # 验证top_topics数量
        if "top_topics" in result:
            topics = result["top_topics"]
            min_count = self.output_validation.get("top_topics", {}).get("min_count", 3)
            max_count = self.output_validation.get("top_topics", {}).get("max_count", 5)
            if not (min_count <= len(topics) <= max_count):
                print(f"⚠️ top_topics数量不符合要求: {len(topics)}")

        # 验证key_influencers数量
        if "key_influencers" in result:
            influencers = result["key_influencers"]
            min_count = self.output_validation.get("key_influencers", {}).get("min_count", 2)
            max_count = self.output_validation.get("key_influencers", {}).get("max_count", 5)
            if not (min_count <= len(influencers) <= max_count):
                print(f"⚠️ key_influencers数量不符合要求: {len(influencers)}")

        return True

    def _fix_invalid_output(self, result: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """
        修复无效输出（补全缺失字段）

        Args:
            result: 原始结果
            symbol: 币种符号

        Returns:
            Dict: 修复后的结果
        """
        from datetime import datetime, timezone

        # 修复overall_sentiment
        if "overall_sentiment" not in result:
            result["overall_sentiment"] = {}

        overall = result["overall_sentiment"]
        overall.setdefault("label", "中性")
        overall.setdefault("score", 50)
        overall.setdefault("confidence", 50)
        overall.setdefault("summary", f"{symbol}的社交媒体情绪数据不完整，暂时无法给出详细分析。")

        # 修复sentiment_breakdown
        if "sentiment_breakdown" not in result:
            result["sentiment_breakdown"] = {}

        breakdown = result["sentiment_breakdown"]
        breakdown.setdefault("positive_percent", 33)
        breakdown.setdefault("neutral_percent", 34)
        breakdown.setdefault("negative_percent", 33)
        breakdown.setdefault("trend", "情绪稳定")

        # 修复top_topics
        if "top_topics" not in result or len(result["top_topics"]) < 3:
            result["top_topics"] = [
                {
                    "topic": "数据不足",
                    "mentions": 0,
                    "sentiment": "中性",
                    "keywords": [],
                    "impact": "低",
                }
            ] * 3

        # 修复key_influencers
        if "key_influencers" not in result or len(result["key_influencers"]) < 2:
            result["key_influencers"] = [
                {
                    "name": "数据不足",
                    "platform": "Twitter",
                    "followers": 0,
                    "recent_stance": "中性",
                    "key_message": "暂无数据",
                    "credibility": "低",
                }
            ] * 2

        # 修复community_health
        if "community_health" not in result:
            result["community_health"] = {
                "activity_level": "低",
                "growth_trend": "数据不足",
                "engagement_quality": "一般",
                "fud_level": "无明显FUD",
                "fomo_level": "无",
                "concerns": ["数据不完整"],
            }

        # 修复narrative_analysis
        if "narrative_analysis" not in result:
            result["narrative_analysis"] = {
                "dominant_narrative": "数据不足",
                "narrative_strength": "弱",
                "competing_narratives": [],
                "narrative_shift": "无法判断",
            }

        # 补全新增强分析字段
        if "twitter_analysis" not in result:
            result["twitter_analysis"] = {
                "sentiment_score": 50,
                "sentiment_label": "中性",
                "engagement_level": "低",
                "total_tweets": 0,
                "trend_direction": "稳定",
                "key_topics": [],
                "risk_signals": [],
                "assessment": "Twitter数据不足"
            }

        if "reddit_analysis" not in result:
            result["reddit_analysis"] = {
                "sentiment_score": 50,
                "sentiment_label": "中性",
                "community_size": "小",
                "discussion_quality": "一般",
                "total_posts": 0,
                "trend_direction": "稳定",
                "subreddits": [],
                "risk_signals": [],
                "assessment": "Reddit数据不足"
            }

        if "news_analysis" not in result:
            result["news_analysis"] = {
                "sentiment_score": 50,
                "sentiment_label": "中性",
                "media_coverage": "低",
                "credibility_weight": "中",
                "total_news": 0,
                "trend_direction": "稳定",
                "key_publications": [],
                "risk_signals": [],
                "assessment": "新闻数据不足"
            }

        if "comprehensive_sentiment" not in result:
            result["comprehensive_sentiment"] = {
                "comprehensive_score": 50,
                "overall_sentiment": "中性",
                "confidence": 60,
                "data_sources": {
                    "twitter": result.get("twitter_analysis", {}),
                    "reddit": result.get("reddit_analysis", {}),
                    "news": result.get("news_analysis", {}),
                },
                "weights": {"twitter": 0.3, "reddit": 0.4, "news": 0.3},
                "risk_signals": [],
                "risk_level": "低",
                "sentiment_market_alignment": "未知",
                "assessment": "综合情绪数据不足"
            }

        # 补全其他字段
        result.setdefault("risk_signals", [])
        result.setdefault("data_sources", [])
        result.setdefault("updated_at", datetime.now(timezone.utc).isoformat())

        return result

    def _create_error_response(self, symbol: str, error_msg: str, model_used: str) -> AnalyzerOutput:
        """
        创建错误响应

        Args:
            symbol: 币种符号
            error_msg: 错误信息
            model_used: 尝试使用的模型

        Returns:
            AnalyzerOutput: 错误响应
        """
        return create_error_output(
            analyzer_name="SentimentAnalyzer",
            error_msg=f"{symbol}的社交媒体情绪分析失败: {error_msg}",
            model_used=model_used,
        )


# 全局单例
sentiment_analyzer = SentimentAnalyzer()
