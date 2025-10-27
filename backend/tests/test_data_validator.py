"""
数据验证器和数据质量测试套件（任务6.8）

测试场景：
1. 价格数据合理性检查（6.1）
2. 市值计算一致性验证（6.2）
3. 社交媒体数据时效性验证（6.3）
4. 链上数据完整性校验（6.4）
5. 数据异常检测Z-score（6.5）
6. 数据质量指标计算（6.6）
7. 综合质量分析
"""
import pytest
from datetime import datetime, timedelta
from typing import Dict, Any

from app.core.data_validator import (
    DataValidator,
    ValidationResult,
    ValidationSeverity,
    data_validator,
)
from app.core.data_quality import (
    DataQualityMetrics,
    data_quality_metrics,
)


# ================================
# 测试1: 价格数据合理性检查（任务6.1）
# ================================


def test_price_reasonability_normal_change():
    """测试正常价格变化（<50%）"""
    result = data_validator.validate_price_reasonability(
        current_price=105.0,
        previous_price=100.0,
        threshold=0.5,
        symbol="TEST",
    )

    assert result.valid is True
    assert result.check_name == "price_reasonability"
    assert result.severity == ValidationSeverity.INFO


def test_price_reasonability_large_increase():
    """测试价格大幅上涨（>50%）"""
    result = data_validator.validate_price_reasonability(
        current_price=200.0,
        previous_price=100.0,
        threshold=0.5,
        symbol="TEST",
    )

    assert result.valid is False
    assert result.severity == ValidationSeverity.WARNING
    assert "上涨" in result.message
    assert result.details["change_pct"] == 1.0  # 100% increase


def test_price_reasonability_large_decrease():
    """测试价格大幅下跌（>50%）"""
    result = data_validator.validate_price_reasonability(
        current_price=40.0,
        previous_price=100.0,
        threshold=0.5,
        symbol="TEST",
    )

    assert result.valid is False
    assert result.severity == ValidationSeverity.WARNING
    assert "下跌" in result.message
    assert result.details["change_pct"] == 0.6  # 60% decrease


def test_price_reasonability_no_previous_price():
    """测试无历史价格时跳过检查"""
    result = data_validator.validate_price_reasonability(
        current_price=100.0,
        previous_price=None,
        symbol="TEST",
    )

    assert result.valid is True
    assert "无历史价格" in result.message


# ================================
# 测试2: 市值计算一致性验证（任务6.2）
# ================================


def test_market_cap_consistency_valid():
    """测试市值计算一致（差异<5%）"""
    result = data_validator.validate_market_cap_consistency(
        price_usd=100.0,
        circulating_supply=1_000_000.0,
        reported_market_cap=100_000_000.0,  # 期望值：100 * 1M = 100M
        tolerance=0.05,
        symbol="TEST",
    )

    assert result.valid is True
    assert result.check_name == "market_cap_consistency"


def test_market_cap_consistency_invalid():
    """测试市值计算不一致（差异>5%）"""
    result = data_validator.validate_market_cap_consistency(
        price_usd=100.0,
        circulating_supply=1_000_000.0,
        reported_market_cap=120_000_000.0,  # 期望值：100M，实际120M，差异20%
        tolerance=0.05,
        symbol="TEST",
    )

    assert result.valid is False
    assert result.severity == ValidationSeverity.WARNING
    assert "不一致" in result.message
    assert result.details["diff_pct"] > 0.05


def test_market_cap_consistency_missing_data():
    """测试缺少市值计算数据"""
    result = data_validator.validate_market_cap_consistency(
        price_usd=100.0,
        circulating_supply=None,
        reported_market_cap=100_000_000.0,
        symbol="TEST",
    )

    assert result.valid is True  # 跳过检查
    assert "缺少市值计算所需数据" in result.message


# ================================
# 测试3: 社交媒体数据时效性验证（任务6.3）
# ================================


def test_social_data_freshness_valid():
    """测试社交数据新鲜（<24小时）"""
    now = datetime.utcnow()
    one_hour_ago = (now - timedelta(hours=1)).isoformat()

    social_data = {
        "twitter": {
            "mention_count": 100,
            "last_updated": one_hour_ago,
        },
        "reddit": {
            "post_count": 50,
            "last_updated": one_hour_ago,
        },
    }

    result = data_validator.validate_social_data_freshness(
        social_data=social_data,
        max_age_hours=24,
        symbol="TEST",
    )

    assert result.valid is True
    assert result.check_name == "social_data_freshness"


