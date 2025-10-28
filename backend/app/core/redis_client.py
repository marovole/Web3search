"""
Redis客户端模块
提供缓存、会话存储、速率限制等功能
"""
import json
from typing import Any, Optional
from redis import Redis
from redis.asyncio import Redis as AsyncRedis

from app.core.config import settings


# 同步Redis客户端（用于Celery等）
redis_client: Optional[Redis] = None

# 异步Redis客户端（用于FastAPI）
async_redis_client: Optional[AsyncRedis] = None


def get_redis() -> Redis:
    """
    获取同步Redis客户端（单例模式）

    Returns:
        Redis: 同步Redis客户端实例
    """
    global redis_client
    if redis_client is None:
        redis_client = Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            encoding="utf-8",
        )
    return redis_client


async def get_async_redis() -> AsyncRedis:
    """
    获取异步Redis客户端（单例模式）

    Returns:
        AsyncRedis: 异步Redis客户端实例
    """
    global async_redis_client
    if async_redis_client is None:
        async_redis_client = await AsyncRedis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            encoding="utf-8",
        )
    return async_redis_client


async def close_redis() -> None:
    """关闭Redis连接"""
    global redis_client, async_redis_client

    if redis_client:
        redis_client.close()
        redis_client = None

    if async_redis_client:
        await async_redis_client.close()
        async_redis_client = None


# ================================
# 缓存辅助函数
# ================================

async def cache_get(key: str) -> Optional[str]:
    """
    从缓存获取值

    Args:
        key: 缓存键

    Returns:
        Optional[str]: 缓存值，不存在返回None
    """
    redis = await get_async_redis()
    return await redis.get(key)


async def cache_set(key: str, value: Any, ttl: Optional[int] = None) -> bool:
    """
    设置缓存值

    Args:
        key: 缓存键
        value: 缓存值（会自动序列化为JSON）
        ttl: 过期时间（秒），None表示永不过期

    Returns:
        bool: 是否设置成功
    """
    redis = await get_async_redis()

    # 如果value是字典或列表，序列化为JSON
    if isinstance(value, (dict, list)):
        value = json.dumps(value, ensure_ascii=False)

    if ttl:
        return await redis.setex(key, ttl, value)
    else:
        return await redis.set(key, value)


async def cache_delete(key: str) -> int:
    """
    删除缓存

    Args:
        key: 缓存键

    Returns:
        int: 删除的键数量
    """
    redis = await get_async_redis()
    return await redis.delete(key)


async def cache_exists(key: str) -> bool:
    """
    检查缓存是否存在

    Args:
        key: 缓存键

    Returns:
        bool: 是否存在
    """
    redis = await get_async_redis()
    return await redis.exists(key) > 0


async def cache_get_json(key: str) -> Optional[dict]:
    """
    从缓存获取JSON值并反序列化

    Args:
        key: 缓存键

    Returns:
        Optional[dict]: 反序列化后的字典，不存在或解析失败返回None
    """
    value = await cache_get(key)
    if value:
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return None
    return None


async def cache_increment(key: str, amount: int = 1) -> int:
    """
    递增缓存值（用于计数）

    Args:
        key: 缓存键
        amount: 递增量

    Returns:
        int: 递增后的值
    """
    redis = await get_async_redis()
    return await redis.incrby(key, amount)


async def cache_set_hash(key: str, field: str, value: Any) -> int:
    """
    设置Hash类型缓存

    Args:
        key: 缓存键
        field: Hash字段
        value: 值

    Returns:
        int: 新增字段数量
    """
    redis = await get_async_redis()

    if isinstance(value, (dict, list)):
        value = json.dumps(value, ensure_ascii=False)

    return await redis.hset(key, field, value)


async def cache_get_hash(key: str, field: str) -> Optional[str]:
    """
    获取Hash类型缓存

    Args:
        key: 缓存键
        field: Hash字段

    Returns:
        Optional[str]: 字段值，不存在返回None
    """
    redis = await get_async_redis()
    return await redis.hget(key, field)


async def cache_get_all_hash(key: str) -> dict:
    """
    获取Hash类型缓存的所有字段

    Args:
        key: 缓存键

    Returns:
        dict: 所有字段和值的字典
    """
    redis = await get_async_redis()
    return await redis.hgetall(key)


# ================================
# 速率限制辅助函数
# ================================

