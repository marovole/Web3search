"""
API性能基准和回归检测系统
建立性能基准，自动检测性能回归，提供趋势分析
"""

import asyncio
import time
import json
import statistics
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict, deque
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RegressionType(Enum):
    """回归类型"""
    PERFORMANCE = "performance"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"
    AVAILABILITY = "availability"

class Severity(Enum):
    """严重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class PerformanceBaseline:
    """性能基准"""
    endpoint: str
    method: str
    metric_name: str
    baseline_value: float
    tolerance_percent: float
    sample_size: int
    created_at: float
    updated_at: float

@dataclass
class PerformanceTestResult:
    """性能测试结果"""
    endpoint: str
    method: str
    metric_name: str
    current_value: float
    baseline_value: float
    deviation_percent: float
    is_regression: bool
    severity: Severity
    timestamp: float
    test_duration: float

@dataclass
class RegressionAlert:
    """回归告警"""
    id: str
    endpoint: str
    method: str
    regression_type: RegressionType
    severity: Severity
    current_value: float
    baseline_value: float
    deviation_percent: float
    message: str
    timestamp: float
    resolved: bool = False

class PerformanceBaselineManager:
    """性能基准管理器"""
    
    def __init__(self):
        self.baselines = {}
        self.test_history = defaultdict(list)
        self.regression_thresholds = {
            "response_time": 15.0,      # 15%增长视为回归
            "error_rate": 50.0,         # 50%增长视为回归
            "throughput": 20.0,         # 20%下降视为回归
            "availability": 5.0         # 5%下降视为回归
        }
        
    def create_baseline(self, endpoint: str, method: str, metric_name: str, 
                        values: List[float], tolerance_percent: float = 10.0) -> PerformanceBaseline:
        """创建性能基准"""
        if len(values) < 10:
            raise ValueError("需要至少10个数据点来创建基准")
        
        # 计算基准值（使用P95而不是平均值，更稳定）
        sorted_values = sorted(values)
        baseline_value = sorted_values[int(len(sorted_values) * 0.95)]
        
        baseline = PerformanceBaseline(
            endpoint=endpoint,
            method=method,
            metric_name=metric_name,
            baseline_value=baseline_value,
            tolerance_percent=tolerance_percent,
            sample_size=len(values),
            created_at=time.time(),
            updated_at=time.time()
        )
        
        key = f"{method}:{endpoint}:{metric_name}"
        self.baselines[key] = baseline
        
        logger.info(f"Created baseline for {key}: {baseline_value:.2f} (±{tolerance_percent}%)")
        return baseline
    
    def update_baseline(self, endpoint: str, method: str, metric_name: str, 
                       new_values: List[float]) -> PerformanceBaseline:
        """更新性能基准"""
        key = f"{method}:{endpoint}:{metric_name}"
        
        if key not in self.baselines:
            return self.create_baseline(endpoint, method, metric_name, new_values)
        
        # 合并历史数据和新数据
        existing_baseline = self.baselines[key]
        all_values = new_values + [existing_baseline.baseline_value]
        
        # 重新计算基准
        return self.create_baseline(endpoint, method, metric_name, all_values, 
                                   existing_baseline.tolerance_percent)
    
    def get_baseline(self, endpoint: str, method: str, metric_name: str) -> Optional[PerformanceBaseline]:
        """获取性能基准"""
        key = f"{method}:{endpoint}:{metric_name}"
        return self.baselines.get(key)
    
    def list_baselines(self) -> List[PerformanceBaseline]:
        """列出所有基准"""
        return list(self.baselines.values())

class PerformanceRegressionDetector:
    """性能回归检测器"""
    
    def __init__(self, baseline_manager: PerformanceBaselineManager):
        self.baseline_manager = baseline_manager
        self.regression_history = deque(maxlen=1000)
        self.active_regressions = {}
        self.test_history = defaultdict(list)
        
    def detect_regression(self, endpoint: str, method: str, metric_name: str, 
                          current_value: float) -> Optional[PerformanceTestResult]:
        """检测性能回归"""
        baseline = self.baseline_manager.get_baseline(endpoint, method, metric_name)
        
        if not baseline:
            logger.warning(f"No baseline found for {method}:{endpoint}:{metric_name}")
            return None
        
        # 计算偏差
        deviation_percent = self._calculate_deviation(current_value, baseline.baseline_value, metric_name)
        
        # 判断是否为回归
        threshold = self._get_regression_threshold(metric_name)
        is_regression = abs(deviation_percent) > threshold
        
        # 确定严重程度
        severity = self._calculate_severity(deviation_percent, threshold)
        
        # 创建测试结果
        result = PerformanceTestResult(
            endpoint=endpoint,
            method=method,
            metric_name=metric_name,
            current_value=current_value,
            baseline_value=baseline.baseline_value,
            deviation_percent=deviation_percent,
            is_regression=is_regression,
            severity=severity,
            timestamp=time.time(),
            test_duration=0.1  # 模拟测试时间
        )
        
        # 记录历史
        key = f"{method}:{endpoint}:{metric_name}"
        self.test_history[key].append(result)
        
        # 如果是回归，创建告警
        if is_regression:
            self._create_regression_alert(result)
        
        return result
    
    def _calculate_deviation(self, current: float, baseline: float, metric_name: str) -> float:
        """计算偏差百分比"""
        if baseline == 0:
            return 0.0
        
        if metric_name in ["response_time", "error_rate"]:
            # 对于响应时间和错误率，增长是坏的
            return ((current - baseline) / baseline) * 100
        else:
            # 对于吞吐量和可用性，下降是坏的
            return ((baseline - current) / baseline) * 100
    
    def _get_regression_threshold(self, metric_name: str) -> float:
        """获取回归阈值"""
        return self.baseline_manager.regression_thresholds.get(metric_name, 10.0)
    
    def _calculate_severity(self, deviation: float, threshold: float) -> Severity:
        """计算严重程度"""
        ratio = abs(deviation) / threshold
        
        if ratio >= 3.0:
            return Severity.CRITICAL
        elif ratio >= 2.0:
            return Severity.HIGH
        elif ratio >= 1.5:
            return Severity.MEDIUM
        else:
            return Severity.LOW
    
    def _create_regression_alert(self, result: PerformanceTestResult):
        """创建回归告警"""
        regression_type = self._map_metric_to_regression_type(result.metric_name)
        
        alert = RegressionAlert(
            id=f"regression_{int(time.time())}_{result.endpoint}_{result.metric_name}",
            endpoint=result.endpoint,
            method=result.method,
            regression_type=regression_type,
            severity=result.severity,
            current_value=result.current_value,
            baseline_value=result.baseline_value,
            deviation_percent=result.deviation_percent,
            message=self._generate_alert_message(result),
            timestamp=result.timestamp
        )
        
        # 添加到活跃回归
        alert_key = f"{result.method}:{result.endpoint}:{result.metric_name}"
        self.active_regressions[alert_key] = alert
        
        # 添加到历史记录
        self.regression_history.append(alert)
        
        logger.warning(f"🚨 Regression detected: {alert.message}")
    
    def _map_metric_to_regression_type(self, metric_name: str) -> RegressionType:
        """映射指标到回归类型"""
        mapping = {
            "response_time": RegressionType.PERFORMANCE,
            "error_rate": RegressionType.ERROR_RATE,
            "throughput": RegressionType.THROUGHPUT,
            "availability": RegressionType.AVAILABILITY
        }
        return mapping.get(metric_name, RegressionType.PERFORMANCE)
    
    def _generate_alert_message(self, result: PerformanceTestResult) -> str:
        """生成告警消息"""
        direction = "increased" if result.deviation_percent > 0 else "decreased"
        
        return (f"{result.metric_name.replace('_', ' ').title()} {direction} by "
                f"{abs(result.deviation_percent):.1f}% for {result.method} {result.endpoint} "
                f"(current: {result.current_value:.2f}, baseline: {result.baseline_value:.2f})")
    
    def resolve_regression(self, endpoint: str, method: str, metric_name: str):
        """解决回归"""
        alert_key = f"{method}:{endpoint}:{metric_name}"
        
        if alert_key in self.active_regressions:
            alert = self.active_regressions[alert_key]
            alert.resolved = True
            del self.active_regressions[alert_key]
            
            logger.info(f"✅ Regression resolved: {alert.message}")
    
    def get_regression_summary(self) -> Dict[str, Any]:
        """获取回归摘要"""
        active_count = len(self.active_regressions)
        total_count = len(self.regression_history)
        
        severity_counts = defaultdict(int)
        type_counts = defaultdict(int)
        
        for alert in self.regression_history:
            severity_counts[alert.severity.value] += 1
            type_counts[alert.regression_type.value] += 1
        
        return {
            "active_regressions": active_count,
            "total_regressions": total_count,
            "severity_breakdown": dict(severity_counts),
            "type_breakdown": dict(type_counts),
            "recent_regressions": [asdict(alert) for alert in list(self.regression_history)[-10:]]
        }

class PerformanceBenchmarkRunner:
    """性能基准测试运行器"""
    
    def __init__(self, baseline_manager: PerformanceBaselineManager, 
                 regression_detector: PerformanceRegressionDetector):
        self.baseline_manager = baseline_manager
        self.regression_detector = regression_detector
        self.test_endpoints = self._define_test_endpoints()
        
    def _define_test_endpoints(self) -> List[Dict[str, Any]]:
        """定义测试端点"""
        return [
            {
                "path": "/api/v1/chat/quick-chat",
                "method": "POST",
                "metrics": ["response_time", "error_rate", "throughput"],
                "target_response_time": 3000,
                "target_error_rate": 1.0,
                "target_throughput": 10
            },
            {
                "path": "/api/v1/chat/deep-research",
                "method": "POST", 
                "metrics": ["response_time", "error_rate", "throughput"],
                "target_response_time": 60000,
                "target_error_rate": 5.0,
                "target_throughput": 2
            },
            {
                "path": "/api/v1/search/autocomplete",
                "method": "GET",
                "metrics": ["response_time", "error_rate", "throughput"],
                "target_response_time": 500,
                "target_error_rate": 0.5,
                "target_throughput": 50
            },
            {
                "path": "/api/v1/trending/hotspots",
                "method": "GET",
                "metrics": ["response_time", "error_rate", "throughput"],
                "target_response_time": 1000,
                "target_error_rate": 1.0,
                "target_throughput": 20
            }
        ]
    
    async def run_benchmark_test(self, endpoint_config: Dict[str, Any]) -> Dict[str, PerformanceTestResult]:
        """运行基准测试"""
        results = {}
        endpoint = endpoint_config["path"]
        method = endpoint_config["method"]
        
        # 模拟性能测试
        test_results = await self._simulate_performance_test(endpoint_config)
        
        for metric_name, current_value in test_results.items():
            result = self.regression_detector.detect_regression(endpoint, method, metric_name, current_value)
            if result:
                results[metric_name] = result
        
        return results
    
    async def _simulate_performance_test(self, endpoint_config: Dict[str, Any]) -> Dict[str, float]:
        """模拟性能测试"""
        # 模拟不同的性能表现
        base_metrics = {
            "response_time": endpoint_config["target_response_time"],
            "error_rate": endpoint_config["target_error_rate"],
            "throughput": endpoint_config["target_throughput"]
        }
        
        # 添加随机变化
        import random
        random.seed(hash(endpoint_config["path"]))
        
        simulated_metrics = {}
        for metric, base_value in base_metrics.items():
            if metric == "response_time":
                # 响应时间可能增加
                variation = random.uniform(0.8, 1.3)
                simulated_metrics[metric] = base_value * variation
            elif metric == "error_rate":
                # 错误率可能有波动
                variation = random.uniform(0.5, 2.0)
                simulated_metrics[metric] = base_value * variation
            else:
                # 吞吐量可能下降
                variation = random.uniform(0.7, 1.1)
                simulated_metrics[metric] = base_value * variation
        
        # 模拟测试延迟
        await asyncio.sleep(0.1)
        
        return simulated_metrics
    
    async def create_initial_baselines(self):
        """创建初始基准"""
        print("📊 Creating initial performance baselines...")
        
        for endpoint_config in self.test_endpoints:
            endpoint = endpoint_config["path"]
            method = endpoint_config["method"]
            
            # 收集基准数据
            baseline_data = await self._collect_baseline_data(endpoint_config)
            
            # 为每个指标创建基准
            for metric_name, values in baseline_data.items():
                try:
                    self.baseline_manager.create_baseline(endpoint, method, metric_name, values)
                except ValueError as e:
                    logger.error(f"Failed to create baseline for {metric_name}: {e}")
    
    async def _collect_baseline_data(self, endpoint_config: Dict[str, Any]) -> Dict[str, List[float]]:
        """收集基准数据"""
        # 模拟收集30个数据点
        baseline_data = defaultdict(list)
        
        for i in range(30):
            test_results = await self._simulate_performance_test(endpoint_config)
            
            for metric_name, value in test_results.items():
                baseline_data[metric_name].append(value)
            
            await asyncio.sleep(0.05)  # 模拟测试间隔
        
        return dict(baseline_data)
    
    async def run_regression_test_suite(self) -> Dict[str, Any]:
        """运行回归测试套件"""
        print("🧪 Running regression test suite...")
        
        test_results = {}
        regressions_found = []
        
        for endpoint_config in self.test_endpoints:
            endpoint = endpoint_config["path"]
            method = endpoint_config["method"]
            
            print(f"Testing {method} {endpoint}...")
            
            results = await self.run_benchmark_test(endpoint_config)
            test_results[f"{method}:{endpoint}"] = results
            
            # 检查回归
            for metric_name, result in results.items():
                if result.is_regression:
                    regressions_found.append({
                        "endpoint": endpoint,
                        "method": method,
                        "metric": metric_name,
                        "severity": result.severity.value,
                        "deviation": result.deviation_percent
                    })
        
        return {
            "test_results": test_results,
            "regressions_found": regressions_found,
            "summary": self._generate_test_summary(test_results, regressions_found)
        }
    
    def _generate_test_summary(self, test_results: Dict[str, Any], regressions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成测试摘要"""
        total_tests = sum(len(results) for results in test_results.values())
        failed_tests = len(regressions)
        passed_tests = total_tests - failed_tests
        
        severity_counts = defaultdict(int)
        for regression in regressions:
            severity_counts[regression["severity"]] += 1
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "pass_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            "severity_breakdown": dict(severity_counts),
            "test_timestamp": time.time()
        }

