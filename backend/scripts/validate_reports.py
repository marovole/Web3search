#!/usr/bin/env python3
"""
报告质量验证脚本
用于验证数据库中的报告或单个 Markdown 文件

用法：
    # 验证数据库中的所有报告
    python scripts/validate_reports.py --all

    # 验证指定 ID 的报告
    python scripts/validate_reports.py --id 123

    # 验证 Markdown 文件
    python scripts/validate_reports.py --file report.md

    # 导出验证报告
    python scripts/validate_reports.py --all --export validation_report.json
"""
import asyncio
import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.report import Report, ReportStatus
from app.services.report.quality_validator import (
    quality_validator,
    validate_markdown_syntax,
    estimate_reading_time
)


# ================================
# 验证函数
# ================================

async def validate_report_by_id(report_id: int) -> Dict[str, Any]:
    """验证指定 ID 的报告"""
    async with AsyncSessionLocal() as db:
        stmt = select(Report).where(Report.id == report_id)
        result = await db.execute(stmt)
        report = result.scalar_one_or_none()

        if not report:
            return {
                "error": f"报告 ID {report_id} 不存在"
            }

        # 执行验证
        score, details = quality_validator.validate_report(
            markdown_content=report.content_markdown or "",
            sections=report.sections,
            data_sources=report.data_sources,
            report_type=report.report_type.value,
            metadata={
                "generation_time_seconds": report.generation_time_seconds
            }
        )

        # Markdown 语法验证
        syntax_result = validate_markdown_syntax(report.content_markdown or "")

        # 阅读时间
        reading_time = estimate_reading_time(report.content_markdown or "")

        return {
            "report_id": report.id,
            "symbol": report.symbol,
            "report_type": report.report_type.value,
            "status": report.status.value,
            "quality_score": score,
            "quality_details": details,
            "markdown_syntax": syntax_result,
            "reading_time_minutes": reading_time,
            "current_score_in_db": report.quality_score,
            "score_needs_update": report.quality_score != score
        }


async def validate_all_reports(limit: int = None) -> List[Dict[str, Any]]:
    """验证所有报告"""
    async with AsyncSessionLocal() as db:
        stmt = select(Report).where(Report.status == ReportStatus.COMPLETED)

        if limit:
            stmt = stmt.limit(limit)

        result = await db.execute(stmt)
        reports = result.scalars().all()

        print(f"📊 找到 {len(reports)} 个已完成的报告，开始验证...\n")

        results = []
        for i, report in enumerate(reports, 1):
            print(f"[{i}/{len(reports)}] 验证报告 ID={report.id} ({report.symbol})...")

            # 执行验证
            score, details = quality_validator.validate_report(
                markdown_content=report.content_markdown or "",
                sections=report.sections,
                data_sources=report.data_sources,
                report_type=report.report_type.value,
                metadata={
                    "generation_time_seconds": report.generation_time_seconds
                }
            )

            results.append({
                "report_id": report.id,
                "symbol": report.symbol,
                "report_type": report.report_type.value,
                "quality_score": score,
                "grade": details["grade"],
                "current_score_in_db": report.quality_score,
                "issues": details["issues"],
                "recommendations": details["recommendations"]
            })

            # 打印简要结果
            print(f"   得分: {score}/100 ({details['grade']}) - "
                  f"{'✅ 优秀' if score >= 85 else '⚠️ 需改进' if score < 70 else '✔️ 良好'}")

        return results


