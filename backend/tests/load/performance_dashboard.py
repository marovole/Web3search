"""
性能监控Dashboard
实时显示负载测试性能指标
"""

import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import statistics
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.animation import FuncAnimation
import pandas as pd
import seaborn as sns
from flask import Flask, render_template, jsonify
import plotly.graph_objects as go
import plotly.utils
from collections import deque, defaultdict

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, max_history_points: int = 100):
        self.max_history_points = max_history_points
        self.metrics_history = defaultdict(lambda: deque(maxlen=max_history_points))
        self.alerts = []
        self.is_monitoring = False
        self.monitor_thread = None
        
        # 性能目标
        self.performance_targets = {
            "quick_chat_p95": 3000,  # ms
            "deep_research_p95": 60000,  # ms
            "hotspots_p95": 1000,  # ms
            "autocomplete_p95": 500,  # ms
            "market_data_p95": 800,  # ms
            "error_rate_max": 0.001,  # 0.1%
            "throughput_min": 1000  # rps
        }
        
    def add_metrics(self, timestamp: datetime, metrics: Dict[str, float]):
        """添加性能指标数据"""
        for metric_name, value in metrics.items():
            self.metrics_history[metric_name].append({
                "timestamp": timestamp,
                "value": value
            })
            
        # 检查告警
        self._check_alerts(timestamp, metrics)
        
    def _check_alerts(self, timestamp: datetime, metrics: Dict[str, float]):
        """检查性能告警"""
        for metric_name, value in metrics.items():
            threshold = self.performance_targets.get(metric_name)
            
            if threshold is not None:
                if "response_time" in metric_name or "p95" in metric_name:
                    if value > threshold:
                        alert = {
                            "timestamp": timestamp.isoformat(),
                            "metric": metric_name,
                            "value": value,
                            "threshold": threshold,
                            "severity": "warning" if value < threshold * 1.5 else "critical",
                            "message": f"{metric_name}: {value:.0f}ms exceeds threshold {threshold:.0f}ms"
                        }
                        self.alerts.append(alert)
                        
                elif "error_rate" in metric_name:
                    if value > threshold:
                        alert = {
                            "timestamp": timestamp.isoformat(),
                            "metric": metric_name,
                            "value": value,
                            "threshold": threshold,
                            "severity": "warning" if value < threshold * 2 else "critical",
                            "message": f"{metric_name}: {value*100:.2f}% exceeds threshold {threshold*100:.2f}%"
                        }
                        self.alerts.append(alert)
                        
                elif "throughput" in metric_name:
                    if value < threshold:
                        alert = {
                            "timestamp": timestamp.isoformat(),
                            "metric": metric_name,
                            "value": value,
                            "threshold": threshold,
                            "severity": "warning" if value > threshold * 0.5 else "critical",
                            "message": f"{metric_name}: {value:.0f}rps below threshold {threshold:.0f}rps"
                        }
                        self.alerts.append(alert)
                        
    def get_current_metrics(self) -> Dict[str, Any]:
        """获取当前性能指标"""
        current = {}
        
        for metric_name, history in self.metrics_history.items():
            if history:
                latest = history[-1]
                current[metric_name] = latest["value"]
                
        return current
        
    def get_metrics_summary(self, time_window_minutes: int = 10) -> Dict[str, Any]:
        """获取指定时间窗口内的指标摘要"""
        cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)
        summary = {}
        
        for metric_name, history in self.metrics_history.items():
            recent_data = [
                point["value"] for point in history 
                if point["timestamp"] > cutoff_time
            ]
            
            if recent_data:
                summary[metric_name] = {
                    "current": recent_data[-1],
                    "min": min(recent_data),
                    "max": max(recent_data),
                    "avg": statistics.mean(recent_data),
                    "p50": statistics.median(recent_data),
                    "p95": self._percentile(recent_data, 95),
                    "p99": self._percentile(recent_data, 99),
                    "count": len(recent_data)
                }
                
        return summary
        
    def _percentile(self, data: List[float], percentile: int) -> float:
        """计算百分位数"""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]
        
    def get_recent_alerts(self, count: int = 10) -> List[Dict]:
        """获取最近的告警"""
        return sorted(self.alerts, key=lambda x: x["timestamp"], reverse=True)[:count]
        
    def clear_alerts(self):
        """清除告警历史"""
        self.alerts.clear()

