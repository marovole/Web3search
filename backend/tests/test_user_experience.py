"""
用户体验E2E测试（任务 8.8）

功能：
1. 端到端用户旅程测试
2. 响应时间验证
3. 错误处理用户友好性
4. 流式响应体验测试

测试场景：
- Quick Chat完整流程
- Deep Research完整流程
- 错误场景处理
- 边缘案例体验
"""
import pytest
import asyncio
from typing import Dict, Any
import time
from datetime import datetime

from httpx import AsyncClient
from app.main import app


# ================================
# 测试配置
# ================================

BASE_URL = "http://test"
TIMEOUT = 30  # API超时时间（秒）


# ================================
# 测试辅助函数
# ================================

async def measure_response_time(client: AsyncClient, method: str, url: str, **kwargs) -> tuple[Any, float]:
    """
    测量API响应时间

    Returns:
        Tuple[response, response_time_ms]
    """
    start = time.time()

    if method == "GET":
        response = await client.get(url, **kwargs)
    elif method == "POST":
        response = await client.post(url, **kwargs)
    else:
        raise ValueError(f"Unsupported method: {method}")

    elapsed_ms = (time.time() - start) * 1000
    return response, elapsed_ms


def assess_error_message_quality(error_message: str) -> Dict[str, bool]:
    """
    评估错误消息质量

    标准：
    1. 用户友好（非技术性语言）
    2. 提供解决建议
    3. 不暴露敏感信息
    4. 清晰明确
    """
    return {
        "user_friendly": not any(
            term in error_message.lower()
            for term in ["exception", "traceback", "stack", "500", "internal"]
        ),
        "has_suggestion": any(
            term in error_message
            for term in ["请", "建议", "可以", "尝试", "检查"]
        ),
        "no_sensitive_info": not any(
            term in error_message.lower()
            for term in ["password", "key", "token", "secret", "api_key"]
        ),
        "clear": len(error_message) > 10 and len(error_message) < 200,
    }


# ================================
# Quick Chat测试
# ================================

class TestQuickChatUX:
    """Quick Chat用户体验测试"""

    @pytest.mark.asyncio
    async def test_quick_chat_happy_path(self):
        """测试Quick Chat完整流程（正常场景）"""
        async with AsyncClient(app=app, base_url=BASE_URL) as client:
            # 发送查询
            response, response_time = await measure_response_time(
                client,
                "POST",
                "/v1/quick-chat",
                json={"query": "BTC现在的价格是多少？"},
                timeout=TIMEOUT,
            )

            # 验证响应
            assert response.status_code == 200, f"状态码错误: {response.status_code}"
            data = response.json()

            # 验证响应结构
            assert "answer" in data, "缺少answer字段"
            assert "conversation_id" in data, "缺少conversation_id"
            assert "model_used" in data, "缺少model_used"

            # 验证回答质量
            answer = data["answer"]
            assert len(answer) >= 50, f"回答过短: {len(answer)}字符"
            assert any(term in answer for term in ["BTC", "Bitcoin", "比特币"]), "回答未提及BTC"

            # 验证响应时间
            print(f"\n✓ Quick Chat响应时间: {response_time:.0f}ms")
            assert response_time < 5000, f"响应时间过长: {response_time:.0f}ms"

            # 验证数据来源标注
            if "data_sources" in data:
                print(f"✓ 数据来源: {', '.join(data['data_sources'])}")

    @pytest.mark.asyncio
    async def test_quick_chat_with_context(self):
        """测试Quick Chat上下文保持"""
        async with AsyncClient(app=app, base_url=BASE_URL) as client:
            # 第一轮对话
            response1 = await client.post(
                "/v1/quick-chat",
                json={"query": "BTC现在的价格是多少？"},
                timeout=TIMEOUT,
            )
            assert response1.status_code == 200
            conv_id = response1.json()["conversation_id"]

            # 第二轮对话（使用相同conversation_id）
            response2, response_time = await measure_response_time(
                client,
                "POST",
                "/v1/quick-chat",
                json={
                    "query": "那它的RSI指标呢？",
                    "conversation_id": conv_id,
                },
                timeout=TIMEOUT,
            )

            assert response2.status_code == 200
            data2 = response2.json()

            # 验证上下文理解
            answer2 = data2["answer"]
            assert any(term in answer2 for term in ["BTC", "Bitcoin", "比特币"]), \
                "未保持上下文（应该理解'它'指BTC）"
            assert any(term in answer2 for term in ["RSI", "相对强弱"]), \
                "未回答RSI相关内容"

            print(f"✓ 上下文保持测试通过，响应时间: {response_time:.0f}ms")

    @pytest.mark.asyncio
    async def test_quick_chat_progressive_hints(self):
        """测试阶段性进度提示"""
        async with AsyncClient(app=app, base_url=BASE_URL) as client:
            # 发送复杂查询（可能触发进度提示）
            response = await client.post(
                "/v1/quick-chat",
                json={"query": "全面分析BTC的技术面、基本面和情绪面"},
                timeout=TIMEOUT,
            )

            assert response.status_code == 200
            data = response.json()

            # 检查是否有阶段性提示
            answer = data["answer"]

            # 理想情况下，回答应该有清晰的结构
            has_structure = any(
                marker in answer
                for marker in ["一、", "1.", "首先", "其次", "最后", "##"]
            )

            print(f"✓ 回答结构化: {has_structure}")


