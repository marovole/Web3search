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

        # 简单情感分析（基于upvote ratio）
        # upvote_ratio: 0.5表示中性，>0.5正面，<0.5负面
        sentiment_score = (avg_upvote_ratio - 0.5) * 2  # 映射到[-1, 1]

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
            "sentiment_score": round(sentiment_score, 2),
            "top_post": {
                "title": top_post["title"],
                "url": top_post["url"],
                "score": top_post["score"],
                "comments": top_post["num_comments"],
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

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
