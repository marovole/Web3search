"""
语义搜索服务（任务 10.6-10.7）

功能：
1. 示例向量化（sentence-transformers）
2. 语义相似度搜索
3. 动态few-shot选择

注意：sentence-transformers是可选依赖
如果未安装，将回退到简单的关键词匹配
"""
from typing import List, Dict, Any, Optional, Tuple
import logging
from dataclasses import dataclass
import numpy as np

from app.services.few_shot_library import (
    FewShotExample,
    ExampleLibrary,
    ExampleType,
    example_library
)

logger = logging.getLogger(__name__)

# 尝试导入sentence-transformers
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning(
        "sentence-transformers未安装，将使用简单关键词匹配。"
        "安装: pip install sentence-transformers"
    )


# ================================
# 向量化引擎（任务 10.6）
# ================================

class EmbeddingEngine:
    """
    示例向量化引擎

    使用sentence-transformers将文本转换为向量
    """

    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        """
        初始化向量化引擎

        Args:
            model_name: 模型名称（默认：多语言MiniLM）
        """
        self.model_name = model_name
        self.model: Optional[Any] = None

        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                logger.info(f"加载embedding模型: {model_name}")
                self.model = SentenceTransformer(model_name)
                logger.info("Embedding模型加载成功")
            except Exception as e:
                logger.error(f"加载embedding模型失败: {e}")
                self.model = None
        else:
            logger.warning("sentence-transformers不可用，将使用简单匹配")

    def encode(self, text: str) -> Optional[np.ndarray]:
        """
        文本向量化

        Args:
            text: 输入文本

        Returns:
            Optional[np.ndarray]: 向量（如果可用）
        """
        if self.model is None:
            return None

        try:
            # 编码为向量
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding
        except Exception as e:
            logger.error(f"文本向量化失败: {e}")
            return None

    def encode_batch(self, texts: List[str]) -> Optional[np.ndarray]:
        """
        批量文本向量化

        Args:
            texts: 文本列表

        Returns:
            Optional[np.ndarray]: 向量矩阵
        """
        if self.model is None:
            return None

        try:
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            return embeddings
        except Exception as e:
            logger.error(f"批量向量化失败: {e}")
            return None

    def is_available(self) -> bool:
        """检查向量化是否可用"""
        return self.model is not None


# ================================
# 向量索引（任务 10.6）
# ================================

@dataclass
class IndexedExample:
    """带向量的示例"""
    example: FewShotExample
    embedding: Optional[np.ndarray] = None


class ExampleVectorIndex:
    """
    示例向量索引

    存储示例及其向量，支持快速检索
    """

    def __init__(self, embedding_engine: EmbeddingEngine):
        """
        初始化向量索引

        Args:
            embedding_engine: 向量化引擎
        """
        self.embedding_engine = embedding_engine
        self.indexed_examples: List[IndexedExample] = []
        self._index_built = False

    def build_index(self, examples: List[FewShotExample]):
        """
        构建向量索引

        Args:
            examples: 示例列表
        """
        logger.info(f"开始构建向量索引，共{len(examples)}个示例")

        if not self.embedding_engine.is_available():
            # 无向量化能力，仅存储示例
            self.indexed_examples = [
                IndexedExample(example=ex, embedding=None)
                for ex in examples
            ]
            logger.warning("向量化不可用，索引将使用关键词匹配")
            self._index_built = True
            return

        # 批量向量化
        queries = [ex.input_query for ex in examples]
        embeddings = self.embedding_engine.encode_batch(queries)

        if embeddings is None:
            # 向量化失败，回退到无向量模式
            self.indexed_examples = [
                IndexedExample(example=ex, embedding=None)
                for ex in examples
            ]
        else:
            # 创建索引
            self.indexed_examples = [
                IndexedExample(example=ex, embedding=emb)
                for ex, emb in zip(examples, embeddings)
            ]

        self._index_built = True
        logger.info(f"向量索引构建完成，索引大小：{len(self.indexed_examples)}")

    def is_ready(self) -> bool:
        """检查索引是否就绪"""
        return self._index_built


# ================================
# 语义搜索引擎（任务 10.7）
# ================================

