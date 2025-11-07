"""
GitLab API schemas
定义GitLab搜索的请求和响应模型
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


class GitLabSearchRequest(BaseModel):
    """GitLab搜索请求模型"""
    query: str = Field(..., description="搜索关键词", min_length=1, max_length=200)
    search_type: Literal["projects", "commits", "issues"] = Field(
        default="projects",
        description="搜索类型: projects(项目), commits(提交), issues(议题和MR)"
    )
    page: int = Field(default=1, ge=1, description="页码")
    per_page: int = Field(default=20, ge=1, le=100, description="每页数量")


class GitLabProjectItem(BaseModel):
    """GitLab项目项"""
    id: int = Field(..., description="项目ID")
    name: str = Field(..., description="项目名称")
    path_with_namespace: str = Field(..., description="完整路径（group/project）")
    description: Optional[str] = Field(None, description="项目描述")
    web_url: str = Field(..., description="项目URL")
    readme_url: Optional[str] = Field(None, description="README URL")
    star_count: int = Field(default=0, description="星标数")
    forks_count: int = Field(default=0, description="分叉数")
    open_issues_count: int = Field(default=0, description="开放议题数")
    namespace: dict = Field(..., description="命名空间信息")
    created_at: datetime = Field(..., description="创建时间")
    last_activity_at: datetime = Field(..., description="最后活动时间")
    topics: List[str] = Field(default_factory=list, description="主题标签")


class GitLabCommitItem(BaseModel):
    """GitLab提交记录项"""
    id: str = Field(..., description="提交ID（SHA）")
    title: str = Field(..., description="提交标题")
    message: str = Field(..., description="完整提交信息")
    web_url: str = Field(..., description="提交URL")
    author_name: str = Field(..., description="作者名称")
    author_email: str = Field(..., description="作者邮箱")
    authored_date: datetime = Field(..., description="作者日期")
    committed_date: datetime = Field(..., description="提交日期")


class GitLabIssueItem(BaseModel):
    """GitLab议题/MR项"""
    id: int = Field(..., description="议题ID")
    iid: int = Field(..., description="项目内议题编号")
    title: str = Field(..., description="标题")
    state: str = Field(..., description="状态（opened/closed）")
    web_url: str = Field(..., description="议题URL")
    author: dict = Field(..., description="作者信息")
    labels: List[str] = Field(default_factory=list, description="标签")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    closed_at: Optional[datetime] = Field(None, description="关闭时间")
    merge_requests_count: int = Field(default=0, description="关联MR数量")


class GitLabSearchResult(BaseModel):
    """GitLab搜索结果"""
    total_count: int = Field(..., description="总结果数")
    items: List[dict] = Field(default_factory=list, description="搜索结果列表")
    page: int = Field(..., description="当前页码")
    per_page: int = Field(..., description="每页数量")


class GitLabSearchResponse(BaseModel):
    """GitLab搜索响应"""
    success: bool = Field(..., description="请求是否成功")
    data: Optional[GitLabSearchResult] = Field(None, description="原始搜索结果")
    summary: Optional[dict] = Field(None, description="AI生成的摘要")
    query: str = Field(..., description="搜索关键词")
    search_type: str = Field(..., description="搜索类型")
    execution_time_ms: float = Field(..., description="执行时间（毫秒）")
