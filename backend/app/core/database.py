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
from sqlalchemy import text

from app.core.config import settings
from app.core.db_middleware import setup_query_monitoring, setup_pool_monitoring


# 创建异步引擎
# 注意：DATABASE_URL 需要使用 postgresql+asyncpg:// 协议
database_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# 连接池配置
pool_config = {
    "pool_size": settings.DATABASE_POOL_MIN_SIZE,  # 最小连接数
    "max_overflow": settings.DATABASE_POOL_MAX_SIZE - settings.DATABASE_POOL_MIN_SIZE,  # 最大溢出连接数
    "pool_timeout": settings.DATABASE_POOL_TIMEOUT,  # 获取连接超时
    "pool_recycle": settings.DATABASE_POOL_RECYCLE,  # 连接回收时间
    "pool_pre_ping": True,  # 连接池预检查
}

engine = create_async_engine(
    database_url,
    echo=settings.DATABASE_ECHO or settings.DEBUG,  # 调试模式或配置开启时输出SQL日志
    future=True,
    poolclass=NullPool if settings.ENVIRONMENT == "test" else None,  # 测试环境不使用连接池
    connect_args={
        "timeout": settings.DATABASE_COMMAND_TIMEOUT,  # SQL命令执行超时
        "command_timeout": settings.DATABASE_COMMAND_TIMEOUT,  # asyncpg命令超时
        "server_settings": {
            "application_name": "web3search_backend",  # 应用名称（便于数据库监控）
        }
    },
    **pool_config if settings.ENVIRONMENT != "test" else {},  # 非测试环境应用连接池配置
)

# 设置查询性能监控和连接池监控
if settings.ENVIRONMENT != "test":
    setup_query_monitoring(engine)
    setup_pool_monitoring(engine)

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


def get_async_session():
    """
    获取数据库会话的异步上下文管理器

    用于需要直接使用数据库会话的场景（非FastAPI依赖注入）

    使用方法:
    async with get_async_session() as session:
        result = await session.execute(select(Item))
        await session.commit()

    Returns:
        AsyncSession: 异步数据库会话上下文管理器
    """
    return AsyncSessionLocal()


# 依赖注入：获取数据库会话
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI依赖项，用于获取数据库会话

    带事务超时控制和自动回滚

    使用方法:
    @app.get("/items")
    async def read_items(db: AsyncSession = Depends(get_db)):
        result = await db.execute(select(Item))
        return result.scalars().all()
    """
    async with AsyncSessionLocal() as session:
        try:
            # 设置事务超时（PostgreSQL）
            await session.execute(
                text(f"SET LOCAL statement_timeout = '{int(settings.DATABASE_COMMAND_TIMEOUT * 1000)}'")
            )

            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            # 记录事务失败
            import logging
            logger = logging.getLogger(__name__)
            logger.error(
                "Database transaction failed",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )
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
        from app.models import (  # noqa: F401
            project,
            snapshot,
            report,
            conversation,
            user,
        )

        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)


# 关闭数据库连接
async def close_db() -> None:
    """关闭数据库引擎"""
    await engine.dispose()


# 获取连接池统计信息
def get_pool_stats() -> dict:
    """
    获取数据库连接池统计信息

    Returns:
        dict: 连接池统计数据
    """
    if settings.ENVIRONMENT == "test":
        return {"message": "Test environment uses NullPool"}

    pool = engine.pool
    return {
        "pool_size": pool.size(),  # 当前连接数
        "checked_in": pool.checkedin(),  # 可用连接数
        "checked_out": pool.checkedout(),  # 已使用连接数
        "overflow": pool.overflow(),  # 溢出连接数
        "max_overflow": pool._max_overflow,  # 最大溢出数
        "total_size": pool.size() + pool.overflow(),  # 总连接数
        "timeout": pool._timeout,  # 超时设置
    }


# 健康检查
async def check_database_health() -> dict:
    """
    检查数据库连接健康状态

    Returns:
        dict: 健康状态信息
    """
    import time
    try:
        start_time = time.time()

        # 执行简单查询测试连接
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))

        latency_ms = round((time.time() - start_time) * 1000, 2)

        return {
            "status": "healthy",
            "latency_ms": latency_ms,
            "pool_stats": get_pool_stats(),
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "pool_stats": get_pool_stats() if settings.ENVIRONMENT != "test" else {},
        }