class SemanticSearchEngine:
    """
    语义搜索引擎

    基于向量相似度搜索最相关的few-shot示例
    """

    def __init__(
        self,
        example_library: ExampleLibrary,
        embedding_engine: Optional[EmbeddingEngine] = None
    ):
        """
        初始化搜索引擎

        Args:
            example_library: 示例库
            embedding_engine: 向量化引擎（可选）
        """
        self.example_library = example_library

        # 初始化向量化引擎
        if embedding_engine is None:
            self.embedding_engine = EmbeddingEngine()
        else:
            self.embedding_engine = embedding_engine

        # 按类型创建向量索引
        self.indexes: Dict[ExampleType, ExampleVectorIndex] = {}
        self._build_all_indexes()

    def _build_all_indexes(self):
        """构建所有类型的向量索引"""
        for example_type in ExampleType:
            examples = self.example_library.get_examples_by_type(example_type)

            if examples:
                index = ExampleVectorIndex(self.embedding_engine)
                index.build_index(examples)
                self.indexes[example_type] = index
                logger.info(f"构建{example_type.value}索引：{len(examples)}个示例")

    def search(
        self,
        query: str,
        example_type: Optional[ExampleType] = None,
        top_k: int = 3
    ) -> List[FewShotExample]:
        """
        语义搜索最相关的示例

        Args:
            query: 查询文本
            example_type: 示例类型（可选，None则搜索所有）
            top_k: 返回前k个结果

        Returns:
            List[FewShotExample]: 最相关的示例列表
        """
        if example_type:
            # 搜索指定类型
            return self._search_in_type(query, example_type, top_k)
        else:
            # 搜索所有类型
            return self._search_all_types(query, top_k)

    def _search_in_type(
        self,
        query: str,
        example_type: ExampleType,
        top_k: int
    ) -> List[FewShotExample]:
        """在指定类型中搜索"""
        index = self.indexes.get(example_type)
        if not index or not index.is_ready():
            return []

        # 向量化查询
        query_embedding = self.embedding_engine.encode(query)

        if query_embedding is None:
            # 回退到关键词匹配
            return self._keyword_search(query, example_type, top_k)

        # 计算相似度
        similarities = []
        for indexed in index.indexed_examples:
            if indexed.embedding is not None:
                # 余弦相似度
                sim = self._cosine_similarity(query_embedding, indexed.embedding)
                similarities.append((indexed.example, sim))

        # 按相似度排序
        similarities.sort(key=lambda x: x[1], reverse=True)

        # 返回top-k
        return [ex for ex, sim in similarities[:top_k]]

    def _search_all_types(self, query: str, top_k: int) -> List[FewShotExample]:
        """在所有类型中搜索"""
        all_results = []

        for example_type in ExampleType:
            results = self._search_in_type(query, example_type, top_k)
            all_results.extend(results)

        # 如果有向量，重新排序
        if self.embedding_engine.is_available():
            query_embedding = self.embedding_engine.encode(query)
            if query_embedding is not None:
                # 重新计算相似度并排序
                scored = []
                for ex in all_results:
                    # 重新编码示例并计算相似度
                    ex_embedding = self.embedding_engine.encode(ex.input_query)
                    if ex_embedding is not None:
                        sim = self._cosine_similarity(query_embedding, ex_embedding)
                        scored.append((ex, sim))

                scored.sort(key=lambda x: x[1], reverse=True)
                return [ex for ex, sim in scored[:top_k]]

        # 回退：简单返回前k个
        return all_results[:top_k]

    def _keyword_search(
        self,
        query: str,
        example_type: ExampleType,
        top_k: int
    ) -> List[FewShotExample]:
        """关键词匹配搜索（回退方案）"""
        examples = self.example_library.get_examples_by_type(example_type)

        # 简单的关键词重叠计分
        scored = []
        query_words = set(query.lower().split())

        for ex in examples:
            ex_words = set(ex.input_query.lower().split())
            overlap = len(query_words & ex_words)
            scored.append((ex, overlap))

        # 按重叠度排序
        scored.sort(key=lambda x: x[1], reverse=True)

        return [ex for ex, score in scored[:top_k] if score > 0]

    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """
        计算余弦相似度

        Args:
            a: 向量a
            b: 向量b

        Returns:
            float: 相似度（0-1）
        """
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return float(dot_product / (norm_a * norm_b))


# ================================
# 全局实例
# ================================

# 创建全局搜索引擎
semantic_search_engine = SemanticSearchEngine(example_library)


# ================================
# 便捷函数
# ================================

def search_examples(
    query: str,
    example_type: Optional[ExampleType] = None,
    top_k: int = 3
) -> List[FewShotExample]:
    """
    便捷函数：搜索最相关的示例

    Args:
        query: 查询文本
        example_type: 示例类型（可选）
        top_k: 返回数量

    Returns:
        List[FewShotExample]: 最相关的示例
    """
    return semantic_search_engine.search(query, example_type, top_k)
