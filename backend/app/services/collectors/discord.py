"""
Discord数据采集器
集成Discord API，采集Web3项目相关社区的实时讨论数据
"""
import asyncio
import aiohttp
import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
import re
import json

from app.core.config import settings
from app.core.redis_client import cache_get_json, cache_set


logger = logging.getLogger(__name__)


class DiscordCollector:
    """
    Discord数据采集器
    通过Discord Bot API采集公开频道和群组的消息数据
    """

    def __init__(self):
        """初始化Discord采集器"""
        self.base_url = "https://discord.com/api/v10"
        self.bot_token = getattr(settings, 'DISCORD_BOT_TOKEN', None)
        self.web3_channels = self._load_web3_channels()
        self.rate_limiter = DiscordRateLimiter()

        # 会话管理
        self.session: Optional[aiohttp.ClientSession] = None
        self._connected = False

    def _load_web3_channels(self) -> Dict[str, List[str]]:
        """加载Web3相关Discord频道配置"""
        return {
            "general": [
                # 主要加密货币讨论频道
                "discord.gg/crypto",  # 示例频道ID
                "discord.gg/bitcoin",
                "discord.gg/ethereum",
            ],
            "defi": [
                # DeFi相关频道
                "discord.gg/defi",
                "discord.gg/uniswap",
                "discord.gg/compound",
            ],
            "nft": [
                # NFT相关频道
                "discord.gg/nft",
                "discord.gg/opensea",
            ],
            "gaming": [
                # GameFi相关频道
                "discord.gg/axie",
                "discord.gg/sandbox",
            ]
        }

    async def connect(self) -> bool:
        """连接到Discord API"""
        if not self.bot_token:
            logger.warning("Discord bot token未配置")
            return False

        try:
            self.session = aiohttp.ClientSession(
                headers={"Authorization": f"Bot {self.bot_token}"}
            )

            # 验证连接
            response = await self.session.get(f"{self.base_url}/users/@me")
            if response.status == 200:
                self._connected = True
                logger.info("Discord API连接成功")
                return True
            else:
                logger.error(f"Discord API认证失败: {response.status}")
                return False

        except Exception as e:
            logger.error(f"Discord连接失败: {e}")
            return False

    async def disconnect(self):
        """断开Discord连接"""
        if self.session:
            await self.session.close()
            self._connected = False
            logger.info("Discord连接已断开")

    async def collect_channel_messages(
        self,
        channel_id: str,
        hours: int = 24,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        采集指定频道的消息

        Args:
            channel_id: Discord频道ID
            hours: 采集时间范围（小时）
            limit: 最大消息数量

        Returns:
            List[Dict]: 消息列表
        """
        if not self._connected:
            await self.connect()

        if not self._connected:
            return []

        try:
            # 计算时间戳
            since_time = datetime.utcnow() - timedelta(hours=hours)

            messages = []
            last_message_id = None

            # 分页获取消息
            while len(messages) < limit:
                await self.rate_limiter.wait()

                url = f"{self.base_url}/channels/{channel_id}/messages"
                params = {
                    "limit": min(100, limit - len(messages)),  # Discord限制每次最多100条
                    "after": last_message_id if last_message_id else None
                }

                response = await self.session.get(url, params=params)
                if response.status != 200:
                    logger.error(f"获取Discord消息失败: {response.status}")
                    break

                batch_messages = await response.json()
                if not batch_messages:
                    break

                # 过滤时间和相关内容
                for msg in batch_messages:
                    msg_time = datetime.fromisoformat(msg["timestamp"].replace("Z", "+00:00"))
                    if msg_time < since_time:
                        return messages

                    if self._is_crypto_related(msg.get("content", "")):
                        messages.append(self._process_message(msg))

                last_message_id = batch_messages[-1]["id"]

                # 避免API限制
                await asyncio.sleep(0.5)

            logger.info(f"Discord频道{channel_id}采集到{len(messages)}条相关消息")
            return messages

        except Exception as e:
            logger.error(f"Discord消息采集失败: {e}")
            return []

    async def collect_project_mentions(
        self,
        symbols: List[str],
        hours: int = 24
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        采集指定项目的Discord讨论

        Args:
            symbols: 币种符号列表
            hours: 采集时间范围

        Returns:
            Dict[str, List[Dict]]: 按项目分组的消息
        """
        results = {symbol: [] for symbol in symbols}

        # 并发采集所有频道
        tasks = []
        for category, channels in self.web3_channels.items():
            for channel_id in channels:
                task = self._collect_channel_for_symbols(
                    channel_id, symbols, hours
                )
                tasks.append(task)

        if tasks:
            channel_results = await asyncio.gather(*tasks, return_exceptions=True)

            # 合并结果
            for result in channel_results:
                if isinstance(result, dict):
                    for symbol, messages in result.items():
                        results[symbol].extend(messages)

        return results

    async def _collect_channel_for_symbols(
        self,
        channel_id: str,
        symbols: List[str],
        hours: int
    ) -> Dict[str, List[Dict[str, Any]]]:
        """为指定符号采集频道消息"""
        try:
            messages = await self.collect_channel_messages(channel_id, hours)

            results = {symbol: [] for symbol in symbols}

            for msg in messages:
                content = msg["content"].lower()

                for symbol in symbols:
                    # 检查是否提及该币种
                    if (symbol.lower() in content or
                        f"${symbol.lower()}" in content):
                        results[symbol].append(msg)

            return results

        except Exception as e:
            logger.error(f"频道{channel_id}采集失败: {e}")
            return {symbol: [] for symbol in symbols}

    def _is_crypto_related(self, content: str) -> bool:
        """判断消息是否与加密货币相关"""
        crypto_keywords = [
            # 币种相关
            'bitcoin', 'btc', 'ethereum', 'eth', 'bnb', 'bnb chain',
            'solana', 'sol', 'cardano', 'ada', 'polygon', 'matic',
            'avalanche', 'avax', 'chainlink', 'link', 'uniswap', 'uni',
            'defi', 'nft', 'dao', 'web3', 'blockchain', 'crypto',
            # 术语相关
            'bullish', 'bearish', 'hodl', 'fomo', 'fud', 'dump', 'pump',
            'whale', 'ape', 'diamond hands', 'paper hands', 'moon',
            'rekt', 'shitcoin', 'gem', 'rug pull', 'airdrop',
            # 技术相关
            'gas fee', 'smart contract', 'defi', 'yield farming', 'staking',
            'mining', 'proof of work', 'proof of stake', 'layer 2', 'sidechain'
        ]

        content_lower = content.lower()
        return any(keyword in content_lower for keyword in crypto_keywords)

    def _process_message(self, msg: Dict[str, Any]) -> Dict[str, Any]:
        """处理单条消息数据"""
        return {
            "id": msg["id"],
            "channel_id": msg["channel_id"],
            "author": {
                "id": msg["author"]["id"],
                "username": msg["author"]["username"],
                "discriminator": msg["author"]["discriminator"],
                "bot": msg["author"].get("bot", False)
            },
            "content": msg["content"],
            "timestamp": msg["timestamp"],
            "edited_timestamp": msg.get("edited_timestamp"),
            "mentions": len(msg.get("mentions", [])),
            "reactions": self._process_reactions(msg.get("reactions", [])),
            "attachments": len(msg.get("attachments", [])),
            "type": msg["type"],
            "flags": msg.get("flags", 0)
        }

    def _process_reactions(self, reactions: List[Dict]) -> Dict[str, int]:
        """处理消息反应数据"""
        processed = {}
        for reaction in reactions:
            emoji = reaction["emoji"]["name"]
            count = reaction["count"]
            processed[emoji] = count
        return processed

    async def get_channel_info(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """获取频道信息"""
        if not self._connected:
            await self.connect()

        try:
            await self.rate_limiter.wait()
            response = await self.session.get(f"{self.base_url}/channels/{channel_id}")

            if response.status == 200:
                return await response.json()
            else:
                logger.error(f"获取频道信息失败: {response.status}")
                return None

        except Exception as e:
            logger.error(f"获取频道信息异常: {e}")
            return None

    async def get_guild_channels(self, guild_id: str) -> List[Dict[str, Any]]:
        """获取服务器频道列表"""
        if not self._connected:
            await self.connect()

        try:
            await self.rate_limiter.wait()
            response = await self.session.get(f"{self.base_url}/guilds/{guild_id}/channels")

            if response.status == 200:
                channels = await response.json()
                # 只返回文本频道
                return [ch for ch in channels if ch["type"] == 0]
            else:
                logger.error(f"获取服务器频道失败: {response.status}")
                return []

        except Exception as e:
            logger.error(f"获取服务器频道异常: {e}")
            return []


class DiscordRateLimiter:
    """Discord API限流器"""

    def __init__(self):
        self.requests = []
        self.max_requests = 50  # 每分钟最大请求数
        self.window = 60  # 时间窗口（秒）

    async def wait(self):
        """等待限流"""
        now = datetime.utcnow()

        # 清理过期请求
        self.requests = [
            req_time for req_time in self.requests
            if (now - req_time).total_seconds() < self.window
        ]

        # 检查是否超限
        if len(self.requests) >= self.max_requests:
            sleep_time = self.window - (now - self.requests[0]).total_seconds()
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)

        # 记录当前请求
        self.requests.append(now)


# 全局Discord采集器实例
discord_collector = DiscordCollector()