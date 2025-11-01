"""
WebSocket消息处理器
处理客户端发送的各种WebSocket消息
"""
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect
from .connection_manager import connection_manager
from .sentiment_broadcaster import sentiment_broadcaster

logger = logging.getLogger(__name__)


class WebSocketMessageHandler:
    """
    WebSocket消息处理器
    处理客户端发送的各种消息类型
    """

    def __init__(self):
        """初始化消息处理器"""
        self.handlers = {
            "subscribe": self._handle_subscribe,
            "unsubscribe": self._handle_unsubscribe,
            "ping": self._handle_ping,
            "get_status": self._handle_get_status,
            "get_subscriptions": self._handle_get_subscriptions,
            "force_update": self._handle_force_update,
        }

    async def handle_message(
        self,
        websocket: WebSocket,
        client_id: str,
        message: str
    ) -> Optional[Dict[str, Any]]:
        """
        处理客户端消息

        Args:
            websocket: WebSocket连接
            client_id: 客户端ID
            message: 客户端消息

        Returns:
            Optional[Dict[str, Any]]: 响应消息
        """
        try:
            data = json.loads(message)
            message_type = data.get("type")

            if not message_type:
                await self._send_error(client_id, "消息类型不能为空")
                return None

            handler = self.handlers.get(message_type)
            if not handler:
                await self._send_error(client_id, f"不支持的消息类型: {message_type}")
                return None

            # 调用对应的处理器
            response = await handler(client_id, data)
            return response

        except json.JSONDecodeError:
            await self._send_error(client_id, "消息格式错误，必须是有效的JSON")
        except Exception as e:
            logger.error(f"处理消息失败: {e}")
            await self._send_error(client_id, f"处理消息时发生错误: {str(e)}")

        return None

    async def _handle_subscribe(self, client_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理订阅消息

        Args:
            client_id: 客户端ID
            data: 消息数据

        Returns:
            Dict[str, Any]: 响应数据
        """
        symbol = data.get("symbol")
        if not symbol:
            raise ValueError("币种符号不能为空")

        success = await connection_manager.subscribe_symbol(client_id, symbol)

        if success:
            # 立即发送一次当前数据
            await sentiment_broadcaster.force_broadcast_symbol(symbol)

            return {
                "type": "subscribe_response",
                "success": True,
                "symbol": symbol,
                "message": f"已订阅 {symbol}"
            }
        else:
            return {
                "type": "subscribe_response",
                "success": False,
                "symbol": symbol,
                "message": f"订阅 {symbol} 失败"
            }

    async def _handle_unsubscribe(self, client_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理取消订阅消息

        Args:
            client_id: 客户端ID
            data: 消息数据

        Returns:
            Dict[str, Any]: 响应数据
        """
        symbol = data.get("symbol")
        if not symbol:
            raise ValueError("币种符号不能为空")

        success = await connection_manager.unsubscribe_symbol(client_id, symbol)

        return {
            "type": "unsubscribe_response",
            "success": success,
            "symbol": symbol,
            "message": f"已取消订阅 {symbol}" if success else f"取消订阅 {symbol} 失败"
        }

    async def _handle_ping(self, client_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理ping消息

        Args:
            client_id: 客户端ID
            data: 消息数据

        Returns:
            Dict[str, Any]: 响应数据
        """
        # 更新客户端最后ping时间
        if client_id in connection_manager.connection_metadata:
            connection_manager.connection_metadata[client_id]["last_ping"] = datetime.utcnow().isoformat()

        return {
            "type": "pong",
            "timestamp": datetime.utcnow().isoformat(),
            "client_id": client_id
        }

    async def _handle_get_status(self, client_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理获取状态消息

        Args:
            client_id: 客户端ID
            data: 消息数据

        Returns:
            Dict[str, Any]: 响应数据
        """
        connection_stats = connection_manager.get_connection_stats()
        broadcast_stats = sentiment_broadcaster.get_broadcast_stats()
        client_subscriptions = connection_manager.get_client_subscriptions(client_id)

        return {
            "type": "status_response",
            "timestamp": datetime.utcnow().isoformat(),
            "client_id": client_id,
            "client_subscriptions": client_subscriptions,
            "connection_stats": connection_stats,
            "broadcast_stats": broadcast_stats
        }

    async def _handle_get_subscriptions(self, client_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理获取订阅列表消息

        Args:
            client_id: 客户端ID
            data: 消息数据

        Returns:
            Dict[str, Any]: 响应数据
        """
        subscriptions = connection_manager.get_client_subscriptions(client_id)

        return {
            "type": "subscriptions_response",
            "timestamp": datetime.utcnow().isoformat(),
            "client_id": client_id,
            "subscriptions": subscriptions,
            "count": len(subscriptions)
        }

    async def _handle_force_update(self, client_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理强制更新消息

        Args:
            client_id: 客户端ID
            data: 消息数据

        Returns:
            Dict[str, Any]: 响应数据
        """
        symbol = data.get("symbol")
        if not symbol:
            raise ValueError("币种符号不能为空")

        # 检查客户端是否订阅了该币种
        client_subscriptions = connection_manager.get_client_subscriptions(client_id)
        if symbol.upper() not in client_subscriptions:
            return {
                "type": "force_update_response",
                "success": False,
                "symbol": symbol,
                "message": f"未订阅 {symbol}，无法强制更新"
            }

        success = await sentiment_broadcaster.force_broadcast_symbol(symbol)

        return {
            "type": "force_update_response",
            "success": success,
            "symbol": symbol,
            "message": f"强制更新 {symbol} {'成功' if success else '失败'}"
        }

    async def _send_error(self, client_id: str, error_message: str):
        """
        发送错误消息给客户端

        Args:
            client_id: 客户端ID
            error_message: 错误消息
        """
        error_data = {
            "type": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "message": error_message
        }

        await connection_manager.send_to_client(client_id, error_data)


# 全局消息处理器实例
message_handler = WebSocketMessageHandler()