"""
FastAPI主应用
Web3 Search - 加密货币AI搜索引擎
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import close_db, init_db
from app.core.redis_client import close_redis


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
    description="专注于加密货币领域的AI驱动研究平台",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


# ================================
# CORS中间件配置
# ================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ================================
# 全局异常处理器
# ================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    """全局异常处理"""
    import traceback

    # 打印详细错误信息（仅开发环境）
    if settings.DEBUG:
        print(f"❌ Error: {exc}")
        traceback.print_exc()

    # 返回用户友好的错误信息
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "服务暂时不可用，请稍后重试",
            "detail": str(exc) if settings.DEBUG else None,
        },
    )


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
    try:
        redis = await get_async_redis()
        await redis.ping()
        health_status["redis"] = "connected"
    except Exception as e:
        health_status["redis"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"

    # 如果有服务不健康，返回503状态码
    status_code = 200 if health_status["status"] == "healthy" else 503

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
async def init_database():
    """
    【临时管理接口】初始化数据库表结构

    警告: 这是一个临时接口，仅用于首次部署时创建表结构
    完成后应该删除此端点

    Returns:
        dict: 初始化结果
    """
    try:
        # 导入所有模型
        from app.models import project, snapshot, report, conversation  # noqa: F401
        from app.core.database import Base

        # 创建所有表
        async with engine.connect() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # 获取创建的表列表
        tables = [table.name for table in Base.metadata.sorted_tables]

        return {
            "success": True,
            "message": "数据库表创建成功",
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
