#!/usr/bin/env python3
"""
数据库性能分析脚本

用于分析数据库性能、索引使用情况、生成优化建议

Usage:
    python scripts/analyze_db_performance.py [--format json|text] [--output file.json]
"""
import asyncio
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import check_database_health, get_pool_stats
from app.core.db_middleware import performance_collector
from app.core.index_analyzer import analyze_database_indexes


async def analyze_performance() -> dict:
    """
    执行完整的数据库性能分析

    Returns:
        性能分析报告
    """
    print("🔍 正在分析数据库性能...\n")

    # 1. 数据库健康检查
    print("1️⃣  检查数据库健康状态...")
    health_data = await check_database_health()

    # 2. 连接池统计
    print("2️⃣  收集连接池统计...")
    pool_stats = get_pool_stats()

    # 3. 查询性能统计
    print("3️⃣  分析查询性能...")
    query_stats = performance_collector.get_stats()

    # 4. 索引分析
    print("4️⃣  分析索引使用情况...")
    index_report = await analyze_database_indexes()

    # 生成综合报告
    report = {
        "timestamp": datetime.now().isoformat(),
        "database_health": health_data,
        "connection_pool": pool_stats,
        "query_performance": query_stats,
        "index_analysis": index_report,
        "overall_score": calculate_overall_score(
            health_data,
            pool_stats,
            query_stats,
            index_report
        ),
    }

    return report


def calculate_overall_score(
    health_data: dict,
    pool_stats: dict,
    query_stats: dict,
    index_report: dict
) -> dict:
    """
    计算数据库整体健康评分

    Args:
        health_data: 健康检查数据
        pool_stats: 连接池统计
        query_stats: 查询性能统计
        index_report: 索引分析报告

    Returns:
        评分结果（0-100分）
    """
    score = 100
    issues = []

    # 健康状态（-30分）
    if health_data["status"] != "healthy":
        score -= 30
        issues.append("数据库连接不健康")
    elif health_data.get("latency_ms", 0) > 100:
        score -= 10
        issues.append(f"数据库延迟过高: {health_data['latency_ms']}ms")

    # 连接池使用率（-20分）
    if pool_stats.get("checked_out", 0) > pool_stats.get("pool_size", 10) * 0.8:
        score -= 20
        issues.append("连接池使用率过高（>80%）")

    # 慢查询率（-25分）
    slow_query_rate = query_stats.get("slow_query_rate", 0)
    if slow_query_rate > 0.1:
        score -= 25
        issues.append(f"慢查询率过高: {slow_query_rate * 100:.1f}%")
    elif slow_query_rate > 0.05:
        score -= 10
        issues.append(f"慢查询率偏高: {slow_query_rate * 100:.1f}%")

    # 索引问题（-25分）
    unused_count = index_report["summary"]["total_unused_indexes"]
    duplicate_count = index_report["summary"]["total_duplicate_indexes"]

    if unused_count > 5:
        score -= 15
        issues.append(f"未使用索引过多: {unused_count}个")
    elif unused_count > 0:
        score -= 5
        issues.append(f"存在未使用索引: {unused_count}个")

    if duplicate_count > 0:
        score -= 10
        issues.append(f"存在重复索引: {duplicate_count}对")

    # 确保分数不低于0
    score = max(0, score)

    # 评级
    if score >= 90:
        grade = "优秀"
        status = "excellent"
    elif score >= 75:
        grade = "良好"
        status = "good"
    elif score >= 60:
        grade = "一般"
        status = "fair"
    else:
        grade = "需要改进"
        status = "poor"

    return {
        "score": score,
        "grade": grade,
        "status": status,
        "issues": issues,
    }


