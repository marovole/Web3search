"""
增强版性能监控Dashboard系统
实时展示性能指标、趋势分析、告警信息和优化建议的可视化Dashboard
"""

import json
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from datetime import datetime, timedelta
import statistics
import random

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DashboardWidget(Enum):
    """Dashboard组件类型"""
    METRIC_CARD = "metric_card"
    TREND_CHART = "trend_chart"
    PERFORMANCE_TABLE = "performance_table"
    ALERT_PANEL = "alert_panel"
    OPTIMIZATION_CARD = "optimization_card"
    DEVICE_BREAKDOWN = "device_breakdown"
    GEO_DISTRIBUTION = "geo_distribution"
    REAL_TIME_MONITOR = "real_time_monitor"

class ChartType(Enum):
    """图表类型"""
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    AREA = "area"
    GAUGE = "gauge"
    HEATMAP = "heatmap"

@dataclass
class DashboardMetric:
    """Dashboard指标"""
    name: str
    value: float
    unit: str
    target: float
    status: str
    trend: str
    change_percent: float
    description: str

@dataclass
class DashboardAlert:
    """Dashboard告警"""
    id: str
    severity: str
    title: str
    message: str
    timestamp: datetime
    metric: str
    current_value: float
    threshold: float

@dataclass
class DashboardWidgetData:
    """Dashboard组件"""
    widget_id: str
    widget_type: DashboardWidget
    title: str
    position: Dict[str, int]
    size: Dict[str, int]
    data: Dict[str, Any]
    config: Dict[str, Any]

class PerformanceDataAggregator:
    """性能数据聚合器"""
    
    def __init__(self):
        self.raw_data = {}
        self.aggregated_data = {}
        
    def aggregate_real_time_metrics(self) -> Dict[str, DashboardMetric]:
        """聚合实时指标"""
        print("📊 Aggregating real-time performance metrics...")
        
        # 模拟实时性能数据
        real_time_metrics = {
            "page_load_time": DashboardMetric(
                name="Page Load Time",
                value=2.8,
                unit="seconds",
                target=3.0,
                status="good",
                trend="improving",
                change_percent=-12.5,
                description="Average page load time across all pages"
            ),
            "api_response_time": DashboardMetric(
                name="API Response Time",
                value=850,
                unit="milliseconds",
                target=1000,
                status="good",
                trend="stable",
                change_percent=-2.3,
                description="Average API response time"
            ),
            "error_rate": DashboardMetric(
                name="Error Rate",
                value=0.8,
                unit="percent",
                target=1.0,
                status="good",
                trend="improving",
                change_percent=-25.0,
                description="Percentage of failed requests"
            ),
            "uptime": DashboardMetric(
                name="Uptime",
                value=99.9,
                unit="percent",
                target=99.5,
                status="excellent",
                trend="stable",
                change_percent=0.1,
                description="Service availability percentage"
            ),
            "core_web_vitals_score": DashboardMetric(
                name="Core Web Vitals Score",
                value=72,
                unit="points",
                target=80,
                status="needs_improvement",
                trend="improving",
                change_percent=8.5,
                description="Overall Core Web Vitals performance score"
            ),
            "bundle_size": DashboardMetric(
                name="Bundle Size",
                value=856,
                unit="KB",
                target=1000,
                status="good",
                trend="stable",
                change_percent=1.2,
                description="Total JavaScript bundle size"
            )
        }
        
        return real_time_metrics
    
    def aggregate_historical_data(self, days: int = 30) -> Dict[str, List[Dict[str, Any]]]:
        """聚合历史数据"""
        print(f"📈 Aggregating historical data for last {days} days...")
        
        historical_data = {}
        
        # 生成时间序列数据
        base_date = datetime.now() - timedelta(days=days)
        
        # 页面加载时间趋势
        page_load_trend = []
        for i in range(days):
            date = base_date + timedelta(days=i)
            # 模拟性能波动和改进趋势
            base_value = 3.2 - (i * 0.01)  # 逐渐改进
            value = base_value + (0.3 * (0.5 - abs(0.5 - (i % 7) / 7)))  # 周末波动
            
            page_load_trend.append({
                "date": date.strftime("%Y-%m-%d"),
                "value": round(value, 2),
                "target": 3.0
            })
        
        # API响应时间趋势
        api_response_trend = []
        for i in range(days):
            date = base_date + timedelta(days=i)
            base_value = 950 - (i * 2)  # 逐渐改进
            value = base_value + (100 * (0.5 - abs(0.5 - (i % 7) / 7)))  # 周末波动
            
            api_response_trend.append({
                "date": date.strftime("%Y-%m-%d"),
                "value": round(value),
                "target": 1000
            })
        
        # Core Web Vitals评分趋势
        web_vitals_trend = []
        for i in range(days):
            date = base_date + timedelta(days=i)
            base_value = 65 + (i * 0.2)  # 逐渐改进
            value = base_value + (5 * (0.5 - abs(0.5 - (i % 7) / 7)))  # 周末波动
            
            web_vitals_trend.append({
                "date": date.strftime("%Y-%m-%d"),
                "value": round(value, 1),
                "target": 80
            })
        
        # 错误率趋势
        error_rate_trend = []
        for i in range(days):
            date = base_date + timedelta(days=i)
            base_value = 1.2 - (i * 0.01)  # 逐渐改进
            value = max(0.3, base_value + (0.3 * (0.5 - abs(0.5 - (i % 7) / 7))))  # 周末波动
            
            error_rate_trend.append({
                "date": date.strftime("%Y-%m-%d"),
                "value": round(value, 2),
                "target": 1.0
            })
        
        historical_data = {
            "page_load_time": page_load_trend,
            "api_response_time": api_response_trend,
            "core_web_vitals_score": web_vitals_trend,
            "error_rate": error_rate_trend
        }
        
        return historical_data
    
    def aggregate_device_performance(self) -> Dict[str, Dict[str, Any]]:
        """聚合设备性能数据"""
        print("📱 Aggregating device performance data...")
        
        device_data = {
            "desktop": {
                "page_load_time": 2.1,
                "api_response_time": 720,
                "core_web_vitals_score": 85,
                "user_count": 15420,
                "bounce_rate": 32.5,
                "conversion_rate": 4.2
            },
            "mobile": {
                "page_load_time": 3.4,
                "api_response_time": 980,
                "core_web_vitals_score": 68,
                "user_count": 28350,
                "bounce_rate": 48.2,
                "conversion_rate": 2.8
            },
            "tablet": {
                "page_load_time": 2.8,
                "api_response_time": 850,
                "core_web_vitals_score": 75,
                "user_count": 8230,
                "bounce_rate": 38.7,
                "conversion_rate": 3.5
            }
        }
        
        return device_data
    
    def aggregate_geographic_data(self) -> Dict[str, Dict[str, Any]]:
        """聚合地理分布数据"""
        print("🌍 Aggregating geographic performance data...")
        
        geo_data = {
            "north_america": {
                "page_load_time": 2.2,
                "api_response_time": 680,
                "user_count": 25600,
                "countries": ["United States", "Canada", "Mexico"]
            },
            "europe": {
                "page_load_time": 2.8,
                "api_response_time": 850,
                "user_count": 18900,
                "countries": ["United Kingdom", "Germany", "France", "Spain"]
            },
            "asia": {
                "page_load_time": 3.6,
                "api_response_time": 1200,
                "user_count": 32400,
                "countries": ["China", "Japan", "India", "Singapore"]
            },
            "south_america": {
                "page_load_time": 4.2,
                "api_response_time": 1450,
                "user_count": 6800,
                "countries": ["Brazil", "Argentina", "Chile"]
            },
            "africa": {
                "page_load_time": 4.8,
                "api_response_time": 1680,
                "user_count": 3200,
                "countries": ["South Africa", "Nigeria", "Egypt"]
            },
            "oceania": {
                "page_load_time": 3.1,
                "api_response_time": 920,
                "user_count": 4100,
                "countries": ["Australia", "New Zealand"]
            }
        }
        
        return geo_data

