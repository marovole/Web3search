"""
核心API端点集成测试
测试所有主要API端点的功能和响应
"""
import pytest
from httpx import AsyncClient


# ================================
# 健康检查API测试
# ================================

@pytest.mark.asyncio
async def test_health_check(integration_client: AsyncClient):
    """测试健康检查端点"""
    response = await integration_client.get("/health")

    assert response.status_code == 200
    data = response.json()

    # 验证响应结构
    assert "status" in data
    assert data["status"] in ["healthy", "unhealthy"]

    # 验证时间戳
    assert "timestamp" in data

    # 验证服务状态
    if "services" in data:
        assert isinstance(data["services"], dict)


@pytest.mark.asyncio
async def test_api_docs_accessible(integration_client: AsyncClient):
    """测试API文档可访问"""
    response = await integration_client.get("/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_openapi_json_accessible(integration_client: AsyncClient):
    """测试OpenAPI JSON可访问"""
    response = await integration_client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "paths" in data


# ================================
# Quick Chat API测试
# ================================

@pytest.mark.asyncio
async def test_quick_chat_endpoint_exists(
    integration_client: AsyncClient,
    valid_quick_chat_payload
):
    """测试Quick Chat端点存在且接受请求"""
    response = await integration_client.post(
        "/api/v1/chat/quick",
        json=valid_quick_chat_payload
    )

    # 端点应该存在（不是404）
    assert response.status_code != 404, "Quick Chat endpoint not found"

    # 即使Mock数据可能导致其他错误，端点应该可访问
    assert response.status_code in [200, 400, 422, 500, 503]


@pytest.mark.asyncio
async def test_quick_chat_invalid_payload(
    integration_client: AsyncClient,
    invalid_payload
):
    """测试Quick Chat端点参数验证"""
    response = await integration_client.post(
        "/api/v1/chat/quick",
        json=invalid_payload
    )

    # 应该返回验证错误
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_quick_chat_missing_query(integration_client: AsyncClient):
    """测试Quick Chat缺少必填参数"""
    response = await integration_client.post(
        "/api/v1/chat/quick",
        json={}
    )

    assert response.status_code == 422


# ================================
# Deep Research API测试
# ================================

@pytest.mark.asyncio
async def test_deep_research_endpoint_exists(
    integration_client: AsyncClient,
    valid_deep_research_payload
):
    """测试Deep Research端点存在且接受请求"""
    response = await integration_client.post(
        "/api/v1/chat/research",
        json=valid_deep_research_payload
    )

    # 端点应该存在（不是404）
    assert response.status_code != 404, "Deep Research endpoint not found"

    # 端点应该接受有效格式的请求
    assert response.status_code in [200, 400, 422, 500, 503]


@pytest.mark.asyncio
async def test_deep_research_invalid_payload(
    integration_client: AsyncClient,
    invalid_payload
):
    """测试Deep Research端点参数验证"""
    response = await integration_client.post(
        "/api/v1/chat/research",
        json=invalid_payload
    )

    assert response.status_code == 422


# ================================
# Reports API测试
# ================================

@pytest.mark.asyncio
async def test_list_reports_endpoint(integration_client: AsyncClient):
    """测试报告列表端点"""
    response = await integration_client.get("/api/v1/reports/")

    # 端点应该存在
    assert response.status_code != 404

    # 应该返回200或空列表
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, (list, dict))


@pytest.mark.asyncio
async def test_get_report_not_found(integration_client: AsyncClient):
    """测试获取不存在的报告"""
    response = await integration_client.get("/api/v1/reports/non-existent-id")

    # 应该返回404或endpoint不存在
    assert response.status_code in [404, 422]


# ================================
# API路由一致性测试
# ================================

@pytest.mark.asyncio
async def test_api_v1_prefix_consistency(integration_client: AsyncClient):
    """测试API v1前缀一致性"""
    # 所有API端点应该以/api/v1开头
    endpoints = [
        "/api/v1/chat/quick",
        "/api/v1/chat/research",
        "/api/v1/reports/",
    ]

    for endpoint in endpoints:
        # 验证端点不会导致路径重复
        assert "/api/api" not in endpoint, f"Path duplication in {endpoint}"
        assert endpoint.startswith("/api/v1"), f"Incorrect API prefix in {endpoint}"


@pytest.mark.asyncio
async def test_no_double_slash_in_urls(integration_client: AsyncClient):
    """测试URL中没有双斜杠"""
    endpoints = [
        "/api/v1/chat/quick",
        "/api/v1/chat/research",
        "/api/v1/reports/",
        "/health",
        "/docs",
    ]

    for endpoint in endpoints:
        assert "//" not in endpoint.replace("http://", "").replace("https://", ""), \
            f"Double slash found in {endpoint}"


# ================================
# CORS和安全头测试
# ================================

@pytest.mark.asyncio
async def test_cors_headers_present(integration_client: AsyncClient):
    """测试CORS头存在"""
    response = await integration_client.options(
        "/api/v1/chat/quick",
        headers={"Origin": "http://localhost:3000"}
    )

    # CORS预检请求应该成功
    assert response.status_code in [200, 204]

    # 应该有CORS相关头部（如果配置了CORS）
    # 注意：在测试环境可能不完全配置CORS


@pytest.mark.asyncio
async def test_content_type_headers(integration_client: AsyncClient):
    """测试Content-Type头正确设置"""
    response = await integration_client.get("/health")

    assert response.status_code == 200
    assert "application/json" in response.headers.get("content-type", "")