def print_text_report(report: dict):
    """
    以文本格式打印报告

    Args:
        report: 性能分析报告
    """
    print("\n" + "=" * 80)
    print("📊 数据库性能分析报告".center(80))
    print("=" * 80)

    print(f"\n生成时间: {report['timestamp']}")

    # 整体评分
    overall = report["overall_score"]
    print(f"\n🎯 整体评分: {overall['score']}/100 ({overall['grade']})")

    if overall["issues"]:
        print("\n⚠️  发现的问题:")
        for i, issue in enumerate(overall["issues"], 1):
            print(f"   {i}. {issue}")

    # 数据库健康
    health = report["database_health"]
    print(f"\n💊 数据库健康: {health['status']}")
    if "latency_ms" in health:
        print(f"   延迟: {health['latency_ms']}ms")

    # 连接池
    pool = report["connection_pool"]
    print(f"\n🔌 连接池状态:")
    print(f"   总连接数: {pool.get('total_size', 0)}")
    print(f"   活跃连接: {pool.get('checked_out', 0)}")
    print(f"   空闲连接: {pool.get('checked_in', 0)}")
    if pool.get('pool_size', 0) > 0:
        usage_rate = pool.get('checked_out', 0) / pool.get('pool_size', 1) * 100
        print(f"   使用率: {usage_rate:.1f}%")

    # 查询性能
    query = report["query_performance"]
    print(f"\n⚡ 查询性能:")
    print(f"   总查询数: {query.get('total_queries', 0)}")
    print(f"   慢查询数: {query.get('slow_queries', 0)}")
    print(f"   慢查询率: {query.get('slow_query_rate', 0) * 100:.2f}%")
    print(f"   平均查询时间: {query.get('avg_query_time', 0):.4f}s")

    # 索引分析
    index = report["index_analysis"]
    print(f"\n📑 索引分析:")
    print(f"   未使用索引: {index['summary']['total_unused_indexes']}个")
    print(f"   重复索引: {index['summary']['total_duplicate_indexes']}对")
    print(f"   需要优化的表: {index['summary']['tables_need_indexes']}个")

    if index["recommendations"]:
        print("\n💡 优化建议:")
        for i, rec in enumerate(index["recommendations"], 1):
            priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(
                rec["priority"], "⚪"
            )
            print(f"   {priority_emoji} {rec['message']}")

    # 详细的未使用索引
    if index["unused_indexes"]:
        print("\n🗑️  未使用的索引（详细）:")
        for idx in index["unused_indexes"][:10]:  # 只显示前10个
            print(f"   - {idx['table']}.{idx['index_name']}")
            print(f"     扫描次数: {idx['idx_scan']}, 大小: {idx['size_mb']:.2f}MB")

    print("\n" + "=" * 80)


def print_json_report(report: dict):
    """
    以JSON格式打印报告

    Args:
        report: 性能分析报告
    """
    print(json.dumps(report, indent=2, ensure_ascii=False))


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="数据库性能分析工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 输出文本报告
  python scripts/analyze_db_performance.py

  # 输出JSON报告
  python scripts/analyze_db_performance.py --format json

  # 保存报告到文件
  python scripts/analyze_db_performance.py --format json --output report.json
        """
    )

    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="输出格式（默认: text）"
    )

    parser.add_argument(
        "--output",
        "-o",
        help="输出文件路径（如果不指定则输出到stdout）"
    )

    args = parser.parse_args()

    try:
        # 执行分析
        report = await analyze_performance()

        # 输出报告
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                if args.format == "json":
                    json.dump(report, f, indent=2, ensure_ascii=False)
                else:
                    # 重定向stdout到文件
                    import contextlib
                    with contextlib.redirect_stdout(f):
                        print_text_report(report)
            print(f"\n✅ 报告已保存到: {args.output}")
        else:
            # 输出到控制台
            if args.format == "json":
                print_json_report(report)
            else:
                print_text_report(report)

        # 根据评分决定退出码
        score = report["overall_score"]["score"]
        if score < 60:
            sys.exit(1)  # 评分过低，返回非零退出码
        else:
            sys.exit(0)

    except Exception as e:
        print(f"\n❌ 分析失败: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(2)


if __name__ == "__main__":
    asyncio.run(main())
