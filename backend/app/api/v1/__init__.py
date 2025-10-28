"""
API v1 router
"""
from fastapi import APIRouter
from app.api.v1 import chat, reports, search, trending, health, metrics, cache

# Create v1 API router
api_router = APIRouter()

# Include routers
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(search.router, prefix="/search", tags=["Search"])
api_router.include_router(trending.router, prefix="/trending", tags=["Trending"])
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(metrics.router, prefix="/metrics", tags=["Metrics"])
api_router.include_router(cache.router, prefix="/cache", tags=["Cache"])

__all__ = ["api_router"]
