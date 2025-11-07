"""
GitLab API服务
封装GitLab API调用，提供搜索功能
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


class GitLabService:
    """
    GitLab API服务类
    提供GitLab搜索和数据获取功能
    """

    def __init__(self):
        self.base_url = settings.GITLAB_BASE_URL
        self.token = settings.GITLAB_TOKEN
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
            "Accept": "application/json",
            "User-Agent": "Web3Search-App"
        }

        # 如果配置了token，添加认证头
        if self.token and self.token != "your_gitlab_token_here":
            headers["PRIVATE-TOKEN"] = self.token
            logger.info("GitLab API认证已启用")
        else:
            logger.warning("GitLab API未配置token，将使用匿名访问（速率限制较低）")

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=30.0
        )

        logger.info("GitLab服务初始化完成")

    async def close(self):
        """关闭服务"""
        if self.client:
            await self.client.aclose()
            logger.info("GitLab服务已关闭")

    async def search_projects(
        self,
        query: str,
        page: int = 1,
        per_page: int = 20
    ) -> Dict[str, Any]:
        """
        搜索GitLab项目

        Args:
            query: 搜索关键词
            page: 页码
            per_page: 每页数量

        Returns:
            搜索结果字典
        """
        start_time = datetime.now()
        cache_key = f"gitlab:projects:{query}:{page}:{per_page}"

        # 尝试从缓存获取
        if self.redis_client:
            try:
                cached = await self.redis_client.get(cache_key)
                if cached:
                    duration_ms = (datetime.now() - start_time).total_seconds() * 1000
                    logger.info(f"GitLab项目搜索缓存命中: {query}")
                    apm_collector.record_external_api_call(
                        service_name="gitlab",
                        endpoint="/projects",
                        method="GET",
                        status_code=200,
                        duration_ms=duration_ms,
                        response_size_bytes=len(cached)
                    )
                    return {"cached": True, "data": eval(cached)}
            except Exception as e:
                logger.debug(f"缓存读取失败: {e}")

        try:
            # 调用GitLab API
            params = {
                "search": query,
                "order_by": "stars",  # 按星标数排序
                "sort": "desc",
                "page": page,
                "per_page": per_page
            }

            response = await self.client.get("/projects", params=params)
            response.raise_for_status()

            data = response.json()

            # GitLab返回的是数组，需要转换为类似GitHub的格式
            total_count = len(data)
            if page == 1 and len(data) == per_page:
                # 如果第一页满，说明可能有更多结果，估算总数
                total_count = per_page * 10  # 估算最多10页

            formatted_data = {
                "total_count": total_count,
                "items": data
            }

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            # 记录APM指标
            apm_collector.record_external_api_call(
                service_name="gitlab",
                endpoint="/projects",
                method="GET",
                status_code=response.status_code,
                duration_ms=duration_ms,
                response_size_bytes=len(response.content)
            )

            logger.info(f"GitLab项目搜索成功: {query}, 找到 {len(data)} 个结果")

            # 缓存结果（5分钟）
            if self.redis_client:
                try:
                    await self.redis_client.setex(
                        cache_key,
                        300,
                        str(formatted_data)
                    )
                except Exception as e:
                    logger.debug(f"缓存写入失败: {e}")

            return {"cached": False, "data": formatted_data}

        except httpx.HTTPStatusError as e:
            logger.error(f"GitLab API错误: {e.response.status_code} - {e.response.text}")
            apm_collector.record_external_api_call(
                service_name="gitlab",
                endpoint="/projects",
                method="GET",
                status_code=e.response.status_code,
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
            raise

        except Exception as e:
            logger.error(f"GitLab项目搜索失败: {str(e)}")
            raise

    async def search_commits(
        self,
        query: str,
        page: int = 1,
        per_page: int = 20
    ) -> Dict[str, Any]:
        """
        搜索GitLab提交记录

        Args:
            query: 搜索关键词
            page: 页码
            per_page: 每页数量

        Returns:
            搜索结果字典
        """
        start_time = datetime.now()
        cache_key = f"gitlab:commits:{query}:{page}:{per_page}"

        # 尝试从缓存获取
        if self.redis_client:
            try:
                cached = await self.redis_client.get(cache_key)
                if cached:
                    duration_ms = (datetime.now() - start_time).total_seconds() * 1000
                    logger.info(f"GitLab提交搜索缓存命中: {query}")
                    apm_collector.record_external_api_call(
                        service_name="gitlab",
                        endpoint="/search",
                        method="GET",
                        status_code=200,
                        duration_ms=duration_ms,
                        response_size_bytes=len(cached)
                    )
                    return {"cached": True, "data": eval(cached)}
            except Exception as e:
                logger.debug(f"缓存读取失败: {e}")

        try:
            # GitLab需要使用通用搜索端点
            params = {
                "scope": "commits",
                "search": query,
                "page": page,
                "per_page": per_page
            }

            # GitLab搜索需要指定项目，这里使用全局搜索
            response = await self.client.get("/search", params=params)
            response.raise_for_status()

            data = response.json()

            # 格式化数据
            total_count = len(data)
            if page == 1 and len(data) == per_page:
                total_count = per_page * 10

            formatted_data = {
                "total_count": total_count,
                "items": data
            }

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            # 记录APM指标
            apm_collector.record_external_api_call(
                service_name="gitlab",
                endpoint="/search",
                method="GET",
                status_code=response.status_code,
                duration_ms=duration_ms,
                response_size_bytes=len(response.content)
            )

            logger.info(f"GitLab提交搜索成功: {query}, 找到 {len(data)} 个结果")

            # 缓存结果（3分钟）
            if self.redis_client:
                try:
                    await self.redis_client.setex(
                        cache_key,
                        180,
                        str(formatted_data)
                    )
                except Exception as e:
                    logger.debug(f"缓存写入失败: {e}")

            return {"cached": False, "data": formatted_data}

        except httpx.HTTPStatusError as e:
            logger.error(f"GitLab API错误: {e.response.status_code} - {e.response.text}")
            apm_collector.record_external_api_call(
                service_name="gitlab",
                endpoint="/search",
                method="GET",
                status_code=e.response.status_code,
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
            raise

        except Exception as e:
            logger.error(f"GitLab提交搜索失败: {str(e)}")
            raise

    async def search_issues(
        self,
        query: str,
        page: int = 1,
        per_page: int = 20
    ) -> Dict[str, Any]:
        """
        搜索GitLab议题和MR

        Args:
            query: 搜索关键词
            page: 页码
            per_page: 每页数量

        Returns:
            搜索结果字典
        """
        start_time = datetime.now()
        cache_key = f"gitlab:issues:{query}:{page}:{per_page}"

        # 尝试从缓存获取
        if self.redis_client:
            try:
                cached = await self.redis_client.get(cache_key)
                if cached:
                    duration_ms = (datetime.now() - start_time).total_seconds() * 1000
                    logger.info(f"GitLab议题搜索缓存命中: {query}")
                    apm_collector.record_external_api_call(
                        service_name="gitlab",
                        endpoint="/search",
                        method="GET",
                        status_code=200,
                        duration_ms=duration_ms,
                        response_size_bytes=len(cached)
                    )
                    return {"cached": True, "data": eval(cached)}
            except Exception as e:
                logger.debug(f"缓存读取失败: {e}")

        try:
            # 调用GitLab API搜索议题
            params = {
                "scope": "issues",
                "search": query,
                "page": page,
                "per_page": per_page
            }

            response = await self.client.get("/search", params=params)
            response.raise_for_status()

            data = response.json()

            # 格式化数据
            total_count = len(data)
            if page == 1 and len(data) == per_page:
                total_count = per_page * 10

            formatted_data = {
                "total_count": total_count,
                "items": data
            }

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            # 记录APM指标
            apm_collector.record_external_api_call(
                service_name="gitlab",
                endpoint="/search",
                method="GET",
                status_code=response.status_code,
                duration_ms=duration_ms,
                response_size_bytes=len(response.content)
            )

            logger.info(f"GitLab议题搜索成功: {query}, 找到 {len(data)} 个结果")

            # 缓存结果（5分钟）
            if self.redis_client:
                try:
                    await self.redis_client.setex(
                        cache_key,
                        300,
                        str(formatted_data)
                    )
                except Exception as e:
                    logger.debug(f"缓存写入失败: {e}")

            return {"cached": False, "data": formatted_data}

        except httpx.HTTPStatusError as e:
            logger.error(f"GitLab API错误: {e.response.status_code} - {e.response.text}")
            apm_collector.record_external_api_call(
                service_name="gitlab",
                endpoint="/search",
                method="GET",
                status_code=e.response.status_code,
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
            raise

        except Exception as e:
            logger.error(f"GitLab议题搜索失败: {str(e)}")
            raise


# 全局GitLab服务实例
gitlab_service = GitLabService()
