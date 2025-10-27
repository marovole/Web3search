"""
A/B测试框架（任务 12.4）

功能：
1. 对比不同prompt版本
2. 随机分组测试
3. 统计显著性检验
4. 结果可视化数据
"""
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging
import json
import random
from enum import Enum
import numpy as np

from app.services.prompt_version import PromptVersion, PromptVersionControl
from app.services.prompt_evaluator import PromptEvaluator, EvaluationResult

logger = logging.getLogger(__name__)


# ================================
# A/B测试配置
# ================================

class TestVariant(str, Enum):
    """测试变体"""
    A = "A"  # 对照组
    B = "B"  # 实验组


@dataclass
class ABTestConfig:
    """A/B测试配置"""
    test_name: str
    variant_a: PromptVersion  # 对照组版本
    variant_b: PromptVersion  # 实验组版本
    traffic_split: float = 0.5  # B组流量比例（0-1）
    min_sample_size: int = 30  # 最小样本量
    confidence_level: float = 0.95  # 置信水平
    metadata: Dict[str, Any] = field(default_factory=dict)


# ================================
# 测试结果
# ================================

@dataclass
class VariantResult:
    """单个变体的结果"""
    variant: TestVariant
    version: str
    sample_size: int
    scores: List[float]  # 综合得分列表
    mean_score: float
    std_score: float
    evaluation_details: List[EvaluationResult] = field(default_factory=list)


@dataclass
class ABTestResult:
    """A/B测试结果"""
    test_name: str
    variant_a: VariantResult
    variant_b: VariantResult
    winner: Optional[TestVariant] = None
    confidence: float = 0.0  # 置信度
    p_value: float = 1.0  # p值
    effect_size: float = 0.0  # 效应量（Cohen's d）
    is_significant: bool = False
    recommendation: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "test_name": self.test_name,
            "variant_a": {
                "variant": self.variant_a.variant.value,
                "version": self.variant_a.version,
                "sample_size": self.variant_a.sample_size,
                "mean_score": self.variant_a.mean_score,
                "std_score": self.variant_a.std_score
            },
            "variant_b": {
                "variant": self.variant_b.variant.value,
                "version": self.variant_b.version,
                "sample_size": self.variant_b.sample_size,
                "mean_score": self.variant_b.mean_score,
                "std_score": self.variant_b.std_score
            },
            "winner": self.winner.value if self.winner else None,
            "confidence": self.confidence,
            "p_value": self.p_value,
            "effect_size": self.effect_size,
            "is_significant": self.is_significant,
            "recommendation": self.recommendation,
            "metadata": self.metadata
        }


# ================================
# A/B测试执行器
# ================================

