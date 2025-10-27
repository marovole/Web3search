"""
数据验证器模块（任务6.1-6.5）

提供数据质量验证功能：
- 价格数据合理性检查
- 市值计算一致性验证
- 社交媒体数据时效性验证
- 链上数据完整性校验
- 数据异常检测（Z-score）
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import statistics

logger = logging.getLogger(__name__)


# ================================
# 验证结果数据类
# ================================


class ValidationSeverity(Enum):
    """验证问题严重程度"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationResult:
    """
    验证结果数据类

    Attributes:
        valid: 是否通过验证
        check_name: 检查项名称
        message: 验证消息
        severity: 严重程度
        details: 额外详情
    """
    valid: bool
    check_name: str
    message: str
    severity: ValidationSeverity = ValidationSeverity.INFO
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "valid": self.valid,
            "check_name": self.check_name,
            "message": self.message,
            "severity": self.severity.value,
            "details": self.details or {},
        }


# ================================
# 数据验证器类
# ================================


class DataValidator:
    """
    数据验证器

    提供各类数据质量检查功能
    """

    def __init__(self):
        """初始化验证器"""
        pass

    # ================================
    # 任务6.1: 价格数据合理性检查（±50%波动告警）
    # ================================

    def validate_price_reasonability(
        self,
        current_price: float,
        previous_price: Optional[float],
        threshold: float = 0.5,
        symbol: str = "Unknown",
    ) -> ValidationResult:
        """
        检查价格波动是否在合理范围内（任务6.1）

        Args:
            current_price: 当前价格
            previous_price: 上一次价格
            threshold: 波动阈值（默认0.5即50%）
            symbol: 币种符号

        Returns:
            ValidationResult: 验证结果
        """
        check_name = "price_reasonability"

        # 如果没有历史价格，跳过检查
        if previous_price is None or previous_price == 0:
            return ValidationResult(
                valid=True,
                check_name=check_name,
                message=f"{symbol}: 无历史价格数据，跳过合理性检查",
                severity=ValidationSeverity.INFO,
            )

        # 计算价格变化百分比
        price_change_pct = abs(current_price - previous_price) / previous_price

        # 检查是否超过阈值
        if price_change_pct > threshold:
            direction = "上涨" if current_price > previous_price else "下跌"
            return ValidationResult(
                valid=False,
                check_name=check_name,
                message=f"{symbol}: 价格异常{direction} {price_change_pct*100:.2f}%（阈值{threshold*100}%）",
                severity=ValidationSeverity.WARNING,
                details={
                    "current_price": current_price,
                    "previous_price": previous_price,
                    "change_pct": price_change_pct,
                    "threshold": threshold,
                },
            )

        return ValidationResult(
            valid=True,
            check_name=check_name,
            message=f"{symbol}: 价格变化正常 ({price_change_pct*100:.2f}%)",
            severity=ValidationSeverity.INFO,
            details={"change_pct": price_change_pct},
        )

    # ================================
    # 任务6.2: 验证市值计算一致性（price * supply）
    # ================================

    def validate_market_cap_consistency(
        self,
        price_usd: float,
        circulating_supply: float,
        reported_market_cap: float,
        tolerance: float = 0.05,
        symbol: str = "Unknown",
    ) -> ValidationResult:
        """
        验证市值计算一致性（任务6.2）

        市值 = 价格 * 流通供应量

        Args:
            price_usd: USD价格
            circulating_supply: 流通供应量
            reported_market_cap: 报告的市值
            tolerance: 容忍度（默认0.05即5%）
            symbol: 币种符号

        Returns:
            ValidationResult: 验证结果
        """
        check_name = "market_cap_consistency"

        # 跳过无效数据
        if not all([price_usd, circulating_supply, reported_market_cap]):
            return ValidationResult(
                valid=True,
                check_name=check_name,
                message=f"{symbol}: 缺少市值计算所需数据",
                severity=ValidationSeverity.INFO,
            )

        # 计算期望市值
        expected_market_cap = price_usd * circulating_supply

        # 计算差异百分比
        diff_pct = abs(expected_market_cap - reported_market_cap) / reported_market_cap

        # 检查是否超过容忍度
        if diff_pct > tolerance:
            return ValidationResult(
                valid=False,
                check_name=check_name,
                message=f"{symbol}: 市值计算不一致，差异{diff_pct*100:.2f}%（容忍度{tolerance*100}%）",
                severity=ValidationSeverity.WARNING,
                details={
                    "price_usd": price_usd,
                    "circulating_supply": circulating_supply,
                    "expected_market_cap": expected_market_cap,
                    "reported_market_cap": reported_market_cap,
                    "diff_pct": diff_pct,
                },
            )

        return ValidationResult(
            valid=True,
            check_name=check_name,
            message=f"{symbol}: 市值计算一致（差异{diff_pct*100:.2f}%）",
            severity=ValidationSeverity.INFO,
            details={"diff_pct": diff_pct},
        )

    # ================================
    # 任务6.3: 社交媒体数据时效性验证（24小时内）
    # ================================

    def validate_social_data_freshness(
        self,
        social_data: Dict[str, Any],
        max_age_hours: int = 24,
        symbol: str = "Unknown",
    ) -> ValidationResult:
        """
        验证社交媒体数据的新鲜度（任务6.3）

        Args:
            social_data: 社交数据字典（包含twitter和reddit）
            max_age_hours: 最大数据年龄（小时，默认24）
            symbol: 币种符号

        Returns:
            ValidationResult: 验证结果
        """
        check_name = "social_data_freshness"

        if not social_data:
            return ValidationResult(
                valid=False,
                check_name=check_name,
                message=f"{symbol}: 无社交媒体数据",
                severity=ValidationSeverity.WARNING,
            )

        now = datetime.utcnow()
        stale_sources = []

        # 检查Twitter数据
        twitter = social_data.get("twitter", {})
        if twitter and not twitter.get("error"):
            twitter_timestamp = twitter.get("last_updated")
            if twitter_timestamp:
                # 支持字符串和datetime对象
                if isinstance(twitter_timestamp, str):
                    twitter_timestamp = datetime.fromisoformat(twitter_timestamp.replace("Z", "+00:00"))
                age = (now - twitter_timestamp).total_seconds() / 3600
                if age > max_age_hours:
                    stale_sources.append(f"Twitter({age:.1f}h)")

        # 检查Reddit数据
        reddit = social_data.get("reddit", {})
        if reddit and not reddit.get("error"):
            reddit_timestamp = reddit.get("last_updated")
            if reddit_timestamp:
                if isinstance(reddit_timestamp, str):
                    reddit_timestamp = datetime.fromisoformat(reddit_timestamp.replace("Z", "+00:00"))
                age = (now - reddit_timestamp).total_seconds() / 3600
                if age > max_age_hours:
                    stale_sources.append(f"Reddit({age:.1f}h)")

        # 如果有过期数据
        if stale_sources:
            return ValidationResult(
                valid=False,
                check_name=check_name,
                message=f"{symbol}: 社交数据过期: {', '.join(stale_sources)}",
                severity=ValidationSeverity.WARNING,
                details={"stale_sources": stale_sources, "max_age_hours": max_age_hours},
            )

        return ValidationResult(
            valid=True,
            check_name=check_name,
            message=f"{symbol}: 社交数据新鲜（<{max_age_hours}小时）",
            severity=ValidationSeverity.INFO,
        )

    # ================================
    # 任务6.4: 链上数据完整性校验（必填字段检查）
    # ================================

    def validate_onchain_data_completeness(
        self,
        onchain_data: Dict[str, Any],
        symbol: str = "Unknown",
    ) -> ValidationResult:
        """
        验证链上数据完整性（任务6.4）

        Args:
            onchain_data: 链上数据字典
            symbol: 币种符号

        Returns:
            ValidationResult: 验证结果
        """
        check_name = "onchain_data_completeness"

        if not onchain_data or not isinstance(onchain_data, dict):
            return ValidationResult(
                valid=False,
                check_name=check_name,
                message=f"{symbol}: 无链上数据",
                severity=ValidationSeverity.WARNING,
            )

        # 必填字段列表（至少一条链应该有这些字段）
        required_fields = [
            "transaction_count_24h",
            "active_addresses_24h",
        ]

        # 检查每条链的数据
        missing_fields_by_chain = {}
        valid_chains = []

        for chain_name, chain_data in onchain_data.items():
            if not isinstance(chain_data, dict) or chain_data.get("error"):
                continue

            missing = []
            for field in required_fields:
                if field not in chain_data or chain_data[field] is None:
                    missing.append(field)

            if missing:
                missing_fields_by_chain[chain_name] = missing
            else:
                valid_chains.append(chain_name)

        # 如果没有任何链有完整数据
        if not valid_chains:
            return ValidationResult(
                valid=False,
                check_name=check_name,
                message=f"{symbol}: 链上数据不完整",
                severity=ValidationSeverity.WARNING,
                details={"missing_fields_by_chain": missing_fields_by_chain},
            )

        # 至少有一条链数据完整
        return ValidationResult(
            valid=True,
            check_name=check_name,
            message=f"{symbol}: 链上数据完整（{', '.join(valid_chains)}）",
            severity=ValidationSeverity.INFO,
            details={"valid_chains": valid_chains},
        )

    # ================================
    # 任务6.5: 数据异常检测（基于历史数据的Z-score）
    # ================================

    def detect_anomalies_zscore(
        self,
        metric_name: str,
        current_value: float,
        historical_values: List[float],
        threshold: float = 3.0,
        symbol: str = "Unknown",
    ) -> ValidationResult:
        """
        使用Z-score检测异常值（任务6.5）

        Z-score = (value - mean) / std
        如果 abs(z-score) > threshold，标记为异常

        Args:
            metric_name: 指标名称（如"price", "volume"）
            current_value: 当前值
            historical_values: 历史值列表（过去7天）
            threshold: Z-score阈值（默认3.0）
            symbol: 币种符号

        Returns:
            ValidationResult: 验证结果
        """
        check_name = f"anomaly_detection_{metric_name}"

        # 需要至少3个历史数据点才能计算
        if len(historical_values) < 3:
            return ValidationResult(
                valid=True,
                check_name=check_name,
                message=f"{symbol}: 历史数据不足，跳过{metric_name}异常检测",
                severity=ValidationSeverity.INFO,
            )

        try:
            # 计算均值和标准差
            mean = statistics.mean(historical_values)
            stdev = statistics.stdev(historical_values)

            # 标准差为0，说明数据没有变化
            if stdev == 0:
                return ValidationResult(
                    valid=True,
                    check_name=check_name,
                    message=f"{symbol}: {metric_name}数据无变化",
                    severity=ValidationSeverity.INFO,
                )

            # 计算Z-score
            z_score = (current_value - mean) / stdev

            # 检查是否为异常值
            if abs(z_score) > threshold:
                return ValidationResult(
                    valid=False,
                    check_name=check_name,
                    message=f"{symbol}: {metric_name}异常值检测（Z-score={z_score:.2f}）",
                    severity=ValidationSeverity.WARNING,
                    details={
                        "metric_name": metric_name,
                        "current_value": current_value,
                        "mean": mean,
                        "stdev": stdev,
                        "z_score": z_score,
                        "threshold": threshold,
                    },
                )

            return ValidationResult(
                valid=True,
                check_name=check_name,
                message=f"{symbol}: {metric_name}数值正常（Z-score={z_score:.2f}）",
                severity=ValidationSeverity.INFO,
                details={"z_score": z_score},
            )

        except Exception as e:
            logger.error(f"Z-score计算失败: {e}", extra={"symbol": symbol, "metric": metric_name})
            return ValidationResult(
                valid=True,
                check_name=check_name,
                message=f"{symbol}: Z-score计算失败",
                severity=ValidationSeverity.INFO,
            )

    # ================================
    # 综合验证方法
    # ================================

    def validate_project_snapshot(
        self,
        current_snapshot: Dict[str, Any],
        previous_snapshot: Optional[Dict[str, Any]] = None,
        historical_data: Optional[Dict[str, List[float]]] = None,
    ) -> List[ValidationResult]:
        """
        对项目快照执行所有验证检查

        Args:
            current_snapshot: 当前快照数据
            previous_snapshot: 上一次快照数据（可选）
            historical_data: 历史数据（用于Z-score检测，可选）

        Returns:
            List[ValidationResult]: 所有验证结果列表
        """
        symbol = current_snapshot.get("symbol", "Unknown")
        results = []

        # 任务6.1: 价格合理性检查
        current_price = current_snapshot.get("market_data", {}).get("current", {}).get("price_usd")
        previous_price = None
        if previous_snapshot:
            previous_price = previous_snapshot.get("market_data", {}).get("current", {}).get("price_usd")

        if current_price:
            results.append(
                self.validate_price_reasonability(
                    current_price=current_price,
                    previous_price=previous_price,
                    symbol=symbol,
                )
            )

        # 任务6.2: 市值一致性检查
        market_data = current_snapshot.get("market_data", {}).get("current", {})
        price = market_data.get("price_usd")
        supply = market_data.get("circulating_supply")
        market_cap = market_data.get("market_cap")

        if all([price, supply, market_cap]):
            results.append(
                self.validate_market_cap_consistency(
                    price_usd=price,
                    circulating_supply=supply,
                    reported_market_cap=market_cap,
                    symbol=symbol,
                )
            )

        # 任务6.3: 社交数据新鲜度检查
        social_data = current_snapshot.get("social_data", {})
        if social_data:
            results.append(
                self.validate_social_data_freshness(
                    social_data=social_data,
                    symbol=symbol,
                )
            )

        # 任务6.4: 链上数据完整性检查
        onchain_data = current_snapshot.get("onchain_data", {})
        if onchain_data:
            results.append(
                self.validate_onchain_data_completeness(
                    onchain_data=onchain_data,
                    symbol=symbol,
                )
            )

        # 任务6.5: 异常检测（如果有历史数据）
        if historical_data:
            # 检测价格异常
            if "price" in historical_data and current_price:
                results.append(
                    self.detect_anomalies_zscore(
                        metric_name="price",
                        current_value=current_price,
                        historical_values=historical_data["price"],
                        symbol=symbol,
                    )
                )

            # 检测交易量异常
            current_volume = market_data.get("total_volume_24h")
            if "volume" in historical_data and current_volume:
                results.append(
                    self.detect_anomalies_zscore(
                        metric_name="volume",
                        current_value=current_volume,
                        historical_values=historical_data["volume"],
                        symbol=symbol,
                    )
                )

        return results


# ================================
# 全局实例
# ================================

data_validator = DataValidator()
