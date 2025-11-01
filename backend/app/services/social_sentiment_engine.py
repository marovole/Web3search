"""
社交情绪分析引擎
整合多平台数据采集和情感分析，提供全面的Web3项目情绪洞察
"""
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
from dataclasses import dataclass

from app.services.collectors.twitter import twitter_collector
from app.services.collectors.reddit import reddit_collector
from app.services.collectors.telegram import telegram_collector
from app.services.collectors.discord import discord_collector
from app.services.sentiment_analyzer import sentiment_analyzer
from app.core.config import settings
from app.core.redis_client import cache_get_json, cache_set


@dataclass
class SentimentMetrics:
    """情感指标数据类"""
    score: float
    confidence: float
    volume: int
    engagement: int
    distribution: Dict[str, float]
    timestamp: datetime


class SocialSentimentEngine:
    """
    社交情绪分析引擎
    整合Twitter、Reddit、Telegram等多平台数据，提供统一的情绪分析服务
    """

    def __init__(self):
        """初始化情绪分析引擎"""
        self.platforms = {
            "twitter": twitter_collector,
            "reddit": reddit_collector,
            "telegram": telegram_collector,
            "discord": discord_collector
        }

        # 平台权重配置
        self.platform_weights = {
            "twitter": 0.35,  # Twitter权重35%
            "reddit": 0.30,  # Reddit权重30%
            "telegram": 0.20,  # Telegram权重20%
            "discord": 0.15   # Discord权重15%
        }
        
        # 热门加密货币列表
        self.popular_cryptos = [
            "BTC", "ETH", "BNB", "SOL", "ADA", "DOT", "AVAX", "MATIC",
            "LINK", "UNI", "ATOM", "NEAR", "FTM", "ALGO", "ONE", "HBAR"
        ]
        
        # KOL影响力权重
        self.kol_weight_factor = 2.0  # KOL影响力权重倍数

    async def get_comprehensive_sentiment(
        self,
        symbol: str,
        hours: int = 24,
        platforms: List[str] = None,
        include_kol: bool = True
    ) -> Dict[str, Any]:
        """
        获取综合情感分析

        Args:
            symbol: 币种符号
            hours: 时间范围（小时）
            platforms: 要分析的平台列表，None表示全部
            include_kol: 是否包含KOL分析

        Returns:
            Dict: 综合情感分析结果
        """
        # 检查缓存
        cache_key = f"comprehensive_sentiment:{symbol}:{hours}:{str(platforms)}:{include_kol}"
        cached = await cache_get_json(cache_key)
        if cached:
            return cached

        if platforms is None:
            platforms = list(self.platforms.keys())

        # 并行获取各平台数据
        platform_tasks = []
        for platform in platforms:
            if platform in self.platforms:
                task = self._get_platform_sentiment(platform, symbol, hours)
                platform_tasks.append(task)

        platform_results = await asyncio.gather(*platform_tasks, return_exceptions=True)

        # 处理平台结果
        valid_results = []
        platform_data = {}
        
        for i, result in enumerate(platform_results):
            platform = platforms[i]
            if isinstance(result, Exception):
                print(f"⚠️ {platform}平台数据获取失败: {result}")
                continue
                
            valid_results.append(result)
            platform_data[platform] = result

        # 获取KOL分析（如果启用）
        kol_data = None
        if include_kol and "twitter" in platforms:
            try:
                kol_data = await self.platforms["twitter"].get_kol_sentiment(symbol, hours=hours)
            except Exception as e:
                print(f"⚠️ KOL分析失败: {e}")

        # 计算综合指标
        comprehensive_result = self._calculate_comprehensive_sentiment(
            platform_data, kol_data, symbol, hours
        )

        # 缓存结果
        await cache_set(cache_key, comprehensive_result, 300)  # 5分钟缓存

        return comprehensive_result

    async def _get_platform_sentiment(
        self,
        platform: str,
        symbol: str,
        hours: int
    ) -> Dict[str, Any]:
        """
        获取特定平台的情感数据

        Args:
            platform: 平台名称
            symbol: 币种符号
            hours: 时间范围

        Returns:
            Dict: 平台情感数据
        """
        collector = self.platforms[platform]
        
        if platform == "twitter":
            return await collector.get_crypto_sentiment(symbol, hours=hours, advanced_keywords=True)
        elif platform == "reddit":
            return await collector.get_multi_subreddit_sentiment(symbol, hours=hours)
        elif platform == "telegram":
            return await collector.get_crypto_sentiment(symbol, hours=hours)
        else:
            raise ValueError(f"不支持的平台: {platform}")

    def _calculate_comprehensive_sentiment(
        self,
        platform_data: Dict[str, Any],
        kol_data: Dict[str, Any] = None,
        symbol: str = "unknown",
        hours: int = 24
    ) -> Dict[str, Any]:
        """
        计算综合情感指标

        Args:
            platform_data: 各平台数据
            kol_data: KOL数据
            symbol: 币种符号
            hours: 时间范围

        Returns:
            Dict: 综合情感结果
        """
        if not platform_data:
            return self._empty_result(symbol, hours)

        # 提取各平台指标
        platform_scores = []
        platform_volumes = []
        platform_engagements = []
        platform_distributions = []

        total_volume = 0
        total_engagement = 0

        for platform, data in platform_data.items():
            # 获取情感得分
            if "sentiment_score" in data:
                score = data["sentiment_score"]
            elif "weighted_sentiment_score" in data:
                score = data["weighted_sentiment_score"]
            else:
                score = 0.0

            # 获取数据量
            if platform == "twitter":
                volume = data.get("mention_count", 0)
                engagement = data.get("total_engagement", 0)
            elif platform == "reddit":
                volume = data.get("total_posts", 0)
                engagement = data.get("total_comments", 0)
            elif platform == "telegram":
                volume = data.get("total_messages", 0)
                engagement = data.get("total_views", 0)
            else:
                volume = engagement = 0

            # 获取情感分布
            distribution = {}
            if "sentiment_distribution" in data:
                distribution = data["sentiment_distribution"]
            elif platform == "twitter" and "positive_mentions" in data:
                total = data["positive_mentions"] + data["negative_mentions"] + data.get("neutral_mentions", 0)
                if total > 0:
                    distribution = {
                        "positive": round(data["positive_mentions"] / total * 100, 1),
                        "negative": round(data["negative_mentions"] / total * 100, 1),
                        "neutral": round(data.get("neutral_mentions", 0) / total * 100, 1)
                    }

            platform_scores.append(score)
            platform_volumes.append(volume)
            platform_engagements.append(engagement)
            platform_distributions.append(distribution)

            total_volume += volume
            total_engagement += engagement

        # 计算加权情感得分
        weighted_sentiment = 0.0
        total_weight = 0.0

        for i, platform in enumerate(platform_data.keys()):
            weight = self.platform_weights.get(platform, 0)
            
            # 根据数据量调整权重
            volume_factor = min(platform_volumes[i] / 100, 1.0)  # 归一化到0-1
            adjusted_weight = weight * (0.5 + 0.5 * volume_factor)  # 基础权重50% + 数据量权重50%
            
            weighted_sentiment += platform_scores[i] * adjusted_weight
            total_weight += adjusted_weight

        if total_weight > 0:
            final_sentiment = weighted_sentiment / total_weight
        else:
            final_sentiment = 0.0

        # 整合KOL影响
        kol_influence = 0.0
        if kol_data and kol_data.get("kol_count", 0) > 0:
            kol_sentiment = kol_data.get("weighted_sentiment_score", 0.0)
            kol_influence = kol_sentiment * 0.2  # KOL影响力占20%
            final_sentiment = final_sentiment * 0.8 + kol_influence

        # 计算综合情感分布
        comprehensive_distribution = self._merge_distributions(platform_distributions)

        # 计算置信度
        confidence = self._calculate_confidence(
            platform_data, total_volume, total_engagement
        )

        # 生成趋势分析
        trend_analysis = self._generate_trend_analysis(final_sentiment, platform_data)

        return {
            "symbol": symbol,
            "time_range_hours": hours,
            "final_sentiment_score": round(final_sentiment, 3),
            "confidence": round(confidence, 3),
            "sentiment_classification": self._classify_sentiment(final_sentiment),
            "total_volume": total_volume,
            "total_engagement": total_engagement,
            "active_platforms": len(platform_data),
            "sentiment_distribution": comprehensive_distribution,
            "platform_breakdown": {
                platform: {
                    "sentiment_score": platform_scores[i],
                    "volume": platform_volumes[i],
                    "engagement": platform_engagements[i],
                    "weight": self.platform_weights.get(platform, 0),
                    "data": data
                }
                for i, (platform, data) in enumerate(platform_data.items())
            },
            "kol_analysis": kol_data,
            "trend_analysis": trend_analysis,
            "insights": self._generate_insights(final_sentiment, platform_data, kol_data),
            "timestamp": datetime.utcnow().isoformat()
        }

    def _merge_distributions(self, distributions: List[Dict[str, float]]) -> Dict[str, float]:
        """
        合并多个情感分布

        Args:
            distributions: 情感分布列表

        Returns:
            Dict: 合并后的情感分布
        """
        if not distributions:
            return {"positive": 0, "negative": 0, "neutral": 0}

        merged = {"positive": 0, "negative": 0, "neutral": 0}
        count = 0

        for dist in distributions:
            if dist:
                for key in merged:
                    merged[key] += dist.get(key, 0)
                count += 1

        if count > 0:
            for key in merged:
                merged[key] = round(merged[key] / count, 1)

        return merged

    def _calculate_confidence(
        self,
        platform_data: Dict[str, Any],
        total_volume: int,
        total_engagement: int
    ) -> float:
        """
        计算分析置信度

        Args:
            platform_data: 平台数据
            total_volume: 总数据量
            total_engagement: 总参与度

        Returns:
            float: 置信度 (0-1)
        """
        # 基础置信度（平台数量）
        platform_confidence = min(len(platform_data) / 3, 1.0)  # 最多3个平台

        # 数据量置信度
        volume_confidence = min(total_volume / 500, 1.0)  # 500条消息为满分

        # 参与度置信度
        engagement_confidence = min(total_engagement / 10000, 1.0)  # 10000参与为满分

        # 综合置信度
        final_confidence = (
            platform_confidence * 0.3 +
            volume_confidence * 0.4 +
            engagement_confidence * 0.3
        )

        return round(final_confidence, 3)

    def _classify_sentiment(self, score: float) -> str:
        """
        分类情感

        Args:
            score: 情感得分

        Returns:
            str: 情感分类
        """
        if score > 0.2:
            return "strong_positive" if score > 0.5 else "positive"
        elif score < -0.2:
            return "strong_negative" if score < -0.5 else "negative"
        else:
            return "neutral"

    def _generate_trend_analysis(
        self,
        current_sentiment: float,
        platform_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成趋势分析

        Args:
            current_sentiment: 当前情感得分
            platform_data: 平台数据

        Returns:
            Dict: 趋势分析
        """
        # 这里简化实现，实际应该与历史数据对比
        trends = {}

        for platform, data in platform_data.items():
            if platform == "twitter":
                # Twitter趋势基于参与度变化
                engagement = data.get("total_engagement", 0)
                trends[platform] = {
                    "volume_trend": "increasing" if engagement > 100 else "stable",
                    "sentiment_trend": "improving" if current_sentiment > 0.1 else "stable"
                }
            elif platform == "reddit":
                # Reddit趋势基于帖子数量和评分
                posts = data.get("total_posts", 0)
                trends[platform] = {
                    "volume_trend": "increasing" if posts > 50 else "stable",
                    "sentiment_trend": "improving" if current_sentiment > 0.1 else "stable"
                }
            elif platform == "telegram":
                # Telegram趋势基于消息数量
                messages = data.get("total_messages", 0)
                trends[platform] = {
                    "volume_trend": "increasing" if messages > 100 else "stable",
                    "sentiment_trend": "improving" if current_sentiment > 0.1 else "stable"
                }

        return trends

    def _generate_insights(
        self,
        sentiment: float,
        platform_data: Dict[str, Any],
        kol_data: Dict[str, Any] = None
    ) -> List[str]:
        """
        生成洞察分析

        Args:
            sentiment: 情感得分
            platform_data: 平台数据
            kol_data: KOL数据

        Returns:
            List[str]: 洞察列表
        """
        insights = []

        # 基础情感洞察
        if sentiment > 0.5:
            insights.append("整体情绪非常积极，市场可能处于上涨趋势")
        elif sentiment > 0.2:
            insights.append("整体情绪偏正面，投资者信心较强")
        elif sentiment < -0.5:
            insights.append("整体情绪非常消极，市场可能面临下跌压力")
        elif sentiment < -0.2:
            insights.append("整体情绪偏负面，投资者较为谨慎")
        else:
            insights.append("整体情绪中性，市场处于观望状态")

        # 平台特色洞察
        if "twitter" in platform_data:
            twitter_data = platform_data["twitter"]
            if twitter_data.get("mention_count", 0) > 100:
                insights.append("Twitter讨论热度很高，市场关注度上升")

        if "reddit" in platform_data:
            reddit_data = platform_data["reddit"]
            if reddit_data.get("total_posts", 0) > 50:
                insights.append("Reddit社区讨论活跃，深度参与度较高")

        if "telegram" in platform_data:
            telegram_data = platform_data["telegram"]
            if telegram_data.get("total_messages", 0) > 200:
                insights.append("Telegram群组讨论激烈，即时信息传播快速")

        # KOL洞察
        if kol_data and kol_data.get("kol_count", 0) > 0:
            kol_sentiment = kol_data.get("weighted_sentiment_score", 0)
            kol_count = kol_data.get("kol_count", 0)
            
            if kol_sentiment > 0.3 and kol_count >= 3:
                insights.append("多位KOL表达积极观点，可能影响市场情绪")
            elif kol_sentiment < -0.3 and kol_count >= 3:
                insights.append("多位KOL表达担忧情绪，需要关注潜在风险")

        return insights

    def _empty_result(self, symbol: str, hours: int) -> Dict[str, Any]:
        """
        返回空结果

        Args:
            symbol: 币种符号
            hours: 时间范围

        Returns:
            Dict: 空结果
        """
        return {
            "symbol": symbol,
            "time_range_hours": hours,
            "final_sentiment_score": 0.0,
            "confidence": 0.0,
            "sentiment_classification": "neutral",
            "total_volume": 0,
            "total_engagement": 0,
            "active_platforms": 0,
            "sentiment_distribution": {"positive": 0, "negative": 0, "neutral": 0},
            "platform_breakdown": {},
            "kol_analysis": None,
            "trend_analysis": {},
            "insights": ["暂无相关社交数据"],
            "timestamp": datetime.utcnow().isoformat()
        }

    async def get_trending_topics(
        self,
        hours: int = 24,
        platforms: List[str] = None
    ) -> Dict[str, Any]:
        """
        获取热门话题

        Args:
            hours: 时间范围
            platforms: 平台列表

        Returns:
            Dict: 热门话题数据
        """
        if platforms is None:
            platforms = ["twitter", "reddit", "telegram"]

        # 检查缓存
        cache_key = f"trending_topics:{hours}:{str(platforms)}"
        cached = await cache_get_json(cache_key)
        if cached:
            return cached

        all_topics = []
        platform_tasks = []

        # Twitter热门话题
        if "twitter" in platforms:
            # 这里简化实现，实际需要Twitter Trends API
            pass

        # Reddit热门话题
        if "reddit" in platforms:
            task = reddit_collector.get_trending_crypto_topics(hours=hours)
            platform_tasks.append(("reddit", task))

        # Telegram热门话题
        if "telegram" in platforms:
            task = telegram_collector.get_trending_crypto_topics(hours=hours)
            platform_tasks.append(("telegram", task))

        # 并行获取数据
        results = await asyncio.gather(*[task for _, task in platform_tasks], return_exceptions=True)

        for i, result in enumerate(results):
            platform = platform_tasks[i][0]
            if isinstance(result, Exception):
                print(f"⚠️ {platform}热门话题获取失败: {result}")
                continue

            for topic in result:
                topic["source_platform"] = platform
                all_topics.append(topic)

        # 按参与度排序
        all_topics.sort(key=lambda x: x.get("engagement_score", 0), reverse=True)

        result = {
            "topics": all_topics[:20],  # 前20个话题
            "total_topics": len(all_topics),
            "platforms": platforms,
            "time_range_hours": hours,
            "timestamp": datetime.utcnow().isoformat()
        }

        # 缓存结果
        await cache_set(cache_key, result, 600)  # 10分钟缓存

        return result

    async def get_sentiment_comparison(
        self,
        symbols: List[str],
        hours: int = 24
    ) -> Dict[str, Any]:
        """
        获取多个币种的情感对比

        Args:
            symbols: 币种符号列表
            hours: 时间范围

        Returns:
            Dict: 情感对比数据
        """
        # 检查缓存
        cache_key = f"sentiment_comparison:{hours}:{','.join(symbols)}"
        cached = await cache_get_json(cache_key)
        if cached:
            return cached

        # 并行获取各币种情感数据
        tasks = [
            self.get_comprehensive_sentiment(symbol, hours)
            for symbol in symbols
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        comparisons = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"⚠️ {symbols[i]} 情感分析失败: {result}")
                continue

            comparisons.append({
                "symbol": result["symbol"],
                "sentiment_score": result["final_sentiment_score"],
                "confidence": result["confidence"],
                "volume": result["total_volume"],
                "engagement": result["total_engagement"],
                "classification": result["sentiment_classification"],
                "platforms": result["active_platforms"]
            })

        # 按情感得分排序
        comparisons.sort(key=lambda x: x["sentiment_score"], reverse=True)

        result = {
            "comparisons": comparisons,
            "time_range_hours": hours,
            "total_symbols": len(comparisons),
            "timestamp": datetime.utcnow().isoformat()
        }

        # 缓存结果
        await cache_set(cache_key, result, 300)  # 5分钟缓存

        return result


# ================================
# 全局实例
# ================================

social_sentiment_engine = SocialSentimentEngine()
