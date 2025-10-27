"""
查询去重服务（任务 9.5）

功能：
1. 防止相同查询并发执行
2. 合并相同查询的结果
3. 使用Redis分布式锁确保互斥
"""
import asyncio
import json
from typing import Any, Dict, Optional, Callable, Awaitable
import logging

from app.core.distributed_lock import DistributedLock
from app.core.redis_client import cache_set, cache_get_json
from app.core.query_cache import generate_query_hash, DataType

logger = logging.getLogger(__name__)


class QueryDedup:
    """
    查询去重服务

    工作流程：
    1. 为查询生成唯一键（query_hash）
    2. 尝试获取分布式锁
    3. 如果获取成功，执行查询并缓存结果
    4. 如果获取失败，等待结果并返回
    """

    def __init__(self):
        """初始化查询去重服务"""
        self.result_ttl = 60  # 结果缓存TTL（秒）
        self.lock_timeout = 30  # 锁超时时间（秒）
        self.wait_timeout = 35  # 等待结果超时时间（秒）
        self.wait_interval = 0.5  # 等待检查间隔（秒）

    async def execute_with_dedup(
        self,
        query: str,
        executor: Callable[[], Awaitable[Dict[str, Any]]],
        symbol: Optional[str] = None,
        data_type: Optional[DataType] = None,
        additional_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        使用去重机制执行查询

        Args:
            query: 查询字符串
            executor: 异步执行函数（返回查询结果）
            symbol: 代币符号（可选）
            data_type: 数据类型（可选）
            additional_params: 额外参数（可选）

        Returns:
            Dict: 查询结果
        """
        # 生成查询哈希（作为锁和结果的键）
        query_hash = generate_query_hash(query, symbol, data_type, additional_params)

        # 结果键
        result_key = f"dedup_result:{query_hash}"

        # 锁键
        lock_key = f"dedup_lock:{query_hash}"

        # 尝试获取锁
        lock = DistributedLock(
            lock_key=lock_key,
            timeout=self.lock_timeout,
            retry_delay=0,  # 不重试，直接等待结果
            max_retries=0,
        )

        if await lock.acquire():
            # 成功获取锁，执行查询
            try:
                logger.info(f"执行查询（去重）: {query_hash}")

                # 执行查询
                result = await executor()

                # 缓存结果供其他等待的请求使用
                await cache_set(result_key, result, self.result_ttl)

                logger.info(f"查询完成并缓存结果: {query_hash}")

                return result

            except Exception as e:
                logger.error(f"查询执行失败: {query_hash}, 错误: {e}")

                # 缓存错误结果（避免其他请求继续等待）
                error_result = {
                    "error": True,
                    "message": str(e),
                }
                await cache_set(result_key, error_result, self.result_ttl)

                raise

            finally:
                # 释放锁
                await lock.release()
        else:
            # 无法获取锁，等待结果
            logger.info(f"等待查询结果（去重）: {query_hash}")
            result = await self._wait_for_result(result_key)

            if result is None:
                # 等待超时，执行查询（可能锁已过期）
                logger.warning(f"等待超时，直接执行查询: {query_hash}")
                return await executor()

            # 检查是否为错误结果
            if result.get("error"):
                error_message = result.get("message", "查询失败")
                logger.error(f"获取到缓存的错误结果: {error_message}")
                raise Exception(error_message)

            logger.info(f"成功获取缓存结果（去重）: {query_hash}")
            return result

    async def _wait_for_result(self, result_key: str) -> Optional[Dict[str, Any]]:
        """
        等待查询结果

        Args:
            result_key: 结果键

        Returns:
            Optional[Dict]: 查询结果，超时返回None
        """
        elapsed = 0.0

        while elapsed < self.wait_timeout:
            # 检查结果是否已缓存
            result = await cache_get_json(result_key)

            if result is not None:
                return result

            # 等待一段时间后重试
            await asyncio.sleep(self.wait_interval)
            elapsed += self.wait_interval

        # 超时
        logger.warning(f"等待结果超时: {result_key}")
        return None


# ================================
# 全局实例
# ================================

query_dedup = QueryDedup()


# ================================
# 便捷函数
# ================================

async def execute_deduped(
    query: str,
    executor: Callable[[], Awaitable[Dict[str, Any]]],
    symbol: Optional[str] = None,
    data_type: Optional[DataType] = None,
) -> Dict[str, Any]:
    """
    便捷函数：执行去重查询

    Args:
        query: 查询字符串
        executor: 异步执行函数
        symbol: 代币符号
        data_type: 数据类型

    Returns:
        Dict: 查询结果
    """
    return await query_dedup.execute_with_dedup(
        query=query,
        executor=executor,
        symbol=symbol,
        data_type=data_type,
    )
