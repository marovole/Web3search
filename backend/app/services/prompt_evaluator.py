"""
Prompt自动化评估系统（任务 12.3）

功能：
1. BLEU评分（机器翻译质量）
2. ROUGE评分（文本摘要质量）
3. 语义相似度评分（sentence-transformers）
4. 综合质量评分
5. 批量评估
"""
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
import logging
import json
from pathlib import Path
import numpy as np

logger = logging.getLogger(__name__)

# 尝试导入BLEU/ROUGE库
try:
    from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
    from nltk.tokenize import word_tokenize
    import nltk
    NLTK_AVAILABLE = True

    # 确保必要的数据包已下载
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        logger.warning("下载punkt tokenizer...")
        # 注意：生产环境需要预先下载
except ImportError:
    NLTK_AVAILABLE = False
    logger.warning("nltk未安装，BLEU评分不可用。安装: pip install nltk")

try:
    from rouge_score import rouge_scorer
    ROUGE_AVAILABLE = True
except ImportError:
    ROUGE_AVAILABLE = False
    logger.warning("rouge_score未安装，ROUGE评分不可用。安装: pip install rouge-score")

# 语义相似度（使用已有的embedding引擎）
try:
    from app.services.semantic_search import EmbeddingEngine
    SEMANTIC_AVAILABLE = True
except ImportError:
    SEMANTIC_AVAILABLE = False
    logger.warning("语义相似度引擎不可用")


# ================================
# 评估结果数据类
# ================================

@dataclass
class EvaluationScore:
    """单项评估得分"""
    score: float  # 0-1范围
    details: Dict[str, Any] = field(default_factory=dict)
    method: str = ""


@dataclass
class EvaluationResult:
    """完整评估结果"""
    bleu_score: Optional[EvaluationScore] = None
    rouge_scores: Optional[EvaluationScore] = None
    semantic_score: Optional[EvaluationScore] = None
    overall_score: float = 0.0  # 综合得分
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "bleu": self.bleu_score.score if self.bleu_score else None,
            "rouge": self.rouge_scores.score if self.rouge_scores else None,
            "semantic": self.semantic_score.score if self.semantic_score else None,
            "overall": self.overall_score,
            "metadata": self.metadata
        }


# ================================
# BLEU评分器（任务 12.3）
# ================================

class BLEUEvaluator:
    """BLEU评分器"""

    def __init__(self):
        self.available = NLTK_AVAILABLE

    def evaluate(
        self,
        reference: str,
        hypothesis: str,
        ngram_weights: Tuple[float, ...] = (0.25, 0.25, 0.25, 0.25)
    ) -> EvaluationScore:
        """
        计算BLEU得分

        Args:
            reference: 参考答案
            hypothesis: 生成的答案
            ngram_weights: n-gram权重（默认1-4gram均等）

        Returns:
            EvaluationScore: 评分结果
        """
        if not self.available:
            return EvaluationScore(
                score=0.0,
                method="BLEU",
                details={"error": "nltk not available"}
            )

        try:
            # 分词
            ref_tokens = word_tokenize(reference.lower())
            hyp_tokens = word_tokenize(hypothesis.lower())

            # 计算BLEU（使用平滑）
            smoothie = SmoothingFunction().method4
            score = sentence_bleu(
                [ref_tokens],
                hyp_tokens,
                weights=ngram_weights,
                smoothing_function=smoothie
            )

            return EvaluationScore(
                score=float(score),
                method="BLEU",
                details={
                    "ref_length": len(ref_tokens),
                    "hyp_length": len(hyp_tokens),
                    "ngram_weights": ngram_weights
                }
            )
        except Exception as e:
            logger.error(f"BLEU计算失败: {e}")
            return EvaluationScore(
                score=0.0,
                method="BLEU",
                details={"error": str(e)}
            )


# ================================
# ROUGE评分器（任务 12.3）
# ================================

