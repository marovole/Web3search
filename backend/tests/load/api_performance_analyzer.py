"""
API性能分析和优化工具
分析关键API端点性能瓶颈并提供优化建议
"""

import json
import time
import asyncio
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import psutil
import aiohttp
from concurrent.futures import ThreadPoolExecutor
import cProfile
import pstats
import io

@dataclass
class APIEndpoint:
    """API端点定义"""
    path: str
    method: str
    name: str
    description: str
    criticality: str  # critical, high, medium, low
    target_response_time: float  # ms
    current_avg_response_time: float = 0.0
    current_p95_response_time: float = 0.0
    current_error_rate: float = 0.0
    optimization_priority: int = 0

@dataclass
class PerformanceIssue:
    """性能问题"""
    endpoint: str
    issue_type: str
    severity: str  # critical, high, medium, low
    description: str
    impact: str
    recommendation: str
    estimated_improvement: str

@dataclass
class OptimizationResult:
    """优化结果"""
    endpoint: str
    optimization_type: str
    before_metrics: Dict[str, float]
    after_metrics: Dict[str, float]
    improvement_percentage: float
    implementation_cost: str  # low, medium, high
    roi_score: float

class APIPerformanceAnalyzer:
    """API性能分析器"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        self.endpoints = self._define_critical_endpoints()
        self.performance_data = {}
        self.issues = []
        self.optimizations = []
        
    def _define_critical_endpoints(self) -> List[APIEndpoint]:
        """定义关键API端点"""
        return [
            # Chat APIs - 最高优先级
            APIEndpoint(
                path="/api/v1/chat/quick-chat",
                method="POST",
                name="Quick Chat",
                description="快速AI对话接口",
                criticality="critical",
                target_response_time=3000,  # 3秒
                optimization_priority=1
            ),
            APIEndpoint(
                path="/api/v1/chat/deep-research",
                method="POST",
                name="Deep Research",
                description="深度研究报告生成",
                criticality="critical",
                target_response_time=60000,  # 60秒
                optimization_priority=2
            ),
            
            # Search APIs - 高优先级
            APIEndpoint(
                path="/api/v1/search/autocomplete",
                method="GET",
                name="Autocomplete Search",
                description="搜索自动补全",
                criticality="high",
                target_response_time=500,  # 0.5秒
                optimization_priority=3
            ),
            
            # Trending APIs - 高优先级
            APIEndpoint(
                path="/api/v1/trending/hotspots",
                method="GET",
                name="Market Hotspots",
                description="市场热点数据",
                criticality="high",
                target_response_time=1000,  # 1秒
                optimization_priority=4
            ),
            
            # Market Data APIs - 中等优先级
            APIEndpoint(
                path="/api/v1/market/data",
                method="GET",
                name="Market Data",
                description="市场数据查询",
                criticality="medium",
                target_response_time=800,  # 0.8秒
                optimization_priority=5
            ),
            
            # Health Check - 低优先级但重要
            APIEndpoint(
                path="/health",
                method="GET",
                name="Health Check",
                description="系统健康检查",
                criticality="low",
                target_response_time=100,  # 0.1秒
                optimization_priority=6
            )
        ]
    
    async def analyze_all_endpoints(self, concurrent_users: int = 10, duration: int = 60) -> Dict[str, Any]:
        """分析所有端点性能"""
        print(f"🔍 Starting comprehensive API performance analysis...")
        print(f"   - Concurrent users: {concurrent_users}")
        print(f"   - Test duration: {duration}s")
        print(f"   - Endpoints to test: {len(self.endpoints)}")
        
        self.session = aiohttp.ClientSession()
        
        try:
            # 分析每个端点
            for endpoint in self.endpoints:
                print(f"\n📊 Analyzing {endpoint.name}...")
                await self._analyze_endpoint(endpoint, concurrent_users, duration)
            
            # 识别性能问题
            self._identify_performance_issues()
            
            # 生成优化建议
            self._generate_optimization_recommendations()
            
            # 生成分析报告
            report = self._generate_analysis_report()
            
            return report
            
        finally:
            if self.session:
                await self.session.close()
    
    async def _analyze_endpoint(self, endpoint: APIEndpoint, concurrent_users: int, duration: int):
        """分析单个端点性能"""
        response_times = []
        errors = 0
        total_requests = 0
        
        # 准备测试数据
        test_data = self._get_test_data(endpoint)
        
        # 执行并发测试
        start_time = time.time()
        tasks = []
        
        for user_id in range(concurrent_users):
            task = self._simulate_user_load(endpoint, test_data, start_time, duration)
            tasks.append(task)
        
        # 等待所有任务完成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 收集结果
        for result in results:
            if isinstance(result, dict):
                response_times.extend(result['response_times'])
                errors += result['errors']
                total_requests += result['total_requests']
        
        # 计算性能指标
        if response_times:
            endpoint.current_avg_response_time = statistics.mean(response_times)
            endpoint.current_p95_response_time = self._percentile(response_times, 95)
            endpoint.current_error_rate = errors / total_requests if total_requests > 0 else 0
        
        # 保存性能数据
        self.performance_data[endpoint.name] = {
            'avg_response_time': endpoint.current_avg_response_time,
            'p95_response_time': endpoint.current_p95_response_time,
            'error_rate': endpoint.current_error_rate,
            'total_requests': total_requests,
            'total_errors': errors,
            'throughput': total_requests / duration if duration > 0 else 0,
            'response_times': response_times[:1000]  # 保存样本数据
        }
        
        print(f"   ✅ Average: {endpoint.current_avg_response_time:.0f}ms")
        print(f"   ✅ P95: {endpoint.current_p95_response_time:.0f}ms")
        print(f"   ✅ Error Rate: {endpoint.current_error_rate*100:.2f}%")
        print(f"   ✅ Throughput: {total_requests/duration:.1f} RPS")
    
    async def _simulate_user_load(self, endpoint: APIEndpoint, test_data: Dict, start_time: float, duration: int) -> Dict[str, Any]:
        """模拟用户负载"""
        response_times = []
        errors = 0
        total_requests = 0
        
        while time.time() - start_time < duration:
            try:
                # 发送请求
                request_start = time.time()
                
                if endpoint.method == "GET":
                    async with self.session.get(
                        f"{self.base_url}{endpoint.path}",
                        params=test_data.get('params', {}),
                        timeout=30
                    ) as response:
                        await response.text()
                        request_time = (time.time() - request_start) * 1000
                        
                        if response.status >= 400:
                            errors += 1
                        else:
                            response_times.append(request_time)
                            
                elif endpoint.method == "POST":
                    async with self.session.post(
                        f"{self.base_url}{endpoint.path}",
                        json=test_data.get('json', {}),
                        timeout=30
                    ) as response:
                        await response.text()
                        request_time = (time.time() - request_start) * 1000
                        
                        if response.status >= 400:
                            errors += 1
                        else:
                            response_times.append(request_time)
                
                total_requests += 1
                
                # 模拟用户思考时间
                await asyncio.sleep(0.1)
                
            except Exception as e:
                errors += 1
                total_requests += 1
                print(f"   ⚠️ Request failed: {e}")
        
        return {
            'response_times': response_times,
            'errors': errors,
            'total_requests': total_requests
        }
    
    def _get_test_data(self, endpoint: APIEndpoint) -> Dict[str, Any]:
        """获取端点测试数据"""
        test_data_map = {
            "/api/v1/chat/quick-chat": {
                "json": {
                    "query": "What is the current price of Bitcoin?",
                    "session_id": None
                }
            },
            "/api/v1/chat/deep-research": {
                "json": {
                    "query": "Bitcoin",
                    "symbol": "BTC",
                    "session_id": None
                }
            },
            "/api/v1/search/autocomplete": {
                "params": {"q": "BTC"}
            },
            "/api/v1/trending/hotspots": {
                "params": {"limit": 10}
            },
            "/api/v1/market/data": {
                "params": {"symbol": "BTC"}
            },
            "/health": {
                "params": {}
            }
        }
        
        return test_data_map.get(endpoint.path, {})
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """计算百分位数"""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def _identify_performance_issues(self):
        """识别性能问题"""
        self.issues = []
        
        for endpoint in self.endpoints:
            # 响应时间问题
            if endpoint.current_p95_response_time > endpoint.target_response_time:
                severity = "critical" if endpoint.current_p95_response_time > endpoint.target_response_time * 2 else "high"
                
                issue = PerformanceIssue(
                    endpoint=endpoint.name,
                    issue_type="response_time",
                    severity=severity,
                    description=f"P95响应时间 {endpoint.current_p95_response_time:.0f}ms 超过目标 {endpoint.target_response_time:.0f}ms",
                    impact="用户体验下降，可能影响转化率",
                    recommendation="优化数据库查询、添加缓存、减少外部API调用",
                    estimated_improvement=f"可减少 {((endpoint.current_p95_response_time - endpoint.target_response_time) / endpoint.current_p95_response_time * 100):.0f}% 响应时间"
                )
                self.issues.append(issue)
            
            # 错误率问题
            if endpoint.current_error_rate > 0.01:  # 1%
                severity = "critical" if endpoint.current_error_rate > 0.05 else "high"
                
                issue = PerformanceIssue(
                    endpoint=endpoint.name,
                    issue_type="error_rate",
                    severity=severity,
                    description=f"错误率 {endpoint.current_error_rate*100:.2f}% 超过可接受范围 1%",
                    impact="用户请求失败，影响系统可靠性",
                    recommendation="添加错误处理、实现熔断机制、优化资源管理",
                    estimated_improvement="可将错误率降低至 0.1% 以下"
                )
                self.issues.append(issue)
            
            # 吞吐量问题
            throughput = self.performance_data.get(endpoint.name, {}).get('throughput', 0)
            if throughput < 10 and endpoint.criticality in ['critical', 'high']:
                issue = PerformanceIssue(
                    endpoint=endpoint.name,
                    issue_type="throughput",
                    severity="medium",
                    description=f"吞吐量 {throughput:.1f} RPS 过低",
                    impact="无法支持高并发访问",
                    recommendation="优化连接池、增加并发处理能力、使用异步处理",
                    estimated_improvement="可提升吞吐量 3-5 倍"
                )
                self.issues.append(issue)
    
    def _generate_optimization_recommendations(self):
        """生成优化建议"""
        self.optimizations = []
        
        for endpoint in self.endpoints:
            optimizations = self._get_endpoint_optimizations(endpoint)
            self.optimizations.extend(optimizations)
    
    def _get_endpoint_optimizations(self, endpoint: APIEndpoint) -> List[OptimizationResult]:
        """获取端点优化建议"""
        optimizations = []
        
        # 基于端点类型提供具体优化建议
        if "quick-chat" in endpoint.path:
            optimizations.append(OptimizationResult(
                endpoint=endpoint.name,
                optimization_type="AI模型优化",
                before_metrics={"response_time": endpoint.current_avg_response_time},
                after_metrics={"response_time": endpoint.current_avg_response_time * 0.7},
                improvement_percentage=30,
                implementation_cost="medium",
                roi_score=8.5
            ))
            
            optimizations.append(OptimizationResult(
                endpoint=endpoint.name,
                optimization_type="响应缓存",
                before_metrics={"response_time": endpoint.current_avg_response_time},
                after_metrics={"response_time": endpoint.current_avg_response_time * 0.3},
                improvement_percentage=70,
                implementation_cost="low",
                roi_score=9.5
            ))
        
        elif "deep-research" in endpoint.path:
            optimizations.append(OptimizationResult(
                endpoint=endpoint.name,
                optimization_type="并行数据处理",
                before_metrics={"response_time": endpoint.current_avg_response_time},
                after_metrics={"response_time": endpoint.current_avg_response_time * 0.6},
                improvement_percentage=40,
                implementation_cost="high",
                roi_score=7.0
            ))
        
        elif "autocomplete" in endpoint.path:
            optimizations.append(OptimizationResult(
                endpoint=endpoint.name,
                optimization_type="搜索索引优化",
                before_metrics={"response_time": endpoint.current_avg_response_time},
                after_metrics={"response_time": endpoint.current_avg_response_time * 0.4},
                improvement_percentage=60,
                implementation_cost="medium",
                roi_score=8.0
            ))
        
        elif "hotspots" in endpoint.path:
            optimizations.append(OptimizationResult(
                endpoint=endpoint.name,
                optimization_type="数据预计算",
                before_metrics={"response_time": endpoint.current_avg_response_time},
                after_metrics={"response_time": endpoint.current_avg_response_time * 0.2},
                improvement_percentage=80,
                implementation_cost="medium",
                roi_score=9.0
            ))
        
        return optimizations
    
    def _generate_analysis_report(self) -> Dict[str, Any]:
        """生成分析报告"""
        # 计算整体性能分数
        total_score = 0
        max_score = 0
        
        for endpoint in self.endpoints:
            # 响应时间分数 (40%)
            response_score = max(0, 100 - (endpoint.current_p95_response_time / endpoint.target_response_time - 1) * 100)
            if endpoint.current_p95_response_time <= endpoint.target_response_time:
                response_score = 100
            
            # 错误率分数 (30%)
            error_score = max(0, 100 - endpoint.current_error_rate * 10000)
            
            # 吞吐量分数 (30%)
            throughput = self.performance_data.get(endpoint.name, {}).get('throughput', 0)
            throughput_score = min(100, throughput * 10)
            
            endpoint_score = (response_score * 0.4 + error_score * 0.3 + throughput_score * 0.3)
            total_score += endpoint_score
            max_score += 100
        
        overall_score = (total_score / max_score * 100) if max_score > 0 else 0
        
        # 按严重程度分类问题
        critical_issues = [issue for issue in self.issues if issue.severity == "critical"]
        high_issues = [issue for issue in self.issues if issue.severity == "high"]
        medium_issues = [issue for issue in self.issues if issue.severity == "medium"]
        
        # 计算优化潜力
        total_optimization_potential = sum(opt.improvement_percentage for opt in self.optimizations)
        avg_roi = statistics.mean([opt.roi_score for opt in self.optimizations]) if self.optimizations else 0
        
        report = {
            "analysis_timestamp": datetime.now().isoformat(),
            "base_url": self.base_url,
            "overall_performance_score": overall_score,
            "summary": {
                "total_endpoints": len(self.endpoints),
                "critical_issues": len(critical_issues),
                "high_issues": len(high_issues),
                "medium_issues": len(medium_issues),
                "total_issues": len(self.issues),
                "optimization_opportunities": len(self.optimizations),
                "estimated_improvement_potential": total_optimization_potential / len(self.optimizations) if self.optimizations else 0
            },
            "endpoint_performance": [
                {
                    "name": endpoint.name,
                    "path": endpoint.path,
                    "criticality": endpoint.criticality,
                    "avg_response_time": endpoint.current_avg_response_time,
                    "p95_response_time": endpoint.current_p95_response_time,
                    "target_response_time": endpoint.target_response_time,
                    "error_rate": endpoint.current_error_rate,
                    "performance_score": max(0, 100 - (endpoint.current_p95_response_time / endpoint.target_response_time - 1) * 100)
                }
                for endpoint in self.endpoints
            ],
            "performance_issues": [asdict(issue) for issue in self.issues],
            "optimization_recommendations": [asdict(opt) for opt in self.optimizations],
            "system_metrics": self._get_system_metrics(),
            "recommendations": self._get_prioritized_recommendations()
        }
        
        return report
    
    def _get_system_metrics(self) -> Dict[str, Any]:
        """获取系统指标"""
        return {
            "cpu_usage": psutil.cpu_percent(interval=1),
            "memory_usage": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "network_connections": len(psutil.net_connections()),
            "process_count": len(psutil.pids())
        }
    
    def _get_prioritized_recommendations(self) -> List[Dict[str, Any]]:
        """获取优先级建议"""
        recommendations = []
        
        # 立即修复的关键问题
        critical_issues = [issue for issue in self.issues if issue.severity == "critical"]
        if critical_issues:
            recommendations.append({
                "priority": "immediate",
                "title": "修复关键性能问题",
                "description": f"发现 {len(critical_issues)} 个关键性能问题需要立即修复",
                "actions": [issue.recommendation for issue in critical_issues],
                "estimated_impact": "显著提升用户体验和系统稳定性"
            })
        
        # 高ROI优化
        high_roi_optimizations = [opt for opt in self.optimizations if opt.roi_score >= 8.0]
        if high_roi_optimizations:
            recommendations.append({
                "priority": "high",
                "title": "实施高ROI优化",
                "description": f"发现 {len(high_roi_optimizations)} 个高投资回报率优化机会",
                "actions": [f"{opt.optimization_type} (预期提升 {opt.improvement_percentage}%)" for opt in high_roi_optimizations[:3]],
                "estimated_impact": "快速提升性能，用户感知明显"
            })
        
        # 监控和告警
        recommendations.append({
            "priority": "medium",
            "title": "建立性能监控体系",
            "description": "实施全面的性能监控和告警机制",
            "actions": [
                "部署APM工具监控API响应时间",
                "设置性能阈值告警",
                "建立性能回归检测机制",
                "定期执行性能测试"
            ],
            "estimated_impact": "持续保障性能，快速发现问题"
        })
        
        return recommendations
    
    def save_report(self, filename: str = None):
        """保存分析报告"""
        if filename is None:
            filename = f"api_performance_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report = self._generate_analysis_report()
        
        with open(filename, "w") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"📁 Performance analysis report saved to: {filename}")
        return filename

if __name__ == "__main__":
    async def main():
        analyzer = APIPerformanceAnalyzer()
        
        # 执行性能分析
        report = await analyzer.analyze_all_endpoints(
            concurrent_users=5,
            duration=30
        )
        
        # 保存报告
        analyzer.save_report()
        
        # 打印摘要
        print("\n" + "="*60)
        print("📊 API PERFORMANCE ANALYSIS SUMMARY")
        print("="*60)
        print(f"Overall Performance Score: {report['overall_performance_score']:.1f}/100")
        print(f"Critical Issues: {report['summary']['critical_issues']}")
        print(f"High Issues: {report['summary']['high_issues']}")
        print(f"Optimization Opportunities: {report['summary']['optimization_opportunities']}")
        print(f"Estimated Improvement Potential: {report['summary']['estimated_improvement_potential']:.1f}%")
        
        print("\n🎯 Top Recommendations:")
        for i, rec in enumerate(report['recommendations'][:3], 1):
            print(f"{i}. [{rec['priority'].upper()}] {rec['title']}")
            print(f"   {rec['description']}")
        
        print("\n📈 System Metrics:")
        metrics = report['system_metrics']
        print(f"   CPU Usage: {metrics['cpu_usage']:.1f}%")
        print(f"   Memory Usage: {metrics['memory_usage']:.1f}%")
        print(f"   Disk Usage: {metrics['disk_usage']:.1f}%")
    
    # 运行分析
    asyncio.run(main())
