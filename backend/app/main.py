"""
FastAPI主应用
Web3 Search - 加密货币AI搜索引擎
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import close_db, init_db
from app.core.redis_client import close_redis
from app.core.logging_config import setup_logging
from app.core.monitoring import init_sentry

# 初始化日志系统
setup_logging(level=settings.LOG_LEVEL)

# 初始化Sentry（如果配置了DSN）
init_sentry()


# ================================
# 应用生命周期管理
# ================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用启动和关闭时的生命周期管理

    启动时：
    - 初始化数据库连接
    - 初始化Redis连接
    - （开发环境）创建数据库表

    关闭时：
    - 关闭数据库连接
    - 关闭Redis连接
    """
    # 启动
    print("🚀 Starting Web3 Search API...")

    # 开发环境：初始化数据库表
    if settings.DEBUG:
        print("📊 Initializing database tables...")
        try:
            await init_db()
            print("✅ Database tables created successfully")
        except Exception as e:
            print(f"⚠️ Database initialization warning: {e}")

    # Stage 4: 启动预加载（后台任务，不阻塞API启动）
    import asyncio
    from app.services.startup_preloader import run_startup_preloading

    async def preload_in_background():
        """后台执行预加载"""
        try:
            print("🔥 Starting cache preloading...")
            stats = await run_startup_preloading()
            print(
                f"✅ Cache preloading completed: "
                f"{stats['coins_prewarmed']} coins in {stats['duration_seconds']}s"
            )
        except Exception as e:
            print(f"⚠️  Cache preloading warning: {e}")

    # 创建后台任务（不等待完成）
    asyncio.create_task(preload_in_background())

    print("✅ API is ready!")

    yield  # 应用运行中

    # 关闭
    print("🛑 Shutting down Web3 Search API...")
    await close_db()
    await close_redis()
    print("✅ Cleanup completed")


# ================================
# 创建FastAPI应用实例
# ================================

app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="""
# Web3 Search API

专注于加密货币领域的AI驱动研究平台，提供快速对话和深度研究功能。

## 核心功能

- **Quick Chat**: 3秒内快速回答加密货币相关问题
- **Deep Research**: 15-30秒生成全面的深度研究报告
- **Market Search**: 实时搜索和自动补全功能
- **Trending Analysis**: 多维度市场热点识别

## 数据源

- 🪙 CoinGecko - 价格和市场数据
- ⛓️ Etherscan - 链上数据分析
- 🐦 Twitter - 社交媒体情绪
- 💬 Reddit - 社区讨论
- 📰 CryptoPanic - 新闻聚合

## AI模型

- Claude 3.5 Sonnet (OpenRouter)
- Llama 3.1 70B (OpenRouter)
- 零AI成本（使用免费配额）

## 速率限制

- Quick Chat: 10次/分钟
- Deep Research: 3次/小时
- 其他端点: 30次/分钟

## 文档资源

- [API使用教程](https://github.com/your-repo/docs/API_TUTORIAL.md)
- [错误码参考](https://github.com/your-repo/docs/API_ERRORS.md)
- [认证说明](https://github.com/your-repo/docs/API_AUTH.md)
""",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
    contact={
        "name": "Web3 Search Team",
        "email": "support@web3search.com",
        "url": "https://web3search.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    openapi_tags=[
        {
            "name": "Chat",
            "description": "快速对话接口 - 3秒内响应的AI问答",
        },
        {
            "name": "Research",
            "description": "深度研究接口 - 全面的多维度分析报告",
        },
        {
            "name": "Reports",
            "description": "报告管理 - 查询、检索和分享研究报告",
        },
        {
            "name": "Search",
            "description": "搜索功能 - 加密货币搜索和自动补全",
        },
        {
            "name": "Trending",
            "description": "趋势分析 - 市场热点识别和追踪",
        },
        {
            "name": "Health",
            "description": "健康检查 - 服务状态和依赖监控",
        },
        {
            "name": "Admin",
            "description": "管理接口 - 仅用于开发和维护",
        },
        {
            "name": "Root",
            "description": "根路径 - API基本信息",
        },
    ],
)


# ================================
# 中间件配置
# ================================

# GZip压缩中间件（任务 9.4）
# 自动压缩响应大小 > 1KB 的响应
app.add_middleware(
    GZipMiddleware,
    minimum_size=1024,  # 1KB = 1024 bytes
    compresslevel=6,     # 压缩级别 (1-9)，6 是平衡速度和压缩率的推荐值
)

# CORS中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_origin_regex=r"https://.*\.vercel\.app",  # 支持所有Vercel预览部署
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ================================
# 全局异常处理器
# ================================

from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import Web3SearchException
from app.core.error_handler import (
    web3search_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    generic_exception_handler,
)

# 注册自定义异常处理器
app.add_exception_handler(Web3SearchException, web3search_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)


# ================================
# 健康检查端点
# ================================