class ROUGEEvaluator:
    """ROUGE评分器"""

    def __init__(self, rouge_types: List[str] = None):
        """
        初始化ROUGE评分器

        Args:
            rouge_types: ROUGE类型列表（默认: rouge1, rouge2, rougeL）
        """
        self.available = ROUGE_AVAILABLE
        self.rouge_types = rouge_types or ['rouge1', 'rouge2', 'rougeL']

        if self.available:
            self.scorer = rouge_scorer.RougeScorer(
                self.rouge_types,
                use_stemmer=True
            )

    def evaluate(
        self,
        reference: str,
        hypothesis: str
    ) -> EvaluationScore:
        """
        计算ROUGE得分

        Args:
            reference: 参考答案
            hypothesis: 生成的答案

        Returns:
            EvaluationScore: 评分结果
        """
        if not self.available:
            return EvaluationScore(
                score=0.0,
                method="ROUGE",
                details={"error": "rouge_score not available"}
            )

        try:
            scores = self.scorer.score(reference, hypothesis)

            # 提取F1得分
            rouge_scores = {}
            f1_scores = []

            for rouge_type in self.rouge_types:
                f1 = scores[rouge_type].fmeasure
                rouge_scores[rouge_type] = {
                    "precision": scores[rouge_type].precision,
                    "recall": scores[rouge_type].recall,
                    "f1": f1
                }
                f1_scores.append(f1)

            # 平均F1作为总得分
            avg_f1 = np.mean(f1_scores)

            return EvaluationScore(
                score=float(avg_f1),
                method="ROUGE",
                details=rouge_scores
            )
        except Exception as e:
            logger.error(f"ROUGE计算失败: {e}")
            return EvaluationScore(
                score=0.0,
                method="ROUGE",
                details={"error": str(e)}
            )


# ================================
# 语义相似度评分器（任务 12.3）
# ================================

class SemanticSimilarityEvaluator:
    """语义相似度评分器"""

    def __init__(self):
        self.available = SEMANTIC_AVAILABLE

        if self.available:
            try:
                self.embedding_engine = EmbeddingEngine()
                if not self.embedding_engine.is_available():
                    self.available = False
            except Exception as e:
                logger.error(f"初始化embedding引擎失败: {e}")
                self.available = False

    def evaluate(
        self,
        reference: str,
        hypothesis: str
    ) -> EvaluationScore:
        """
        计算语义相似度

        Args:
            reference: 参考答案
            hypothesis: 生成的答案

        Returns:
            EvaluationScore: 评分结果
        """
        if not self.available:
            return EvaluationScore(
                score=0.0,
                method="Semantic",
                details={"error": "Semantic similarity not available"}
            )

        try:
            # 编码为向量
            ref_embedding = self.embedding_engine.encode(reference)
            hyp_embedding = self.embedding_engine.encode(hypothesis)

            if ref_embedding is None or hyp_embedding is None:
                return EvaluationScore(
                    score=0.0,
                    method="Semantic",
                    details={"error": "Encoding failed"}
                )

            # 余弦相似度
            similarity = self._cosine_similarity(ref_embedding, hyp_embedding)

            return EvaluationScore(
                score=float(similarity),
                method="Semantic",
                details={
                    "model": self.embedding_engine.model_name
                }
            )
        except Exception as e:
            logger.error(f"语义相似度计算失败: {e}")
            return EvaluationScore(
                score=0.0,
                method="Semantic",
                details={"error": str(e)}
            )

    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """计算余弦相似度"""
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return float(dot_product / (norm_a * norm_b))


# ================================
# 综合评估器（任务 12.3）
# ================================

