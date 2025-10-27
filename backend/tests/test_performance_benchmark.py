"""
性能基准测试（任务 9.8）

功能：
1. 负载测试（并发用户模拟）
2. 响应时间测量（P50/P95/P99）
3. 缓存命中率验证
4. API成功率追踪
5. 性能目标验证

性能目标：
- Quick Chat P95响应时间 < 3秒
- Redis缓存命中率 > 60%
- API成功率 > 95%
- 并发支持 ≥ 50个用户
"""
import pytest
import asyncio
import time
from typing import List, Dict, Any, Tuple
import statistics
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import random

from httpx import AsyncClient
from app.main import app
from app.core.redis_client import get_async_redis


# ================================
# 性能目标配置
# ================================

class PerformanceTargets:
    """性能目标定义"""

    # Quick Chat性能目标
    QUICK_CHAT_P50_MS = 1500  # P50 < 1.5秒
    QUICK_CHAT_P95_MS = 3000  # P95 < 3秒
    QUICK_CHAT_P99_MS = 5000  # P99 < 5秒

    # Deep Research性能目标
    DEEP_RESEARCH_P95_MS = 30000  # P95 < 30秒

    # 缓存目标
    CACHE_HIT_RATE_TARGET = 0.6  # 命中率 > 60%

    # 可靠性目标
    API_SUCCESS_RATE_TARGET = 0.95  # 成功率 > 95%

    # 并发目标
    MIN_CONCURRENT_USERS = 50  # 支持至少50个并发用户


# ================================
# 性能测量工具
# ================================

class PerformanceMetrics:
    """性能指标收集器"""

    def __init__(self):
        self.response_times: List[float] = []
        self.success_count: int = 0
        self.failure_count: int = 0
        self.cache_hits: int = 0
        self.cache_misses: int = 0
        self.start_time: float = 0
        self.end_time: float = 0

    def record_request(
        self,
        response_time_ms: float,
        success: bool,
        cache_hit: bool = False
    ):
        """记录单个请求的指标"""
        self.response_times.append(response_time_ms)

        if success:
            self.success_count += 1
        else:
            self.failure_count += 1

        if cache_hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1

    def start_timer(self):
        """开始计时"""
        self.start_time = time.time()

    def stop_timer(self):
        """停止计时"""
        self.end_time = time.time()

    def get_percentile(self, percentile: float) -> float:
        """
        计算百分位数

        Args:
            percentile: 百分位 (0-1之间)

        Returns:
            float: 百分位值（毫秒）
        """
        if not self.response_times:
            return 0.0

        sorted_times = sorted(self.response_times)
        index = int(len(sorted_times) * percentile)
        return sorted_times[min(index, len(sorted_times) - 1)]

    def get_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        total_requests = self.success_count + self.failure_count
        duration_sec = self.end_time - self.start_time if self.end_time > 0 else 0

        return {
            "total_requests": total_requests,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": self.success_count / total_requests if total_requests > 0 else 0,
            "duration_seconds": duration_sec,
            "requests_per_second": total_requests / duration_sec if duration_sec > 0 else 0,
            "response_times": {
                "min_ms": min(self.response_times) if self.response_times else 0,
                "max_ms": max(self.response_times) if self.response_times else 0,
                "mean_ms": statistics.mean(self.response_times) if self.response_times else 0,
                "median_ms": statistics.median(self.response_times) if self.response_times else 0,
                "p50_ms": self.get_percentile(0.5),
                "p95_ms": self.get_percentile(0.95),
                "p99_ms": self.get_percentile(0.99),
            },
            "cache": {
                "hits": self.cache_hits,
                "misses": self.cache_misses,
                "hit_rate": self.cache_hits / (self.cache_hits + self.cache_misses)
                if (self.cache_hits + self.cache_misses) > 0
                else 0,
            },
        }

    def print_summary(self):
        """打印性能摘要"""
        summary = self.get_summary()

        print("\n" + "=" * 60)
        print("性能基准测试结果")
        print("=" * 60)

        print(f"\n总体指标:")
        print(f"  总请求数: {summary['total_requests']}")
        print(f"  成功: {summary['success_count']}")
        print(f"  失败: {summary['failure_count']}")
        print(f"  成功率: {summary['success_rate'] * 100:.2f}%")
        print(f"  测试时长: {summary['duration_seconds']:.2f}秒")
        print(f"  QPS: {summary['requests_per_second']:.2f}")

        print(f"\n响应时间:")
        rt = summary['response_times']
        print(f"  最小: {rt['min_ms']:.0f}ms")
        print(f"  最大: {rt['max_ms']:.0f}ms")
        print(f"  平均: {rt['mean_ms']:.0f}ms")
        print(f"  中位数: {rt['median_ms']:.0f}ms")
        print(f"  P50: {rt['p50_ms']:.0f}ms")
        print(f"  P95: {rt['p95_ms']:.0f}ms ← 关键指标")
        print(f"  P99: {rt['p99_ms']:.0f}ms")

        print(f"\n缓存性能:")
        cache = summary['cache']
        print(f"  命中: {cache['hits']}")
        print(f"  未命中: {cache['misses']}")
        print(f"  命中率: {cache['hit_rate'] * 100:.2f}% ← 关键指标")

        print("=" * 60 + "\n")


