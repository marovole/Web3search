"""
响应格式化服务（任务 8.4-8.5）

提供响应增强功能：
1. 用户友好的错误消息转换
2. 数据源引用注入
3. 答案质量评分（任务 8.6）
"""
import re
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum


# ================================
# 错误类型和消息映射（任务 8.4）
# ================================


class ErrorType(str, Enum):
    """错误类型枚举"""
    API_ERROR = "api_error"
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    DATA_NOT_FOUND = "data_not_found"
    VALIDATION_ERROR = "validation_error"
    INTERNAL_ERROR = "internal_error"
    NETWORK_ERROR = "network_error"


# 用户友好的错误消息映射
ERROR_MESSAGES = {
    # API错误
    "api_error": {
        "user_message": "抱歉，我们在获取数据时遇到了一些问题。",
        "suggestion": "请稍后再试，或者换一个问题问我。",
        "emoji": "⚠️"
    },
    "rate_limit": {
        "user_message": "您的请求太频繁了，请稍作休息。",
        "suggestion": "我们限制每分钟10次请求，以确保服务稳定。请等待一会儿再试。",
        "emoji": "🚦"
    },
    "timeout": {
        "user_message": "响应超时了，数据源可能比较慢。",
        "suggestion": "您可以尝试更简单的查询，或者稍后再试。",
        "emoji": "⏱️"
    },
    "data_not_found": {
        "user_message": "抱歉，我没有找到相关的数据。",
        "suggestion": "请检查代币符号是否正确，或者尝试使用全称（如 'Bitcoin' 而不是 'BTC'）。",
        "emoji": "🔍"
    },
    "validation_error": {
        "user_message": "您的请求格式不正确。",
        "suggestion": "请检查输入内容，确保符合要求。",
        "emoji": "❌"
    },
    "internal_error": {
        "user_message": "服务器内部出现了问题。",
        "suggestion": "我们的团队已经收到通知，正在处理。请稍后再试。",
        "emoji": "🔧"
    },
    "network_error": {
        "user_message": "网络连接出现问题。",
        "suggestion": "请检查您的网络连接，或稍后再试。",
        "emoji": "🌐"
    },
}


def format_error_message(
    error_type: str,
    technical_details: Optional[str] = None,
    include_technical: bool = False
) -> Dict[str, Any]:
    """
    格式化错误消息（任务 8.4）

    Args:
        error_type: 错误类型
        technical_details: 技术详情（可选）
        include_technical: 是否包含技术详情

    Returns:
        Dict: 格式化后的错误消息
    """
    error_info = ERROR_MESSAGES.get(error_type, ERROR_MESSAGES["internal_error"])

    formatted = {
        "error": True,
        "emoji": error_info["emoji"],
        "message": error_info["user_message"],
        "suggestion": error_info["suggestion"],
        "timestamp": datetime.utcnow().isoformat(),
    }

    # 如果需要，包含技术详情
    if include_technical and technical_details:
        formatted["technical_details"] = technical_details

    return formatted


# ================================
# 数据源引用（任务 8.5）
# ================================


class DataSource(str, Enum):
    """数据源枚举"""
    COINGECKO = "CoinGecko"
    ETHERSCAN = "Etherscan"
    TWITTER = "Twitter"
    REDDIT = "Reddit"
    CRYPTOPANIC = "CryptoPanic"
    COINMARKETCAP = "CoinMarketCap"
    BLOCKCHAIR = "Blockchair"
    GITHUB = "GitHub"
    UNKNOWN = "Unknown"


def add_data_source_references(
    content: str,
    sources: List[DataSource],
    add_footer: bool = True
) -> str:
    """
    添加数据源引用（任务 8.5）

    Args:
        content: 原始响应内容
        sources: 使用的数据源列表
        add_footer: 是否添加页脚

    Returns:
        str: 添加引用后的内容
    """
    if not sources:
        return content

    # 去重
    unique_sources = list(dict.fromkeys(sources))

    # 构建引用文本
    if len(unique_sources) == 1:
        citation = f"\n\n📊 **数据来源**: {unique_sources[0].value}"
    else:
        source_names = [s.value for s in unique_sources]
        citation = f"\n\n📊 **数据来源**: {', '.join(source_names)}"

    # 添加页脚（如果需要）
    if add_footer:
        updated_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        citation += f"\n🕒 **更新时间**: {updated_time}"

    return content + citation