class PerformanceDashboard:
    """性能监控Dashboard"""
    
    def __init__(self, monitor: PerformanceMonitor):
        self.monitor = monitor
        self.app = Flask(__name__)
        self.setup_routes()
        
    def setup_routes(self):
        """设置Flask路由"""
        
        @self.app.route('/')
        def dashboard():
            return render_template('dashboard.html')
            
        @self.app.route('/api/metrics')
        def get_metrics():
            return jsonify(self.monitor.get_current_metrics())
            
        @self.app.route('/api/metrics/summary')
        def get_metrics_summary():
            return jsonify(self.monitor.get_metrics_summary())
            
        @self.app.route('/api/alerts')
        def get_alerts():
            return jsonify(self.monitor.get_recent_alerts())
            
        @self.app.route('/api/charts/<metric_name>')
        def get_chart_data(metric_name):
            history = self.monitor.metrics_history.get(metric_name, [])
            
            data = {
                "timestamps": [point["timestamp"].isoformat() for point in history],
                "values": [point["value"] for point in history]
            }
            
            return jsonify(data)
            
        @self.app.route('/api/performance-overview')
        def get_performance_overview():
            """获取性能概览数据"""
            summary = self.monitor.get_metrics_summary()
            alerts = self.monitor.get_recent_alerts(5)
            
            overview = {
                "timestamp": datetime.now().isoformat(),
                "metrics": summary,
                "alerts": alerts,
                "status": self._get_overall_status(summary, alerts)
            }
            
            return jsonify(overview)
            
    def _get_overall_status(self, summary: Dict, alerts: List[Dict]) -> str:
        """获取整体状态"""
        critical_alerts = [a for a in alerts if a.get("severity") == "critical"]
        warning_alerts = [a for a in alerts if a.get("severity") == "warning"]
        
        if critical_alerts:
            return "critical"
        elif warning_alerts:
            return "warning"
        else:
            return "healthy"
            
    def create_plotly_chart(self, metric_name: str) -> str:
        """创建Plotly图表"""
        history = self.monitor.metrics_history.get(metric_name, [])
        
        if not history:
            return "No data available"
            
        timestamps = [point["timestamp"] for point in history]
        values = [point["value"] for point in history]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=values,
            mode='lines+markers',
            name=metric_name,
            line=dict(width=2)
        ))
        
        # 添加性能目标线
        target = self.monitor.performance_targets.get(metric_name)
        if target:
            fig.add_hline(
                y=target,
                line_dash="dash",
                line_color="red",
                annotation_text=f"Target: {target}"
            )
            
        fig.update_layout(
            title=f"{metric_name} Performance",
            xaxis_title="Time",
            yaxis_title="Value",
            hovermode='x unified'
        )
        
        return fig.to_html(include_plotlyjs='cdn')
        
    def run(self, host: str = '0.0.0.0', port: int = 8080, debug: bool = False):
        """启动Dashboard"""
        print(f"🚀 Performance Dashboard starting on http://{host}:{port}")
        self.app.run(host=host, port=port, debug=debug)

