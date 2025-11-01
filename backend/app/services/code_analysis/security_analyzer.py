"""
Security Vulnerability Analyzer
"""
from typing import Dict, Any, List
import re
import json
from datetime import datetime

from .base_analyzer import BaseCodeAnalyzer
from app.models.code_review import CodeReview, Vulnerability, VulnerabilitySeverity


class SecurityVulnerabilityAnalyzer(BaseCodeAnalyzer):
    """Analyzer for detecting security vulnerabilities in smart contracts"""
    
    def __init__(self, llm_service):
        super().__init__(llm_service)
        self.name = "SecurityVulnerabilityAnalyzer"
        
        # Common vulnerability patterns
        self.vulnerability_patterns = {
            "reentrancy": [
                r"\.call\{value:\s*.*?\}\(",
                r"\.send\(",
                r"\.transfer\(",
                r"external.*call.*\(",
            ],
            "integer_overflow": [
                r"\+\s*=",
                r"\*\s*=",
                r"-.*=",
                r"/.*=",
                r"uint256.*=.*\+",
                r"uint256.*=.*\*",
            ],
            "access_control": [
                r"function\s+\w+\s*public",
                r"function\s+\w+\s*external",
                r"modifier\s+onlyOwner",
                r"require\(msg\.sender",
            ],
            "unchecked_external_call": [
                r"\.call\(",
                r"\.delegatecall\(",
                r"\.staticcall\(",
            ],
            "logic_bomb": [
                r"require\(.*==.*false",
                r"if\(.*false.*\)",
                r"revert\(",
            ]
        }
    
    async def analyze(self, code_review: CodeReview, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze smart contract for security vulnerabilities"""
        
        # Prepare context
        analysis_context = await self.prepare_context(code_review)
        
        # Get appropriate model
        model = await self.get_model_for_task("complex")
        
        # Build prompt
        prompt = self._build_security_prompt(code_review.source_code, analysis_context)
        
        # Get AI analysis
        ai_response = await self.llm_service.generate_response(
            prompt=prompt,
            model=model,
            temperature=0.1,
            max_tokens=4000
        )
        
        # Parse AI response
        ai_vulnerabilities = self._parse_ai_response(ai_response)
        
        # Perform static analysis
        static_vulnerabilities = self._perform_static_analysis(code_review.source_code)
        
        # Combine results
        all_vulnerabilities = self._combine_vulnerabilities(ai_vulnerabilities, static_vulnerabilities)
        
        # Calculate severity distribution
        severity_stats = self._calculate_severity_stats(all_vulnerabilities)
        
        return {
            "vulnerabilities": all_vulnerabilities,
            "severity_distribution": severity_stats,
            "total_vulnerabilities": len(all_vulnerabilities),
            "high_risk_count": len([v for v in all_vulnerabilities if v["severity"] in ["critical", "high"]]),
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "model_used": model
        }
    
    def _build_security_prompt(self, source_code: str, context: Dict[str, Any]) -> str:
        """Build security analysis prompt"""
        
        prompt = f"""
You are a smart contract security expert. Analyze the following Solidity code for security vulnerabilities.

Contract Details:
- Network: {context.get('network', 'Unknown')}
- File Name: {context.get('file_name', 'Unknown')}
- Contract Name: {context.get('contract_name', 'Unknown')}
- Analysis Mode: {context.get('analysis_mode', 'thorough')}

Source Code:
```solidity
{source_code}
```

Please identify and analyze the following types of vulnerabilities:
1. Reentrancy attacks
2. Integer overflow/underflow
3. Access control issues
4. Unchecked external calls
5. Logic bombs and time-based attacks
6. Front-running susceptibility
7. Gas limit issues
8. Delegatecall vulnerabilities
9. Selfdestruct usage
10. Random number generation issues

For each vulnerability found, provide:
- Title and description
- Severity level (CRITICAL, HIGH, MEDIUM, LOW)
- Exact location (file, line number, function name)
- Vulnerable code snippet
- Detailed explanation of the risk
- Specific fix recommendation
- Fixed code example
- Related CVE/SWC references if applicable

Format your response as JSON:
{{
    "vulnerabilities": [
        {{
            "title": "Vulnerability Title",
            "description": "Detailed description",
            "severity": "CRITICAL|HIGH|MEDIUM|LOW",
            "category": "reentrancy|overflow|access_control|etc",
            "file_name": "contract.sol",
            "line_number": 123,
            "function_name": "withdraw",
            "code_snippet": "vulnerable code",
            "confidence": 0.95,
            "recommendation": "Fix description",
            "fixed_code": "fixed code example",
            "cve_id": "CVE-2023-XXXX",
            "swc_id": "SWC-107",
            "references": ["https://swcregistry.io/docs/SWC-107"]
        }}
    ]
}}

If no vulnerabilities are found, return an empty vulnerabilities array.
Focus on practical, exploitable vulnerabilities rather than theoretical issues.
"""
        
        return prompt
    
    def _parse_ai_response(self, ai_response: str) -> List[Dict[str, Any]]:
        """Parse AI response for vulnerabilities"""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', ai_response)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)
                return data.get("vulnerabilities", [])
            else:
                # Fallback: try to parse the entire response
                data = json.loads(ai_response)
                return data.get("vulnerabilities", [])
        except json.JSONDecodeError:
            # If JSON parsing fails, return empty list
            # In production, you might want to log this and try alternative parsing
            return []
    
    def _perform_static_analysis(self, source_code: str) -> List[Dict[str, Any]]:
        """Perform static analysis using pattern matching"""
        vulnerabilities = []
        lines = source_code.split('\n')
        
        for category, patterns in self.vulnerability_patterns.items():
            for pattern in patterns:
                for line_num, line in enumerate(lines, 1):
                    if re.search(pattern, line, re.IGNORECASE):
                        # Determine severity based on category
                        severity = self._get_pattern_severity(category)
                        
                        vuln = {
                            "title": f"Potential {category.replace('_', ' ').title()}",
                            "description": f"Static analysis detected potential {category} pattern",
                            "severity": severity,
                            "category": category,
                            "file_name": "contract.sol",
                            "line_number": line_num,
                            "function_name": self._extract_function_name(source_code, line_num),
                            "code_snippet": line.strip(),
                            "confidence": 0.7,  # Lower confidence for static analysis
                            "recommendation": f"Review this {category} pattern for proper security measures",
                            "fixed_code": None,
                            "cve_id": None,
                            "swc_id": None,
                            "references": []
                        }
                        vulnerabilities.append(vuln)
        
        return vulnerabilities
    
    def _get_pattern_severity(self, category: str) -> str:
        """Get severity level for pattern category"""
        severity_mapping = {
            "reentrancy": "HIGH",
            "integer_overflow": "HIGH", 
            "access_control": "HIGH",
            "unchecked_external_call": "MEDIUM",
            "logic_bomb": "CRITICAL"
        }
        return severity_mapping.get(category, "MEDIUM")
    
    def _extract_function_name(self, source_code: str, line_num: int) -> str:
        """Extract function name near a given line"""
        lines = source_code.split('\n')
        
        # Look for function definition within 5 lines before the target
        start = max(0, line_num - 6)
        for i in range(start, min(line_num, len(lines))):
            line = lines[i]
            func_match = re.search(r'function\s+(\w+)\s*\(', line)
            if func_match:
                return func_match.group(1)
        
        return "unknown"
    
    def _combine_vulnerabilities(self, ai_vulns: List[Dict], static_vulns: List[Dict]) -> List[Dict]:
        """Combine AI and static analysis results, removing duplicates"""
        combined = []
        
        # Add AI vulnerabilities first (higher confidence)
        for vuln in ai_vulns:
            vuln["source"] = "ai_analysis"
            combined.append(vuln)
        
        # Add static analysis vulnerabilities that aren't duplicates
        for static_vuln in static_vulns:
            is_duplicate = False
            
            for ai_vuln in ai_vulns:
                # Check if same line and category
                if (static_vuln["line_number"] == ai_vuln.get("line_number") and
                    static_vuln["category"] == ai_vuln.get("category")):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                static_vuln["source"] = "static_analysis"
                combined.append(static_vuln)
        
        # Sort by severity and confidence
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        combined.sort(key=lambda x: (
            severity_order.get(x["severity"], 3),
            -x.get("confidence", 0)
        ))
        
        return combined
    
    def _calculate_severity_stats(self, vulnerabilities: List[Dict]) -> Dict[str, int]:
        """Calculate severity distribution statistics"""
        stats = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0
        }
        
        for vuln in vulnerabilities:
            severity = vuln.get("severity", "LOW").lower()
            if severity in stats:
                stats[severity] += 1
        
        return stats
    
    def get_prompt_template(self) -> str:
        """Get the security analysis prompt template"""
        return self._build_security_prompt("", {})
    
    async def save_vulnerabilities(self, code_review: CodeReview, vulnerabilities: List[Dict]):
        """Save vulnerabilities to database"""
        from app.core.database import get_db
        
        async for db in get_db():
            try:
                for vuln_data in vulnerabilities:
                    vulnerability = Vulnerability(
                        code_review_id=code_review.id,
                        title=vuln_data["title"],
                        description=vuln_data["description"],
                        severity=VulnerabilitySeverity(vuln_data["severity"].lower()),
                        category=vuln_data["category"],
                        file_name=vuln_data.get("file_name"),
                        line_number=vuln_data.get("line_number"),
                        function_name=vuln_data.get("function_name"),
                        code_snippet=vuln_data.get("code_snippet"),
                        confidence=vuln_data.get("confidence"),
                        recommendation=vuln_data.get("recommendation"),
                        fixed_code=vuln_data.get("fixed_code"),
                        cve_id=vuln_data.get("cve_id"),
                        swc_id=vuln_data.get("swc_id"),
                        references=vuln_data.get("references", [])
                    )
                    db.add(vulnerability)
                
                await db.commit()
                
            except Exception as e:
                await db.rollback()
                raise e
