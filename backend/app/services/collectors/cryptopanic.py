"""
CryptoPanic数据采集器
采集加密货币相关新闻、事件、舆情
"""
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import httpx

from app.core.config import settings
from app.core.redis_client import cache_get_json, cache_set


class CryptoPanicCollector:
    """
    CryptoPanic API客户端
    提供加密货币新闻和事件数据采集功能
    """

    def __init__(self):
        """初始化CryptoPanic客户端"""
        self.base_url = settings.CRYPTOPANIC_BASE_URL
        self.api_key = settings.CRYPTOPANIC_API_KEY
        self.timeout = 30.0

    async def _request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
        cache_ttl: int = 300,
    ) -> Dict[str, Any]:
        """
        发送HTTP请求到CryptoPanic API

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

        # 添加API密钥
        if params is None:
            params = {}
        params["auth_token"] = self.api_key

        # 检查缓存
        cache_key = f"cryptopanic:{endpoint}:{str(params)}"
        if use_cache:
            cached = await cache_get_json(cache_key)
            if cached:
                return cached

        # 发送请求（带重试）
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(url, params=params)

                    if response.status_code == 429:  # Rate limit
                        wait_time = 2 ** attempt
                        print(f"⚠️ CryptoPanic限流，等待{wait_time}秒...")
                        await asyncio.sleep(wait_time)
                        continue

                    response.raise_for_status()
                    data = response.json()

                    # 缓存结果
                    if use_cache:
                        await cache_set(cache_key, data, cache_ttl)

                    return data

            except httpx.HTTPStatusError as e:
                raise Exception(f"CryptoPanic API错误: {e.response.status_code}")

            except Exception as e:
                if attempt < 2:
                    await asyncio.sleep(1)
                    continue
                else:
                    raise Exception(f"CryptoPanic请求失败: {str(e)}")

        raise Exception("CryptoPanic API请求达到最大重试次数")

    # ================================
    # 新闻数据采集
    # ================================

    async def get_posts(
        self,
        kind: str = "news",
        filter_: Optional[str] = None,
        currencies: Optional[str] = None,
        regions: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        获取新闻和帖子

        Args:
            kind: 类型（news, media, all）
            filter_: 过滤器（rising, hot, bullish, bearish, important, saved, lol）
            currencies: 币种筛选（如"BTC,ETH"）
            regions: 地区筛选（如"en,cn"）

        Returns:
            List[Dict]: 新闻列表
        """
        params = {"kind": kind}

        if filter_:
            params["filter"] = filter_
        if currencies:
            params["currencies"] = currencies
        if regions:
            params["regions"] = regions

        try:
            data = await self._request(
                "/posts/",
                params=params,
                cache_ttl=300,  # 5分钟缓存
            )

            posts = []
            for item in data.get("results", []):
                # 提取币种信息
                currencies_data = item.get("currencies", [])
                currency_symbols = [c.get("code") for c in currencies_data]

                # 提取投票信息
                votes = item.get("votes", {})

                posts.append({
                    "id": item.get("id"),
                    "title": item.get("title"),
                    "url": item.get("url"),
                    "source": item.get("source", {}).get("title"),
                    "published_at": item.get("published_at"),
                    "created_at": item.get("created_at"),
                    "currencies": currency_symbols,
                    "kind": item.get("kind"),
                    "votes": {
                        "positive": votes.get("positive", 0),
                        "negative": votes.get("negative", 0),
                        "important": votes.get("important", 0),
                        "liked": votes.get("liked", 0),
                        "disliked": votes.get("disliked", 0),
                        "lol": votes.get("lol", 0),
                        "toxic": votes.get("toxic", 0),
                        "saved": votes.get("saved", 0),
                    },
                })

            return posts

        except Exception as e:
            print(f"⚠️ 获取CryptoPanic新闻失败: {e}")
            return []

    async def get_trending_news(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取热门新闻

        Args:
            limit: 最大结果数

        Returns:
            List[Dict]: 热门新闻列表
        """
        posts = await self.get_posts(kind="news", filter_="hot")
        return posts[:limit]

    async def get_bullish_news(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取利好新闻

        Args:
            limit: 最大结果数

        Returns:
            List[Dict]: 利好新闻列表
        """
        posts = await self.get_posts(kind="news", filter_="bullish")
        return posts[:limit]

    async def get_bearish_news(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取利空新闻

        Args:
            limit: 最大结果数

        Returns:
            List[Dict]: 利空新闻列表
        """
        posts = await self.get_posts(kind="news", filter_="bearish")
        return posts[:limit]

    async def get_important_news(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取重要新闻

        Args:
            limit: 最大结果数

        Returns:
            List[Dict]: 重要新闻列表
        """
        posts = await self.get_posts(kind="news", filter_="important")
        return posts[:limit]

    async def get_currency_news(
        self,
        currency: str,
        filter_: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        获取特定币种的新闻

        Args:
            currency: 币种符号（如"BTC"）
            filter_: 过滤器（可选）

        Returns:
            List[Dict]: 新闻列表
        """
        return await self.get_posts(
            kind="news",
            filter_=filter_,
            currencies=currency,
        )

    # ================================
    # 情感分析和统计
    # ================================

    async def analyze_currency_sentiment(
        self,
        currency: str,
    ) -> Dict[str, Any]:
        """
        分析币种的新闻情感

        Args:
            currency: 币种符号

        Returns:
            Dict: 情感分析结果
        """
        # 获取该币种的新闻
        posts = await self.get_currency_news(currency)

        if not posts:
            return {
                "currency": currency,
                "news_count": 0,
                "sentiment_score": 0,
                "bullish_count": 0,
                "bearish_count": 0,
                "important_count": 0,
                "timestamp": datetime.utcnow().isoformat(),
            }

        # 统计投票数据
        total_positive = 0
        total_negative = 0
        total_important = 0
        bullish_count = 0
        bearish_count = 0

        for post in posts:
            votes = post.get("votes", {})
            total_positive += votes.get("positive", 0)
            total_negative += votes.get("negative", 0)
            total_important += votes.get("important", 0)

            # 判断新闻倾向
            if votes.get("positive", 0) > votes.get("negative", 0):
                bullish_count += 1
            elif votes.get("negative", 0) > votes.get("positive", 0):
                bearish_count += 1

        # 计算情感得分: -1.0（极度负面）到 1.0（极度正面）
        total_sentiment = total_positive + total_negative
        if total_sentiment > 0:
            sentiment_score = (total_positive - total_negative) / total_sentiment
        else:
            sentiment_score = 0

        # 找出最重要的新闻
        important_posts = sorted(
            posts,
            key=lambda p: p.get("votes", {}).get("important", 0),
            reverse=True
        )[:5]

        return {
            "currency": currency,
            "news_count": len(posts),
            "sentiment_score": round(sentiment_score, 2),
            "bullish_count": bullish_count,
            "bearish_count": bearish_count,
            "neutral_count": len(posts) - bullish_count - bearish_count,
            "important_count": total_important,
            "top_news": [
                {
                    "title": post["title"],
                    "url": post["url"],
                    "source": post["source"],
                    "published_at": post["published_at"],
                }
                for post in important_posts
            ],
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def get_market_sentiment(self) -> Dict[str, Any]:
        """
        获取市场整体情感

        Returns:
            Dict: 市场情感数据
        """
        # 并行获取不同类型的新闻
        bullish, bearish, important = await asyncio.gather(
            self.get_bullish_news(limit=50),
            self.get_bearish_news(limit=50),
            self.get_important_news(limit=50),
            return_exceptions=True,
        )

        # 处理异常结果
        if isinstance(bullish, Exception):
            bullish = []
        if isinstance(bearish, Exception):
            bearish = []
        if isinstance(important, Exception):
            important = []

        # 计算情感得分
        bullish_count = len(bullish)
        bearish_count = len(bearish)
        total = bullish_count + bearish_count

        if total > 0:
            sentiment_score = (bullish_count - bearish_count) / total
        else:
            sentiment_score = 0

        return {
            "sentiment_score": round(sentiment_score, 2),
            "bullish_news_count": bullish_count,
            "bearish_news_count": bearish_count,
            "important_news_count": len(important),
            "market_mood": (
                "极度看涨" if sentiment_score > 0.5 else
                "看涨" if sentiment_score > 0.2 else
                "中性" if sentiment_score > -0.2 else
                "看跌" if sentiment_score > -0.5 else
                "极度看跌"
            ),
            "timestamp": datetime.utcnow().isoformat(),
        }


# ================================
# 全局实例
# ================================

cryptopanic_collector = CryptoPanicCollector()
