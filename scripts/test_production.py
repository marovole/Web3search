#!/usr/bin/env python3
"""
生产环境功能测试脚本
测试Web3search生产环境的所有核心功能
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import sys


class TestStatus(Enum):
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"


@dataclass
class TestResult:
    name: str
    status: TestStatus
    duration: float = 0.0
    details: str = ""
    error: Optional[str] = None
    response_time: Optional[float] = None


class ProductionTester:
    """生产环境测试器"""
    
    def __init__(self):
        self.frontend_url = "https://web3search.vercel.app"
        self.backend_url = "https://web3search-api.onrender.com"
        self.results: List[TestResult] = []
        self.session = requests.Session()
        self.session.timeout = 30
        
    def run_test(self, name: str, test_func) -> TestResult:
        """运行单个测试"""
        start_time = time.time()
        try:
            result = test_func()
            duration = time.time() - start_time
            result.duration = duration
            self.results.append(result)
            status_icon = "✅" if result.status == TestStatus.PASSED else \
                         "❌" if result.status == TestStatus.FAILED else \
                         "⚠️" if result.status == TestStatus.WARNING else "⏭️"
            print(f"{status_icon} {name}: {result.details}")
            if result.error:
                print(f"   错误: {result.error}")
            return result
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult(
                name=name,
                status=TestStatus.FAILED,
                duration=duration,
                details=f"测试异常: {str(e)}",
                error=str(e)
            )
            self.results.append(result)
            print(f"❌ {name}: 测试异常 - {str(e)}")
            return result
    
    # ================================
    # 基础系统测试
    # ================================
    
    def test_backend_health(self) -> TestResult:
        """测试后端健康检查"""
        try:
            url = f"{self.backend_url}/health"
            start = time.time()
            response = self.session.get(url, timeout=10)
            response_time = (time.time() - start) * 1000
            
            if response.status_code == 200:
                data = response.json()
                status = data.get("status", "unknown")
                return TestResult(
                    name="后端健康检查",
                    status=TestStatus.PASSED if status == "healthy" else TestStatus.WARNING,
                    response_time=response_time,
                    details=f"状态: {status}, 响应时间: {response_time:.0f}ms"
                )
            else:
                return TestResult(
                    name="后端健康检查",
                    status=TestStatus.FAILED,
                    response_time=response_time,
                    details=f"HTTP {response.status_code}",
                    error=f"状态码: {response.status_code}"
                )
        except requests.exceptions.Timeout:
            return TestResult(
                name="后端健康检查",
                status=TestStatus.FAILED,
                details="请求超时",
                error="连接超时"
            )
        except Exception as e:
            return TestResult(
                name="后端健康检查",
                status=TestStatus.FAILED,
                details=f"异常: {str(e)}",
                error=str(e)
            )
    
    def test_frontend_accessibility(self) -> TestResult:
        """测试前端可访问性"""
        try:
            start = time.time()
            response = self.session.get(self.frontend_url, timeout=10)
            response_time = (time.time() - start) * 1000
            
            if response.status_code == 200:
                return TestResult(
                    name="前端可访问性",
                    status=TestStatus.PASSED,
                    response_time=response_time,
                    details=f"HTTP 200, 响应时间: {response_time:.0f}ms"
                )
            elif response.status_code == 404:
                return TestResult(
                    name="前端可访问性",
                    status=TestStatus.FAILED,
                    response_time=response_time,
                    details="HTTP 404 - 部署未找到",
                    error="前端部署可能失败"
                )
            else:
                return TestResult(
                    name="前端可访问性",
                    status=TestStatus.WARNING,
                    response_time=response_time,
                    details=f"HTTP {response.status_code}",
                    error=f"非预期状态码: {response.status_code}"
                )
        except requests.exceptions.Timeout:
            return TestResult(
                name="前端可访问性",
                status=TestStatus.FAILED,
                details="请求超时",
                error="连接超时"
            )
        except Exception as e:
            return TestResult(
                name="前端可访问性",
                status=TestStatus.FAILED,
                details=f"异常: {str(e)}",
                error=str(e)
            )
    
    def test_api_docs(self) -> TestResult:
        """测试API文档可访问性"""
        try:
            url = f"{self.backend_url}/docs"
            start = time.time()
            response = self.session.get(url, timeout=10)
            response_time = (time.time() - start) * 1000
            
            if response.status_code == 200:
                return TestResult(
                    name="API文档",
                    status=TestStatus.PASSED,
                    response_time=response_time,
                    details=f"Swagger UI可访问, 响应时间: {response_time:.0f}ms"
                )
            else:
                return TestResult(
                    name="API文档",
                    status=TestStatus.FAILED,
                    response_time=response_time,
                    details=f"HTTP {response.status_code}",
                    error=f"无法访问API文档"
                )
        except Exception as e:
            return TestResult(
                name="API文档",
                status=TestStatus.FAILED,
                details=f"异常: {str(e)}",
                error=str(e)
            )
    
    # ================================
    # Quick Chat功能测试
    # ================================
    
    def test_quick_chat(self) -> TestResult:
        """测试Quick Chat功能"""
        try:
            url = f"{self.backend_url}/api/v1/chat/quick-chat"
            payload = {
                "query": "什么是比特币？",
                "session_id": None
            }
            start = time.time()
            response = self.session.post(url, json=payload, timeout=30)
            response_time = (time.time() - start) * 1000
            
            if response.status_code == 200:
                data = response.json()
                # 检查content字段（标准响应格式）
                content = data.get("content", "")
                # 兼容旧格式answer字段
                if not content:
                    content = data.get("answer", "")
                
                if content:
                    return TestResult(
                        name="Quick Chat",
                        status=TestStatus.PASSED,
                        response_time=response_time,
                        details=f"成功返回答案, 响应时间: {response_time:.0f}ms, 答案长度: {len(content)}字符"
                    )
                else:
                    return TestResult(
                        name="Quick Chat",
                        status=TestStatus.WARNING,
                        response_time=response_time,
                        details=f"返回成功但内容为空, 响应数据: {json.dumps(data, ensure_ascii=False)[:200]}",
                        error="答案内容为空"
                    )
            elif response.status_code == 500:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                error_msg = error_data.get("detail", response.text[:200])
                return TestResult(
                    name="Quick Chat",
                    status=TestStatus.FAILED,
                    response_time=response_time,
                    details=f"服务器错误: {error_msg}",
                    error=error_msg
                )
            else:
                return TestResult(
                    name="Quick Chat",
                    status=TestStatus.FAILED,
                    response_time=response_time,
                    details=f"HTTP {response.status_code}",
                    error=f"状态码: {response.status_code}"
                )
        except requests.exceptions.Timeout:
            return TestResult(
                name="Quick Chat",
                status=TestStatus.FAILED,
                details="请求超时（>30秒）",
                error="响应时间过长"
            )
        except Exception as e:
            return TestResult(
                name="Quick Chat",
                status=TestStatus.FAILED,
                details=f"异常: {str(e)}",
                error=str(e)
            )
    
    def test_quick_chat_stream(self) -> TestResult:
        """测试Quick Chat流式输出"""
        try:
            url = f"{self.backend_url}/api/v1/chat/quick-chat/stream"
            payload = {
                "query": "比特币的价格",
                "session_id": None
            }
            start = time.time()
            response = self.session.post(url, json=payload, stream=True, timeout=30)
            response_time = (time.time() - start) * 1000
            
            if response.status_code == 200:
                chunks_received = 0
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        chunks_received += 1
                        if chunks_received >= 1:  # 至少收到一个chunk
                            break
                
                return TestResult(
                    name="Quick Chat流式输出",
                    status=TestStatus.PASSED,
                    response_time=response_time,
                    details=f"流式输出正常, 收到{chunks_received}个数据块"
                )
            else:
                return TestResult(
                    name="Quick Chat流式输出",
                    status=TestStatus.FAILED,
                    response_time=response_time,
                    details=f"HTTP {response.status_code}",
                    error=f"状态码: {response.status_code}"
                )
        except requests.exceptions.Timeout:
            return TestResult(
                name="Quick Chat流式输出",
                status=TestStatus.FAILED,
                details="请求超时",
                error="流式输出超时"
            )
        except Exception as e:
            return TestResult(
                name="Quick Chat流式输出",
                status=TestStatus.FAILED,
                details=f"异常: {str(e)}",
                error=str(e)
            )
    
    # ================================
    # Deep Research功能测试
    # ================================
    
    def test_deep_research(self) -> TestResult:
        """测试Deep Research功能"""
        try:
            url = f"{self.backend_url}/api/v1/chat/deep-research"
            payload = {
                "query": "分析比特币",
                "symbol": "BTC"
            }
            start = time.time()
            response = self.session.post(url, json=payload, timeout=120)  # 2分钟超时
            response_time = (time.time() - start) * 1000
            
            if response.status_code == 200:
                data = response.json()
                report_id = data.get("report_id")
                if report_id:
                    return TestResult(
                        name="Deep Research",
                        status=TestStatus.PASSED,
                        response_time=response_time,
                        details=f"成功创建报告, ID: {report_id}, 响应时间: {response_time:.0f}ms"
                    )
                else:
                    return TestResult(
                        name="Deep Research",
                        status=TestStatus.WARNING,
                        response_time=response_time,
                        details="返回成功但缺少report_id",
                        error="响应格式异常"
                    )
            elif response.status_code == 500:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                error_msg = error_data.get("detail", response.text[:200])
                return TestResult(
                    name="Deep Research",
                    status=TestStatus.FAILED,
                    response_time=response_time,
                    details=f"服务器错误: {error_msg}",
                    error=error_msg
                )
            else:
                return TestResult(
                    name="Deep Research",
                    status=TestStatus.FAILED,
                    response_time=response_time,
                    details=f"HTTP {response.status_code}",
                    error=f"状态码: {response.status_code}"
                )
        except requests.exceptions.Timeout:
            return TestResult(
                name="Deep Research",
                status=TestStatus.FAILED,
                details="请求超时（>120秒）",
                error="响应时间过长"
            )
        except Exception as e:
            return TestResult(
                name="Deep Research",
                status=TestStatus.FAILED,
                details=f"异常: {str(e)}",
                error=str(e)
            )
    
    # ================================
    # 报告管理功能测试
    # ================================
    
    def test_reports_list(self) -> TestResult:
        """测试报告列表"""
        try:
            url = f"{self.backend_url}/api/v1/reports"
            params = {"page": 1, "page_size": 10}
            start = time.time()
            response = self.session.get(url, params=params, timeout=10)
            response_time = (time.time() - start) * 1000
            
            if response.status_code == 200:
                data = response.json()
                reports = data.get("reports", [])
                return TestResult(
                    name="报告列表",
                    status=TestStatus.PASSED,
                    response_time=response_time,
                    details=f"成功获取报告列表, 共{len(reports)}条记录"
                )
            else:
                # 尝试解析错误响应
                error_detail = f"HTTP {response.status_code}"
                try:
                    if response.headers.get('content-type', '').startswith('application/json'):
                        error_data = response.json()
                        error_msg = error_data.get("detail") or error_data.get("error", {}).get("message", str(error_data))
                        error_detail = f"HTTP {response.status_code}: {error_msg}"
                except:
                    error_detail = f"HTTP {response.status_code}: {response.text[:200]}"
                
                return TestResult(
                    name="报告列表",
                    status=TestStatus.FAILED,
                    response_time=response_time,
                    details=error_detail,
                    error=error_detail
                )
        except Exception as e:
            return TestResult(
                name="报告列表",
                status=TestStatus.FAILED,
                details=f"异常: {str(e)}",
                error=str(e)
            )
    
    # ================================
    # 搜索功能测试
    # ================================
    
    def test_search_autocomplete(self) -> TestResult:
        """测试搜索自动完成"""
        try:
            url = f"{self.backend_url}/api/v1/search/autocomplete"
            params = {"q": "bitcoin"}
            start = time.time()
            response = self.session.get(url, params=params, timeout=10)
            response_time = (time.time() - start) * 1000
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                return TestResult(
                    name="搜索自动完成",
                    status=TestStatus.PASSED,
                    response_time=response_time,
                    details=f"成功返回{len(results)}个搜索结果, 响应时间: {response_time:.0f}ms"
                )
            else:
                # 尝试解析错误响应
                error_detail = f"HTTP {response.status_code}"
                try:
                    if response.headers.get('content-type', '').startswith('application/json'):
                        error_data = response.json()
                        error_msg = error_data.get("detail") or error_data.get("error", {}).get("message", str(error_data))
                        error_detail = f"HTTP {response.status_code}: {error_msg}"
                except:
                    error_detail = f"HTTP {response.status_code}: {response.text[:200]}"
                
                return TestResult(
                    name="搜索自动完成",
                    status=TestStatus.FAILED,
                    response_time=response_time,
                    details=error_detail,
                    error=error_detail
                )
        except Exception as e:
            return TestResult(
                name="搜索自动完成",
                status=TestStatus.FAILED,
                details=f"异常: {str(e)}",
                error=str(e)
            )
    
    # ================================
    # 热点识别功能测试
    # ================================
    
    def test_trending_hotspots(self) -> TestResult:
        """测试热点识别"""
        try:
            url = f"{self.backend_url}/api/v1/trending/hotspots"
            start = time.time()
            response = self.session.get(url, timeout=10)
            response_time = (time.time() - start) * 1000
            
            if response.status_code == 200:
                data = response.json()
                hotspots = data.get("hotspots", [])
                return TestResult(
                    name="热点识别",
                    status=TestStatus.PASSED,
                    response_time=response_time,
                    details=f"成功获取{len(hotspots)}个热点, 响应时间: {response_time:.0f}ms"
                )
            else:
                # 尝试解析错误响应
                error_detail = f"HTTP {response.status_code}"
                try:
                    if response.headers.get('content-type', '').startswith('application/json'):
                        error_data = response.json()
                        error_msg = error_data.get("detail") or error_data.get("error", {}).get("message", str(error_data))
                        error_detail = f"HTTP {response.status_code}: {error_msg}"
                except:
                    error_detail = f"HTTP {response.status_code}: {response.text[:200]}"
                
                return TestResult(
                    name="热点识别",
                    status=TestStatus.FAILED,
                    response_time=response_time,
                    details=error_detail,
                    error=error_detail
                )
        except Exception as e:
            return TestResult(
                name="热点识别",
                status=TestStatus.FAILED,
                details=f"异常: {str(e)}",
                error=str(e)
            )
    
    # ================================
    # 安全测试
    # ================================
    
    def test_cors_config(self) -> TestResult:
        """测试CORS配置"""
        try:
            url = f"{self.backend_url}/health"
            headers = {
                "Origin": "https://web3search.vercel.app",
                "Access-Control-Request-Method": "GET"
            }
            response = self.session.options(url, headers=headers, timeout=10)
            
            cors_headers = {
                "access-control-allow-origin": response.headers.get("access-control-allow-origin"),
                "access-control-allow-methods": response.headers.get("access-control-allow-methods"),
                "access-control-allow-credentials": response.headers.get("access-control-allow-credentials")
            }
            
            if cors_headers["access-control-allow-origin"]:
                return TestResult(
                    name="CORS配置",
                    status=TestStatus.PASSED,
                    details=f"CORS配置正确: {cors_headers}"
                )
            else:
                return TestResult(
                    name="CORS配置",
                    status=TestStatus.WARNING,
                    details="CORS头未设置或配置不完整",
                    error="CORS配置可能存在问题"
                )
        except Exception as e:
            return TestResult(
                name="CORS配置",
                status=TestStatus.FAILED,
                details=f"测试异常: {str(e)}",
                error=str(e)
            )
    
    def test_input_validation(self) -> TestResult:
        """测试输入验证"""
        try:
            url = f"{self.backend_url}/api/v1/chat/quick-chat"
            # 测试SQL注入尝试
            payload = {
                "query": "'; DROP TABLE users; --",
                "session_id": None
            }
            response = self.session.post(url, json=payload, timeout=10)
            
            # 应该返回400或422（验证错误），而不是500（服务器错误）
            if response.status_code in [400, 422]:
                return TestResult(
                    name="输入验证",
                    status=TestStatus.PASSED,
                    details=f"输入验证正常，拒绝恶意输入 (HTTP {response.status_code})"
                )
            elif response.status_code == 500:
                return TestResult(
                    name="输入验证",
                    status=TestStatus.WARNING,
                    details="服务器错误，可能未正确处理恶意输入",
                    error="输入验证可能不足"
                )
            else:
                return TestResult(
                    name="输入验证",
                    status=TestStatus.WARNING,
                    details=f"未预期的状态码: {response.status_code}"
                )
        except Exception as e:
            return TestResult(
                name="输入验证",
                status=TestStatus.FAILED,
                details=f"测试异常: {str(e)}",
                error=str(e)
            )
    
    def test_empty_query(self) -> TestResult:
        """测试空查询处理"""
        try:
            url = f"{self.backend_url}/api/v1/chat/quick-chat"
            payload = {
                "query": "",
                "session_id": None
            }
            response = self.session.post(url, json=payload, timeout=10)
            
            if response.status_code in [400, 422]:
                return TestResult(
                    name="空查询验证",
                    status=TestStatus.PASSED,
                    details=f"正确拒绝空查询 (HTTP {response.status_code})"
                )
            else:
                return TestResult(
                    name="空查询验证",
                    status=TestStatus.WARNING,
                    details=f"未拒绝空查询 (HTTP {response.status_code})",
                    error="输入验证可能不足"
                )
        except Exception as e:
            return TestResult(
                name="空查询验证",
                status=TestStatus.FAILED,
                details=f"测试异常: {str(e)}",
                error=str(e)
            )
    
    # ================================
    # 性能测试
    # ================================
    
    def test_api_response_time(self) -> TestResult:
        """测试API响应时间"""
        endpoints = [
            ("/health", "GET", None),
            ("/api/v1/search/autocomplete?q=bitcoin", "GET", None),
        ]
        
        response_times = []
        for endpoint, method, payload in endpoints:
            try:
                url = f"{self.backend_url}{endpoint}"
                start = time.time()
                if method == "GET":
                    response = self.session.get(url, timeout=10)
                else:
                    response = self.session.post(url, json=payload, timeout=10)
                response_time = (time.time() - start) * 1000
                if response.status_code == 200:
                    response_times.append(response_time)
            except:
                pass
        
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)
            status = TestStatus.PASSED if avg_time < 2000 else TestStatus.WARNING
            return TestResult(
                name="API响应时间",
                status=status,
                response_time=avg_time,
                details=f"平均响应时间: {avg_time:.0f}ms, 最大: {max_time:.0f}ms"
            )
        else:
            return TestResult(
                name="API响应时间",
                status=TestStatus.WARNING,
                details="无法获取响应时间数据"
            )
    
    # ================================
    # 运行所有测试
    # ================================
    
    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 60)
        print("🚀 Web3search 生产环境功能测试")
        print("=" * 60)
        print(f"前端URL: {self.frontend_url}")
        print(f"后端URL: {self.backend_url}")
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        print()
        
        # 基础系统测试
        print("📋 1. 基础系统测试")
        print("-" * 60)
        self.run_test("后端健康检查", self.test_backend_health)
        self.run_test("前端可访问性", self.test_frontend_accessibility)
        self.run_test("API文档", self.test_api_docs)
        print()
        
        # Quick Chat功能测试
        print("💬 2. Quick Chat功能测试")
        print("-" * 60)
        self.run_test("Quick Chat", self.test_quick_chat)
        self.run_test("Quick Chat流式输出", self.test_quick_chat_stream)
        print()
        
        # Deep Research功能测试
        print("🔬 3. Deep Research功能测试")
        print("-" * 60)
        self.run_test("Deep Research", self.test_deep_research)
        print()
        
        # 报告管理功能测试
        print("📄 4. 报告管理功能测试")
        print("-" * 60)
        self.run_test("报告列表", self.test_reports_list)
        print()
        
        # 搜索功能测试
        print("🔍 5. 搜索功能测试")
        print("-" * 60)
        self.run_test("搜索自动完成", self.test_search_autocomplete)
        print()
        
        # 热点识别功能测试
        print("🔥 6. 热点识别功能测试")
        print("-" * 60)
        self.run_test("热点识别", self.test_trending_hotspots)
        print()
        
        # 安全测试
        print("🔒 7. 安全测试")
        print("-" * 60)
        self.run_test("CORS配置", self.test_cors_config)
        self.run_test("输入验证", self.test_input_validation)
        self.run_test("空查询验证", self.test_empty_query)
        print()
        
        # 性能测试
        print("⚡ 8. 性能测试")
        print("-" * 60)
        self.run_test("API响应时间", self.test_api_response_time)
        print()
        
        # 生成报告
        self.generate_report()
    
    def generate_report(self):
        """生成测试报告"""
        print("=" * 60)
        print("📊 测试报告")
        print("=" * 60)
        
        passed = sum(1 for r in self.results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in self.results if r.status == TestStatus.FAILED)
        warning = sum(1 for r in self.results if r.status == TestStatus.WARNING)
        skipped = sum(1 for r in self.results if r.status == TestStatus.SKIPPED)
        total = len(self.results)
        
        print(f"\n总计: {total} 个测试")
        print(f"✅ 通过: {passed}")
        print(f"❌ 失败: {failed}")
        print(f"⚠️  警告: {warning}")
        print(f"⏭️  跳过: {skipped}")
        print(f"通过率: {(passed/total*100):.1f}%")
        print()
        
        # 失败的测试
        failed_tests = [r for r in self.results if r.status == TestStatus.FAILED]
        if failed_tests:
            print("❌ 失败的测试:")
            print("-" * 60)
            for test in failed_tests:
                print(f"  • {test.name}")
                if test.error:
                    print(f"    错误: {test.error[:100]}")
                print()
        
        # 警告的测试
        warning_tests = [r for r in self.results if r.status == TestStatus.WARNING]
        if warning_tests:
            print("⚠️  警告的测试:")
            print("-" * 60)
            for test in warning_tests:
                print(f"  • {test.name}: {test.details}")
            print()
        
        # 性能统计
        response_times = [r.response_time for r in self.results if r.response_time]
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)
            min_time = min(response_times)
            print("⚡ 性能统计:")
            print("-" * 60)
            print(f"  平均响应时间: {avg_time:.0f}ms")
            print(f"  最大响应时间: {max_time:.0f}ms")
            print(f"  最小响应时间: {min_time:.0f}ms")
            print()
        
        # 保存JSON报告
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "frontend_url": self.frontend_url,
            "backend_url": self.backend_url,
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "warning": warning,
                "skipped": skipped,
                "pass_rate": round(passed/total*100, 1) if total > 0 else 0
            },
            "results": [
                {
                    "name": r.name,
                    "status": r.status.value,
                    "duration": r.duration,
                    "details": r.details,
                    "error": r.error,
                    "response_time": r.response_time
                }
                for r in self.results
            ]
        }
        
        report_file = "production_test_report.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        print(f"📄 详细报告已保存到: {report_file}")
        print()
        
        # 返回退出码
        return 0 if failed == 0 else 1


if __name__ == "__main__":
    tester = ProductionTester()
    exit_code = tester.run_all_tests()
    sys.exit(exit_code)

