"""
WebSocket连接管理器
管理客户端WebSocket连接、订阅和消息分发
"""
import asyncio
import json
import logging
from typing import Dict, Set, List, Optional, Any
from datetime import datetime
import uuid

from fastapi import WebSocket, WebSocketDisconnect
from app.core.redis_client import cache_get_json, cache_set

logger = logging.getLogger(__name__)


class SentimentConnectionManager:
    """
    WebSocket连接管理器
    负责管理客户端连接、订阅关系和消息分发
    """

    def __init__(self):
        """初始化连接管理器"""
        # 活跃连接 {client_id: WebSocket}
        self.active_connections: Dict[str, WebSocket] = {}

        # 币种订阅关系 {symbol: Set[client_id]}
        self.symbol_subscriptions: Dict[str, Set[str]] = {}

        # 客户端订阅的币种 {client_id: Set[symbol]}
        self.client_subscriptions: Dict[str, Set[str]] = {}

        # 连接元数据 {client_id: connection_info}
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}

        # 统计信息
        self.stats = {
            "total_connections": 0,
            "active_connections": 0,
            "total_subscriptions": 0
        }

    async def connect(self, websocket: WebSocket, client_id: Optional[str] = None) -> str:
        """
        接受新的WebSocket连接

        Args:
            websocket: WebSocket连接对象
            client_id: 客户端ID，如果未提供则自动生成

        Returns:
            str: 客户端ID
        """
        await websocket.accept()

        if not client_id:
            client_id = str(uuid.uuid4())

        # 记录连接
        self.active_connections[client_id] = websocket
        self.client_subscriptions[client_id] = set()

        # 记录连接元数据
        self.connection_metadata[client_id] = {
            "connected_at": datetime.utcnow().isoformat(),
            "last_ping": datetime.utcnow().isoformat(),
            "user_agent": websocket.headers.get("user-agent", "unknown"),
            "remote_addr": websocket.client.host if websocket.client else "unknown"
        }

        # 更新统计
        self.stats["total_connections"] += 1
        self.stats["active_connections"] = len(self.active_connections)

        logger.info(f"WebSocket客户端已连接: {client_id}")

        # 发送连接确认
        await self.send_to_client(client_id, {
            "type": "connection_established",
            "client_id": client_id,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "WebSocket连接已建立"
        })

        return client_id

    async def disconnect(self, client_id: str):
        """
        断开客户端连接

        Args:
            client_id: 客户端ID
        """
        if client_id not in self.active_connections:
            return

        # 获取客户端订阅的币种
        subscribed_symbols = self.client_subscriptions.get(client_id, set())

        # 清理订阅关系
        for symbol in subscribed_symbols:
            self.unsubscribe_symbol(client_id, symbol)

        # 清理连接信息
        del self.active_connections[client_id]
        if client_id in self.client_subscriptions:
            del self.client_subscriptions[client_id]
        if client_id in self.connection_metadata:
            del self.connection_metadata[client_id]

        # 更新统计
        self.stats["active_connections"] = len(self.active_connections)

        logger.info(f"WebSocket客户端已断开: {client_id}")

    async def subscribe_symbol(self, client_id: str, symbol: str) -> bool:
        """
        订阅币种情绪数据

        Args:
            client_id: 客户端ID
            symbol: 币种符号

        Returns:
            bool: 订阅是否成功
        """
        if client_id not in self.active_connections:
            logger.warning(f"客户端 {client_id} 未连接，无法订阅 {symbol}")
            return False

        symbol = symbol.upper()

        # 添加订阅关系
        if symbol not in self.symbol_subscriptions:
            self.symbol_subscriptions[symbol] = set()

        self.symbol_subscriptions[symbol].add(client_id)
        self.client_subscriptions[client_id].add(symbol)

        # 更新统计
        self.stats["total_subscriptions"] = sum(
            len(subscribers) for subscribers in self.symbol_subscriptions.values()
        )

        logger.info(f"客户端 {client_id} 已订阅 {symbol}")

        # 发送订阅确认
        await self.send_to_client(client_id, {
            "type": "subscription_confirmed",
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"已订阅 {symbol} 实时情绪数据"
        })

        return True

    async def unsubscribe_symbol(self, client_id: str, symbol: str) -> bool:
        """
        取消订阅币种情绪数据

        Args:
            client_id: 客户端ID
            symbol: 币种符号

        Returns:
            bool: 取消订阅是否成功
        """
        symbol = symbol.upper()

        # 清理币种订阅
        if symbol in self.symbol_subscriptions:
            self.symbol_subscriptions[symbol].discard(client_id)
            if not self.symbol_subscriptions[symbol]:
                del self.symbol_subscriptions[symbol]

        # 清理客户端订阅
        if client_id in self.client_subscriptions:
            self.client_subscriptions[client_id].discard(symbol)

        # 更新统计
        self.stats["total_subscriptions"] = sum(
            len(subscribers) for subscribers in self.symbol_subscriptions.values()
        )

        logger.info(f"客户端 {client_id} 已取消订阅 {symbol}")

        # 发送取消订阅确认
        await self.send_to_client(client_id, {
            "type": "unsubscription_confirmed",
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"已取消订阅 {symbol}"
        })

        return True

    async def send_to_client(self, client_id: str, data: Dict[str, Any]) -> bool:
        """
        发送消息给指定客户端

        Args:
            client_id: 客户端ID
            data: 要发送的数据

        Returns:
            bool: 发送是否成功
        """
        if client_id not in self.active_connections:
            return False

        try:
            websocket = self.active_connections[client_id]
            await websocket.send_text(json.dumps(data))
            return True
        except Exception as e:
            logger.error(f"发送消息给客户端 {client_id} 失败: {e}")
            # 连接可能已断开，清理连接
            await self.disconnect(client_id)
            return False

    async def broadcast_to_subscribers(self, symbol: str, data: Dict[str, Any]) -> int:
        """
        向订阅指定币种的所有客户端广播消息

        Args:
            symbol: 币种符号
            data: 要广播的数据

        Returns:
            int: 成功发送的客户端数量
        """
        symbol = symbol.upper()

        if symbol not in self.symbol_subscriptions:
            return 0

        subscribers = self.symbol_subscriptions[symbol].copy()
        success_count = 0

        # 并发发送给所有订阅者
        tasks = []
        for client_id in subscribers:
            task = self.send_to_client(client_id, data)
            tasks.append((client_id, task))

        if tasks:
            results = await asyncio.gather(
                *[task for _, task in tasks],
                return_exceptions=True
            )

            for (client_id, _), success in zip(tasks, results):
                if success is True:
                    success_count += 1
                else:
                    logger.warning(f"广播给客户端 {client_id} 失败")

        logger.debug(f"广播 {symbol} 数据给 {success_count}/{len(subscribers)} 个客户端")
        return success_count

    async def broadcast_to_all(self, data: Dict[str, Any]) -> int:
        """
        向所有连接的客户端广播消息

        Args:
            data: 要广播的数据

        Returns:
            int: 成功发送的客户端数量
        """
        if not self.active_connections:
            return 0

        client_ids = list(self.active_connections.keys())
        success_count = 0

        # 并发发送给所有客户端
        tasks = []
        for client_id in client_ids:
            task = self.send_to_client(client_id, data)
            tasks.append((client_id, task))

        if tasks:
            results = await asyncio.gather(
                *[task for _, task in tasks],
                return_exceptions=True
            )

            for (client_id, _), success in zip(tasks, results):
                if success is True:
                    success_count += 1
                else:
                    logger.warning(f"广播给客户端 {client_id} 失败")

        logger.debug(f"广播数据给 {success_count}/{len(client_ids)} 个客户端")
        return success_count

    def get_client_subscriptions(self, client_id: str) -> List[str]:
        """
        获取客户端订阅的币种列表

        Args:
            client_id: 客户端ID

        Returns:
            List[str]: 订阅的币种列表
        """
        return list(self.client_subscriptions.get(client_id, []))

    def get_symbol_subscribers(self, symbol: str) -> List[str]:
        """
        获取订阅指定币种的客户端列表

        Args:
            symbol: 币种符号

        Returns:
            List[str]: 订阅的客户端ID列表
        """
        return list(self.symbol_subscriptions.get(symbol.upper(), []))

    def get_connection_stats(self) -> Dict[str, Any]:
        """
        获取连接统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            **self.stats,
            "symbol_count": len(self.symbol_subscriptions),
            "popular_symbols": sorted(
                [(symbol, len(subscribers))
                 for symbol, subscribers in self.symbol_subscriptions.items()],
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }

    async def ping_all_clients(self) -> int:
        """
        向所有客户端发送ping消息

        Returns:
            int: 成功发送的客户端数量
        """
        ping_data = {
            "type": "ping",
            "timestamp": datetime.utcnow().isoformat()
        }
        return await self.broadcast_to_all(ping_data)

    async def cleanup_inactive_connections(self, timeout_minutes: int = 30):
        """
        清理不活跃的连接

        Args:
            timeout_minutes: 超时时间（分钟）
        """
        now = datetime.utcnow()
        inactive_clients = []

        for client_id, metadata in self.connection_metadata.items():
            last_ping = datetime.fromisoformat(metadata["last_ping"])
            if (now - last_ping).total_seconds() > timeout_minutes * 60:
                inactive_clients.append(client_id)

        for client_id in inactive_clients:
            logger.info(f"清理不活跃连接: {client_id}")
            await self.disconnect(client_id)

        if inactive_clients:
            logger.info(f"清理了 {len(inactive_clients)} 个不活跃连接")


# 全局连接管理器实例
connection_manager = SentimentConnectionManager()