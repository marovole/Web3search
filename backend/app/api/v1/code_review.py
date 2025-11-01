"""
Code Review API Endpoints
"""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import asyncio
import json
from datetime import datetime

from app.core.database import get_db
from app.models.code_review import (
    CodeReview, Vulnerability, CodeQualityMetric, AnalysisResult,
    CodeReviewStatus, VulnerabilitySeverity, BlockchainNetwork
)
from app.services.code_analysis import CodeAnalysisOrchestrator
from app.services.code_analysis.blockchain_explorer import BlockchainExplorerService
from app.core.redis_client import redis_client

router = APIRouter(prefix="/code-review", tags=["code-review"])


# Pydantic models for requests/responses
class CodeReviewRequest(BaseModel):
    """Request model for code review submission"""
    source_code: Optional[str] = Field(None, description="Source code to analyze")
    contract_address: Optional[str] = Field(None, description="Contract address to fetch and analyze")
    network: BlockchainNetwork = Field(BlockchainNetwork.ETHEREUM, description="Blockchain network")
    contract_name: Optional[str] = Field(None, description="Contract name")
    file_name: Optional[str] = Field("contract.sol", description="Source file name")
    language: str = Field("solidity", description="Programming language")
    analysis_mode: str = Field("thorough", description="Analysis mode: quick or thorough")


class CodeReviewResponse(BaseModel):
    """Response model for code review"""
    id: str
    status: CodeReviewStatus
    contract_address: Optional[str]
    contract_name: Optional[str]
    network: BlockchainNetwork
    file_name: Optional[str]
    language: str
    analysis_mode: str
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    confidence_score: Optional[float]
    analysis_duration: Optional[float]


class VulnerabilityResponse(BaseModel):
    """Response model for vulnerability findings"""
    id: str
    title: str
    description: str
    severity: VulnerabilitySeverity
    category: str
    file_name: Optional[str]
    line_number: Optional[int]
    function_name: Optional[str]
    code_snippet: Optional[str]
    confidence: Optional[float]
    recommendation: Optional[str]
    fixed_code: Optional[str]
    cve_id: Optional[str]
    swc_id: Optional[str]
    references: Optional[List[str]]


class QualityMetricResponse(BaseModel):
    """Response model for quality metrics"""
    id: str
    overall_score: float
    quality_grade: str
    complexity_score: Optional[float]
    maintainability_index: Optional[float]
    code_duplication_percentage: Optional[float]
    comment_coverage_percentage: Optional[float]
    function_count: Optional[int]
    average_function_length: Optional[float]
    follows_standards: Optional[bool]
    standards_violations: Optional[List[str]]


class AnalysisResultResponse(BaseModel):
    """Response model for analysis results"""
    id: str
    analyzer_name: str
    analyzer_version: str
    analysis_data: Dict[str, Any]
    execution_time: Optional[float]
    tokens_used: Optional[int]
    model_used: Optional[str]
    status: str
    error_message: Optional[str]


# Initialize services
blockchain_explorer = BlockchainExplorerService()
analysis_orchestrator = CodeAnalysisOrchestrator()


@router.post("/analyze", response_model=CodeReviewResponse)
async def create_code_review(
    request: CodeReviewRequest,
    background_tasks: BackgroundTasks,
    db=Depends(get_db)
):
    """
    Create a new code review and start analysis
    
    - **source_code**: Direct source code submission
    - **contract_address**: Contract address to fetch from blockchain
    - **network**: Blockchain network (ethereum, bsc, polygon, etc.)
    - **analysis_mode**: quick or thorough analysis
    """
    
    # Validate request
    if not request.source_code and not request.contract_address:
        raise HTTPException(
            status_code=400,
            detail="Either source_code or contract_address must be provided"
        )
    
    # Create code review record
    code_review = CodeReview(
        contract_address=request.contract_address,
        contract_name=request.contract_name,
        network=request.network,
        file_name=request.file_name,
        language=request.language,
        analysis_mode=request.analysis_mode,
        status=CodeReviewStatus.PENDING
    )
    
    # If contract address provided, fetch source code
    if request.contract_address:
        try:
            verification_data = await blockchain_explorer.get_contract_source(
                request.contract_address,
                request.network
            )
            
            if verification_data and verification_data.get("source_code"):
                code_review.source_code = verification_data["source_code"]
                code_review.contract_name = verification_data.get("contract_name")
                code_review.is_verified = True
            else:
                raise HTTPException(
                    status_code=404,
                    detail=f"Contract source code not found for address {request.contract_address}"
                )
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to fetch contract source code: {str(e)}"
            )
    else:
        code_review.source_code = request.source_code
    
    # Save to database
    db.add(code_review)
    await db.commit()
    await db.refresh(code_review)
    
    # Start analysis in background
    background_tasks.add_task(
        analysis_orchestrator.run_analysis,
        str(code_review.id)
    )
    
    return CodeReviewResponse.from_orm(code_review)


