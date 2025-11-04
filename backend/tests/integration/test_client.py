"""
API客户端测试辅助工具
提供通用的API测试方法和断言
"""
import pytest
from typing import Dict, Any, Optional
from httpx import AsyncClient, Response


class APITestClient:
    """API测试客户端包装器"""

    def __init__(self, client: AsyncClient):
        self.client = client

    async def test_endpoint(
        self,
        method: str,
        url: str,
        expected_status: int = 200,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        """
        测试API端点的通用方法

        Args:
            method: HTTP方法 (GET, POST, PUT, DELETE)
            url: API端点URL
            expected_status: 期望的HTTP状态码
            json_data: JSON请求体
            headers: 请求头

        Returns:
            响应对象
        """
        response = await self.client.request(
            method=method,
            url=url,
            json=json_data,
            headers=headers or {}
        )

        assert response.status_code == expected_status, (
            f"Expected status {expected_status}, got {response.status_code}. "
            f"Response: {response.text}"
        )

        return response

    async def get(self, url: str, expected_status: int = 200, **kwargs) -> Response:
        """GET请求"""
        return await self.test_endpoint("GET", url, expected_status, **kwargs)

    async def post(
        self,
        url: str,
        json_data: Dict[str, Any],
        expected_status: int = 200,
        **kwargs
    ) -> Response:
        """POST请求"""
        return await self.test_endpoint("POST", url, expected_status, json_data, **kwargs)

    async def put(
        self,
        url: str,
        json_data: Dict[str, Any],
        expected_status: int = 200,
        **kwargs
    ) -> Response:
        """PUT请求"""
        return await self.test_endpoint("PUT", url, expected_status, json_data, **kwargs)

    async def delete(self, url: str, expected_status: int = 200, **kwargs) -> Response:
        """DELETE请求"""
        return await self.test_endpoint("DELETE", url, expected_status, **kwargs)


@pytest.fixture
async def api_test_client(client: AsyncClient):
    """创建API测试客户端"""
    return APITestClient(client)


def assert_json_structure(response: Response, expected_keys: list):
    """断言JSON响应包含期望的键"""
    json_data = response.json()
    missing_keys = set(expected_keys) - set(json_data.keys())
    assert not missing_keys, f"Missing keys in response: {missing_keys}"


def assert_error_response(response: Response, expected_error_type: str):
    """断言错误响应格式"""
    json_data = response.json()
    assert "detail" in json_data or "error" in json_data, "Error response missing detail/error field"


def assert_pagination(response: Response):
    """断言分页响应格式"""
    json_data = response.json()
    required_keys = ["items", "total", "page", "size"]
    missing_keys = set(required_keys) - set(json_data.keys())
    assert not missing_keys, f"Missing pagination keys: {missing_keys}"
