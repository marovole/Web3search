"""
Twitter数据采集器
采集推特上的加密货币相关讨论、热度、情感
"""
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import httpx

from app.core.config import settings
from app.core.redis_client import cache_get_json, cache_set


class TwitterCollector:
    """
    Twitter API v2客户端
    提供社交媒体数据采集功能
    """

    def __init__(self):
        """初始化Twitter客户端"""
        self.bearer_token = settings.TWITTER_BEARER_TOKEN
        self.base_url = "https://api.twitter.com/2"
        self.timeout = 30.0

        # 请求头
        self.headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json",
        }

    async def _request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
        cache_ttl: int = 300,
    ) -> Dict[str, Any]:
        """
        发送HTTP请求到Twitter API

        Args:
            endpoint: API端点
            params: 查询参数
            use_cache: 是否使用缓存
            cache_ttl: 缓存时间（秒）

        Returns:
            Dict: API响应数据

        Raises:
            Exception: API请求失败
        """
        url = f"{self.base_url}{endpoint}"

        # 检查缓存
        cache_key = f"twitter:{endpoint}:{str(params)}"
        if use_cache:
            cached = await cache_get_json(cache_key)
            if cached:
                return cached

        # 发送请求（带重试）
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(url, params=params, headers=self.headers)

                    if response.status_code == 429:  # Rate limit
                        wait_time = 2 ** attempt
                        print(f"⚠️ Twitter限流，等待{wait_time}秒...")
                        await asyncio.sleep(wait_time)
                        continue

                    response.raise_for_status()
                    data = response.json()

                    # 缓存结果
                    if use_cache:
                        await cache_set(cache_key, data, cache_ttl)

                    return data

            except httpx.HTTPStatusError as e:
                error_data = e.response.json() if e.response.content else {}
                error_msg = error_data.get("detail") or error_data.get("title")
                raise Exception(f"Twitter API错误: {e.response.status_code} - {error_msg}")

            except Exception as e:
                if attempt < 2:
                    await asyncio.sleep(1)
                    continue
                else:
                    raise Exception(f"Twitter请求失败: {str(e)}")

        raise Exception("Twitter API请求达到最大重试次数")

    # ================================
    # 用户数据采集
    # ================================

    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        根据用户名获取用户信息

        Args:
            username: Twitter用户名（不带@）

        Returns:
            Dict: 用户信息
        """
        try:
            # 移除可能的@符号
            username = username.lstrip("@")

            data = await self._request(
                f"/users/by/username/{username}",
                params={
                    "user.fields": "created_at,description,public_metrics,verified,url"
                },
                cache_ttl=3600,  # 1小时缓存
            )

            user = data.get("data", {})
            if not user:
                return None

            metrics = user.get("public_metrics", {})

            return {
                "id": user.get("id"),
                "username": user.get("username"),
                "name": user.get("name"),
                "description": user.get("description"),
                "verified": user.get("verified", False),
                "followers_count": metrics.get("followers_count", 0),
                "following_count": metrics.get("following_count", 0),
                "tweet_count": metrics.get("tweet_count", 0),
                "created_at": user.get("created_at"),
                "url": user.get("url"),
            }

        except Exception as e:
            print(f"⚠️ 获取Twitter用户失败: {e}")
            return None

    # ================================
    # 推文搜索
    # ================================

    async def search_recent_tweets(
        self,
        query: str,
        max_results: int = 100,
        since_hours: int = 24,
    ) -> List[Dict[str, Any]]:
        """
        搜索最近的推文

        Args:
            query: 搜索关键词
            max_results: 最大结果数（10-100）
            since_hours: 最近多少小时内

        Returns:
            List[Dict]: 推文列表
        """
        try:
            # 计算时间范围
            start_time = (datetime.utcnow() - timedelta(hours=since_hours)).isoformat() + "Z"

            params = {
                "query": query,
                "max_results": min(max_results, 100),
                "start_time": start_time,
                "tweet.fields": "created_at,public_metrics,entities,referenced_tweets,lang",
                "expansions": "author_id",
                "user.fields": "username,verified,public_metrics",
            }

            data = await self._request(
                "/tweets/search/recent",
                params=params,
                cache_ttl=300,  # 5分钟缓存
            )

            tweets = data.get("data", [])
            users = {u["id"]: u for u in data.get("includes", {}).get("users", [])}

            results = []
            for tweet in tweets:
                author_id = tweet.get("author_id")
                author = users.get(author_id, {})
                metrics = tweet.get("public_metrics", {})

                results.append({
                    "id": tweet.get("id"),
                    "text": tweet.get("text"),
                    "created_at": tweet.get("created_at"),
                    "lang": tweet.get("lang"),
                    "like_count": metrics.get("like_count", 0),
                    "retweet_count": metrics.get("retweet_count", 0),
                    "reply_count": metrics.get("reply_count", 0),
                    "quote_count": metrics.get("quote_count", 0),
                    "author": {
                        "username": author.get("username"),
                        "verified": author.get("verified", False),
                        "followers_count": author.get("public_metrics", {}).get("followers_count", 0),
                    },
                })

            return results

        except Exception as e:
            print(f"⚠️ 搜索Twitter推文失败: {e}")
            return []

    # ================================
    # 情感分析和统计
    # ================================

    async def get_crypto_sentiment(
        self,
        symbol: str,
        hours: int = 24,
    ) -> Dict[str, Any]:
        """
        获取加密货币的Twitter情感数据

        Args:
            symbol: 币种符号（如"BTC"）
            hours: 时间范围（小时）

        Returns:
            Dict: 情感统计数据
        """
        # 构建搜索查询（包含多种提及方式）
        query = f"({symbol} OR #{symbol} OR ${symbol}) -is:retweet lang:en"

        tweets = await self.search_recent_tweets(
            query=query,
            max_results=100,
            since_hours=hours,
        )

        if not tweets:
            return {
                "symbol": symbol,
                "mention_count": 0,
                "total_engagement": 0,
                "avg_engagement": 0,
                "top_tweet": None,
                "sentiment_score": 0,
                "timestamp": datetime.utcnow().isoformat(),
            }

        # 计算统计指标
        total_mentions = len(tweets)
        total_engagement = sum(
            t["like_count"] + t["retweet_count"] + t["reply_count"]
            for t in tweets
        )
        avg_engagement = total_engagement / total_mentions if total_mentions > 0 else 0

        # 找出最高参与度的推文
        top_tweet = max(tweets, key=lambda t: t["like_count"] + t["retweet_count"])

        # 简单的情感分析（基于参与度）
        # 真实项目应使用textblob或更复杂的NLP模型
        positive_keywords = ["bullish", "moon", "pump", "buy", "long", "up", "win", "gain"]
        negative_keywords = ["bearish", "dump", "sell", "short", "down", "loss", "crash"]

        positive_count = 0
        negative_count = 0

        for tweet in tweets:
            text_lower = tweet["text"].lower()
            positive_count += sum(1 for kw in positive_keywords if kw in text_lower)
            negative_count += sum(1 for kw in negative_keywords if kw in text_lower)

        # 情感得分: -1.0（极度负面）到 1.0（极度正面）
        total_sentiment = positive_count + negative_count
        if total_sentiment > 0:
            sentiment_score = (positive_count - negative_count) / total_sentiment
        else:
            sentiment_score = 0

        return {
            "symbol": symbol,
            "mention_count": total_mentions,
            "total_engagement": total_engagement,
            "avg_engagement": round(avg_engagement, 2),
            "top_tweet": {
                "text": top_tweet["text"],
                "url": f"https://twitter.com/{top_tweet['author']['username']}/status/{top_tweet['id']}",
                "engagement": (
                    top_tweet["like_count"] +
                    top_tweet["retweet_count"] +
                    top_tweet["reply_count"]
                ),
            },
            "sentiment_score": round(sentiment_score, 2),
            "positive_mentions": positive_count,
            "negative_mentions": negative_count,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def compare_crypto_trends(
        self,
        symbols: List[str],
        hours: int = 24,
    ) -> Dict[str, Any]:
        """
        对比多个币种的Twitter热度

        Args:
            symbols: 币种符号列表
            hours: 时间范围（小时）

        Returns:
            Dict: 对比数据
        """
        # 并行获取所有币种的数据
        tasks = [self.get_crypto_sentiment(symbol, hours) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        comparisons = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"⚠️ 获取 {symbols[i]} 数据失败: {result}")
                continue
            comparisons.append(result)

        # 按提及次数排序
        comparisons.sort(key=lambda x: x["mention_count"], reverse=True)

        return {
            "comparisons": comparisons,
            "timestamp": datetime.utcnow().isoformat(),
        }


# ================================
# 全局实例
# ================================

twitter_collector = TwitterCollector()