async def rate_limit_check(
    identifier: str,
    limit: int,
    window: int
) -> tuple[bool, int]:
    """
    检查速率限制（使用滑动窗口算法）

    Args:
        identifier: 标识符（如IP地址、用户ID）
        limit: 限制次数
        window: 时间窗口（秒）

    Returns:
        tuple[bool, int]: (是否允许, 剩余次数)
    """
    redis = await get_async_redis()
    key = f"rate_limit:{identifier}"

    # 获取当前计数
    current = await redis.get(key)

    if current is None:
        # 首次请求，设置计数为1
        await redis.setex(key, window, 1)
        return True, limit - 1

    current_count = int(current)

    if current_count >= limit:
        # 超过限制
        ttl = await redis.ttl(key)
        return False, 0

    # 未超过限制，递增计数
    await redis.incr(key)
    return True, limit - current_count - 1


# ================================
# 会话存储辅助函数
# ================================

async def session_set(session_id: str, data: dict, ttl: int = 1800) -> bool:
    """
    存储会话数据

    Args:
        session_id: 会话ID
        data: 会话数据
        ttl: 过期时间（秒），默认30分钟

    Returns:
        bool: 是否成功
    """
    key = f"session:{session_id}"
    return await cache_set(key, data, ttl)


async def session_get(session_id: str) -> Optional[dict]:
    """
    获取会话数据

    Args:
        session_id: 会话ID

    Returns:
        Optional[dict]: 会话数据，不存在返回None
    """
    key = f"session:{session_id}"
    return await cache_get_json(key)


async def session_delete(session_id: str) -> int:
    """
    删除会话

    Args:
        session_id: 会话ID

    Returns:
        int: 删除的键数量
    """
    key = f"session:{session_id}"
    return await cache_delete(key)


# ================================
# Redis健康检查（Stage 4任务4.2）
# ================================

async def check_redis_health() -> dict:
    """
    检查Redis连接和性能

    测试Redis的连接状态、响应延迟和基本操作

    Returns:
        dict: 健康检查结果
            - status: "healthy" | "unhealthy"
            - latency_ms: 响应延迟（毫秒）
            - connected: 是否连接成功
            - error: 错误信息（如果有）
    """
    import time

    try:
        redis = await get_async_redis()

        # 测试PING命令并计算延迟
        start = time.time()
        pong = await redis.ping()
        latency = (time.time() - start) * 1000  # 转换为毫秒

        if not pong:
            return {
                "status": "unhealthy",
                "connected": False,
                "latency_ms": 0,
                "error": "PING command failed"
            }

        # 测试SET/GET操作
        test_key = "health_check:test"
        test_value = "ok"

        await redis.set(test_key, test_value, ex=10)
        retrieved = await redis.get(test_key)

        if retrieved != test_value:
            return {
                "status": "unhealthy",
                "connected": True,
                "latency_ms": latency,
                "error": "SET/GET test failed"
            }

        # 清理测试键
        await redis.delete(test_key)

        # 判断健康状态（延迟超过100ms视为降级）
        status = "healthy" if latency < 100 else "degraded"

        return {
            "status": status,
            "connected": True,
            "latency_ms": round(latency, 2),
            "error": None
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "connected": False,
            "latency_ms": 0,
            "error": str(e)
        }


async def get_redis_info() -> dict:
    """
    获取Redis服务器信息

    包括内存使用、连接数、命中率等统计信息

    Returns:
        dict: Redis服务器信息
            - used_memory_human: 已用内存（人类可读）
            - used_memory_peak_human: 峰值内存
            - connected_clients: 连接客户端数
            - total_commands_processed: 总命令数
            - instantaneous_ops_per_sec: 每秒操作数
            - keyspace_hits: 命中次数
            - keyspace_misses: 未命中次数
            - hit_rate: 命中率
    """
    try:
        redis = await get_async_redis()
        info = await redis.info()

        # 提取关键指标
        stats = {
            "used_memory_human": info.get("used_memory_human", "N/A"),
            "used_memory_peak_human": info.get("used_memory_peak_human", "N/A"),
            "connected_clients": info.get("connected_clients", 0),
            "total_commands_processed": info.get("total_commands_processed", 0),
            "instantaneous_ops_per_sec": info.get("instantaneous_ops_per_sec", 0),
            "keyspace_hits": info.get("keyspace_hits", 0),
            "keyspace_misses": info.get("keyspace_misses", 0),
        }

        # 计算命中率
        hits = stats["keyspace_hits"]
        misses = stats["keyspace_misses"]
        total = hits + misses
        stats["hit_rate"] = round(hits / total, 4) if total > 0 else 0.0

        return stats

    except Exception as e:
        return {
            "error": str(e)
        }
