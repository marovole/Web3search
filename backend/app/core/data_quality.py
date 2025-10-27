"""
数据质量指标计算模块（任务6.6）

计算数据质量维度指标：
- 完整度（Completeness）
- 准确度（Accuracy）
- 时效性（Timeliness）
- 综合质量得分
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from app.core.data_validator import ValidationResult, ValidationSeverity

logger = logging.getLogger(__name__)


# ================================
# 数据质量指标计算器
# ================================


class DataQualityMetrics:
    """
    数据质量指标计算器

    计算三大核心维度：完整度、准确度、时效性
    """

    def __init__(self):
        """初始化质量指标计算器"""
        # 定义核心字段列表（用于完整度计算）
        self.core_market_fields = [
            "price_usd",
            "market_cap",
            "total_volume_24h",
            "circulating_supply",
            "total_supply",
            "price_change_24h",
            "price_change_7d",
        ]

        self.core_onchain_fields = [
            "transaction_count_24h",
            "active_addresses_24h",
        ]

        self.core_social_fields = [
            "twitter.mention_count",
            "twitter.sentiment_score",
            "reddit.post_count",
            "reddit.sentiment_score",
        ]

    # ================================
    # 任务6.6: 完整度计算
    # ================================

    def calculate_completeness(self, snapshot_data: Dict[str, Any]) -> float:
        """
        计算数据完整度（任务6.6）

        完整度 = 已填充字段数 / 总字段数

        Args:
            snapshot_data: 项目快照数据

        Returns:
            float: 完整度得分（0.0-1.0）
        """
        filled_count = 0
        total_count = 0

        # 检查市场数据
        market_data = snapshot_data.get("market_data", {}).get("current", {})
        for field in self.core_market_fields:
            total_count += 1
            if market_data.get(field) is not None:
                filled_count += 1

        # 检查链上数据
        onchain_data = snapshot_data.get("onchain_data", {})
        for chain_name, chain_data in onchain_data.items():
            if isinstance(chain_data, dict) and not chain_data.get("error"):
                for field in self.core_onchain_fields:
                    total_count += 1
                    if chain_data.get(field) is not None:
                        filled_count += 1
                break  # 只检查第一条有效链

        # 检查社交数据
        social_data = snapshot_data.get("social_data", {})
        for field_path in self.core_social_fields:
            total_count += 1
            parts = field_path.split(".")
            value = social_data
            for part in parts:
                value = value.get(part, {}) if isinstance(value, dict) else None
                if value is None:
                    break
            if value is not None:
                filled_count += 1

        # 计算完整度
        if total_count == 0:
            return 0.0

        completeness = filled_count / total_count
        return round(completeness, 3)

    # ================================
    # 任务6.6: 准确度计算
    # ================================

    def calculate_accuracy(self, validation_results: List[ValidationResult]) -> float:
        """
        计算数据准确度（任务6.6）

        准确度 = 通过验证的检查数 / 总检查数

        Args:
            validation_results: 验证结果列表

        Returns:
            float: 准确度得分（0.0-1.0）
        """
        if not validation_results:
            return 1.0  # 如果没有验证结果，默认为准确

        # 只统计实际执行的检查（排除INFO级别的跳过检查）
        valid_checks = [
            r for r in validation_results
            if r.severity != ValidationSeverity.INFO or r.valid is False
        ]

        if not valid_checks:
            return 1.0

        passed_count = sum(1 for r in valid_checks if r.valid)
        total_count = len(valid_checks)

        accuracy = passed_count / total_count
        return round(accuracy, 3)

    # ================================
    # 任务6.6: 时效性计算
    # ================================

    def calculate_timeliness(self, data_timestamp: datetime) -> float:
        """
        计算数据时效性（任务6.6）

        时效性得分基于数据新鲜度：
        - 最近 5 分钟：1.0
        - 5-15 分钟：0.9
        - 15-60 分钟：0.7
        - 1-24 小时：0.5
        - 超过 24 小时：0.0

        Args:
            data_timestamp: 数据时间戳

        Returns:
            float: 时效性得分（0.0-1.0）
        """
        now = datetime.utcnow()

        # 处理时间戳格式
        if isinstance(data_timestamp, str):
            try:
                data_timestamp = datetime.fromisoformat(data_timestamp.replace("Z", "+00:00"))
            except ValueError:
                logger.warning(f"无法解析时间戳: {data_timestamp}")
                return 0.0

        # 计算时间差（分钟）
        age_minutes = (now - data_timestamp).total_seconds() / 60

        # 分段计算时效性得分
        if age_minutes <= 5:
            return 1.0
        elif age_minutes <= 15:
            return 0.9
        elif age_minutes <= 60:
            return 0.7
        elif age_minutes <= 1440:  # 24小时
            return 0.5
        else:
            return 0.0

    # ================================
    # 综合质量得分
    # ================================

    def calculate_overall_score(
        self,
        completeness: float,
        accuracy: float,
        timeliness: float,
        weights: Optional[Dict[str, float]] = None,
    ) -> float:
        """
        计算综合质量得分

        默认权重：
        - 完整度：30%
        - 准确度：50%
        - 时效性：20%

        Args:
            completeness: 完整度得分
            accuracy: 准确度得分
            timeliness: 时效性得分
            weights: 自定义权重（可选）

        Returns:
            float: 综合质量得分（0.0-1.0）
        """
        if weights is None:
            weights = {
                "completeness": 0.3,
                "accuracy": 0.5,
                "timeliness": 0.2,
            }

        overall_score = (
            completeness * weights["completeness"]
            + accuracy * weights["accuracy"]
            + timeliness * weights["timeliness"]
        )

        return round(overall_score, 3)

    # ================================
    # 综合分析方法
    # ================================

    def analyze_snapshot_quality(
        self,
        snapshot_data: Dict[str, Any],
        validation_results: List[ValidationResult],
    ) -> Dict[str, Any]:
        """
        对快照数据执行完整的质量分析

        Args:
            snapshot_data: 项目快照数据
            validation_results: 验证结果列表

        Returns:
            Dict: 质量分析报告
        """
        # 获取数据时间戳
        timestamp_str = snapshot_data.get("timestamp")
        timestamp = datetime.utcnow()
        if timestamp_str:
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            except ValueError:
                pass

        # 计算三大指标
        completeness = self.calculate_completeness(snapshot_data)
        accuracy = self.calculate_accuracy(validation_results)
        timeliness = self.calculate_timeliness(timestamp)

        # 计算综合得分
        overall_score = self.calculate_overall_score(completeness, accuracy, timeliness)

        # 统计验证问题
        warnings = [r for r in validation_results if r.severity == ValidationSeverity.WARNING and not r.valid]
        errors = [r for r in validation_results if r.severity == ValidationSeverity.ERROR and not r.valid]
        critical = [r for r in validation_results if r.severity == ValidationSeverity.CRITICAL and not r.valid]

        # 生成质量等级
        if overall_score >= 0.9:
            quality_level = "excellent"
        elif overall_score >= 0.7:
            quality_level = "good"
        elif overall_score >= 0.5:
            quality_level = "fair"
        else:
            quality_level = "poor"

        return {
            "symbol": snapshot_data.get("symbol", "Unknown"),
            "timestamp": timestamp.isoformat(),
            "metrics": {
                "completeness": completeness,
                "accuracy": accuracy,
                "timeliness": timeliness,
                "overall_score": overall_score,
            },
            "quality_level": quality_level,
            "issues": {
                "warnings": len(warnings),
                "errors": len(errors),
                "critical": len(critical),
            },
            "validation_results": [r.to_dict() for r in validation_results],
        }

    # ================================
    # 批量质量分析
    # ================================

    def analyze_batch_quality(
        self,
        quality_reports: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        分析一批质量报告，生成汇总统计

        Args:
            quality_reports: 质量报告列表

        Returns:
            Dict: 汇总统计信息
        """
        if not quality_reports:
            return {
                "total_count": 0,
                "avg_metrics": {},
                "quality_distribution": {},
            }

        # 计算平均指标
        avg_completeness = sum(r["metrics"]["completeness"] for r in quality_reports) / len(quality_reports)
        avg_accuracy = sum(r["metrics"]["accuracy"] for r in quality_reports) / len(quality_reports)
        avg_timeliness = sum(r["metrics"]["timeliness"] for r in quality_reports) / len(quality_reports)
        avg_overall = sum(r["metrics"]["overall_score"] for r in quality_reports) / len(quality_reports)

        # 统计质量等级分布
        quality_distribution = {}
        for report in quality_reports:
            level = report["quality_level"]
            quality_distribution[level] = quality_distribution.get(level, 0) + 1

        # 统计问题数量
        total_warnings = sum(r["issues"]["warnings"] for r in quality_reports)
        total_errors = sum(r["issues"]["errors"] for r in quality_reports)
        total_critical = sum(r["issues"]["critical"] for r in quality_reports)

        return {
            "total_count": len(quality_reports),
            "avg_metrics": {
                "completeness": round(avg_completeness, 3),
                "accuracy": round(avg_accuracy, 3),
                "timeliness": round(avg_timeliness, 3),
                "overall_score": round(avg_overall, 3),
            },
            "quality_distribution": quality_distribution,
            "total_issues": {
                "warnings": total_warnings,
                "errors": total_errors,
                "critical": total_critical,
            },
        }


# ================================
# 全局实例
# ================================

data_quality_metrics = DataQualityMetrics()
