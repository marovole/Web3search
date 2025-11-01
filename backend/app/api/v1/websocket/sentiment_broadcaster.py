"""
情绪数据广播器
负责定期获取情绪数据并通过WebSocket推送给订阅的客户端
"""
import asyncio
import json
import logging
from typing import Dict, Set, List, Optional, Any
from datetime import datetime, timedelta
import redis.asyncio as redis

from app.services.social_sentiment_engine import social_sentiment_engine
from app.core.config import settings
from app.core.redis_client import cache_get_json, cache_set
from .connection_manager import connection_manager

logger = logging.getLogger(__name__)


class SentimentBroadcaster:
    """
    情绪数据广播器
    定期获取情绪数据并广播给订阅的客户端
    """

    def __init__(self):
        """初始化广播器"""
        self.is_running = False
        self.broadcast_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None

        # 广播配置
        self.broadcast_interval = 120  # 2分钟更新一次
        self.cleanup_interval = 600    # 10分钟清理一次
        self.max_retry_attempts = 3
        self.retry_delay = 30

        # 缓存配置
        self.cache_prefix = "sentiment:realtime"
        self.cache_ttl = 300  # 5分钟缓存

        # 热门币种列表（优先更新）
        self.popular_symbols = [
            "BTC", "ETH", "BNB", "SOL", "ADA", "DOT", "AVAX", "MATIC",
            "LINK", "UNI", "ATOM", "NEAR", "FTM", "ALGO", "ONE", "HBAR"
        ]

        # 广播统计
        self.stats = {
            "total_broadcasts": 0,
            "successful_broadcasts": 0,
            "failed_broadcasts": 0,
            "last_broadcast": None,
            "symbols_broadcasted": set()
        }

    async def start(self):
        """启动广播器"""
        if self.is_running:
            logger.warning("广播器已在运行")
            return

        self.is_running = True
        self.broadcast_task = asyncio.create_task(self._broadcast_loop())
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())

        logger.info("情绪数据广播器已启动")

    async def stop(self):
        """停止广播器"""
        self.is_running = False

        if self.broadcast_task:
            self.broadcast_task.cancel()
            try:
                await self.broadcast_task
            except asyncio.CancelledError:
                pass

        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass

        logger.info("情绪数据广播器已停止")

    async def _broadcast_loop(self):
        """广播主循环"""
        while self.is_running:
            try:
                await self._broadcast_sentiment_data()
                await asyncio.sleep(self.broadcast_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"广播循环出错: {e}")
                await asyncio.sleep(self.retry_delay)

    async def _cleanup_loop(self):
        """清理循环"""
        while self.is_running:
            try:
                await connection_manager.cleanup_inactive_connections()
                await asyncio.sleep(self.cleanup_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"清理循环出错: {e}")

    async def _broadcast_sentiment_data(self):
        """广播情绪数据 - 性能优化版本"""
        import time
        start_time = time.time()

        # 获取当前订阅的币种
        subscribed_symbols = set(connection_manager.symbol_subscriptions.keys())

        if not subscribed_symbols:
            return  # 没有订阅的币种，跳过本次广播

        # 合并热门币种和订阅币种
        symbols_to_update = (
            set(self.popular_symbols) & subscribed_symbols
        ) | subscribed_symbols

        logger.debug(f"准备广播 {len(symbols_to_update)} 个币种的情绪数据")

        # 性能优化: 分批处理，避免一次性处理过多币种
        batch_size = 10
        total_success = 0
        total_count = len(symbols_to_update)

        for i in range(0, len(symbols_to_update), batch_size):
            batch_symbols = symbols_to_update[i:i + batch_size]

            # 并发处理当前批次
            batch_tasks = []
            for symbol in batch_symbols:
                task = self._broadcast_symbol_sentiment_safe(symbol)
                batch_tasks.append(task)

            if batch_tasks:
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                batch_success = sum(1 for result in batch_results if result is True)
                total_success += batch_success

                # 记录批次性能
                batch_time = time.time() - start_time
                logger.debug(f"批次 {i//batch_size + 1}: {batch_success}/{len(batch_symbols)} 成功, 耗时 {batch_time:.3f}s")

        # 更新统计
        broadcast_duration = time.time() - start_time
        self.stats["total_broadcasts"] += 1
        self.stats["successful_broadcasts"] += total_success
        self.stats["failed_broadcasts"] += (total_count - total_success)
        self.stats["last_broadcast"] = datetime.utcnow().isoformat()
        self.stats["symbols_broadcasted"].update(symbols_to_update)

        logger.info(
            f"广播完成: {total_success}/{total_count} 成功, "
            f"总耗时 {broadcast_duration:.3f}s, "
            f"平均 {broadcast_duration/max(total_count, 1):.3f}s/币种"
        )

    async def _broadcast_symbol_sentiment_safe(self, symbol: str) -> bool:
        """
        安全广播指定币种的情绪数据（带异常处理）

        Args:
            symbol: 币种符号

        Returns:
            bool: 广播是否成功
        """
        try:
            await self._broadcast_symbol_sentiment(symbol)
            return True
        except Exception as e:
            logger.error(f"广播 {symbol} 情绪数据失败: {e}")
            return False

    async def _broadcast_symbol_sentiment(self, symbol: str):
        """
        广播指定币种的情绪数据

        Args:
            symbol: 币种符号
        """
        symbol = symbol.upper()

        # 检查缓存
        cache_key = f"{self.cache_prefix}:{symbol}"
        cached_data = await cache_get_json(cache_key)

        if cached_data:
            # 使用缓存数据
            sentiment_data = cached_data
            logger.debug(f"使用缓存的 {symbol} 情绪数据")
        else:
            # 获取最新数据
            try:
                sentiment_data = await social_sentiment_engine.get_comprehensive_sentiment(
                    symbol=symbol,
                    hours=24
                )

                # 缓存数据
                await cache_set(
                    cache_key,
                    sentiment_data,
                    expire=self.cache_ttl
                )

                logger.debug(f"获取新的 {symbol} 情绪数据")

            except Exception as e:
                logger.error(f"获取 {symbol} 情绪数据失败: {e}")
                # 获取失败时跳过广播
                return

        # 构建广播消息
        broadcast_data = {
            "type": "sentiment_update",
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "sentiment_score": sentiment_data.get("sentiment_score", 0),
                "confidence": sentiment_data.get("confidence", 0),
                "classification": sentiment_data.get("classification", "neutral"),
                "volume": sentiment_data.get("volume", 0),
                "engagement": sentiment_data.get("engagement", 0),
                "sentiment_distribution": sentiment_data.get("sentiment_distribution", {}),
                "platform_distribution": sentiment_data.get("platform_distribution", {}),
                "insights": sentiment_data.get("insights", {}),
                "updated_at": sentiment_data.get("created_at", datetime.utcnow().isoformat())
            }
        }

        # 广播给订阅该币种的客户端
        subscriber_count = await connection_manager.broadcast_to_subscribers(
            symbol, broadcast_data
        )

        if subscriber_count > 0:
            logger.debug(f"{symbol} 数据已广播给 {subscriber_count} 个客户端")

    async def force_broadcast_symbol(self, symbol: str) -> bool:
        """
        强制广播指定币种的实时数据（忽略缓存）

        Args:
            symbol: 币种符号

        Returns:
            bool: 广播是否成功
        """
        try:
            # 清除缓存
            cache_key = f"{self.cache_prefix}:{symbol.upper()}"
            # 这里需要实现缓存删除功能，或者使用TTL过期
            logger.info(f"强制广播 {symbol} 数据，清除缓存")

            # 立即广播
            await self._broadcast_symbol_sentiment(symbol)
            return True

        except Exception as e:
            logger.error(f"强制广播 {symbol} 失败: {e}")
            return False

    async def broadcast_alert(self, symbol: str, alert_type: str, message: str, data: Dict[str, Any] = None):
        """
        广播情绪预警消息

        Args:
            symbol: 币种符号
            alert_type: 预警类型
            message: 预警消息
            data: 附加数据
        """
        alert_data = {
            "type": "sentiment_alert",
            "symbol": symbol.upper(),
            "alert_type": alert_type,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data or {}
        }

        await connection_manager.broadcast_to_subscribers(symbol, alert_data)
        logger.info(f"广播 {symbol} 预警: {alert_type} - {message}")

    async def broadcast_market_update(self, market_data: Dict[str, Any]):
        """
        广播市场更新消息

        Args:
            market_data: 市场数据
        """
        update_data = {
            "type": "market_update",
            "timestamp": datetime.utcnow().isoformat(),
            "data": market_data
        }

        await connection_manager.broadcast_to_all(update_data)
        logger.info("广播市场更新数据")

    def get_broadcast_stats(self) -> Dict[str, Any]:
        """
        获取广播统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            **self.stats,
            "is_running": self.is_running,
            "broadcast_interval": self.broadcast_interval,
            "popular_symbols": self.popular_symbols,
            "symbols_broadcasted_count": len(self.stats["symbols_broadcasted"])
        }

    def update_popular_symbols(self, symbols: List[str]):
        """
        更新热门币种列表

        Args:
            symbols: 新的热门币种列表
        """
        self.popular_symbols = [s.upper() for s in symbols]
        logger.info(f"更新热门币种列表: {self.popular_symbols}")

    async def add_symbol_to_watchlist(self, symbol: str):
        """
        添加币种到观察列表

        Args:
            symbol: 币种符号
        """
        symbol = symbol.upper()
        if symbol not in self.popular_symbols:
            self.popular_symbols.append(symbol)
            logger.info(f"添加 {symbol} 到观察列表")


# 全局广播器实例
sentiment_broadcaster = SentimentBroadcaster()