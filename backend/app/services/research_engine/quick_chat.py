"""
Quick Chat 引擎
提供3秒内的快速问答服务
"""
import asyncio
from typing import AsyncGenerator, Dict, Any
from datetime import datetime

from app.services.llm import llm_client, ModelConfig
from app.services.data_aggregator import data_aggregator
from app.services.prompt_manager import prompt_manager


class QuickChatEngine:
    """
    Quick Chat 引擎
    快速响应用户查询，3秒内完成
    """

    def __init__(self):
        """初始化Quick Chat引擎"""
        self.llm_client = llm_client
        self.data_aggregator = data_aggregator
        self.prompt_manager = prompt_manager

    async def chat(
        self,
        query: str,
        stream: bool = False,
    ) -> Dict[str, Any] | AsyncGenerator[str, None]:
        """
        快速对话

        Args:
            query: 用户查询
            stream: 是否流式返回

        Returns:
            Dict 或 AsyncGenerator: 响应结果
        """
        start_time = datetime.utcnow()

        # 检测查询类型
        query_type = self._detect_query_type(query)

        # 根据查询类型处理
        if query_type == "crypto_lookup":
            # 加密货币查询
            symbol = self._extract_symbol(query)
            response = await self._handle_crypto_lookup(query, symbol, stream)
        elif query_type == "market_overview":
            # 市场概览
            response = await self._handle_market_overview(query, stream)
        elif query_type == "general":
            # 一般问答
            response = await self._handle_general_question(query, stream)
        else:
            response = await self._handle_general_question(query, stream)

        # 如果不是流式，添加元数据
        if not stream:
            end_time = datetime.utcnow()
            response_time = (end_time - start_time).total_seconds()

            if isinstance(response, dict):
                response["metadata"] = {
                    "query_type": query_type,
                    "response_time": response_time,
                    "model": ModelConfig.QUICK_CHAT,
                }

        return response

    def _detect_query_type(self, query: str) -> str:
        """
        检测查询类型

        Args:
            query: 用户查询

        Returns:
            str: 查询类型
        """
        query_lower = query.lower()

        # 加密货币查询关键词
        crypto_keywords = ["价格", "市值", "涨跌", "btc", "eth", "币", "代币", "$"]
        if any(kw in query_lower for kw in crypto_keywords):
            return "crypto_lookup"

        # 市场概览关键词
        market_keywords = ["市场", "行情", "热门", "趋势", "排行"]
        if any(kw in query_lower for kw in market_keywords):
            return "market_overview"

        return "general"

    def _extract_symbol(self, query: str) -> str:
        """
        从查询中提取币种符号

        Args:
            query: 用户查询

        Returns:
            str: 币种符号
        """
        # 常见币种符号
        common_symbols = {
            "比特币": "BTC",
            "以太坊": "ETH",
            "币安币": "BNB",
            "瑞波币": "XRP",
            "狗狗币": "DOGE",
            "solana": "SOL",
            "cardano": "ADA",
            "polygon": "MATIC",
            "polkadot": "DOT",
            "avalanche": "AVAX",
        }

        query_lower = query.lower()

        # 检查是否包含中文名称
        for name, symbol in common_symbols.items():
            if name in query_lower:
                return symbol

        # 检查是否包含符号（大写）
        words = query.split()
        for word in words:
            word_upper = word.upper()
            if len(word_upper) >= 2 and len(word_upper) <= 10:
                if word_upper in [
                    "BTC", "ETH", "BNB", "XRP", "DOGE", "SOL", "ADA",
                    "MATIC", "DOT", "AVAX", "LINK", "UNI", "USDT", "USDC"
                ]:
                    return word_upper

        # 默认返回BTC
        return "BTC"

    async def _handle_crypto_lookup(
        self,
        query: str,
        symbol: str,
        stream: bool,
    ) -> Dict[str, Any] | AsyncGenerator[str, None]:
        """
        处理加密货币查询

        Args:
            query: 用户查询
            symbol: 币种符号
            stream: 是否流式返回

        Returns:
            响应结果
        """
        # 快速获取数据
        quick_data = await self.data_aggregator.quick_lookup(symbol)

        # 构建系统提示词
        system_prompt = self.prompt_manager.get_quick_chat_system_prompt()

        # 构建用户消息
        user_message = f"""用户查询: {query}

相关数据:
{quick_data}

请基于上述数据简洁地回答用户的问题。"""

        # 调用LLM
        response = await self.llm_client.quick_chat(
            user_message=user_message,
            system_message=system_prompt,
            stream=stream,
        )

        if stream:
            return response
        else:
            return {
                "content": response["content"],
                "symbol": symbol,
                "data": quick_data,
            }

    async def _handle_market_overview(
        self,
        query: str,
        stream: bool,
    ) -> Dict[str, Any] | AsyncGenerator[str, None]:
        """
        处理市场概览查询

        Args:
            query: 用户查询
            stream: 是否流式返回

        Returns:
            响应结果
        """
        # 获取热门币种
        from app.services.collectors import coingecko_collector

        trending = await coingecko_collector.get_trending_coins(limit=10)

        # 格式化数据
        trending_str = "\n".join([
            f"{i+1}. {coin.get('name')} ({coin.get('symbol')}) - 市值排名第{coin.get('market_cap_rank', 'N/A')}"
            for i, coin in enumerate(trending)
        ])

        # 构建系统提示词
        system_prompt = self.prompt_manager.get_quick_chat_system_prompt()

        # 构建用户消息
        user_message = f"""用户查询: {query}

当前热门币种:
{trending_str}

请简要介绍当前加密货币市场的热门项目和趋势。"""

        # 调用LLM
        response = await self.llm_client.quick_chat(
            user_message=user_message,
            system_message=system_prompt,
            stream=stream,
        )

        if stream:
            return response
        else:
            return {
                "content": response["content"],
                "trending": trending,
            }

    async def _handle_general_question(
        self,
        query: str,
        stream: bool,
    ) -> Dict[str, Any] | AsyncGenerator[str, None]:
        """
        处理一般问答

        Args:
            query: 用户查询
            stream: 是否流式返回

        Returns:
            响应结果
        """
        # 构建系统提示词
        system_prompt = self.prompt_manager.get_quick_chat_system_prompt()

        # 调用LLM
        response = await self.llm_client.quick_chat(
            user_message=query,
            system_message=system_prompt,
            stream=stream,
        )

        if stream:
            return response
        else:
            return {
                "content": response["content"],
            }


# ================================
# 全局实例
# ================================

quick_chat_engine = QuickChatEngine()