def test_social_data_freshness_stale():
    """测试社交数据过期（>24小时）"""
    now = datetime.utcnow()
    two_days_ago = (now - timedelta(days=2)).isoformat()

    social_data = {
        "twitter": {
            "mention_count": 100,
            "last_updated": two_days_ago,
        },
        "reddit": {
            "post_count": 50,
            "last_updated": two_days_ago,
        },
    }

    result = data_validator.validate_social_data_freshness(
        social_data=social_data,
        max_age_hours=24,
        symbol="TEST",
    )

    assert result.valid is False
    assert result.severity == ValidationSeverity.WARNING
    assert "过期" in result.message


def test_social_data_freshness_no_data():
    """测试无社交数据"""
    result = data_validator.validate_social_data_freshness(
        social_data={},
        symbol="TEST",
    )

    assert result.valid is False
    assert "无社交媒体数据" in result.message


# ================================
# 测试4: 链上数据完整性校验（任务6.4）
# ================================


def test_onchain_data_completeness_valid():
    """测试链上数据完整"""
    onchain_data = {
        "ethereum": {
            "transaction_count_24h": 1000,
            "active_addresses_24h": 500,
            "holder_count": 10000,
        }
    }

    result = data_validator.validate_onchain_data_completeness(
        onchain_data=onchain_data,
        symbol="TEST",
    )

    assert result.valid is True
    assert result.check_name == "onchain_data_completeness"
    assert "ethereum" in result.details["valid_chains"]


def test_onchain_data_completeness_incomplete():
    """测试链上数据不完整（缺少必填字段）"""
    onchain_data = {
        "ethereum": {
            "holder_count": 10000,
            # 缺少 transaction_count_24h 和 active_addresses_24h
        },
        "bsc": {
            "holder_count": 5000,
        },
    }

    result = data_validator.validate_onchain_data_completeness(
        onchain_data=onchain_data,
        symbol="TEST",
    )

    assert result.valid is False
    assert result.severity == ValidationSeverity.WARNING
    assert "不完整" in result.message


def test_onchain_data_completeness_no_data():
    """测试无链上数据"""
    result = data_validator.validate_onchain_data_completeness(
        onchain_data={},
        symbol="TEST",
    )

    assert result.valid is False
    assert "无链上数据" in result.message


# ================================
# 测试5: 数据异常检测Z-score（任务6.5）
# ================================


def test_zscore_anomaly_detection_normal():
    """测试Z-score正常值"""
    historical_values = [100.0, 102.0, 98.0, 101.0, 99.0, 103.0, 97.0]
    current_value = 100.0

    result = data_validator.detect_anomalies_zscore(
        metric_name="price",
        current_value=current_value,
        historical_values=historical_values,
        threshold=3.0,
        symbol="TEST",
    )

    assert result.valid is True
    assert "正常" in result.message
    assert abs(result.details["z_score"]) < 3.0


def test_zscore_anomaly_detection_anomaly():
    """测试Z-score异常值"""
    historical_values = [100.0, 102.0, 98.0, 101.0, 99.0, 103.0, 97.0]
    current_value = 200.0  # 明显异常

    result = data_validator.detect_anomalies_zscore(
        metric_name="price",
        current_value=current_value,
        historical_values=historical_values,
        threshold=3.0,
        symbol="TEST",
    )

    assert result.valid is False
    assert result.severity == ValidationSeverity.WARNING
    assert "异常值" in result.message
    assert abs(result.details["z_score"]) > 3.0


def test_zscore_anomaly_detection_insufficient_data():
    """测试历史数据不足"""
    result = data_validator.detect_anomalies_zscore(
        metric_name="price",
        current_value=100.0,
        historical_values=[100.0, 101.0],  # 少于3个数据点
        symbol="TEST",
    )

    assert result.valid is True  # 跳过检查
    assert "历史数据不足" in result.message


