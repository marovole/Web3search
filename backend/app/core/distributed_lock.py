"""
Redis分布式锁管理器（任务 9.5）

提供分布式锁功能，用于：
1. 防止并发执行相同操作
2. 确保资源访问的互斥性
3. 支持超时和自动释放
"""
import asyncio
import uuid
from typing import Optional
import logging

from app.core.redis_client import get_async_redis

logger = logging.getLogger(__name__)


class DistributedLock:
    """
    Redis分布式锁

    使用Redis SET NX EX命令实现：
    - NX: 仅当键不存在时设置
    - EX: 设置过期时间（防止死锁）
    """

    def __init__(
        self,
        lock_key: str,
        timeout: int = 30,
        retry_delay: float = 0.1,
        max_retries: int = 0,
    ):
        """
        初始化分布式锁

        Args:
            lock_key: 锁的键名
            timeout: 锁的超时时间（秒），默认30秒
            retry_delay: 获取锁失败时的重试延迟（秒）
            max_retries: 最大重试次数，0表示不重试
        """
        self.lock_key = f"lock:{lock_key}"
        self.timeout = timeout
        self.retry_delay = retry_delay
        self.max_retries = max_retries

        # 生成唯一标识符，用于释放锁时验证所有权
        self.lock_value = str(uuid.uuid4())

        # 标记锁是否被当前实例持有
        self.is_locked = False

    async def acquire(self) -> bool:
        """
        获取锁

        Returns:
            bool: 是否成功获取锁
        """
        redis = await get_async_redis()

        retries = 0
        while retries <= self.max_retries:
            try:
                # 使用SET NX EX命令原子性地获取锁
                result = await redis.set(
                    self.lock_key,
                    self.lock_value,
                    ex=self.timeout,  # 过期时间
                    nx=True,  # 仅当键不存在时设置
                )

                if result:
                    self.is_locked = True
                    logger.debug(f"成功获取锁: {self.lock_key}")
                    return True

                # 获取失败，可能需要重试
                if retries < self.max_retries:
                    logger.debug(
                        f"锁已被占用: {self.lock_key}, "
                        f"重试 {retries + 1}/{self.max_retries}"
                    )
                    await asyncio.sleep(self.retry_delay)
                    retries += 1
                else:
                    logger.debug(f"无法获取锁: {self.lock_key}")
                    return False

            except Exception as e:
                logger.error(f"获取锁失败: {self.lock_key}, 错误: {e}")
                return False

        return False

    async def release(self) -> bool:
        """
        释放锁

        使用Lua脚本确保只有锁的持有者才能释放

        Returns:
            bool: 是否成功释放锁
        """
        if not self.is_locked:
            logger.warning(f"尝试释放未持有的锁: {self.lock_key}")
            return False

        redis = await get_async_redis()

        try:
            # Lua脚本：检查锁的值是否匹配，匹配则删除
            # 这确保只有锁的持有者才能释放锁
            lua_script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("del", KEYS[1])
            else
                return 0
            end
            """

            result = await redis.eval(lua_script, 1, self.lock_key, self.lock_value)

            if result == 1:
                self.is_locked = False
                logger.debug(f"成功释放锁: {self.lock_key}")
                return True
            else:
                logger.warning(
                    f"无法释放锁（可能已过期或被其他持有者占用）: {self.lock_key}"
                )
                self.is_locked = False
                return False

        except Exception as e:
            logger.error(f"释放锁失败: {self.lock_key}, 错误: {e}")
            return False

    async def extend(self, additional_time: int) -> bool:
        """
        延长锁的过期时间

        Args:
            additional_time: 延长的时间（秒）

        Returns:
            bool: 是否成功延长
        """
        if not self.is_locked:
            logger.warning(f"尝试延长未持有的锁: {self.lock_key}")
            return False

        redis = await get_async_redis()

        try:
            # Lua脚本：检查锁的值是否匹配，匹配则延长过期时间
            lua_script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("expire", KEYS[1], ARGV[2])
            else
                return 0
            end
            """

            result = await redis.eval(
                lua_script, 1, self.lock_key, self.lock_value, str(additional_time)
            )

            if result == 1:
                logger.debug(f"成功延长锁: {self.lock_key}, 延长 {additional_time}秒")
                return True
            else:
                logger.warning(f"无法延长锁（可能已过期或被其他持有者占用）: {self.lock_key}")
                return False

        except Exception as e:
            logger.error(f"延长锁失败: {self.lock_key}, 错误: {e}")
            return False

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        await self.release()


# ================================
# 便捷函数
# ================================

async def acquire_lock(
    lock_key: str,
    timeout: int = 30,
    retry_delay: float = 0.1,
    max_retries: int = 0,
) -> Optional[DistributedLock]:
    """
    便捷函数：获取分布式锁

    Args:
        lock_key: 锁的键名
        timeout: 锁的超时时间（秒）
        retry_delay: 重试延迟（秒）
        max_retries: 最大重试次数

    Returns:
        Optional[DistributedLock]: 成功返回锁对象，失败返回None
    """
    lock = DistributedLock(
        lock_key=lock_key,
        timeout=timeout,
        retry_delay=retry_delay,
        max_retries=max_retries,
    )

    if await lock.acquire():
        return lock
    else:
        return None


async def release_lock(lock: DistributedLock) -> bool:
    """
    便捷函数：释放分布式锁

    Args:
        lock: 锁对象

    Returns:
        bool: 是否成功释放
    """
    return await lock.release()
