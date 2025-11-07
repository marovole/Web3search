"""
GitHub API端点
提供GitHub代码仓库、提交记录、议题和PR的搜索功能
"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import Annotated
import time

from app.schemas.github_schemas import (
    GitHubSearchRequest, GitHubSearchResponse, AIGeneratedSummary
)
from app.services.github_service import github_service
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
    response_model=GitHubSearchResponse,
    summary="GitHub搜索",
    description="搜索GitHub上的代码仓库、提交记录、议题和PR，并提供AI智能摘要",
    tags=["GitHub"],
    responses={
        200: {
            "description": "搜索成功",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "query": "blockchain",
                        "search_type": "repositories",
                        "data": {
                            "total_count": 1000,
                            "items": [
                                {
                                    "id": 123456,
                                    "name": "bitcoin",
                                    "full_name": "bitcoin/bitcoin",
                                    "description": "Bitcoin Core integration/staging tree",
                                    "html_url": "https://github.com/bitcoin/bitcoin",
                                    "language": "C++",
                                    "stargazers_count": 50000
                                }
                            ],
                            "page": 1,
                            "per_page": 20
                        },
                        "summary": {
                            "total_results": 1000,
                            "result_types": {"repositories": 800, "issues": 200},
                            "key_insights": [
                                "Blockchain相关项目主要使用C++, Go和Rust语言",
                                "热门项目包括Bitcoin, Ethereum, Hyperledger等",
                                "最近活跃度高，显示持续开发"
                            ],
                            "top_repositories": ["bitcoin/bitcoin", "ethereum/go-ethereum"],
                            "languages": [{"name": "C++", "count": 300}, {"name": "Go", "count": 250}]
                        },
                        "execution_time_ms": 1500.5
                    }
                }
            }
        },
        400: {"description": "搜索关键词无效"},
        401: {"description": "GitHub API认证失败"},
        429: {"description": "GitHub API速率限制"},
        500: {"description": "服务器内部错误"}
    }
)
@track_feature_usage(FeatureType.SEARCH, "github_search")
async def github_search(
    query: str,
    search_type: str = "repositories",
    page: int = 1,
    per_page: int = 20
):
    """
    GitHub搜索API

    搜索GitHub上的代码仓库、提交记录、议题和PR，
    并使用AI生成智能摘要。

    Args:
        query: 搜索关键词
        search_type: 搜索类型（repositories, commits, issues）
        page: 页码
        per_page: 每页数量

    Returns:
        包含原始数据和AI摘要的搜索结果
    """
    start_time = time.time()

    try:
        # 初始化GitHub服务
        async with github_service:
            # 根据搜索类型调用不同API
            if search_type == "repositories":
                result = await github_service.search_repositories(query, page, per_page)
            elif search_type == "commits":
                result = await github_service.search_commits(query, page, per_page)
            elif search_type == "issues":
                result = await github_service.search_issues(query, page, per_page)
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"无效的搜索类型: {search_type}. 可选值: repositories, commits, issues"
                )

            # 获取搜索数据
            search_data = result["data"]

            # 生成AI摘要
            summary = await generate_ai_summary(query, search_data, search_type)

            execution_time_ms = (time.time() - start_time) * 1000

            # 构建响应
            response = GitHubSearchResponse(
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

            logger.info(f"GitHub搜索完成: {query} (类型: {search_type}), 耗时: {execution_time_ms:.2f}ms")

            return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GitHub搜索失败: {str(e)}", exc_info=True)
        apm_collector.record_error(
            error_type="github_search_error",
            error_message=str(e),
            context={"query": query, "search_type": search_type}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"GitHub搜索失败: {str(e)}"
        )


async def generate_ai_summary(query: str, search_data: dict, search_type: str) -> AIGeneratedSummary:
    """
    生成AI摘要

    Args:
        query: 搜索关键词
        search_data: 原始搜索数据
        search_type: 搜索类型

    Returns:
        AI生成的摘要
    """
    try:
        items = search_data.get("items", [])
        if not items:
            return AIGeneratedSummary(
                total_results=0,
                result_types={search_type: 0},
                key_insights=["未找到相关结果"],
                top_repositories=[],
                languages=[]
            )

        total_count = search_data.get("total_count", len(items))

        # 准备数据用于AI分析
        analysis_data = {
            "query": query,
            "total_results": total_count,
            "search_type": search_type,
            "items_count": len(items)
        }

        # 提取语言统计
        languages = {}
        for item in items:
            if search_type == "repositories":
                lang = item.get("language")
                if lang:
                    languages[lang] = languages.get(lang, 0) + 1
            elif search_type == "issues":
                # 议题的语言信息在仓库中
                pass

        # 准备语言分布数据
        lang_distribution = [
            {"name": lang, "count": count}
            for lang, count in sorted(languages.items(), key=lambda x: x[1], reverse=True)[:10]
        ]

        # 提取热门仓库
        top_repos = []
        for item in items[:5]:
            if search_type == "repositories":
                top_repos.append(item.get("full_name", ""))
            elif search_type == "issues":
                repo_url = item.get("repository_url", "")
                if repo_url:
                    repo_name = repo_url.replace("https://api.github.com/repos/", "")
                    top_repos.append(repo_name)

        # 生成结果类型分布
        result_types = {search_type: len(items)}

        # 使用AI生成关键洞察
        key_insights = await generate_insights_with_ai(query, items, search_type)

        return AIGeneratedSummary(
            total_results=total_count,
            result_types=result_types,
            key_insights=key_insights,
            top_repositories=top_repos,
            languages=lang_distribution
        )

    except Exception as e:
        logger.warning(f"AI摘要生成失败: {str(e)}")
        return AIGeneratedSummary(
            total_results=search_data.get("total_count", 0),
            result_types={search_type: len(search_data.get("items", []))},
            key_insights=["AI摘要生成失败，显示原始数据"],
            top_repositories=[],
            languages=[]
        )


async def generate_insights_with_ai(query: str, items: list, search_type: str) -> list:
    """
    使用AI生成关键洞察

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
        分析以下GitHub搜索结果并提供3-5个关键洞察。
        搜索关键词: {query}
        搜索类型: {search_type}
        结果数量: {len(items)}

        请提供以下洞察：
        1. 主要技术栈/编程语言
        2. 热门项目/趋势
        3. 社区活跃度
        4. 最近发展动态

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
            if line and (line.startswith("-") or line.startswith("•") or line.startswith("1.")):
                # 移除项目符号和编号
                line = line.lstrip("-•\t 1234567890.")
                line = line.strip()
                if line:
                    insights.append(line)

        if not insights:
            insights = ["AI分析完成，但未生成具体洞察"]

        return insights[:5]  # 最多5个洞察

    except Exception as e:
        logger.warning(f"AI洞察生成失败: {str(e)}")
        return ["AI洞察生成失败"]


@router.get("/rate-limit", summary="获取GitHub API速率限制信息", tags=["GitHub"])
async def get_github_rate_limit():
    """
    获取GitHub API速率限制信息

    Returns:
        速率限制信息
    """
    try:
        async with github_service as service:
            # 调用GitHub rate limit API
            response_data = await service.client.get("/rate_limit")
            response_data.raise_for_status()
            rate_data = response_data.json()

            return {
                "success": True,
                "rate_limit": rate_data.get("rate", {}),
                "resources": rate_data.get("resources", {})
            }

    except Exception as e:
        logger.error(f"获取GitHub速率限制失败: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "无法获取速率限制信息"
        }
