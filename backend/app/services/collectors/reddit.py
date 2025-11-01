"""
Reddit数据采集器
采集Reddit上的加密货币讨论、热度、情感
"""
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import httpx

from app.core.config import settings
from app.core.redis_client import cache_get_json, cache_set


class RedditCollector:
    """
    Reddit API客户端
    提供社区讨论数据采集功能
    """

    def __init__(self):
        """初始化Reddit客户端"""
        self.client_id = settings.REDDIT_CLIENT_ID
        self.client_secret = settings.REDDIT_CLIENT_SECRET
        self.user_agent = settings.REDDIT_USER_AGENT
        self.base_url = "https://oauth.reddit.com"
        self.auth_url = "https://www.reddit.com/api/v1/access_token"
        self.timeout = 30.0

        # OAuth Token（延迟初始化）
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None

    async def _get_access_token(self) -> str:
        """
        获取OAuth访问令牌

        Returns:
            str: 访问令牌
        """
        # 检查现有token是否过期
        if self.access_token and self.token_expires_at:
            if datetime.utcnow() < self.token_expires_at:
                return self.access_token

        # 获取新token
        auth = httpx.BasicAuth(self.client_id, self.client_secret)
        data = {"grant_type": "client_credentials"}
        headers = {"User-Agent": self.user_agent}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.auth_url,
                auth=auth,
                data=data,
                headers=headers,
            )
            response.raise_for_status()
            token_data = response.json()

            self.access_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 3600)
            self.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in - 60)

            return self.access_token

    async def _request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
        cache_ttl: int = 300,
    ) -> Dict[str, Any]:
        """
        发送HTTP请求到Reddit API

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
        cache_key = f"reddit:{endpoint}:{str(params)}"
        if use_cache:
            cached = await cache_get_json(cache_key)
            if cached:
                return cached

        # 获取访问令牌
        token = await self._get_access_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": self.user_agent,
        }

        # 发送请求（带重试）
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(url, params=params, headers=headers)

                    if response.status_code == 429:  # Rate limit
                        wait_time = 2 ** attempt
                        print(f"⚠️ Reddit限流，等待{wait_time}秒...")
                        await asyncio.sleep(wait_time)
                        continue

                    response.raise_for_status()
                    data = response.json()

                    # 缓存结果
                    if use_cache:
                        await cache_set(cache_key, data, cache_ttl)

                    return data

            except httpx.HTTPStatusError as e:
                raise Exception(f"Reddit API错误: {e.response.status_code}")

            except Exception as e:
                if attempt < 2:
                    await asyncio.sleep(1)
                    continue
                else:
                    raise Exception(f"Reddit请求失败: {str(e)}")

        raise Exception("Reddit API请求达到最大重试次数")

    # ================================
    # 子版块数据采集
    # ================================

    async def get_subreddit_info(self, subreddit: str) -> Optional[Dict[str, Any]]:
        """
        获取子版块信息

        Args:
            subreddit: 子版块名称（如"cryptocurrency"）

        Returns:
            Dict: 子版块信息
        """
        try:
            data = await self._request(
                f"/r/{subreddit}/about",
                cache_ttl=3600,  # 1小时缓存
            )

            subreddit_data = data.get("data", {})

            return {
                "name": subreddit_data.get("display_name"),
                "title": subreddit_data.get("title"),
                "description": subreddit_data.get("public_description"),
                "subscribers": subreddit_data.get("subscribers", 0),
                "active_users": subreddit_data.get("active_user_count", 0),
                "created_utc": subreddit_data.get("created_utc"),
            }

        except Exception as e:
            print(f"⚠️ 获取Reddit子版块信息失败: {e}")
            return None

    async def get_subreddit_posts(
        self,
        subreddit: str,
        sort: str = "hot",
        time_filter: str = "day",
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        获取子版块的帖子列表

        Args:
            subreddit: 子版块名称
            sort: 排序方式（hot, new, top, rising）
            time_filter: 时间过滤（hour, day, week, month, year, all）
            limit: 最大结果数

        Returns:
            List[Dict]: 帖子列表
        """
        try:
            params = {"limit": min(limit, 100)}
            if sort == "top":
                params["t"] = time_filter

            data = await self._request(
                f"/r/{subreddit}/{sort}",
                params=params,
                cache_ttl=300,  # 5分钟缓存
            )

            posts = []
            for child in data.get("data", {}).get("children", []):
                post_data = child.get("data", {})

                posts.append({
                    "id": post_data.get("id"),
                    "title": post_data.get("title"),
                    "text": post_data.get("selftext", ""),
                    "author": post_data.get("author"),
                    "score": post_data.get("score", 0),
                    "upvote_ratio": post_data.get("upvote_ratio", 0),
                    "num_comments": post_data.get("num_comments", 0),
                    "created_utc": post_data.get("created_utc"),
                    "url": f"https://reddit.com{post_data.get('permalink')}",
                    "flair": post_data.get("link_flair_text"),
                })

            return posts

        except Exception as e:
            print(f"⚠️ 获取Reddit帖子失败: {e}")
            return []

    # ================================
    # 搜索功能
    # ================================

    async def search_posts(
        self,
        query: str,
        subreddit: Optional[str] = None,
        sort: str = "relevance",
        time_filter: str = "week",
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        搜索帖子

        Args:
            query: 搜索关键词
            subreddit: 限定子版块（可选）
            sort: 排序方式（relevance, hot, top, new, comments）
            time_filter: 时间过滤
            limit: 最大结果数

        Returns:
            List[Dict]: 搜索结果
        """
        try:
            params = {
                "q": query,
                "sort": sort,
                "t": time_filter,
                "limit": min(limit, 100),
                "type": "link",
            }

            # 如果指定了子版块，只在该版块内搜索
            if subreddit:
                endpoint = f"/r/{subreddit}/search"
                params["restrict_sr"] = "true"
            else:
                endpoint = "/search"

            data = await self._request(
                endpoint,
                params=params,
                cache_ttl=300,  # 5分钟缓存
            )

            posts = []
            for child in data.get("data", {}).get("children", []):
                post_data = child.get("data", {})

                posts.append({
                    "id": post_data.get("id"),
                    "subreddit": post_data.get("subreddit"),
                    "title": post_data.get("title"),
                    "text": post_data.get("selftext", ""),
                    "author": post_data.get("author"),
                    "score": post_data.get("score", 0),
                    "upvote_ratio": post_data.get("upvote_ratio", 0),
                    "num_comments": post_data.get("num_comments", 0),
                    "created_utc": post_data.get("created_utc"),
                    "url": f"https://reddit.com{post_data.get('permalink')}",
                })

            return posts

        except Exception as e:
            print(f"⚠️ 搜索Reddit帖子失败: {e}")
            return []

    # ================================
    # 情感分析和统计
    # ================================

    async def get_crypto_sentiment(
        self,
        symbol: str,
        subreddit: str = "cryptocurrency",
        hours: int = 24,
    ) -> Dict[str, Any]:
        """
        获取加密货币的Reddit情感数据

        Args:
            symbol: 币种符号或名称
            subreddit: 子版块名称
            hours: 时间范围（小时）

        Returns:
            Dict: 情感统计数据
        """
        # 搜索相关帖子
        posts = await self.search_posts(
            query=symbol,
            subreddit=subreddit,
            sort="top",
            time_filter="day" if hours <= 24 else "week",
            limit=100,
        )

        # 过滤时间范围
        cutoff_time = datetime.utcnow().timestamp() - (hours * 3600)
        filtered_posts = [
            p for p in posts
            if p.get("created_utc", 0) >= cutoff_time
        ]

        if not filtered_posts:
            return {
                "symbol": symbol,
                "subreddit": subreddit,
                "post_count": 0,
                "total_score": 0,
                "avg_score": 0,
                "total_comments": 0,
                "avg_upvote_ratio": 0,
                "sentiment_score": 0,
                "timestamp": datetime.utcnow().isoformat(),
            }

        # 计算统计指标
        total_score = sum(p["score"] for p in filtered_posts)
        total_comments = sum(p["num_comments"] for p in filtered_posts)
        avg_upvote_ratio = sum(p["upvote_ratio"] for p in filtered_posts) / len(filtered_posts)

        # 增强的情感分析
        sentiment_data = self._analyze_reddit_sentiment(filtered_posts)

        # 找出最热门的帖子
        top_post = max(filtered_posts, key=lambda p: p["score"])

        return {
            "symbol": symbol,
            "subreddit": subreddit,
            "post_count": len(filtered_posts),
            "total_score": total_score,
            "avg_score": round(total_score / len(filtered_posts), 2),
            "total_comments": total_comments,
            "avg_comments": round(total_comments / len(filtered_posts), 2),
            "avg_upvote_ratio": round(avg_upvote_ratio, 2),
            "top_post": {
                "title": top_post["title"],
                "url": top_post["url"],
                "score": top_post["score"],
                "comments": top_post["num_comments"],
            },
            **sentiment_data,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def get_multi_subreddit_sentiment(
        self,
        symbol: str,
        subreddits: List[str] = None,
        hours: int = 24,
    ) -> Dict[str, Any]:
        """
        从多个subreddit并行获取加密货币情感数据

        Args:
            symbol: 币种符号或名称
            subreddits: 子版块列表，如果为None则使用默认列表
            hours: 时间范围（小时）

        Returns:
            Dict: 多subreddit综合情感数据
        """
        # 默认加密货币相关subreddit列表
        if subreddits is None:
            subreddits = [
                "cryptocurrency", "CryptoCurrency", "Bitcoin", "ethereum", 
                "CryptoMarkets", "binance", "CoinBase", "Cardano", "solana",
                "dogecoin", "Crypto", "altcoin", "Defi", "NFT"
            ]

        # 并行获取各个subreddit的数据
        tasks = [
            self.get_crypto_sentiment(symbol, subreddit, hours)
            for subreddit in subreddits
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        subreddit_data = []
        total_posts = 0
        total_score = 0
        total_comments = 0
        all_sentiment_scores = []

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"⚠️ 获取 {subreddits[i]} 数据失败: {result}")
                continue

            if result.get("post_count", 0) > 0:
                subreddit_data.append({
                    "subreddit": result["subreddit"],
                    "post_count": result["post_count"],
                    "avg_score": result["avg_score"],
                    "sentiment_score": result.get("sentiment_score", 0),
                    "total_engagement": result["total_comments"] + result["total_score"]
                })
                
                total_posts += result["post_count"]
                total_score += result["total_score"]
                total_comments += result["total_comments"]
                
                if "sentiment_score" in result:
                    all_sentiment_scores.append(result["sentiment_score"])

        # 计算综合指标
        if total_posts > 0:
            avg_score = total_score / total_posts
            avg_comments = total_comments / total_posts
            weighted_sentiment = sum(
                data["sentiment_score"] * data["total_engagement"] 
                for data in subreddit_data
            ) / sum(data["total_engagement"] for data in subreddit_data)
        else:
            avg_score = 0
            avg_comments = 0
            weighted_sentiment = 0

        # 按活跃度排序subreddit
        subreddit_data.sort(key=lambda x: x["total_engagement"], reverse=True)

        return {
            "symbol": symbol,
            "total_posts": total_posts,
            "total_score": total_score,
            "avg_score": round(avg_score, 2),
            "total_comments": total_comments,
            "avg_comments": round(avg_comments, 2),
            "weighted_sentiment_score": round(weighted_sentiment, 3),
            "active_subreddits": len(subreddit_data),
            "subreddit_details": subreddit_data,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _analyze_reddit_sentiment(self, posts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析Reddit帖子的情感

        Args:
            posts: Reddit帖子列表

        Returns:
            Dict: 情感分析结果
        """
        if not posts:
            return {
                "sentiment_score": 0,
                "positive_posts": 0,
                "negative_posts": 0,
                "neutral_posts": 0,
                "sentiment_distribution": {"positive": 0, "negative": 0, "neutral": 0}
            }

        # Reddit情感关键词
        crypto_keywords = self._get_crypto_sentiment_keywords()
        
        positive_posts = 0
        negative_posts = 0
        neutral_posts = 0
        sentiment_scores = []

        for post in posts:
            title_lower = post["title"].lower()
            text_lower = post.get("text", "").lower()
            combined_text = f"{title_lower} {text_lower}"
            
            # 计算情感得分
            pos_score = sum(1 for kw in crypto_keywords["positive"] if kw in combined_text)
            neg_score = sum(1 for kw in crypto_keywords["negative"] if kw in combined_text)
            
            # 基于upvote ratio和关键词的综合情感分析
            upvote_ratio = post.get("upvote_ratio", 0.5)
            
            if pos_score > neg_score and upvote_ratio > 0.6:
                positive_posts += 1
                score = min(1.0, (pos_score - neg_score) / max(pos_score + neg_score, 1) + (upvote_ratio - 0.5))
            elif neg_score > pos_score and upvote_ratio < 0.4:
                negative_posts += 1
                score = max(-1.0, -(neg_score - pos_score) / max(pos_score + neg_score, 1) - (0.5 - upvote_ratio))
            else:
                neutral_posts += 1
                score = (upvote_ratio - 0.5) * 2  # 基于upvote ratio的情感得分
            
            sentiment_scores.append(score)

        # 计算整体情感得分
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0

        return {
            "sentiment_score": round(avg_sentiment, 3),
            "positive_posts": positive_posts,
            "negative_posts": negative_posts,
            "neutral_posts": neutral_posts,
            "sentiment_distribution": {
                "positive": round(positive_posts / len(posts) * 100, 1),
                "negative": round(negative_posts / len(posts) * 100, 1),
                "neutral": round(neutral_posts / len(posts) * 100, 1)
            }
        }

    def _get_crypto_sentiment_keywords(self) -> Dict[str, List[str]]:
        """
        获取加密货币相关的Reddit情感关键词

        Returns:
            Dict: 包含正面、负面、中性关键词的字典
        """
        return {
            "positive": [
                # 价格相关正面词汇
                "bullish", "moon", "pump", "buy", "long", "up", "gain", "profit", "surge",
                "rally", "breakout", "ath", "all time high", "rocket", "dip", "accumulate",
                # 技术和基本面正面词汇
                "adoption", "mainnet", "launch", "partnership", "upgrade", "scaling", "innovation",
                "defi", "yield", "staking", "airdrop", "burn", "halving", "whale", "bullish",
                # 社区正面词汇
                "hodl", "diamond hands", "to the moon", "lambo", "gm", "wen", "ser"
            ],
            "negative": [
                # 价格相关负面词汇
                "bearish", "dump", "sell", "short", "down", "loss", "crash", "fall", "drop",
                "plunge", "collapse", "bear", "recession", "panic", "fear", "fud", "scam",
                # 技术和基本面负面词汇
                "hack", "exploit", "vulnerability", "delist", "ban", "regulation", "delay",
                "bug", "glitch", "downtime", "maintenance", "fork", "controversy", "sec",
                # 社区负面词汇
                "rugpull", "shitcoin", "pump and dump", "ponzi", "exit scam", "paper hands"
            ],
            "neutral": [
                # 中性分析词汇
                "analysis", "prediction", "forecast", "technical", "fundamental", "market",
                "price", "chart", "volume", "resistance", "support", "trend", "correction",
                "consolidation", "accumulation", "distribution", "volatility", "macd", "rsi"
            ]
        }

    async def get_trending_crypto_topics(
        self,
        subreddit: str = "cryptocurrency",
        limit: int = 20,
        hours: int = 24,
    ) -> List[Dict[str, Any]]:
        """
        获取热门加密货币话题

        Args:
            subreddit: 子版块名称
            limit: 最大结果数
            hours: 时间范围（小时）

        Returns:
            List[Dict]: 热门话题列表
        """
        posts = await self.get_subreddit_posts(
            subreddit=subreddit,
            sort="hot",
            limit=limit,
        )

        # 过滤时间范围
        cutoff_time = datetime.utcnow().timestamp() - (hours * 3600)
        recent_posts = [
            p for p in posts
            if p.get("created_utc", 0) >= cutoff_time
        ]

        # 分析帖子内容，提取加密货币相关话题
        crypto_keywords = self._get_crypto_sentiment_keywords()
        trending_topics = []

        for post in recent_posts:
            title = post["title"].lower()
            text = post.get("text", "").lower()
            combined = f"{title} {text}"
            
            # 计算加密货币关键词匹配度
            crypto_mentions = []
            for keyword_list in crypto_keywords.values():
                for keyword in keyword_list:
                    if keyword in combined:
                        crypto_mentions.append(keyword)
            
            if crypto_mentions:
                trending_topics.append({
                    "title": post["title"],
                    "url": post["url"],
                    "score": post["score"],
                    "comments": post["num_comments"],
                    "crypto_mentions": list(set(crypto_mentions)),
                    "mention_count": len(crypto_mentions),
                    "engagement_score": post["score"] + post["num_comments"]
                })

        # 按参与度排序
        trending_topics.sort(key=lambda x: x["engagement_score"], reverse=True)

        return trending_topics[:limit]

    async def get_trending_topics(
        self,
        subreddit: str = "cryptocurrency",
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        获取热门话题

        Args:
            subreddit: 子版块名称
            limit: 最大结果数

        Returns:
            List[Dict]: 热门话题列表
        """
        posts = await self.get_subreddit_posts(
            subreddit=subreddit,
            sort="hot",
            limit=limit,
        )

        return [
            {
                "title": post["title"],
                "url": post["url"],
                "score": post["score"],
                "comments": post["num_comments"],
                "flair": post.get("flair"),
            }
            for post in posts
        ]


# ================================
# 全局实例
# ================================

reddit_collector = RedditCollector()