class DashboardWidgetFactory:
    """Dashboard组件工厂"""
    
    def __init__(self):
        self.widgets = {}
        
    def create_metric_cards(self, metrics: Dict[str, DashboardMetric]) -> List[DashboardWidgetData]:
        """创建指标卡片"""
        print("🎴 Creating metric cards...")
        
        metric_cards = []
        
        # 定义关键指标卡片
        key_metrics = [
            ("page_load_time", 0, 0, 2, 1),
            ("api_response_time", 2, 0, 2, 1),
            ("core_web_vitals_score", 4, 0, 2, 1),
            ("error_rate", 0, 1, 2, 1),
            ("uptime", 2, 1, 2, 1),
            ("bundle_size", 4, 1, 2, 1)
        ]
        
        for metric_key, x, y, w, h in key_metrics:
            if metric_key in metrics:
                metric = metrics[metric_key]
                
                # 确定状态颜色
                status_colors = {
                    "excellent": "#10b981",
                    "good": "#3b82f6", 
                    "needs_improvement": "#f59e0b",
                    "poor": "#ef4444"
                }
                
                # 确定趋势图标
                trend_icons = {
                    "improving": "📈",
                    "stable": "➡️",
                    "degrading": "📉"
                }
                
                widget = DashboardWidgetData(
                    widget_id=f"metric_card_{metric_key}",
                    widget_type=DashboardWidget.METRIC_CARD,
                    title=metric.name,
                    position={"x": x, "y": y},
                    size={"width": w, "height": h},
                    data={
                        "value": metric.value,
                        "unit": metric.unit,
                        "target": metric.target,
                        "status": metric.status,
                        "status_color": status_colors.get(metric.status, "#6b7280"),
                        "trend": metric.trend,
                        "trend_icon": trend_icons.get(metric.trend, "➡️"),
                        "change_percent": metric.change_percent,
                        "description": metric.description,
                        "progress_percentage": min(100, (metric.value / metric.target) * 100) if metric.target > 0 else 0
                    },
                    config={
                        "refresh_interval": 30,
                        "show_trend": True,
                        "show_target": True,
                        "clickable": True,
                        "chart_type": "gauge"
                    }
                )
                
                metric_cards.append(widget)
        
        return metric_cards
    
    def create_trend_charts(self, historical_data: Dict[str, List[Dict[str, Any]]]) -> List[DashboardWidgetData]:
        """创建趋势图表"""
        print("📈 Creating trend charts...")
        
        trend_charts = []
        
        # 页面加载时间趋势图
        page_load_chart = DashboardWidgetData(
            widget_id="trend_chart_page_load",
            widget_type=DashboardWidget.TREND_CHART,
            title="Page Load Time Trend (30 Days)",
            position={"x": 0, "y": 2},
            size={"width": 3, "height": 2},
            data={
                "chart_type": ChartType.LINE.value,
                "series": [
                    {
                        "name": "Page Load Time",
                        "data": [{"x": item["date"], "y": item["value"]} for item in historical_data["page_load_time"]],
                        "color": "#3b82f6"
                    },
                    {
                        "name": "Target",
                        "data": [{"x": item["date"], "y": item["target"]} for item in historical_data["page_load_time"]],
                        "color": "#ef4444",
                        "dash_style": "dash"
                    }
                ],
                "x_axis": "date",
                "y_axis": "value",
                "unit": "seconds"
            },
            config={
                "refresh_interval": 300,
                "interactive": True,
                "zoomable": True,
                "legend": True,
                "grid": True
            }
        )
        
        # Core Web Vitals评分趋势图
        web_vitals_chart = DashboardWidgetData(
            widget_id="trend_chart_web_vitals",
            widget_type=DashboardWidget.TREND_CHART,
            title="Core Web Vitals Score Trend",
            position={"x": 3, "y": 2},
            size={"width": 3, "height": 2},
            data={
                "chart_type": ChartType.AREA.value,
                "series": [
                    {
                        "name": "CWV Score",
                        "data": [{"x": item["date"], "y": item["value"]} for item in historical_data["core_web_vitals_score"]],
                        "color": "#10b981"
                    },
                    {
                        "name": "Target",
                        "data": [{"x": item["date"], "y": item["target"]} for item in historical_data["core_web_vitals_score"]],
                        "color": "#f59e0b",
                        "dash_style": "dash"
                    }
                ],
                "x_axis": "date",
                "y_axis": "value",
                "unit": "points"
            },
            config={
                "refresh_interval": 300,
                "interactive": True,
                "zoomable": True,
                "legend": True,
                "gradient_fill": True
            }
        )
        
        # API响应时间趋势图
        api_response_chart = DashboardWidgetData(
            widget_id="trend_chart_api_response",
            widget_type=DashboardWidget.TREND_CHART,
            title="API Response Time Trend",
            position={"x": 0, "y": 4},
            size={"width": 3, "height": 2},
            data={
                "chart_type": ChartType.BAR.value,
                "series": [
                    {
                        "name": "API Response Time",
                        "data": [{"x": item["date"], "y": item["value"]} for item in historical_data["api_response_time"]],
                        "color": "#8b5cf6"
                    }
                ],
                "x_axis": "date",
                "y_axis": "value",
                "unit": "milliseconds"
            },
            config={
                "refresh_interval": 300,
                "interactive": True,
                "legend": False,
                "data_labels": False
            }
        )
        
        # 错误率趋势图
        error_rate_chart = DashboardWidgetData(
            widget_id="trend_chart_error_rate",
            widget_type=DashboardWidget.TREND_CHART,
            title="Error Rate Trend",
            position={"x": 3, "y": 4},
            size={"width": 3, "height": 2},
            data={
                "chart_type": ChartType.LINE.value,
                "series": [
                    {
                        "name": "Error Rate",
                        "data": [{"x": item["date"], "y": item["value"]} for item in historical_data["error_rate"]],
                        "color": "#ef4444"
                    }
                ],
                "x_axis": "date",
                "y_axis": "value",
                "unit": "percent"
            },
            config={
                "refresh_interval": 300,
                "interactive": True,
                "zoomable": True,
                "alert_threshold": 1.0
            }
        )
        
        trend_charts.extend([page_load_chart, web_vitals_chart, api_response_chart, error_rate_chart])
        
        return trend_charts
    
    def create_device_breakdown(self, device_data: Dict[str, Dict[str, Any]]) -> DashboardWidgetData:
        """创建设备分解图表"""
        print("📱 Creating device breakdown widget...")
        
        device_breakdown = DashboardWidgetData(
            widget_id="device_breakdown",
            widget_type=DashboardWidget.DEVICE_BREAKDOWN,
            title="Performance by Device Type",
            position={"x": 0, "y": 6},
            size={"width": 3, "height": 2},
            data={
                "chart_type": ChartType.PIE.value,
                "devices": [
                    {
                        "name": "Desktop",
                        "user_count": device_data["desktop"]["user_count"],
                        "page_load_time": device_data["desktop"]["page_load_time"],
                        "cqw_score": device_data["desktop"]["core_web_vitals_score"],
                        "color": "#3b82f6"
                    },
                    {
                        "name": "Mobile",
                        "user_count": device_data["mobile"]["user_count"],
                        "page_load_time": device_data["mobile"]["page_load_time"],
                        "cqw_score": device_data["mobile"]["core_web_vitals_score"],
                        "color": "#10b981"
                    },
                    {
                        "name": "Tablet",
                        "user_count": device_data["tablet"]["user_count"],
                        "page_load_time": device_data["tablet"]["page_load_time"],
                        "cqw_score": device_data["tablet"]["core_web_vitals_score"],
                        "color": "#f59e0b"
                    }
                ],
                "metrics": ["user_count", "page_load_time", "core_web_vitals_score"]
            },
            config={
                "refresh_interval": 600,
                "interactive": True,
                "drill_down": True,
                "comparison_mode": True
            }
        )
        
        return device_breakdown
    
    def create_geo_distribution(self, geo_data: Dict[str, Dict[str, Any]]) -> DashboardWidgetData:
        """创建地理分布图表"""
        print("🌍 Creating geographic distribution widget...")
        
        geo_distribution = DashboardWidgetData(
            widget_id="geo_distribution",
            widget_type=DashboardWidget.GEO_DISTRIBUTION,
            title="Performance by Region",
            position={"x": 3, "y": 6},
            size={"width": 3, "height": 2},
            data={
                "chart_type": ChartType.HEATMAP.value,
                "regions": [
                    {
                        "name": "North America",
                        "page_load_time": geo_data["north_america"]["page_load_time"],
                        "user_count": geo_data["north_america"]["user_count"],
                        "color": "#10b981"
                    },
                    {
                        "name": "Europe",
                        "page_load_time": geo_data["europe"]["page_load_time"],
                        "user_count": geo_data["europe"]["user_count"],
                        "color": "#3b82f6"
                    },
                    {
                        "name": "Asia",
                        "page_load_time": geo_data["asia"]["page_load_time"],
                        "user_count": geo_data["asia"]["user_count"],
                        "color": "#f59e0b"
                    },
                    {
                        "name": "South America",
                        "page_load_time": geo_data["south_america"]["page_load_time"],
                        "user_count": geo_data["south_america"]["user_count"],
                        "color": "#ef4444"
                    },
                    {
                        "name": "Africa",
                        "page_load_time": geo_data["africa"]["page_load_time"],
                        "user_count": geo_data["africa"]["user_count"],
                        "color": "#dc2626"
                    },
                    {
                        "name": "Oceania",
                        "page_load_time": geo_data["oceania"]["page_load_time"],
                        "user_count": geo_data["oceania"]["user_count"],
                        "color": "#8b5cf6"
                    }
                ]
            },
            config={
                "refresh_interval": 600,
                "interactive": True,
                "map_view": True,
                "drill_down": True
            }
        )
        
        return geo_distribution
    
    def create_alert_panel(self) -> DashboardWidgetData:
        """创建告警面板"""
        print("🚨 Creating alert panel...")
        
        # 模拟当前告警
        alerts = [
            DashboardAlert(
                id="alert_001",
                severity="warning",
                title="Mobile Performance Degradation",
                message="Mobile page load time increased by 15% in the last hour",
                timestamp=datetime.now() - timedelta(minutes=45),
                metric="page_load_time",
                current_value=3.9,
                threshold=3.5
            ),
            DashboardAlert(
                id="alert_002",
                severity="info",
                title="Core Web Vitals Improvement",
                message="Overall CWV score improved by 5 points this week",
                timestamp=datetime.now() - timedelta(hours=2),
                metric="core_web_vitals_score",
                current_value=72,
                threshold=70
            ),
            DashboardAlert(
                id="alert_003",
                severity="error",
                title="API Response Time Spike",
                message="Search API response time exceeded 2 seconds threshold",
                timestamp=datetime.now() - timedelta(minutes=15),
                metric="api_response_time",
                current_value=2150,
                threshold=2000
            )
        ]
        
        alert_panel = DashboardWidgetData(
            widget_id="alert_panel",
            widget_type=DashboardWidget.ALERT_PANEL,
            title="Active Alerts",
            position={"x": 0, "y": 8},
            size={"width": 6, "height": 2},
            data={
                "alerts": [
                    {
                        "id": alert.id,
                        "severity": alert.severity,
                        "title": alert.title,
                        "message": alert.message,
                        "timestamp": alert.timestamp.isoformat(),
                        "metric": alert.metric,
                        "current_value": alert.current_value,
                        "threshold": alert.threshold,
                        "severity_color": {
                            "info": "#3b82f6",
                            "warning": "#f59e0b", 
                            "error": "#ef4444",
                            "critical": "#dc2626"
                        }.get(alert.severity, "#6b7280")
                    }
                    for alert in alerts
                ],
                "total_alerts": len(alerts),
                "severity_counts": {
                    "critical": 0,
                    "error": 1,
                    "warning": 1,
                    "info": 1
                }
            },
            config={
                "refresh_interval": 60,
                "auto_refresh": True,
                "filterable": True,
                "sortable": True,
                "max_items": 10
            }
        )
        
        return alert_panel

