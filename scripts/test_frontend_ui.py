#!/usr/bin/env python3
"""
前端UI功能测试脚本
使用Playwright测试前端界面功能
"""

import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class TestStatus(Enum):
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"


@dataclass
class UITestResult:
    name: str
    status: TestStatus
    duration: float = 0.0
    details: str = ""
    error: Optional[str] = None
    screenshot: Optional[str] = None


class FrontendUITester:
    """前端UI测试器"""
    
    def __init__(self):
        self.frontend_url = "https://web3search.vercel.app"
        self.backend_url = "https://web3search-api.onrender.com"
        self.results: List[UITestResult] = []
        self.screenshots_dir = "test_screenshots"
        
    async def run_test(self, name: str, test_func) -> UITestResult:
        """运行单个测试"""
        import time
        start_time = time.time()
        try:
            result = await test_func()
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
            result = UITestResult(
                name=name,
                status=TestStatus.FAILED,
                duration=duration,
                details=f"测试异常: {str(e)}",
                error=str(e)
            )
            self.results.append(result)
            print(f"❌ {name}: 测试异常 - {str(e)}")
            return result
    
    async def test_page_load(self, page) -> UITestResult:
        """测试页面加载"""
        try:
            await page.goto(self.frontend_url, timeout=30000, wait_until="networkidle")
            title = await page.title()
            
            if title and len(title) > 0:
                return UITestResult(
                    name="页面加载",
                    status=TestStatus.PASSED,
                    details=f"页面成功加载, 标题: {title}"
                )
            else:
                return UITestResult(
                    name="页面加载",
                    status=TestStatus.FAILED,
                    details="页面加载但标题为空",
                    error="页面标题为空"
                )
        except PlaywrightTimeout:
            return UITestResult(
                name="页面加载",
                status=TestStatus.FAILED,
                details="页面加载超时",
                error="30秒内页面未加载完成"
            )
        except Exception as e:
            return UITestResult(
                name="页面加载",
                status=TestStatus.FAILED,
                details=f"页面加载失败: {str(e)}",
                error=str(e)
            )
    
    async def test_ui_elements(self, page) -> UITestResult:
        """测试UI元素存在"""
        try:
            # 检查关键UI元素
            elements_found = []
            elements_missing = []
            
            selectors = [
                ("input[type='text']", "输入框"),
                ("button", "按钮"),
                ("main", "主内容区"),
            ]
            
            for selector, name in selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=5000)
                    if element:
                        elements_found.append(name)
                    else:
                        elements_missing.append(name)
                except:
                    elements_missing.append(name)
            
            if len(elements_found) > 0:
                status = TestStatus.PASSED if len(elements_missing) == 0 else TestStatus.WARNING
                return UITestResult(
                    name="UI元素检查",
                    status=status,
                    details=f"找到{len(elements_found)}个元素, 缺失{len(elements_missing)}个: {', '.join(elements_missing) if elements_missing else '无'}"
                )
            else:
                return UITestResult(
                    name="UI元素检查",
                    status=TestStatus.FAILED,
                    details="未找到任何关键UI元素",
                    error="页面结构异常"
                )
        except Exception as e:
            return UITestResult(
                name="UI元素检查",
                status=TestStatus.FAILED,
                details=f"检查异常: {str(e)}",
                error=str(e)
            )
    
    async def test_console_errors(self, page) -> UITestResult:
        """测试控制台错误"""
        try:
            console_errors = []
            
            def handle_console(msg):
                if msg.type == "error":
                    console_errors.append(msg.text)
            
            page.on("console", handle_console)
            await page.reload(wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(2000)
            
            if len(console_errors) == 0:
                return UITestResult(
                    name="控制台错误检查",
                    status=TestStatus.PASSED,
                    details="未发现控制台错误"
                )
            else:
                return UITestResult(
                    name="控制台错误检查",
                    status=TestStatus.WARNING,
                    details=f"发现{len(console_errors)}个控制台错误",
                    error="; ".join(console_errors[:3])  # 只显示前3个
                )
        except Exception as e:
            return UITestResult(
                name="控制台错误检查",
                status=TestStatus.FAILED,
                details=f"检查异常: {str(e)}",
                error=str(e)
            )
    
    async def test_responsive_design(self, page) -> UITestResult:
        """测试响应式设计"""
        try:
            viewports = [
                (1920, 1080, "桌面"),
                (768, 1024, "平板"),
                (375, 667, "移动端"),
            ]
            
            results = []
            for width, height, name in viewports:
                await page.set_viewport_size({"width": width, "height": height})
                await page.wait_for_timeout(500)
                
                # 检查页面是否正常渲染
                body = await page.query_selector("body")
                if body:
                    results.append(f"{name}: 正常")
                else:
                    results.append(f"{name}: 异常")
            
            return UITestResult(
                name="响应式设计",
                status=TestStatus.PASSED,
                details=f"测试了{len(viewports)}种屏幕尺寸: {', '.join(results)}"
            )
        except Exception as e:
            return UITestResult(
                name="响应式设计",
                status=TestStatus.FAILED,
                details=f"测试异常: {str(e)}",
                error=str(e)
            )
    
    async def test_api_connectivity(self, page) -> UITestResult:
        """测试API连通性"""
        try:
            # 检查网络请求
            api_calls = []
            
            def handle_request(request):
                url = request.url
                if "api" in url or "onrender.com" in url:
                    api_calls.append(url)
            
            page.on("request", handle_request)
            
            # 尝试触发API调用（如果有搜索框）
            try:
                search_input = await page.query_selector("input[type='text']")
                if search_input:
                    await search_input.fill("test")
                    await page.wait_for_timeout(1000)
            except:
                pass
            
            if len(api_calls) > 0:
                return UITestResult(
                    name="API连通性",
                    status=TestStatus.PASSED,
                    details=f"检测到{len(api_calls)}个API调用"
                )
            else:
                return UITestResult(
                    name="API连通性",
                    status=TestStatus.WARNING,
                    details="未检测到API调用（可能页面未触发）"
                )
        except Exception as e:
            return UITestResult(
                name="API连通性",
                status=TestStatus.FAILED,
                details=f"测试异常: {str(e)}",
                error=str(e)
            )
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("=" * 60)
        print("🌐 Web3search 前端UI功能测试")
        print("=" * 60)
        print(f"前端URL: {self.frontend_url}")
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        print()
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            )
            page = await context.new_page()
            
            try:
                # 基础功能测试
                print("📋 1. 基础功能测试")
                print("-" * 60)
                await self.run_test("页面加载", lambda: self.test_page_load(page))
                await self.run_test("UI元素检查", lambda: self.test_ui_elements(page))
                await self.run_test("控制台错误检查", lambda: self.test_console_errors(page))
                print()
                
                # 响应式设计测试
                print("📱 2. 响应式设计测试")
                print("-" * 60)
                await self.run_test("响应式设计", lambda: self.test_responsive_design(page))
                print()
                
                # API连通性测试
                print("🔌 3. API连通性测试")
                print("-" * 60)
                await self.run_test("API连通性", lambda: self.test_api_connectivity(page))
                print()
                
            finally:
                await browser.close()
            
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
                print(f"  • {test.name}: {test.details}")
            print()
        
        # 保存JSON报告
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "frontend_url": self.frontend_url,
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
                    "error": r.error
                }
                for r in self.results
            ]
        }
        
        report_file = "frontend_ui_test_report.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        print(f"📄 详细报告已保存到: {report_file}")
        print()


if __name__ == "__main__":
    tester = FrontendUITester()
    asyncio.run(tester.run_all_tests())

