"""
WebSocket集成测试
测试WebSocket连接、消息传递和性能
"""
import asyncio
import json
import websockets
import pytest
from typing import Dict, List
import time
from datetime import datetime

from app.api.v1.websocket.connection_manager import connection_manager
from app.api.v1.websocket.sentiment_broadcaster import sentiment_broadcaster


class WebSocketIntegrationTester:
    """WebSocket集成测试器"""

    def __init__(self, websocket_url: str = "ws://localhost:8000/ws/sentiment"):
        self.websocket_url = websocket_url
        self.test_results = {}

    async def test_connection_performance(self, num_clients: int = 10) -> Dict:
        """测试连接性能"""
        print(f"\n🔌 测试WebSocket连接性能 ({num_clients}个客户端)...")

        start_time = time.time()
        connections = []

        try:
            # 并发建立多个连接
            connect_tasks = []
            for i in range(num_clients):
                task = self._create_test_connection(f"test_client_{i}")
                connect_tasks.append(task)

            connections = await asyncio.gather(*connect_tasks)
            connect_time = time.time() - start_time

            # 测试消息发送性能
            message_start = time.time()
            message_tasks = []

            for i, ws in enumerate(connections):
                if ws:
                    task = self._send_test_message(ws, f"test_message_{i}")
                    message_tasks.append(task)

            message_results = await asyncio.gather(*message_tasks, return_exceptions=True)
            message_time = time.time() - message_start

            # 统计成功连接和消息
            successful_connections = sum(1 for ws in connections if ws is not None)
            successful_messages = sum(1 for result in message_results if result is True)

            # 关闭连接
            close_tasks = []
            for ws in connections:
                if ws:
                    close_tasks.append(ws.close())

            if close_tasks:
                await asyncio.gather(*close_tasks, return_exceptions=True)

            self.test_results["connection_performance"] = {
                "total_clients": num_clients,
                "successful_connections": successful_connections,
                "connection_time": connect_time,
                "successful_messages": successful_messages,
                "message_time": message_time,
                "connections_per_second": successful_connections / connect_time if connect_time > 0 else 0,
                "messages_per_second": successful_messages / message_time if message_time > 0 else 0
            }

            print(f"✅ 连接性能测试完成: {successful_connections}/{num_clients} 连接成功")
            return self.test_results["connection_performance"]

        except Exception as e:
            print(f"❌ 连接性能测试失败: {e}")
            return {"error": str(e)}

    async def _create_test_connection(self, client_id: str):
        """创建测试连接"""
        try:
            uri = f"{self.websocket_url}/{client_id}"
            ws = await websockets.connect(uri, timeout=5)

            # 等待连接确认消息
            response = await asyncio.wait_for(ws.recv(), timeout=5)
            data = json.loads(response)

            if data.get("type") == "connection_established":
                return ws
            else:
                await ws.close()
                return None

        except Exception as e:
            print(f"⚠️ 客户端 {client_id} 连接失败: {e}")
            return None

    async def _send_test_message(self, websocket, message: str) -> bool:
        """发送测试消息"""
        try:
            test_data = {
                "type": "test",
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            }

            await websocket.send(json.dumps(test_data))
            return True

        except Exception as e:
            print(f"⚠️ 发送消息失败: {e}")
            return False

    async def test_subscription_flow(self) -> Dict:
        """测试订阅流程"""
        print(f"\n📡 测试订阅流程...")

        try:
            # 创建连接
            ws = await self._create_test_connection("subscription_test")
            if not ws:
                return {"error": "Failed to create connection"}

            subscription_results = []
            test_symbols = ["BTC", "ETH", "SOL"]

            # 测试订阅
            for symbol in test_symbols:
                try:
                    # 发送订阅消息
                    subscribe_msg = {
                        "action": "subscribe",
                        "symbol": symbol
                    }
                    await ws.send(json.dumps(subscribe_msg))

                    # 等待订阅确认
                    response = await asyncio.wait_for(ws.recv(), timeout=5)
                    data = json.loads(response)

                    subscription_results.append({
                        "symbol": symbol,
                        "success": data.get("type") == "subscription_confirmed",
                        "response": data
                    })

                except Exception as e:
                    subscription_results.append({
                        "symbol": symbol,
                        "success": False,
                        "error": str(e)
                    })

            # 测试取消订阅
            unsubscribe_results = []
            for symbol in test_symbols[:1]:  # 测试取消第一个订阅
                try:
                    unsubscribe_msg = {
                        "action": "unsubscribe",
                        "symbol": symbol
                    }
                    await ws.send(json.dumps(unsubscribe_msg))

                    response = await asyncio.wait_for(ws.recv(), timeout=5)
                    data = json.loads(response)

                    unsubscribe_results.append({
                        "symbol": symbol,
                        "success": data.get("type") == "unsubscription_confirmed",
                        "response": data
                    })

                except Exception as e:
                    unsubscribe_results.append({
                        "symbol": symbol,
                        "success": False,
                        "error": str(e)
                    })

            await ws.close()

            self.test_results["subscription_flow"] = {
                "subscriptions": subscription_results,
                "unsubscriptions": unsubscribe_results,
                "successful_subscriptions": sum(1 for r in subscription_results if r["success"]),
                "successful_unsubscriptions": sum(1 for r in unsubscribe_results if r["success"])
            }

            print(f"✅ 订阅流程测试完成")
            return self.test_results["subscription_flow"]

        except Exception as e:
            print(f"❌ 订阅流程测试失败: {e}")
            return {"error": str(e)}

    async def test_broadcast_performance(self, num_subscribers: int = 5) -> Dict:
        """测试广播性能"""
        print(f"\n📢 测试广播性能 ({num_subscribers}个订阅者)...")

        try:
            # 创建多个订阅者连接
            connections = []
            connect_tasks = []

            for i in range(num_subscribers):
                task = self._create_test_connection(f"broadcast_subscriber_{i}")
                connect_tasks.append(task)

            connections = await asyncio.gather(*connect_tasks)
            successful_connections = [ws for ws in connections if ws is not None]

            if not successful_connections:
                return {"error": "No successful connections"}

            # 订阅测试币种
            test_symbol = "BTC"
            subscription_tasks = []

            for ws in successful_connections:
                task = self._subscribe_to_symbol(ws, test_symbol)
                subscription_tasks.append(task)

            subscription_results = await asyncio.gather(*subscription_tasks, return_exceptions=True)
            successful_subscriptions = sum(1 for r in subscription_results if r is True)

            if successful_subscriptions == 0:
                return {"error": "No successful subscriptions"}

            # 模拟广播消息
            broadcast_start = time.time()
            broadcast_data = {
                "type": "sentiment_update",
                "symbol": test_symbol,
                "data": {
                    "sentiment_score": 0.5,
                    "confidence": 0.8,
                    "volume": 1000,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }

            # 通过连接管理器广播
            success_count = await connection_manager.broadcast_to_subscribers(
                test_symbol, broadcast_data
            )

            broadcast_time = time.time() - broadcast_start

            # 验证客户端是否收到消息
            receive_tasks = []
            for ws in successful_connections:
                task = self._wait_for_message(ws, timeout=2)
                receive_tasks.append(task)

            receive_results = await asyncio.gather(*receive_tasks, return_exceptions=True)
            successful_receives = sum(1 for r in receive_results if r is True)

            # 关闭连接
            close_tasks = []
            for ws in successful_connections:
                close_tasks.append(ws.close())

            if close_tasks:
                await asyncio.gather(*close_tasks, return_exceptions=True)

            self.test_results["broadcast_performance"] = {
                "total_subscribers": num_subscribers,
                "successful_connections": len(successful_connections),
                "successful_subscriptions": successful_subscriptions,
                "broadcast_sent_count": success_count,
                "broadcast_receive_count": successful_receives,
                "broadcast_time": broadcast_time,
                "broadcast_efficiency": successful_receives / success_count if success_count > 0 else 0
            }

            print(f"✅ 广播性能测试完成: {successful_receives}/{success_count} 消息成功接收")
            return self.test_results["broadcast_performance"]

        except Exception as e:
            print(f"❌ 广播性能测试失败: {e}")
            return {"error": str(e)}

    async def _subscribe_to_symbol(self, websocket, symbol: str) -> bool:
        """订阅币种"""
        try:
            subscribe_msg = {
                "action": "subscribe",
                "symbol": symbol
            }
            await websocket.send(json.dumps(subscribe_msg))

            # 等待订阅确认
            response = await asyncio.wait_for(websocket.recv(), timeout=5)
            data = json.loads(response)

            return data.get("type") == "subscription_confirmed"

        except Exception:
            return False

    async def _wait_for_message(self, websocket, timeout: float = 5) -> bool:
        """等待接收消息"""
        try:
            response = await asyncio.wait_for(websocket.recv(), timeout=timeout)
            data = json.loads(response)
            return data.get("type") == "sentiment_update"
        except Exception:
            return False

    async def test_memory_usage(self, duration_seconds: int = 60) -> Dict:
        """测试内存使用情况"""
        print(f"\n💾 测试内存使用情况 ({duration_seconds}秒)...")

        try:
            import psutil
            import os

            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB

            # 创建一些连接
            connections = []
            for i in range(5):
                ws = await self._create_test_connection(f"memory_test_{i}")
                if ws:
                    connections.append(ws)

            # 监控内存使用
            memory_samples = [initial_memory]
            start_time = time.time()

            while time.time() - start_time < duration_seconds:
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_samples.append(current_memory)
                await asyncio.sleep(5)

            final_memory = process.memory_info().rss / 1024 / 1024

            # 关闭连接
            for ws in connections:
                await ws.close()

            # 等待内存清理
            await asyncio.sleep(2)
            cleanup_memory = process.memory_info().rss / 1024 / 1024

            self.test_results["memory_usage"] = {
                "initial_memory_mb": initial_memory,
                "final_memory_mb": final_memory,
                "cleanup_memory_mb": cleanup_memory,
                "peak_memory_mb": max(memory_samples),
                "memory_increase_mb": final_memory - initial_memory,
                "memory_leak_suspected": cleanup_memory > initial_memory * 1.1
            }

            print(f"✅ 内存使用测试完成: 初始 {initial_memory:.1f}MB, 峰值 {max(memory_samples):.1f}MB")
            return self.test_results["memory_usage"]

        except Exception as e:
            print(f"❌ 内存使用测试失败: {e}")
            return {"error": str(e)}

    def generate_report(self) -> str:
        """生成测试报告"""
        report = "\n" + "="*60 + "\n"
        report += "           WebSocket集成测试报告\n"
        report += "="*60 + "\n"

        for test_name, results in self.test_results.items():
            report += f"\n📊 {test_name.replace('_', ' ').title()}\n"
            report += "-" * 40 + "\n"

            if "error" in results:
                report += f"❌ 测试失败: {results['error']}\n"
            else:
                for key, value in results.items():
                    if isinstance(value, float):
                        report += f"   {key}: {value:.3f}\n"
                    elif isinstance(value, dict):
                        report += f"   {key}:\n"
                        for sub_key, sub_value in value.items():
                            report += f"     {sub_key}: {sub_value}\n"
                    else:
                        report += f"   {key}: {value}\n"

        report += "\n" + "="*60 + "\n"
        return report


async def run_integration_tests():
    """运行所有集成测试"""
    print("🚀 开始WebSocket集成测试...")

    tester = WebSocketIntegrationTester()

    # 运行所有测试
    await tester.test_connection_performance(10)
    await tester.test_subscription_flow()
    await tester.test_broadcast_performance(5)
    await tester.test_memory_usage(30)

    # 生成报告
    report = tester.generate_report()
    print(report)

    return tester.test_results


if __name__ == "__main__":
    # 运行测试
    results = asyncio.run(run_integration_tests())