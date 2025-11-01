"""
Telegram数据采集器
采集Telegram公开频道和群组中的加密货币讨论、热度、情感
"""
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import httpx

from app.core.config import settings
from app.core.redis_client import cache_get_json, cache_set


class TelegramCollector:
    """
    Telegram Bot API客户端
    提供Telegram公开频道和群组数据采集功能
    """

    def __init__(self):
        """初始化Telegram客户端"""
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.timeout = 30.0

    async def _request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
        cache_ttl: int = 300,
    ) -> Dict[str, Any]:
        """
        发送HTTP请求到Telegram Bot API

        Args:
            endpoint: API端点
            params: 查询参数
            use_cache: 是否使用缓存
            cache_ttl: 缓存时间（秒）

        Returns:
            Dict: API响应数据

        Raises:
            Exception: API请求失败
        """
        url = f"{self.base_url}/{endpoint}"

        # 检查缓存
        cache_key = f"telegram:{endpoint}:{str(params)}"
        if use_cache:
            cached = await cache_get_json(cache_key)
            if cached:
                return cached

        # 发送请求（带重试）
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(url, params=params)

                    if response.status_code == 429:  # Rate limit
                        wait_time = 2 ** attempt
                        print(f"⚠️ Telegram限流，等待{wait_time}秒...")
                        await asyncio.sleep(wait_time)
                        continue

                    response.raise_for_status()
                    data = response.json()

                    if not data.get("ok"):
                        error_msg = data.get("description", "Unknown error")
                        raise Exception(f"Telegram API错误: {error_msg}")

                    # 缓存结果
                    if use_cache:
                        await cache_set(cache_key, data, cache_ttl)

                    return data

            except httpx.HTTPStatusError as e:
                raise Exception(f"Telegram API错误: {e.response.status_code}")

            except Exception as e:
                if attempt < 2:
                    await asyncio.sleep(1)
                    continue
                else:
                    raise Exception(f"Telegram请求失败: {str(e)}")

        raise Exception("Telegram API请求达到最大重试次数")

    # ================================
    # 频道和群组数据采集
    # ================================

    async def get_chat_info(self, chat_id: str) -> Optional[Dict[str, Any]]:
        """
        获取频道或群组信息

        Args:
            chat_id: 频道或群组ID（@username或数字ID）

        Returns:
            Dict: 频道/群组信息
        """
        try:
            data = await self._request(
                "getChat",
                params={"chat_id": chat_id},
                cache_ttl=3600,  # 1小时缓存
            )

            chat = data.get("result", {})
            chat_type = chat.get("type", "")

            return {
                "id": chat.get("id"),
                "type": chat_type,
                "title": chat.get("title"),
                "username": chat.get("username"),
                "description": chat.get("description"),
                "member_count": chat.get("member_count", 0) if chat_type in ["supergroup", "channel"] else 0,
                "is_verified": chat.get("is_verified", False),
                "is_scamm": chat.get("is_scam", False),
                "slow_mode_delay": chat.get("slow_mode_delay", 0),
                "location": chat.get("location"),
                "photo_url": chat.get("photo", {}).get("small_file_id"),
            }

        except Exception as e:
            print(f"⚠️ 获取Telegram聊天信息失败: {e}")
            return None

    async def search_messages(
        self,
        query: str,
        chat_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        搜索消息（由于Telegram Bot API限制，这里模拟搜索功能）

        Args:
            query: 搜索关键词
            chat_id: 限定聊天ID
            limit: 最大结果数
            offset: 偏移量

        Returns:
            List[Dict]: 消息列表
        """
        try:
            # 由于Bot API限制，我们只能获取最近的消息然后进行过滤
            if not chat_id:
                return []  # 需要指定chat_id

            data = await self._request(
                "getChatHistory",
                params={
                    "chat_id": chat_id,
                    "limit": min(limit * 2, 100),  # 获取更多消息用于过滤
                    "offset": offset,
                },
                cache_ttl=60,  # 1分钟缓存
            )

            messages = data.get("result", [])
            
            # 过滤包含查询关键词的消息
            filtered_messages = []
            for message in messages:
                text = message.get("text", "")
                if query.lower() in text.lower():
                    filtered_messages.append(self._format_message(message))

                if len(filtered_messages) >= limit:
                    break

            return filtered_messages

        except Exception as e:
            print(f"⚠️ 搜索Telegram消息失败: {e}")
            return []

    async def get_recent_messages(
        self,
        chat_id: str,
        limit: int = 100,
        hours: int = 24,
    ) -> List[Dict[str, Any]]:
        """
        获取最近的消息

        Args:
            chat_id: 聊天ID
            limit: 最大结果数
            hours: 时间范围（小时）

        Returns:
            List[Dict]: 消息列表
        """
        try:
            # 计算时间偏移
            offset_date = int((datetime.utcnow() - timedelta(hours=hours)).timestamp())

            data = await self._request(
                "getChatHistory",
                params={
                    "chat_id": chat_id,
                    "limit": min(limit, 100),
                    "offset_date": offset_date,
                },
                cache_ttl=300,  # 5分钟缓存
            )

            messages = data.get("result", [])
            return [self._format_message(msg) for msg in messages]

        except Exception as e:
            print(f"⚠️ 获取Telegram最近消息失败: {e}")
            return []

    def _format_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        格式化消息数据

        Args:
            message: 原始消息数据

        Returns:
            Dict: 格式化后的消息
        """
        from_user = message.get("from", {})
        forward_from = message.get("forward_from", {})
        
        return {
            "id": message.get("message_id"),
            "text": message.get("text", ""),
            "date": message.get("date"),
            "edit_date": message.get("edit_date"),
            "views": message.get("views", 0),
            "forwards": message.get("forwards", 0),
            "reply_to_message_id": message.get("reply_to_message", {}).get("message_id"),
            "author": {
                "id": from_user.get("id"),
                "first_name": from_user.get("first_name"),
                "last_name": from_user.get("last_name"),
                "username": from_user.get("username"),
                "is_bot": from_user.get("is_bot", False),
            },
            "forward_from": {
                "id": forward_from.get("id"),
                "first_name": forward_from.get("first_name"),
                "last_name": forward_from.get("last_name"),
                "username": forward_from.get("username"),
            } if forward_from else None,
        }

    # ================================
    # 情感分析和统计
    # ================================

    async def get_crypto_sentiment(
        self,
        symbol: str,
        chat_ids: List[str] = None,
        hours: int = 24,
    ) -> Dict[str, Any]:
        """
        获取加密货币的Telegram情感数据

        Args:
            symbol: 币种符号（如"BTC"）
            chat_ids: 频道/群组ID列表
            hours: 时间范围（小时）

        Returns:
            Dict: 情感统计数据
        """
        # 默认加密货币相关频道列表
        if chat_ids is None:
            chat_ids = [
                "@cryptopumpsignals", "@coinbase", "@binance_official", 
                "@cointelegraph", "@cryptocom", "@coindesk", "@whale_alert_io"
            ]

        all_messages = []
        chat_details = []

        # 并行获取所有频道的消息
        tasks = []
        for chat_id in chat_ids:
            tasks.append(self._get_channel_messages(chat_id, symbol, hours))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"⚠️ 获取 {chat_ids[i]} 消息失败: {result}")
                continue

            messages, chat_info = result
            if messages:
                all_messages.extend(messages)
                chat_details.append({
                    "chat_id": chat_ids[i],
                    "title": chat_info.get("title") if chat_info else "Unknown",
                    "message_count": len(messages),
                    "avg_views": sum(m.get("views", 0) for m in messages) / len(messages)
                })

        if not all_messages:
            return {
                "symbol": symbol,
                "total_messages": 0,
                "total_views": 0,
                "avg_views": 0,
                "active_chats": 0,
                "sentiment_score": 0,
                "chat_details": [],
                "timestamp": datetime.utcnow().isoformat(),
            }

        # 计算统计指标
        total_messages = len(all_messages)
        total_views = sum(m.get("views", 0) for m in all_messages)
        avg_views = total_views / total_messages if total_messages > 0 else 0

        # 情感分析
        sentiment_data = self._analyze_message_sentiment(all_messages, symbol)

        # 找出最受欢迎的消息
        top_message = max(all_messages, key=lambda m: m.get("views", 0) + m.get("forwards", 0))

        return {
            "symbol": symbol,
            "total_messages": total_messages,
            "total_views": total_views,
            "avg_views": round(avg_views, 2),
            "active_chats": len(chat_details),
            "top_message": {
                "text": top_message["text"][:200] + "..." if len(top_message["text"]) > 200 else top_message["text"],
                "views": top_message.get("views", 0),
                "forwards": top_message.get("forwards", 0),
                "date": top_message.get("date"),
            },
            "chat_details": chat_details,
            **sentiment_data,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def _get_channel_messages(
        self, 
        chat_id: str, 
        symbol: str, 
        hours: int
    ) -> tuple:
        """
        获取特定频道的消息

        Args:
            chat_id: 频道ID
            symbol: 币种符号
            hours: 时间范围

        Returns:
            tuple: (消息列表, 频道信息)
        """
        try:
            # 获取频道信息
            chat_info = await self.get_chat_info(chat_id)
            
            # 获取最近消息
            messages = await self.get_recent_messages(chat_id, limit=100, hours=hours)
            
            # 过滤包含币种符号的消息
            symbol_lower = symbol.lower()
            filtered_messages = [
                msg for msg in messages 
                if symbol_lower in msg["text"].lower()
            ]
            
            return filtered_messages, chat_info

        except Exception as e:
            return [], None

    def _analyze_message_sentiment(
        self, 
        messages: List[Dict[str, Any]], 
        symbol: str
    ) -> Dict[str, Any]:
        """
        分析消息的情感

        Args:
            messages: 消息列表
            symbol: 币种符号

        Returns:
            Dict: 情感分析结果
        """
        if not messages:
            return {
                "sentiment_score": 0,
                "positive_messages": 0,
                "negative_messages": 0,
                "neutral_messages": 0,
                "sentiment_distribution": {"positive": 0, "negative": 0, "neutral": 0}
            }

        # Telegram特定的情感关键词
        telegram_keywords = {
            "positive": [
                # 价格相关
                "🚀", "📈", "💰", "🎯", "🌙", "bull", "pump", "buy", "long", "up",
                "moon", "rocket", "gain", "profit", "strong", "good", "great", "excellent",
                # 技术相关
                "launch", "upgrade", "partnership", "adoption", "mainnet", "staking", "yield",
                # 表情符号
                "👍", "😊", "🔥", "💎", "🌟", "✅", "💪", "🏆"
            ],
            "negative": [
                # 价格相关
                "📉", "🕳️", "bear", "dump", "sell", "short", "down", "loss", "crash", "fall",
                "scam", "hack", "risk", "bad", "terrible", "awful", "poor",
                # 技术相关
                "bug", "glitch", "delay", "issue", "problem", "vulnerability",
                # 表情符号
                "👎", "😢", "⚠️", "❌", "🚫", "💔", "😡", "😠"
            ],
            "neutral": [
                "price", "market", "analysis", "chart", "news", "update", "info",
                "data", "report", "trading", "volume", "resistance", "support"
            ]
        }

        positive_messages = 0
        negative_messages = 0
        neutral_messages = 0
        sentiment_scores = []

        for message in messages:
            text = message["text"].lower()
            
            # 计算情感得分
            pos_score = sum(1 for kw in telegram_keywords["positive"] if kw in text)
            neg_score = sum(1 for kw in telegram_keywords["negative"] if kw in text)
            
            # 考虑消息浏览量和转发量的权重
            views = message.get("views", 0)
            forwards = message.get("forwards", 0)
            engagement_weight = min(views / 1000 + forwards / 100, 1.0)
            
            if pos_score > neg_score:
                positive_messages += 1
                score = min(1.0, (pos_score - neg_score) / max(pos_score + neg_score, 1))
            elif neg_score > pos_score:
                negative_messages += 1
                score = max(-1.0, -(neg_score - pos_score) / max(pos_score + neg_score, 1))
            else:
                neutral_messages += 1
                score = 0
            
            # 应用参与度权重
            weighted_score = score * (1 + engagement_weight)
            sentiment_scores.append(weighted_score)

        # 计算整体情感得分
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0

        return {
            "sentiment_score": round(avg_sentiment, 3),
            "positive_messages": positive_messages,
            "negative_messages": negative_messages,
            "neutral_messages": neutral_messages,
            "sentiment_distribution": {
                "positive": round(positive_messages / len(messages) * 100, 1),
                "negative": round(negative_messages / len(messages) * 100, 1),
                "neutral": round(neutral_messages / len(messages) * 100, 1)
            }
        }

    async def get_trending_crypto_topics(
        self,
        chat_ids: List[str] = None,
        limit: int = 20,
        hours: int = 24,
    ) -> List[Dict[str, Any]]:
        """
        获取热门加密货币话题

        Args:
            chat_ids: 频道/群组ID列表
            limit: 最大结果数
            hours: 时间范围（小时）

        Returns:
            List[Dict]: 热门话题列表
        """
        if chat_ids is None:
            chat_ids = [
                "@cryptopumpsignals", "@coinbase", "@binance_official", 
                "@cointelegraph", "@cryptocom"
            ]

        all_messages = []

        # 并行获取所有频道的消息
        tasks = []
        for chat_id in chat_ids:
            tasks.append(self.get_recent_messages(chat_id, limit=50, hours=hours))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                continue
            all_messages.extend(result)

        # 分析话题热度
        crypto_symbols = ["btc", "eth", "bitcoin", "ethereum", "bnb", "sol", "ada", "dot", "avax"]
        trending_topics = []

        for message in all_messages:
            text = message["text"].lower()
            mentioned_symbols = [symbol for symbol in crypto_symbols if symbol in text]
            
            if mentioned_symbols:
                trending_topics.append({
                    "text": message["text"][:200] + "..." if len(message["text"]) > 200 else message["text"],
                    "views": message.get("views", 0),
                    "forwards": message.get("forwards", 0),
                    "mentioned_symbols": mentioned_symbols,
                    "engagement": message.get("views", 0) + message.get("forwards", 0),
                    "date": message.get("date"),
                })

        # 按参与度排序
        trending_topics.sort(key=lambda x: x["engagement"], reverse=True)

        return trending_topics[:limit]


# ================================
# 全局实例
# ================================

telegram_collector = TelegramCollector()
