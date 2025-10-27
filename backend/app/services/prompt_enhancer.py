"""
Prompt 增强服务（任务 7.6-7.7）

提供智能 Prompt 增强功能：
1. 查询类型识别
2. 动态 Few-shot 示例选择
3. Chain-of-Thought 思维链引导
"""
import re
from typing import List, Dict, Any, Optional
from enum import Enum

from app.services.prompt_manager import prompt_manager

# ================================
# 查询类型枚举
# ================================


class QueryType(str, Enum):
    """查询类型"""
    PRICE = "price"                         # 价格查询
    TECHNICAL_ANALYSIS = "technical_analysis"  # 技术分析
    SENTIMENT = "sentiment"                 # 情绪分析
    RISK_ASSESSMENT = "risk_assessment"     # 风险评估
    TOKENOMICS = "tokenomics"               # 代币经济学
    GENERAL = "general"                     # 通用查询


# ================================
# 查询类型识别（任务 7.7）
# ================================


# 查询类型关键词映射
QUERY_TYPE_KEYWORDS = {
    QueryType.PRICE: [
        "价格", "price", "多少钱", "多少", "成本", "买入", "卖出", "cost",
        "当前价", "current price", "worth", "值多少"
    ],
    QueryType.TECHNICAL_ANALYSIS: [
        "技术分析", "technical analysis", "走势", "趋势", "trend", "ma", "rsi", "macd",
        "均线", "移动平均", "指标", "indicator", "图表", "chart", "分析",
        "涨", "跌", "上涨", "下跌", "突破", "支撑", "阻力", "support", "resistance"
    ],
    QueryType.SENTIMENT: [
        "情绪", "sentiment", "看法", "opinion", "社区", "community", "讨论", "discussion",
        "热度", "热点", "火", "评价", "口碑", "reputation", "twitter", "reddit",
        "正面", "负面", "乐观", "悲观", "fud", "fomo", "氛围", "atmosphere"
    ],
    QueryType.RISK_ASSESSMENT: [
        "风险", "risk", "安全", "safe", "security", "危险", "danger", "漏洞", "vulnerability",
        "靠谱", "可靠", "reliable", "信任", "trust", "骗局", "scam", "rug pull",
        "审计", "audit", "问题", "问题", "缺陷", "defect"
    ],
    QueryType.TOKENOMICS: [
        "代币", "token", "经济", "economics", "tokenomics", "通胀", "通缩",
        "inflation", "deflation", "供应", "supply", "流通", "circulation",
        "销毁", "burn", "质押", "stake", "分配", "distribution", "解锁", "unlock",
        "释放", "emission", "代币经济", "经济模型"
    ],
}


def detect_query_type(query: str) -> QueryType:
    """
    检测查询类型（基于关键词匹配）

    Args:
        query: 用户查询

    Returns:
        QueryType: 检测到的查询类型
    """
    query_lower = query.lower()

    # 统计每个类型的关键词匹配数
    type_scores = {qt: 0 for qt in QueryType}

    for query_type, keywords in QUERY_TYPE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in query_lower:
                type_scores[query_type] += 1

    # 找到得分最高的类型
    max_score = max(type_scores.values())

    if max_score == 0:
        # 没有匹配到任何关键词，返回通用类型
        return QueryType.GENERAL

    # 返回得分最高的类型
    for query_type, score in type_scores.items():
        if score == max_score:
            return query_type

    return QueryType.GENERAL


# ================================
# Few-shot 示例选择（任务 7.7）
# ================================


def load_few_shot_examples() -> Dict[str, List[Dict[str, Any]]]:
    """
    加载 Few-shot 示例库

    Returns:
        Dict: 按类别组织的示例
    """
    try:
        data = prompt_manager._load_yaml("few_shot_examples.yaml")

        examples = {
            "technical_analysis": data.get("technical_analysis_examples", []),
            "sentiment": data.get("sentiment_analysis_examples", []),
            "risk_assessment": data.get("risk_assessment_examples", []),
            "tokenomics": data.get("tokenomics_examples", []),
        }

        return examples

    except Exception as e:
        print(f"⚠️ 加载 few-shot 示例失败: {e}")
        return {}


