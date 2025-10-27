"""
相关问题推荐服务（任务 8.7）

基于用户查询和回答内容，智能推荐相关问题
"""
from typing import List, Dict, Any, Optional
import random

from app.services.prompt_enhancer import QueryType, detect_query_type


# ================================
# 问题推荐规则库
# ================================

# 基于查询类型的推荐问题模板
QUESTION_TEMPLATES = {
    QueryType.PRICE: [
        "{symbol}的历史最高价是多少？",
        "{symbol}适合现在买入吗？",
        "{symbol}的价格支撑位和阻力位在哪里？",
        "{symbol}未来一周的价格预测如何？",
        "影响{symbol}价格的主要因素有哪些？",
        "{symbol}的交易量趋势如何？",
        "{symbol}相比昨天涨了还是跌了？",
        "{symbol}的市值排名是第几？",
    ],

    QueryType.TECHNICAL_ANALYSIS: [
        "{symbol}的MACD指标显示什么信号？",
        "{symbol}的RSI指标是超买还是超卖？",
        "{symbol}的布林带走势如何？",
        "{symbol}有哪些重要的技术指标？",
        "{symbol}的成交量变化说明什么？",
        "{symbol}是否突破了关键阻力位？",
        "{symbol}的移动平均线呈现什么形态？",
        "{symbol}适合短线还是长线投资？",
    ],

    QueryType.SENTIMENT: [
        "{symbol}社区最近在讨论什么？",
        "{symbol}的Twitter热度如何？",
        "{symbol}最近有什么重大新闻？",
        "市场对{symbol}的看法是乐观还是悲观？",
        "{symbol}的Reddit讨论活跃度怎么样？",
        "{symbol}的开发团队活跃吗？",
        "{symbol}最近有没有负面消息？",
        "KOL对{symbol}的评价如何？",
    ],

    QueryType.RISK_ASSESSMENT: [
        "{symbol}有哪些主要风险？",
        "{symbol}的合约是否经过审计？",
        "{symbol}是否有rug pull风险？",
        "{symbol}的流动性如何？",
        "{symbol}的代币分配是否合理？",
        "{symbol}项目方的背景可靠吗？",
        "{symbol}是否存在安全漏洞？",
        "投资{symbol}需要注意什么？",
    ],

    QueryType.TOKENOMICS: [
        "{symbol}的总供应量是多少？",
        "{symbol}是通胀还是通缩模型？",
        "{symbol}的代币销毁机制如何？",
        "{symbol}的质押奖励是多少？",
        "{symbol}的代币解锁计划是什么？",
        "{symbol}的经济模型可持续吗？",
        "{symbol}的流通量占总量的比例？",
        "{symbol}有哪些代币使用场景？",
    ],

    QueryType.GENERAL: [
        "{symbol}是什么项目？",
        "{symbol}的主要功能是什么？",
        "{symbol}和{competitor}有什么区别？",
        "{symbol}的发展路线图是什么？",
        "{symbol}的团队背景如何？",
        "{symbol}的生态系统有哪些应用？",
        "{symbol}适合长期持有吗？",
        "{symbol}的竞争优势是什么？",
    ],
}

# 跨类型通用推荐（任何查询都可能感兴趣）
UNIVERSAL_QUESTIONS = [
    "{symbol}最近有什么重大更新？",
    "比较{symbol}和{competitor}",
    "{symbol}的未来发展前景如何？",
    "{symbol}适合什么样的投资者？",
    "分析{symbol}的优势和劣势",
]

# 竞品映射（用于生成对比问题）
COMPETITOR_MAP = {
    "BTC": ["ETH", "BNB"],
    "ETH": ["BTC", "SOL"],
    "BNB": ["ETH", "MATIC"],
    "SOL": ["ETH", "AVAX"],
    "DOGE": ["SHIB", "PEPE"],
    "XRP": ["XLM", "ADA"],
    "ADA": ["ETH", "DOT"],
    "MATIC": ["ARB", "OP"],
    "DOT": ["ATOM", "AVAX"],
}

