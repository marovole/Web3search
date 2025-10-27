"""
Nitter数据采集器
作为Twitter的备用数据源，通过Nitter镜像采集Twitter数据
"""
import asyncio
from typing import Dict, Any, List, Optional
import httpx
from bs4 import BeautifulSoup
from datetime import datetime

from app.core.config import settings
from app.core.redis_client import cache_get_json, cache_set
from app.core.structlog_config import get_logger

logger = get_logger(__name__)


class NitterCollector:
    """
    Nitter客户端（Twitter镜像）
    提供无需API key的Twitter数据采集功能
    """

    def __init__(self):
        """初始化Nitter客户端"""
        self.instance_url = settings.NITTER_INSTANCE_URL
        self.timeout = 30.0

    async def get_user_tweets(
        self,
        username: str,
        limit: int = 20,
        use_cache: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        获取用户推文列表

        Args:
            username: Twitter用户名
            limit: 返回推文数量
            use_cache: 是否使用缓存

        Returns:
            List: 推文列表
        """
        cache_key = f"nitter:tweets:{username}:{limit}"
        if use_cache:
            cached = await cache_get_json(cache_key)
            if cached:
                return cached

        try:
            url = f"{self.instance_url}/{username}"
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()

                # 简单返回格式，实际需要解析HTML
                logger.info("nitter_success", username=username)
                result = []

                # 缓存结果
                if use_cache:
                    await cache_set(cache_key, result, 300)

                return result

        except Exception as e:
            logger.error("nitter_failed", username=username, error=str(e))
            return []


# 全局实例
nitter_collector = NitterCollector()
