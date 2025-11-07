"""
GitHub API服务
封装GitHub API调用，提供搜索功能
"""
import httpx
from typing import Dict, Any, Optional
from datetime import datetime
import asyncio

from app.core.config import settings
from app.core.redis_client import get_redis_client
from app.core.monitoring import apm_collector
import logging

logger = logging.getLogger(__name__)


class GitHubService:
    """
    GitHub API服务类
    提供GitHub搜索和数据获取功能
    """

    def __init__(self):
        self.base_url = settings.GITHUB_BASE_URL
        self.token = settings.GITHUB_TOKEN
        self.redis_client = None
        self.client = None

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()

    async def initialize(self):
        """初始化服务"""
        # 初始化Redis客户端
        try:
            self.redis_client = await get_redis_client()
        except Exception as e:
            logger.warning(f"Redis初始化警告: {e}")
            self.redis_client = None

        # 初始化HTTP客户端
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Web3Search-App"
        }

        # 如果配置了token，添加认证头
        if self.token and self.token != "your_github_token_here":
            headers["Authorization"] = f"token {self.token}"
            logger.info("GitHub API认证已启用")
        else:
            logger.warning("GitHub API未配置token，将使用匿名访问（速率限制较低）")

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=30.0
        )

        logger.info("GitHub服务初始化完成")

    async def close(self):
        """关闭服务"""
        if self.client:
            await self.client.aclose()
            logger.info("GitHub服务已关闭")

    async def search_repositories(
        self,
        query: str,
        page: int = 1,
        per_page: int = 20
    ) -> Dict[str, Any]:
        """
        搜索GitHub仓库

        Args:
            query: 搜索关键词
            page: 页码
            per_page: 每页数量

        Returns:
            搜索结果字典
        """
        start_time = datetime.now()
        cache_key = f"github:repos:{query}:{page}:{per_page}"

        # 尝试从缓存获取
        if self.redis_client:
            try:
                cached = await self.redis_client.get(cache_key)
                if cached:
                    duration_ms = (datetime.now() - start_time).total_seconds() * 1000
                    logger.info(f"GitHub仓库搜索缓存命中: {query}")
                    apm_collector.record_external_api_call(
                        service_name="github",
                        endpoint="/search/repositories",
                        method="GET",
                        status_code=200,
                        duration_ms=duration_ms,
                        response_size_bytes=len(cached)
                    )
                    return {"cached": True, "data": eval(cached)}
            except Exception as e:
                logger.debug(f"缓存读取失败: {e}")

        try:
            # 调用GitHub API
            params = {
                "q": query,
                "sort": "stars",  # 按星标数排序
                "order": "desc",
                "page": page,
                "per_page": per_page
            }

            response = await self.client.get("/search/repositories", params=params)
            response.raise_for_status()

            data = response.json()
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            # 记录APM指标
            apm_collector.record_external_api_call(
                service_name="github",
                endpoint="/search/repositories",
                method="GET",
                status_code=response.status_code,
                duration_ms=duration_ms,
                response_size_bytes=len(response.content)
            )

            logger.info(f"GitHub仓库搜索成功: {query}, 找到 {data.get('total_count', 0)} 个结果")

            # 缓存结果（5分钟）
            if self.redis_client:
                try:
                    await self.redis_client.setex(
                        cache_key,
                        300,  # 5分钟缓存
                        str(data)
                    )
                except Exception as e:
                    logger.debug(f"缓存写入失败: {e}")

            return {"cached": False, "data": data}

        except httpx.HTTPStatusError as e:
            logger.error(f"GitHub API错误: {e.response.status_code} - {e.response.text}")
            apm_collector.record_external_api_call(
                service_name="github",
                endpoint="/search/repositories",
                method="GET",
                status_code=e.response.status_code,
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
            raise

        except Exception as e:
            logger.error(f"GitHub仓库搜索失败: {str(e)}")
            raise

    async def search_commits(
        self,
        query: str,
        page: int = 1,
        per_page: int = 20
    ) -> Dict[str, Any]:
        """
        搜索GitHub提交记录

        Args:
            query: 搜索关键词
            page: 页码
            per_page: 每页数量

        Returns:
            搜索结果字典
        """
        start_time = datetime.now()
        cache_key = f"github:commits:{query}:{page}:{per_page}"

        # 尝试从缓存获取
        if self.redis_client:
            try:
                cached = await self.redis_client.get(cache_key)
                if cached:
                    duration_ms = (datetime.now() - start_time).total_seconds() * 1000
                    logger.info(f"GitHub提交搜索缓存命中: {query}")
                    apm_collector.record_external_api_call(
                        service_name="github",
                        endpoint="/search/commits",
                        method="GET",
                        status_code=200,
                        duration_ms=duration_ms,
                        response_size_bytes=len(cached)
                    )
                    return {"cached": True, "data": eval(cached)}
            except Exception as e:
                logger.debug(f"缓存读取失败: {e}")

        try:
            # 调用GitHub API
            headers = {
                "Accept": "application/vnd.github.cloak-preview"  # commits搜索需要预览头
            }

            params = {
                "q": query,
                "page": page,
                "per_page": per_page
            }

            response = await self.client.get(
                "/search/commits",
                params=params,
                headers=headers
            )
            response.raise_for_status()

            data = response.json()
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            # 记录APM指标
            apm_collector.record_external_api_call(
                service_name="github",
                endpoint="/search/commits",
                method="GET",
                status_code=response.status_code,
                duration_ms=duration_ms,
                response_size_bytes=len(response.content)
            )

            logger.info(f"GitHub提交搜索成功: {query}, 找到 {data.get('total_count', 0)} 个结果")

            # 缓存结果（3分钟，提交记录变化较快）
            if self.redis_client:
                try:
                    await self.redis_client.setex(
                        cache_key,
                        180,  # 3分钟缓存
                        str(data)
                    )
                except Exception as e:
                    logger.debug(f"缓存写入失败: {e}")

            return {"cached": False, "data": data}

        except httpx.HTTPStatusError as e:
            logger.error(f"GitHub API错误: {e.response.status_code} - {e.response.text}")
            apm_collector.record_external_api_call(
                service_name="github",
                endpoint="/search/commits",
                method="GET",
                status_code=e.response.status_code,
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
            raise

        except Exception as e:
            logger.error(f"GitHub提交搜索失败: {str(e)}")
            raise

    async def search_issues(
        self,
        query: str,
        page: int = 1,
        per_page: int = 20
    ) -> Dict[str, Any]:
        """
        搜索GitHub议题和PR

        Args:
            query: 搜索关键词
            page: 页码
            per_page: 每页数量

        Returns:
            搜索结果字典
        """
        start_time = datetime.now()
        cache_key = f"github:issues:{query}:{page}:{per_page}"

        # 尝试从缓存获取
        if self.redis_client:
            try:
                cached = await self.redis_client.get(cache_key)
                if cached:
                    duration_ms = (datetime.now() - start_time).total_seconds() * 1000
                    logger.info(f"GitHub议题搜索缓存命中: {query}")
                    apm_collector.record_external_api_call(
                        service_name="github",
                        endpoint="/search/issues",
                        method="GET",
                        status_code=200,
                        duration_ms=duration_ms,
                        response_size_bytes=len(cached)
                    )
                    return {"cached": True, "data": eval(cached)}
            except Exception as e:
                logger.debug(f"缓存读取失败: {e}")

        try:
            # 调用GitHub API
            params = {
                "q": query,
                "page": page,
                "per_page": per_page
            }

            response = await self.client.get("/search/issues", params=params)
            response.raise_for_status()

            data = response.json()
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            # 记录APM指标
            apm_collector.record_external_api_call(
                service_name="github",
                endpoint="/search/issues",
                method="GET",
                status_code=response.status_code,
                duration_ms=duration_ms,
                response_size_bytes=len(response.content)
            )

            issues_count = data.get('total_count', 0)
            logger.info(f"GitHub议题搜索成功: {query}, 找到 {issues_count} 个结果")

            # 缓存结果（5分钟）
            if self.redis_client:
                try:
                    await self.redis_client.setex(
                        cache_key,
                        300,
                        str(data)
                    )
                except Exception as e:
                    logger.debug(f"缓存写入失败: {e}")

            return {"cached": False, "data": data}

        except httpx.HTTPStatusError as e:
            logger.error(f"GitHub API错误: {e.response.status_code} - {e.response.text}")
            apm_collector.record_external_api_call(
                service_name="github",
                endpoint="/search/issues",
                method="GET",
                status_code=e.response.status_code,
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
            raise

        except Exception as e:
            logger.error(f"GitHub议题搜索失败: {str(e)}")
            raise


# 全局GitHub服务实例
github_service = GitHubService()
