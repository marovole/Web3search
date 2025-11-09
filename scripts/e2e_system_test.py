#!/usr/bin/env python3
"""
Web3search 端到端系统测试
Week 4 Day 16-17: 端到端功能测试

测试覆盖：
1. API 基础功能
2. 聊天 API（流式和非流式）
3. 搜索 API
4. 报告生成 API
5. 数据库集成
6. 错误处理
7. 性能基准测试
"""

import asyncio
import aiohttp
import json
import time
import sys
from typing import Dict, List, Any
import traceback

# 测试配置
API_BASE_URL = "https://web3search-api.marovole.workers.dev"
TIMEOUT = 30  # 30秒超时

class SystemTest:
    def __init__(self):
        self.session = None
        self.test_results = []
        self.performance_metrics = {}

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=TIMEOUT),
            headers={'Content-Type': 'application/json'}
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def log_result(self, test_name: str, passed: bool, details: str = "", response_time: float = 0):
        """记录测试结果"""
        result = {
            "test_name": test_name,
            "passed": passed,
            "details": details,
            "response_time_ms": round(response_time * 1000, 2),
            "timestamp": time.time()
        }
        self.test_results.append(result)

        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        if response_time > 0:
            print(f"    Response time: {result['response_time_ms']}ms")
        print()

    async def test_health_check(self):
        """测试健康检查端点"""
        start_time = time.time()
        try:
            async with self.session.get(f"{API_BASE_URL}/api/v1/health") as response:
                data = await response.json()
                response_time = time.time() - start_time

                passed = (
                    response.status == 200 and
                    data.get("status") == "healthy" and
                    "database" in data and
                    "cache" in data
                )

                details = f"Status: {data.get('status')}, DB: {data.get('database', {}).get('status')}, Cache: {data.get('cache', {}).get('status')}"
                self.log_result("Health Check API", passed, details, response_time)

        except Exception as e:
            response_time = time.time() - start_time
            self.log_result("Health Check API", False, f"Exception: {str(e)}", response_time)

    async def test_search_api(self):
        """测试搜索自动完成 API"""
        start_time = time.time()
        try:
            async with self.session.get(f"{API_BASE_URL}/api/v1/search/autocomplete?q=bitcoin") as response:
                data = await response.json()
                response_time = time.time() - start_time

                passed = (
                    response.status == 200 and
                    "query" in data and
                    "results" in data and
                    len(data["results"]) > 0
                )

                details = f"Query: {data.get('query')}, Results: {len(data.get('results', []))}"
                self.log_result("Search Autocomplete API", passed, details, response_time)

        except Exception as e:
            response_time = time.time() - start_time
            self.log_result("Search Autocomplete API", False, f"Exception: {str(e)}", response_time)

    async def test_chat_api_non_streaming(self):
        """测试聊天 API（非流式）"""
        start_time = time.time()
        try:
            payload = {
                "query": "What is Bitcoin?",
                "stream": False
            }

            async with self.session.post(f"{API_BASE_URL}/api/v1/chat/quick-chat", json=payload) as response:
                data = await response.json()
                response_time = time.time() - start_time

                passed = (
                    response.status == 200 and
                    "conversation_id" in data and
                    "content" in data and
                    len(data["content"]) > 50
                )

                details = f"Conversation ID: {data.get('conversation_id', 'N/A')}, Content length: {len(data.get('content', ''))}"
                self.log_result("Chat API (Non-streaming)", passed, details, response_time)

        except Exception as e:
            response_time = time.time() - start_time
            self.log_result("Chat API (Non-streaming)", False, f"Exception: {str(e)}", response_time)

    async def test_chat_api_streaming(self):
        """测试聊天 API（流式响应）"""
        start_time = time.time()
        chunks_received = 0
        try:
            payload = {
                "query": "Explain Ethereum in simple terms",
                "stream": True
            }

            async with self.session.post(f"{API_BASE_URL}/api/v1/chat/quick-chat", json=payload) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}")

                content_length = 0
                async for line in response.content:
                    if line:
                        line_str = line.decode('utf-8').strip()
                        if line_str.startswith('data: '):
                            chunks_received += 1
                            try:
                                chunk_data = json.loads(line_str[6:])
                                if chunk_data.get("delta"):
                                    content_length += len(chunk_data["delta"])
                            except:
                                pass

                response_time = time.time() - start_time
                passed = chunks_received > 0 and content_length > 100

                details = f"Chunks: {chunks_received}, Content length: {content_length}"
                self.log_result("Chat API (Streaming)", passed, details, response_time)

        except Exception as e:
            response_time = time.time() - start_time
            self.log_result("Chat API (Streaming)", False, f"Exception: {str(e)}", response_time)

    async def test_chat_history(self):
        """测试对话历史功能"""
        # 首先发送一条消息建立对话
        conversation_id = None
        try:
            payload1 = {"query": "Hello, this is a test message", "stream": False}
            async with self.session.post(f"{API_BASE_URL}/api/v1/chat/quick-chat", json=payload1) as response:
                data1 = await response.json()
                if response.status == 200:
                    conversation_id = data1.get("conversation_id")
        except:
            pass

        if not conversation_id:
            self.log_result("Chat History API", False, "Failed to create initial conversation")
            return

        # 使用相同 conversation_id 发送第二条消息
        start_time = time.time()
        try:
            payload2 = {
                "query": "Can you continue the conversation?",
                "conversation_id": conversation_id,
                "stream": False
            }

            async with self.session.post(f"{API_BASE_URL}/api/v1/chat/quick-chat", json=payload2) as response:
                data2 = await response.json()
                response_time = time.time() - start_time

                passed = (
                    response.status == 200 and
                    data2.get("conversation_id") == conversation_id and
                    len(data2.get("content", "")) > 20
                )

                details = f"Same conversation ID: {data2.get('conversation_id') == conversation_id}"
                self.log_result("Chat History API", passed, details, response_time)

        except Exception as e:
            response_time = time.time() - start_time
            self.log_result("Chat History API", False, f"Exception: {str(e)}", response_time)

    async def test_report_generation_api(self):
        """测试报告生成 API（流式）"""
        start_time = time.time()
        chunks_received = 0
        sections_completed = 0

        try:
            payload = {
                "topic": "Bitcoin Mining Overview",
                "sections": [
                    {
                        "id": "basics",
                        "title": "Mining Basics",
                        "description": "Introduction to Bitcoin mining"
                    }
                ],
                "save_to_database": False
            }

            async with self.session.post(f"{API_BASE_URL}/api/v1/reports/generate", json=payload) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}")

                async for line in response.content:
                    if line:
                        line_str = line.decode('utf-8').strip()
                        if line_str.startswith('data: '):
                            chunks_received += 1
                            try:
                                chunk_data = json.loads(line_str[6:])
                                if chunk_data.get("type") == "report_complete":
                                    sections_completed = len(chunk_data.get("completed_sections", []))
                            except:
                                pass

                response_time = time.time() - start_time
                passed = chunks_received > 0 and sections_completed > 0

                details = f"Chunks: {chunks_received}, Sections completed: {sections_completed}"
                self.log_result("Report Generation API", passed, details, response_time)

        except Exception as e:
            response_time = time.time() - start_time
            self.log_result("Report Generation API", False, f"Exception: {str(e)}", response_time)

    async def test_error_handling(self):
        """测试错误处理"""
        test_cases = [
            ("Invalid endpoint", "/api/v1/invalid-endpoint", "GET"),
            ("Invalid JSON", "/api/v1/chat/quick-chat", "POST", "invalid-json"),
            ("Missing required fields", "/api/v1/chat/quick-chat", "POST", {}),
        ]

        for test_name, endpoint, method, *args in test_cases:
            start_time = time.time()
            try:
                if method == "GET":
                    async with self.session.get(f"{API_BASE_URL}{endpoint}") as response:
                        response_time = time.time() - start_time
                        passed = response.status in [400, 404, 422]
                        details = f"Status: {response.status}"
                        self.log_result(f"Error Handling: {test_name}", passed, details, response_time)
                else:  # POST
                    if args[0] == "invalid-json":
                        async with self.session.post(f"{API_BASE_URL}{endpoint}", data="invalid-json") as response:
                            response_time = time.time() - start_time
                            passed = response.status == 400
                            details = f"Status: {response.status}"
                            self.log_result(f"Error Handling: {test_name}", passed, details, response_time)
                    else:  # Missing fields
                        async with self.session.post(f"{API_BASE_URL}{endpoint}", json=args[0]) as response:
                            response_time = time.time() - start_time
                            passed = response.status == 400
                            details = f"Status: {response.status}"
                            self.log_result(f"Error Handling: {test_name}", passed, details, response_time)
            except Exception as e:
                response_time = time.time() - start_time
                self.log_result(f"Error Handling: {test_name}", False, f"Exception: {str(e)}", response_time)

    async def test_performance_benchmarks(self):
        """性能基准测试"""
        # 测试健康检查的响应时间
        response_times = []
        for i in range(5):
            start_time = time.time()
            try:
                async with self.session.get(f"{API_BASE_URL}/api/v1/health") as response:
                    await response.json()
                    response_times.append(time.time() - start_time)
            except:
                pass

        if response_times:
            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)

            # 性能目标：健康检查 < 500ms
            passed = avg_time < 0.5 and max_time < 1.0

            details = f"Avg: {avg_time*1000:.1f}ms, Max: {max_time*1000:.1f}ms"
            self.log_result("Performance: Health Check", passed, details, avg_time)

            self.performance_metrics["health_check"] = {
                "avg_ms": avg_time * 1000,
                "max_ms": max_time * 1000,
                "passed": passed
            }

    async def run_all_tests(self):
        """运行所有测试"""
        print("🧪 Web3search 端到端系统测试开始")
        print("=" * 50)
        print(f"API Base URL: {API_BASE_URL}")
        print()

        # 基础功能测试
        await self.test_health_check()
        await self.test_search_api()
        await self.test_chat_api_non_streaming()
        await self.test_chat_api_streaming()
        await self.test_chat_history()
        await self.test_report_generation_api()

        # 错误处理测试
        await self.test_error_handling()

        # 性能测试
        await self.test_performance_benchmarks()

        # 测试总结
        self.print_summary()

    def print_summary(self):
        """打印测试总结"""
        print("=" * 50)
        print("🏁 测试总结")
        print("=" * 50)

        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["passed"])
        failed_tests = total_tests - passed_tests

        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests} ✅")
        print(f"失败: {failed_tests} ❌")
        print(f"通过率: {(passed_tests/total_tests)*100:.1f}%")
        print()

        if failed_tests > 0:
            print("❌ 失败的测试:")
            for result in self.test_results:
                if not result["passed"]:
                    print(f"  - {result['test_name']}: {result['details']}")
            print()

        # 性能指标
        if self.performance_metrics:
            print("⚡ 性能指标:")
            for metric, data in self.performance_metrics.items():
                status = "✅" if data["passed"] else "❌"
                print(f"  {metric}: {status} 平均 {data['avg_ms']:.1f}ms, 最大 {data['max_ms']:.1f}ms")
            print()

        # 建议
        if passed_tests == total_tests:
            print("🎉 所有测试通过！系统已准备好进入生产环境。")
        elif passed_tests / total_tests >= 0.9:
            print("⚠️  大部分测试通过，建议修复失败的测试后进入生产环境。")
        else:
            print("🚨 测试失败率较高，建议修复问题后再继续。")

async def main():
    """主函数"""
    try:
        async with SystemTest() as tester:
            await tester.run_all_tests()

        # 根据测试结果设置退出码
        failed_tests = sum(1 for r in tester.test_results if not r["passed"])
        total_tests = len(tester.test_results)

        if failed_tests == 0:
            sys.exit(0)  # 所有测试通过
        elif failed_tests / total_tests < 0.2:
            sys.exit(1)  # 少量失败，警告
        else:
            sys.exit(2)  # 大量失败，错误

    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 测试执行出错: {str(e)}")
        traceback.print_exc()
        sys.exit(3)

if __name__ == "__main__":
    asyncio.run(main())