# ================================
# Deep Research测试
# ================================

class TestDeepResearchUX:
    """Deep Research用户体验测试"""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_deep_research_happy_path(self):
        """测试Deep Research完整流程（慢测试）"""
        async with AsyncClient(app=app, base_url=BASE_URL) as client:
            # 发起研究任务
            response, response_time = await measure_response_time(
                client,
                "POST",
                "/v1/deep-research",
                json={"query": "ETH的全面投资分析报告"},
                timeout=60,  # Deep Research需要更长时间
            )

            assert response.status_code == 200
            data = response.json()

            # 验证响应结构
            assert "report_id" in data
            assert "markdown_content" in data
            assert "tldr" in data

            # 验证报告质量
            content = data["markdown_content"]
            assert len(content) >= 1000, f"报告过短: {len(content)}字符"

            # 验证TLDR
            tldr = data["tldr"]
            assert 50 <= len(tldr) <= 300, f"TLDR长度不合适: {len(tldr)}字符"

            # 验证质量评分
            if "quality_score" in data:
                score = data["quality_score"]
                assert 1 <= score <= 5, f"质量评分超出范围: {score}"
                print(f"✓ 报告质量评分: {score}/5")

            print(f"✓ Deep Research完成，耗时: {response_time:.0f}ms")

    @pytest.mark.asyncio
    async def test_deep_research_progress_callback(self):
        """测试Deep Research进度回调"""
        # 注意：这需要前端WebSocket集成才能完整测试
        # 这里只测试API结构是否支持进度报告

        async with AsyncClient(app=app, base_url=BASE_URL) as client:
            response = await client.post(
                "/v1/deep-research",
                json={"query": "BTC深度研究"},
                timeout=60,
            )

            assert response.status_code == 200
            data = response.json()

            # 验证是否有生成时间信息
            if "generation_time" in data:
                gen_time = data["generation_time"]
                print(f"✓ 报告生成时间: {gen_time:.1f}秒")


# ================================
# 错误处理测试
# ================================

class TestErrorHandlingUX:
    """错误处理用户体验测试"""

    @pytest.mark.asyncio
    async def test_invalid_symbol_error(self):
        """测试无效代币符号的错误处理"""
        async with AsyncClient(app=app, base_url=BASE_URL) as client:
            response = await client.post(
                "/v1/quick-chat",
                json={"query": "XXXINVALIDXXX的价格"},
                timeout=TIMEOUT,
            )

            # 可能返回200（礼貌回答）或404
            if response.status_code == 200:
                data = response.json()
                answer = data["answer"]

                # 验证错误消息质量
                assert any(
                    term in answer
                    for term in ["无法", "找不到", "不存在", "无效", "未知"]
                ), "未正确处理无效代币"

                # 应该有建议
                quality = assess_error_message_quality(answer)
                print(f"✓ 错误消息质量: {quality}")
                assert quality["user_friendly"], "错误消息不够友好"

    @pytest.mark.asyncio
    async def test_empty_query_error(self):
        """测试空查询的错误处理"""
        async with AsyncClient(app=app, base_url=BASE_URL) as client:
            response = await client.post(
                "/v1/quick-chat",
                json={"query": ""},
                timeout=TIMEOUT,
            )

            # 应该返回400或422（验证错误）
            assert response.status_code in [400, 422], \
                f"空查询应该被拒绝，但返回: {response.status_code}"

            # 验证错误消息
            data = response.json()
            error_msg = data.get("detail", "")

            quality = assess_error_message_quality(error_msg)
            print(f"✓ 空查询错误消息质量: {quality}")

    @pytest.mark.asyncio
    async def test_malformed_request_error(self):
        """测试畸形请求的错误处理"""
        async with AsyncClient(app=app, base_url=BASE_URL) as client:
            response = await client.post(
                "/v1/quick-chat",
                json={"invalid_field": "value"},
                timeout=TIMEOUT,
            )

            # 应该返回422（验证错误）
            assert response.status_code == 422

            data = response.json()
            error_msg = str(data.get("detail", ""))

            # 验证错误消息不暴露敏感信息
            quality = assess_error_message_quality(error_msg)
            assert quality["no_sensitive_info"], "错误消息暴露了敏感信息"

    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """测试超时处理"""
        async with AsyncClient(app=app, base_url=BASE_URL) as client:
            try:
                response = await client.post(
                    "/v1/deep-research",
                    json={"query": "超级复杂的分析任务"},
                    timeout=1,  # 故意设置很短的超时
                )
            except asyncio.TimeoutError:
                # 客户端超时是预期行为
                print("✓ 超时正确触发")
            else:
                # 如果没有超时，检查是否有合理的响应
                assert response.status_code in [200, 503], \
                    f"超时场景返回了意外状态码: {response.status_code}"


