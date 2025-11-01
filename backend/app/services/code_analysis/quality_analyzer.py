"""
Code Quality Analyzer
"""
from typing import Dict, Any, List
import re
import json
from datetime import datetime

from .base_analyzer import BaseCodeAnalyzer
from app.models.code_review import CodeReview, CodeQualityMetric


class CodeQualityAnalyzer(BaseCodeAnalyzer):
    """Analyzer for assessing code quality metrics"""
    
    def __init__(self, llm_service):
        super().__init__(llm_service)
        self.name = "CodeQualityAnalyzer"
    
    async def analyze(self, code_review: CodeReview, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze code quality metrics"""
        
        # Prepare context
        analysis_context = await self.prepare_context(code_review)
        
        # Get appropriate model
        model = await self.get_model_for_task("medium")
        
        # Calculate static metrics first
        static_metrics = self._calculate_static_metrics(code_review.source_code)
        
        # Build prompt for AI analysis
        prompt = self._build_quality_prompt(code_review.source_code, static_metrics, analysis_context)
        
        # Get AI analysis
        ai_response = await self.llm_service.generate_response(
            prompt=prompt,
            model=model,
            temperature=0.2,
            max_tokens=3000
        )
        
        # Parse AI response
        ai_metrics = self._parse_ai_response(ai_response)
        
        # Combine static and AI metrics
        combined_metrics = self._combine_metrics(static_metrics, ai_metrics)
        
        # Calculate overall score and grade
        overall_score, grade = self._calculate_overall_score(combined_metrics)
        
        return {
            "overall_score": overall_score,
            "quality_grade": grade,
            "metrics": combined_metrics,
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "model_used": model
        }
    
    def _calculate_static_metrics(self, source_code: str) -> Dict[str, Any]:
        """Calculate static code metrics"""
        if not source_code:
            return {}
        
        lines = source_code.split('\n')
        code_lines = [line for line in lines if line.strip() and not line.strip().startswith('//')]
        
        # Basic metrics
        metrics = {
            "total_lines": len(lines),
            "code_lines": len(code_lines),
            "comment_lines": len([line for line in lines if line.strip().startswith('//')]),
            "empty_lines": len([line for line in lines if not line.strip()])
        }
        
        # Comment coverage
        if metrics["code_lines"] > 0:
            metrics["comment_coverage"] = (metrics["comment_lines"] / metrics["code_lines"]) * 100
        else:
            metrics["comment_coverage"] = 0
        
        # Function analysis
        functions = self._analyze_functions(source_code)
        metrics.update(functions)
        
        # Complexity analysis
        complexity = self._analyze_complexity(source_code)
        metrics.update(complexity)
        
        # Standards compliance
        compliance = self._check_standards_compliance(source_code)
        metrics.update(compliance)
        
        return metrics
    
    def _analyze_functions(self, source_code: str) -> Dict[str, Any]:
        """Analyze function-related metrics"""
        # Find all function definitions
        function_pattern = r'function\s+(\w+)\s*\([^)]*\)\s*(public|private|external|internal)?\s*(view|pure|payable)?\s*(returns\s*\([^)]*\))?\s*\{'
        functions = re.finditer(function_pattern, source_code, re.MULTILINE)
        
        function_details = []
        total_length = 0
        
        for match in functions:
            func_name = match.group(1)
            visibility = match.group(2) or "internal"
            
            # Find function body
            start_pos = match.end()
            brace_count = 1
            func_end = start_pos
            
            for i in range(start_pos, len(source_code)):
                if source_code[i] == '{':
                    brace_count += 1
                elif source_code[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        func_end = i + 1
                        break
            
            func_body = source_code[start_pos:func_end]
            func_lines = len(func_body.split('\n'))
            
            function_details.append({
                "name": func_name,
                "visibility": visibility,
                "lines": func_lines
            })
            
            total_length += func_lines
        
        if function_details:
            avg_length = total_length / len(function_details)
        else:
            avg_length = 0
        
        return {
            "function_count": len(function_details),
            "average_function_length": avg_length,
            "max_function_length": max([f["lines"] for f in function_details], default=0),
            "functions": function_details
        }
    
    def _analyze_complexity(self, source_code: str) -> Dict[str, Any]:
        """Analyze cyclomatic complexity"""
        # Count complexity contributors
        complexity_keywords = [
            r'\bif\b',
            r'\belse\b',
            r'\bfor\b',
            r'\bwhile\b',
            r'\bdo\b',
            r'\bswitch\b',
            r'\bcase\b',
            r'&&|\|\|',
            r'\?[^:]*:'
        ]
        
        complexity_score = 1  # Base complexity
        
        for pattern in complexity_keywords:
            matches = re.findall(pattern, source_code, re.IGNORECASE)
            complexity_score += len(matches)
        
        # Calculate maintainability index (simplified version)
        lines = source_code.split('\n')
        code_lines = len([line for line in lines if line.strip() and not line.strip().startswith('//')])
        
        if code_lines > 0:
            # Simplified maintainability index
            maintainability = max(0, 171 - 5.2 * (complexity_score ** 0.23) - 0.23 * complexity_score - 16.2 * (code_lines ** 0.5))
        else:
            maintainability = 100
        
        return {
            "cyclomatic_complexity": complexity_score,
            "maintainability_index": maintainability,
            "complexity_level": self._get_complexity_level(complexity_score)
        }
    
    def _get_complexity_level(self, complexity: int) -> str:
        """Get complexity level based on score"""
        if complexity <= 5:
            return "low"
        elif complexity <= 10:
            return "moderate"
        elif complexity <= 20:
            return "high"
        else:
            return "very_high"
    
    def _check_standards_compliance(self, source_code: str) -> Dict[str, Any]:
        """Check Solidity coding standards compliance"""
        violations = []
        
        # Check for pragma solidity
        if not re.search(r'pragma\s+solidity\s+\^?\d+\.\d+\.\d+', source_code):
            violations.append("Missing pragma solidity version")
        
        # Check for SPDX license identifier
        if not re.search(r'//\s*SPDX-License-Identifier:', source_code):
            violations.append("Missing SPDX license identifier")
        
        # Check for proper function visibility
        functions_no_visibility = re.findall(r'function\s+\w+\s*\([^)]*\)\s*(?!(public|private|external|internal))\s*\{', source_code)
        if functions_no_visibility:
            violations.append(f"Functions without explicit visibility: {len(functions_no_visibility)}")
        
        # Check for proper constructor naming
        if re.search(r'function\s+\w+\s*\([^)]*\)\s*\{[^}]*constructor', source_code):
            violations.append("Old-style constructor detected")
        
        return {
            "follows_standards": len(violations) == 0,
            "standards_violations": violations,
            "violation_count": len(violations)
        }
    
    def _build_quality_prompt(self, source_code: str, static_metrics: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Build quality analysis prompt"""
        
        prompt = f"""
You are a Solidity code quality expert. Analyze the following smart contract code for quality issues.

Contract Details:
- Network: {context.get('network', 'Unknown')}
- File Name: {context.get('file_name', 'Unknown')}
- Contract Name: {context.get('contract_name', 'Unknown')}

Static Metrics Already Calculated:
- Total Lines: {static_metrics.get('total_lines', 0)}
- Code Lines: {static_metrics.get('code_lines', 0)}
- Comment Coverage: {static_metrics.get('comment_coverage', 0):.1f}%
- Function Count: {static_metrics.get('function_count', 0)}
- Average Function Length: {static_metrics.get('average_function_length', 0):.1f}
- Cyclomatic Complexity: {static_metrics.get('cyclomatic_complexity', 0)}
- Maintainability Index: {static_metrics.get('maintainability_index', 0):.1f}

Source Code:
```solidity
{source_code}
```

Please analyze the code for:
1. Code organization and structure
2. Naming conventions and readability
3. Documentation quality
4. Error handling patterns
5. Code duplication
6. Design patterns usage
7. Gas optimization opportunities
8. Best practices adherence

Provide a quality assessment with:
- Overall quality score (0-100)
- Quality grade (A+, A, B+, B, C+, C, D, F)
- Specific quality issues found
- Improvement recommendations
- Best practices that should be implemented

Format your response as JSON:
{{
    "quality_score": 85.5,
    "quality_grade": "B+",
    "issues": [
        {{
            "category": "documentation",
            "description": "Missing function documentation",
            "severity": "medium",
            "recommendation": "Add NatSpec comments for all public functions"
        }}
    ],
    "recommendations": [
        "Add comprehensive documentation",
        "Improve function naming consistency",
        "Reduce function complexity"
    ],
    "best_practices": [
        "Use explicit function visibility",
        "Add input validation",
        "Implement proper error handling"
    ]
}}
"""
        
        return prompt
    
    def _parse_ai_response(self, ai_response: str) -> Dict[str, Any]:
        """Parse AI response for quality metrics"""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', ai_response)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            else:
                # Fallback: try to parse the entire response
                return json.loads(ai_response)
        except json.JSONDecodeError:
            # If JSON parsing fails, return empty metrics
            return {}
    
    def _combine_metrics(self, static_metrics: Dict[str, Any], ai_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Combine static and AI metrics"""
        combined = static_metrics.copy()
        
        # Add AI metrics if available
        if "quality_score" in ai_metrics:
            combined["ai_quality_score"] = ai_metrics["quality_score"]
        
        if "issues" in ai_metrics:
            combined["quality_issues"] = ai_metrics["issues"]
        
        if "recommendations" in ai_metrics:
            combined["recommendations"] = ai_metrics["recommendations"]
        
        if "best_practices" in ai_metrics:
            combined["best_practices"] = ai_metrics["best_practices"]
        
        return combined
    
    def _calculate_overall_score(self, metrics: Dict[str, Any]) -> tuple[float, str]:
        """Calculate overall quality score and grade"""
        
        # Weight different components
        weights = {
            "maintainability_index": 0.3,
            "comment_coverage": 0.2,
            "complexity_score": 0.2,
            "standards_compliance": 0.15,
            "function_analysis": 0.15
        }
        
        # Normalize metrics to 0-100 scale
        scores = {}
        
        # Maintainability (already 0-100)
        scores["maintainability_index"] = metrics.get("maintainability_index", 0)
        
        # Comment coverage (already 0-100)
        scores["comment_coverage"] = metrics.get("comment_coverage", 0)
        
        # Complexity (inverse - lower complexity is better)
        complexity = metrics.get("cyclomatic_complexity", 50)
        scores["complexity_score"] = max(0, 100 - (complexity * 2))
        
        # Standards compliance
        if metrics.get("follows_standards", False):
            scores["standards_compliance"] = 100
        else:
            violations = metrics.get("violation_count", 1)
            scores["standards_compliance"] = max(0, 100 - (violations * 20))
        
        # Function analysis
        avg_length = metrics.get("average_function_length", 50)
        if avg_length <= 20:
            scores["function_analysis"] = 100
        elif avg_length <= 50:
            scores["function_analysis"] = 80
        elif avg_length <= 100:
            scores["function_analysis"] = 60
        else:
            scores["function_analysis"] = 40
        
        # Calculate weighted average
        overall_score = sum(scores[component] * weight for component, weight in weights.items())
        
        # Determine grade
        if overall_score >= 95:
            grade = "A+"
        elif overall_score >= 90:
            grade = "A"
        elif overall_score >= 85:
            grade = "B+"
        elif overall_score >= 80:
            grade = "B"
        elif overall_score >= 75:
            grade = "C+"
        elif overall_score >= 70:
            grade = "C"
        elif overall_score >= 60:
            grade = "D"
        else:
            grade = "F"
        
        return round(overall_score, 1), grade
    
    def get_prompt_template(self) -> str:
        """Get the quality analysis prompt template"""
        return self._build_quality_prompt("", {}, {})
    
    async def save_quality_metrics(self, code_review: CodeReview, metrics: Dict[str, Any]):
        """Save quality metrics to database"""
        from app.core.database import get_db
        
        async for db in get_db():
            try:
                quality_metric = CodeQualityMetric(
                    code_review_id=code_review.id,
                    overall_score=metrics.get("overall_score", 0),
                    quality_grade=metrics.get("quality_grade", "F"),
                    complexity_score=metrics.get("cyclomatic_complexity"),
                    maintainability_index=metrics.get("maintainability_index"),
                    code_duplication_percentage=metrics.get("code_duplication_percentage"),
                    comment_coverage_percentage=metrics.get("comment_coverage"),
                    function_count=metrics.get("function_count"),
                    average_function_length=metrics.get("average_function_length"),
                    follows_standards=metrics.get("follows_standards", False),
                    standards_violations=metrics.get("standards_violations", [])
                )
                db.add(quality_metric)
                await db.commit()
                
            except Exception as e:
                await db.rollback()
                raise e