def validate_markdown_file(file_path: str) -> Dict[str, Any]:
    """验证 Markdown 文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()

        # 执行验证
        score, details = quality_validator.validate_report(
            markdown_content=markdown_content,
            data_sources=None,
            report_type="deep_research",
            metadata=None
        )

        # Markdown 语法验证
        syntax_result = validate_markdown_syntax(markdown_content)

        # 阅读时间
        reading_time = estimate_reading_time(markdown_content)

        return {
            "file_path": file_path,
            "quality_score": score,
            "quality_details": details,
            "markdown_syntax": syntax_result,
            "reading_time_minutes": reading_time,
            "word_count": len(markdown_content)
        }

    except FileNotFoundError:
        return {
            "error": f"文件不存在: {file_path}"
        }
    except Exception as e:
        return {
            "error": f"验证文件失败: {str(e)}"
        }


# ================================
# 输出函数
# ================================

def print_validation_result(result: Dict[str, Any]):
    """打印验证结果"""
    if "error" in result:
        print(f"\n❌ 错误: {result['error']}")
        return

    print("\n" + "=" * 80)
    print(f"📊 报告质量验证结果")
    print("=" * 80)

    if "report_id" in result:
        print(f"\n🆔 报告 ID: {result['report_id']}")
        print(f"📈 币种: {result.get('symbol', 'N/A')}")
        print(f"📝 类型: {result['report_type']}")
        print(f"🔄 状态: {result.get('status', 'N/A')}")

    if "file_path" in result:
        print(f"\n📄 文件: {result['file_path']}")
        print(f"📏 字数: {result['word_count']:,}")

    details = result.get("quality_details", {})

    print(f"\n🏆 质量得分: {result['quality_score']}/100 ({details.get('grade', 'N/A')})")

    if "breakdown" in details:
        print(f"\n📋 评分细节:")
        breakdown = details["breakdown"]
        print(f"   - 内容完整性: {breakdown.get('completeness', 0):.1f}/40")
        print(f"   - 数据质量: {breakdown.get('data_quality', 0):.1f}/30")
        print(f"   - 结构规范: {breakdown.get('structure', 0):.1f}/20")
        print(f"   - 内容深度: {breakdown.get('depth', 0):.1f}/10")

    if details.get("issues"):
        print(f"\n⚠️  质量问题:")
        for issue in details["issues"]:
            print(f"   - {issue}")

    if details.get("recommendations"):
        print(f"\n💡 改进建议:")
        for rec in details["recommendations"]:
            print(f"   - {rec}")

    # Markdown 语法
    syntax = result.get("markdown_syntax", {})
    if syntax:
        print(f"\n📝 Markdown 语法: {'✅ 有效' if syntax.get('valid') else '❌ 无效'}")
        if syntax.get("errors"):
            print(f"   错误:")
            for err in syntax["errors"]:
                print(f"   - {err}")
        if syntax.get("warnings"):
            print(f"   警告:")
            for warn in syntax["warnings"]:
                print(f"   - {warn}")

    # 阅读时间
    if "reading_time_minutes" in result:
        print(f"\n⏱️  预估阅读时间: {result['reading_time_minutes']} 分钟")

    # 数据库更新建议
    if result.get("score_needs_update"):
        print(f"\n🔄 数据库得分需要更新:")
        print(f"   当前: {result.get('current_score_in_db')}")
        print(f"   新值: {result['quality_score']}")

    print("\n" + "=" * 80)


def export_validation_results(results: List[Dict[str, Any]], output_file: str):
    """导出验证结果到 JSON"""
    try:
        export_data = {
            "validation_time": datetime.utcnow().isoformat(),
            "total_reports": len(results),
            "results": results,
            "summary": {
                "average_score": sum(r.get("quality_score", 0) for r in results) / len(results) if results else 0,
                "grade_distribution": {},
                "reports_needing_improvement": sum(1 for r in results if r.get("quality_score", 0) < 70)
            }
        }

        # 统计等级分布
        for result in results:
            grade = result.get("quality_details", {}).get("grade", "N/A")
            export_data["summary"]["grade_distribution"][grade] = \
                export_data["summary"]["grade_distribution"].get(grade, 0) + 1

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        print(f"\n✅ 验证结果已导出到: {output_file}")
        print(f"   总报告数: {export_data['total_reports']}")
        print(f"   平均得分: {export_data['summary']['average_score']:.1f}/100")
        print(f"   需改进报告: {export_data['summary']['reports_needing_improvement']}")

    except Exception as e:
        print(f"\n❌ 导出失败: {str(e)}")


# ================================
# 主函数
# ================================

async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="报告质量验证脚本")

    # 验证模式
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true", help="验证所有报告")
    group.add_argument("--id", type=int, help="验证指定 ID 的报告")
    group.add_argument("--file", type=str, help="验证 Markdown 文件")

    # 可选参数
    parser.add_argument("--limit", type=int, help="限制验证报告数量（仅用于 --all）")
    parser.add_argument("--export", type=str, help="导出验证结果到 JSON 文件")

    args = parser.parse_args()

    # 执行验证
    if args.all:
        results = await validate_all_reports(limit=args.limit)

        # 打印摘要
        print("\n" + "=" * 80)
        print(f"📊 验证摘要")
        print("=" * 80)
        print(f"总报告数: {len(results)}")

        if results:
            avg_score = sum(r["quality_score"] for r in results) / len(results)
            print(f"平均得分: {avg_score:.1f}/100")

            grade_dist = {}
            for r in results:
                grade = r["grade"]
                grade_dist[grade] = grade_dist.get(grade, 0) + 1

            print(f"\n等级分布:")
            for grade in ["A", "B", "C", "D", "F"]:
                count = grade_dist.get(grade, 0)
                if count > 0:
                    print(f"   {grade}: {count} 个报告")

            needs_improvement = sum(1 for r in results if r["quality_score"] < 70)
            print(f"\n需改进报告: {needs_improvement}")

        # 导出结果
        if args.export:
            export_validation_results(results, args.export)

    elif args.id:
        result = await validate_report_by_id(args.id)
        print_validation_result(result)

        # 导出结果
        if args.export:
            export_validation_results([result], args.export)

    elif args.file:
        result = validate_markdown_file(args.file)
        print_validation_result(result)

        # 导出结果
        if args.export:
            export_validation_results([result], args.export)


if __name__ == "__main__":
    asyncio.run(main())
