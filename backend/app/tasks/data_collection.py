"""
数据采集任务
定时执行的后台任务，采集各类加密货币数据
"""
import asyncio
from datetime import datetime
from typing import List
from celery import Task

from app.tasks.celery_app import celery_app
from app.services.collectors import (
    coingecko_collector,
    etherscan_collector,
    twitter_collector,
    reddit_collector,
    cryptopanic_collector,
)
from app.core.redis_client import get_redis


# ================================
# 辅助函数：运行异步任务
# ================================

def run_async(coro):
    """在Celery任务中运行异步协程"""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)


# ================================
# 价格数据更新任务
# ================================

@celery_app.task(
    name="app.tasks.data_collection.update_trending_coin_prices",
    bind=True,
    max_retries=3,
)
def update_trending_coin_prices(self: Task):
    """
    更新热门币种价格数据
    每分钟执行一次
    """
    try:
        print("🔄 开始更新热门币种价格...")

        # 获取热门币种
        trending = run_async(coingecko_collector.get_trending_coins(limit=20))

        updated_count = 0
        for coin in trending:
            try:
                coin_id = coin.get("coingecko_id")
                if not coin_id:
                    continue

                # 获取市场数据
                market_data = run_async(coingecko_collector.get_coin_market_data(coin_id))

                # 这里应该将数据存储到数据库
                # 暂时只打印日志
                print(f"  ✅ 更新 {coin.get('symbol')}: ${market_data.get('price_usd', 0):.4f}")
                updated_count += 1

            except Exception as e:
                print(f"  ⚠️ 更新 {coin.get('symbol')} 失败: {e}")
                continue

        print(f"✅ 价格更新完成，共更新 {updated_count} 个币种")
        return {"status": "success", "updated_count": updated_count}

    except Exception as e:
        print(f"❌ 价格更新任务失败: {e}")
        raise self.retry(exc=e, countdown=60)  # 1分钟后重试


# ================================
# 项目快照任务
# ================================

@celery_app.task(
    name="app.tasks.data_collection.snapshot_trending_projects",
    bind=True,
    max_retries=3,
)
def snapshot_trending_projects(self: Task):
    """
    为热门项目创建数据快照
    每小时执行一次
    """
    try:
        print("🔄 开始创建项目快照...")

        # 获取热门币种
        trending = run_async(coingecko_collector.get_trending_coins(limit=50))

        snapshot_count = 0
        for coin in trending:
            try:
                coin_id = coin.get("coingecko_id")
                symbol = coin.get("symbol", "").upper()

                if not coin_id:
                    continue

                # 并行获取多个数据源
                market_data = run_async(coingecko_collector.get_coin_market_data(coin_id))

                # 获取合约地址（如果有）
                coin_info = run_async(coingecko_collector.get_coin_info(coin_id))
                contract_addresses = coin_info.get("contract_addresses", {})

                # 如果是以太坊代币，获取链上数据
                onchain_data = {}
                if "ethereum" in contract_addresses:
                    eth_address = contract_addresses["ethereum"]
                    try:
                        onchain_data = run_async(
                            etherscan_collector.get_token_onchain_data(eth_address)
                        )
                    except Exception as e:
                        print(f"  ⚠️ 获取 {symbol} 链上数据失败: {e}")

                # 这里应该将快照数据存储到数据库
                print(f"  ✅ 创建快照: {symbol}")
                snapshot_count += 1

            except Exception as e:
                print(f"  ⚠️ 创建快照失败: {e}")
                continue

        print(f"✅ 快照创建完成，共创建 {snapshot_count} 个快照")
        return {"status": "success", "snapshot_count": snapshot_count}

    except Exception as e:
        print(f"❌ 快照任务失败: {e}")
        raise self.retry(exc=e, countdown=300)  # 5分钟后重试


# ================================
# 社交数据更新任务
# ================================

@celery_app.task(
    name="app.tasks.data_collection.update_social_data",
    bind=True,
    max_retries=2,
)
def update_social_data(self: Task):
    """
    更新社交媒体数据（Twitter、Reddit）
    每6小时执行一次
    """
    try:
        print("🔄 开始更新社交数据...")

        # 热门币种列表
        top_symbols = ["BTC", "ETH", "BNB", "SOL", "ADA", "XRP", "DOGE", "MATIC", "DOT", "AVAX"]

        updated_count = 0
        for symbol in top_symbols:
            try:
                # Twitter情感分析
                twitter_sentiment = run_async(
                    twitter_collector.get_crypto_sentiment(symbol, hours=24)
                )

                # Reddit情感分析
                reddit_sentiment = run_async(
                    reddit_collector.get_crypto_sentiment(symbol, hours=24)
                )

                # 这里应该将数据存储到数据库
                print(f"  ✅ {symbol} - Twitter: {twitter_sentiment.get('mention_count')} 提及")
                print(f"           Reddit: {reddit_sentiment.get('post_count')} 帖子")
                updated_count += 1

            except Exception as e:
                print(f"  ⚠️ 更新 {symbol} 社交数据失败: {e}")
                continue

        print(f"✅ 社交数据更新完成，共更新 {updated_count} 个币种")
        return {"status": "success", "updated_count": updated_count}

    except Exception as e:
        print(f"❌ 社交数据更新任务失败: {e}")
        raise self.retry(exc=e, countdown=600)  # 10分钟后重试