def test_zscore_anomaly_detection_no_variance():
    """测试数据无变化（标准差为0）"""
    historical_values = [100.0, 100.0, 100.0, 100.0]
    current_value = 100.0

    result = data_validator.detect_anomalies_zscore(
        metric_name="price",
        current_value=current_value,
        historical_values=historical_values,
        threshold=3.0,
        symbol="TEST",
    )

    assert result.valid is True
    assert "无变化" in result.message


# ================================
# 测试6: 数据质量指标计算（任务6.6）
# ================================


def test_completeness_calculation_full():
    """测试完整度计算（所有字段齐全）"""
    snapshot_data = {
        "symbol": "TEST",
        "timestamp": datetime.utcnow().isoformat(),
        "market_data": {
            "current": {
                "price_usd": 100.0,
                "market_cap": 100_000_000.0,
                "total_volume_24h": 10_000_000.0,
                "circulating_supply": 1_000_000.0,
                "total_supply": 2_000_000.0,
                "price_change_24h": 5.0,
                "price_change_7d": 10.0,
            }
        },
        "onchain_data": {
            "ethereum": {
                "transaction_count_24h": 1000,
                "active_addresses_24h": 500,
            }
        },
        "social_data": {
            "twitter": {
                "mention_count": 100,
                "sentiment_score": 0.7,
            },
            "reddit": {
                "post_count": 50,
                "sentiment_score": 0.6,
            },
        },
    }

    completeness = data_quality_metrics.calculate_completeness(snapshot_data)
    assert completeness == 1.0  # 100%完整


def test_completeness_calculation_partial():
    """测试完整度计算（部分字段缺失）"""
    snapshot_data = {
        "symbol": "TEST",
        "market_data": {
            "current": {
                "price_usd": 100.0,
                "market_cap": 100_000_000.0,
                # 缺少其他字段
            }
        },
        "onchain_data": {},
        "social_data": {},
    }

    completeness = data_quality_metrics.calculate_completeness(snapshot_data)
    assert 0.0 < completeness < 1.0  # 部分完整


def test_accuracy_calculation_all_passed():
    """测试准确度计算（所有验证通过）"""
    validation_results = [
        ValidationResult(
            valid=True,
            check_name="test_1",
            message="Pass",
            severity=ValidationSeverity.INFO,
        ),
        ValidationResult(
            valid=True,
            check_name="test_2",
            message="Pass",
            severity=ValidationSeverity.INFO,
        ),
    ]

    accuracy = data_quality_metrics.calculate_accuracy(validation_results)
    assert accuracy == 1.0


def test_accuracy_calculation_some_failed():
    """测试准确度计算（部分验证失败）"""
    validation_results = [
        ValidationResult(
            valid=True,
            check_name="test_1",
            message="Pass",
            severity=ValidationSeverity.INFO,
        ),
        ValidationResult(
            valid=False,
            check_name="test_2",
            message="Fail",
            severity=ValidationSeverity.WARNING,
        ),
        ValidationResult(
            valid=False,
            check_name="test_3",
            message="Fail",
            severity=ValidationSeverity.WARNING,
        ),
    ]

    accuracy = data_quality_metrics.calculate_accuracy(validation_results)
    assert accuracy < 1.0


def test_timeliness_calculation_fresh():
    """测试时效性计算（最近5分钟）"""
    now = datetime.utcnow()
    timeliness = data_quality_metrics.calculate_timeliness(now)
    assert timeliness == 1.0


def test_timeliness_calculation_moderate():
    """测试时效性计算（30分钟前）"""
    thirty_min_ago = datetime.utcnow() - timedelta(minutes=30)
    timeliness = data_quality_metrics.calculate_timeliness(thirty_min_ago)
    assert timeliness == 0.7


def test_timeliness_calculation_old():
    """测试时效性计算（超过24小时）"""
    two_days_ago = datetime.utcnow() - timedelta(days=2)
    timeliness = data_quality_metrics.calculate_timeliness(two_days_ago)
    assert timeliness == 0.0


def test_overall_score_calculation():
    """测试综合质量得分计算"""
    overall = data_quality_metrics.calculate_overall_score(
        completeness=0.9,
        accuracy=0.95,
        timeliness=1.0,
    )

    # 默认权重：30%完整度 + 50%准确度 + 20%时效性
    expected = 0.9 * 0.3 + 0.95 * 0.5 + 1.0 * 0.2
    assert abs(overall - expected) < 0.01