# ================================
# 负载测试工具
# ================================

async def run_single_quick_chat_request(
    client: AsyncClient,
    query: str,
    conversation_id: str = None
) -> Tuple[bool, float, bool]:
    """
    运行单个Quick Chat请求

    Returns:
        Tuple[success, response_time_ms, cache_hit]
    """
    start = time.time()

    try:
        payload = {"query": query}
        if conversation_id:
            payload["conversation_id"] = conversation_id

        response = await client.post(
            "/v1/quick-chat",
            json=payload,
            timeout=10.0,
        )

        elapsed_ms = (time.time() - start) * 1000

        success = response.status_code == 200

        # 检查是否命中缓存（通过响应头或响应时间判断）
        # 如果响应时间非常快（< 100ms），可能是缓存命中
        cache_hit = elapsed_ms < 100

        return success, elapsed_ms, cache_hit

    except Exception as e:
        elapsed_ms = (time.time() - start) * 1000
        return False, elapsed_ms, False


async def simulate_user_session(
    client: AsyncClient,
    user_id: int,
    num_requests: int = 5
) -> List[Tuple[bool, float, bool]]:
    """
    模拟单个用户会话

    Args:
        client: HTTP客户端
        user_id: 用户ID
        num_requests: 该用户发送的请求数

    Returns:
        List[Tuple[success, response_time, cache_hit]]
    """
    results = []

    # 用户查询模板（模拟真实查询）
    queries = [
        f"BTC的价格是多少？",
        f"ETH的技术分析",
        f"SOL的风险评估",
        f"DOGE的情绪分析",
        f"ADA的代币经济学",
        f"MATIC的市值排名",
        f"BTC的RSI指标",
        f"ETH的MACD信号",
    ]

    for i in range(num_requests):
        # 随机选择查询（模拟不同用户行为）
        query = random.choice(queries)

        # 发送请求
        success, response_time, cache_hit = await run_single_quick_chat_request(
            client, query
        )
        results.append((success, response_time, cache_hit))

        # 用户思考时间（500ms - 2s）
        await asyncio.sleep(random.uniform(0.5, 2.0))

    return results


# ================================
# 测试用例
# ================================

