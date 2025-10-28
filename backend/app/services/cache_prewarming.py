"""
缓存预热系统 (Phase 15 - Stage 1)

提供智能缓存预热功能：
1. 分层预热策略 (Top 10/100/长尾币种)
2. 优先级队列管理
3. 批量并发预热
4. 失败重试机制（3次，指数退避）
5. 预热统计和监控
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
import httpx

from app.core.redis_client import cache_set, cache_get_json
from app.core.query_cache import DataType
from app.services.collectors.coingecko import coingecko_collector

logger = logging.getLogger(__name__)


# ================================
# 数据结构定义（任务 1.3）
# ================================


class PrewarmingPriority(str, Enum):
    """预热优先级枚举"""
    HIGH = "high"      # Top 10币种：每1分钟更新
    MEDIUM = "medium"  # Top 11-100币种：每5分钟更新
    LOW = "low"        # 长尾币种：每15分钟更新


@dataclass
class PrewarmingTask:
    """
    预热任务数据结构

    Attributes:
        coin_id: CoinGecko币种ID（如"bitcoin"）
        symbol: 币种符号（如"BTC"）
        priority: 优先级
        market_cap_rank: 市值排名
        retry_count: 当前重试次数
        last_attempt: 最后尝试时间
    """
    coin_id: str
    symbol: str
    priority: PrewarmingPriority
    market_cap_rank: int
    retry_count: int = 0
    last_attempt: Optional[datetime] = None


@dataclass
class PrewarmingResult:
    """
    预热结果数据结构

    Attributes:
        task: 原始任务
        success: 是否成功
        duration: 执行耗时（秒）
        error: 错误信息（失败时）
        cached_data_size: 缓存数据大小（字节）
        timestamp: 完成时间
    """
    task: PrewarmingTask
    success: bool
    duration: float
    error: Optional[str] = None
    cached_data_size: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)


# ================================
# 预热管理器（任务 1.2）
# ================================


class PrewarmingManager:
    """
    缓存预热管理器（单例模式）

    负责：
    - Top 100币种列表管理
    - 预热任务调度
    - 批量并发预热
    - 失败重试
    - 统计追踪
    """

    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls):
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化预热管理器"""
        if hasattr(self, '_initialized'):
            return

        self._initialized = True

        # 预热队列（按优先级分组）
        self.high_priority_queue: List[PrewarmingTask] = []
        self.medium_priority_queue: List[PrewarmingTask] = []
        self.low_priority_queue: List[PrewarmingTask] = []

        # 统计信息
        self.stats = {
            "total_prewarmed": 0,
            "total_success": 0,
            "total_failed": 0,
            "last_run": None,
            "cached_coins": 0,
        }

        # 配置
        self.max_retries = 3
        self.retry_delays = [1, 2, 4]  # 指数退避（秒）
        self.concurrency_limit = 10    # 并发限制

        logger.info("PrewarmingManager 初始化完成")

    # ================================
    # Top 100币种列表获取（任务 1.4）
    # ================================

    async def fetch_top_coins(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        从CoinGecko获取Top N市值币种列表

        Args:
            limit: 获取数量（默认100）

        Returns:
            List[Dict]: 币种列表，每个元素包含id, symbol, market_cap_rank

        Raises:
            Exception: API请求失败
        """
        try:
            # 使用CoinGecko /coins/markets端点获取Top币种
            url = f"{coingecko_collector.base_url}/coins/markets"
            params = {
                "vs_currency": "usd",
                "order": "market_cap_desc",
                "per_page": limit,
                "page": 1,
                "sparkline": False,
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    url,
                    params=params,
                    headers=coingecko_collector.headers
                )
                response.raise_for_status()
                data = response.json()

            # 提取关键信息
            top_coins = []
            for coin in data:
                top_coins.append({
                    "id": coin.get("id"),
                    "symbol": coin.get("symbol", "").upper(),
                    "market_cap_rank": coin.get("market_cap_rank", 999),
                })

            logger.info(f"成功获取Top {len(top_coins)}币种列表")
            return top_coins

        except Exception as e:
            logger.error(f"获取Top币种列表失败: {e}", exc_info=True)
            raise

    # ================================
    # 预热任务优先级队列（任务 1.5）
    # ================================

    async def build_prewarming_queues(self, limit: int = 100) -> Dict[str, int]:
        """
        构建分层预热队列

        Args:
            limit: Top币种数量

        Returns:
            Dict: 各队列的任务数量统计
        """
        try:
            # 清空现有队列
            self.high_priority_queue.clear()
            self.medium_priority_queue.clear()
            self.low_priority_queue.clear()

            # 获取Top币种
            top_coins = await self.fetch_top_coins(limit)

            # 分配到不同优先级队列
            for coin in top_coins:
                rank = coin["market_cap_rank"]

                if rank <= 10:
                    priority = PrewarmingPriority.HIGH
                    queue = self.high_priority_queue
                elif rank <= 100:
                    priority = PrewarmingPriority.MEDIUM
                    queue = self.medium_priority_queue
                else:
                    priority = PrewarmingPriority.LOW
                    queue = self.low_priority_queue

                task = PrewarmingTask(
                    coin_id=coin["id"],
                    symbol=coin["symbol"],
                    priority=priority,
                    market_cap_rank=rank,
                )
                queue.append(task)

            stats = {
                "high": len(self.high_priority_queue),
                "medium": len(self.medium_priority_queue),
                "low": len(self.low_priority_queue),
                "total": len(top_coins),
            }

            logger.info(
                f"预热队列构建完成: "
                f"高优先级={stats['high']}, "
                f"中优先级={stats['medium']}, "
                f"低优先级={stats['low']}"
            )

            return stats

        except Exception as e:
            logger.error(f"构建预热队列失败: {e}", exc_info=True)
            raise

    # ================================
    # 预热执行器（任务 1.6）
    # ================================

    async def prewarm_single_coin(self, task: PrewarmingTask) -> PrewarmingResult:
        """
        预热单个币种数据

        Args:
            task: 预热任务

        Returns:
            PrewarmingResult: 预热结果
        """
        start_time = datetime.utcnow()

        try:
            # 获取币种市场数据
            market_data = await coingecko_collector.get_coin_market_data(task.coin_id)

            if not market_data:
                raise Exception(f"币种 {task.coin_id} 数据为空")

            # 缓存到Redis（使用query_cache格式）
            cache_key = f"prewarmed:coin:{task.coin_id}"
            ttl = self._get_ttl_by_priority(task.priority)

            await cache_set(cache_key, market_data, ttl)

            # 计算耗时
            duration = (datetime.utcnow() - start_time).total_seconds()

            # 记录成功
            self.stats["total_success"] += 1

            logger.debug(
                f"预热成功: {task.symbol} ({task.coin_id}) "
                f"耗时={duration:.2f}s, TTL={ttl}s"
            )

            return PrewarmingResult(
                task=task,
                success=True,
                duration=duration,
                cached_data_size=len(str(market_data)),
            )

        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.stats["total_failed"] += 1

            logger.error(
                f"预热失败: {task.symbol} ({task.coin_id}) "
                f"错误={str(e)}"
            )

            return PrewarmingResult(
                task=task,
                success=False,
                duration=duration,
                error=str(e),
            )

    async def prewarm_batch(
        self,
        tasks: List[PrewarmingTask],
        max_concurrent: int = 10
    ) -> List[PrewarmingResult]:
        """
        批量并发预热

        Args:
            tasks: 预热任务列表
            max_concurrent: 最大并发数

        Returns:
            List[PrewarmingResult]: 预热结果列表
        """
        if not tasks:
            return []

        # 使用信号量控制并发
        semaphore = asyncio.Semaphore(max_concurrent)

        async def prewarm_with_semaphore(task: PrewarmingTask) -> PrewarmingResult:
            async with semaphore:
                return await self.prewarm_single_coin(task)

        # 并发执行所有任务
        results = await asyncio.gather(
            *[prewarm_with_semaphore(task) for task in tasks],
            return_exceptions=True
        )

        # 处理异常结果
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # 转换异常为失败结果
                final_results.append(PrewarmingResult(
                    task=tasks[i],
                    success=False,
                    duration=0.0,
                    error=str(result),
                ))
            else:
                final_results.append(result)

        return final_results

    # ================================
    # 失败重试机制（任务 1.7）
    # ================================

    async def prewarm_with_retry(self, task: PrewarmingTask) -> PrewarmingResult:
        """
        预热单个币种（带重试机制）

        Args:
            task: 预热任务

        Returns:
            PrewarmingResult: 最终结果（成功或重试耗尽后失败）
        """
        for attempt in range(self.max_retries):
            task.retry_count = attempt
            task.last_attempt = datetime.utcnow()

            result = await self.prewarm_single_coin(task)

            if result.success:
                return result

            # 失败，检查是否还有重试次数
            if attempt < self.max_retries - 1:
                delay = self.retry_delays[attempt]
                logger.warning(
                    f"预热失败，{delay}秒后重试 "
                    f"({attempt + 1}/{self.max_retries}): "
                    f"{task.symbol} - {result.error}"
                )
                await asyncio.sleep(delay)
            else:
                logger.error(
                    f"预热失败，已达最大重试次数: "
                    f"{task.symbol} - {result.error}"
                )

        return result

    async def prewarm_batch_with_retry(
        self,
        tasks: List[PrewarmingTask],
        max_concurrent: int = 10
    ) -> List[PrewarmingResult]:
        """
        批量预热（带重试）

        Args:
            tasks: 预热任务列表
            max_concurrent: 最大并发数

        Returns:
            List[PrewarmingResult]: 预热结果列表
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def prewarm_with_semaphore_and_retry(
            task: PrewarmingTask
        ) -> PrewarmingResult:
            async with semaphore:
                return await self.prewarm_with_retry(task)

        results = await asyncio.gather(
            *[prewarm_with_semaphore_and_retry(task) for task in tasks],
            return_exceptions=True
        )

        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(PrewarmingResult(
                    task=tasks[i],
                    success=False,
                    duration=0.0,
                    error=str(result),
                ))
            else:
                final_results.append(result)

        return final_results

    # ================================
    # 核心执行流程
    # ================================

    async def run_prewarming(
        self,
        priority: Optional[PrewarmingPriority] = None
    ) -> Dict[str, Any]:
        """
        执行预热任务

        Args:
            priority: 指定优先级（None表示全部）

        Returns:
            Dict: 执行统计
                - total: 总任务数
                - success: 成功数
                - failed: 失败数
                - duration: 总耗时（秒）
        """
        start_time = datetime.utcnow()

        # 选择要执行的队列
        if priority == PrewarmingPriority.HIGH:
            tasks = self.high_priority_queue
        elif priority == PrewarmingPriority.MEDIUM:
            tasks = self.medium_priority_queue
        elif priority == PrewarmingPriority.LOW:
            tasks = self.low_priority_queue
        else:
            # 全部队列（按优先级顺序）
            tasks = (
                self.high_priority_queue +
                self.medium_priority_queue +
                self.low_priority_queue
            )

        if not tasks:
            logger.warning("没有待预热的任务")
            return {"total": 0, "success": 0, "failed": 0, "duration": 0.0}

        logger.info(f"开始预热: {len(tasks)}个任务")

        # 批量预热（带重试）
        results = await self.prewarm_batch_with_retry(
            tasks,
            max_concurrent=self.concurrency_limit
        )

        # 统计结果
        total = len(results)
        success = sum(1 for r in results if r.success)
        failed = total - success
        duration = (datetime.utcnow() - start_time).total_seconds()

        # 更新全局统计
        self.stats["total_prewarmed"] += total
        self.stats["last_run"] = datetime.utcnow().isoformat()
        self.stats["cached_coins"] = success

        logger.info(
            f"预热完成: "
            f"成功={success}/{total}, "
            f"失败={failed}, "
            f"耗时={duration:.2f}s"
        )

        return {
            "total": total,
            "success": success,
            "failed": failed,
            "success_rate": success / total if total > 0 else 0.0,
            "duration": duration,
            "timestamp": datetime.utcnow().isoformat(),
        }

    # ================================
    # 辅助方法
    # ================================

    def _get_ttl_by_priority(self, priority: PrewarmingPriority) -> int:
        """根据优先级获取TTL（秒）"""
        ttl_map = {
            PrewarmingPriority.HIGH: 60,      # 1分钟
            PrewarmingPriority.MEDIUM: 300,   # 5分钟
            PrewarmingPriority.LOW: 900,      # 15分钟
        }
        return ttl_map.get(priority, 300)

    def get_stats(self) -> Dict[str, Any]:
        """获取预热统计信息"""
        return {
            **self.stats,
            "queue_sizes": {
                "high": len(self.high_priority_queue),
                "medium": len(self.medium_priority_queue),
                "low": len(self.low_priority_queue),
            },
        }

    async def add_task(
        self,
        coin_id: str,
        priority: PrewarmingPriority = PrewarmingPriority.MEDIUM,
        force_refresh: bool = False
    ) -> bool:
        """
        动态添加预热任务到队列

        Args:
            coin_id: CoinGecko币种ID
            priority: 优先级
            force_refresh: 是否强制刷新（忽略缓存）

        Returns:
            bool: 是否成功添加
        """
        try:
            # 检查是否已在队列中
            all_queues = [
                self.high_priority_queue,
                self.medium_priority_queue,
                self.low_priority_queue
            ]
            for queue in all_queues:
                if any(task.coin_id == coin_id for task in queue):
                    logger.debug(f"任务已存在: {coin_id}")
                    return False

            # 创建任务（简化版，不需要完整币种信息）
            task = PrewarmingTask(
                coin_id=coin_id,
                symbol=coin_id.upper()[:10],  # 临时symbol
                priority=priority,
                market_cap_rank=0  # 动态添加的任务不设置排名
            )

            # 添加到对应队列
            if priority == PrewarmingPriority.HIGH:
                self.high_priority_queue.append(task)
            elif priority == PrewarmingPriority.MEDIUM:
                self.medium_priority_queue.append(task)
            else:
                self.low_priority_queue.append(task)

            logger.debug(f"任务已添加: {coin_id} (priority={priority.value})")
            return True

        except Exception as e:
            logger.error(f"添加任务失败: {coin_id}, error={e}")
            return False

    def get_status(self) -> Dict[str, Any]:
        """
        获取预热系统状态（用于健康检查）

        Returns:
            Dict: 状态信息
                - queue_size: 队列总大小
                - is_running: 是否正在运行
                - stats: 统计信息
        """
        total_queue_size = (
            len(self.high_priority_queue) +
            len(self.medium_priority_queue) +
            len(self.low_priority_queue)
        )

        return {
            "queue_size": total_queue_size,
            "queue_breakdown": {
                "high": len(self.high_priority_queue),
                "medium": len(self.medium_priority_queue),
                "low": len(self.low_priority_queue),
            },
            "is_running": False,  # 注：Celery任务是独立的，无法直接检测
            "stats": self.stats.copy(),
        }


# ================================
# 全局实例
# ================================

prewarming_manager = PrewarmingManager()


# ================================
# 便捷函数
# ================================


def get_prewarming_manager() -> PrewarmingManager:
    """
    获取全局预热管理器实例

    Returns:
        PrewarmingManager: 预热管理器实例
    """
    return prewarming_manager


async def initialize_prewarming(limit: int = 100) -> Dict[str, int]:
    """
    初始化预热系统（构建队列）

    Args:
        limit: Top币种数量

    Returns:
        Dict: 队列统计
    """
    return await prewarming_manager.build_prewarming_queues(limit)


async def run_top10_prewarming() -> Dict[str, Any]:
    """
    执行Top 10币种预热（高优先级）

    Returns:
        Dict: 执行统计
    """
    return await prewarming_manager.run_prewarming(PrewarmingPriority.HIGH)


async def run_top100_prewarming() -> Dict[str, Any]:
    """
    执行Top 100币种预热（中优先级）

    Returns:
        Dict: 执行统计
    """
    return await prewarming_manager.run_prewarming(PrewarmingPriority.MEDIUM)


async def run_full_prewarming() -> Dict[str, Any]:
    """
    执行全量预热

    Returns:
        Dict: 执行统计
    """
    return await prewarming_manager.run_prewarming()


def get_prewarming_stats() -> Dict[str, Any]:
    """
    获取预热统计

    Returns:
        Dict: 统计信息
    """
    return prewarming_manager.get_stats()