def select_few_shot_examples(
    query_type: QueryType,
    max_examples: int = 2
) -> List[Dict[str, Any]]:
    """
    根据查询类型选择相关的 Few-shot 示例

    Args:
        query_type: 查询类型
        max_examples: 最多返回的示例数

    Returns:
        List[Dict]: 选中的示例列表
    """
    # 加载所有示例
    all_examples = load_few_shot_examples()

    # 映射查询类型到示例类别
    type_to_category = {
        QueryType.TECHNICAL_ANALYSIS: "technical_analysis",
        QueryType.SENTIMENT: "sentiment",
        QueryType.RISK_ASSESSMENT: "risk_assessment",
        QueryType.TOKENOMICS: "tokenomics",
    }

    category = type_to_category.get(query_type)

    if not category or category not in all_examples:
        # 没有对应的示例，返回空列表
        return []

    # 获取该类别的示例
    examples = all_examples[category]

    # 返回前 N 个示例
    return examples[:max_examples]


def format_few_shot_examples(examples: List[Dict[str, Any]]) -> str:
    """
    格式化 Few-shot 示例为 Prompt 文本

    Args:
        examples: 示例列表

    Returns:
        str: 格式化后的示例文本
    """
    if not examples:
        return ""

    formatted_parts = ["# 参考示例\n\n以下是一些高质量的分析示例供参考：\n"]

    for i, example in enumerate(examples, 1):
        scenario = example.get("scenario", "")
        user_query = example.get("user_query", "")
        assistant_response = example.get("assistant_response", "")

        formatted_parts.append(f"## 示例 {i}：{scenario}\n")
        formatted_parts.append(f"**用户提问：** {user_query}\n\n")
        formatted_parts.append(f"**AI 回答：**\n{assistant_response}\n\n")
        formatted_parts.append("---\n\n")

    return "".join(formatted_parts)


# ================================
# Chain-of-Thought 引导（任务 7.6）
# ================================


def add_chain_of_thought_guidance(query: str, query_type: QueryType) -> str:
    """
    添加 Chain-of-Thought 思维链引导

    Args:
        query: 用户查询
        query_type: 查询类型

    Returns:
        str: 增强后的查询（带思维链引导）
    """
    # 根据查询类型提供不同的思维链引导
    cot_templates = {
        QueryType.PRICE: """
        请对以下查询进行回答，并使用思维链方法逐步分析：

        用户查询：{query}

        请按照以下步骤回答：
        1. 首先，确定查询的具体代币
        2. 然后，收集当前价格数据
        3. 接着，分析最近的价格变化（24小时、7天）
        4. 最后，总结价格状况并提供数据来源
        """,

        QueryType.TECHNICAL_ANALYSIS: """
        请对以下查询进行技术分析，并使用思维链方法逐步推理：

        用户查询：{query}

        请按照以下步骤分析：
        1. 首先，明确分析的技术指标（MA、RSI、MACD等）
        2. 然后，收集相关的历史价格数据
        3. 接着，计算技术指标并解读信号
        4. 之后，识别关键的支撑位和阻力位
        5. 最后，得出技术面结论和建议
        """,

        QueryType.SENTIMENT: """
        请对以下查询进行情绪分析，并使用思维链方法逐步推理：

        用户查询：{query}

        请按照以下步骤分析：
        1. 首先，明确要分析情绪的代币/项目
        2. 然后，收集社交媒体数据（Twitter、Reddit等）
        3. 接着，统计正面、负面、中性情绪的占比
        4. 之后，识别影响情绪的主要驱动因素
        5. 最后，总结市场情绪状态和趋势
        """,

        QueryType.RISK_ASSESSMENT: """
        请对以下查询进行风险评估，并使用思维链方法逐步推理：

        用户查询：{query}

        请按照以下步骤评估：
        1. 首先，识别项目的主要风险维度（技术、市场、团队、监管、竞争）
        2. 然后，对每个风险维度进行评估（发生概率、影响程度）
        3. 接着，计算单项和综合风险等级
        4. 之后，识别是否有极高风险或多个高风险
        5. 最后，总结风险状况并提供管理建议
        """,

        QueryType.TOKENOMICS: """
        请对以下查询进行代币经济学分析，并使用思维链方法逐步推理：

        用户查询：{query}

        请按照以下步骤分析：
        1. 首先，明确代币的基本信息（总量、流通量）
        2. 然后，分析供应机制（通胀/通缩、销毁/增发）
        3. 接着，评估需求驱动因素（使用场景、价值捕获）
        4. 之后，分析供需平衡和长期可持续性
        5. 最后，总结代币经济模型的优劣势
        """,

        QueryType.GENERAL: """
        请对以下查询进行回答：

        用户查询：{query}

        请先理解查询意图，然后逐步分析并给出清晰、准确的回答。
        """,
    }

    template = cot_templates.get(query_type, cot_templates[QueryType.GENERAL])
    return template.format(query=query).strip()


