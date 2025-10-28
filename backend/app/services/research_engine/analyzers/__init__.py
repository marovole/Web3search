"""
Research Engine Analyzers
六维度分析器模块
"""
from app.services.research_engine.analyzers.tldr_generator import TLDRGenerator, tldr_generator
from app.services.research_engine.analyzers.timeframe_analyzer import TimeframeAnalyzer, timeframe_analyzer
from app.services.research_engine.analyzers.sentiment_analyzer import SentimentAnalyzer, sentiment_analyzer
from app.services.research_engine.analyzers.technical_analyzer import TechnicalAnalyzer, technical_analyzer
from app.services.research_engine.analyzers.onchain_analyzer import OnchainAnalyzer, onchain_analyzer
from app.services.research_engine.analyzers.competitor_analyzer import CompetitorAnalyzer, competitor_analyzer
from app.services.research_engine.analyzers.tokenomics_analyzer import TokenomicsAnalyzer, tokenomics_analyzer
from app.services.research_engine.analyzers.risk_assessor import RiskAssessor, risk_assessor
from app.services.research_engine.analyzers.conclusion_synthesizer import ConclusionSynthesizer, conclusion_synthesizer

# 统一输出接口
from app.services.research_engine.analyzers.analyzer_output import (
    AnalyzerOutput,
    AnalyzerMetadata,
    VisualizationHint,
    create_analyzer_output,
    create_error_output,
    create_competitor_table_hint,
    create_price_chart_hint,
    create_sentiment_pie_hint,
)

__all__ = [
    # Analyzers
    "TLDRGenerator",
    "tldr_generator",
    "TimeframeAnalyzer",
    "timeframe_analyzer",
    "SentimentAnalyzer",
    "sentiment_analyzer",
    "TechnicalAnalyzer",
    "technical_analyzer",
    "OnchainAnalyzer",
    "onchain_analyzer",
    "CompetitorAnalyzer",
    "competitor_analyzer",
    "TokenomicsAnalyzer",
    "tokenomics_analyzer",
    "RiskAssessor",
    "risk_assessor",
    "ConclusionSynthesizer",
    "conclusion_synthesizer",
    # 统一输出接口
    "AnalyzerOutput",
    "AnalyzerMetadata",
    "VisualizationHint",
    "create_analyzer_output",
    "create_error_output",
    "create_competitor_table_hint",
    "create_price_chart_hint",
    "create_sentiment_pie_hint",
]
