"""
数据聚合器
从多个数据源并行采集数据，汇总为结构化格式
"""
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

from app.services.collectors import (
    coingecko_collector,
    etherscan_collector,
    bscscan_collector,
    twitter_collector,
    reddit_collector,
    cryptopanic_collector,
)
from app.services.collectors.coingecko import CoinGeckoAPIError


class DataAggregator:
    """
    数据聚合器
    负责协调多个数据采集器，并行获取和汇总数据
    """

    def __init__(self):
        """初始化数据聚合器"""
        pass

    # ================================
    # 核心聚合方法
    # ================================

    async def aggregate_project_data(
        self,
        symbol: str,
        coingecko_id: Optional[str] = None,
        timeout: float = 30.0,
    ) -> Dict[str, Any]:
        """
        聚合项目的全部数据（任务 9.3 优化）

        实现功能：
        - 并行调用多个数据源（asyncio.gather）
        - 超时控制（单个请求10s，总计30s）
        - 部分成功处理（某些数据源失败不影响整体）

        Args:
            symbol: 币种符号（如"BTC"）
            coingecko_id: CoinGecko ID（如"bitcoin"）
            timeout: 总超时时间（秒），默认30s

        Returns:
            Dict: 聚合后的数据
        """
        # 如果没有提供coingecko_id，尝试搜索
        if not coingecko_id:
            coingecko_id = await self._resolve_coingecko_id(symbol)

        if not coingecko_id:
            return {
                "error": f"无法找到 {symbol} 的项目信息",
                "symbol": symbol,
            }

        # 并行获取多个数据源，带超时控制（任务 9.3）
        try:
            (
                project_info,
                market_data,
                onchain_data,
                social_data,
                news_data,
            ) = await asyncio.wait_for(
                asyncio.gather(
                    self._get_project_info(coingecko_id),
                    self._get_market_data(coingecko_id),
                    self._get_onchain_data(coingecko_id),
                    self._get_social_data(symbol),
                    self._get_news_data(symbol),
                    return_exceptions=True,  # 部分成功处理
                ),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            # 总超时，返回部分数据
            return {
                "error": f"数据获取超时（{timeout}秒）",
                "symbol": symbol.upper(),
                "coingecko_id": coingecko_id,
                "timestamp": datetime.utcnow().isoformat(),
            }

        # 处理异常结果（部分成功处理）
        if isinstance(project_info, Exception):
            project_info = {"error": str(project_info)}
        if isinstance(market_data, Exception):
            market_data = {"error": str(market_data)}
        if isinstance(onchain_data, Exception):
            onchain_data = {"error": str(onchain_data)}
        if isinstance(social_data, Exception):
            social_data = {"error": str(social_data)}
        if isinstance(news_data, Exception):
            news_data = {"error": str(news_data)}

        return {
            "symbol": symbol.upper(),
            "coingecko_id": coingecko_id,
            "project_info": project_info,
            "market_data": market_data,
            "onchain_data": onchain_data,
            "social_data": social_data,
            "news_data": news_data,
            "timestamp": datetime.utcnow().isoformat(),
        }

    # ================================
    # 私有方法：数据获取
    # ================================

    async def _resolve_coingecko_id(self, symbol: str) -> Optional[str]:
        """
        通过符号查找CoinGecko ID

        Args:
            symbol: 币种符号

        Returns:
            Optional[str]: CoinGecko ID
        """
        try:
            results = await coingecko_collector.search_coins(symbol)
            if results and len(results) > 0:
                # 返回第一个匹配结果
                return results[0].get("coingecko_id")
            return None
        except Exception as e:
            print(f"⚠️ 搜索CoinGecko ID失败: {e}")
            return None

    async def _get_project_info(self, coingecko_id: str) -> Dict[str, Any]:
        """获取项目基本信息"""
        try:
            info = await coingecko_collector.get_coin_info(coingecko_id)
            return info
        except Exception as e:
            print(f"⚠️ 获取项目信息失败: {e}")
            return {}

    async def _get_market_data(self, coingecko_id: str) -> Dict[str, Any]:
        """获取市场数据"""
        try:
            market_data = await coingecko_collector.get_coin_market_data(coingecko_id)

            # 验证数据有效性，避免返回虚假的 $0 价格
            if not market_data or market_data.get("price_usd") is None:
                raise CoinGeckoAPIError(f"未能获取 {coingecko_id} 的实时价格")

            # 获取历史数据（7天）
            historical_data = await coingecko_collector.get_market_chart(
                coingecko_id,
                days=7,
                interval="daily",
            )

            return {
                "current": market_data,
                "historical": historical_data,
            }
        except Exception as e:
            print(f"⚠️ 获取市场数据失败: {e}")
            # 重新抛出异常，让上层处理
            raise

    async def _get_onchain_data(self, coingecko_id: str) -> Dict[str, Any]:
        """获取链上数据"""
        try:
            # 先获取合约地址
            info = await coingecko_collector.get_coin_info(coingecko_id)
            contract_addresses = info.get("contract_addresses", {})

            onchain_results = {}

            # 如果有以太坊合约地址
            if "ethereum" in contract_addresses:
                eth_address = contract_addresses["ethereum"]
                eth_data = await etherscan_collector.get_token_onchain_data(eth_address)
                onchain_results["ethereum"] = eth_data

            # 如果有BSC合约地址
            if "binance-smart-chain" in contract_addresses:
                bsc_address = contract_addresses["binance-smart-chain"]
                bsc_data = await bscscan_collector.get_token_onchain_data(bsc_address)
                onchain_results["bsc"] = bsc_data

            return onchain_results

        except Exception as e:
            print(f"⚠️ 获取链上数据失败: {e}")
            return {}

    async def _get_social_data(self, symbol: str) -> Dict[str, Any]:
        """获取社交媒体数据"""
        try:
            # 并行获取Twitter和Reddit数据
            twitter_data, reddit_data = await asyncio.gather(
                twitter_collector.get_crypto_sentiment(symbol, hours=24),
                reddit_collector.get_crypto_sentiment(symbol, hours=24),
                return_exceptions=True,
            )

            # 处理异常
            if isinstance(twitter_data, Exception):
                twitter_data = {"error": str(twitter_data)}
            if isinstance(reddit_data, Exception):
                reddit_data = {"error": str(reddit_data)}

            # 计算综合情感得分
            twitter_score = twitter_data.get("sentiment_score", 0)
            reddit_score = reddit_data.get("sentiment_score", 0)
            overall_sentiment = (twitter_score + reddit_score) / 2

            return {
                "twitter": twitter_data,
                "reddit": reddit_data,
                "overall_sentiment": round(overall_sentiment, 2),
            }

        except Exception as e:
            print(f"⚠️ 获取社交数据失败: {e}")
            return {}

    async def _get_news_data(self, symbol: str) -> Dict[str, Any]:
        """获取新闻数据"""
        try:
            # 获取币种相关新闻和市场情绪
            news, sentiment = await asyncio.gather(
                cryptopanic_collector.get_currency_news(symbol),
                cryptopanic_collector.analyze_currency_sentiment(symbol),
                return_exceptions=True,
            )

            # 处理异常
            if isinstance(news, Exception):
                news = []
            if isinstance(sentiment, Exception):
                sentiment = {}

            return {
                "recent_news": news[:10],  # 最近10条新闻
                "sentiment": sentiment,
            }

        except Exception as e:
            print(f"⚠️ 获取新闻数据失败: {e}")
            return {}

    # ================================
    # 格式化方法
    # ================================

    def format_for_llm(self, aggregated_data: Dict[str, Any]) -> Dict[str, str]:
        """
        将聚合数据格式化为适合LLM处理的字符串格式

        Args:
            aggregated_data: 聚合后的数据

        Returns:
            Dict[str, str]: 格式化后的数据字典
        """
        symbol = aggregated_data.get("symbol", "Unknown")
        project_info = aggregated_data.get("project_info", {})
        market_data = aggregated_data.get("market_data", {})
        onchain_data = aggregated_data.get("onchain_data", {})
        social_data = aggregated_data.get("social_data", {})
        news_data = aggregated_data.get("news_data", {})

        # 格式化项目信息
        project_info_str = f"""
**项目名称**: {project_info.get('name', 'N/A')}
**代币符号**: {project_info.get('symbol', 'N/A')}
**所属类别**: {', '.join(project_info.get('categories', []))}
**主要区块链**: {project_info.get('blockchain', 'N/A')}
**官网**: {project_info.get('website', 'N/A')}
**简介**: {project_info.get('description', 'N/A')[:500]}...
"""

        # 格式化市场数据
        current_market = market_data.get("current", {})
        market_data_str = f"""
**当前价格**: ${current_market.get('price_usd', 0):.4f}
**市值**: ${current_market.get('market_cap', 0):,.0f} (排名第{current_market.get('market_cap_rank', 'N/A')})
**24h交易量**: ${current_market.get('total_volume_24h', 0):,.0f}
**24h价格变化**: {current_market.get('price_change_24h', 0):.2f}%
**7日价格变化**: {current_market.get('price_change_7d', 0):.2f}%
**30日价格变化**: {current_market.get('price_change_30d', 0):.2f}%
**流通供应量**: {current_market.get('circulating_supply', 0):,.0f}
**总供应量**: {current_market.get('total_supply', 0):,.0f}
**最大供应量**: {current_market.get('max_supply', 'N/A')}
"""

        # 格式化链上数据
        onchain_str_parts = []
        for chain, data in onchain_data.items():
            if not isinstance(data, dict):
                continue
            onchain_str_parts.append(f"""
**{chain.capitalize()}链数据**:
- 24h交易数: {data.get('transaction_count_24h', 'N/A')}
- 活跃地址: {data.get('active_addresses_24h', 'N/A')}
- 合约验证: {'是' if data.get('is_verified') else '否'}
""")
        onchain_data_str = "\n".join(onchain_str_parts) or "暂无链上数据"

        # 格式化社交数据
        twitter = social_data.get("twitter", {})
        reddit = social_data.get("reddit", {})
        social_data_str = f"""
**Twitter**:
- 24h提及数: {twitter.get('mention_count', 0)}
- 平均参与度: {twitter.get('avg_engagement', 0)}
- 情感得分: {twitter.get('sentiment_score', 0):.2f}

**Reddit**:
- 24h帖子数: {reddit.get('post_count', 0)}
- 平均得分: {reddit.get('avg_score', 0)}
- 情感得分: {reddit.get('sentiment_score', 0):.2f}

**综合情感**: {social_data.get('overall_sentiment', 0):.2f}
"""

        # 格式化新闻数据
        news = news_data.get("recent_news", [])
        sentiment = news_data.get("sentiment", {})
        news_str_parts = [f"""
**新闻情感分析**:
- 新闻总数: {sentiment.get('news_count', 0)}
- 情感得分: {sentiment.get('sentiment_score', 0):.2f}
- 利好新闻: {sentiment.get('bullish_count', 0)}
- 利空新闻: {sentiment.get('bearish_count', 0)}

**最新新闻**:
"""]
        for i, item in enumerate(news[:5], 1):
            news_str_parts.append(f"{i}. {item.get('title')} ({item.get('source')})")

        news_data_str = "\n".join(news_str_parts)

        return {
            "symbol": symbol,
            "project_info": project_info_str,
            "market_data": market_data_str,
            "onchain_data": onchain_data_str,
            "social_data": social_data_str,
            "news_data": news_data_str,
        }

    # ================================
    # 快速查询方法
    # ================================

    async def quick_lookup(self, symbol: str) -> str:
        """
        快速查询，返回简要信息（用于Quick Chat）

        Args:
            symbol: 币种符号

        Returns:
            str: 简要信息文本
        """
        coingecko_id = await self._resolve_coingecko_id(symbol)

        if not coingecko_id:
            return f"❌ 无法找到 {symbol} 的信息"

        # 只获取基本市场数据
        market_data = await coingecko_collector.get_coin_market_data(coingecko_id)

        # 验证数据有效性，避免返回虚假的 $0 价格
        if not market_data or market_data.get("price_usd") is None:
            raise CoinGeckoAPIError(f"无法获取 {symbol.upper()} 的实时价格数据")

        name = market_data.get("name", symbol)
        price = market_data.get("price_usd")
        change_24h = market_data.get("price_change_24h")
        market_cap = market_data.get("market_cap")
        rank = market_data.get("market_cap_rank", "N/A")

        direction = "上涨" if (change_24h or 0) > 0 else "下跌"

        return f"""
**{name} ({symbol.upper()})**
💰 当前价格: ${price:.4f}
📊 24h变化: {abs(change_24h or 0):.2f}% ({direction})
💎 市值: ${(market_cap or 0):,.0f} (排名第{rank})
"""


# ================================
# 全局实例
# ================================

data_aggregator = DataAggregator()
