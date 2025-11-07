"""
GitLab API端点
提供GitLab项目、提交记录、议题和MR的搜索功能
"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import Annotated
import time

from app.schemas.gitlab_schemas import (
    GitLabSearchRequest, GitLabSearchResponse
)
from app.services.gitlab_service import gitlab_service
from app.services.ai_service import ai_service
from app.core.config import settings
from app.core.monitoring import apm_collector
from app.core.business_tracker import track_feature_usage
from app.core.business_metrics import FeatureType
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/search",
    response_model=GitLabSearchResponse,
    summary="GitLab搜索",
    description="搜索GitLab上的项目、提交记录、议题和MR，并提供AI智能摘要",
    tags=["GitLab"],
    responses={
        200: {
            "description": "搜索成功",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "query": "blockchain",
                        "search_type": "projects",
                        "data": {
                            "total_count": 500,
                            "items": [
                                {
                                    "id": 12345,
                                    "name": "blockchain-explorer",
                                    "path_with_namespace": "group/blockchain-explorer",
                                    "description": "A blockchain explorer tool",
                                    "web_url": "https://gitlab.com/group/blockchain-explorer",
                                    "star_count": 100,
                                    "forks_count": 50
                                }
                            ],
                            "page": 1,
                            "per_page": 20
                        },
                        "summary": {
                            "total_results": 500,
                            "result_types": {"projects": 400, "issues": 100},
                            "key_insights": [
                                "在GitLab上找到多个活跃的区块链项目",
                                "项目主要集中在DeFi和基础设施领域",
                                "近期有显著的贡献活动"
                            ],
                            "top_repositories": ["group/blockchain-explorer", "group/defi-protocol"],
                            "languages": [{"name": "Solidity", "count": 150}, {"name": "Rust", "count": 100}]
                        },
                        "execution_time_ms": 1200.5
                    }
                }
            }
        },
        400: {"description": "搜索关键词无效"},
        401: {"description": "GitLab API认证失败"},
        429: {"description": "GitLab API速率限制"},
        500: {"description": "服务器内部错误"}
    }
)
@track_feature_usage(FeatureType.SEARCH, "gitlab_search")
async def gitlab_search(
    query: str,
    search_type: str = "projects",
    page: int = 1,
    per_page: int = 20
):
    """
    GitLab搜索API

    搜索GitLab上的项目、提交记录、议题和MR，
    并使用AI生成智能摘要。

    Args:
        query: 搜索关键词
        search_type: 搜索类型（projects, commits, issues）
        page: 页码
        per_page: 每页数量

    Returns:
        包含原始数据和AI摘要的搜索结果
    """
    start_time = time.time()

    try:
        # 初始化GitLab服务
        async with gitlab_service:
            # 根据搜索类型调用不同API
            if search_type == "projects":
                result = await gitlab_service.search_projects(query, page, per_page)
            elif search_type == "commits":
                result = await gitlab_service.search_commits(query, page, per_page)
            elif search_type == "issues":
                result = await gitlab_service.search_issues(query, page, per_page)
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"无效的搜索类型: {search_type}. 可选值: projects, commits, issues"
                )

            # 获取搜索数据
            search_data = result["data"]

            # 生成AI摘要
            summary = await generate_gitlab_ai_summary(query, search_data, search_type)

            execution_time_ms = (time.time() - start_time) * 1000

            # 构建响应
            response = GitLabSearchResponse(
                success=True,
                data={
                    "total_count": search_data.get("total_count", 0),
                    "items": search_data.get("items", []),
                    "page": page,
                    "per_page": per_page
                },
                summary=summary,
                query=query,
                search_type=search_type,
                execution_time_ms=execution_time_ms
            )

            logger.info(f"GitLab搜索完成: {query} (类型: {search_type}), 耗时: {execution_time_ms:.2f}ms")

            return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GitLab搜索失败: {str(e)}", exc_info=True)
        apm_collector.record_error(
            error_type="gitlab_search_error",
            error_message=str(e),
            context={"query": query, "search_type": search_type}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"GitLab搜索失败: {str(e)}"
        )


async def generate_gitlab_ai_summary(query: str, search_data: dict, search_type: str):
    """
    生成GitLab搜索AI摘要

    Args:
        query: 搜索关键词
        search_data: 原始搜索数据
        search_type: 搜索类型

    Returns:
        AI生成的摘要字典
    """
    try:
        items = search_data.get("items", [])
        if not items:
            return {
                "total_results": 0,
                "result_types": {search_type: 0},
                "key_insights": ["未找到相关结果"],
                "top_repositories": [],
                "languages": []
            }

        total_count = search_data.get("total_count", len(items))

        # 根据搜索类型提取信息
        top_repos = []
        languages = {}

        for item in items[:10]:  # 只分析前10个
            if search_type == "projects":
                # 提取项目名称
                name = item.get("path_with_namespace", "")
                if name:
                    top_repos.append(name)

            elif search_type == "issues":
                # 议题的项目信息
                project = item.get("references", {}).get("full", "")
                if project:
                    top_repos.append(project)

        # 生成关键洞察
        insights = await generate_gitlab_insights(query, items, search_type)

        # 准备响应
        return {
            "total_results": total_count,
            "result_types": {search_type: len(items)},
            "key_insights": insights,
            "top_repositories": top_repos[:5],
            "languages": []  # GitLab API不直接返回语言信息
        }

    except Exception as e:
        logger.warning(f"GitLab AI摘要生成失败: {str(e)}")
        return {
            "total_results": search_data.get("total_count", 0),
            "result_types": {search_type: len(search_data.get("items", []))},
            "key_insights": ["AI摘要生成失败，显示原始数据"],
            "top_repositories": [],
            "languages": []
        }


async def generate_gitlab_insights(query: str, items: list, search_type: str):
    """
    使用AI生成GitLab关键洞察

    Args:
        query: 搜索关键词
        items: 搜索结果项
        search_type: 搜索类型

    Returns:
        关键洞察列表
    """
    try:
        if not items:
            return ["未找到相关结果"]

        # 准备提示词
        prompt = f"""
        分析以下GitLab搜索结果并提供3-5个关键洞察。

        搜索关键词: {query}
        搜索类型: {search_type}
        结果数量: {len(items)}

        请注意GitLab主要面向企业和组织项目，
        与GitHub的开源社区有所不同。

        请提供以下洞察：
        1. 项目类型和组织背景
        2. 技术栈和开发活跃度
        3. 企业采用情况
        4. 最近发展趋势

        请用简洁的中文回答，提供3-5个要点。
        """

        # 调用AI服务生成洞察
        response = await ai_service.chat_completion(
            prompt=prompt,
            model="anthropic/claude-3-haiku",
            temperature=0.3,
            max_tokens=500
        )

        insights_text = response.get("content", "")

        # 将文本拆分为要点
        insights = []
        for line in insights_text.split("\n"):
            line = line.strip()
            if line and (line.startswith("-") or line.startswith("•") or line[0].isdigit()):
                # 移除项目符号和编号
                line = line.lstrip("-•\t 1234567890.")
                line = line.strip()
                if line:
                    insights.append(line)

        if not insights:
            insights = ["AI分析完成，但未生成具体洞察"]

        return insights[:5]  # 最多5个洞察

    except Exception as e:
        logger.warning(f"GitLab AI洞察生成失败: {str(e)}")
        return ["AI洞察生成失败"]
