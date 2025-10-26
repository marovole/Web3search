"""
热点自动识别服务
综合多个维度自动识别当前市场热点
"""
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from app.services.collectors import (
    coingecko_collector,
    twitter_collector,
    reddit_collector,
    cryptopanic_collector,
)
from app.core.redis_client import cache_get_json, cache_set


class HotspotAnalyzer:
    """
    热点分析器
    综合5个维度识别市场热点：
    1. Twitter提及量
    2. Reddit讨论量
    3. 24h价格变化
    4. 24h交易量变化
    5. 新闻数量
    """

    def __init__(self):
        """初始化热点分析器"""
        self.cache_key = "hotspots:latest"
        self.cache_ttl = 3600  # 1小时缓存

    async def calculate_hotspots(
        self, limit: int = 20, min_market_cap_rank: int = 300
    ) -> List[Dict[str, Any]]:
        """
        计算当前市场热点

        Args:
            limit: 返回热点数量
            min_market_cap_rank: 最小市值排名（过滤小市值币种）

        Returns:
            List[Dict]: 热点列表，按得分排序
        """
        print("🔥 开始计算市场热点...")

        # 1. 获取基础币种列表（Top 100 + 趋势币）
        trending_coins = await coingecko_collector.get_trending_coins(limit=50)
        coin_ids = [coin["coingecko_id"] for coin in trending_coins if coin.get("coingecko_id")]

        # 2. 并发收集各维度数据
        hotspot_scores = {}
        tasks = []

        for coin_id in coin_ids[:50]:  # 限制50个避免超时
            tasks.append(self._analyze_coin(coin_id, min_market_cap_rank))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 3. 汇总结果
        for result in results:
            if isinstance(result, dict) and result.get("coin_id"):
                coin_id = result["coin_id"]
                hotspot_scores[coin_id] = result

        # 4. 按总分排序
        sorted_hotspots = sorted(
            hotspot_scores.values(),
            key=lambda x: x.get("total_score", 0),
            reverse=True,
        )

        # 5. 返回Top N
        top_hotspots = sorted_hotspots[:limit]

        print(f"✅ 热点计算完成，共发现 {len(top_hotspots)} 个热点")

        return top_hotspots

    async def _analyze_coin(
        self, coin_id: str, min_market_cap_rank: int
    ) -> Dict[str, Any]:
        """
        分析单个币种的热度

        Args:
            coin_id: CoinGecko币种ID
            min_market_cap_rank: 最小市值排名

        Returns:
            Dict: 热度分析结果
        """
        try:
            # 获取基本信息和市场数据
            coin_data = await coingecko_collector.get_coin_data(
                coin_id,
                include_market_data=True,
                include_community_data=True,
            )

            if not coin_data:
                return {}

            # 过滤小市值币种
            market_cap_rank = coin_data.get("market_cap_rank", 9999)
            if market_cap_rank > min_market_cap_rank:
                return {}

            symbol = coin_data.get("symbol", "").upper()
            name = coin_data.get("name", "")
            market_data = coin_data.get("market_data", {})

            # 初始化评分
            scores = {
                "twitter_score": 0,
                "reddit_score": 0,
                "price_score": 0,
                "volume_score": 0,
                "news_score": 0,
            }

            # 维度1：Twitter提及量（权重25%）
            twitter_followers = (
                coin_data.get("community_data", {}).get("twitter_followers") or 0
            )
            if twitter_followers > 0:
                # 归一化到0-100分
                scores["twitter_score"] = min(100, (twitter_followers / 10000) * 100) * 0.25

            # 维度2：Reddit讨论量（权重20%）
            reddit_subscribers = (
                coin_data.get("community_data", {}).get("reddit_subscribers") or 0
            )
            if reddit_subscribers > 0:
                scores["reddit_score"] = min(100, (reddit_subscribers / 5000) * 100) * 0.20

            # 维度3：24h价格变化（权重30%）
            price_change_24h = market_data.get("price_change_percentage_24h", 0)
            if price_change_24h:
                # 价格变化越大，分数越高（绝对值）
                # 上涨加分更多，下跌也有一定分数（关注度）
                if price_change_24h > 0:
                    scores["price_score"] = min(100, abs(price_change_24h) * 5) * 0.30
                else:
                    scores["price_score"] = min(100, abs(price_change_24h) * 2) * 0.30

            # 维度4：24h交易量变化（权重15%）
            # 简化实现：使用当前交易量作为活跃度指标
            volume_24h = market_data.get("total_volume", {}).get("usd", 0)
            if volume_24h > 0:
                # 归一化（假设1亿美元交易量为满分）
                scores["volume_score"] = min(100, (volume_24h / 100_000_000) * 100) * 0.15

            # 维度5：新闻数量（权重10%）
            # 这里可以通过CryptoPanic API获取，暂时简化
            # 使用市值排名作为替代指标（排名越高，新闻越多）
            if market_cap_rank <= 10:
                scores["news_score"] = 100 * 0.10
            elif market_cap_rank <= 50:
                scores["news_score"] = 70 * 0.10
            elif market_cap_rank <= 100:
                scores["news_score"] = 40 * 0.10

            # 计算总分
            total_score = sum(scores.values())

            return {
                "coin_id": coin_id,
                "symbol": symbol,
                "name": name,
                "market_cap_rank": market_cap_rank,
                "price_usd": market_data.get("current_price", {}).get("usd"),
                "price_change_24h": price_change_24h,
                "volume_24h": volume_24h,
                "total_score": round(total_score, 2),
                "scores_breakdown": {
                    "twitter": round(scores["twitter_score"], 2),
                    "reddit": round(scores["reddit_score"], 2),
                    "price": round(scores["price_score"], 2),
                    "volume": round(scores["volume_score"], 2),
                    "news": round(scores["news_score"], 2),
                },
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            print(f"⚠️ 分析币种 {coin_id} 失败: {e}")
            return {}

    async def get_cached_hotspots(self) -> Optional[List[Dict[str, Any]]]:
        """
        获取缓存的热点数据

        Returns:
            Optional[List[Dict]]: 缓存的热点列表，如果没有则返回None
        """
        return await cache_get_json(self.cache_key)

    async def cache_hotspots(self, hotspots: List[Dict[str, Any]]):
        """
        缓存热点数据

        Args:
            hotspots: 热点列表
        """
        await cache_set(self.cache_key, hotspots, self.cache_ttl)
        print(f"💾 热点数据已缓存，TTL={self.cache_ttl}秒")

    async def get_hotspots(
        self, limit: int = 20, force_refresh: bool = False
    ) -> List[Dict[str, Any]]:
        """
        获取热点列表（优先从缓存读取）

        Args:
            limit: 返回热点数量
            force_refresh: 强制刷新（忽略缓存）

        Returns:
            List[Dict]: 热点列表
        """
        # 如果不强制刷新，先尝试从缓存获取
        if not force_refresh:
            cached = await self.get_cached_hotspots()
            if cached:
                print("✅ 从缓存读取热点数据")
                return cached[:limit]

        # 计算新的热点
        hotspots = await self.calculate_hotspots(limit=limit)

        # 缓存结果
        await self.cache_hotspots(hotspots)

        return hotspots


# ================================
# 全局实例
# ================================

hotspot_analyzer = HotspotAnalyzer()
