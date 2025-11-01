"""
WebSocket API模块
提供实时情绪数据推送服务
"""
from .sentiment_websocket import router
from .connection_manager import connection_manager
from .message_handlers import message_handler
from .sentiment_broadcaster import sentiment_broadcaster
from .performance_monitor import router as performance_router

# 合并路由
from fastapi import APIRouter
websocket_router = APIRouter()
websocket_router.include_router(router)
websocket_router.include_router(performance_router, prefix="/performance", tags=["Performance"])

__all__ = [
    "websocket_router",
    "connection_manager",
    "message_handler",
    "sentiment_broadcaster"
]