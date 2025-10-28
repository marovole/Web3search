"""
API v1 router
"""
from fastapi import APIRouter
from app.api.v1 import chat, reports, search, trending, health, metrics, cache

# Create v1 API router
api_router = APIRouter()

# Include routers
api_router.include_router(chat.router, prefix="", tags=["Chat"])
api_router.include_router(reports.router, prefix="", tags=["Reports"])
api_router.include_router(search.router, prefix="", tags=["Search"])
api_router.include_router(trending.router, prefix="", tags=["Trending"])
api_router.include_router(health.router, prefix="", tags=["Health"])
api_router.include_router(metrics.router, prefix="", tags=["Metrics"])
api_router.include_router(cache.router, prefix="", tags=["Cache"])

__all__ = ["api_router"]