@app.get("/health", tags=["Health"])
async def health_check():
    """
    健康检查端点

    Returns:
        dict: 服务健康状态
    """
    from datetime import datetime
    from app.core.redis_client import get_async_redis
    from app.core.database import engine

    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.API_VERSION,
        "environment": settings.ENVIRONMENT,
    }

    # 检查数据库连接
    try:
        from sqlalchemy import text
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        health_status["database"] = "connected"
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"

    # 检查Redis连接
    # 注意：Redis在Render免费计划中不可用是预期行为，不影响API健康状态
    try:
        redis = await get_async_redis()
        await redis.ping()
        health_status["redis"] = "connected"
    except Exception as e:
        health_status["redis"] = f"unavailable: {str(e)}"
        # Redis不可用不影响整体健康状态

    # 检查Celery状态
    # 注意：Celery在Render免费计划中不可用是预期行为（没有Worker）
    try:
        from app.tasks.celery_app import celery_app

        # 检查broker连接（通过ping Redis）
        try:
            redis = await get_async_redis()
            await redis.ping()
            broker_status = "connected"
        except Exception:
            # Redis不可用，Broker离线（预期）
            broker_status = "unavailable"

        # 尝试获取active workers信息
        try:
            # 使用Celery inspect获取worker状态
            inspect = celery_app.control.inspect()
            stats = inspect.stats(timeout=1.0)
            active_workers = len(stats) if stats else 0

            health_status["celery"] = {
                "broker": broker_status,
                "workers": active_workers,
                "status": "running" if active_workers > 0 else "no_workers"
            }

            # 如果没有worker运行，标记为警告（不影响API服务）
            if active_workers == 0:
                health_status["celery"]["warning"] = "No active workers (expected in staging)"
        except Exception:
            # 如果无法获取worker信息，标记为unavailable（不影响API服务）
            health_status["celery"] = {
                "broker": broker_status,
                "workers": "none",
                "status": "unavailable"
            }
    except Exception as e:
        health_status["celery"] = {
            "status": "unavailable",
            "error": str(e)
        }
        # Celery问题不影响API服务的健康状态

    # 只有在关键依赖（数据库）失败时才返回503
    # Redis和Celery不可用在Render免费计划中是预期行为
    status_code = 200 if health_status["status"] != "unhealthy" else 503

    return JSONResponse(content=health_status, status_code=status_code)


@app.get("/", tags=["Root"])
async def root():
    """
    根路径

    Returns:
        dict: API信息
    """
    return {
        "name": settings.API_TITLE,
        "version": settings.API_VERSION,
        "description": "专注于加密货币领域的AI驱动研究平台",
        "docs": "/docs",
        "health": "/health",
    }


@app.post("/admin/init-db", tags=["Admin"])
async def init_database(force: bool = False):
    """
    【临时管理接口】初始化数据库表结构

    警告: 这是一个临时接口，仅用于首次部署时创建表结构
    完成后应该删除此端点

    Args:
        force: 如果为True，先删除所有表再重新创建（危险操作！）

    Returns:
        dict: 初始化结果
    """
    try:
        # 导入所有模型（确保SQLAlchemy注册所有表）
        from app.models import Project, ProjectSnapshot, Report, Conversation, Message  # noqa: F401
        from app.core.database import Base, engine
        from sqlalchemy import text

        # 如果force=True，使用CASCADE彻底删除所有对象
        if force:
            async with engine.begin() as conn:
                # 删除所有表及其依赖对象（索引、约束等）
                await conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
                # 重新创建public schema
                await conn.execute(text("CREATE SCHEMA public"))
                # 恢复public schema的权限
                await conn.execute(text("GRANT ALL ON SCHEMA public TO postgres"))
                await conn.execute(text("GRANT ALL ON SCHEMA public TO public"))
        else:
            # 非force模式：确保public schema存在
            async with engine.begin() as conn:
                await conn.execute(text("CREATE SCHEMA IF NOT EXISTS public"))

        # 创建所有表（在新的连接中，确保看到最新的schema状态）
        await engine.dispose()  # 关闭所有连接池连接
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # 获取创建的表列表
        tables = [table.name for table in Base.metadata.sorted_tables]

        return {
            "success": True,
            "message": "数据库表创建成功" + (" (force模式)" if force else ""),
            "tables": tables
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/admin/tables", tags=["Admin"])
async def list_tables():
    """
    【临时管理接口】列出数据库中的所有表

    Returns:
        dict: 表列表
    """
    try:
        from sqlalchemy import text
        from app.core.database import engine
        async with engine.connect() as conn:
            result = await conn.execute(text(
                "SELECT tablename FROM pg_tables WHERE schemaname='public'"
            ))
            tables = [row[0] for row in result]

        return {
            "success": True,
            "tables": tables
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# ================================
# 速率限制中间件
# ================================

from app.api.middleware.rate_limit import RateLimitMiddleware

app.add_middleware(RateLimitMiddleware)


# ================================
# 注册API路由
# ================================

from app.api.v1 import api_router

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# ================================
# 开发环境调试信息
# ================================

if settings.DEBUG:
    print(f"""
    ╔══════════════════════════════════════════════════╗
    ║  Web3 Search API - Development Mode             ║
    ╠══════════════════════════════════════════════════╣
    ║  API Docs: http://localhost:8000/docs            ║
    ║  ReDoc:    http://localhost:8000/redoc           ║
    ║  Health:   http://localhost:8000/health          ║
    ╚══════════════════════════════════════════════════╝
    """)