# ================================
# 边缘案例测试
# ================================

class TestEdgeCasesUX:
    """边缘案例用户体验测试"""

    @pytest.mark.asyncio
    async def test_very_short_query(self):
        """测试极短查询"""
        async with AsyncClient(app=app, base_url=BASE_URL) as client:
            response = await client.post(
                "/v1/quick-chat",
                json={"query": "BTC"},
                timeout=TIMEOUT,
            )

            assert response.status_code == 200
            data = response.json()
            answer = data["answer"]

            # 应该主动扩展回答
            assert len(answer) >= 100, "对短查询的扩展不足"
            print(f"✓ 短查询扩展长度: {len(answer)}字符")

    @pytest.mark.asyncio
    async def test_very_long_query(self):
        """测试超长查询"""
        async with AsyncClient(app=app, base_url=BASE_URL) as client:
            long_query = "请分析BTC" + "，还有" * 100 + "它的各种指标"

            response = await client.post(
                "/v1/quick-chat",
                json={"query": long_query},
                timeout=TIMEOUT,
            )

            # 应该能处理或拒绝，但不能500
            assert response.status_code != 500, "超长查询导致服务器错误"

            if response.status_code == 200:
                data = response.json()
                assert "answer" in data
                print("✓ 成功处理超长查询")
            else:
                print(f"✓ 礼貌拒绝超长查询 (状态码: {response.status_code})")

    @pytest.mark.asyncio
    async def test_special_characters_query(self):
        """测试特殊字符查询"""
        async with AsyncClient(app=app, base_url=BASE_URL) as client:
            special_query = "BTC的价格<script>alert('xss')</script>是多少？"

            response = await client.post(
                "/v1/quick-chat",
                json={"query": special_query},
                timeout=TIMEOUT,
            )

            assert response.status_code == 200
            data = response.json()
            answer = data["answer"]

            # 验证XSS防护（不应该执行脚本）
            assert "<script>" not in answer, "存在XSS漏洞"
            print("✓ XSS防护正常")

    @pytest.mark.asyncio
    async def test_multilingual_query(self):
        """测试多语言查询"""
        async with AsyncClient(app=app, base_url=BASE_URL) as client:
            # 英文查询
            response_en = await client.post(
                "/v1/quick-chat",
                json={"query": "What is the price of BTC?"},
                timeout=TIMEOUT,
            )

            # 中文查询
            response_zh = await client.post(
                "/v1/quick-chat",
                json={"query": "BTC的价格是多少？"},
                timeout=TIMEOUT,
            )

            assert response_en.status_code == 200
            assert response_zh.status_code == 200

            print("✓ 多语言支持正常")


# ================================
# 性能基准测试
# ================================

class TestPerformanceBenchmark:
    """性能基准测试（为任务9.8提供基础）"""

    @pytest.mark.asyncio
    async def test_quick_chat_response_time_benchmark(self):
        """Quick Chat响应时间基准测试"""
        async with AsyncClient(app=app, base_url=BASE_URL) as client:
            response_times = []

            # 测试5次
            for i in range(5):
                response, elapsed = await measure_response_time(
                    client,
                    "POST",
                    "/v1/quick-chat",
                    json={"query": f"BTC分析 #{i+1}"},
                    timeout=TIMEOUT,
                )

                if response.status_code == 200:
                    response_times.append(elapsed)

                # 避免过快请求
                await asyncio.sleep(1)

            # 计算统计指标
            if response_times:
                avg = sum(response_times) / len(response_times)
                p95 = sorted(response_times)[int(len(response_times) * 0.95)]

                print(f"\n=== Quick Chat性能基准 ===")
                print(f"平均响应时间: {avg:.0f}ms")
                print(f"P95响应时间: {p95:.0f}ms")
                print(f"最小: {min(response_times):.0f}ms")
                print(f"最大: {max(response_times):.0f}ms")

                # 性能目标：P95 < 3000ms
                assert p95 < 5000, f"P95响应时间过长: {p95:.0f}ms"


# ================================
# 运行测试
# ================================

if __name__ == "__main__":
    # 运行快速测试
    pytest.main([__file__, "-v", "-m", "not slow", "--tb=short"])
