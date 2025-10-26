"""
报告质量验证器
验证生成的报告是否符合质量标准
"""
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import re


class ReportQualityValidator:
    """
    报告质量验证器

    评分标准（0-100分）：
    - 内容完整性（40分）：所有必需章节是否存在
    - 数据质量（30分）：数据源数量、数据新鲜度
    - 结构规范（20分）：Markdown格式、章节顺序
    - 内容深度（10分）：分析深度、字数
    """

    # 必需章节（Deep Research）
    REQUIRED_SECTIONS_DEEP = [
        "tldr",
        "timeframe",
        "sentiment",
        "technical",
        "onchain",
        "competitor",
        "tokenomics",
        "risk",
        "conclusion"
    ]

    # 必需数据源
    REQUIRED_DATA_SOURCES = ["CoinGecko", "Twitter", "Reddit"]

    # 最小字数
    MIN_WORD_COUNT = 1000

    # 最小数据源数量
    MIN_DATA_SOURCES = 3

    def __init__(self):
        """初始化验证器"""
        pass

    def validate_report(
        self,
        markdown_content: str,
        sections: Optional[Dict[str, Any]] = None,
        data_sources: Optional[List[str]] = None,
        report_type: str = "deep_research",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[int, Dict[str, Any]]:
        """
        验证报告质量并打分

        Args:
            markdown_content: Markdown 格式的报告内容
            sections: 报告章节数据（JSON）
            data_sources: 数据来源列表
            report_type: 报告类型
            metadata: 元数据（生成时间、token使用等）

        Returns:
            Tuple[int, Dict[str, Any]]: (质量得分 0-100, 详细评分)
        """
        scores = {}

        # 1. 内容完整性（40分）
        completeness_score = self._validate_completeness(
            markdown_content, sections, report_type
        )
        scores["completeness"] = completeness_score

        # 2. 数据质量（30分）
        data_quality_score = self._validate_data_quality(
            data_sources, metadata
        )
        scores["data_quality"] = data_quality_score

        # 3. 结构规范（20分）
        structure_score = self._validate_structure(markdown_content)
        scores["structure"] = structure_score

        # 4. 内容深度（10分）
        depth_score = self._validate_depth(markdown_content, sections)
        scores["depth"] = depth_score

        # 计算总分
        total_score = sum(scores.values())

        # 添加详细信息
        details = {
            "total_score": total_score,
            "breakdown": scores,
            "grade": self._get_grade(total_score),
            "issues": self._collect_issues(scores),
            "recommendations": self._get_recommendations(scores),
            "validated_at": datetime.utcnow().isoformat()
        }

        return int(total_score), details

    def _validate_completeness(
        self,
        markdown_content: str,
        sections: Optional[Dict[str, Any]],
        report_type: str
    ) -> float:
        """
        验证内容完整性（40分）

        检查：
        - 必需章节是否存在
        - 每个章节是否有内容
        - 关键数据是否缺失
        """
        score = 0.0
        max_score = 40.0

        # Quick Chat 只需要简单检查
        if report_type == "quick_chat":
            if len(markdown_content) > 200:
                return max_score
            else:
                return max_score * 0.5

        # Deep Research 需要详细检查
        required_sections = self.REQUIRED_SECTIONS_DEEP

        if sections:
            # 基于 sections JSON 检查
            present_sections = [k for k in sections.keys() if sections[k]]
            missing_sections = set(required_sections) - set(present_sections)

            # 每个章节约 4.4 分
            score_per_section = max_score / len(required_sections)
            score = (len(required_sections) - len(missing_sections)) * score_per_section

        else:
            # 基于 Markdown 内容检查
            score = self._check_markdown_sections(markdown_content, required_sections, max_score)

        return round(score, 2)

    def _check_markdown_sections(
        self,
        markdown_content: str,
        required_sections: List[str],
        max_score: float
    ) -> float:
        """通过 Markdown 标题检查章节"""
        score = 0.0
        score_per_section = max_score / len(required_sections)

        # 提取所有 ## 标题
        section_headers = re.findall(r'^## (.+)$', markdown_content, re.MULTILINE)

        # 映射标题到章节名
        section_mapping = {
            "TL;DR": "tldr",
            "TL DR": "tldr",
            "摘要": "tldr",
            "时间框架分析": "timeframe",
            "多时间周期分析": "timeframe",
            "社交情绪分析": "sentiment",
            "情绪分析": "sentiment",
            "技术分析": "technical",
            "链上数据": "onchain",
            "链上分析": "onchain",
            "竞品对比": "competitor",
            "竞争分析": "competitor",
            "代币经济学": "tokenomics",
            "Token经济": "tokenomics",
            "风险评估": "risk",
            "风险分析": "risk",
            "投资结论": "conclusion",
            "总结": "conclusion",
        }

        # 检查每个必需章节
        for required in required_sections:
            # 查找对应的标题
            found = False
            for header in section_headers:
                if required in section_mapping.values() and section_mapping.get(header.strip()) == required:
                    found = True
                    break
                # 模糊匹配
                if required in header.lower().replace(" ", "").replace("_", ""):
                    found = True
                    break

            if found:
                score += score_per_section

        return round(score, 2)

    def _validate_data_quality(
        self,
        data_sources: Optional[List[str]],
        metadata: Optional[Dict[str, Any]]
    ) -> float:
        """
        验证数据质量（30分）

        检查：
        - 数据源数量（15分）
        - 数据新鲜度（10分）
        - 必需数据源（5分）
        """
        score = 0.0

        # 1. 数据源数量（15分）
        if data_sources:
            source_count = len(data_sources)
            if source_count >= 5:
                score += 15.0
            elif source_count >= self.MIN_DATA_SOURCES:
                score += 10.0
            elif source_count >= 1:
                score += 5.0

        # 2. 数据新鲜度（10分）- 基于生成时间
        if metadata:
            generation_time = metadata.get("generation_time_seconds", 0)
            # 生成时间在合理范围内（5-60秒）认为数据新鲜
            if 5 <= generation_time <= 60:
                score += 10.0
            elif generation_time > 0:
                score += 5.0

        # 3. 必需数据源（5分）
        if data_sources:
            required_present = sum(
                1 for req in self.REQUIRED_DATA_SOURCES
                if any(req.lower() in src.lower() for src in data_sources)
            )
            score += (required_present / len(self.REQUIRED_DATA_SOURCES)) * 5.0

        return round(score, 2)

    def _validate_structure(self, markdown_content: str) -> float:
        """
        验证结构规范（20分）

        检查：
        - Markdown 格式正确性（10分）
        - 章节顺序合理（5分）
        - 无格式错误（5分）
        """
        score = 0.0

        # 1. Markdown 格式（10分）
        # 检查是否有标题
        if re.search(r'^# .+', markdown_content, re.MULTILINE):
            score += 3.0

        # 检查是否有二级标题
        if re.search(r'^## .+', markdown_content, re.MULTILINE):
            score += 3.0

        # 检查是否有列表
        if re.search(r'^\- .+', markdown_content, re.MULTILINE) or \
           re.search(r'^\* .+', markdown_content, re.MULTILINE):
            score += 2.0

        # 检查是否有粗体或强调
        if re.search(r'\*\*.+\*\*', markdown_content) or \
           re.search(r'__.+__', markdown_content):
            score += 2.0

        # 2. 章节顺序（5分）
        # 检查 TL;DR 是否在开头附近
        tldr_match = re.search(r'## (TL;DR|TL DR|摘要)', markdown_content)
        if tldr_match and tldr_match.start() < len(markdown_content) * 0.2:
            score += 5.0

        # 3. 无格式错误（5分）
        # 检查是否有未闭合的粗体、代码块等
        if markdown_content.count('**') % 2 == 0 and \
           markdown_content.count('```') % 2 == 0:
            score += 5.0

        return round(score, 2)

    def _validate_depth(
        self,
        markdown_content: str,
        sections: Optional[Dict[str, Any]]
    ) -> float:
        """
        验证内容深度（10分）

        检查：
        - 字数（5分）
        - 分析深度（3分）
        - 数据表格/图表（2分）
        """
        score = 0.0

        # 1. 字数（5分）
        word_count = len(markdown_content)
        if word_count >= 5000:
            score += 5.0
        elif word_count >= 3000:
            score += 4.0
        elif word_count >= self.MIN_WORD_COUNT:
            score += 3.0
        elif word_count >= 500:
            score += 1.0

        # 2. 分析深度（3分）
        # 检查是否有数据、百分比、趋势分析
        if re.search(r'\d+%', markdown_content):  # 百分比
            score += 1.0
        if re.search(r'\$[\d,]+', markdown_content):  # 价格数据
            score += 1.0
        if re.search(r'(上涨|下跌|增长|下降|趋势|变化)', markdown_content):  # 趋势分析
            score += 1.0

        # 3. 数据表格/图表（2分）
        if '|' in markdown_content and '---' in markdown_content:  # Markdown 表格
            score += 1.0
        if re.search(r'!\[.+\]\(.+\)', markdown_content):  # 图片/图表
            score += 1.0

        return round(score, 2)

    def _get_grade(self, total_score: float) -> str:
        """获取等级"""
        if total_score >= 90:
            return "A"
        elif total_score >= 80:
            return "B"
        elif total_score >= 70:
            return "C"
        elif total_score >= 60:
            return "D"
        else:
            return "F"

    def _collect_issues(self, scores: Dict[str, float]) -> List[str]:
        """收集质量问题"""
        issues = []

        if scores["completeness"] < 30:
            issues.append("内容完整性不足：缺少必需章节")

        if scores["data_quality"] < 20:
            issues.append("数据质量较低：数据源不足或数据不够新鲜")

        if scores["structure"] < 15:
            issues.append("结构规范性不足：Markdown 格式不规范")

        if scores["depth"] < 7:
            issues.append("内容深度不够：字数不足或分析不够深入")

        return issues

    def _get_recommendations(self, scores: Dict[str, float]) -> List[str]:
        """获取改进建议"""
        recommendations = []

        if scores["completeness"] < 35:
            recommendations.append("补充缺失的章节，确保所有必需分析都包含")

        if scores["data_quality"] < 25:
            recommendations.append("增加数据源，使用更多平台的数据进行分析")

        if scores["structure"] < 18:
            recommendations.append("规范 Markdown 格式，确保章节顺序合理")

        if scores["depth"] < 8:
            recommendations.append("增加内容深度，添加更多数据分析和趋势解读")

        return recommendations


# ================================
# 辅助函数
# ================================

def validate_markdown_syntax(markdown_content: str) -> Dict[str, Any]:
    """
    验证 Markdown 语法

    Returns:
        Dict: {
            "valid": bool,
            "errors": List[str],
            "warnings": List[str]
        }
    """
    errors = []
    warnings = []

    # 检查未闭合的粗体
    if markdown_content.count('**') % 2 != 0:
        errors.append("存在未闭合的粗体标记 **")

    # 检查未闭合的代码块
    if markdown_content.count('```') % 2 != 0:
        errors.append("存在未闭合的代码块标记 ```")

    # 检查未闭合的斜体
    if markdown_content.count('*') % 2 != 0:
        warnings.append("存在未闭合的斜体标记 *")

    # 检查标题层级
    lines = markdown_content.split('\n')
    prev_level = 0
    for i, line in enumerate(lines):
        if line.startswith('#'):
            level = len(line) - len(line.lstrip('#'))
            if level - prev_level > 1:
                warnings.append(f"第 {i+1} 行：标题层级跳跃过大")
            prev_level = level

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }


def estimate_reading_time(markdown_content: str) -> int:
    """
    估算阅读时间（分钟）

    假设：
    - 中文：200字/分钟
    - 英文：200单词/分钟
    """
    # 移除 Markdown 标记
    text = re.sub(r'[#*`\[\]()!]', '', markdown_content)

    # 统计中文字符数
    chinese_chars = len(re.findall(r'[\u4e00-\u9fa5]', text))

    # 统计英文单词数
    english_words = len(re.findall(r'\b[a-zA-Z]+\b', text))

    # 计算阅读时间
    reading_time = (chinese_chars / 200) + (english_words / 200)

    return max(1, int(reading_time))


# ================================
# 全局实例
# ================================

quality_validator = ReportQualityValidator()