# ================================
# 链上数据更新任务
# ================================

@celery_app.task(
    name="app.tasks.data_collection.update_onchain_data",
    bind=True,
    max_retries=2,
)
def update_onchain_data(self: Task):
    """
    更新链上数据（交易数、持有者等）
    每天执行一次
    """
    try:
        print("🔄 开始更新链上数据...")

        # 这里应该从数据库获取需要更新的合约地址列表
        # 暂时使用示例地址
        example_contracts = {
            "USDT": "0xdac17f958d2ee523a2206206994597c13d831ec7",
            "USDC": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
            # 可以添加更多合约地址
        }

        updated_count = 0
        for symbol, contract_address in example_contracts.items():
            try:
                # 获取链上数据
                onchain_data = run_async(
                    etherscan_collector.get_token_onchain_data(contract_address)
                )

                # 这里应该将数据存储到数据库
                print(f"  ✅ {symbol} - 24h交易: {onchain_data.get('transaction_count_24h')}")
                updated_count += 1

            except Exception as e:
                print(f"  ⚠️ 更新 {symbol} 链上数据失败: {e}")
                continue

        print(f"✅ 链上数据更新完成，共更新 {updated_count} 个合约")
        return {"status": "success", "updated_count": updated_count}

    except Exception as e:
        print(f"❌ 链上数据更新任务失败: {e}")
        raise self.retry(exc=e, countdown=1800)  # 30分钟后重试


# ================================
# 新闻采集任务
# ================================

@celery_app.task(
    name="app.tasks.data_collection.collect_crypto_news",
    bind=True,
    max_retries=3,
)
def collect_crypto_news(self: Task):
    """
    采集加密货币新闻
    每30分钟执行一次
    """
    try:
        print("🔄 开始采集加密货币新闻...")

        # 获取各类新闻
        trending_news = run_async(cryptopanic_collector.get_trending_news(limit=20))
        important_news = run_async(cryptopanic_collector.get_important_news(limit=20))

        total_news = len(trending_news) + len(important_news)

        # 这里应该将新闻存储到数据库或缓存
        print(f"  ✅ 采集热门新闻: {len(trending_news)} 条")
        print(f"  ✅ 采集重要新闻: {len(important_news)} 条")

        print(f"✅ 新闻采集完成，共采集 {total_news} 条新闻")
        return {"status": "success", "news_count": total_news}

    except Exception as e:
        print(f"❌ 新闻采集任务失败: {e}")
        raise self.retry(exc=e, countdown=300)  # 5分钟后重试


# ================================
# 缓存清理任务
# ================================

@celery_app.task(
    name="app.tasks.data_collection.cleanup_expired_cache",
    bind=True,
)
def cleanup_expired_cache(self: Task):
    """
    清理过期的Redis缓存
    每天执行一次
    """
    try:
        print("🔄 开始清理过期缓存...")

        redis_client = get_redis()

        # 获取所有缓存键（使用scan避免阻塞）
        cursor = 0
        expired_count = 0

        while True:
            cursor, keys = redis_client.scan(
                cursor=cursor,
                match="*",
                count=1000,
            )

            # 检查TTL并删除过期键
            for key in keys:
                ttl = redis_client.ttl(key)
                if ttl == -2:  # 键不存在
                    expired_count += 1
                elif ttl == -1:  # 键永不过期但应该过期的
                    if key.startswith(("coingecko:", "twitter:", "reddit:", "cryptopanic:")):
                        redis_client.delete(key)
                        expired_count += 1

            if cursor == 0:
                break

        print(f"✅ 缓存清理完成，清理 {expired_count} 个过期键")
        return {"status": "success", "cleaned_count": expired_count}

    except Exception as e:
        print(f"❌ 缓存清理任务失败: {e}")
        return {"status": "error", "message": str(e)}


# ================================
# 热点识别任务
# ================================

@celery_app.task(
    name="app.tasks.data_collection.update_hotspots",
    bind=True,
    max_retries=3,
)
def update_hotspots(self: Task):
    """
    更新市场热点数据
    每小时执行一次
    """
    try:
        print("🔥 开始更新市场热点...")

        # 导入热点分析器
        from app.services.hotspot_analyzer import hotspot_analyzer

        # 计算热点（force_refresh=True强制重新计算）
        hotspots = run_async(hotspot_analyzer.get_hotspots(limit=20, force_refresh=True))

        print(f"✅ 热点更新完成，共发现 {len(hotspots)} 个热点")

        # 返回前3名热点的简要信息
        top_3 = [
            {
                "symbol": h.get("symbol"),
                "score": h.get("total_score"),
            }
            for h in hotspots[:3]
        ]

        return {
            "status": "success",
            "hotspots_count": len(hotspots),
            "top_3": top_3,
        }

    except Exception as e:
        print(f"❌ 热点更新任务失败: {e}")
        raise self.retry(exc=e, countdown=1800)  # 30分钟后重试
