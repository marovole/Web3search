"""
API端点测试
测试Quick Chat、Deep Research和Reports API
"""
import pytest
from httpx import AsyncClient
from fastapi import status


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """测试健康检查端点"""
    response = await client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] in ["healthy", "unhealthy"]
    assert "database" in data
    assert "redis" in data


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """测试根路径"""
    response = await client.get("/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "Web3 Search API"
    assert "version" in data


# ================================
# Quick Chat Tests
# ================================

@pytest.mark.asyncio
async def test_quick_chat_success(client: AsyncClient):
    """测试Quick Chat成功场景"""
    response = await client.post(
        "/api/v1/quick-chat",
        json={
            "query": "BTC现在的价格是多少？",
            "stream": False
        }
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "content" in data
    assert "query_type" in data
    assert "response_time" in data
    assert data["model"] is not None


@pytest.mark.asyncio
async def test_quick_chat_empty_query(client: AsyncClient):
    """测试空查询"""
    response = await client.post(
        "/api/v1/quick-chat",
        json={"query": ""}
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_quick_chat_rate_limit(client: AsyncClient):
    """测试速率限制"""
    # 连续发送多个请求
    for i in range(12):
        response = await client.post(
            "/api/v1/quick-chat",
            json={"query": f"测试查询 {i}"}
        )
        if i < 10:
            # 前10个应该成功
            assert response.status_code == status.HTTP_200_OK
        else:
            # 第11个应该被限流
            assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS


# ================================
# Deep Research Tests
# ================================

@pytest.mark.asyncio
async def test_deep_research_success(client: AsyncClient):
    """测试Deep Research成功场景"""
    response = await client.post(
        "/api/v1/deep-research",
        json={
            "query": "请分析以太坊",
            "symbol": "ETH"
        }
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "report_id" in data
    assert "symbol" in data
    assert "tldr" in data
    assert "sections" in data
    assert "markdown_content" in data
    assert data["quality_score"] >= 0


@pytest.mark.asyncio
async def test_deep_research_invalid_symbol(client: AsyncClient):
    """测试无效币种"""
    response = await client.post(
        "/api/v1/deep-research",
        json={
            "query": "分析这个币",
            "symbol": "INVALIDCOIN123"
        }
    )
    # 应该返回404或500
    assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_500_INTERNAL_SERVER_ERROR]


# ================================
# Reports Tests
# ================================

@pytest.mark.asyncio
async def test_get_reports_list(client: AsyncClient):
    """测试获取报告列表"""
    response = await client.get("/api/v1/reports?page=1&page_size=10")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "reports" in data
    assert "total" in data
    assert "page" in data
    assert data["page"] == 1


@pytest.mark.asyncio
async def test_get_report_detail(client: AsyncClient):
    """测试获取报告详情"""
    # 先创建一个报告
    create_response = await client.post(
        "/api/v1/deep-research",
        json={"query": "测试报告", "symbol": "BTC"}
    )

    if create_response.status_code == status.HTTP_200_OK:
        report_id = create_response.json()["report_id"]

        # 获取报告详情
        response = await client.get(f"/api/v1/reports/{report_id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == report_id
        assert "markdown_content" in data


@pytest.mark.asyncio
async def test_get_report_not_found(client: AsyncClient):
    """测试获取不存在的报告"""
    response = await client.get("/api/v1/reports/99999")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_get_report_stats(client: AsyncClient):
    """测试报告统计"""
    response = await client.get("/api/v1/reports/stats/summary")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "total_reports" in data
    assert "by_type" in data
    assert "by_status" in data


@pytest.mark.asyncio
async def test_filter_reports_by_symbol(client: AsyncClient):
    """测试按币种筛选报告"""
    response = await client.get("/api/v1/reports?symbol=BTC&page=1&page_size=10")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    for report in data["reports"]:
        assert report["symbol"] == "BTC"


@pytest.mark.asyncio
async def test_delete_report(client: AsyncClient):
    """测试删除报告"""
    # 先创建一个报告
    create_response = await client.post(
        "/api/v1/deep-research",
        json={"query": "待删除的报告", "symbol": "BTC"}
    )

    if create_response.status_code == status.HTTP_200_OK:
        report_id = create_response.json()["report_id"]

        # 删除报告
        response = await client.delete(f"/api/v1/reports/{report_id}")
        assert response.status_code == status.HTTP_200_OK

        # 验证已删除
        get_response = await client.get(f"/api/v1/reports/{report_id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND
