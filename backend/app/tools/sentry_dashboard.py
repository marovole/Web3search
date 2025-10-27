"""
Sentry Dashboard配置生成工具（任务 13.4）

功能：生成Sentry Dashboard的JSON配置
用法：python -m app.tools.sentry_dashboard
"""
import json
from typing import Dict, Any, List


def generate_dashboard_config() -> Dict[str, Any]:
    """
    生成Sentry Dashboard配置

    Returns:
        Dict[str, Any]: Dashboard JSON配置
    """
    dashboard = {
        "title": "Web3 Search API - 监控Dashboard",
        "description": "Web3加密货币AI搜索引擎核心指标监控",
        "widgets": [
            # 错误率指标
            {
                "title": "错误率（Last 24h）",
                "displayType": "big_number",
                "interval": "5m",
                "queries": [
                    {
                        "name": "Error Rate",
                        "fields": ["equation|failure_rate()"],
                        "conditions": "!event.type:transaction",
                        "orderby": "-equation|failure_rate()",
                    }
                ],
            },
            # API响应时间
            {
                "title": "API响应时间（P95）",
                "displayType": "line",
                "interval": "5m",
                "queries": [
                    {
                        "name": "P95 Response Time",
                        "fields": ["p95(transaction.duration)"],
                        "conditions": "event.type:transaction",
                        "orderby": "-p95(transaction.duration)",
                    }
                ],
            },
            # Quick Chat性能
            {
                "title": "Quick Chat响应时间",
                "displayType": "line",
                "interval": "5m",
                "queries": [
                    {
                        "name": "Quick Chat P95",
                        "fields": ["p95(transaction.duration)"],
                        "conditions": 'event.type:transaction transaction:"/api/v1/chat/quick-chat"',
                        "orderby": "-p95(transaction.duration)",
                    }
                ],
            },
            # Deep Research性能
            {
                "title": "Deep Research响应时间",
                "displayType": "line",
                "interval": "5m",
                "queries": [
                    {
                        "name": "Deep Research P95",
                        "fields": ["p95(transaction.duration)"],
                        "conditions": 'event.type:transaction transaction:"deep_research"',
                        "orderby": "-p95(transaction.duration)",
                    }
                ],
            },
            # 错误类型分布
            {
                "title": "错误类型分布（Top 10）",
                "displayType": "table",
                "interval": "5m",
                "queries": [
                    {
                        "name": "Error Types",
                        "fields": ["error.type", "count()"],
                        "conditions": "!event.type:transaction",
                        "orderby": "-count()",
                        "limit": 10,
                    }
                ],
            },
            # 数据源成功率
            {
                "title": "数据源成功率",
                "displayType": "table",
                "interval": "5m",
                "queries": [
                    {
                        "name": "Data Source Success Rate",
                        "fields": ["tags[source]", "equation|success_rate()"],
                        "conditions": 'event.type:transaction transaction:"data_collection"',
                        "orderby": "-equation|success_rate()",
                    }
                ],
            },
            # LLM调用统计
            {
                "title": "LLM调用次数",
                "displayType": "line",
                "interval": "5m",
                "queries": [
                    {
                        "name": "LLM Calls",
                        "fields": ["count()"],
                        "conditions": 'event.type:transaction transaction:"llm_call"',
                        "orderby": "-count()",
                    }
                ],
            },
            # Token消耗
            {
                "title": "Token消耗（每小时）",
                "displayType": "line",
                "interval": "1h",
                "queries": [
                    {
                        "name": "Total Tokens",
                        "fields": ["sum(measurements.llm_tokens)"],
                        "conditions": 'event.type:transaction has:measurements.llm_tokens',
                        "orderby": "-sum(measurements.llm_tokens)",
                    }
                ],
            },
            # 请求量
            {
                "title": "请求量（RPS）",
                "displayType": "line",
                "interval": "1m",
                "queries": [
                    {
                        "name": "Requests Per Second",
                        "fields": ["eps()"],
                        "conditions": "event.type:transaction",
                        "orderby": "-eps()",
                    }
                ],
            },
            # 用户分布（按endpoint）
            {
                "title": "端点使用分布",
                "displayType": "bar",
                "interval": "5m",
                "queries": [
                    {
                        "name": "Endpoint Distribution",
                        "fields": ["transaction", "count()"],
                        "conditions": "event.type:transaction",
                        "orderby": "-count()",
                        "limit": 10,
                    }
                ],
            },
        ],
        "projects": [-1],  # 所有项目
        "environment": ["production", "staging"],
        "period": "24h",
    }

    return dashboard


def generate_key_metrics_dashboard() -> Dict[str, Any]:
    """
    生成关键指标Dashboard（精简版）

    Returns:
        Dict[str, Any]: 精简Dashboard配置
    """
    dashboard = {
        "title": "Web3 Search - 关键指标",
        "description": "核心业务指标总览",
        "widgets": [
            # 可用性（Uptime）
            {
                "title": "服务可用性（24h）",
                "displayType": "big_number",
                "queries": [
                    {
                        "name": "Uptime",
                        "fields": ["equation|1 - failure_rate()"],
                        "conditions": "event.type:transaction",
                    }
                ],
            },
            # P95延迟
            {
                "title": "P95延迟（ms）",
                "displayType": "big_number",
                "queries": [
                    {
                        "name": "P95 Latency",
                        "fields": ["p95(transaction.duration)"],
                        "conditions": "event.type:transaction",
                    }
                ],
            },
            # 错误率
            {
                "title": "错误率（%）",
                "displayType": "big_number",
                "queries": [
                    {
                        "name": "Error Rate",
                        "fields": ["equation|failure_rate() * 100"],
                        "conditions": "!event.type:transaction",
                    }
                ],
            },
            # 总请求数
            {
                "title": "总请求数（24h）",
                "displayType": "big_number",
                "queries": [
                    {
                        "name": "Total Requests",
                        "fields": ["count()"],
                        "conditions": "event.type:transaction",
                    }
                ],
            },
        ],
        "projects": [-1],
        "environment": ["production"],
        "period": "24h",
    }

    return dashboard


def save_dashboards():
    """保存Dashboard配置到JSON文件"""
    # 完整Dashboard
    full_dashboard = generate_dashboard_config()
    with open("sentry_dashboard_full.json", "w", encoding="utf-8") as f:
        json.dump(full_dashboard, f, indent=2, ensure_ascii=False)
    print("✅ 完整Dashboard配置已保存: sentry_dashboard_full.json")

    # 关键指标Dashboard
    key_metrics_dashboard = generate_key_metrics_dashboard()
    with open("sentry_dashboard_key_metrics.json", "w", encoding="utf-8") as f:
        json.dump(key_metrics_dashboard, f, indent=2, ensure_ascii=False)
    print("✅ 关键指标Dashboard配置已保存: sentry_dashboard_key_metrics.json")

    # 使用说明
    print("\n📖 使用说明:")
    print("1. 登录Sentry控制台")
    print("2. 进入项目 → Dashboards")
    print("3. 点击 'Create Dashboard'")
    print("4. 点击右上角 '...' → 'Import from JSON'")
    print("5. 复制JSON文件内容并粘贴")
    print("6. 保存Dashboard")


if __name__ == "__main__":
    print("🚀 生成Sentry Dashboard配置...\n")
    save_dashboards()
    print("\n✅ 完成!")