# ================================
# Prompt 增强主服务
# ================================


class PromptEnhancer:
    """
    Prompt 增强服务

    功能：
    1. 查询类型识别
    2. 动态 Few-shot 示例选择
    3. Chain-of-Thought 引导
    """

    def __init__(self):
        """初始化 Prompt 增强器"""
        pass

    def enhance_prompt(
        self,
        query: str,
        system_prompt: Optional[str] = None,
        include_few_shot: bool = True,
        include_cot: bool = True,
        max_few_shot_examples: int = 2
    ) -> Dict[str, Any]:
        """
        增强用户查询 Prompt

        Args:
            query: 用户查询
            system_prompt: 系统提示词（可选）
            include_few_shot: 是否包含 Few-shot 示例
            include_cot: 是否包含 Chain-of-Thought 引导
            max_few_shot_examples: 最多包含的示例数

        Returns:
            Dict: 增强后的 Prompt 信息
                - enhanced_query: 增强后的查询
                - system_prompt: 系统提示词
                - query_type: 检测到的查询类型
                - few_shot_examples: 使用的示例（如果有）
        """
        # 1. 检测查询类型
        query_type = detect_query_type(query)

        # 2. 选择 Few-shot 示例
        few_shot_examples = []
        few_shot_text = ""

        if include_few_shot:
            few_shot_examples = select_few_shot_examples(query_type, max_few_shot_examples)
            few_shot_text = format_few_shot_examples(few_shot_examples)

        # 3. 添加 Chain-of-Thought 引导
        if include_cot:
            enhanced_query = add_chain_of_thought_guidance(query, query_type)
        else:
            enhanced_query = query

        # 4. 如果有 Few-shot 示例，添加到增强查询之前
        if few_shot_text:
            enhanced_query = few_shot_text + "\n\n" + enhanced_query

        # 5. 使用提供的 system_prompt 或默认的
        if system_prompt is None:
            system_prompt = prompt_manager.get_quick_chat_system_prompt()

        return {
            "enhanced_query": enhanced_query,
            "system_prompt": system_prompt,
            "query_type": query_type.value,
            "few_shot_examples": few_shot_examples,
            "original_query": query,
        }

    def enhance_for_quick_chat(self, query: str) -> Dict[str, Any]:
        """
        为 Quick Chat 模式增强 Prompt

        Args:
            query: 用户查询

        Returns:
            Dict: 增强后的 Prompt
        """
        system_prompt = prompt_manager.get_quick_chat_system_prompt()

        return self.enhance_prompt(
            query=query,
            system_prompt=system_prompt,
            include_few_shot=True,   # Quick Chat 也使用 Few-shot
            include_cot=True,         # Quick Chat 使用简化的 CoT
            max_few_shot_examples=1,  # Quick Chat 只用 1 个示例（更快）
        )

    def enhance_for_deep_research(self, query: str) -> Dict[str, Any]:
        """
        为 Deep Research 模式增强 Prompt

        Args:
            query: 用户查询

        Returns:
            Dict: 增强后的 Prompt
        """
        system_prompt = prompt_manager.get_deep_research_system_prompt()

        return self.enhance_prompt(
            query=query,
            system_prompt=system_prompt,
            include_few_shot=True,   # Deep Research 使用 Few-shot
            include_cot=True,         # Deep Research 使用完整的 CoT
            max_few_shot_examples=2,  # Deep Research 用 2 个示例（更全面）
        )


# ================================
# 全局实例
# ================================

prompt_enhancer = PromptEnhancer()