class PerformanceTrendAnalyzer:
    """性能趋势分析器"""
    
    def __init__(self, regression_detector: PerformanceRegressionDetector):
        self.regression_detector = regression_detector
        
    def analyze_trends(self, days: int = 7) -> Dict[str, Any]:
        """分析性能趋势"""
        cutoff_time = time.time() - (days * 24 * 3600)
        
        # 获取指定时间范围内的测试结果
        recent_results = []
        for key, results in self.regression_detector.test_history.items():
            recent_results.extend([r for r in results if r.timestamp >= cutoff_time])
        
        if not recent_results:
            return {"trend": "no_data"}
        
        # 按端点和指标分组
        trends = defaultdict(list)
        for result in recent_results:
            trend_key = f"{result.method}:{result.endpoint}:{result.metric_name}"
            trends[trend_key].append(result)
        
        # 分析每个趋势
        trend_analysis = {}
        for trend_key, results in trends.items():
            if len(results) < 3:
                trend_analysis[trend_key] = {"trend": "insufficient_data"}
                continue
            
            analysis = self._analyze_metric_trend(results)
            trend_analysis[trend_key] = analysis
        
        return {
            "trends": trend_analysis,
            "overall_health": self._calculate_overall_health(trend_analysis),
            "analysis_period": f"{days} days",
            "data_points": len(recent_results)
        }
    
    def _analyze_metric_trend(self, results: List[PerformanceTestResult]) -> Dict[str, Any]:
        """分析单个指标趋势"""
        # 按时间排序
        sorted_results = sorted(results, key=lambda x: x.timestamp)
        
        # 计算趋势
        values = [r.current_value for r in sorted_results]
        
        # 简单线性回归分析趋势
        n = len(values)
        x = list(range(n))
        
        # 计算斜率
        x_mean = sum(x) / n
        y_mean = sum(values) / n
        
        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        slope = numerator / denominator if denominator != 0 else 0
        
        # 确定趋势方向
        if abs(slope) < 0.01:
            trend_direction = "stable"
        elif slope > 0:
            # 对于响应时间和错误率，上升是坏的
            metric_name = sorted_results[0].metric_name
            if metric_name in ["response_time", "error_rate"]:
                trend_direction = "degrading"
            else:
                trend_direction = "improving"
        else:
            # 对于响应时间和错误率，下降是好的
            metric_name = sorted_results[0].metric_name
            if metric_name in ["response_time", "error_rate"]:
                trend_direction = "improving"
            else:
                trend_direction = "degrading"
        
        return {
            "trend": trend_direction,
            "slope": slope,
            "current_value": values[-1],
            "average_value": y_mean,
            "volatility": statistics.stdev(values) if len(values) > 1 else 0,
            "sample_count": n
        }
    
    def _calculate_overall_health(self, trend_analysis: Dict[str, Any]) -> str:
        """计算整体健康状态"""
        if not trend_analysis:
            return "unknown"
        
        degrading_count = sum(1 for analysis in trend_analysis.values() 
                            if analysis.get("trend") == "degrading")
        improving_count = sum(1 for analysis in trend_analysis.values() 
                            if analysis.get("trend") == "improving")
        stable_count = sum(1 for analysis in trend_analysis.values() 
                         if analysis.get("trend") == "stable")
        
        total = len(trend_analysis)
        
        if degrading_count / total > 0.3:
            return "critical"
        elif degrading_count / total > 0.1:
            return "warning"
        elif improving_count / total > 0.5:
            return "excellent"
        else:
            return "healthy"

