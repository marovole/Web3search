"""
性能基准测试和监控配置
定义性能目标、基准线和监控指标
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import statistics

@dataclass
class PerformanceTarget:
    """性能目标定义"""
    name: str
    metric: str
    target_value: float
    threshold_value: float  # 警告阈值
    unit: str
    description: str
    
@dataclass
class BenchmarkResult:
    """基准测试结果"""
    test_name: str
    timestamp: str
    users: int
    duration: int
    metrics: Dict[str, float]
    targets_met: Dict[str, bool]
    overall_success: bool

class PerformanceBenchmark:
    """性能基准测试管理器"""
    
    # 性能目标定义
    PERFORMANCE_TARGETS = {
        "quick_chat": [
            PerformanceTarget(
                name="response_time_p50",
                metric="response_time_p50",
                target_value=2000.0,
                threshold_value=2500.0,
                unit="ms",
                description="Quick Chat 50分位响应时间"
            ),
            PerformanceTarget(
                name="response_time_p95",
                metric="response_time_p95", 
                target_value=3000.0,
                threshold_value=4000.0,
                unit="ms",
                description="Quick Chat 95分位响应时间"
            ),
            PerformanceTarget(
                name="response_time_p99",
                metric="response_time_p99",
                target_value=5000.0,
                threshold_value=6000.0,
                unit="ms", 
                description="Quick Chat 99分位响应时间"
            ),
            PerformanceTarget(
                name="error_rate",
                metric="error_rate",
                target_value=0.001,  # 0.1%
                threshold_value=0.005,  # 0.5%
                unit="ratio",
                description="Quick Chat 错误率"
            ),
            PerformanceTarget(
                name="throughput",
                metric="requests_per_second",
                target_value=500.0,
                threshold_value=300.0,
                unit="rps",
                description="Quick Chat 吞吐量"
            )
        ],
        
        "deep_research": [
            PerformanceTarget(
                name="response_time_p95",
                metric="response_time_p95",
                target_value=60000.0,
                threshold_value=90000.0,
                unit="ms",
                description="Deep Research 95分位响应时间"
            ),
            PerformanceTarget(
                name="success_rate",
                metric="success_rate",
                target_value=0.95,
                threshold_value=0.90,
                unit="ratio",
                description="Deep Research 成功率"
            )
        ],
        
        "hotspots": [
            PerformanceTarget(
                name="response_time_p95",
                metric="response_time_p95",
                target_value=1000.0,
                threshold_value=1500.0,
                unit="ms",
                description="Hotspots 95分位响应时间"
            ),
            PerformanceTarget(
                name="throughput",
                metric="requests_per_second",
                target_value=100.0,
                threshold_value=50.0,
                unit="rps",
                description="Hotspots 吞吐量"
            )
        ],
        
        "autocomplete": [
            PerformanceTarget(
                name="response_time_p95",
                metric="response_time_p95",
                target_value=500.0,
                threshold_value=800.0,
                unit="ms",
                description="Autocomplete 95分位响应时间"
            ),
            PerformanceTarget(
                name="throughput",
                metric="requests_per_second",
                target_value=200.0,
                threshold_value=100.0,
                unit="rps",
                description="Autocomplete 吞吐量"
            )
        ],
        
        "market_data": [
            PerformanceTarget(
                name="response_time_p95",
                metric="response_time_p95",
                target_value=800.0,
                threshold_value=1200.0,
                unit="ms",
                description="Market Data 95分位响应时间"
            ),
            PerformanceTarget(
                name="throughput",
                metric="requests_per_second",
                target_value=150.0,
                threshold_value=80.0,
                unit="rps",
                description="Market Data 吞吐量"
            )
        ]
    }
    
    # 负载测试场景基准
    LOAD_TEST_SCENARIOS = {
        "smoke_test": {
            "users": 50,
            "duration": 60,
            "description": "冒烟测试 - 验证基本功能"
        },
        "functional_test": {
            "users": 200,
            "duration": 120,
            "description": "功能测试 - 验证完整功能"
        },
        "load_test": {
            "users": 1000,
            "duration": 300,
            "description": "负载测试 - 1000并发用户"
        },
        "stress_test": {
            "users": 1500,
            "duration": 600,
            "description": "压力测试 - 1500并发用户"
        },
        "peak_test": {
            "users": 2000,
            "duration": 180,
            "description": "峰值测试 - 2000并发用户"
        }
    }
    
    def __init__(self):
        self.baseline_data = {}
        self.historical_results = []
        
    def run_benchmark(self, test_name: str, locust_stats: Dict) -> BenchmarkResult:
        """运行基准测试并评估结果"""
        print(f"🎯 Running benchmark: {test_name}")
        
        # 提取关键指标
        metrics = self._extract_metrics(locust_stats)
        
        # 评估性能目标
        targets_met = {}
        overall_success = True
        
        for endpoint_name, targets in self.PERFORMANCE_TARGETS.items():
            endpoint_metrics = metrics.get(endpoint_name, {})
            endpoint_targets_met = {}
            
            for target in targets:
                actual_value = endpoint_metrics.get(target.metric)
                if actual_value is not None:
                    # 根据指标类型判断是否满足目标
                    if target.metric in ["error_rate"] or "rate" in target.metric:
                        # 对于错误率等指标，值越小越好
                        met = actual_value <= target.target_value
                    else:
                        # 对于响应时间等指标，值越小越好
                        met = actual_value <= target.target_value
                    
                    endpoint_targets_met[target.name] = met
                    
                    if not met:
                        overall_success = False
                        
                    # 记录警告
                    if not met and actual_value <= target.threshold_value:
                        print(f"⚠️ {target.name}: {actual_value:.2f}{target.unit} (target: {target.target_value:.2f}{target.unit})")
                    elif not met:
                        print(f"❌ {target.name}: {actual_value:.2f}{target.unit} (target: {target.target_value:.2f}{target.unit})")
                    else:
                        print(f"✅ {target.name}: {actual_value:.2f}{target.unit}")
                        
            targets_met[endpoint_name] = endpoint_targets_met
            
        # 创建基准测试结果
        result = BenchmarkResult(
            test_name=test_name,
            timestamp=datetime.now().isoformat(),
            users=locust_stats.get("users", 0),
            duration=locust_stats.get("duration", 0),
            metrics=metrics,
            targets_met=targets_met,
            overall_success=overall_success
        )
        
        # 保存结果
        self.historical_results.append(result)
        
        print(f"📊 Benchmark {test_name}: {'✅ PASSED' if overall_success else '❌ FAILED'}")
        
        return result
        
    def _extract_metrics(self, locust_stats: Dict) -> Dict[str, Dict[str, float]]:
        """从Locust统计数据中提取关键指标"""
        metrics = {}
        
        # 处理每个端点的统计数据
        for name, stats in locust_stats.get("requests", {}).items():
            endpoint_name = self._get_endpoint_name(name)
            
            if endpoint_name not in metrics:
                metrics[endpoint_name] = {}
                
            # 响应时间指标
            metrics[endpoint_name]["response_time_p50"] = stats.get("median_response_time", 0)
            metrics[endpoint_name]["response_time_p95"] = stats.get("p95_response_time", 0)
            metrics[endpoint_name]["response_time_p99"] = stats.get("p99_response_time", 0)
            
            # 错误率和成功率
            total_requests = stats.get("num_requests", 0)
            failed_requests = stats.get("num_failures", 0)
            
            if total_requests > 0:
                metrics[endpoint_name]["error_rate"] = failed_requests / total_requests
                metrics[endpoint_name]["success_rate"] = (total_requests - failed_requests) / total_requests
            else:
                metrics[endpoint_name]["error_rate"] = 0.0
                metrics[endpoint_name]["success_rate"] = 0.0
                
            # 吞吐量
            metrics[endpoint_name]["requests_per_second"] = stats.get("total_rps", 0)
            
        return metrics
        
    def _get_endpoint_name(self, locust_name: str) -> str:
        """从Locust任务名称获取端点名称"""
        if "quick-chat" in locust_name:
            return "quick_chat"
        elif "deep-research" in locust_name:
            return "deep_research"
        elif "hotspots" in locust_name:
            return "hotspots"
        elif "autocomplete" in locust_name:
            return "autocomplete"
        elif "market-data" in locust_name:
            return "market_data"
        else:
            return "unknown"
            
    def save_benchmark_results(self, filename: str = None):
        """保存基准测试结果"""
        if filename is None:
            filename = f"benchmark_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
        results_data = {
            "timestamp": datetime.now().isoformat(),
            "performance_targets": {
                name: [asdict(target) for target in targets]
                for name, targets in self.PERFORMANCE_TARGETS.items()
            },
            "load_test_scenarios": self.LOAD_TEST_SCENARIOS,
            "results": [asdict(result) for result in self.historical_results]
        }
        
        with open(filename, "w") as f:
            json.dump(results_data, f, indent=2)
            
        print(f"📁 Benchmark results saved to: {filename}")
        
    def generate_performance_report(self) -> str:
        """生成性能报告"""
        if not self.historical_results:
            return "No benchmark results available"
            
        report = []
        report.append("# Performance Benchmark Report")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # 总体摘要
        total_tests = len(self.historical_results)
        passed_tests = sum(1 for r in self.historical_results if r.overall_success)
        
        report.append("## Summary")
        report.append(f"- Total Tests: {total_tests}")
        report.append(f"- Passed: {passed_tests}")
        report.append(f"- Failed: {total_tests - passed_tests}")
        report.append(f"- Success Rate: {passed_tests/total_tests*100:.1f}%")
        report.append("")
        
        # 详细结果
        report.append("## Detailed Results")
        
        for result in self.historical_results:
            status = "✅ PASSED" if result.overall_success else "❌ FAILED"
            report.append(f"### {result.test_name} - {status}")
            report.append(f"- Users: {result.users}")
            report.append(f"- Duration: {result.duration}s")
            report.append(f"- Timestamp: {result.timestamp}")
            
            # 关键指标
            for endpoint, metrics in result.metrics.items():
                if metrics:
                    report.append(f"- **{endpoint}**:")
                    for metric, value in metrics.items():
                        if "rate" in metric:
                            report.append(f"  - {metric}: {value*100:.2f}%")
                        else:
                            report.append(f"  - {metric}: {value:.0f}ms")
            report.append("")
            
        return "\n".join(report)
        
    def compare_with_baseline(self, current_result: BenchmarkResult) -> Dict[str, Any]:
        """与基准线比较"""
        comparison = {
            "test_name": current_result.test_name,
            "timestamp": current_result.timestamp,
            "comparisons": {}
        }
        
        # 找到最近的基准线结果
        baseline = self._find_baseline(current_result.test_name)
        
        if baseline is None:
            comparison["status"] = "no_baseline"
            return comparison
            
        # 比较各项指标
        for endpoint, current_metrics in current_result.metrics.items():
            baseline_metrics = baseline.metrics.get(endpoint, {})
            endpoint_comparison = {}
            
            for metric, current_value in current_metrics.items():
                baseline_value = baseline_metrics.get(metric)
                
                if baseline_value is not None:
                    change_percent = ((current_value - baseline_value) / baseline_value) * 100
                    endpoint_comparison[metric] = {
                        "current": current_value,
                        "baseline": baseline_value,
                        "change_percent": change_percent,
                        "trend": "improved" if change_percent < 0 else "degraded"
                    }
                    
            comparison["comparisons"][endpoint] = endpoint_comparison
            
        # 总体趋势
        all_changes = []
        for endpoint_comp in comparison["comparisons"].values():
            for metric_comp in endpoint_comp.values():
                all_changes.append(metric_comp["change_percent"])
                
        if all_changes:
            avg_change = statistics.mean(all_changes)
            comparison["overall_trend"] = "improved" if avg_change < 0 else "degraded"
            comparison["average_change_percent"] = avg_change
            
        return comparison
        
    def _find_baseline(self, test_name: str) -> Optional[BenchmarkResult]:
        """找到指定测试的基准线结果"""
        # 查找相同测试的历史结果
        same_tests = [r for r in self.historical_results if r.test_name == test_name]
        
        if len(same_tests) >= 2:
            # 返回倒数第二个结果作为基准线
            return same_tests[-2]
        elif len(same_tests) == 1:
            # 如果只有一个结果，返回它自己作为基准线
            return same_tests[0]
        else:
            return None

# 性能监控配置
MONITORING_CONFIG = {
    "metrics_collection": {
        "interval_seconds": 5,
        "retention_days": 30,
        "storage_path": "metrics/"
    },
    
    "alerts": {
        "response_time_threshold": {
            "quick_chat_p95": 4000,  # ms
            "deep_research_p95": 90000,  # ms
            "hotspots_p95": 1500,  # ms
            "autocomplete_p95": 800,  # ms
            "market_data_p95": 1200  # ms
        },
        "error_rate_threshold": 0.01,  # 1%
        "throughput_threshold": {
            "quick_chat": 300,  # rps
            "hotspots": 50,  # rps
            "autocomplete": 100,  # rps
            "market_data": 80   # rps
        }
    },
    
    "dashboard": {
        "refresh_interval": 10,  # seconds
        "chart_history_points": 100,
        "performance_targets": PERFORMANCE_TARGETS
    }
}

if __name__ == "__main__":
    # 示例用法
    benchmark = PerformanceBenchmark()
    
    # 模拟Locust统计数据
    mock_stats = {
        "users": 1000,
        "duration": 300,
        "requests": {
            "/api/v1/chat/quick-chat": {
                "num_requests": 10000,
                "num_failures": 50,
                "median_response_time": 1800,
                "p95_response_time": 2800,
                "p99_response_time": 4500,
                "total_rps": 550
            },
            "/api/v1/trending/hotspots": {
                "num_requests": 2000,
                "num_failures": 10,
                "median_response_time": 400,
                "p95_response_time": 800,
                "p99_response_time": 1200,
                "total_rps": 110
            }
        }
    }
    
    # 运行基准测试
    result = benchmark.run_benchmark("load_test_1000", mock_stats)
    
    # 生成报告
    report = benchmark.generate_performance_report()
    print(report)
    
    # 保存结果
    benchmark.save_benchmark_results()