class ABTestRunner:
    """A/B测试执行器"""

    def __init__(
        self,
        config: ABTestConfig,
        evaluator: Optional[PromptEvaluator] = None
    ):
        """
        初始化A/B测试执行器

        Args:
            config: 测试配置
            evaluator: Prompt评估器
        """
        self.config = config
        self.evaluator = evaluator or PromptEvaluator()

        # 结果收集
        self.variant_a_scores: List[float] = []
        self.variant_a_details: List[EvaluationResult] = []

        self.variant_b_scores: List[float] = []
        self.variant_b_details: List[EvaluationResult] = []

    def assign_variant(self) -> TestVariant:
        """
        随机分配变体

        Returns:
            TestVariant: A或B
        """
        return TestVariant.B if random.random() < self.config.traffic_split else TestVariant.A

    def run_test_case(
        self,
        test_case: Dict[str, str],
        variant: Optional[TestVariant] = None
    ) -> Tuple[TestVariant, EvaluationResult]:
        """
        执行单个测试用例

        Args:
            test_case: 测试用例 {"query": "...", "reference": "..."}
            variant: 指定变体（不指定则随机）

        Returns:
            Tuple[TestVariant, EvaluationResult]: 变体和评估结果
        """
        # 分配变体
        if variant is None:
            variant = self.assign_variant()

        # 获取对应版本的prompt
        prompt_version = (
            self.config.variant_a if variant == TestVariant.A
            else self.config.variant_b
        )

        # 注意：这里简化处理，实际应该用prompt生成响应
        # 假设test_case包含hypothesis（AI生成的答案）
        reference = test_case.get("reference", "")
        hypothesis = test_case.get("hypothesis", "")

        # 评估
        result = self.evaluator.evaluate(reference, hypothesis)

        # 收集结果
        if variant == TestVariant.A:
            self.variant_a_scores.append(result.overall_score)
            self.variant_a_details.append(result)
        else:
            self.variant_b_scores.append(result.overall_score)
            self.variant_b_details.append(result)

        return variant, result

    def run_batch(
        self,
        test_cases: List[Dict[str, str]]
    ) -> ABTestResult:
        """
        批量执行A/B测试

        Args:
            test_cases: 测试用例列表

        Returns:
            ABTestResult: 测试结果
        """
        logger.info(f"开始A/B测试：{self.config.test_name}")
        logger.info(f"测试用例数：{len(test_cases)}")

        # 执行所有测试用例
        for case in test_cases:
            self.run_test_case(case)

        # 分析结果
        result = self.analyze_results()
        return result

    def analyze_results(self) -> ABTestResult:
        """
        分析A/B测试结果

        Returns:
            ABTestResult: 测试结果
        """
        # 构建变体结果
        variant_a_result = VariantResult(
            variant=TestVariant.A,
            version=self.config.variant_a.version,
            sample_size=len(self.variant_a_scores),
            scores=self.variant_a_scores,
            mean_score=float(np.mean(self.variant_a_scores)) if self.variant_a_scores else 0.0,
            std_score=float(np.std(self.variant_a_scores)) if self.variant_a_scores else 0.0,
            evaluation_details=self.variant_a_details
        )

        variant_b_result = VariantResult(
            variant=TestVariant.B,
            version=self.config.variant_b.version,
            sample_size=len(self.variant_b_scores),
            scores=self.variant_b_scores,
            mean_score=float(np.mean(self.variant_b_scores)) if self.variant_b_scores else 0.0,
            std_score=float(np.std(self.variant_b_scores)) if self.variant_b_scores else 0.0,
            evaluation_details=self.variant_b_details
        )

        # 统计检验
        winner, confidence, p_value, effect_size, is_significant = self._statistical_test(
            self.variant_a_scores,
            self.variant_b_scores
        )

        # 生成建议
        recommendation = self._generate_recommendation(
            variant_a_result,
            variant_b_result,
            winner,
            is_significant
        )

        return ABTestResult(
            test_name=self.config.test_name,
            variant_a=variant_a_result,
            variant_b=variant_b_result,
            winner=winner,
            confidence=confidence,
            p_value=p_value,
            effect_size=effect_size,
            is_significant=is_significant,
            recommendation=recommendation,
            metadata={
                "timestamp": datetime.utcnow().isoformat(),
                "traffic_split": self.config.traffic_split,
                "min_sample_size": self.config.min_sample_size
            }
        )

    def _statistical_test(
        self,
        scores_a: List[float],
        scores_b: List[float]
    ) -> Tuple[Optional[TestVariant], float, float, float, bool]:
        """
        统计显著性检验（双样本t检验）

        Returns:
            Tuple: (winner, confidence, p_value, effect_size, is_significant)
        """
        if len(scores_a) < self.config.min_sample_size or len(scores_b) < self.config.min_sample_size:
            logger.warning("样本量不足，无法进行统计检验")
            return None, 0.0, 1.0, 0.0, False

        try:
            # 简化t检验（使用numpy）
            mean_a = np.mean(scores_a)
            mean_b = np.mean(scores_b)
            std_a = np.std(scores_a, ddof=1)
            std_b = np.std(scores_b, ddof=1)
            n_a = len(scores_a)
            n_b = len(scores_b)

            # 合并标准差
            pooled_std = np.sqrt(((n_a - 1) * std_a**2 + (n_b - 1) * std_b**2) / (n_a + n_b - 2))

            # t统计量
            t_stat = (mean_b - mean_a) / (pooled_std * np.sqrt(1/n_a + 1/n_b))

            # 自由度
            df = n_a + n_b - 2

            # 简化p值计算（双尾）
            # 实际应使用scipy.stats.t.cdf
            # 这里使用近似
            p_value = 2 * (1 - self._t_cdf(abs(t_stat), df))

            # Cohen's d（效应量）
            effect_size = (mean_b - mean_a) / pooled_std

            # 判断显著性
            alpha = 1 - self.config.confidence_level
            is_significant = p_value < alpha

            # 确定winner
            winner = None
            if is_significant:
                winner = TestVariant.B if mean_b > mean_a else TestVariant.A

            confidence = (1 - p_value) if is_significant else 0.0

            return winner, confidence, p_value, effect_size, is_significant

        except Exception as e:
            logger.error(f"统计检验失败: {e}")
            return None, 0.0, 1.0, 0.0, False

    @staticmethod
    def _t_cdf(t: float, df: int) -> float:
        """
        t分布CDF近似（简化版）

        实际应使用scipy.stats.t.cdf
        """
        # 正态近似（仅当df > 30时较准确）
        if df > 30:
            return 0.5 * (1 + np.tanh(t / np.sqrt(2)))
        else:
            # 简化：使用正态近似
            return 0.5 * (1 + np.tanh(t / np.sqrt(2)))

    def _generate_recommendation(
        self,
        variant_a: VariantResult,
        variant_b: VariantResult,
        winner: Optional[TestVariant],
        is_significant: bool
    ) -> str:
        """生成建议"""
        if not is_significant:
            return (
                f"测试结果无显著差异（p > {1 - self.config.confidence_level:.2f}）。"
                f"建议继续使用当前版本（{variant_a.version}），或增加样本量再测试。"
            )

        if winner == TestVariant.A:
            return (
                f"变体A（{variant_a.version}）显著优于变体B（{variant_b.version}）。"
                f"平均得分：A={variant_a.mean_score:.3f} vs B={variant_b.mean_score:.3f}。"
                f"建议保持使用A版本。"
            )
        else:
            improvement = ((variant_b.mean_score - variant_a.mean_score) / variant_a.mean_score) * 100
            return (
                f"变体B（{variant_b.version}）显著优于变体A（{variant_a.version}）。"
                f"平均得分：B={variant_b.mean_score:.3f} vs A={variant_a.mean_score:.3f}。"
                f"相对提升：{improvement:.1f}%。"
                f"建议升级到B版本（{variant_b.version}）。"
            )


