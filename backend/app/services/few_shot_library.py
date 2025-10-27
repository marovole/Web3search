"""
Few-shot示例库（任务 10.1-10.5, 10.8）

功能：
1. 示例库数据结构定义
2. 示例管理（添加、删除、更新、查询）
3. 示例分类存储（技术分析、情绪、风险、代币经济学）
4. 示例验证和导入/导出
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


# ================================
# 示例类型枚举
# ================================

class ExampleType(str, Enum):
    """Few-shot示例类型"""
    TECHNICAL_ANALYSIS = "technical_analysis"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    RISK_ASSESSMENT = "risk_assessment"
    TOKENOMICS = "tokenomics"
    GENERAL = "general"


# ================================
# 示例数据结构（任务 10.1）
# ================================

@dataclass
class FewShotExample:
    """
    Few-shot示例数据结构

    包含完整的输入-输出对，用于prompt中的示范
    """
    # 基本信息
    id: str
    type: ExampleType
    scenario: str  # 场景描述（如：MA交叉分析、情绪突变检测）

    # 输入输出
    input_query: str  # 输入查询
    expected_output: str  # 期望输出

    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    # 质量指标
    quality_score: float = 5.0  # 1-5分
    usage_count: int = 0  # 使用次数
    success_rate: float = 1.0  # 成功率

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（便于序列化）"""
        data = asdict(self)
        # 转换datetime为ISO格式字符串
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FewShotExample":
        """从字典创建示例"""
        # 转换字符串为datetime
        if isinstance(data.get("created_at"), str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if isinstance(data.get("updated_at"), str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])

        # 转换type为枚举
        if isinstance(data.get("type"), str):
            data["type"] = ExampleType(data["type"])

        return cls(**data)

    def format_for_prompt(self) -> str:
        """
        格式化为prompt中的示例

        Returns:
            str: 格式化后的示例文本
        """
        return f"""### 示例：{self.scenario}

**用户查询**：{self.input_query}

**助手回答**：{self.expected_output}
"""


# ================================
# 示例库管理类
# ================================

