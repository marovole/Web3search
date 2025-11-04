"""
集成测试专用配置
提供集成测试所需的fixtures
"""
import pytest
import os
from typing import AsyncGenerator
from httpx import AsyncClient
from unittest.mock import Mock, patch

from app.main import app
from app.core.config import settings


# ================================
# 环境配置 Fixtures
# ================================

@pytest.fixture
def test_env_vars():
    """测试环境变量"""
    return {
        "ENVIRONMENT": "test",
        "API_BASE_URL": "http://test",
        "DATABASE_URL": "sqlite+aiosqlite:///:memory:",
        "REDIS_URL": "redis://localhost:6379/1",
        "OPENROUTER_API_KEY": "test-key",
    }


@pytest.fixture
def mock_redis():
    """Mock Redis客户端"""
    mock = Mock()
    mock.get = Mock(return_value=None)
    mock.set = Mock(return_value=True)
    mock.delete = Mock(return_value=True)
    mock.exists = Mock(return_value=False)
    mock.ping = Mock(return_value=True)
    return mock


@pytest.fixture
def mock_llm_client():
    """Mock LLM客户端"""
    mock = Mock()
    mock.generate = Mock(return_value={
        "content": "This is a test response",
        "model": "qwen3-30b",
        "tokens": {"input": 10, "output": 5}
    })
    return mock


# ================================
# API集成测试 Fixtures
# ================================

@pytest.fixture
async def integration_client() -> AsyncGenerator[AsyncClient, None]:
    """集成测试客户端（不覆盖依赖）"""
    async with AsyncClient(app=app, base_url="http://test", timeout=30.0) as client:
        yield client


@pytest.fixture
def valid_quick_chat_payload():
    """有效的Quick Chat请求负载"""
    return {
        "query": "What is the current price of Bitcoin?",
        "stream": False
    }


@pytest.fixture
def valid_deep_research_payload():
    """有效的Deep Research请求负载"""
    return {
        "project_name": "Ethereum",
        "symbol": "ETH"
    }


@pytest.fixture
def invalid_payload():
    """无效的请求负载"""
    return {
        "invalid_field": "invalid_value"
    }


# ================================
# 环境配置测试 Fixtures
# ================================

@pytest.fixture
def mock_production_env():
    """模拟生产环境配置"""
    with patch.dict(os.environ, {
        "ENVIRONMENT": "production",
        "API_BASE_URL": "https://web3search-api.onrender.com",
        "DATABASE_URL": "postgresql://prod-db",
        "REDIS_URL": "redis://prod-redis:6379/0",
    }):
        yield


@pytest.fixture
def mock_development_env():
    """模拟开发环境配置"""
    with patch.dict(os.environ, {
        "ENVIRONMENT": "development",
        "API_BASE_URL": "http://localhost:8000",
        "DATABASE_URL": "postgresql://localhost/web3search_dev",
        "REDIS_URL": "redis://localhost:6379/0",
    }):
        yield


# ================================
# 数据Mock Fixtures
# ================================

@pytest.fixture
def mock_market_data():
    """Mock市场数据"""
    return {
        "symbol": "BTC",
        "price": 45000.00,
        "market_cap": 850000000000,
        "volume_24h": 25000000000,
        "price_change_24h": 2.5,
        "timestamp": "2025-01-15T10:00:00Z"
    }


@pytest.fixture
def mock_report_data():
    """Mock报告数据"""
    return {
        "id": "test-report-123",
        "project_name": "Bitcoin",
        "report_type": "deep_research",
        "content": "# Bitcoin Deep Research Report\\n\\nTest content...",
        "metadata": {
            "quality_score": 85,
            "generation_time": 25.5,
            "models_used": ["qwen3-235b"]
        },
        "created_at": "2025-01-15T10:00:00Z"
    }
