"""
API v1ï1
Z@	v1H,„APIï¹
"""
from fastapi import APIRouter
from app.api.v1 import chat, reports

# úv1ï1h
api_router = APIRouter()

# +@	Pï1
api_router.include_router(chat.router, prefix="", tags=["Chat"])
api_router.include_router(reports.router, prefix="", tags=["Reports"])

__all__ = ["api_router"]