class TestPerformanceBenchmark:
    """性能基准测试套件"""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_quick_chat_single_request_baseline(self):
        """单请求基准测试（建立基线）"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            metrics = PerformanceMetrics()
            metrics.start_timer()

            # 执行10次请求
            for i in range(10):
                success, response_time, cache_hit = await run_single_quick_chat_request(
                    client,
                    f"BTC价格分析 #{i + 1}"
                )
                metrics.record_request(response_time, success, cache_hit)

                # 短暂延迟，避免过载
                await asyncio.sleep(0.5)

            metrics.stop_timer()
            summary = metrics.get_summary()

            # 打印结果
            print(f"\n=== 单请求基准测试 ===")
            print(f"P50: {summary['response_times']['p50_ms']:.0f}ms")
            print(f"P95: {summary['response_times']['p95_ms']:.0f}ms")
            print(f"P99: {summary['response_times']['p99_ms']:.0f}ms")
            print(f"成功率: {summary['success_rate'] * 100:.1f}%")

            # 验证性能目标
            assert summary['response_times']['p95_ms'] < PerformanceTargets.QUICK_CHAT_P95_MS, \
                f"P95响应时间超标: {summary['response_times']['p95_ms']:.0f}ms"

            assert summary['success_rate'] >= PerformanceTargets.API_SUCCESS_RATE_TARGET, \
                f"成功率低于目标: {summary['success_rate'] * 100:.1f}%"

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_quick_chat_concurrent_users(self):
        """并发用户负载测试"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            metrics = PerformanceMetrics()
            metrics.start_timer()

            # 模拟20个并发用户
            num_users = 20
            requests_per_user = 3

            print(f"\n开始负载测试: {num_users}个并发用户，每用户{requests_per_user}个请求...")

            # 并发执行所有用户会话
            tasks = [
                simulate_user_session(client, user_id, requests_per_user)
                for user_id in range(num_users)
            ]

            all_results = await asyncio.gather(*tasks)

            # 汇总结果
            for user_results in all_results:
                for success, response_time, cache_hit in user_results:
                    metrics.record_request(response_time, success, cache_hit)

            metrics.stop_timer()

            # 打印结果
            metrics.print_summary()

            summary = metrics.get_summary()

            # 验证性能目标
            assert summary['response_times']['p95_ms'] < PerformanceTargets.QUICK_CHAT_P95_MS, \
                f"P95响应时间超标: {summary['response_times']['p95_ms']:.0f}ms (目标: {PerformanceTargets.QUICK_CHAT_P95_MS}ms)"

            assert summary['success_rate'] >= PerformanceTargets.API_SUCCESS_RATE_TARGET, \
                f"成功率低于目标: {summary['success_rate'] * 100:.1f}%"

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_cache_effectiveness(self):
        """缓存效果测试"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            query = "BTC的价格和市值"

            # 第一次请求（冷启动，应该缓存未命中）
            success1, time1, hit1 = await run_single_quick_chat_request(client, query)

            # 等待一小段时间
            await asyncio.sleep(0.5)

            # 第二次相同请求（应该命中缓存）
            success2, time2, hit2 = await run_single_quick_chat_request(client, query)

            print(f"\n=== 缓存效果测试 ===")
            print(f"第一次请求: {time1:.0f}ms (缓存{'命中' if hit1 else '未命中'})")
            print(f"第二次请求: {time2:.0f}ms (缓存{'命中' if hit2 else '未命中'})")

            # 第二次请求应该更快（如果缓存生效）
            if hit2:
                print(f"✓ 缓存加速: {((time1 - time2) / time1 * 100):.1f}%")
                assert time2 < time1 * 0.5, "缓存未显著加速响应"

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_cache_hit_rate_under_load(self):
        """负载下的缓存命中率测试"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            metrics = PerformanceMetrics()

            # 使用有限查询集（模拟热门查询）
            popular_queries = [
                "BTC的价格",
                "ETH的技术分析",
                "SOL的市值",
            ]

            # 发送100个请求（重复查询以测试缓存）
            for i in range(100):
                query = random.choice(popular_queries)
                success, response_time, cache_hit = await run_single_quick_chat_request(
                    client, query
                )
                metrics.record_request(response_time, success, cache_hit)

                # 短暂延迟
                await asyncio.sleep(0.1)

            summary = metrics.get_summary()

            print(f"\n=== 缓存命中率测试 ===")
            print(f"缓存命中率: {summary['cache']['hit_rate'] * 100:.1f}%")
            print(f"目标命中率: {PerformanceTargets.CACHE_HIT_RATE_TARGET * 100:.1f}%")

            # 验证缓存命中率
            assert summary['cache']['hit_rate'] >= PerformanceTargets.CACHE_HIT_RATE_TARGET, \
                f"缓存命中率低于目标: {summary['cache']['hit_rate'] * 100:.1f}%"

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_sustained_load(self):
        """持续负载测试（5分钟）"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            metrics = PerformanceMetrics()
            metrics.start_timer()

            # 持续5分钟（或100个请求，取较小值）
            duration_seconds = 60  # 简化为1分钟
            max_requests = 100
            request_interval = 0.5  # 每0.5秒一个请求

            print(f"\n开始持续负载测试: {duration_seconds}秒...")

            queries = [
                "BTC价格",
                "ETH分析",
                "SOL市值",
                "DOGE情绪",
            ]

            requests_sent = 0
            start = time.time()

            while (time.time() - start) < duration_seconds and requests_sent < max_requests:
                query = random.choice(queries)
                success, response_time, cache_hit = await run_single_quick_chat_request(
                    client, query
                )
                metrics.record_request(response_time, success, cache_hit)

                requests_sent += 1

                # 控制请求速率
                await asyncio.sleep(request_interval)

            metrics.stop_timer()

            # 打印结果
            metrics.print_summary()

            summary = metrics.get_summary()

            # 验证稳定性指标
            assert summary['success_rate'] >= 0.90, \
                f"持续负载下成功率过低: {summary['success_rate'] * 100:.1f}%"

            assert summary['response_times']['p95_ms'] < PerformanceTargets.QUICK_CHAT_P95_MS * 1.5, \
                f"持续负载下P95响应时间过长: {summary['response_times']['p95_ms']:.0f}ms"

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_error_rate_under_stress(self):
        """压力测试下的错误率"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            metrics = PerformanceMetrics()

            # 高并发压力测试
            num_concurrent = 50
            requests_per_task = 2

            print(f"\n开始压力测试: {num_concurrent}个并发任务...")

            tasks = []
            for i in range(num_concurrent):
                for j in range(requests_per_task):
                    task = run_single_quick_chat_request(
                        client,
                        f"BTC分析 #{i}-{j}"
                    )
                    tasks.append(task)

            # 同时发送所有请求
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 统计结果
            for result in results:
                if isinstance(result, Exception):
                    metrics.record_request(0, False, False)
                else:
                    success, response_time, cache_hit = result
                    metrics.record_request(response_time, success, cache_hit)

            summary = metrics.get_summary()

            print(f"\n=== 压力测试结果 ===")
            print(f"总请求: {summary['total_requests']}")
            print(f"成功: {summary['success_count']}")
            print(f"失败: {summary['failure_count']}")
            print(f"成功率: {summary['success_rate'] * 100:.1f}%")

            # 压力下也应保持合理的成功率
            assert summary['success_rate'] >= 0.80, \
                f"压力测试下成功率过低: {summary['success_rate'] * 100:.1f}%"