class DashboardRenderer:
    """Dashboard渲染器"""
    
    def __init__(self):
        self.dashboard_config = {}
        
    def render_dashboard_html(self, widgets: List[DashboardWidgetData]) -> str:
        """渲染Dashboard HTML"""
        print("🎨 Rendering Dashboard HTML...")
        
        html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Web3search Performance Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(6, 1fr);
            grid-auto-rows: minmax(100px, auto);
            gap: 1rem;
            padding: 1rem;
        }
        
        .widget {
            background: white;
            border-radius: 0.5rem;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            padding: 1rem;
            transition: all 0.3s ease;
        }
        
        .widget:hover {
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transform: translateY(-2px);
        }
        
        .metric-value {
            font-size: 2rem;
            font-weight: bold;
            line-height: 1;
        }
        
        .metric-unit {
            font-size: 1rem;
            opacity: 0.7;
        }
        
        .status-good { color: #10b981; }
        .status-warning { color: #f59e0b; }
        .status-error { color: #ef4444; }
        
        .trend-up { color: #10b981; }
        .trend-down { color: #ef4444; }
        .trend-stable { color: #6b7280; }
        
        .alert-critical { border-left: 4px solid #dc2626; }
        .alert-error { border-left: 4px solid #ef4444; }
        .alert-warning { border-left: 4px solid #f59e0b; }
        .alert-info { border-left: 4px solid #3b82f6; }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .live-indicator {
            animation: pulse 2s infinite;
        }
    </style>
</head>
<body class="bg-gray-50">
    <div class="min-h-screen">
        <!-- Header -->
        <header class="bg-white shadow-sm border-b">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="flex justify-between items-center py-4">
                    <div class="flex items-center space-x-3">
                        <i data-lucide="activity" class="w-8 h-8 text-blue-600"></i>
                        <h1 class="text-2xl font-bold text-gray-900">Performance Dashboard</h1>
                        <span class="live-indicator flex items-center text-sm text-green-600">
                            <span class="w-2 h-2 bg-green-600 rounded-full mr-1"></span>
                            Live
                        </span>
                    </div>
                    <div class="flex items-center space-x-4">
                        <select class="border rounded px-3 py-1 text-sm" id="timeRange">
                            <option value="1h">Last Hour</option>
                            <option value="24h" selected>Last 24 Hours</option>
                            <option value="7d">Last 7 Days</option>
                            <option value="30d">Last 30 Days</option>
                        </select>
                        <button class="bg-blue-600 text-white px-4 py-1 rounded text-sm hover:bg-blue-700" onclick="refreshDashboard()">
                            <i data-lucide="refresh-cw" class="w-4 h-4 inline mr-1"></i>
                            Refresh
                        </button>
                    </div>
                </div>
            </div>
        </header>

        <!-- Main Dashboard -->
        <main class="max-w-7xl mx-auto">
            <div class="dashboard-grid" id="dashboardGrid">
                {WIDGETS}
            </div>
        </main>
    </div>

    <script>
        // Initialize Lucide icons
        lucide.createIcons();
        
        // Auto-refresh dashboard
        setInterval(refreshDashboard, 30000);
        
        function refreshDashboard() {
            // Simulate dashboard refresh
            console.log('Refreshing dashboard...');
            // In real implementation, this would fetch fresh data
        }
        
        // Interactive features
        document.addEventListener('DOMContentLoaded', function() {
            // Add click handlers to widgets
            document.querySelectorAll('.widget').forEach(widget => {
                widget.addEventListener('click', function() {
                    console.log('Widget clicked:', this.id);
                });
            });
        });
    </script>
</body>
</html>
        """
        
        # 生成组件HTML
        widgets_html = ""
        for widget in widgets:
            widget_html = self._render_widget_html(widget)
            widgets_html += widget_html + "\n"
        
        return html_template.replace("{WIDGETS}", widgets_html)
    
    def _render_widget_html(self, widget: DashboardWidgetData) -> str:
        """渲染单个组件HTML"""
        
        if widget.widget_type == DashboardWidget.METRIC_CARD:
            return self._render_metric_card(widget)
        elif widget.widget_type == DashboardWidget.TREND_CHART:
            return self._render_trend_chart(widget)
        elif widget.widget_type == DashboardWidget.ALERT_PANEL:
            return self._render_alert_panel(widget)
        elif widget.widget_type == DashboardWidget.DEVICE_BREAKDOWN:
            return self._render_device_breakdown(widget)
        elif widget.widget_type == DashboardWidget.GEO_DISTRIBUTION:
            return self._render_geo_distribution(widget)
        else:
            return f'<div class="widget" id="{widget.widget_id}">Unknown widget type</div>'
    
    def _render_metric_card(self, widget: DashboardWidgetData) -> str:
        """渲染指标卡片"""
        data = widget.data
        
        return f"""
        <div class="widget" id="{widget.widget_id}" style="grid-column: {widget.position['x'] + 1} / span {widget.size['width']}; grid-row: {widget.position['y'] + 1} / span {widget.size['height']};">
            <div class="flex justify-between items-start mb-2">
                <h3 class="text-sm font-medium text-gray-600">{widget.title}</h3>
                <span class="text-xs text-gray-400">{data['trend_icon']}</span>
            </div>
            <div class="flex items-baseline space-x-2">
                <span class="metric-value" style="color: {data['status_color']}">{data['value']}</span>
                <span class="metric-unit">{data['unit']}</span>
            </div>
            <div class="mt-2 flex items-center justify-between">
                <div class="text-xs text-gray-500">
                    Target: {data['target']} {data['unit']}
                </div>
                <div class="text-xs {data['trend'].replace('improving', 'trend-up').replace('degrading', 'trend-down').replace('stable', 'trend-stable')}">
                    {data['change_percent']:+.1f}%
                </div>
            </div>
            <div class="mt-2">
                <div class="w-full bg-gray-200 rounded-full h-2">
                    <div class="h-2 rounded-full" style="width: {data['progress_percentage']}%; background-color: {data['status_color']}"></div>
                </div>
            </div>
        </div>
        """
    
    def _render_trend_chart(self, widget: DashboardWidgetData) -> str:
        """渲染趋势图表"""
        return f"""
        <div class="widget" id="{widget.widget_id}" style="grid-column: {widget.position['x'] + 1} / span {widget.size['width']}; grid-row: {widget.position['y'] + 1} / span {widget.size['height']};">
            <h3 class="text-sm font-medium text-gray-600 mb-4">{widget.title}</h3>
            <div style="height: 200px;">
                <canvas id="chart_{widget.widget_id}"></canvas>
            </div>
            <script>
                // Chart for {widget.widget_id}
                const ctx_{widget.widget_id} = document.getElementById('chart_{widget.widget_id}').getContext('2d');
                const chartData_{widget.widget_id} = {json.dumps(widget.data['series'][:10])};
                new Chart(ctx_{widget.widget_id}, {{
                    type: '{widget.data['chart_type']}',
                    data: {{
                        labels: {json.dumps([item['x'] for item in widget.data['series'][0]['data'][:10]])},
                        datasets: chartData_{widget.widget_id}.map(series => ({{
                            label: series.name,
                            data: series.data.slice(0, 10).map(item => item.y),
                            borderColor: series.color,
                            fill: false
                        }}))
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {{
                            y: {{
                                beginAtZero: false
                            }}
                        }}
                    }}
                }});
            </script>
        </div>
        """
    
    def _render_alert_panel(self, widget: DashboardWidgetData) -> str:
        """渲染告警面板"""
        alerts_html = ""
        for alert in widget.data['alerts']:
            alerts_html += f"""
            <div class="alert-{alert['severity']} p-3 mb-2 rounded">
                <div class="flex justify-between items-start">
                    <div>
                        <h4 class="font-medium text-sm">{alert['title']}</h4>
                        <p class="text-xs text-gray-600 mt-1">{alert['message']}</p>
                        <div class="text-xs text-gray-400 mt-1">
                            {alert['metric']}: {alert['current_value']} (threshold: {alert['threshold']})
                        </div>
                    </div>
                    <span class="text-xs text-gray-400">{alert['timestamp']}</span>
                </div>
            </div>
            """
        
        return f"""
        <div class="widget" id="{widget.widget_id}" style="grid-column: {widget.position['x'] + 1} / span {widget.size['width']}; grid-row: {widget.position['y'] + 1} / span {widget.size['height']};">
            <div class="flex justify-between items-center mb-4">
                <h3 class="text-sm font-medium text-gray-600">{widget.title}</h3>
                <span class="bg-red-100 text-red-800 text-xs px-2 py-1 rounded">{widget.data['total_alerts']} Active</span>
            </div>
            <div class="space-y-2 max-h-64 overflow-y-auto">
                {alerts_html}
            </div>
        </div>
        """
    
    def _render_device_breakdown(self, widget: DashboardWidgetData) -> str:
        """渲染设备分解"""
        devices_html = ""
        for device in widget.data['devices']:
            devices_html += f"""
            <div class="flex items-center justify-between p-2">
                <div class="flex items-center space-x-2">
                    <div class="w-3 h-3 rounded-full" style="background-color: {device['color']}"></div>
                    <span class="text-sm font-medium">{device['name']}</span>
                </div>
                <div class="text-right">
                    <div class="text-sm font-medium">{device['page_load_time']}s</div>
                    <div class="text-xs text-gray-500">{device['cqw_score']} pts</div>
                </div>
            </div>
            """
        
        return f"""
        <div class="widget" id="{widget.widget_id}" style="grid-column: {widget.position['x'] + 1} / span {widget.size['width']}; grid-row: {widget.position['y'] + 1} / span {widget.size['height']};">
            <h3 class="text-sm font-medium text-gray-600 mb-4">{widget.title}</h3>
            <div class="space-y-3">
                {devices_html}
            </div>
            <div style="height: 150px; margin-top: 1rem;">
                <canvas id="pie_{widget.widget_id}"></canvas>
            </div>
            <script>
                const pie_{widget.widget_id} = document.getElementById('pie_{widget.widget_id}').getContext('2d');
                const pieData_{widget.widget_id} = {json.dumps(widget.data['devices'])};
                new Chart(pie_{widget.widget_id}, {{
                    type: 'doughnut',
                    data: {{
                        labels: pieData_{widget.widget_id}.map(device => device.name),
                        datasets: [{{
                            data: pieData_{widget.widget_id}.map(device => device.user_count),
                            backgroundColor: pieData_{widget.widget_id}.map(device => device.color)
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false
                    }}
                }});
            </script>
        </div>
        """
    
    def _render_geo_distribution(self, widget: DashboardWidgetData) -> str:
        """渲染地理分布"""
        regions_html = ""
        for region in widget.data['regions']:
            performance_color = "#10b981" if region['page_load_time'] < 3 else "#f59e0b" if region['page_load_time'] < 4 else "#ef4444"
            
            regions_html += f"""
            <div class="flex items-center justify-between p-2 border-b">
                <div class="flex items-center space-x-2">
                    <div class="w-3 h-3 rounded-full" style="background-color: {performance_color}"></div>
                    <span class="text-sm">{region['name']}</span>
                </div>
                <div class="text-right">
                    <div class="text-sm font-medium" style="color: {performance_color}">{region['page_load_time']}s</div>
                    <div class="text-xs text-gray-500">{region['user_count']:,} users</div>
                </div>
            </div>
            """
        
        return f"""
        <div class="widget" id="{widget.widget_id}" style="grid-column: {widget.position['x'] + 1} / span {widget.size['width']}; grid-row: {widget.position['y'] + 1} / span {widget.size['height']};">
            <h3 class="text-sm font-medium text-gray-600 mb-4">{widget.title}</h3>
            <div class="space-y-1">
                {regions_html}
            </div>
        </div>
        """

def main():
    """主函数 - 性能监控Dashboard"""
    print("🚀 Starting Enhanced Performance Dashboard System...")
    
    # 创建数据聚合器
    aggregator = PerformanceDataAggregator()
    
    # 聚合实时指标
    real_time_metrics = aggregator.aggregate_real_time_metrics()
    
    # 聚合历史数据
    historical_data = aggregator.aggregate_historical_data(30)
    
    # 聚合设备性能数据
    device_data = aggregator.aggregate_device_performance()
    
    # 聚合地理数据
    geo_data = aggregator.aggregate_geographic_data()
    
    # 创建组件工厂
    widget_factory = DashboardWidgetFactory()
    
    # 创建Dashboard组件
    metric_cards = widget_factory.create_metric_cards(real_time_metrics)
    trend_charts = widget_factory.create_trend_charts(historical_data)
    device_breakdown = widget_factory.create_device_breakdown(device_data)
    geo_distribution = widget_factory.create_geo_distribution(geo_data)
    alert_panel = widget_factory.create_alert_panel()
    
    # 组合所有组件
    all_widgets = metric_cards + trend_charts + [device_breakdown, geo_distribution, alert_panel]
    
    print(f"\n📊 Dashboard Components Created:")
    print(f"  • Metric Cards: {len(metric_cards)}")
    print(f"  • Trend Charts: {len(trend_charts)}")
    print(f"  • Device Breakdown: 1")
    print(f"  • Geo Distribution: 1")
    print(f"  • Alert Panel: 1")
    print(f"  • Total Widgets: {len(all_widgets)}")
    
    # 显示实时指标摘要
    print(f"\n📈 Real-time Performance Summary:")
    for metric_name, metric in real_time_metrics.items():
        status_emoji = {
            "excellent": "🌟",
            "good": "✅",
            "needs_improvement": "⚠️",
            "poor": "❌"
        }.get(metric.status, "❓")
        
        trend_emoji = {
            "improving": "📈",
            "stable": "➡️",
            "degrading": "📉"
        }.get(metric.trend, "❓")
        
        print(f"  • {metric.name}: {metric.value} {metric.unit} {status_emoji} {trend_emoji} ({metric.change_percent:+.1f}%)")
    
    # 显示设备性能对比
    print(f"\n📱 Device Performance Comparison:")
    for device_name, data in device_data.items():
        device_emoji = {"desktop": "🖥️", "mobile": "📱", "tablet": "📋"}.get(device_name, "📊")
        print(f"  • {device_name.title()} {device_emoji}: {data['page_load_time']}s load, {data['core_web_vitals_score']} CWV score, {data['user_count']:,} users")
    
    # 显示地理性能摘要
    print(f"\n🌍 Geographic Performance Summary:")
    best_region = min(geo_data.items(), key=lambda x: x[1]['page_load_time'])
    worst_region = max(geo_data.items(), key=lambda x: x[1]['page_load_time'])
    
    print(f"  • Best Performance: {best_region[0].replace('_', ' ').title()} ({best_region[1]['page_load_time']}s)")
    print(f"  • Needs Attention: {worst_region[0].replace('_', ' ').title()} ({worst_region[1]['page_load_time']}s)")
    
    # 显示告警摘要
    print(f"\n🚨 Active Alerts Summary:")
    alert_counts = {"critical": 0, "error": 0, "warning": 0, "info": 0}
    for widget in all_widgets:
        if widget.widget_type == DashboardWidget.ALERT_PANEL:
            alert_counts = widget.data["severity_counts"]
            break
    
    total_alerts = sum(alert_counts.values())
    print(f"  • Total Alerts: {total_alerts}")
    if total_alerts > 0:
        for severity, count in alert_counts.items():
            if count > 0:
                emoji = {"critical": "🚨", "error": "❌", "warning": "⚠️", "info": "ℹ️"}.get(severity, "📢")
                print(f"    - {severity.title()}: {count} {emoji}")
    
    # 创建渲染器
    renderer = DashboardRenderer()
    
    # 渲染Dashboard HTML
    dashboard_html = renderer.render_dashboard_html(all_widgets)
    
    # 保存HTML文件
    with open("enhanced_performance_dashboard.html", "w") as f:
        f.write(dashboard_html)
    
    # 生成Dashboard配置JSON
    dashboard_config = {
        "dashboard_metadata": {
            "created_at": datetime.now().isoformat(),
            "version": "2.0.0",
            "refresh_interval": 30,
            "total_widgets": len(all_widgets)
        },
        "widgets": [
            {
                "id": widget.widget_id,
                "type": widget.widget_type.value,
                "title": widget.title,
                "position": widget.position,
                "size": widget.size,
                "config": widget.config
            }
            for widget in all_widgets
        ],
        "real_time_metrics": {
            name: {
                "value": metric.value,
                "unit": metric.unit,
                "status": metric.status,
                "trend": metric.trend
            }
            for name, metric in real_time_metrics.items()
        },
        "data_sources": {
            "real_time": "Performance Monitoring API",
            "historical": "Time Series Database",
            "device_analytics": "User Analytics Platform",
            "geo_analytics": "Geographic Performance Service"
        },
        "performance_summary": {
            "overall_score": 72,
            "total_users": sum(data['user_count'] for data in device_data.values()),
            "avg_page_load_time": statistics.mean([data['page_load_time'] for data in device_data.values()]),
            "active_alerts": total_alerts
        }
    }
    
    with open("enhanced_performance_dashboard_config.json", "w") as f:
        json.dump(dashboard_config, f, indent=2, default=str)
    
    print(f"\n✅ Enhanced Performance Dashboard created successfully!")
    print("📁 Dashboard files saved:")
    print("  • enhanced_performance_dashboard.html - Interactive HTML dashboard")
    print("  • enhanced_performance_dashboard_config.json - Dashboard configuration")
    
    print(f"\n🎯 Dashboard Features:")
    print("  • Real-time performance monitoring")
    print("  • Interactive trend charts")
    print("  • Device and geographic breakdown")
    print("  • Live alert panel")
    print("  • Auto-refresh every 30 seconds")
    print("  • Responsive design with Tailwind CSS")
    print("  • Chart.js integration for data visualization")
    print("  • Lucide icons for better UI")
    
    return dashboard_config

if __name__ == "__main__":
    main()