# ================================
# A/B测试管理器
# ================================

class ABTestManager:
    """A/B测试管理器"""

    def __init__(self):
        self.tests: Dict[str, ABTestRunner] = {}
        self.results: Dict[str, ABTestResult] = {}

    def create_test(
        self,
        test_name: str,
        prompt_name: str,
        version_a: str,
        version_b: str,
        traffic_split: float = 0.5
    ) -> ABTestRunner:
        """
        创建A/B测试

        Args:
            test_name: 测试名称
            prompt_name: Prompt名称
            version_a: A版本号
            version_b: B版本号
            traffic_split: B组流量比例

        Returns:
            ABTestRunner: 测试执行器
        """
        # 加载版本
        vc = PromptVersionControl(prompt_name)

        variant_a = vc.get_version(version_a)
        variant_b = vc.get_version(version_b)

        if not variant_a or not variant_b:
            raise ValueError(f"版本不存在: {version_a} or {version_b}")

        # 创建配置
        config = ABTestConfig(
            test_name=test_name,
            variant_a=variant_a,
            variant_b=variant_b,
            traffic_split=traffic_split
        )

        # 创建执行器
        runner = ABTestRunner(config)
        self.tests[test_name] = runner

        return runner

    def run_test(
        self,
        test_name: str,
        test_cases: List[Dict[str, str]]
    ) -> ABTestResult:
        """
        执行测试

        Args:
            test_name: 测试名称
            test_cases: 测试用例

        Returns:
            ABTestResult: 测试结果
        """
        runner = self.tests.get(test_name)
        if not runner:
            raise ValueError(f"测试不存在: {test_name}")

        result = runner.run_batch(test_cases)
        self.results[test_name] = result

        return result

    def get_result(self, test_name: str) -> Optional[ABTestResult]:
        """获取测试结果"""
        return self.results.get(test_name)

    def list_tests(self) -> List[str]:
        """列出所有测试"""
        return list(self.tests.keys())


# ================================
# 全局实例
# ================================

ab_test_manager = ABTestManager()


# ================================
# 便捷函数
# ================================

def create_ab_test(
    test_name: str,
    prompt_name: str,
    version_a: str,
    version_b: str,
    traffic_split: float = 0.5
) -> ABTestRunner:
    """
    便捷函数：创建A/B测试

    Args:
        test_name: 测试名称
        prompt_name: Prompt名称
        version_a: A版本号
        version_b: B版本号
        traffic_split: B组流量比例

    Returns:
        ABTestRunner: 测试执行器
    """
    return ab_test_manager.create_test(
        test_name,
        prompt_name,
        version_a,
        version_b,
        traffic_split
    )


def run_ab_test(
    test_name: str,
    test_cases: List[Dict[str, str]]
) -> ABTestResult:
    """
    便捷函数：执行A/B测试

    Args:
        test_name: 测试名称
        test_cases: 测试用例

    Returns:
        ABTestResult: 测试结果
    """
    return ab_test_manager.run_test(test_name, test_cases)
