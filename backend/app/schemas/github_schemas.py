"""
GitHub API schemas
定义GitHub搜索的请求和响应模型
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


class GitHubSearchRequest(BaseModel):
    """GitHub搜索请求模型"""
    query: str = Field(..., description="搜索关键词", min_length=1, max_length=200)
    search_type: Literal["repositories", "commits", "issues"] = Field(
        default="repositories",
        description="搜索类型: repositories(仓库), commits(提交), issues(议题和PR)"
    )
    page: int = Field(default=1, ge=1, description="页码")
    per_page: int = Field(default=20, ge=1, le=100, description="每页数量")


class GitHubRepositoryItem(BaseModel):
    """GitHub仓库项"""
    id: int = Field(..., description="仓库ID")
    name: str = Field(..., description="仓库名称")
    full_name: str = Field(..., description="完整名称（owner/repo）")
    description: Optional[str] = Field(None, description="仓库描述")
    html_url: str = Field(..., description="仓库URL")
    language: Optional[str] = Field(None, description="主要编程语言")
    stargazers_count: int = Field(default=0, description="星标数")
    forks_count: int = Field(default=0, description="分叉数")
    open_issues_count: int = Field(default=0, description="开放议题数")
    owner: dict = Field(..., description="所有者信息")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    topics: List[str] = Field(default_factory=list, description="主题标签")


class GitHubCommitItem(BaseModel):
    """GitHub提交记录项"""
    sha: str = Field(..., description="提交SHA")
    commit: dict = Field(..., description="提交信息")
    html_url: str = Field(..., description="提交URL")
    author: Optional[dict] = Field(None, description="作者信息")
    committer: Optional[dict] = Field(None, description="提交者信息")


class GitHubIssueItem(BaseModel):
    """GitHub议题/PR项"""
    id: int = Field(..., description="议题ID")
    number: int = Field(..., description="议题编号")
    title: str = Field(..., description="标题")
    state: str = Field(..., description="状态（open/closed）")
    html_url: str = Field(..., description="议题URL")
    user: dict = Field(..., description="创建者信息")
    labels: List[dict] = Field(default_factory=list, description="标签")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    closed_at: Optional[datetime] = Field(None, description="关闭时间")
    pull_request: Optional[dict] = Field(None, description="PR信息（如果是PR）")


class GitHubSearchResult(BaseModel):
    """GitHub搜索结果"""
    total_count: int = Field(..., description="总结果数")
    items: List[dict] = Field(default_factory=list, description="搜索结果列表")
    page: int = Field(..., description="当前页码")
    per_page: int = Field(..., description="每页数量")


class AIGeneratedSummary(BaseModel):
    """AI生成的搜索摘要"""
    total_results: int = Field(..., description="总结果数")
    result_types: dict = Field(..., description="结果类型分布")
    key_insights: List[str] = Field(default_factory=list, description="关键洞察")
    top_repositories: List[str] = Field(default_factory=list, description="热门仓库")
    languages: List[dict] = Field(default_factory=list, description="编程语言分布")
    recent_activity: Optional[str] = Field(None, description="最近活动趋势")


class GitHubSearchResponse(BaseModel):
    """GitHub搜索响应"""
    success: bool = Field(..., description="请求是否成功")
    data: Optional[GitHubSearchResult] = Field(None, description="原始搜索结果")
    summary: Optional[AIGeneratedSummary] = Field(None, description="AI生成的摘要")
    query: str = Field(..., description="搜索关键词")
    search_type: str = Field(..., description="搜索类型")
    execution_time_ms: float = Field(..., description="执行时间（毫秒）")
