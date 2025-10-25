"""
API v1 router
"""
from fastapi import APIRouter
from app.api.v1 import chat, reports

# Create v1 API router
api_router = APIRouter()

# Include routers
api_router.include_router(chat.router, prefix="", tags=["Chat"])
api_router.include_router(reports.router, prefix="", tags=["Reports"])

__all__ = ["api_router"]