async def main():
    """主函数 - 演示性能基准和回归检测"""
    print("🚀 Starting API Performance Baseline and Regression Detection System...")
    
    # 创建组件
    baseline_manager = PerformanceBaselineManager()
    regression_detector = PerformanceRegressionDetector(baseline_manager)
    benchmark_runner = PerformanceBenchmarkRunner(baseline_manager, regression_detector)
    trend_analyzer = PerformanceTrendAnalyzer(regression_detector)
    
    # 创建初始基准
    await benchmark_runner.create_initial_baselines()
    
    print(f"\n📊 Created {len(baseline_manager.list_baselines())} performance baselines")
    
    # 显示基准信息
    for baseline in baseline_manager.list_baselines():
        print(f"  • {baseline.method} {baseline.endpoint} - {baseline.metric_name}: "
              f"{baseline.baseline_value:.2f} (±{baseline.tolerance_percent}%)")
    
    # 运行回归测试
    print("\n🧪 Running performance regression tests...")
    test_results = await benchmark_runner.run_regression_test_suite()
    
    # 显示测试结果
    summary = test_results["summary"]
    print(f"\n📈 Test Summary:")
    print(f"  Total Tests: {summary['total_tests']}")
    print(f"  Passed: {summary['passed_tests']}")
    print(f"  Failed: {summary['failed_tests']}")
    print(f"  Pass Rate: {summary['pass_rate']:.1f}%")
    
    if test_results["regressions_found"]:
        print(f"\n🚨 Regressions Found:")
        for regression in test_results["regressions_found"]:
            print(f"  • {regression['severity'].upper()}: {regression['method']} {regression['endpoint']} "
                  f"- {regression['metric']} ({regression['deviation']:+.1f}%)")
    else:
        print(f"\n✅ No regressions detected!")
    
    # 获取回归摘要
    regression_summary = regression_detector.get_regression_summary()
    print(f"\n📊 Regression Summary:")
    print(f"  Active Regressions: {regression_summary['active_regressions']}")
    print(f"  Total Regressions: {regression_summary['total_regressions']}")
    
    if regression_summary["severity_breakdown"]:
        print(f"  Severity Breakdown:")
        for severity, count in regression_summary["severity_breakdown"].items():
            print(f"    • {severity}: {count}")
    
    # 分析趋势
    print(f"\n📈 Analyzing performance trends...")
    trend_analysis = trend_analyzer.analyze_trends(days=7)
    
    print(f"  Overall Health: {trend_analysis['overall_health']}")
    print(f"  Data Points: {trend_analysis['data_points']}")
    
    # 显示关键趋势
    critical_trends = {k: v for k, v in trend_analysis["trends"].items() 
                      if v.get("trend") in ["degrading", "improving"]}
    
    if critical_trends:
        print(f"  Key Trends:")
        for trend_key, analysis in list(critical_trends.items())[:5]:
            print(f"    • {trend_key}: {analysis['trend']} "
                  f"(current: {analysis.get('current_value', 0):.2f})")
    
    # 生成完整报告
    performance_report = {
        "baseline_summary": {
            "total_baselines": len(baseline_manager.list_baselines()),
            "created_at": time.time()
        },
        "baselines": [asdict(baseline) for baseline in baseline_manager.list_baselines()],
        "test_results": test_results,
        "regression_summary": regression_summary,
        "trend_analysis": trend_analysis,
        "recommendations": [
            "Monitor response time trends for Quick Chat endpoint",
            "Investigate error rate spikes in Autocomplete service",
            "Set up automated baseline updates weekly",
            "Implement performance gates in CI/CD pipeline",
            "Create alerting for critical regressions"
        ],
        "next_steps": [
            "Schedule regular regression tests",
            "Integrate with deployment pipeline",
            "Set up performance budget monitoring",
            "Create performance dashboards"
        ]
    }
    
    # 保存报告
    with open("performance_baseline_report.json", "w") as f:
        json.dump(performance_report, f, indent=2, default=str)
    
    print(f"\n✅ API Performance Baseline and Regression Detection completed!")
    print("📁 Performance report saved to: performance_baseline_report.json")
    
    return performance_report

if __name__ == "__main__":
    asyncio.run(main())
