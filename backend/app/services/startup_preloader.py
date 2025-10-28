"""
启动预加载器 (Stage 4 任务 4.1)

应用启动时自动预热Top热门币种，确保首次请求有缓存数据
"""
import asyncio
import logging
from typing import List, Dict, Any
from datetime import datetime

from app.services.prewarming_scheduler import get_scheduler
from app.services.cache_prewarming import (
    get_prewarming_manager,
    PrewarmingPriority
)

logger = logging.getLogger(__name__)


# ================================
# 启动预加载器
# ================================

class StartupPreloader:
    """
    应用启动时的缓存预加载器

    功能：
    - 从调度器获取高优先级币种列表
    - 并发预热Top 10热门币种
    - 控制并发数（避免启动时过载）
    - 超时控制（不阻塞应用启动）
    - 失败不影响启动流程
    """

    # 并发控制
    MAX_CONCURRENT = 5  # 最多5个并发预热任务
    TIMEOUT_SECONDS = 30  # 预加载超时时间

    def __init__(self):
        """初始化预加载器"""
        self.scheduler = get_scheduler()
        self.prewarming_manager = get_prewarming_manager()
        self._stats = {
            "started_at": None,
            "completed_at": None,
            "coins_prewarmed": 0,
            "coins_failed": 0,
            "duration_seconds": 0,
            "timed_out": False
        }

    async def run(self) -> Dict[str, Any]:
        """
        执行启动预加载

        Returns:
            Dict: 预加载统计信息
        """
        self._stats["started_at"] = datetime.now()
        logger.info("🚀 Starting startup preloading...")

        try:
            # 使用超时控制
            result = await asyncio.wait_for(
                self._preload_with_concurrency_control(),
                timeout=self.TIMEOUT_SECONDS
            )

            self._stats["completed_at"] = datetime.now()
            duration = (self._stats["completed_at"] - self._stats["started_at"]).total_seconds()
            self._stats["duration_seconds"] = round(duration, 2)

            logger.info(
                f"✅ Startup preloading completed: "
                f"{self._stats['coins_prewarmed']} success, "
                f"{self._stats['coins_failed']} failed, "
                f"{duration:.2f}s"
            )

            return self._stats

        except asyncio.TimeoutError:
            self._stats["timed_out"] = True
            self._stats["completed_at"] = datetime.now()
            duration = (self._stats["completed_at"] - self._stats["started_at"]).total_seconds()
            self._stats["duration_seconds"] = round(duration, 2)

            logger.warning(
                f"⚠️  Startup preloading timed out after {self.TIMEOUT_SECONDS}s. "
                f"Prewarmed {self._stats['coins_prewarmed']} coins."
            )

            return self._stats

        except Exception as e:
            logger.error(f"❌ Startup preloading failed: {e}", exc_info=True)
            self._stats["completed_at"] = datetime.now()

            # 失败不影响应用启动
            return self._stats

    async def _preload_with_concurrency_control(self) -> None:
        """
        并发控制的预加载流程

        使用Semaphore限制并发数
        """
        # 1. 获取高优先级列表（Top 10）
        coin_ids = await self.scheduler.get_priority_list(PrewarmingPriority.HIGH)

        if not coin_ids:
            logger.warning("No high-priority coins found for startup preloading")
            return

        logger.info(f"Found {len(coin_ids)} coins to prewarm")

        # 2. 创建并发控制信号量
        semaphore = asyncio.Semaphore(self.MAX_CONCURRENT)

        # 3. 创建预热任务
        tasks = [
            self._prewarm_single_coin(coin_id, semaphore)
            for coin_id in coin_ids
        ]

        # 4. 并发执行所有任务
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 5. 统计结果
        for result in results:
            if isinstance(result, Exception):
                self._stats["coins_failed"] += 1
            elif result:
                self._stats["coins_prewarmed"] += 1
            else:
                self._stats["coins_failed"] += 1

    async def _prewarm_single_coin(
        self,
        coin_id: str,
        semaphore: asyncio.Semaphore
    ) -> bool:
        """
        预热单个币种（带并发控制）

        Args:
            coin_id: 币种ID
            semaphore: 并发控制信号量

        Returns:
            bool: 是否成功
        """
        async with semaphore:
            try:
                logger.debug(f"Prewarming {coin_id}...")

                success = await self.prewarming_manager.add_task(
                    coin_id=coin_id,
                    priority=PrewarmingPriority.HIGH,
                    force_refresh=False  # 启动时不强制刷新，使用现有缓存
                )

                if success:
                    logger.debug(f"✓ {coin_id} prewarmed successfully")
                else:
                    logger.warning(f"✗ {coin_id} prewarming failed")

                return success

            except Exception as e:
                logger.error(f"Error prewarming {coin_id}: {e}")
                return False

    def get_stats(self) -> Dict[str, Any]:
        """
        获取预加载统计信息

        Returns:
            Dict: 统计信息
        """
        return self._stats.copy()


# ================================
# 全局实例（单例）
# ================================

_preloader_instance = None


def get_preloader() -> StartupPreloader:
    """
    获取全局预加载器实例（单例模式）

    Returns:
        StartupPreloader: 预加载器实例
    """
    global _preloader_instance

    if _preloader_instance is None:
        _preloader_instance = StartupPreloader()
        logger.info("Global StartupPreloader instance created")

    return _preloader_instance


# ================================
# 便捷函数
# ================================

async def run_startup_preloading() -> Dict[str, Any]:
    """
    便捷函数：运行启动预加载

    在应用启动时调用此函数

    Returns:
        Dict: 预加载统计信息
    """
    preloader = get_preloader()
    return await preloader.run()
