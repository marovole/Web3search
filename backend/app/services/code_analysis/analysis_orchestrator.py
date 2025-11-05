"""
Code Analysis Orchestrator
"""
from typing import Dict, Any, List
import asyncio
import logging
from datetime import datetime
from uuid import UUID

from app.core.database import get_db
from app.core.redis_client import redis_client
from app.models.code_review import CodeReview, CodeReviewStatus
from app.services.llm import LLMClient
from .security_analyzer import SecurityVulnerabilityAnalyzer
from .quality_analyzer import CodeQualityAnalyzer
from .architecture_analyzer import ArchitectureAnalyzer
from .gas_analyzer import GasEfficiencyAnalyzer
from .compliance_analyzer import ComplianceAnalyzer

logger = logging.getLogger(__name__)


class CodeAnalysisOrchestrator:
    """Orchestrates multiple code analyzers and manages the analysis pipeline"""
    
    def __init__(self):
        self.llm_service = LLMClient()
        self.analyzers = {
            "security": SecurityVulnerabilityAnalyzer(self.llm_service),
            "quality": CodeQualityAnalyzer(self.llm_service),
            "architecture": ArchitectureAnalyzer(self.llm_service),
            "gas": GasEfficiencyAnalyzer(self.llm_service),
            "compliance": ComplianceAnalyzer(self.llm_service)
        }
    
    async def run_analysis(self, code_review_id: str):
        """
        Run complete code analysis pipeline
        
        Args:
            code_review_id: UUID of the code review to analyze
        """
        start_time = datetime.utcnow()
        
        try:
            # Get code review from database
            async for db in get_db():
                code_review = await db.get(CodeReview, code_review_id)
                if not code_review:
                    logger.error(f"Code review {code_review_id} not found")
                    return
                
                # Update status to in progress
                code_review.status = CodeReviewStatus.IN_PROGRESS
                code_review.started_at = start_time
                await db.commit()
                
                # Update progress in Redis
                await self._update_progress(code_review_id, {
                    "status": "running",
                    "stage": "initialization",
                    "progress": 5,
                    "message": "Starting code analysis..."
                })
            
            # Prepare analysis context
            context = await self._prepare_analysis_context(code_review)
            
            # Run analyzers based on analysis mode
            if code_review.analysis_mode == "quick":
                analyzers_to_run = ["security", "quality"]
            else:  # thorough
                analyzers_to_run = list(self.analyzers.keys())
            
            # Execute analyzers in parallel
            results = await self._execute_analyzers(
                code_review, 
                analyzers_to_run, 
                context
            )
            
            # Process and save results
            await self._process_results(code_review_id, results)
            
            # Calculate final metrics
            await self._calculate_final_metrics(code_review_id)
            
            # Update completion status
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            async for db in get_db():
                code_review = await db.get(CodeReview, code_review_id)
                code_review.status = CodeReviewStatus.COMPLETED
                code_review.completed_at = end_time
                code_review.analysis_duration = duration
                code_review.confidence_score = await self._calculate_confidence_score(results)
                await db.commit()
            
            # Final progress update
            await self._update_progress(code_review_id, {
                "status": "completed",
                "stage": "completed",
                "progress": 100,
                "message": "Analysis completed successfully",
                "duration": duration
            })
            
            logger.info(f"Code analysis {code_review_id} completed in {duration:.2f}s")
            
        except Exception as e:
            logger.error(f"Code analysis {code_review_id} failed: {str(e)}")
            
            # Update error status
            async for db in get_db():
                code_review = await db.get(CodeReview, code_review_id)
                if code_review:
                    code_review.status = CodeReviewStatus.FAILED
                    await db.commit()
            
            # Update progress with error
            await self._update_progress(code_review_id, {
                "status": "failed",
                "stage": "error",
                "progress": 0,
                "message": f"Analysis failed: {str(e)}"
            })
    
    async def _prepare_analysis_context(self, code_review: CodeReview) -> Dict[str, Any]:
        """Prepare analysis context with additional information"""
        
        context = {
            "contract_address": code_review.contract_address,
            "network": code_review.network,
            "language": code_review.language,
            "analysis_mode": code_review.analysis_mode,
            "file_name": code_review.file_name,
            "contract_name": code_review.contract_name,
            "created_at": code_review.created_at.isoformat()
        }
        
        # Add code statistics
        if code_review.source_code:
            lines = code_review.source_code.split('\n')
            context.update({
                "line_count": len(lines),
                "char_count": len(code_review.source_code),
                "is_empty": len(code_review.source_code.strip()) == 0,
                "has_comments": '//' in code_review.source_code,
                "has_functions": 'function' in code_review.source_code
            })
        
        return context
    
    async def _execute_analyzers(
        self, 
        code_review: CodeReview, 
        analyzer_names: List[str], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute specified analyzers in parallel"""
        
        total_analyzers = len(analyzer_names)
        completed_analyzers = 0
        results = {}
        
        # Create tasks for parallel execution
        tasks = []
        for analyzer_name in analyzer_names:
            if analyzer_name in self.analyzers:
                task = self._run_single_analyzer(
                    self.analyzers[analyzer_name],
                    code_review,
                    context,
                    analyzer_name
                )
                tasks.append((analyzer_name, task))
        
        # Execute tasks and update progress
        for analyzer_name, task in tasks:
            try:
                # Update progress for starting analyzer
                await self._update_progress(str(code_review.id), {
                    "status": "running",
                    "stage": f"analyzing_{analyzer_name}",
                    "progress": 10 + (completed_analyzers * 80 // total_analyzers),
                    "message": f"Running {analyzer_name} analysis..."
                })
                
                # Execute analyzer
                result = await task
                results[analyzer_name] = result
                completed_analyzers += 1
                
                logger.info(f"Completed {analyzer_name} analysis for {code_review.id}")
                
            except Exception as e:
                logger.error(f"{analyzer_name} analysis failed: {str(e)}")
                results[analyzer_name] = {"error": str(e)}
        
        return results
    
    async def _run_single_analyzer(
        self, 
        analyzer, 
        code_review: CodeReview, 
        context: Dict[str, Any],
        analyzer_name: str
    ) -> Dict[str, Any]:
        """Run a single analyzer and save its results"""
        
        # Validate input
        if not analyzer.validate_input(code_review):
            raise ValueError(f"Invalid input for {analyzer_name} analyzer")
        
        # Execute analysis
        analysis_result = await analyzer.execute_analysis(code_review, context)
        
        # Save result to database
        async for db in get_db():
            db.add(analysis_result)
            await db.commit()
            await db.refresh(analysis_result)
        
        # Save specific results based on analyzer type
        if analyzer_name == "security" and hasattr(analyzer, 'save_vulnerabilities'):
            analysis_data = analysis_result.analysis_data
            vulnerabilities = analysis_data.get("vulnerabilities", [])
            await analyzer.save_vulnerabilities(code_review, vulnerabilities)
        
        elif analyzer_name == "quality" and hasattr(analyzer, 'save_quality_metrics'):
            analysis_data = analysis_result.analysis_data
            await analyzer.save_quality_metrics(code_review, analysis_data)
        
        return {
            "result_id": str(analysis_result.id),
            "analysis_data": analysis_result.analysis_data,
            "execution_time": analysis_result.execution_time,
            "tokens_used": analysis_result.tokens_used,
            "model_used": analysis_result.model_used
        }
    
    async def _process_results(self, code_review_id: str, results: Dict[str, Any]):
        """Process and combine results from all analyzers"""
        
        # Update progress
        await self._update_progress(code_review_id, {
            "status": "running",
            "stage": "processing_results",
            "progress": 90,
            "message": "Processing analysis results..."
        })
        
        # Combine results into a comprehensive report
        combined_results = {
            "analysis_summary": {
                "analyzers_run": list(results.keys()),
                "successful_analyses": [name for name, result in results.items() if "error" not in result],
                "failed_analyses": [name for name, result in results.items() if "error" in result]
            }
        }
        
        # Add specific results
        for analyzer_name, result in results.items():
            if "error" not in result:
                combined_results[f"{analyzer_name}_analysis"] = result["analysis_data"]
        
        # Cache combined results
        cache_key = f"combined_results:{code_review_id}"
        await redis_client.setex(cache_key, 86400, combined_results)  # Cache for 24 hours
    
    async def _calculate_final_metrics(self, code_review_id: str):
        """Calculate final aggregated metrics"""
        
        async for db in get_db():
            # Get all analysis results
            from app.models.code_review import AnalysisResult, Vulnerability, CodeQualityMetric
            
            analysis_results = await db.query(AnalysisResult).where(
                AnalysisResult.code_review_id == code_review_id
            ).all()
            
            vulnerabilities = await db.query(Vulnerability).where(
                Vulnerability.code_review_id == code_review_id
            ).all()
            
            quality_metrics = await db.query(CodeQualityMetric).where(
                CodeQualityMetric.code_review_id == code_review_id
            ).first()
            
            # Calculate aggregated metrics
            total_execution_time = sum(r.execution_time or 0 for r in analysis_results)
            total_tokens_used = sum(r.tokens_used or 0 for r in analysis_results)
            
            # Store aggregated metrics
            aggregated_data = {
                "total_execution_time": total_execution_time,
                "total_tokens_used": total_tokens_used,
                "vulnerability_count": len(vulnerabilities),
                "high_risk_vulnerabilities": len([v for v in vulnerabilities if v.severity.value in ["critical", "high"]]),
                "quality_score": quality_metrics.overall_score if quality_metrics else None
            }
            
            # Cache aggregated metrics
            cache_key = f"aggregated_metrics:{code_review_id}"
            await redis_client.setex(cache_key, 86400, aggregated_data)
    
    async def _calculate_confidence_score(self, results: Dict[str, Any]) -> float:
        """Calculate overall confidence score based on analyzer results"""
        
        if not results:
            return 0.0
        
        confidence_scores = []
        
        for analyzer_name, result in results.items():
            if "error" not in result:
                analysis_data = result.get("analysis_data", {})
                
                # Get confidence from different analyzers
                if analyzer_name == "security":
                    vulns = analysis_data.get("vulnerabilities", [])
                    if vulns:
                        avg_confidence = sum(v.get("confidence", 0.5) for v in vulns) / len(vulns)
                        confidence_scores.append(avg_confidence)
                    else:
                        confidence_scores.append(0.8)  # High confidence if no vulnerabilities found
                
                elif analyzer_name == "quality":
                    quality_score = analysis_data.get("overall_score", 0)
                    confidence_scores.append(quality_score / 100.0)
                
                else:
                    # Default confidence for other analyzers
                    confidence_scores.append(0.7)
        
        if confidence_scores:
            return sum(confidence_scores) / len(confidence_scores)
        else:
            return 0.0
    
    async def _update_progress(self, code_review_id: str, progress_data: Dict[str, Any]):
        """Update analysis progress in Redis"""
        
        progress_key = f"analysis_progress:{code_review_id}"
        progress_data["timestamp"] = datetime.utcnow().isoformat()
        
        await redis_client.setex(progress_key, 3600, progress_data)  # Keep for 1 hour
    
    async def get_analysis_progress(self, code_review_id: str) -> Dict[str, Any]:
        """Get current analysis progress"""
        
        progress_key = f"analysis_progress:{code_review_id}"
        progress_data = await redis_client.get(progress_key)
        
        if progress_data:
            return progress_data
        
        # Fallback to database status
        async for db in get_db():
            code_review = await db.get(CodeReview, code_review_id)
            if code_review:
                return {
                    "status": code_review.status.value,
                    "progress": 100 if code_review.status == CodeReviewStatus.COMPLETED else 0,
                    "message": "Analysis complete" if code_review.status == CodeReviewStatus.COMPLETED else "Status unknown"
                }
        
        return {"status": "unknown", "progress": 0, "message": "Analysis not found"}
    
    async def cancel_analysis(self, code_review_id: str):
        """Cancel ongoing analysis"""
        
        # Update progress to cancelled
        await self._update_progress(code_review_id, {
            "status": "cancelled",
            "stage": "cancelled",
            "progress": 0,
            "message": "Analysis cancelled by user"
        })
        
        # Update database status
        async for db in get_db():
            code_review = await db.get(CodeReview, code_review_id)
            if code_review and code_review.status == CodeReviewStatus.IN_PROGRESS:
                code_review.status = CodeReviewStatus.FAILED
                await db.commit()