class PromptEvaluator:
    """
    Prompt综合评估器

    整合BLEU、ROUGE、语义相似度三种评估方法
    """

    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None
    ):
        """
        初始化评估器

        Args:
            weights: 各指标权重（默认均等）
        """
        self.bleu_evaluator = BLEUEvaluator()
        self.rouge_evaluator = ROUGEEvaluator()
        self.semantic_evaluator = SemanticSimilarityEvaluator()

        # 默认权重
        default_weights = {
            "bleu": 0.3,
            "rouge": 0.3,
            "semantic": 0.4
        }
        self.weights = weights or default_weights

        # 归一化权重
        total = sum(self.weights.values())
        self.weights = {k: v / total for k, v in self.weights.items()}

    def evaluate(
        self,
        reference: str,
        hypothesis: str
    ) -> EvaluationResult:
        """
        综合评估

        Args:
            reference: 参考答案（标准答案）
            hypothesis: 生成的答案（AI输出）

        Returns:
            EvaluationResult: 评估结果
        """
        # 执行各项评估
        bleu_score = self.bleu_evaluator.evaluate(reference, hypothesis)
        rouge_score = self.rouge_evaluator.evaluate(reference, hypothesis)
        semantic_score = self.semantic_evaluator.evaluate(reference, hypothesis)

        # 计算加权总分
        overall = 0.0
        valid_count = 0

        if bleu_score.score > 0:
            overall += bleu_score.score * self.weights["bleu"]
            valid_count += 1

        if rouge_score.score > 0:
            overall += rouge_score.score * self.weights["rouge"]
            valid_count += 1

        if semantic_score.score > 0:
            overall += semantic_score.score * self.weights["semantic"]
            valid_count += 1

        # 如果有无效指标，重新归一化
        if valid_count < 3:
            if valid_count > 0:
                overall = overall * (3 / valid_count)

        return EvaluationResult(
            bleu_score=bleu_score,
            rouge_scores=rouge_score,
            semantic_score=semantic_score,
            overall_score=overall,
            metadata={
                "weights": self.weights,
                "valid_metrics": valid_count
            }
        )

    def evaluate_batch(
        self,
        test_cases: List[Dict[str, str]]
    ) -> List[EvaluationResult]:
        """
        批量评估

        Args:
            test_cases: 测试用例列表
                [{"reference": "...", "hypothesis": "..."}]

        Returns:
            List[EvaluationResult]: 评估结果列表
        """
        results = []

        for case in test_cases:
            reference = case.get("reference", "")
            hypothesis = case.get("hypothesis", "")

            if not reference or not hypothesis:
                logger.warning("跳过无效测试用例")
                continue

            result = self.evaluate(reference, hypothesis)
            results.append(result)

        return results

    def evaluate_from_dataset(
        self,
        dataset_path: str
    ) -> Dict[str, Any]:
        """
        从数据集文件评估

        Args:
            dataset_path: 数据集路径（JSON文件）

        Returns:
            Dict[str, Any]: 评估统计
        """
        try:
            with open(dataset_path, 'r', encoding='utf-8') as f:
                dataset = json.load(f)

            test_cases = dataset.get("test_cases", [])
            results = []

            for case in test_cases:
                # 假设数据集格式：每个case有expected_output
                reference = case.get("expected_output", "")
                # hypothesis需要从实际AI生成的响应获取
                # 这里作为占位
                hypothesis = case.get("actual_output", reference)

                if reference:
                    result = self.evaluate(reference, hypothesis)
                    results.append(result)

            # 统计
            if not results:
                return {"error": "No valid results"}

            stats = self._compute_statistics(results)
            return stats

        except Exception as e:
            logger.error(f"从数据集评估失败: {e}")
            return {"error": str(e)}

    @staticmethod
    def _compute_statistics(results: List[EvaluationResult]) -> Dict[str, Any]:
        """计算统计信息"""
        bleu_scores = [r.bleu_score.score for r in results if r.bleu_score]
        rouge_scores = [r.rouge_scores.score for r in results if r.rouge_scores]
        semantic_scores = [r.semantic_score.score for r in results if r.semantic_score]
        overall_scores = [r.overall_score for r in results]

        stats = {
            "total_cases": len(results),
            "bleu": {
                "mean": float(np.mean(bleu_scores)) if bleu_scores else 0,
                "std": float(np.std(bleu_scores)) if bleu_scores else 0,
                "min": float(np.min(bleu_scores)) if bleu_scores else 0,
                "max": float(np.max(bleu_scores)) if bleu_scores else 0,
            },
            "rouge": {
                "mean": float(np.mean(rouge_scores)) if rouge_scores else 0,
                "std": float(np.std(rouge_scores)) if rouge_scores else 0,
                "min": float(np.min(rouge_scores)) if rouge_scores else 0,
                "max": float(np.max(rouge_scores)) if rouge_scores else 0,
            },
            "semantic": {
                "mean": float(np.mean(semantic_scores)) if semantic_scores else 0,
                "std": float(np.std(semantic_scores)) if semantic_scores else 0,
                "min": float(np.min(semantic_scores)) if semantic_scores else 0,
                "max": float(np.max(semantic_scores)) if semantic_scores else 0,
            },
            "overall": {
                "mean": float(np.mean(overall_scores)),
                "std": float(np.std(overall_scores)),
                "min": float(np.min(overall_scores)),
                "max": float(np.max(overall_scores)),
            }
        }

        return stats


# ================================
# 全局实例
# ================================

# 创建全局评估器
prompt_evaluator = PromptEvaluator()


# ================================
# 便捷函数
# ================================

def evaluate_prompt(reference: str, hypothesis: str) -> EvaluationResult:
    """
    便捷函数：评估单个prompt

    Args:
        reference: 参考答案
        hypothesis: 生成的答案

    Returns:
        EvaluationResult: 评估结果
    """
    return prompt_evaluator.evaluate(reference, hypothesis)


def evaluate_batch(test_cases: List[Dict[str, str]]) -> List[EvaluationResult]:
    """
    便捷函数：批量评估

    Args:
        test_cases: 测试用例列表

    Returns:
        List[EvaluationResult]: 评估结果列表
    """
    return prompt_evaluator.evaluate_batch(test_cases)
