"""
Pushshift数据采集器
作为Reddit的备用数据源，使用Pushshift API采集Reddit历史数据
"""
import asyncio
from typing import Dict, Any, List, Optional
import httpx
from datetime import datetime

from app.core.config import settings
from app.core.redis_client import cache_get_json, cache_set
from app.core.structlog_config import get_logger

logger = get_logger(__name__)


class PushshiftCollector:
    """
    Pushshift API客户端
    提供Reddit历史数据采集功能（Reddit API的fallback）
    """

    def __init__(self):
        """初始化Pushshift客户端"""
        self.base_url = settings.PUSHSHIFT_BASE_URL
        self.timeout = 30.0

    async def search_submissions(
        self,
        subreddit: str,
        query: str,
        limit: int = 25,
        use_cache: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        搜索Reddit帖子

        Args:
            subreddit: 子版块名称
            query: 搜索关键词
            limit: 返回结果数量
            use_cache: 是否使用缓存

        Returns:
            List: 帖子列表
        """
        cache_key = f"pushshift:submissions:{subreddit}:{query}:{limit}"
        if use_cache:
            cached = await cache_get_json(cache_key)
            if cached:
                return cached

        try:
            url = f"{self.base_url}/reddit/search/submission"
            params = {
                "subreddit": subreddit,
                "q": query,
                "size": limit,
                "sort": "desc",
                "sort_type": "created_utc"
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                results = data.get("data", [])
                logger.info("pushshift_success", subreddit=subreddit, count=len(results))

                # 缓存结果
                if use_cache:
                    await cache_set(cache_key, results, 600)

                return results

        except Exception as e:
            logger.error("pushshift_failed", subreddit=subreddit, error=str(e))
            return []


# 全局实例
pushshift_collector = PushshiftCollector()