# HTML模板
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Performance Monitoring Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
        .status-healthy { color: #28a745; }
        .status-warning { color: #ffc107; }
        .status-critical { color: #dc3545; }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .metric-card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .metric-value { font-size: 2em; font-weight: bold; color: #333; }
        .metric-label { color: #666; margin-bottom: 10px; }
        .chart-container { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .alerts-container { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .alert { padding: 10px; margin: 5px 0; border-radius: 5px; }
        .alert-warning { background-color: #fff3cd; border: 1px solid #ffeaa7; }
        .alert-critical { background-color: #f8d7da; border: 1px solid #f5c6cb; }
        .refresh-btn { background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; }
        .refresh-btn:hover { background: #0056b3; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 Performance Monitoring Dashboard</h1>
        <p>Real-time performance metrics for Web3 Search API</p>
        <p>Status: <span id="overall-status" class="status-healthy">Healthy</span></p>
        <p>Last updated: <span id="last-updated">--</span></p>
        <button class="refresh-btn" onclick="refreshData()">Refresh</button>
    </div>

    <div class="metrics-grid" id="metrics-grid">
        <!-- Metrics cards will be populated here -->
    </div>

    <div class="chart-container">
        <h2>Response Time Trends</h2>
        <canvas id="responseTimeChart"></canvas>
    </div>

    <div class="chart-container">
        <h2>Throughput Trends</h2>
        <canvas id="throughputChart"></canvas>
    </div>

    <div class="alerts-container">
        <h2>Recent Alerts</h2>
        <div id="alerts-list">
            <!-- Alerts will be populated here -->
        </div>
    </div>

    <script>
        let responseTimeChart, throughputChart;

        async function refreshData() {
            try {
                // 获取性能概览
                const overview = await fetch('/api/performance-overview').then(r => r.json());
                
                // 更新状态
                updateStatus(overview.status);
                updateLastUpdated();
                
                // 更新指标卡片
                updateMetricsCards(overview.metrics);
                
                // 更新图表
                await updateCharts();
                
                // 更新告警
                updateAlerts(overview.alerts);
                
            } catch (error) {
                console.error('Error refreshing data:', error);
            }
        }

        function updateStatus(status) {
            const statusElement = document.getElementById('overall-status');
            statusElement.textContent = status.charAt(0).toUpperCase() + status.slice(1);
            statusElement.className = `status-${status}`;
        }

        function updateLastUpdated() {
            document.getElementById('last-updated').textContent = new Date().toLocaleString();
        }

        function updateMetricsCards(metrics) {
            const grid = document.getElementById('metrics-grid');
            grid.innerHTML = '';

            const importantMetrics = [
                { key: 'quick_chat_p95', label: 'Quick Chat P95', unit: 'ms' },
                { key: 'deep_research_p95', label: 'Deep Research P95', unit: 'ms' },
                { key: 'hotspots_p95', label: 'Hotspots P95', unit: 'ms' },
                { key: 'error_rate', label: 'Error Rate', unit: '%' },
                { key: 'throughput', label: 'Throughput', unit: 'rps' }
            ];

            importantMetrics.forEach(metric => {
                const value = metrics[metric.key]?.current || 0;
                const displayValue = metric.unit === '%' ? (value * 100).toFixed(2) : Math.round(value);
                
                const card = document.createElement('div');
                card.className = 'metric-card';
                card.innerHTML = `
                    <div class="metric-label">${metric.label}</div>
                    <div class="metric-value">${displayValue} ${metric.unit}</div>
                `;
                grid.appendChild(card);
            });
        }

        async function updateCharts() {
            // 更新响应时间图表
            const quickChatData = await fetch('/api/charts/quick_chat_p95').then(r => r.json());
            updateResponseTimeChart(quickChatData);

            // 更新吞吐量图表
            const throughputData = await fetch('/api/charts/throughput').then(r => r.json());
            updateThroughputChart(throughputData);
        }

        function updateResponseTimeChart(data) {
            const ctx = document.getElementById('responseTimeChart').getContext('2d');
            
            if (responseTimeChart) {
                responseTimeChart.destroy();
            }

            responseTimeChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.timestamps.map(t => new Date(t).toLocaleTimeString()),
                    datasets: [{
                        label: 'Quick Chat P95 Response Time',
                        data: data.values,
                        borderColor: 'rgb(75, 192, 192)',
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Response Time (ms)'
                            }
                        }
                    }
                }
            });
        }

        function updateThroughputChart(data) {
            const ctx = document.getElementById('throughputChart').getContext('2d');
            
            if (throughputChart) {
                throughputChart.destroy();
            }

            throughputChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.timestamps.map(t => new Date(t).toLocaleTimeString()),
                    datasets: [{
                        label: 'Throughput (RPS)',
                        data: data.values,
                        borderColor: 'rgb(255, 99, 132)',
                        backgroundColor: 'rgba(255, 99, 132, 0.2)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Requests Per Second'
                            }
                        }
                    }
                }
            });
        }

        function updateAlerts(alerts) {
            const alertsList = document.getElementById('alerts-list');
            alertsList.innerHTML = '';

            if (alerts.length === 0) {
                alertsList.innerHTML = '<p>No recent alerts</p>';
                return;
            }

            alerts.forEach(alert => {
                const alertDiv = document.createElement('div');
                alertDiv.className = `alert alert-${alert.severity}`;
                alertDiv.innerHTML = `
                    <strong>${alert.severity.toUpperCase()}</strong> - ${alert.message}
                    <br><small>${new Date(alert.timestamp).toLocaleString()}</small>
                `;
                alertsList.appendChild(alertDiv);
            });
        }

        // 自动刷新数据
        setInterval(refreshData, 10000); // 每10秒刷新一次
        
        // 初始加载
        refreshData();
    </script>
</body>
</html>
"""

def create_dashboard_template():
    """创建Dashboard HTML模板"""
    templates_dir = "templates"
    os.makedirs(templates_dir, exist_ok=True)
    
    with open(f"{templates_dir}/dashboard.html", "w") as f:
        f.write(DASHBOARD_TEMPLATE)
        
    print("✅ Dashboard template created")

if __name__ == "__main__":
    import os
    
    # 创建监控器
    monitor = PerformanceMonitor()
    
    # 创建Dashboard
    dashboard = PerformanceDashboard(monitor)
    
    # 创建模板文件
    create_dashboard_template()
    
    # 模拟添加一些测试数据
    now = datetime.now()
    for i in range(50):
        timestamp = now - timedelta(minutes=i)
        monitor.add_metrics(timestamp, {
            "quick_chat_p95": 2000 + random.randint(-500, 1000),
            "deep_research_p95": 45000 + random.randint(-10000, 15000),
            "hotspots_p95": 800 + random.randint(-200, 400),
            "error_rate": random.uniform(0, 0.005),
            "throughput": 1000 + random.randint(-200, 300)
        })
    
    print("🚀 Starting Performance Dashboard...")
    print("📊 Dashboard will be available at: http://localhost:8080")
    print("🔄 Auto-refresh enabled (10 seconds)")
    
    # 启动Dashboard
    dashboard.run(debug=True)