@router.get("/{review_id}", response_model=CodeReviewResponse)
async def get_code_review(review_id: str, db=Depends(get_db)):
    """Get code review details by ID"""
    
    code_review = await db.get(CodeReview, review_id)
    if not code_review:
        raise HTTPException(status_code=404, detail="Code review not found")
    
    return CodeReviewResponse.from_orm(code_review)


@router.get("/{review_id}/vulnerabilities", response_model=List[VulnerabilityResponse])
async def get_vulnerabilities(
    review_id: str,
    severity: Optional[VulnerabilitySeverity] = Query(None, description="Filter by severity"),
    db=Depends(get_db)
):
    """Get security vulnerabilities for a code review"""
    
    # Verify code review exists
    code_review = await db.get(CodeReview, review_id)
    if not code_review:
        raise HTTPException(status_code=404, detail="Code review not found")
    
    # Build query
    query = db.query(Vulnerability).where(Vulnerability.code_review_id == review_id)
    
    if severity:
        query = query.where(Vulnerability.severity == severity)
    
    vulnerabilities = await query.all()
    
    return [VulnerabilityResponse.from_orm(vuln) for vuln in vulnerabilities]


@router.get("/{review_id}/quality-metrics", response_model=QualityMetricResponse)
async def get_quality_metrics(review_id: str, db=Depends(get_db)):
    """Get code quality metrics for a code review"""
    
    # Verify code review exists
    code_review = await db.get(CodeReview, review_id)
    if not code_review:
        raise HTTPException(status_code=404, detail="Code review not found")
    
    # Get quality metrics
    quality_metric = await db.query(CodeQualityMetric).where(
        CodeQualityMetric.code_review_id == review_id
    ).first()
    
    if not quality_metric:
        raise HTTPException(status_code=404, detail="Quality metrics not found")
    
    return QualityMetricResponse.from_orm(quality_metric)


@router.get("/{review_id}/analysis-results", response_model=List[AnalysisResultResponse])
async def get_analysis_results(
    review_id: str,
    analyzer: Optional[str] = Query(None, description="Filter by analyzer name"),
    db=Depends(get_db)
):
    """Get detailed analysis results from all analyzers"""
    
    # Verify code review exists
    code_review = await db.get(CodeReview, review_id)
    if not code_review:
        raise HTTPException(status_code=404, detail="Code review not found")
    
    # Build query
    query = db.query(AnalysisResult).where(AnalysisResult.code_review_id == review_id)
    
    if analyzer:
        query = query.where(AnalysisResult.analyzer_name == analyzer)
    
    results = await query.all()
    
    return [AnalysisResultResponse.from_orm(result) for result in results]


@router.get("/{review_id}/summary")
async def get_review_summary(review_id: str, db=Depends(get_db)):
    """Get comprehensive summary of code review results"""
    
    # Verify code review exists
    code_review = await db.get(CodeReview, review_id)
    if not code_review:
        raise HTTPException(status_code=404, detail="Code review not found")
    
    # Get all related data
    vulnerabilities = await db.query(Vulnerability).where(
        Vulnerability.code_review_id == review_id
    ).all()
    
    quality_metric = await db.query(CodeQualityMetric).where(
        CodeQualityMetric.code_review_id == review_id
    ).first()
    
    analysis_results = await db.query(AnalysisResult).where(
        AnalysisResult.code_review_id == review_id
    ).all()
    
    # Calculate summary statistics
    severity_counts = {}
    for vuln in vulnerabilities:
        severity = vuln.severity.value
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
    
    # Build summary
    summary = {
        "review_id": review_id,
        "status": code_review.status.value,
        "created_at": code_review.created_at,
        "completed_at": code_review.completed_at,
        "analysis_duration": code_review.analysis_duration,
        "confidence_score": code_review.confidence_score,
        "vulnerability_summary": {
            "total_vulnerabilities": len(vulnerabilities),
            "severity_breakdown": severity_counts,
            "high_risk_count": severity_counts.get("critical", 0) + severity_counts.get("high", 0)
        },
        "quality_summary": {
            "overall_score": quality_metric.overall_score if quality_metric else None,
            "quality_grade": quality_metric.quality_grade if quality_metric else None,
            "maintainability_index": quality_metric.maintainability_index if quality_metric else None
        },
        "analysis_summary": {
            "analyzers_run": len(analysis_results),
            "total_execution_time": sum(r.execution_time or 0 for r in analysis_results),
            "total_tokens_used": sum(r.tokens_used or 0 for r in analysis_results),
            "successful_analyses": len([r for r in analysis_results if r.status == "completed"])
        }
    }
    
    return summary


