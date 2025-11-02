"""
Locust负载测试脚本
测试Web3 Search API的性能和并发能力
"""
from locust import HttpUser, task, between, events
import random
import json
import time
import gevent
from gevent.pool import Pool


class Web3SearchUser(HttpUser):
    """
    Web3 Search API用户行为模拟

    模拟用户使用Quick Chat和Deep Research功能
    """

    # 请求间隔：0.5-2秒 (提高并发能力)
    wait_time = between(0.5, 2)

    # 测试的加密货币符号列表 (扩展)
    crypto_symbols = [
        "BTC", "ETH", "SOL", "UNI", "AAVE", "LINK", "MATIC", "ARB", "OP", "AVAX",
        "DOT", "ADA", "BNB", "XRP", "LTC", "BCH", "FIL", "ATOM", "NEAR", "FTM",
        "SAND", "MANA", "AXS", "GALA", "ENJ", "CHZ", "LRC", "KSM", "RUNE", "ONE"
    ]
    
    # 连接池配置 (支持高并发)
    pool = Pool(100)  # 每个用户最多100个并发连接

    def on_start(self):
        """用户开始测试时执行"""
        # 健康检查
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure("Health check failed")

    @task(8)
    def quick_chat(self):
        """
        Quick Chat任务（权重8）
        模拟用户提问快速问答
        """
        questions = [
            "What is the current price of Bitcoin?",
            "Tell me about Ethereum's recent performance",
            "How does Uniswap work?",
            "What are the differences between Layer 1 and Layer 2?",
            "Explain DeFi to me",
            "What is Solana's ecosystem like?",
            "How do yield farms work?",
            "What are the risks of DeFi?",
            "Explain NFTs to me",
            "What is blockchain technology?",
            "How do smart contracts work?",
            "What is staking in crypto?",
            "Tell me about centralized exchanges",
            "What are liquidity pools?",
            "How does governance work in DAOs?"
        ]

        question = random.choice(questions)

        payload = {
            "query": question,
            "conversation_id": None,
        }

        start_time = time.time()

        with self.client.post(
            "/api/v1/chat/quick-chat",
            json=payload,
            catch_response=True,
            name="/api/v1/chat/quick-chat",
        ) as response:
            duration = (time.time() - start_time) * 1000  # ms

            if response.status_code == 200:
                try:
                    data = response.json()
                    if "answer" in data and len(data["answer"]) > 0:
                        response.success()
                        # 记录响应时间 (更严格的标准)
                        if duration < 2000:
                            print(f"✅ Quick Chat: {duration:.0f}ms (EXCELLENT)")
                        elif duration < 3000:
                            print(f"✅ Quick Chat: {duration:.0f}ms (GOOD)")
                        elif duration < 5000:
                            print(f"⚠️ Quick Chat: {duration:.0f}ms (SLOW)")
                        else:
                            print(f"❌ Quick Chat: {duration:.0f}ms (TOO SLOW)")
                    else:
                        response.failure("Empty answer received")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            elif response.status_code == 429:
                # 速率限制：不视为失败
                print(f"⚠️ Quick Chat: Rate limited")
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")

    @task(4)
    def get_hotspots(self):
        """
        获取热点任务（权重4）
        模拟用户查看市场热点
        """
        with self.client.get(
            "/api/v1/trending/hotspots?limit=10",
            catch_response=True,
            name="/api/v1/trending/hotspots",
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "hotspots" in data and len(data["hotspots"]) > 0:
                        response.success()
                    else:
                        response.failure("Empty hotspots list")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Status code: {response.status_code}")

    @task(3)
    def search_autocomplete(self):
        """
        搜索自动补全任务（权重3）
        模拟用户搜索加密货币
        """
        query = random.choice(self.crypto_symbols[:15])  # 使用主要币种

        with self.client.get(
            f"/api/v1/search/autocomplete?q={query}",
            catch_response=True,
            name="/api/v1/search/autocomplete",
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "results" in data:
                        response.success()
                    else:
                        response.failure("Missing results field")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Status code: {response.status_code}")

    @task(1)
    def get_market_data(self):
        """
        获取市场数据任务（权重1）
        模拟用户查看实时市场数据
        """
        symbol = random.choice(self.crypto_symbols[:10])
        
        with self.client.get(
            f"/api/v1/market/data?symbol={symbol}",
            catch_response=True,
            name="/api/v1/market/data",
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "price" in data or "market_data" in data:
                        response.success()
                    else:
                        response.failure("Missing market data")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Status code: {response.status_code}")

    @task(1)
    def deep_research(self):
        """
        Deep Research任务（权重1）
        模拟用户生成深度研究报告（最耗时的操作）

        注意：这个操作可能需要30-60秒，并且有速率限制（3次/小时）
        """
        symbol = random.choice(self.crypto_symbols)

        payload = {
            "query": symbol,
            "conversation_id": None,
        }

        # 设置较长的超时时间（90秒）
        start_time = time.time()

        with self.client.post(
            "/api/v1/chat/deep-research",
            json=payload,
            timeout=90,
            catch_response=True,
            name="/api/v1/chat/deep-research",
        ) as response:
            duration = (time.time() - start_time) * 1000  # ms

            if response.status_code == 200:
                try:
                    data = response.json()
                    if "report" in data and len(data["report"]) > 0:
                        response.success()
                        print(f"✅ Deep Research ({symbol}): {duration:.0f}ms")
                    else:
                        response.failure("Empty report received")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            elif response.status_code == 429:
                # 速率限制：Deep Research有更严格的限制
                print(f"⚠️ Deep Research ({symbol}): Rate limited (expected)")
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")


# ================================
# 自定义事件处理器
# ================================


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """测试开始时触发"""
    print("\n" + "=" * 60)
    print("🚀 Web3 Search Load Test Starting")
    print("=" * 60)
    print(f"Target: {environment.host}")
    print(f"Users: {environment.runner.target_user_count if hasattr(environment.runner, 'target_user_count') else 'Unknown'}")
    print("=" * 60 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """测试结束时触发"""
    print("\n" + "=" * 60)
    print("✅ Web3 Search Load Test Completed")
    print("=" * 60)

    stats = environment.stats

    print("\n📊 Summary:")
    print(f"Total Requests: {stats.total.num_requests}")
    print(f"Failed Requests: {stats.total.num_failures}")
    print(f"Failure Rate: {stats.total.fail_ratio * 100:.2f}%")
    print(f"Avg Response Time: {stats.total.avg_response_time:.0f}ms")
    print(f"Min Response Time: {stats.total.min_response_time:.0f}ms")
    print(f"Max Response Time: {stats.total.max_response_time:.0f}ms")
    print(f"RPS: {stats.total.total_rps:.2f}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    """
    运行负载测试

    基本用法:
        locust -f locustfile.py --host=http://localhost:8000

    Web UI模式（推荐）:
        locust -f locustfile.py --host=http://localhost:8000 --web-port=8089

    # 无头模式（1000并发用户，持续300秒）:
        locust -f locustfile.py --host=http://localhost:8000 --headless --users 1000 --spawn-rate 50 --run-time 300s

    # 高负载测试（1500并发用户，持续600秒）:
        locust -f locustfile.py --host=http://localhost:8000 --headless --users 1500 --spawn-rate 100 --run-time 600s

    # 峰值测试（2000并发用户，突发流量）:
        locust -f locustfile.py --host=http://localhost:8000 --headless --users 2000 --spawn-rate 200 --run-time 180s

    测试生产环境:
        locust -f locustfile.py --host=https://web3search-api.onrender.com --headless --users 50 --spawn-rate 5 --run-time 120s
    """
    import sys

    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║  Web3 Search API - Load Testing with Locust                 ║
    ╠══════════════════════════════════════════════════════════════╣
    ║  Usage:                                                      ║
    ║                                                              ║
    ║  1. Web UI mode (recommended):                               ║
    ║     locust -f locustfile.py --host=<API_URL>                 ║
    ║     Then open: http://localhost:8089                         ║
    ║                                                              ║
    ║  2. Headless mode (1000 users, 300s):                        ║
    ║     locust -f locustfile.py --host=<API_URL> \               ║
    ║       --headless --users 1000 --spawn-rate 50 --run-time 300s ║
    ║                                                              ║
    ║  3. High load test (1500 users, 600s):                     ║
    ║     locust -f locustfile.py --host=<API_URL> \               ║
    ║       --headless --users 1500 --spawn-rate 100 --run-time 600s║
    ║                                                              ║
    ║  4. Peak test (2000 users, burst):                         ║
    ║     locust -f locustfile.py --host=<API_URL> \               ║
    ║       --headless --users 2000 --spawn-rate 200 --run-time 180s║
    ║                                                              ║
    ║  Examples:                                                   ║
    ║     --host=http://localhost:8000                             ║
    ║     --host=https://web3search-api.onrender.com               ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
