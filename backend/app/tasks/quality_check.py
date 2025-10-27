"""
数据质量检查任务（任务6.7）

定时生成数据质量报告
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from celery import Task
from sqlalchemy import select, desc

from app.tasks.celery_app import celery_app
from app.core.database import get_db_session
from app.models import ProjectSnapshot, DataQualityReport
from app.core.data_validator import data_validator
from app.core.data_quality import data_quality_metrics

logger = logging.getLogger(__name__)


# ================================
# 辅助函数：运行异步任务
# ================================


def run_async(coro):
    """在Celery任务中运行异步协程"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


# ================================
# 任务6.7: 数据质量报告生成任务
# ================================


@celery_app.task(
    name="app.tasks.quality_check.generate_data_quality_report",
    bind=True,
    max_retries=3,
)
def generate_data_quality_report(self: Task):
    """
    生成数据质量报告（任务6.7）

    每小时执行一次，对最近的项目快照进行质量检查

    流程：
    1. 查询最近 1 小时的所有项目快照
    2. 对每个快照执行所有验证检查（6.1-6.5）
    3. 计算数据质量指标（6.6）
    4. 保存到 DataQualityReport 表
    5. 如果质量得分 < 0.7，发送 Sentry 告警
    """
    try:
        logger.info("🔄 开始生成数据质量报告...")

        # 获取数据库会话
        session = run_async(get_db_session())

        # 查询最近1小时的快照
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)

        # 查询最近的项目快照（每个项目取最新的一条）
        stmt = (
            select(ProjectSnapshot)
            .where(ProjectSnapshot.timestamp >= one_hour_ago)
            .order_by(ProjectSnapshot.project_id, desc(ProjectSnapshot.timestamp))
        )

        result = run_async(session.execute(stmt))
        snapshots = result.scalars().all()

        if not snapshots:
            logger.info("⚠️ 没有找到最近1小时的快照数据")
            run_async(session.close())
            return {
                "status": "skipped",
                "reason": "no_recent_snapshots",
            }

        # 去重：每个项目只保留最新的快照
        latest_snapshots = {}
        for snapshot in snapshots:
            project_id = snapshot.project_id
            if project_id not in latest_snapshots:
                latest_snapshots[project_id] = snapshot

        snapshots = list(latest_snapshots.values())
        logger.info(f"📊 找到 {len(snapshots)} 个项目的最新快照")

        # 对每个快照进行质量检查
        quality_reports = []

        for snapshot in snapshots:
            try:
                report = check_snapshot_quality(snapshot, session)
                quality_reports.append(report)
            except Exception as e:
                logger.error(
                    f"❌ 质量检查失败",
                    extra={"project_id": snapshot.project_id, "error": str(e)},
                )
                continue

        if not quality_reports:
            logger.warning("⚠️ 没有生成任何质量报告")
            run_async(session.close())
            return {
                "status": "failed",
                "reason": "no_reports_generated",
            }

        # 计算汇总统计
        summary = data_quality_metrics.analyze_batch_quality(quality_reports)

        # 统计告警
        anomaly_counts = count_anomalies(quality_reports)

        # 统计质量等级分布
        quality_distribution = summary.get("quality_distribution", {})

        # 创建数据质量报告记录
        db_report = DataQualityReport(
            timestamp=datetime.utcnow(),
            total_projects_checked=summary["total_count"],
            avg_completeness=summary["avg_metrics"]["completeness"],
            avg_accuracy=summary["avg_metrics"]["accuracy"],
            avg_timeliness=summary["avg_metrics"]["timeliness"],
            avg_overall_score=summary["avg_metrics"]["overall_score"],
            # 告警统计
            price_anomalies_count=anomaly_counts["price_anomalies"],
            market_cap_inconsistencies_count=anomaly_counts["market_cap_inconsistencies"],
            stale_data_count=anomaly_counts["stale_data"],
            incomplete_data_count=anomaly_counts["incomplete_data"],
            zscore_anomalies_count=anomaly_counts["zscore_anomalies"],
            total_warnings=summary["total_issues"]["warnings"],
            total_errors=summary["total_issues"]["errors"],
            total_critical=summary["total_issues"]["critical"],
            # 质量等级分布
            excellent_count=quality_distribution.get("excellent", 0),
            good_count=quality_distribution.get("good", 0),
            fair_count=quality_distribution.get("fair", 0),
            poor_count=quality_distribution.get("poor", 0),
            # 详细结果
            detailed_results={"reports": quality_reports},
            summary=summary,
        )

        # 保存到数据库
        session.add(db_report)
        run_async(session.commit())
        run_async(session.close())

        logger.info(
            f"✅ 数据质量报告已生成",
            extra={
                "total_projects": summary["total_count"],
                "avg_score": summary["avg_metrics"]["overall_score"],
                "total_warnings": summary["total_issues"]["warnings"],
            },
        )

        # 如果平均质量得分低于 0.7，发送 Sentry 告警
        if summary["avg_metrics"]["overall_score"] < 0.7:
            send_quality_alert(db_report, summary)

        return {
            "status": "success",
            "total_projects": summary["total_count"],
            "avg_overall_score": summary["avg_metrics"]["overall_score"],
            "report_id": db_report.id,
        }

    except Exception as e:
        logger.error(f"❌ 数据质量报告生成失败: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=300)  # 5分钟后重试


# ================================
# 辅助函数
# ================================


def check_snapshot_quality(snapshot: ProjectSnapshot, session) -> Dict[str, Any]:
    """
    对单个快照执行质量检查

    Args:
        snapshot: 项目快照
        session: 数据库会话

    Returns:
        Dict: 质量报告
    """
    # 构建快照数据字典
    snapshot_data = {
        "symbol": snapshot.project.symbol if snapshot.project else "Unknown",
        "timestamp": snapshot.timestamp.isoformat(),
        "market_data": {
            "current": {
                "price_usd": snapshot.price_usd,
                "market_cap": snapshot.market_cap,
                "circulating_supply": snapshot.circulating_supply,
                "total_supply": snapshot.total_supply,
                "total_volume_24h": snapshot.total_volume_24h,
                "price_change_24h": snapshot.price_change_24h,
                "price_change_7d": snapshot.price_change_7d,
            }
        },
        "onchain_data": snapshot.raw_onchain_data or {},
        "social_data": snapshot.raw_social_data or {},
    }

    # 查询上一次快照（用于价格合理性检查）
    previous_snapshot_stmt = (
        select(ProjectSnapshot)
        .where(
            ProjectSnapshot.project_id == snapshot.project_id,
            ProjectSnapshot.timestamp < snapshot.timestamp,
        )
        .order_by(desc(ProjectSnapshot.timestamp))
        .limit(1)
    )

    result = run_async(session.execute(previous_snapshot_stmt))
    previous_snapshot = result.scalar_one_or_none()

    previous_snapshot_data = None
    if previous_snapshot:
        previous_snapshot_data = {
            "market_data": {
                "current": {
                    "price_usd": previous_snapshot.price_usd,
                }
            }
        }

    # 查询历史数据（用于Z-score检测）
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    historical_stmt = (
        select(ProjectSnapshot.price_usd, ProjectSnapshot.total_volume_24h)
        .where(
            ProjectSnapshot.project_id == snapshot.project_id,
            ProjectSnapshot.timestamp >= seven_days_ago,
            ProjectSnapshot.timestamp < snapshot.timestamp,
        )
        .order_by(ProjectSnapshot.timestamp)
    )

    result = run_async(session.execute(historical_stmt))
    historical_rows = result.all()

    historical_data = {
        "price": [row[0] for row in historical_rows if row[0] is not None],
        "volume": [row[1] for row in historical_rows if row[1] is not None],
    }

    # 执行所有验证检查
    validation_results = data_validator.validate_project_snapshot(
        current_snapshot=snapshot_data,
        previous_snapshot=previous_snapshot_data,
        historical_data=historical_data if historical_data["price"] else None,
    )

    # 计算质量指标
    quality_report = data_quality_metrics.analyze_snapshot_quality(
        snapshot_data=snapshot_data,
        validation_results=validation_results,
    )

    return quality_report


def count_anomalies(quality_reports: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    统计各类异常数量

    Args:
        quality_reports: 质量报告列表

    Returns:
        Dict: 异常计数
    """
    counts = {
        "price_anomalies": 0,
        "market_cap_inconsistencies": 0,
        "stale_data": 0,
        "incomplete_data": 0,
        "zscore_anomalies": 0,
    }

    for report in quality_reports:
        for result in report["validation_results"]:
            if not result["valid"]:
                check_name = result["check_name"]
                if "price_reasonability" in check_name:
                    counts["price_anomalies"] += 1
                elif "market_cap_consistency" in check_name:
                    counts["market_cap_inconsistencies"] += 1
                elif "social_data_freshness" in check_name:
                    counts["stale_data"] += 1
                elif "onchain_data_completeness" in check_name:
                    counts["incomplete_data"] += 1
                elif "anomaly_detection" in check_name:
                    counts["zscore_anomalies"] += 1

    return counts


def send_quality_alert(report: DataQualityReport, summary: Dict[str, Any]):
    """
    发送数据质量告警到Sentry

    Args:
        report: 数据质量报告
        summary: 汇总统计
    """
    try:
        import sentry_sdk

        sentry_sdk.capture_message(
            f"数据质量告警：平均质量得分过低 ({summary['avg_metrics']['overall_score']:.2f})",
            level="warning",
            tags={
                "report_id": str(report.id),
                "total_projects": str(summary["total_count"]),
                "avg_completeness": f"{summary['avg_metrics']['completeness']:.2f}",
                "avg_accuracy": f"{summary['avg_metrics']['accuracy']:.2f}",
                "avg_timeliness": f"{summary['avg_metrics']['timeliness']:.2f}",
            },
        )

        logger.warning(
            f"⚠️ 数据质量告警已发送到Sentry",
            extra={"avg_score": summary["avg_metrics"]["overall_score"]},
        )

    except ImportError:
        logger.debug("Sentry未安装，跳过告警")
    except Exception as e:
        logger.error(f"发送Sentry告警失败: {e}")