@router.get("/{review_id}/stream")
async def stream_analysis_progress(review_id: str):
    """Stream real-time analysis progress using Server-Sent Events"""
    
    async def event_generator():
        """Generate SSE events for analysis progress"""
        
        while True:
            # Get current status from Redis cache
            status_key = f"analysis_progress:{review_id}"
            progress_data = await redis_client.get(status_key)
            
            if progress_data:
                yield f"data: {json.dumps(progress_data)}\n\n"
                
                # If analysis is complete or failed, end the stream
                if progress_data.get("status") in ["completed", "failed"]:
                    break
            else:
                # Check database for final status
                async for db in get_db():
                    code_review = await db.get(CodeReview, review_id)
                    if code_review and code_review.status in [CodeReviewStatus.COMPLETED, CodeReviewStatus.FAILED]:
                        final_data = {
                            "status": code_review.status.value,
                            "progress": 100,
                            "message": "Analysis complete" if code_review.status == CodeReviewStatus.COMPLETED else "Analysis failed"
                        }
                        yield f"data: {json.dumps(final_data)}\n\n"
                        break
            
            await asyncio.sleep(1)  # Poll every second
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


@router.post("/{review_id}/retry")
async def retry_analysis(review_id: str, background_tasks: BackgroundTasks, db=Depends(get_db)):
    """Retry failed analysis"""
    
    code_review = await db.get(CodeReview, review_id)
    if not code_review:
        raise HTTPException(status_code=404, detail="Code review not found")
    
    if code_review.status not in [CodeReviewStatus.FAILED, CodeReviewStatus.COMPLETED]:
        raise HTTPException(
            status_code=400,
            detail="Only failed or completed analyses can be retried"
        )
    
    # Reset status
    code_review.status = CodeReviewStatus.PENDING
    code_review.started_at = None
    code_review.completed_at = None
    code_review.confidence_score = None
    code_review.analysis_duration = None
    
    # Clear previous results
    await db.query(Vulnerability).where(Vulnerability.code_review_id == review_id).delete()
    await db.query(CodeQualityMetric).where(CodeQualityMetric.code_review_id == review_id).delete()
    await db.query(AnalysisResult).where(AnalysisResult.code_review_id == review_id).delete()
    
    await db.commit()
    
    # Start new analysis
    background_tasks.add_task(
        analysis_orchestrator.run_analysis,
        review_id
    )
    
    return {"message": "Analysis retry started", "review_id": review_id}


@router.delete("/{review_id}")
async def delete_code_review(review_id: str, db=Depends(get_db)):
    """Delete a code review and all associated data"""
    
    code_review = await db.get(CodeReview, review_id)
    if not code_review:
        raise HTTPException(status_code=404, detail="Code review not found")
    
    # Delete related data (cascade should handle this, but being explicit)
    await db.query(Vulnerability).where(Vulnerability.code_review_id == review_id).delete()
    await db.query(CodeQualityMetric).where(CodeQualityMetric.code_review_id == review_id).delete()
    await db.query(AnalysisResult).where(AnalysisResult.code_review_id == review_id).delete()
    
    # Delete the code review
    await db.delete(code_review)
    await db.commit()
    
    return {"message": "Code review deleted successfully"}


@router.get("/contracts/{contract_address}/verify")
async def verify_contract(
    contract_address: str,
    network: BlockchainNetwork = Query(BlockchainNetwork.ETHEREUM, description="Blockchain network")
):
    """Verify if a contract is verified and get its source code"""
    
    try:
        verification_data = await blockchain_explorer.get_contract_source(
            contract_address,
            network
        )
        
        if not verification_data:
            return {
                "contract_address": contract_address,
                "network": network,
                "is_verified": False,
                "source_code": None
            }
        
        return {
            "contract_address": contract_address,
            "network": network,
            "is_verified": True,
            "contract_name": verification_data.get("contract_name"),
            "compiler_version": verification_data.get("compiler_version"),
            "source_code": verification_data.get("source_code"),
            "verified_at": verification_data.get("verified_at")
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to verify contract: {str(e)}"
        )
