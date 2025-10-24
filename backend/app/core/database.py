"""
数据库连接模块
使用 SQLAlchemy 2.0 异步引擎连接 PostgreSQL
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.core.config import settings


# 创建异步引擎
# 注意：DATABASE_URL 需要使用 postgresql+asyncpg:// 协议
database_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(
    database_url,
    echo=settings.DEBUG,  # 调试模式下输出SQL日志
    future=True,
    pool_pre_ping=True,  # 连接池预检查
    poolclass=NullPool if settings.ENVIRONMENT == "test" else None,  # 测试环境不使用连接池
)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# 声明式基类
class Base(DeclarativeBase):
    """SQLAlchemy声明式基类"""
    pass


# 依赖注入：获取数据库会话
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI依赖项，用于获取数据库会话

    使用方法:
    @app.get("/items")
    async def read_items(db: AsyncSession = Depends(get_db)):
        result = await db.execute(select(Item))
        return result.scalars().all()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# 初始化数据库（创建所有表）
async def init_db() -> None:
    """
    初始化数据库，创建所有表
    仅在开发环境使用，生产环境应使用 Alembic 迁移
    """
    async with engine.begin() as conn:
        # 导入所有模型，确保它们被注册到 Base.metadata
        from app.models import project, snapshot, report, conversation  # noqa: F401

        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)


# 关闭数据库连接
async def close_db() -> None:
    """关闭数据库引擎"""
    await engine.dispose()
