"""
Code Review Models
"""
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey, Enum as SQLEnum, Float
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
import uuid


class CodeReviewStatus(str, Enum):
    """Code review status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class VulnerabilitySeverity(str, Enum):
    """Vulnerability severity enumeration"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class BlockchainNetwork(str, Enum):
    """Supported blockchain networks"""
    ETHEREUM = "ethereum"
    BSC = "bsc"
    POLYGON = "polygon"
    ARBITRUM = "arbitrum"
    SOLANA = "solana"


class CodeReview(Base):
    """Code review model for smart contract analysis"""
    __tablename__ = "code_reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_address = Column(String(42), nullable=True, index=True)
    contract_name = Column(String(255), nullable=True)
    network = Column(SQLEnum(BlockchainNetwork), nullable=False, default=BlockchainNetwork.ETHEREUM)
    source_code = Column(Text, nullable=True)
    file_name = Column(String(255), nullable=True)
    language = Column(String(50), nullable=False, default="solidity")
    
    # Analysis metadata
    status = Column(SQLEnum(CodeReviewStatus), nullable=False, default=CodeReviewStatus.PENDING)
    analysis_mode = Column(String(20), nullable=False, default="quick")  # quick, thorough
    confidence_score = Column(Float, nullable=True)
    analysis_duration = Column(Float, nullable=True)  # seconds
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    vulnerabilities = relationship("Vulnerability", back_populates="code_review", cascade="all, delete-orphan")
    quality_metrics = relationship("CodeQualityMetric", back_populates="code_review", cascade="all, delete-orphan")
    analysis_results = relationship("AnalysisResult", back_populates="code_review", cascade="all, delete-orphan")


class Vulnerability(Base):
    """Security vulnerability findings"""
    __tablename__ = "vulnerabilities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code_review_id = Column(UUID(as_uuid=True), ForeignKey("code_reviews.id"), nullable=False)
    
    # Vulnerability details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(SQLEnum(VulnerabilitySeverity), nullable=False)
    category = Column(String(100), nullable=False)  # reentrancy, overflow, access_control, etc.
    
    # Location information
    file_name = Column(String(255), nullable=True)
    line_number = Column(Integer, nullable=True)
    function_name = Column(String(255), nullable=True)
    code_snippet = Column(Text, nullable=True)
    
    # Analysis details
    confidence = Column(Float, nullable=True)  # 0.0 to 1.0
    recommendation = Column(Text, nullable=True)
    fixed_code = Column(Text, nullable=True)
    
    # External references
    cve_id = Column(String(20), nullable=True)
    swc_id = Column(String(20), nullable=True)  # Smart Contract Weakness Classification
    references = Column(JSON, nullable=True)  # List of reference URLs
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    code_review = relationship("CodeReview", back_populates="vulnerabilities")


class CodeQualityMetric(Base):
    """Code quality assessment metrics"""
    __tablename__ = "code_quality_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code_review_id = Column(UUID(as_uuid=True), ForeignKey("code_reviews.id"), nullable=False)
    
    # Overall quality score
    overall_score = Column(Float, nullable=False)  # 0.0 to 100.0
    quality_grade = Column(String(2), nullable=False)  # A+, A, B+, B, C+, C, D, F
    
    # Specific metrics
    complexity_score = Column(Float, nullable=True)
    maintainability_index = Column(Float, nullable=True)
    code_duplication_percentage = Column(Float, nullable=True)
    comment_coverage_percentage = Column(Float, nullable=True)
    function_count = Column(Integer, nullable=True)
    average_function_length = Column(Float, nullable=True)
    
    # Gas efficiency metrics (for Solidity)
    gas_efficiency_score = Column(Float, nullable=True)
    estimated_deployment_cost = Column(Float, nullable=True)  # in ETH
    estimated_execution_cost = Column(Float, nullable=True)  # per transaction
    
    # Standards compliance
    follows_standards = Column(Boolean, nullable=True)
    standards_violations = Column(JSON, nullable=True)  # List of standard violations
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    code_review = relationship("CodeReview", back_populates="quality_metrics")


class AnalysisResult(Base):
    """Detailed analysis results from different analyzers"""
    __tablename__ = "analysis_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code_review_id = Column(UUID(as_uuid=True), ForeignKey("code_reviews.id"), nullable=False)
    
    # Analyzer information
    analyzer_name = Column(String(100), nullable=False)  # SecurityVulnerabilityAnalyzer, etc.
    analyzer_version = Column(String(20), nullable=True)
    
    # Analysis data
    analysis_data = Column(JSON, nullable=False)  # Structured analysis results
    meta_info = Column(JSON, nullable=True)  # Additional metadata
    
    # Execution details
    execution_time = Column(Float, nullable=True)  # seconds
    tokens_used = Column(Integer, nullable=True)
    model_used = Column(String(100), nullable=True)
    
    # Status
    status = Column(String(20), nullable=False, default="completed")
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    code_review = relationship("CodeReview", back_populates="analysis_results")


class ContractVerification(Base):
    """Contract verification status from blockchain explorers"""
    __tablename__ = "contract_verifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_address = Column(String(42), nullable=False, index=True)
    network = Column(SQLEnum(BlockchainNetwork), nullable=False)
    
    # Verification status
    is_verified = Column(Boolean, nullable=False)
    verification_source = Column(String(100), nullable=True)  # etherscan, bscscan, etc.
    source_code_hash = Column(String(64), nullable=True)  # SHA256 hash of source code
    
    # Contract metadata
    contract_name = Column(String(255), nullable=True)
    compiler_version = Column(String(50), nullable=True)
    optimization_enabled = Column(Boolean, nullable=True)
    
    # Timestamps
    verified_at = Column(DateTime, nullable=True)
    last_checked = Column(DateTime, default=datetime.utcnow)
    
    created_at = Column(DateTime, default=datetime.utcnow)
