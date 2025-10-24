"""
服务层模块
包含业务逻辑和外部服务集成
"""
from app.services.llm import LLMClient, llm_client, ModelConfig
from app.services.data_aggregator import DataAggregator, data_aggregator
from app.services.prompt_manager import PromptManager, prompt_manager
from app.services.research_engine import (
    QuickChatEngine,
    quick_chat_engine,
    DeepResearchEngine,
    deep_research_engine,
)
from app.services.report import ReportGenerator, report_generator

__all__ = [
    "LLMClient",
    "llm_client",
    "ModelConfig",
    "DataAggregator",
    "data_aggregator",
    "PromptManager",
    "prompt_manager",
    "QuickChatEngine",
    "quick_chat_engine",
    "DeepResearchEngine",
    "deep_research_engine",
    "ReportGenerator",
    "report_generator",
]