class ExampleLibrary:
    """
    Few-shot示例库管理器

    负责示例的存储、检索、管理
    """

    def __init__(self, data_dir: Optional[Path] = None):
        """
        初始化示例库

        Args:
            data_dir: 数据存储目录（默认：app/data/few_shot_examples/）
        """
        if data_dir is None:
            # 默认数据目录
            base_dir = Path(__file__).parent.parent / "data" / "few_shot_examples"
            self.data_dir = base_dir
        else:
            self.data_dir = Path(data_dir)

        # 确保目录存在
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 内存缓存
        self._examples: Dict[str, FewShotExample] = {}
        self._examples_by_type: Dict[ExampleType, List[FewShotExample]] = {
            etype: [] for etype in ExampleType
        }

        # 加载示例
        self._load_all_examples()

    def _load_all_examples(self):
        """加载所有示例到内存"""
        for example_type in ExampleType:
            file_path = self.data_dir / f"{example_type.value}.json"
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        for item in data.get("examples", []):
                            example = FewShotExample.from_dict(item)
                            self._examples[example.id] = example
                            self._examples_by_type[example_type].append(example)

                    logger.info(
                        f"加载示例: {example_type.value} "
                        f"({len(self._examples_by_type[example_type])}个)"
                    )
                except Exception as e:
                    logger.error(f"加载示例失败 {example_type.value}: {e}")

    def add_example(self, example: FewShotExample) -> bool:
        """
        添加示例

        Args:
            example: 要添加的示例

        Returns:
            bool: 是否成功
        """
        try:
            # 添加到内存
            self._examples[example.id] = example
            self._examples_by_type[example.type].append(example)

            # 持久化
            self._save_examples(example.type)

            logger.info(f"添加示例: {example.id} ({example.type.value})")
            return True

        except Exception as e:
            logger.error(f"添加示例失败: {e}")
            return False

    def remove_example(self, example_id: str) -> bool:
        """
        删除示例

        Args:
            example_id: 示例ID

        Returns:
            bool: 是否成功
        """
        if example_id not in self._examples:
            logger.warning(f"示例不存在: {example_id}")
            return False

        try:
            example = self._examples[example_id]
            example_type = example.type

            # 从内存删除
            del self._examples[example_id]
            self._examples_by_type[example_type] = [
                e for e in self._examples_by_type[example_type]
                if e.id != example_id
            ]

            # 持久化
            self._save_examples(example_type)

            logger.info(f"删除示例: {example_id}")
            return True

        except Exception as e:
            logger.error(f"删除示例失败: {e}")
            return False

    def update_example(self, example_id: str, updates: Dict[str, Any]) -> bool:
        """
        更新示例

        Args:
            example_id: 示例ID
            updates: 更新内容

        Returns:
            bool: 是否成功
        """
        if example_id not in self._examples:
            logger.warning(f"示例不存在: {example_id}")
            return False

        try:
            example = self._examples[example_id]

            # 更新字段
            for key, value in updates.items():
                if hasattr(example, key):
                    setattr(example, key, value)

            example.updated_at = datetime.utcnow()

            # 持久化
            self._save_examples(example.type)

            logger.info(f"更新示例: {example_id}")
            return True

        except Exception as e:
            logger.error(f"更新示例失败: {e}")
            return False

    def get_example(self, example_id: str) -> Optional[FewShotExample]:
        """
        获取单个示例

        Args:
            example_id: 示例ID

        Returns:
            Optional[FewShotExample]: 示例对象，不存在返回None
        """
        return self._examples.get(example_id)

    def get_examples_by_type(
        self,
        example_type: ExampleType,
        limit: Optional[int] = None
    ) -> List[FewShotExample]:
        """
        按类型获取示例

        Args:
            example_type: 示例类型
            limit: 限制数量（可选）

        Returns:
            List[FewShotExample]: 示例列表
        """
        examples = self._examples_by_type.get(example_type, [])

        if limit:
            return examples[:limit]
        return examples

    def get_examples_by_tags(
        self,
        tags: List[str],
        match_all: bool = False
    ) -> List[FewShotExample]:
        """
        按标签获取示例

        Args:
            tags: 标签列表
            match_all: 是否匹配所有标签（默认匹配任一）

        Returns:
            List[FewShotExample]: 示例列表
        """
        results = []

        for example in self._examples.values():
            if match_all:
                # 匹配所有标签
                if all(tag in example.tags for tag in tags):
                    results.append(example)
            else:
                # 匹配任一标签
                if any(tag in example.tags for tag in tags):
                    results.append(example)

        return results

    def get_top_quality_examples(
        self,
        example_type: Optional[ExampleType] = None,
        limit: int = 5
    ) -> List[FewShotExample]:
        """
        获取高质量示例

        Args:
            example_type: 示例类型（可选，不指定则全部）
            limit: 限制数量

        Returns:
            List[FewShotExample]: 高质量示例列表
        """
        if example_type:
            examples = self._examples_by_type.get(example_type, [])
        else:
            examples = list(self._examples.values())

        # 按质量评分排序
        sorted_examples = sorted(
            examples,
            key=lambda e: (e.quality_score, e.success_rate),
            reverse=True
        )

        return sorted_examples[:limit]

    def record_usage(self, example_id: str, success: bool = True):
        """
        记录示例使用情况

        Args:
            example_id: 示例ID
            success: 是否成功
        """
        if example_id not in self._examples:
            return

        example = self._examples[example_id]
        example.usage_count += 1

        # 更新成功率（移动平均）
        alpha = 0.1  # 平滑系数
        if success:
            example.success_rate = (1 - alpha) * example.success_rate + alpha * 1.0
        else:
            example.success_rate = (1 - alpha) * example.success_rate + alpha * 0.0

    def _save_examples(self, example_type: ExampleType):
        """
        保存指定类型的示例到文件

        Args:
            example_type: 示例类型
        """
        file_path = self.data_dir / f"{example_type.value}.json"

        examples_data = {
            "type": example_type.value,
            "count": len(self._examples_by_type[example_type]),
            "updated_at": datetime.utcnow().isoformat(),
            "examples": [
                e.to_dict() for e in self._examples_by_type[example_type]
            ]
        }

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(examples_data, f, indent=2, ensure_ascii=False)

    def export_all(self, output_dir: Optional[Path] = None) -> bool:
        """
        导出所有示例

        Args:
            output_dir: 输出目录（默认为当前data_dir）

        Returns:
            bool: 是否成功
        """
        try:
            output_dir = output_dir or self.data_dir
            output_dir.mkdir(parents=True, exist_ok=True)

            for example_type in ExampleType:
                self._save_examples(example_type)

            logger.info(f"导出所有示例到: {output_dir}")
            return True

        except Exception as e:
            logger.error(f"导出失败: {e}")
            return False

    def import_from_file(self, file_path: Path) -> int:
        """
        从文件导入示例

        Args:
            file_path: JSON文件路径

        Returns:
            int: 导入的示例数量
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            count = 0
            for item in data.get("examples", []):
                example = FewShotExample.from_dict(item)
                if self.add_example(example):
                    count += 1

            logger.info(f"从{file_path}导入{count}个示例")
            return count

        except Exception as e:
            logger.error(f"导入失败: {e}")
            return 0

    def validate_example(self, example: FewShotExample) -> List[str]:
        """
        验证示例质量

        Args:
            example: 要验证的示例

        Returns:
            List[str]: 验证错误列表（空列表表示通过）
        """
        errors = []

        # 检查必填字段
        if not example.id:
            errors.append("缺少ID")
        if not example.scenario:
            errors.append("缺少场景描述")
        if not example.input_query:
            errors.append("缺少输入查询")
        if not example.expected_output:
            errors.append("缺少期望输出")

        # 检查长度
        if len(example.input_query) < 5:
            errors.append("输入查询过短")
        if len(example.expected_output) < 20:
            errors.append("期望输出过短")

        # 检查质量评分
        if not (1.0 <= example.quality_score <= 5.0):
            errors.append("质量评分超出范围（1-5）")

        return errors

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取示例库统计信息

        Returns:
            Dict: 统计数据
        """
        stats = {
            "total": len(self._examples),
            "by_type": {},
            "avg_quality": 0.0,
            "total_usage": 0,
        }

        # 按类型统计
        for example_type in ExampleType:
            examples = self._examples_by_type[example_type]
            stats["by_type"][example_type.value] = {
                "count": len(examples),
                "avg_quality": sum(e.quality_score for e in examples) / len(examples)
                if examples else 0.0
            }

        # 全局统计
        if self._examples:
            stats["avg_quality"] = sum(
                e.quality_score for e in self._examples.values()
            ) / len(self._examples)

            stats["total_usage"] = sum(
                e.usage_count for e in self._examples.values()
            )

        return stats


# ================================
# 全局实例
# ================================

example_library = ExampleLibrary()
