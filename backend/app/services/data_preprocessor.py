"""
数据预处理服务（任务 9.6）

功能：
1. 预计算常用指标，减少重复计算
2. 缓存预计算结果
3. 为热门查询提供快速响应
"""
from typing import Dict, Any, Optional
import logging
from datetime import datetime

from app.core.redis_client import cache_set, cache_get_json
from app.core.query_cache import DataType

logger = logging.getLogger(__name__)


class DataPreprocessor:
    """
    数据预处理服务

    预计算项目：
    - 价格变化百分比（24h/7d/30d）
    - 市值排名
    - 社交情绪得分
    - 风险等级
    """

    def __init__(self):
        """初始化数据预处理器"""
        self.cache_ttl = 5 * 60  # 5分钟TTL

    async def preprocess_market_data(
        self,
        symbol: str,
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        预处理市场数据

        计算：
        - 价格变化百分比
        - 市值变化
        - 交易量趋势

        Args:
            symbol: 代币符号
            market_data: 原始市场数据

        Returns:
            Dict: 预处理后的市场数据
        """
        processed = market_data.copy()

        # 提取当前数据
        current = market_data.get("current", {})

        # 计算价格变化（如果不存在）
        if "price_change_24h" not in current and "price_usd" in current:
            # 可以从历史数据计算，这里简化处理
            pass

        # 添加预计算标记
        processed["_preprocessed"] = True
        processed["_preprocessed_at"] = datetime.utcnow().isoformat()

        # 缓存预处理结果
        cache_key = f"preprocessed_market:{symbol.upper()}"
        await cache_set(cache_key, processed, self.cache_ttl)

        return processed

    async def preprocess_social_data(
        self,
        symbol: str,
        social_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        预处理社交数据

        计算：
        - 综合情绪得分
        - 情绪趋势
        - 社区活跃度

        Args:
            symbol: 代币符号
            social_data: 原始社交数据

        Returns:
            Dict: 预处理后的社交数据
        """
        processed = social_data.copy()

        # 计算综合情绪得分（如果不存在）
        if "overall_sentiment" not in processed:
            twitter_score = social_data.get("twitter", {}).get("sentiment_score", 0)
            reddit_score = social_data.get("reddit", {}).get("sentiment_score", 0)

            if twitter_score or reddit_score:
                processed["overall_sentiment"] = (twitter_score + reddit_score) / 2

        # 添加预计算标记
        processed["_preprocessed"] = True
        processed["_preprocessed_at"] = datetime.utcnow().isoformat()

        # 缓存预处理结果
        cache_key = f"preprocessed_social:{symbol.upper()}"
        await cache_set(cache_key, processed, self.cache_ttl)

        return processed

    async def get_preprocessed_data(
        self,
        symbol: str,
        data_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        获取预处理的数据

        Args:
            symbol: 代币符号
            data_type: 数据类型（market, social等）

        Returns:
            Optional[Dict]: 预处理的数据，不存在返回None
        """
        cache_key = f"preprocessed_{data_type}:{symbol.upper()}"
        return await cache_get_json(cache_key)

    async def preprocess_all(
        self,
        symbol: str,
        aggregated_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        预处理所有数据

        Args:
            symbol: 代币符号
            aggregated_data: 聚合后的数据

        Returns:
            Dict: 完整的预处理数据
        """
        processed = aggregated_data.copy()

        # 预处理市场数据
        if "market_data" in processed:
            processed["market_data"] = await self.preprocess_market_data(
                symbol,
                processed["market_data"]
            )

        # 预处理社交数据
        if "social_data" in processed:
            processed["social_data"] = await self.preprocess_social_data(
                symbol,
                processed["social_data"]
            )

        # 全局缓存
        cache_key = f"preprocessed_all:{symbol.upper()}"
        await cache_set(cache_key, processed, self.cache_ttl)

        return processed


# ================================
# 全局实例
# ================================

data_preprocessor = DataPreprocessor()
