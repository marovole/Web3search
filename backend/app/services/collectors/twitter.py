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
        advanced_keywords: bool = True,
    ) -> Dict[str, Any]:
        """
        获取加密货币的Twitter情感数据

        Args:
            symbol: 币种符号（如"BTC"）
            hours: 时间范围（小时）
            advanced_keywords: 是否使用高级情感关键词

        Returns:
            Dict: 情感统计数据
        """
        # 构建高级搜索查询
        base_query = f"({symbol} OR #{symbol} OR ${symbol}) -is:retweet lang:en"
        
        # 添加情感关键词过滤
        if advanced_keywords:
            sentiment_keywords = self._get_sentiment_keywords()
            # 添加更复杂的查询逻辑，包含情感相关词汇
            positive_terms = " OR ".join(sentiment_keywords["positive"])
            negative_terms = " OR ".join(sentiment_keywords["negative"])
            query = f"{base_query} ({positive_terms} OR {negative_terms})"
        else:
            query = base_query

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

        # 增强的情感分析
        sentiment_data = self._analyze_tweet_sentiment(tweets, advanced_keywords)

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
            **sentiment_data,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _get_sentiment_keywords(self) -> Dict[str, List[str]]:
        """
        获取加密货币相关的情感关键词
        
        Returns:
            Dict: 包含正面、负面、中性关键词的字典
        """
        return {
            "positive": [
                # 通用正面词汇
                "bullish", "moon", "pump", "buy", "long", "up", "win", "gain", "profit",
                "rocket", "diamond", "hands", "hodl", "strong", "bull", "rally", "surge",
                "soar", "skyrocket", "breakout", "bullrun", "ath", "all time high",
                # Web3特定正面词汇
                "adoption", "mainnet", "launch", "partnership", "integration", "upgrade",
                "airdrop", "staking", "yield", "farming", "defi", "nft", "metaverse",
                "web3", "blockchain", "innovation", "revolution", "future", "scalable"
            ],
            "negative": [
                # 通用负面词汇
                "bearish", "dump", "sell", "short", "down", "loss", "crash", "fall", "drop",
                "decline", "slump", "plunge", "collapse", "bear", "recession", "panic",
                "fear", "uncertainty", "risk", "volatile", "bubble", "scam", "hack",
                # Web3特定负面词汇
                "rugpull", "exploit", "vulnerability", "delist", "ban", "regulation",
                "delay", "postpone", "bug", "glitch", "downtime", "maintenance", "fork"
            ],
            "neutral": [
                # 中性词汇
                "update", "news", "announcement", "report", "analysis", "chart", "price",
                "market", "trading", "volume", "liquidity", "supply", "demand", "cap",
                "circulating", "total", "max", "token", "coin", "crypto", "btc", "eth"
            ]
        }

    def _analyze_tweet_sentiment(
        self, 
        tweets: List[Dict[str, Any]], 
        use_advanced_keywords: bool = True
    ) -> Dict[str, Any]:
        """
        分析推文集合的情感
        
        Args:
            tweets: 推文列表
            use_advanced_keywords: 是否使用高级关键词分析
            
        Returns:
            Dict: 情感分析结果
        """
        if not tweets:
            return {
                "sentiment_score": 0,
                "positive_mentions": 0,
                "negative_mentions": 0,
                "neutral_mentions": 0,
                "sentiment_distribution": {"positive": 0, "negative": 0, "neutral": 0}
            }

        keywords = self._get_sentiment_keywords() if use_advanced_keywords else {
            "positive": ["bullish", "moon", "pump", "buy", "long", "up", "win", "gain"],
            "negative": ["bearish", "dump", "sell", "short", "down", "loss", "crash"],
            "neutral": []
        }

        positive_count = 0
        negative_count = 0
        neutral_count = 0
        sentiment_scores = []

        for tweet in tweets:
            text_lower = tweet["text"].lower()
            
            # 计算每条推文的情感得分
            pos_score = sum(1 for kw in keywords["positive"] if kw in text_lower)
            neg_score = sum(1 for kw in keywords["negative"] if kw in text_lower)
            
            # 根据情感词数量分类
            if pos_score > neg_score:
                positive_count += 1
                # 计算归一化情感得分 (-1 到 1)
                score = (pos_score - neg_score) / max(pos_score + neg_score, 1)
            elif neg_score > pos_score:
                negative_count += 1
                score = -(neg_score - pos_score) / max(pos_score + neg_score, 1)
            else:
                neutral_count += 1
                score = 0
            
            sentiment_scores.append(score)

        # 计算整体情感得分
        total_mentions = len(tweets)
        if sentiment_scores:
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
        else:
            avg_sentiment = 0

        # 考虑参与度加权的情感得分
        weighted_sentiment = self._calculate_weighted_sentiment(tweets, sentiment_scores)

        return {
            "sentiment_score": round(avg_sentiment, 3),
            "weighted_sentiment_score": round(weighted_sentiment, 3),
            "positive_mentions": positive_count,
            "negative_mentions": negative_count,
            "neutral_mentions": neutral_count,
            "sentiment_distribution": {
                "positive": round(positive_count / total_mentions * 100, 1),
                "negative": round(negative_count / total_mentions * 100, 1),
                "neutral": round(neutral_count / total_mentions * 100, 1)
            }
        }

    def _calculate_weighted_sentiment(
        self, 
        tweets: List[Dict[str, Any]], 
        sentiment_scores: List[float]
    ) -> float:
        """
        基于参与度计算加权情感得分
        
        Args:
            tweets: 推文列表
            sentiment_scores: 对应的情感得分列表
            
        Returns:
            float: 加权情感得分
        """
        if not tweets or not sentiment_scores:
            return 0.0

        total_weight = 0
        weighted_sum = 0

        for i, tweet in enumerate(tweets):
            # 计算权重：基于点赞、转发、评论数
            engagement = (
                tweet.get("like_count", 0) + 
                tweet.get("retweet_count", 0) + 
                tweet.get("reply_count", 0)
            )
            
            # 考虑作者影响力的权重
            author_followers = tweet.get("author", {}).get("followers_count", 0)
            influence_weight = min(author_followers / 10000, 1.0)  # 归一化到0-1
            
            # 综合权重
            weight = engagement * (1 + influence_weight)
            total_weight += weight
            weighted_sum += sentiment_scores[i] * weight

        if total_weight > 0:
            return weighted_sum / total_weight
        else:
            return 0.0

    async def get_kol_sentiment(
        self,
        symbol: str,
        kol_usernames: List[str] = None,
        hours: int = 24,
    ) -> Dict[str, Any]:
        """
        获取KOL（关键意见领袖）的情绪分析
        
        Args:
            symbol: 币种符号
            kol_usernames: KOL用户名列表，如果为None则使用默认KOL列表
            hours: 时间范围
            
        Returns:
            Dict: KOL情感分析结果
        """
        # 默认Web3领域知名KOL列表
        if kol_usernames is None:
            kol_usernames = [
                "VitalikButerin", "elonmusk", "brian_armstrong", "saylor", 
                "cz_binance", "justinsuntron", "balajis", "aantonop",
                "nic__carter", "twobitidiot", "miles_deutscher", "defi_hedge"
            ]

        kol_sentiments = []
        total_engagement = 0

        for username in kol_usernames:
            # 构建KOL特定查询
            query = f"from:{username} ({symbol} OR #{symbol} OR ${symbol}) -is:retweet lang:en"
            
            tweets = await self.search_recent_tweets(
                query=query,
                max_results=10,
                since_hours=hours,
            )

            if tweets:
                # 分析这个KOL的情感
                sentiment_data = self._analyze_tweet_sentiment(tweets, True)
                kol_engagement = sum(
                    t["like_count"] + t["retweet_count"] + t["reply_count"]
                    for t in tweets
                )
                
                kol_sentiments.append({
                    "username": username,
                    "tweet_count": len(tweets),
                    "sentiment_score": sentiment_data["sentiment_score"],
                    "engagement": kol_engagement,
                    "latest_tweet": tweets[0]["text"] if tweets else None
                })
                
                total_engagement += kol_engagement

        # 计算KOL整体情绪（基于影响力权重）
        if kol_sentiments:
            weighted_sentiment = sum(
                s["sentiment_score"] * s["engagement"] 
                for s in kol_sentiments
            ) / total_engagement if total_engagement > 0 else 0
            
            positive_kols = len([s for s in kol_sentiments if s["sentiment_score"] > 0])
            negative_kols = len([s for s in kol_sentiments if s["sentiment_score"] < 0])
        else:
            weighted_sentiment = 0
            positive_kols = negative_kols = 0

        return {
            "symbol": symbol,
            "kol_count": len(kol_sentiments),
            "total_engagement": total_engagement,
            "weighted_sentiment_score": round(weighted_sentiment, 3),
            "positive_kol_count": positive_kols,
            "negative_kol_count": negative_kols,
            "neutral_kol_count": len(kol_sentiments) - positive_kols - negative_kols,
            "kol_sentiments": kol_sentiments,
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
