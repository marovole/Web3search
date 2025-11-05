"""
Base Code Analyzer
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
from app.models.code_review import CodeReview, AnalysisResult
from app.services.llm import LLMClient
from app.core.redis_client import redis_client

logger = logging.getLogger(__name__)


class BaseCodeAnalyzer(ABC):
    """Base class for all code analyzers"""
    
    def __init__(self, llm_service: LLMClient):
        self.llm_service = llm_service
        self.name = self.__class__.__name__
        self.version = "1.0.0"
        
    @abstractmethod
    async def analyze(self, code_review: CodeReview, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze code and return results
        
        Args:
            code_review: The code review object containing code to analyze
            context: Additional context for analysis
            
        Returns:
            Dictionary containing analysis results
        """
        pass
    
    @abstractmethod
    def get_prompt_template(self) -> str:
        """Get the prompt template for this analyzer"""
        pass
    
    async def execute_analysis(self, code_review: CodeReview, context: Dict[str, Any]) -> AnalysisResult:
        """
        Execute the analysis and create an AnalysisResult record
        
        Args:
            code_review: The code review being analyzed
            context: Analysis context
            
        Returns:
            AnalysisResult object with findings
        """
        start_time = datetime.utcnow()
        
        try:
            # Check cache first
            cache_key = f"analysis:{self.name}:{hash(code_review.source_code or '')}:{code_review.network}"
            cached_result = await redis_client.get(cache_key)
            
            if cached_result:
                logger.info(f"Using cached result for {self.name}")
                analysis_data = cached_result
                execution_time = 0.0
                tokens_used = 0
                model_used = "cache"
            else:
                # Perform actual analysis
                analysis_data = await self.analyze(code_review, context)
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                
                # Extract execution metadata from LLM service
                tokens_used = getattr(self.llm_service, 'last_tokens_used', 0)
                model_used = getattr(self.llm_service, 'last_model_used', 'unknown')
                
                # Cache results for 24 hours
                await redis_client.setex(cache_key, 86400, analysis_data)
            
            # Create analysis result record
            result = AnalysisResult(
                code_review_id=code_review.id,
                analyzer_name=self.name,
                analyzer_version=self.version,
                analysis_data=analysis_data,
                execution_time=execution_time,
                tokens_used=tokens_used,
                model_used=model_used,
                status="completed"
            )
            
            logger.info(f"Completed {self.name} analysis in {execution_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Analysis failed for {self.name}: {str(e)}")
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            result = AnalysisResult(
                code_review_id=code_review.id,
                analyzer_name=self.name,
                analyzer_version=self.version,
                analysis_data={},
                execution_time=execution_time,
                status="failed",
                error_message=str(e)
            )
            
            return result
    
    async def prepare_context(self, code_review: CodeReview) -> Dict[str, Any]:
        """
        Prepare analysis context with additional information
        
        Args:
            code_review: The code review being analyzed
            
        Returns:
            Dictionary with context information
        """
        context = {
            "contract_address": code_review.contract_address,
            "network": code_review.network,
            "language": code_review.language,
            "analysis_mode": code_review.analysis_mode,
            "file_name": code_review.file_name,
            "contract_name": code_review.contract_name,
        }
        
        # Add code statistics
        if code_review.source_code:
            lines = code_review.source_code.split('\n')
            context.update({
                "line_count": len(lines),
                "char_count": len(code_review.source_code),
                "is_empty": len(code_review.source_code.strip()) == 0
            })
        
        return context
    
    def validate_input(self, code_review: CodeReview) -> bool:
        """
        Validate input code review
        
        Args:
            code_review: The code review to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not code_review.source_code and not code_review.contract_address:
            logger.error("No source code or contract address provided")
            return False
            
        if code_review.source_code and len(code_review.source_code.strip()) == 0:
            logger.error("Empty source code provided")
            return False
            
        return True
    
    async def get_model_for_task(self, task_complexity: str = "medium") -> str:
        """
        Get the appropriate model for the analysis task
        
        Args:
            task_complexity: Complexity level (simple, medium, complex)
            
        Returns:
            Model name string
        """
        model_mapping = {
            "simple": "qwen/qwen3-30b-a3b:free",
            "medium": "qwen/qwen3-235b-a22b:free", 
            "complex": "deepseek/deepseek-r1-0528:free"
        }
        
        return model_mapping.get(task_complexity, "qwen/qwen3-235b-a22b:free")
    
    def format_analysis_output(self, raw_output: str) -> Dict[str, Any]:
        """
        Format raw LLM output into structured data
        
        Args:
            raw_output: Raw output from LLM
            
        Returns:
            Structured analysis data
        """
        # This method should be overridden by specific analyzers
        # to handle their specific output formats
        return {
            "raw_output": raw_output,
            "formatted_at": datetime.utcnow().isoformat()
        }