def extract_data_sources_from_metadata(metadata: Dict[str, Any]) -> List[DataSource]:
    """
    从元数据中提取数据源

    Args:
        metadata: 元数据字典

    Returns:
        List[DataSource]: 数据源列表
    """
    sources = []

    # 从不同字段提取数据源
    if metadata.get("price_data_source"):
        sources.append(DataSource.COINGECKO)

    if metadata.get("onchain_data_source"):
        sources.append(DataSource.ETHERSCAN)

    if metadata.get("social_data_sources"):
        social_sources = metadata["social_data_sources"]
        if "twitter" in social_sources.lower():
            sources.append(DataSource.TWITTER)
        if "reddit" in social_sources.lower():
            sources.append(DataSource.REDDIT)

    if metadata.get("news_data_source"):
        sources.append(DataSource.CRYPTOPANIC)

    return sources


# ================================
# 答案质量评分（任务 8.6）
# ================================


class QualityScore(str, Enum):
    """质量评分枚举"""
    EXCELLENT = "excellent"  # 5星
    GOOD = "good"            # 4星
    FAIR = "fair"            # 3星
    POOR = "poor"            # 2星
    VERY_POOR = "very_poor"  # 1星


def calculate_quality_score(
    content: str,
    metadata: Dict[str, Any],
    sources: List[DataSource]
) -> Dict[str, Any]:
    """
    计算答案质量评分（任务 8.6）

    评分标准：
    1. 数据完整性（30%）：是否有数据支撑
    2. 来源可靠性（30%）：数据源是否可信
    3. 响应时间（20%）：是否在目标时间内
    4. 内容长度（10%）：是否足够详细
    5. 结构化程度（10%）：是否有清晰的结构

    Args:
        content: 响应内容
        metadata: 元数据
        sources: 数据源列表

    Returns:
        Dict: 质量评分结果
    """
    score = 0
    max_score = 100
    reasons = []

    # 1. 数据完整性（30分）
    data_completeness = 0
    if content and len(content) > 50:
        data_completeness += 10
    if metadata.get("symbol"):
        data_completeness += 10
    if metadata.get("market_data"):
        data_completeness += 10

    score += data_completeness
    reasons.append(f"数据完整性: {data_completeness}/30分")

    # 2. 来源可靠性（30分）
    source_reliability = 0
    reliable_sources = {
        DataSource.COINGECKO,
        DataSource.ETHERSCAN,
        DataSource.COINMARKETCAP,
        DataSource.GITHUB
    }

    reliable_count = sum(1 for s in sources if s in reliable_sources)
    source_reliability = min(reliable_count * 10, 30)

    score += source_reliability
    reasons.append(f"来源可靠性: {source_reliability}/30分")

    # 3. 响应时间（20分）
    response_time_score = 20
    response_time = metadata.get("response_time", 0)

    if response_time <= 3:
        response_time_score = 20  # 优秀
    elif response_time <= 5:
        response_time_score = 15  # 良好
    elif response_time <= 10:
        response_time_score = 10  # 一般
    else:
        response_time_score = 5   # 较慢

    score += response_time_score
    reasons.append(f"响应时间: {response_time_score}/20分 ({response_time:.1f}s)")

    # 4. 内容长度（10分）
    content_length_score = 0
    content_length = len(content)

    if content_length >= 500:
        content_length_score = 10
    elif content_length >= 200:
        content_length_score = 7
    elif content_length >= 100:
        content_length_score = 5
    else:
        content_length_score = 3

    score += content_length_score
    reasons.append(f"内容长度: {content_length_score}/10分 ({content_length}字)")

    # 5. 结构化程度（10分）
    structure_score = 0

    # 检查 Markdown 格式元素
    has_headers = bool(re.search(r'#+\s+', content))
    has_lists = bool(re.search(r'[-*]\s+', content))
    has_bold = bool(re.search(r'\*\*.*?\*\*', content))
    has_code = bool(re.search(r'`.*?`', content))

    structure_elements = sum([has_headers, has_lists, has_bold, has_code])
    structure_score = min(structure_elements * 3, 10)

    score += structure_score
    reasons.append(f"结构化程度: {structure_score}/10分")

    # 计算星级
    if score >= 90:
        quality = QualityScore.EXCELLENT
        stars = 5
    elif score >= 75:
        quality = QualityScore.GOOD
        stars = 4
    elif score >= 60:
        quality = QualityScore.FAIR
        stars = 3
    elif score >= 40:
        quality = QualityScore.POOR
        stars = 2
    else:
        quality = QualityScore.VERY_POOR
        stars = 1

    return {
        "quality_score": score,
        "max_score": max_score,
        "stars": stars,
        "quality_level": quality.value,
        "rating_emoji": "⭐" * stars + "☆" * (5 - stars),
        "score_breakdown": reasons,
    }


