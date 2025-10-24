"""
Pytest配置文件
定义测试fixtures和环境配置
"""
import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings


# ================================
# 测试数据库配置
# ================================

# 使用内存SQLite数据库进行测试
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,
    echo=False,
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ================================
# Event Loop Fixture
# ================================

@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ================================
# Database Fixtures
# ================================

@pytest.fixture(scope="function")
async def db_session():
    """创建测试数据库会话"""
    async with test_engine.begin() as conn:
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        # 清理所有表
        await conn.run_sync(Base.metadata.drop_all)


# ================================
# API Client Fixture
# ================================

@pytest.fixture
async def client(db_session):
    """创建测试客户端"""

    # 覆盖数据库依赖
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    # 清理覆盖
    app.dependency_overrides.clear()


# ================================
# Mock Data Fixtures
# ================================

@pytest.fixture
def mock_quick_chat_request():
    """Mock Quick Chat请求数据"""
    return {
        "query": "BTC现在的价格是多少？",
        "stream": False
    }


@pytest.fixture
def mock_deep_research_request():
    """Mock Deep Research请求数据"""
    return {
        "query": "请深度分析以太坊",
        "symbol": "ETH"
    }


# ================================
# Skip Markers
# ================================

# 跳过需要实际API密钥的测试
skip_if_no_api_key = pytest.mark.skipif(
    not settings.OPENROUTER_API_KEY,
    reason="需要OPENROUTER_API_KEY环境变量"
)

# 跳过需要外部服务的测试
skip_if_no_external_services = pytest.mark.skipif(
    not all([
        settings.COINGECKO_API_KEY,
        settings.TWITTER_BEARER_TOKEN,
        settings.REDDIT_CLIENT_ID,
    ]),
    reason="需要外部API密钥"
)
