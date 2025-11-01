"""
Security Validator for Code Review System
"""
from typing import Dict, Any, List, Optional, Tuple
import re
import hashlib
import logging
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from app.core.config import settings

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """Security validation levels"""
    BASIC = "basic"
    STANDARD = "standard"
    COMPREHENSIVE = "comprehensive"


@dataclass
class SecurityIssue:
    """Security issue found during validation"""
    severity: str  # critical, high, medium, low
    category: str
    title: str
    description: str
    location: Optional[str]
    recommendation: str
    cwe_id: Optional[str] = None


class SecurityValidator:
    """Validates security aspects of the code review system"""
    
    def __init__(self):
        self.validation_rules = self._load_validation_rules()
        self.pattern_blacklist = self._load_pattern_blacklist()
        self.sensitive_data_patterns = self._load_sensitive_data_patterns()
    
    def _load_validation_rules(self) -> Dict[str, Any]:
        """Load security validation rules"""
        return {
            "input_validation": {
                "max_contract_size": 1_000_000,  # 1MB
                "max_line_length": 1000,
                "allowed_languages": ["solidity", "rust", "vyper"],
                "forbidden_patterns": [
                    r"eval\s*\(",
                    r"exec\s*\(",
                    r"import\s+os",
                    r"subprocess\.",
                    r"__import__",
                ]
            },
            "output_sanitization": {
                "max_response_size": 10_000_000,  # 10MB
                "sanitize_html": True,
                "sanitize_javascript": True,
                "sanitize_sql": True
            },
            "api_security": {
                "rate_limit_per_minute": 60,
                "max_concurrent_analyses": 10,
                "require_authentication": True,
                "allowed_origins": settings.ALLOWED_ORIGINS if hasattr(settings, 'ALLOWED_ORIGINS') else ["*"]
            },
            "data_protection": {
                "encrypt_sensitive_data": True,
                "mask_contract_addresses": False,
                "retention_days": 30,
                "audit_logging": True
            }
        }
    
    def _load_pattern_blacklist(self) -> List[str]:
        """Load patterns that should never appear in smart contract code"""
        return [
            r"require\s*\(\s*msg\.sender\s*==\s*address\s*\(\s*0\s*\)\s*\)",  # Hardcoded zero address
            r"suicide\s*\(",  # Deprecated suicide function
            r"block\.timestamp\s*<\s*block\.timestamp",  # Always false condition
            r"now\s*==\s*now",  # Always true condition
            r"tx\.origin\s*==\s*msg\.sender",  # Authorization bypass vulnerability
            r"while\s*\(\s*true\s*\)",  # Potential infinite loop
            r"for\s*\(\s*;;\s*\)",  # Infinite loop
        ]
    
    def _load_sensitive_data_patterns(self) -> List[Dict[str, str]]:
        """Load patterns for detecting sensitive data exposure"""
        return [
            {"pattern": r"private[_\s]*key", "type": "private_key"},
            {"pattern": r"secret[_\s]*key", "type": "secret_key"},
            {"pattern": r"password[_\s]*\w+", "type": "password"},
            {"pattern": r"api[_\s]*key", "type": "api_key"},
            {"pattern": r"0x[a-fA-F0-9]{64}", "type": "private_key_hex"},
            {"pattern": r"-----BEGIN\s+[A-Z]+\s+KEY-----", "type": "pem_key"},
        ]
    
    async def validate_contract_input(
        self, 
        source_code: str, 
        contract_address: Optional[str] = None,
        validation_level: ValidationLevel = ValidationLevel.STANDARD
    ) -> Tuple[bool, List[SecurityIssue]]:
        """
        Validate contract input for security issues
        
        Args:
            source_code: Contract source code to validate
            contract_address: Contract address (if provided)
            validation_level: Level of validation to perform
            
        Returns:
            Tuple of (is_valid, security_issues)
        """
        
        issues = []
        
        # Basic validation
        if validation_level in [ValidationLevel.BASIC, ValidationLevel.STANDARD, ValidationLevel.COMPREHENSIVE]:
            issues.extend(self._validate_basic_input(source_code, contract_address))
        
        # Standard validation
        if validation_level in [ValidationLevel.STANDARD, ValidationLevel.COMPREHENSIVE]:
            issues.extend(self._validate_standard_input(source_code))
        
        # Comprehensive validation
        if validation_level == ValidationLevel.COMPREHENSIVE:
            issues.extend(self._validate_comprehensive_input(source_code))
        
        # Determine if input is valid (no critical or high severity issues)
        is_valid = not any(issue.severity in ["critical", "high"] for issue in issues)
        
        return is_valid, issues
    
    def _validate_basic_input(self, source_code: str, contract_address: Optional[str]) -> List[SecurityIssue]:
        """Basic input validation"""
        
        issues = []
        
        # Size validation
        if len(source_code) > self.validation_rules["input_validation"]["max_contract_size"]:
            issues.append(SecurityIssue(
                severity="high",
                category="input_validation",
                title="Contract too large",
                description=f"Contract size exceeds maximum allowed size",
                location="entire_contract",
                recommendation="Reduce contract size or split into multiple contracts"
            ))
        
        # Line length validation
        lines = source_code.split('\n')
        for i, line in enumerate(lines):
            if len(line) > self.validation_rules["input_validation"]["max_line_length"]:
                issues.append(SecurityIssue(
                    severity="low",
                    category="code_quality",
                    title="Line too long",
                    description=f"Line {i+1} exceeds maximum length",
                    location=f"line_{i+1}",
                    recommendation="Break long lines into multiple lines"
                ))
        
        # Contract address validation
        if contract_address:
            if not re.match(r"^0x[a-fA-F0-9]{40}$", contract_address):
                issues.append(SecurityIssue(
                    severity="high",
                    category="input_validation",
                    title="Invalid contract address",
                    description="Contract address format is invalid",
                    location="contract_address",
                    recommendation="Provide a valid Ethereum address"
                ))
        
        return issues
    
    def _validate_standard_input(self, source_code: str) -> List[SecurityIssue]:
        """Standard input validation"""
        
        issues = []
        
        # Check for forbidden patterns
        for pattern in self.validation_rules["input_validation"]["forbidden_patterns"]:
            matches = re.finditer(pattern, source_code, re.IGNORECASE)
            for match in matches:
                line_num = source_code[:match.start()].count('\n') + 1
                issues.append(SecurityIssue(
                    severity="critical",
                    category="code_injection",
                    title="Forbidden code pattern detected",
                    description=f"Potentially dangerous pattern: {pattern}",
                    location=f"line_{line_num}",
                    recommendation="Remove this pattern as it poses security risks"
                ))
        
        # Check for blacklisted patterns
        for pattern in self.pattern_blacklist:
            matches = re.finditer(pattern, source_code, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                line_num = source_code[:match.start()].count('\n') + 1
                issues.append(SecurityIssue(
                    severity="high",
                    category="vulnerable_pattern",
                    title="Vulnerable pattern detected",
                    description=f"Pattern {pattern} indicates a security vulnerability",
                    location=f"line_{line_num}",
                    recommendation="Review and fix this pattern"
                ))
        
        return issues
    
    def _validate_comprehensive_input(self, source_code: str) -> List[SecurityIssue]:
        """Comprehensive input validation"""
        
        issues = []
        
        # Check for sensitive data exposure
        for pattern_info in self.sensitive_data_patterns:
            matches = re.finditer(pattern_info["pattern"], source_code, re.IGNORECASE)
            for match in matches:
                line_num = source_code[:match.start()].count('\n') + 1
                issues.append(SecurityIssue(
                    severity="critical",
                    category="data_exposure",
                    title=f"Sensitive data detected: {pattern_info['type']}",
                    description=f"Potential exposure of {pattern_info['type']}",
                    location=f"line_{line_num}",
                    recommendation="Remove sensitive data from contract code"
                ))
        
        # Check for potential gas limit issues
        if source_code.count("for(") > 10:
            issues.append(SecurityIssue(
                severity="medium",
                category="gas_limit",
                title="High loop count",
                description="Multiple loops may cause gas limit issues",
                location="entire_contract",
                recommendation="Consider reducing loop iterations or using different patterns"
            ))
        
        # Check for excessive complexity
        complexity_indicators = ["if(", "else if", "for(", "while(", "switch"]
        complexity_score = sum(source_code.count(indicator) for indicator in complexity_indicators)
        
        if complexity_score > 50:
            issues.append(SecurityIssue(
                severity="medium",
                category="complexity",
                title="High contract complexity",
                description=f"Contract complexity score: {complexity_score}",
                location="entire_contract",
                recommendation="Consider simplifying contract logic"
            ))
        
        return issues
    
    async def validate_analysis_output(
        self, 
        analysis_results: Dict[str, Any],
        validation_level: ValidationLevel = ValidationLevel.STANDARD
    ) -> Tuple[bool, List[SecurityIssue]]:
        """
        Validate analysis output for security issues
        
        Args:
            analysis_results: Analysis results to validate
            validation_level: Level of validation to perform
            
        Returns:
            Tuple of (is_valid, security_issues)
        """
        
        issues = []
        
        # Size validation
        results_str = str(analysis_results)
        if len(results_str) > self.validation_rules["output_sanitization"]["max_response_size"]:
            issues.append(SecurityIssue(
                severity="high",
                category="output_validation",
                title="Response too large",
                description="Analysis results exceed maximum size",
                location="entire_response",
                recommendation="Reduce result size or implement pagination"
            ))
        
        # Check for potential code injection in output
        if self._contains_code_injection(analysis_results):
            issues.append(SecurityIssue(
                severity="critical",
                category="output_injection",
                title="Potential code injection in output",
                description="Output contains executable code patterns",
                location="analysis_results",
                recommendation="Sanitize output before returning to client"
            ))
        
        # Validate sensitive data handling
        if validation_level == ValidationLevel.COMPREHENSIVE:
            issues.extend(self._validate_output_data_protection(analysis_results))
        
        is_valid = not any(issue.severity in ["critical", "high"] for issue in issues)
        
        return is_valid, issues
    
    def _contains_code_injection(self, data: Any) -> bool:
        """Check if data contains potential code injection patterns"""
        
        if isinstance(data, str):
            injection_patterns = [
                r"<script[^>]*>",
                r"javascript:",
                r"on\w+\s*=",
                r"eval\s*\(",
                r"exec\s*\(",
            ]
            
            for pattern in injection_patterns:
                if re.search(pattern, data, re.IGNORECASE):
                    return True
        
        elif isinstance(data, dict):
            for value in data.values():
                if self._contains_code_injection(value):
                    return True
        
        elif isinstance(data, list):
            for item in data:
                if self._contains_code_injection(item):
                    return True
        
        return False
    
    def _validate_output_data_protection(self, analysis_results: Dict[str, Any]) -> List[SecurityIssue]:
        """Validate data protection in output"""
        
        issues = []
        
        # Check for sensitive data leakage
        results_str = str(analysis_results).lower()
        
        sensitive_keywords = [
            "private_key", "secret", "password", "api_key", "token"
        ]
        
        for keyword in sensitive_keywords:
            if keyword in results_str:
                issues.append(SecurityIssue(
                    severity="high",
                    category="data_leakage",
                    title=f"Sensitive data detected in output: {keyword}",
                    description=f"Output contains sensitive keyword: {keyword}",
                    location="analysis_results",
                    recommendation="Remove sensitive data from output"
                ))
        
        return issues
    
    async def validate_api_security(
        self, 
        request_data: Dict[str, Any],
        user_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, List[SecurityIssue]]:
        """
        Validate API request for security compliance
        
        Args:
            request_data: API request data
            user_context: User authentication context
            
        Returns:
            Tuple of (is_valid, security_issues)
        """
        
        issues = []
        
        # Rate limiting validation (would be implemented with Redis/DB)
        # This is a placeholder for actual rate limiting logic
        if not self._check_rate_limit(user_context):
            issues.append(SecurityIssue(
                severity="medium",
                category="rate_limit",
                title="Rate limit exceeded",
                description="Too many requests from this user",
                location="api_request",
                recommendation="Implement rate limiting"
            ))
        
        # Authentication validation
        if self.validation_rules["api_security"]["require_authentication"] and not user_context:
            issues.append(SecurityIssue(
                severity="high",
                category="authentication",
                title="Missing authentication",
                description="API requires authentication but none provided",
                location="api_request",
                recommendation="Provide valid authentication credentials"
            ))
        
        # Input size validation
        if len(str(request_data)) > 100_000:  # 100KB
            issues.append(SecurityIssue(
                severity="medium",
                category="input_validation",
                title="Request too large",
                description="API request exceeds maximum size",
                location="entire_request",
                recommendation="Reduce request size"
            ))
        
        is_valid = not any(issue.severity in ["critical", "high"] for issue in issues)
        
        return is_valid, issues
    
    def _check_rate_limit(self, user_context: Optional[Dict[str, Any]]) -> bool:
        """Check if user has exceeded rate limits"""
        # This would be implemented with actual rate limiting logic
        # For now, return True (no rate limiting)
        return True
    
    async def perform_penetration_test(
        self, 
        target_contract: str,
        test_level: ValidationLevel = ValidationLevel.STANDARD
    ) -> Dict[str, Any]:
        """
        Perform automated penetration testing on contract
        
        Args:
            target_contract: Contract source code or address
            test_level: Level of testing to perform
            
        Returns:
            Penetration test results
        """
        
        test_results = {
            "test_timestamp": datetime.utcnow().isoformat(),
            "test_level": test_level.value,
            "target_hash": hashlib.sha256(target_contract.encode()).hexdigest()[:16],
            "vulnerabilities_found": [],
            "security_score": 0,
            "recommendations": [],
            "test_coverage": {}
        }
        
        # Perform different levels of testing
        if test_level == ValidationLevel.BASIC:
            test_results.update(await self._basic_penetration_test(target_contract))
        elif test_level == ValidationLevel.STANDARD:
            test_results.update(await self._standard_penetration_test(target_contract))
        elif test_level == ValidationLevel.COMPREHENSIVE:
            test_results.update(await self._comprehensive_penetration_test(target_contract))
        
        # Calculate security score
        test_results["security_score"] = self._calculate_security_score(test_results["vulnerabilities_found"])
        
        return test_results
    
    async def _basic_penetration_test(self, contract: str) -> Dict[str, Any]:
        """Basic penetration testing"""
        
        vulnerabilities = []
        
        # Test for common vulnerabilities
        if "call{" in contract:
            vulnerabilities.append({
                "type": "reentrancy",
                "severity": "high",
                "description": "Potential reentrancy vulnerability detected",
                "confidence": 0.7
            })
        
        if "msg.sender == tx.origin" in contract:
            vulnerabilities.append({
                "type": "authorization_bypass",
                "severity": "high",
                "description": "tx.origin authorization bypass vulnerability",
                "confidence": 0.9
            })
        
        return {
            "vulnerabilities_found": vulnerabilities,
            "test_coverage": {
                "reentrancy": True,
                "authorization": True,
                "integer_overflow": False
            }
        }
    
    async def _standard_penetration_test(self, contract: str) -> Dict[str, Any]:
        """Standard penetration testing"""
        
        # Start with basic tests
        basic_results = await self._basic_penetration_test(contract)
        vulnerabilities = basic_results["vulnerabilities_found"]
        coverage = basic_results["test_coverage"]
        
        # Additional standard tests
        if "+=" in contract and "uint" in contract:
            vulnerabilities.append({
                "type": "integer_overflow",
                "severity": "medium",
                "description": "Potential integer overflow in arithmetic operations",
                "confidence": 0.6
            })
            coverage["integer_overflow"] = True
        
        if "require(" in contract and "block.timestamp" in contract:
            vulnerabilities.append({
                "type": "timestamp_dependency",
                "severity": "medium",
                "description": "Block timestamp dependency detected",
                "confidence": 0.8
            })
            coverage["timestamp_dependency"] = True
        
        return {
            "vulnerabilities_found": vulnerabilities,
            "test_coverage": coverage
        }
    
    async def _comprehensive_penetration_test(self, contract: str) -> Dict[str, Any]:
        """Comprehensive penetration testing"""
        
        # Start with standard tests
        standard_results = await self._standard_penetration_test(contract)
        vulnerabilities = standard_results["vulnerabilities_found"]
        coverage = standard_results["test_coverage"]
        
        # Additional comprehensive tests
        if "delegatecall" in contract:
            vulnerabilities.append({
                "type": "delegatecall_vulnerability",
                "severity": "critical",
                "description": "Unsafe delegatecall usage detected",
                "confidence": 0.8
            })
            coverage["delegatecall"] = True
        
        if "selfdestruct" in contract:
            vulnerabilities.append({
                "type": "selfdestruct_risk",
                "severity": "high",
                "description": "Selfdestruct function present",
                "confidence": 0.9
            })
            coverage["selfdestruct"] = True
        
        # Gas analysis
        loop_count = contract.count("for(") + contract.count("while(")
        if loop_count > 5:
            vulnerabilities.append({
                "type": "gas_limit_risk",
                "severity": "low",
                "description=f"High loop count ({loop_count}) may cause gas limit issues",
                "confidence": 0.7
            })
            coverage["gas_analysis"] = True
        
        return {
            "vulnerabilities_found": vulnerabilities,
            "test_coverage": coverage
        }
    
    def _calculate_security_score(self, vulnerabilities: List[Dict[str, Any]]) -> int:
        """Calculate security score based on found vulnerabilities"""
        
        if not vulnerabilities:
            return 100
        
        # Weight vulnerabilities by severity
        severity_weights = {
            "critical": 40,
            "high": 20,
            "medium": 10,
            "low": 5
        }
        
        total_deduction = 0
        for vuln in vulnerabilities:
            weight = severity_weights.get(vuln["severity"], 10)
            confidence = vuln.get("confidence", 0.5)
            total_deduction += weight * confidence
        
        score = max(0, 100 - int(total_deduction))
        
        return score
    
    def generate_security_report(
        self, 
        validation_results: Dict[str, Any],
        pen_test_results: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive security report"""
        
        report = {
            "report_timestamp": datetime.utcnow().isoformat(),
            "validation_summary": {
                "input_issues": len(validation_results.get("input_issues", [])),
                "output_issues": len(validation_results.get("output_issues", [])),
                "api_issues": len(validation_results.get("api_issues", [])),
                "overall_valid": validation_results.get("overall_valid", False)
            },
            "risk_assessment": {
                "critical_issues": 0,
                "high_issues": 0,
                "medium_issues": 0,
                "low_issues": 0
            },
            "recommendations": [],
            "compliance_status": "COMPLIANT"
        }
        
        # Count issues by severity
        all_issues = (
            validation_results.get("input_issues", []) +
            validation_results.get("output_issues", []) +
            validation_results.get("api_issues", [])
        )
        
        for issue in all_issues:
            severity = issue.get("severity", "low")
            report["risk_assessment"][f"{severity}_issues"] += 1
        
        # Add penetration test results if available
        if pen_test_results:
            report["penetration_test"] = {
                "security_score": pen_test_results.get("security_score", 0),
                "vulnerabilities_found": len(pen_test_results.get("vulnerabilities_found", [])),
                "test_coverage": pen_test_results.get("test_coverage", {})
            }
        
        # Determine compliance status
        if report["risk_assessment"]["critical_issues"] > 0:
            report["compliance_status"] = "NON_COMPLIANT"
        elif report["risk_assessment"]["high_issues"] > 3:
            report["compliance_status"] = "REQUIRES_REVIEW"
        
        # Generate recommendations
        if report["risk_assessment"]["critical_issues"] > 0:
            report["recommendations"].append("Address all critical security issues immediately")
        
        if report["risk_assessment"]["high_issues"] > 0:
            report["recommendations"].append("Review and fix high-severity vulnerabilities")
        
        if pen_test_results and pen_test_results.get("security_score", 100) < 70:
            report["recommendations"].append("Improve overall security posture based on penetration test results")
        
        return report