def test_overall_score_custom_weights():
    """测试自定义权重的综合得分"""
    custom_weights = {
        "completeness": 0.4,
        "accuracy": 0.4,
        "timeliness": 0.2,
    }

    overall = data_quality_metrics.calculate_overall_score(
        completeness=0.8,
        accuracy=0.9,
        timeliness=0.7,
        weights=custom_weights,
    )

    expected = 0.8 * 0.4 + 0.9 * 0.4 + 0.7 * 0.2
    assert abs(overall - expected) < 0.01


# ================================
# 测试7: 综合质量分析
# ================================


def test_analyze_snapshot_quality_excellent():
    """测试质量分析（优秀质量）"""
    snapshot_data = {
        "symbol": "TEST",
        "timestamp": datetime.utcnow().isoformat(),
        "market_data": {
            "current": {
                "price_usd": 100.0,
                "market_cap": 100_000_000.0,
                "total_volume_24h": 10_000_000.0,
                "circulating_supply": 1_000_000.0,
                "total_supply": 2_000_000.0,
                "price_change_24h": 5.0,
                "price_change_7d": 10.0,
            }
        },
        "onchain_data": {
            "ethereum": {
                "transaction_count_24h": 1000,
                "active_addresses_24h": 500,
            }
        },
        "social_data": {
            "twitter": {"mention_count": 100, "sentiment_score": 0.7},
            "reddit": {"post_count": 50, "sentiment_score": 0.6},
        },
    }

    validation_results = [
        ValidationResult(True, "test_1", "Pass", ValidationSeverity.INFO),
        ValidationResult(True, "test_2", "Pass", ValidationSeverity.INFO),
    ]

    report = data_quality_metrics.analyze_snapshot_quality(
        snapshot_data=snapshot_data,
        validation_results=validation_results,
    )

    assert report["quality_level"] in ["excellent", "good"]
    assert report["metrics"]["overall_score"] >= 0.7
    assert report["issues"]["warnings"] == 0


def test_analyze_snapshot_quality_poor():
    """测试质量分析（差质量）"""
    snapshot_data = {
        "symbol": "TEST",
        "timestamp": (datetime.utcnow() - timedelta(days=3)).isoformat(),  # 过期数据
        "market_data": {
            "current": {}  # 缺失所有字段
        },
        "onchain_data": {},
        "social_data": {},
    }

    validation_results = [
        ValidationResult(False, "test_1", "Fail", ValidationSeverity.WARNING),
        ValidationResult(False, "test_2", "Fail", ValidationSeverity.ERROR),
    ]

    report = data_quality_metrics.analyze_snapshot_quality(
        snapshot_data=snapshot_data,
        validation_results=validation_results,
    )

    assert report["quality_level"] in ["poor", "fair"]
    assert report["metrics"]["overall_score"] < 0.7
    assert report["issues"]["warnings"] > 0 or report["issues"]["errors"] > 0


def test_analyze_batch_quality():
    """测试批量质量分析"""
    quality_reports = [
        {
            "symbol": "BTC",
            "metrics": {
                "completeness": 0.9,
                "accuracy": 0.95,
                "timeliness": 1.0,
                "overall_score": 0.95,
            },
            "quality_level": "excellent",
            "issues": {"warnings": 0, "errors": 0, "critical": 0},
        },
        {
            "symbol": "ETH",
            "metrics": {
                "completeness": 0.8,
                "accuracy": 0.85,
                "timeliness": 0.9,
                "overall_score": 0.85,
            },
            "quality_level": "good",
            "issues": {"warnings": 1, "errors": 0, "critical": 0},
        },
    ]

    summary = data_quality_metrics.analyze_batch_quality(quality_reports)

    assert summary["total_count"] == 2
    assert 0.8 < summary["avg_metrics"]["overall_score"] < 1.0
    assert summary["quality_distribution"]["excellent"] == 1
    assert summary["quality_distribution"]["good"] == 1
    assert summary["total_issues"]["warnings"] == 1