# ================================
# 响应格式化主服务
# ================================


class ResponseFormatter:
    """
    响应格式化服务

    提供：
    1. 错误消息格式化
    2. 数据源引用
    3. 质量评分
    """

    def __init__(self):
        """初始化响应格式化器"""
        pass

    def format_success_response(
        self,
        content: str,
        metadata: Dict[str, Any],
        add_sources: bool = True,
        calculate_quality: bool = True
    ) -> Dict[str, Any]:
        """
        格式化成功响应

        Args:
            content: 响应内容
            metadata: 元数据
            add_sources: 是否添加数据源引用
            calculate_quality: 是否计算质量评分

        Returns:
            Dict: 格式化后的响应
        """
        # 提取数据源
        sources = extract_data_sources_from_metadata(metadata)

        # 添加数据源引用
        if add_sources and sources:
            content = add_data_source_references(content, sources, add_footer=True)

        # 构建基础响应
        response = {
            "content": content,
            "metadata": metadata,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # 计算质量评分
        if calculate_quality:
            quality_info = calculate_quality_score(content, metadata, sources)
            response["quality"] = quality_info

        # 添加数据源信息
        if sources:
            response["data_sources"] = [s.value for s in sources]

        return response

    def format_error_response(
        self,
        error_type: str,
        technical_details: Optional[str] = None,
        include_technical: bool = False
    ) -> Dict[str, Any]:
        """
        格式化错误响应

        Args:
            error_type: 错误类型
            technical_details: 技术详情
            include_technical: 是否包含技术详情

        Returns:
            Dict: 格式化后的错误响应
        """
        return format_error_message(error_type, technical_details, include_technical)

    def format_streaming_chunk(
        self,
        content: str,
        is_final: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        格式化流式响应的chunk

        Args:
            content: chunk内容
            is_final: 是否是最后一个chunk
            metadata: 元数据（仅用于最后一个chunk）

        Returns:
            str: 格式化后的chunk
        """
        if not is_final:
            return content

        # 最后一个chunk，添加数据源引用
        if metadata:
            sources = extract_data_sources_from_metadata(metadata)
            if sources:
                content = add_data_source_references(content, sources, add_footer=True)

        return content


# ================================
# 全局实例
# ================================

response_formatter = ResponseFormatter()


# ================================
# 便捷函数
# ================================


def format_quick_chat_response(
    content: str,
    query_type: str,
    symbol: Optional[str] = None,
    response_time: float = 0.0,
    model: str = "unknown"
) -> Dict[str, Any]:
    """
    便捷函数：格式化 Quick Chat 响应

    Args:
        content: 响应内容
        query_type: 查询类型
        symbol: 代币符号
        response_time: 响应时间
        model: 使用的模型

    Returns:
        Dict: 格式化后的响应
    """
    metadata = {
        "query_type": query_type,
        "symbol": symbol,
        "response_time": response_time,
        "model": model,
        "price_data_source": "coingecko" if symbol else None,
    }

    return response_formatter.format_success_response(
        content=content,
        metadata=metadata,
        add_sources=True,
        calculate_quality=True
    )


def format_api_error(
    exception: Exception,
    include_technical: bool = False
) -> Dict[str, Any]:
    """
    便捷函数：从异常格式化错误响应

    Args:
        exception: Python异常对象
        include_technical: 是否包含技术详情

    Returns:
        Dict: 格式化后的错误响应
    """
    # 根据异常类型确定错误类型
    exception_name = exception.__class__.__name__

    error_type_mapping = {
        "TimeoutError": "timeout",
        "HTTPException": "api_error",
        "ValidationError": "validation_error",
        "ConnectionError": "network_error",
    }

    error_type = error_type_mapping.get(exception_name, "internal_error")

    return response_formatter.format_error_response(
        error_type=error_type,
        technical_details=str(exception),
        include_technical=include_technical
    )