# 深度话题推荐（基于已回答内容的深入问题）
DEEP_DIVE_QUESTIONS = {
    "price_increase": [
        "{symbol}价格上涨的原因是什么？",
        "{symbol}的上涨趋势能持续吗？",
        "现在是{symbol}的高点吗？",
    ],
    "price_decrease": [
        "{symbol}价格下跌的原因是什么？",
        "{symbol}何时会止跌反弹？",
        "现在是{symbol}的抄底机会吗？",
    ],
    "high_volume": [
        "{symbol}交易量暴增说明什么？",
        "大户是在买入还是卖出{symbol}？",
    ],
    "positive_sentiment": [
        "{symbol}的正面情绪能推动价格吗？",
        "社区对{symbol}的预期是什么？",
    ],
    "negative_sentiment": [
        "{symbol}的负面消息有多严重？",
        "市场对{symbol}的担忧是否合理？",
    ],
    "high_risk": [
        "如何降低投资{symbol}的风险？",
        "{symbol}有哪些风险管理策略？",
    ],
}


# ================================
# 问题推荐引擎
# ================================

class QuestionRecommender:
    """
    相关问题推荐引擎

    功能：
    1. 基于查询类型的规则推荐
    2. 动态生成个性化问题
    3. 根据回答内容推荐深度问题
    """

    def __init__(self):
        """初始化问题推荐器"""
        self.templates = QUESTION_TEMPLATES
        self.universal = UNIVERSAL_QUESTIONS
        self.deep_dive = DEEP_DIVE_QUESTIONS
        self.competitor_map = COMPETITOR_MAP

    def recommend_questions(
        self,
        query: str,
        symbol: str,
        query_type: Optional[QueryType] = None,
        answer_metadata: Optional[Dict[str, Any]] = None,
        max_questions: int = 5,
    ) -> List[str]:
        """
        推荐相关问题

        Args:
            query: 用户原始查询
            symbol: 币种符号
            query_type: 查询类型（可选，会自动检测）
            answer_metadata: 回答的元数据（用于生成深度问题）
            max_questions: 最多推荐问题数

        Returns:
            List[str]: 推荐的问题列表
        """
        # 检测查询类型
        if not query_type:
            query_type = detect_query_type(query)

        # 收集候选问题
        candidates = []

        # 1. 基于查询类型的问题（权重最高）
        type_questions = self._get_type_based_questions(symbol, query_type)
        candidates.extend([(q, 3) for q in type_questions])

        # 2. 通用推荐问题（权重中等）
        universal_questions = self._get_universal_questions(symbol)
        candidates.extend([(q, 2) for q in universal_questions])

        # 3. 深度话题问题（基于回答内容，权重高）
        if answer_metadata:
            deep_questions = self._get_deep_dive_questions(symbol, answer_metadata)
            candidates.extend([(q, 4) for q in deep_questions])

        # 去重（保留权重最高的）
        unique_candidates = {}
        for question, weight in candidates:
            if question not in unique_candidates or unique_candidates[question] < weight:
                unique_candidates[question] = weight

        # 按权重排序
        sorted_questions = sorted(
            unique_candidates.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # 提取问题文本
        recommended = [q for q, _ in sorted_questions[:max_questions]]

        # 如果不足，补充随机问题
        if len(recommended) < max_questions:
            all_templates = (
                self.templates.get(query_type, []) +
                self.universal
            )
            random_questions = random.sample(
                [t.format(symbol=symbol.upper(), competitor="主流币") for t in all_templates],
                min(max_questions - len(recommended), len(all_templates))
            )
            recommended.extend(random_questions)

        return recommended[:max_questions]

    def _get_type_based_questions(
        self,
        symbol: str,
        query_type: QueryType
    ) -> List[str]:
        """
        获取基于查询类型的推荐问题

        Args:
            symbol: 币种符号
            query_type: 查询类型

        Returns:
            List[str]: 问题列表
        """
        templates = self.templates.get(query_type, [])

        # 随机选择3-4个模板
        num_questions = min(4, len(templates))
        selected_templates = random.sample(templates, num_questions)

        # 填充符号
        questions = [
            t.format(symbol=symbol.upper(), competitor=self._get_competitor(symbol))
            for t in selected_templates
        ]

        return questions

    def _get_universal_questions(self, symbol: str) -> List[str]:
        """
        获取通用推荐问题

        Args:
            symbol: 币种符号

        Returns:
            List[str]: 问题列表
        """
        # 随机选择1-2个通用问题
        num_questions = min(2, len(self.universal))
        selected = random.sample(self.universal, num_questions)

        return [
            q.format(symbol=symbol.upper(), competitor=self._get_competitor(symbol))
            for q in selected
        ]

    def _get_deep_dive_questions(
        self,
        symbol: str,
        metadata: Dict[str, Any]
    ) -> List[str]:
        """
        基于回答元数据生成深度问题

        Args:
            symbol: 币种符号
            metadata: 回答元数据

        Returns:
            List[str]: 深度问题列表
        """
        questions = []

        # 分析市场数据
        market_data = metadata.get("market_data", {})

        if market_data:
            # 价格变化
            price_change_24h = market_data.get("price_change_24h", 0)
            if price_change_24h > 5:
                topic_questions = self.deep_dive.get("price_increase", [])
                questions.extend([q.format(symbol=symbol.upper()) for q in topic_questions[:2]])
            elif price_change_24h < -5:
                topic_questions = self.deep_dive.get("price_decrease", [])
                questions.extend([q.format(symbol=symbol.upper()) for q in topic_questions[:2]])

            # 交易量
            volume = market_data.get("total_volume_24h", 0)
            if volume > 1000000000:  # 10亿美元
                topic_questions = self.deep_dive.get("high_volume", [])
                questions.extend([q.format(symbol=symbol.upper()) for q in topic_questions[:1]])

        # 分析社交情绪
        social_data = metadata.get("social_data", {})
        if social_data:
            sentiment = social_data.get("overall_sentiment", 0)
            if sentiment > 0.7:
                topic_questions = self.deep_dive.get("positive_sentiment", [])
                questions.extend([q.format(symbol=symbol.upper()) for q in topic_questions[:1]])
            elif sentiment < 0.3:
                topic_questions = self.deep_dive.get("negative_sentiment", [])
                questions.extend([q.format(symbol=symbol.upper()) for q in topic_questions[:1]])

        # 分析风险
        risk_level = metadata.get("risk_level")
        if risk_level and risk_level.lower() in ["high", "extreme"]:
            topic_questions = self.deep_dive.get("high_risk", [])
            questions.extend([q.format(symbol=symbol.upper()) for q in topic_questions[:1]])

        return questions

    def _get_competitor(self, symbol: str) -> str:
        """
        获取竞品代币

        Args:
            symbol: 币种符号

        Returns:
            str: 竞品符号
        """
        symbol_upper = symbol.upper()
        competitors = self.competitor_map.get(symbol_upper, ["BTC", "ETH"])
        return random.choice(competitors)

    def format_recommendations(
        self,
        questions: List[str],
        format_style: str = "numbered"
    ) -> str:
        """
        格式化推荐问题为文本

        Args:
            questions: 问题列表
            format_style: 格式风格（numbered/bulleted/inline）

        Returns:
            str: 格式化后的文本
        """
        if not questions:
            return ""

        if format_style == "numbered":
            # 编号列表
            formatted = "\n\n💡 **您可能还想了解：**\n"
            for i, q in enumerate(questions, 1):
                formatted += f"{i}. {q}\n"
            return formatted

        elif format_style == "bulleted":
            # 项目符号
            formatted = "\n\n💡 **您可能还想了解：**\n"
            for q in questions:
                formatted += f"• {q}\n"
            return formatted

        elif format_style == "inline":
            # 行内格式
            return "\n\n💡 **您可能还想了解：** " + " | ".join(questions)

        else:
            # 默认编号
            return self.format_recommendations(questions, "numbered")


# ================================
# 全局实例
# ================================

question_recommender = QuestionRecommender()


# ================================
# 便捷函数
# ================================

def get_recommended_questions(
    query: str,
    symbol: str,
    answer_metadata: Optional[Dict[str, Any]] = None,
    max_questions: int = 5,
) -> List[str]:
    """
    便捷函数：获取推荐问题

    Args:
        query: 用户查询
        symbol: 币种符号
        answer_metadata: 回答元数据
        max_questions: 最多推荐问题数

    Returns:
        List[str]: 推荐问题列表
    """
    return question_recommender.recommend_questions(
        query=query,
        symbol=symbol,
        answer_metadata=answer_metadata,
        max_questions=max_questions,
    )


def format_recommended_questions(
    query: str,
    symbol: str,
    answer_metadata: Optional[Dict[str, Any]] = None,
    max_questions: int = 5,
    format_style: str = "numbered",
) -> str:
    """
    便捷函数：获取并格式化推荐问题

    Args:
        query: 用户查询
        symbol: 币种符号
        answer_metadata: 回答元数据
        max_questions: 最多推荐问题数
        format_style: 格式风格

    Returns:
        str: 格式化的推荐问题文本
    """
    questions = get_recommended_questions(query, symbol, answer_metadata, max_questions)
    return question_recommender.format_recommendations(questions, format_style)
