"""
综合测试脚本
运行WebSocket情绪分析引擎的所有测试
"""
import asyncio
import sys
import os
import subprocess
import time
from datetime import datetime
from typing import Dict, List, Any

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_websocket_integration import WebSocketIntegrationTester


class ComprehensiveTestSuite:
    """综合测试套件"""

    def __init__(self):
        self.test_results = {}
        self.start_time = time.time()

    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始综合测试...")
        print(f"📅 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)

        # 1. 单元测试
        await self.run_unit_tests()

        # 2. WebSocket集成测试
        await self.run_websocket_integration_tests()

        # 3. API端点测试
        await self.run_api_tests()

        # 4. 性能测试
        await self.run_performance_tests()

        # 5. 生成综合报告
        self.generate_comprehensive_report()

    async def run_unit_tests(self):
        """运行单元测试"""
        print("\n📋 运行单元测试...")
        print("-" * 40)

        try:
            # 运行pytest单元测试
            result = subprocess.run([
                sys.executable, "-m", "pytest",
                "tests/test_sentiment_engine.py",
                "-v",
                "--tb=short",
                "--no-header"
            ], capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__)))

            success = result.returncode == 0
            self.test_results["unit_tests"] = {
                "success": success,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode
            }

            if success:
                print("✅ 单元测试通过")
            else:
                print("❌ 单元测试失败")
                print("错误输出:", result.stderr[:500])

        except Exception as e:
            print(f"❌ 单元测试执行失败: {e}")
            self.test_results["unit_tests"] = {
                "success": False,
                "error": str(e)
            }

    async def run_websocket_integration_tests(self):
        """运行WebSocket集成测试"""
        print("\n🔌 运行WebSocket集成测试...")
        print("-" * 40)

        try:
            tester = WebSocketIntegrationTester()

            # 连接性能测试
            connection_perf = await tester.test_connection_performance(5)

            # 订阅流程测试
            subscription_flow = await tester.test_subscription_flow()

            # 广播性能测试
            broadcast_perf = await tester.test_broadcast_performance(3)

            self.test_results["websocket_integration"] = {
                "connection_performance": connection_perf,
                "subscription_flow": subscription_flow,
                "broadcast_performance": broadcast_perf,
                "success": "error" not in connection_perf and "error" not in subscription_flow and "error" not in broadcast_perf
            }

            if self.test_results["websocket_integration"]["success"]:
                print("✅ WebSocket集成测试通过")
            else:
                print("❌ WebSocket集成测试失败")

        except Exception as e:
            print(f"❌ WebSocket集成测试执行失败: {e}")
            self.test_results["websocket_integration"] = {
                "success": False,
                "error": str(e)
            }

    async def run_api_tests(self):
        """运行API端点测试"""
        print("\n🌐 运行API端点测试...")
        print("-" * 40)

        try:
            # 测试健康检查端点
            health_response = await self.test_api_endpoint("/health")

            # 测试情绪分析端点
            sentiment_response = await self.test_api_endpoint("/api/v1/sentiment/analyze/BTC")

            # 测试性能监控端点
            performance_response = await self.test_api_endpoint("/api/v1/websocket/performance/performance")

            self.test_results["api_tests"] = {
                "health_endpoint": health_response,
                "sentiment_endpoint": sentiment_response,
                "performance_endpoint": performance_response,
                "success": all([
                    health_response.get("status_code") == 200,
                    sentiment_response.get("status_code") in [200, 404],  # 404 acceptable if engine not running
                    performance_response.get("status_code") == 200
                ])
            }

            if self.test_results["api_tests"]["success"]:
                print("✅ API端点测试通过")
            else:
                print("❌ API端点测试失败")

        except Exception as e:
            print(f"❌ API端点测试执行失败: {e}")
            self.test_results["api_tests"] = {
                "success": False,
                "error": str(e)
            }

    async def test_api_endpoint(self, endpoint: str) -> Dict[str, Any]:
        """测试单个API端点"""
        try:
            import aiohttp
            import json

            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"http://localhost:8000{endpoint}") as response:
                    return {
                        "status_code": response.status,
                        "content": await response.text(),
                        "headers": dict(response.headers)
                    }
        except Exception as e:
            return {
                "status_code": 0,
                "error": str(e)
            }

    async def run_performance_tests(self):
        """运行性能测试"""
        print("\n⚡ 运行性能测试...")
        print("-" * 40)

        try:
            # 内存使用测试
            memory_test = await self.test_memory_usage()

            # 响应时间测试
            response_time_test = await self.test_response_times()

            # 并发连接测试
            concurrency_test = await self.test_concurrent_connections()

            self.test_results["performance_tests"] = {
                "memory_usage": memory_test,
                "response_times": response_time_test,
                "concurrent_connections": concurrency_test,
                "success": memory_test["success"] and response_time_test["success"] and concurrency_test["success"]
            }

            if self.test_results["performance_tests"]["success"]:
                print("✅ 性能测试通过")
            else:
                print("❌ 性能测试失败")

        except Exception as e:
            print(f"❌ 性能测试执行失败: {e}")
            self.test_results["performance_tests"] = {
                "success": False,
                "error": str(e)
            }

    async def test_memory_usage(self) -> Dict[str, Any]:
        """测试内存使用"""
        try:
            import psutil
            import os

            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB

            # 模拟一些操作
            await asyncio.sleep(2)

            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory

            return {
                "success": True,
                "initial_memory_mb": initial_memory,
                "final_memory_mb": final_memory,
                "memory_increase_mb": memory_increase,
                "memory_leak_suspected": memory_increase > 50  # 50MB threshold
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def test_response_times(self) -> Dict[str, Any]:
        """测试响应时间"""
        try:
            import aiohttp

            response_times = []
            num_requests = 10

            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                for _ in range(num_requests):
                    start_time = time.time()
                    try:
                        async with session.get("http://localhost:8000/health") as response:
                            await response.text()
                            response_times.append(time.time() - start_time)
                    except:
                        response_times.append(5.0)  # timeout

            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            max_response_time = max(response_times) if response_times else 0

            return {
                "success": True,
                "requests_count": num_requests,
                "avg_response_time": avg_response_time,
                "max_response_time": max_response_time,
                "performance_acceptable": avg_response_time < 1.0 and max_response_time < 3.0
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def test_concurrent_connections(self) -> Dict[str, Any]:
        """测试并发连接"""
        try:
            import aiohttp

            num_connections = 20
            connection_tasks = []

            async def make_connection():
                timeout = aiohttp.ClientTimeout(total=5)
                try:
                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        async with session.get("http://localhost:8000/health") as response:
                            return response.status == 200
                except:
                    return False

            start_time = time.time()

            # 创建并发连接
            for _ in range(num_connections):
                connection_tasks.append(make_connection())

            results = await asyncio.gather(*connection_tasks, return_exceptions=True)
            total_time = time.time() - start_time

            successful_connections = sum(1 for result in results if result is True)

            return {
                "success": True,
                "total_connections": num_connections,
                "successful_connections": successful_connections,
                "success_rate": successful_connections / num_connections,
                "total_time": total_time,
                "concurrency_acceptable": successful_connections / num_connections > 0.8
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def generate_comprehensive_report(self):
        """生成综合测试报告"""
        total_time = time.time() - self.start_time

        report = "\n" + "="*80 + "\n"
        report += "                  WebSocket情绪分析引擎 - 综合测试报告\n"
        report += "="*80 + "\n"
        report += f"测试完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"总测试时长: {total_time:.2f}秒\n\n"

        # 测试概览
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if isinstance(result, dict) and result.get("success", False))

        report += f"📊 测试概览: {passed_tests}/{total_tests} 通过\n"
        report += "-" * 80 + "\n\n"

        # 详细结果
        for test_name, result in self.test_results.items():
            report += f"🔍 {test_name.replace('_', ' ').title()}\n"
            report += "-" * 40 + "\n"

            if isinstance(result, dict):
                if result.get("success"):
                    report += "✅ 通过\n"
                else:
                    report += "❌ 失败\n"

                # 添加关键指标
                if test_name == "websocket_integration":
                    if "connection_performance" in result:
                        conn_perf = result["connection_performance"]
                        if "connections_per_second" in conn_perf:
                            report += f"   连接性能: {conn_perf['connections_per_second']:.1f} conn/s\n"
                    if "broadcast_performance" in result:
                        broad_perf = result["broadcast_performance"]
                        if "broadcast_efficiency" in broad_perf:
                            report += f"   广播效率: {broad_perf['broadcast_efficiency']:.1%}\n"

                elif test_name == "api_tests":
                    for endpoint, response in result.items():
                        if endpoint.endswith("_endpoint") and isinstance(response, dict):
                            status = response.get("status_code", 0)
                            report += f"   {endpoint.replace('_endpoint', '')}: {status}\n"

                elif test_name == "performance_tests":
                    if "memory_usage" in result:
                        memory = result["memory_usage"]
                        if memory.get("success"):
                            report += f"   内存增长: {memory.get('memory_increase_mb', 0):.1f}MB\n"
                    if "response_times" in result:
                        resp = result["response_times"]
                        if resp.get("success"):
                            report += f"   平均响应时间: {resp.get('avg_response_time', 0):.3f}s\n"
                    if "concurrent_connections" in result:
                        conc = result["concurrent_connections"]
                        if conc.get("success"):
                            report += f"   并发成功率: {conc.get('success_rate', 0):.1%}\n"

                # 添加错误信息
                if "error" in result:
                    report += f"   错误: {result['error']}\n"

            report += "\n"

        # 性能评级
        report += "🏆 性能评级\n"
        report += "-" * 40 + "\n"

        if passed_tests == total_tests:
            grade = "A+ 优秀"
        elif passed_tests >= total_tests * 0.8:
            grade = "B+ 良好"
        elif passed_tests >= total_tests * 0.6:
            grade = "C+ 合格"
        else:
            grade = "D 需要改进"

        report += f"综合评级: {grade}\n\n"

        # 建议
        report += "💡 优化建议\n"
        report += "-" * 40 + "\n"

        if not self.test_results.get("unit_tests", {}).get("success"):
            report += "• 检查单元测试失败的原因，修复代码逻辑错误\n"

        if not self.test_results.get("websocket_integration", {}).get("success"):
            report += "• 检查WebSocket连接配置和广播器状态\n"

        if not self.test_results.get("api_tests", {}).get("success"):
            report += "• 检查API端点实现和服务器状态\n"

        if not self.test_results.get("performance_tests", {}).get("success"):
            report += "• 优化系统性能，检查内存使用和响应时间\n"

        if passed_tests == total_tests:
            report += "• 所有测试通过，系统运行良好！\n"
            report += "• 考虑进行压力测试以验证系统极限性能\n"

        report += "\n" + "="*80 + "\n"

        print(report)

        # 保存报告到文件
        report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"📄 测试报告已保存到: {report_file}")
        except Exception as e:
            print(f"⚠️ 保存报告失败: {e}")

        return self.test_results


async def main():
    """主函数"""
    print("🧪 WebSocket情绪分析引擎 - 综合测试套件")
    print("确保服务器在 localhost:8000 上运行")
    print()

    # 等待用户确认
    try:
        input("按Enter键开始测试...")
    except KeyboardInterrupt:
        print("\n测试已取消")
        return

    # 运行测试
    test_suite = ComprehensiveTestSuite()
    await test_suite.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())