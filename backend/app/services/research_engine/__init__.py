"""
Research Engine Module
Includes Quick Chat and Deep Research engines
"""
from app.services.research_engine.quick_chat import QuickChatEngine, quick_chat_engine
from app.services.research_engine.deep_research import DeepResearchEngine, deep_research_engine

__all__ = [
    "QuickChatEngine",
    "quick_chat_engine",
    "DeepResearchEngine",
    "deep_research_engine",
]
