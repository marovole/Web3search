"""
情感分析引擎
集成VADER、BERT等多种NLP模型，提供Web3领域专用的情感分析功能
"""
import asyncio
from typing import Dict, Any, List, Optional, Tuple
import re
import jieba
from datetime import datetime

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False
    print("⚠️ VADER未安装，将使用内置情感分析")

try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("⚠️ Transformers未安装，将跳过BERT情感分析")

from app.core.config import settings
from app.core.redis_client import cache_get_json, cache_set


class SentimentAnalyzer:
    """
    多模型情感分析引擎
    支持VADER、BERT等多种模型，专门优化Web3领域情感分析
    """

    def __init__(self):
        """初始化情感分析器"""
        self.vader_analyzer = None
        self.bert_pipeline = None
        self.crypto_keywords = self._load_crypto_keywords()
        self.emoji_sentiment_map = self._load_emoji_sentiment()
        
        # 异步初始化模型
        self._initialized = False

    async def initialize(self):
        """异步初始化模型"""
        if self._initialized:
            return

        # 初始化VADER
        if VADER_AVAILABLE:
            self.vader_analyzer = SentimentIntensityAnalyzer()
            print("✅ VADER情感分析器初始化成功")

        # 初始化BERT模型（如果可用且设置了）
        if TRANSFORMERS_AVAILABLE and settings.ENABLE_BERT_SENTIMENT:
            try:
                # 使用加密货币微调的模型或通用模型
                model_name = "cardiffnlp/twitter-roberta-base-sentiment-latest"
                self.bert_pipeline = pipeline(
                    "sentiment-analysis",
                    model=model_name,
                    tokenizer=model_name,
                    device=0 if settings.USE_GPU else -1
                )
                print("✅ BERT情感分析器初始化成功")
            except Exception as e:
                print(f"⚠️ BERT模型初始化失败: {e}")

        self._initialized = True

    def _load_crypto_keywords(self) -> Dict[str, List[str]]:
        """
        加载Web3领域特定的情感关键词
        
        Returns:
            Dict: 情感关键词字典
        """
        return {
            "bullish": [
                # 价格上涨相关
                "bull", "bullish", "moon", "pump", "pumping", "rocket", "surge", "rally",
                "breakout", "uptrend", "ascending", "climbing", "soaring", "skyrocket",
                "to the moon", "lambo", "wen moon", "🚀", "📈", "🌙",
                # 买入相关
                "buy", "buying", "long", "holding", "hodl", "accumulate", "dip", "dipping",
                # 正面情绪
                "strong", "solid", "excellent", "amazing", "fantastic", "great", "good",
                "profit", "gains", "winning", "successful", "positive", "optimistic",
                # 技术正面
                "adoption", "mainnet", "launch", "upgrade", "scaling", "innovation",
                "partnership", "integration", "defi", "yield", "staking", "airdrop"
            ],
            "bearish": [
                # 价格下跌相关
                "bear", "bearish", "dump", "dumping", "crash", "collapse", "plunge",
                "falling", "dropping", "decline", "downtrend", "descending", "📉", "🕳️",
                # 卖出相关
                "sell", "selling", "short", "shorting", "panic sell", "rekt", "liquidated",
                # 负面情绪
                "bad", "terrible", "awful", "poor", "weak", "negative", "pessimistic",
                "loss", "losing", "failed", "failure", "scam", "shitcoin", "ponzi",
                # 技术负面
                "hack", "exploit", "vulnerability", "bug", "glitch", "downtime",
                "delay", "postponed", "delist", "ban", "regulation", "fud", "fear"
            ],
            "neutral": [
                # 中性分析词汇
                "analysis", "technical", "fundamental", "market", "price", "chart",
                "volume", "resistance", "support", "trend", "correction", "consolidation",
                "accumulation", "distribution", "volatility", "sideways", "stable",
                # 时间和数量
                "today", "tomorrow", "week", "month", "year", "hour", "minute",
                "bitcoin", "ethereum", "btc", "eth", "crypto", "cryptocurrency",
                "blockchain", "token", "coin", "altcoin", "defi", "nft", "metaverse"
            ]
        }

    def _load_emoji_sentiment(self) -> Dict[str, float]:
        """
        加载表情符号的情感权重
        
        Returns:
            Dict: 表情符号情感权重字典
        """
        return {
            # 正面表情 (0.5 到 1.0)
            "🚀": 1.0, "📈": 0.9, "🌙": 0.9, "💰": 0.8, "💎": 0.8,
            "👍": 0.7, "😊": 0.7, "🔥": 0.8, "🌟": 0.7, "✅": 0.6,
            "💪": 0.7, "🏆": 0.8, "🎯": 0.7, "🎉": 0.8, "💯": 0.9,
            
            # 负面表情 (-1.0 到 -0.5)
            "📉": -1.0, "🕳️": -0.9, "👎": -0.7, "😢": -0.6, "⚠️": -0.5,
            "❌": -0.7, "🚫": -0.6, "💔": -0.8, "😡": -0.8, "😠": -0.7,
            
            # 中性表情 (-0.2 到 0.2)
            "🤔": 0.0, "📊": 0.1, "📱": 0.0, "⏰": 0.0, "📌": 0.0,
        }

    async def analyze_text_sentiment(
        self,
        text: str,
        use_vader: bool = True,
        use_bert: bool = True,
        use_keywords: bool = True,
        use_emoji: bool = True
    ) -> Dict[str, Any]:
        """
        分析文本情感

        Args:
            text: 要分析的文本
            use_vader: 是否使用VADER模型
            use_bert: 是否使用BERT模型
            use_keywords: 是否使用关键词分析
            use_emoji: 是否分析表情符号

        Returns:
            Dict: 综合情感分析结果
        """
        if not self._initialized:
            await self.initialize()

        text = self._preprocess_text(text)
        
        results = {
            "text": text[:100] + "..." if len(text) > 100 else text,
            "vader_score": None,
            "bert_score": None,
            "keyword_score": None,
            "emoji_score": None,
            "final_score": 0.0,
            "confidence": 0.0,
            "analysis_details": {}
        }

        # VADER分析
        if use_vader and self.vader_analyzer:
            try:
                vader_result = self.vader_analyzer.polarity_scores(text)
                results["vader_score"] = vader_result['compound']
                results["analysis_details"]["vader"] = vader_result
            except Exception as e:
                print(f"⚠️ VADER分析失败: {e}")

        # BERT分析
        if use_bert and self.bert_pipeline:
            try:
                bert_result = self.bert_pipeline(text)[0]
                label = bert_result['label']
                score = bert_result['score']
                
                # 转换为-1到1的评分
                if label.lower() == 'positive':
                    results["bert_score"] = score
                elif label.lower() == 'negative':
                    results["bert_score"] = -score
                else:  # neutral
                    results["bert_score"] = (score - 0.5) * 2
                    
                results["analysis_details"]["bert"] = bert_result
            except Exception as e:
                print(f"⚠️ BERT分析失败: {e}")

        # 关键词分析
        if use_keywords:
            keyword_result = self._analyze_keywords(text)
            results["keyword_score"] = keyword_result["score"]
            results["analysis_details"]["keywords"] = keyword_result

        # 表情符号分析
        if use_emoji:
            emoji_result = self._analyze_emoji(text)
            results["emoji_score"] = emoji_result["score"]
            results["analysis_details"]["emoji"] = emoji_result

        # 计算最终评分
        final_score = self._calculate_final_score(results)
        results["final_score"] = round(final_score, 3)
        results["confidence"] = self._calculate_confidence(results)

        # 分类情感
        results["sentiment"] = self._classify_sentiment(final_score)

        return results

    def _preprocess_text(self, text: str) -> str:
        """
        预处理文本
        
        Args:
            text: 原始文本
            
        Returns:
            str: 预处理后的文本
        """
        # 移除URL
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # 移除多余的空格和换行
        text = re.sub(r'\s+', ' ', text).strip()
        
        # 处理特殊字符
        text = text.replace('$', ' $ ').replace('#', ' # ').replace('@', ' @ ')
        
        return text

    def _analyze_keywords(self, text: str) -> Dict[str, Any]:
        """
        基于关键词分析情感
        
        Args:
            text: 文本内容
            
        Returns:
            Dict: 关键词分析结果
        """
        text_lower = text.lower()
        results = {
            "bullish_count": 0,
            "bearish_count": 0,
            "neutral_count": 0,
            "matched_keywords": {"bullish": [], "bearish": [], "neutral": []}
        }

        for category, keywords in self.crypto_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    if category == "bullish":
                        results["bullish_count"] += text_lower.count(keyword)
                        results["matched_keywords"]["bullish"].append(keyword)
                    elif category == "bearish":
                        results["bearish_count"] += text_lower.count(keyword)
                        results["matched_keywords"]["bearish"].append(keyword)
                    else:
                        results["neutral_count"] += text_lower.count(keyword)
                        results["matched_keywords"]["neutral"].append(keyword)

        # 计算关键词情感得分
        total_keywords = results["bullish_count"] + results["bearish_count"]
        if total_keywords == 0:
            score = 0.0
        else:
            score = (results["bullish_count"] - results["bearish_count"]) / total_keywords

        results["score"] = score
        return results

    def _analyze_emoji(self, text: str) -> Dict[str, Any]:
        """
        分析表情符号情感
        
        Args:
            text: 文本内容
            
        Returns:
            Dict: 表情符号分析结果
        """
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+"
        )

        found_emojis = emoji_pattern.findall(text)
        
        results = {
            "found_emojis": found_emojis,
            "positive_emojis": [],
            "negative_emojis": [],
            "neutral_emojis": []
        }

        total_score = 0
        for emoji in found_emojis:
            if emoji in self.emoji_sentiment_map:
                score = self.emoji_sentiment_map[emoji]
                total_score += score
                
                if score > 0.2:
                    results["positive_emojis"].append(emoji)
                elif score < -0.2:
                    results["negative_emojis"].append(emoji)
                else:
                    results["neutral_emojis"].append(emoji)

        if found_emojis:
            results["score"] = total_score / len(found_emojis)
        else:
            results["score"] = 0.0

        return results

    def _calculate_final_score(self, results: Dict[str, Any]) -> float:
        """
        计算最终情感得分
        
        Args:
            results: 各个模型的初步结果
            
        Returns:
            float: 最终情感得分 (-1 到 1)
        """
        scores = []
        weights = []

        # VADER权重
        if results["vader_score"] is not None:
            scores.append(results["vader_score"])
            weights.append(0.3)

        # BERT权重
        if results["bert_score"] is not None:
            scores.append(results["bert_score"])
            weights.append(0.4)

        # 关键词权重
        if results["keyword_score"] is not None:
            scores.append(results["keyword_score"])
            weights.append(0.2)

        # 表情符号权重
        if results["emoji_score"] is not None:
            scores.append(results["emoji_score"])
            weights.append(0.1)

        if not scores:
            return 0.0

        # 加权平均
        total_weight = sum(weights)
        weighted_sum = sum(score * weight for score, weight in zip(scores, weights))
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def _calculate_confidence(self, results: Dict[str, Any]) -> float:
        """
        计算分析置信度
        
        Args:
            results: 分析结果
            
        Returns:
            float: 置信度 (0 到 1)
        """
        available_methods = sum([
            1 for score in [results["vader_score"], results["bert_score"], 
                           results["keyword_score"], results["emoji_score"]]
            if score is not None
        ])

        # 基于可用方法数量和一致性计算置信度
        method_confidence = min(available_methods / 4, 1.0)
        
        # 如果多个方法结果一致，提高置信度
        if available_methods >= 2:
            scores = [
                results["vader_score"], results["bert_score"], 
                results["keyword_score"], results["emoji_score"]
            ]
            valid_scores = [s for s in scores if s is not None]
            
            if len(valid_scores) >= 2:
                score_variance = sum((s - results["final_score"]) ** 2 for s in valid_scores) / len(valid_scores)
                consistency_confidence = max(0, 1 - score_variance)
                return (method_confidence + consistency_confidence) / 2

        return method_confidence

    def _classify_sentiment(self, score: float) -> str:
        """
        分类情感
        
        Args:
            score: 情感得分
            
        Returns:
            str: 情感分类
        """
        if score > 0.3:
            return "positive"
        elif score < -0.3:
            return "negative"
        else:
            return "neutral"

    async def analyze_batch_sentiment(
        self,
        texts: List[str],
        batch_size: int = 10
    ) -> List[Dict[str, Any]]:
        """
        批量分析文本情感
        
        Args:
            texts: 文本列表
            batch_size: 批处理大小
            
        Returns:
            List[Dict]: 情感分析结果列表
        """
        results = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_tasks = [self.analyze_text_sentiment(text) for text in batch]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    print(f"⚠️ 批量分析失败: {result}")
                    results.append({"error": str(result)})
                else:
                    results.append(result)
        
        return results

    async def get_crypto_sentiment_summary(
        self,
        texts: List[str],
        symbol: str = None
    ) -> Dict[str, Any]:
        """
        获取加密货币情感摘要
        
        Args:
            texts: 文本列表
            symbol: 币种符号
            
        Returns:
            Dict: 情感摘要
        """
        if not texts:
            return {
                "symbol": symbol or "unknown",
                "total_texts": 0,
                "avg_sentiment": 0.0,
                "sentiment_distribution": {"positive": 0, "negative": 0, "neutral": 0},
                "confidence": 0.0,
                "timestamp": datetime.utcnow().isoformat()
            }

        # 批量分析
        results = await self.analyze_batch_sentiment(texts)
        
        # 统计情感分布
        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
        sentiment_scores = []
        confidences = []

        for result in results:
            if "error" not in result:
                sentiment = result["sentiment"]
                sentiment_counts[sentiment] += 1
                sentiment_scores.append(result["final_score"])
                confidences.append(result["confidence"])

        # 计算平均值
        total_texts = len([r for r in results if "error" not in r])
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        # 计算分布百分比
        if total_texts > 0:
            for key in sentiment_counts:
                sentiment_counts[key] = round(sentiment_counts[key] / total_texts * 100, 1)

        return {
            "symbol": symbol or "unknown",
            "total_texts": total_texts,
            "avg_sentiment": round(avg_sentiment, 3),
            "sentiment_distribution": sentiment_counts,
            "confidence": round(avg_confidence, 3),
            "detailed_results": results[:10],  # 保留前10个详细结果
            "timestamp": datetime.utcnow().isoformat()
        }


# ================================
# 全局实例
# ================================

sentiment_analyzer = SentimentAnalyzer()