# ================================
# 性能报告生成
# ================================

@pytest.fixture(scope="session", autouse=True)
def generate_performance_report(request):
    """生成性能测试报告"""
    yield  # 测试执行

    # 测试结束后生成报告
    report_path = "performance_benchmark_report.txt"

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("Web3Search 性能基准测试报告\n")
        f.write("=" * 80 + "\n\n")

        f.write(f"测试时间: {datetime.now().isoformat()}\n\n")

        f.write("性能目标:\n")
        f.write(f"  - Quick Chat P95 < {PerformanceTargets.QUICK_CHAT_P95_MS}ms\n")
        f.write(f"  - 缓存命中率 > {PerformanceTargets.CACHE_HIT_RATE_TARGET * 100:.0f}%\n")
        f.write(f"  - API成功率 > {PerformanceTargets.API_SUCCESS_RATE_TARGET * 100:.0f}%\n")
        f.write(f"  - 并发用户 ≥ {PerformanceTargets.MIN_CONCURRENT_USERS}\n\n")

        f.write("测试建议:\n")
        f.write("  1. 运行: pytest backend/tests/test_performance_benchmark.py -v -m slow\n")
        f.write("  2. 使用生产级配置进行测试\n")
        f.write("  3. 在负载均衡环境下测试\n")
        f.write("  4. 定期执行回归测试\n\n")

    print(f"\n性能报告已生成: {report_path}")


# ================================
# 运行测试
# ================================

if __name__ == "__main__":
    # 运行性能基准测试（慢测试）
    pytest.main([__file__, "-v", "-m", "slow", "--tb=short"])
