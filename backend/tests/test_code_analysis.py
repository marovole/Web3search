"""
Unit tests for code analysis services
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from app.services.code_analysis.security_analyzer import SecurityVulnerabilityAnalyzer
from app.services.code_analysis.quality_analyzer import CodeQualityAnalyzer
from app.models.code_review import CodeReview, BlockchainNetwork, CodeReviewStatus


@pytest.fixture
def mock_llm_service():
    """Mock LLM service for testing"""
    service = Mock()
    service.generate_response = AsyncMock()
    service.last_tokens_used = 1000
    service.last_model_used = "test-model"
    return service


@pytest.fixture
def sample_code_review():
    """Sample code review for testing"""
    return CodeReview(
        id="test-review-id",
        contract_address="0x1234567890123456789012345678901234567890",
        network=BlockchainNetwork.ETHEREUM,
        source_code="""
pragma solidity ^0.8.0;

contract VulnerableContract {
    mapping(address => uint) public balances;
    
    function withdraw() public {
        (bool success,) = msg.sender.call{value: balances[msg.sender]}("");
        require(success, "Transfer failed");
        balances[msg.sender] = 0;
    }
    
    function deposit() public payable {
        balances[msg.sender] += msg.value;
    }
}
        """.strip(),
        file_name="VulnerableContract.sol",
        language="solidity",
        analysis_mode="thorough",
        status=CodeReviewStatus.PENDING
    )


@pytest.fixture
def security_analyzer(mock_llm_service):
    """Security analyzer instance for testing"""
    return SecurityVulnerabilityAnalyzer(mock_llm_service)


@pytest.fixture
def quality_analyzer(mock_llm_service):
    """Quality analyzer instance for testing"""
    return CodeQualityAnalyzer(mock_llm_service)


class TestSecurityVulnerabilityAnalyzer:
    """Test cases for SecurityVulnerabilityAnalyzer"""
    
    @pytest.mark.asyncio
    async def test_analyze_vulnerabilities(self, security_analyzer, sample_code_review):
        """Test vulnerability analysis"""
        # Mock AI response
        mock_response = """
{
    "vulnerabilities": [
        {
            "title": "Reentrancy Vulnerability",
            "description": "The withdraw function is vulnerable to reentrancy attacks",
            "severity": "HIGH",
            "category": "reentrancy",
            "file_name": "VulnerableContract.sol",
            "line_number": 7,
            "function_name": "withdraw",
            "code_snippet": "(bool success,) = msg.sender.call{value: balances[msg.sender]}(\"\");",
            "confidence": 0.95,
            "recommendation": "Use the checks-effects-interactions pattern",
            "fixed_code": "uint amount = balances[msg.sender]; balances[msg.sender] = 0; (bool success,) = msg.sender.call{value: amount}(\"\");",
            "cve_id": "CVE-2023-1234",
            "swc_id": "SWC-107",
            "references": ["https://swcregistry.io/docs/SWC-107"]
        }
    ]
}
        """
        security_analyzer.llm_service.generate_response.return_value = mock_response
        
        # Analyze code
        context = await security_analyzer.prepare_context(sample_code_review)
        result = await security_analyzer.analyze(sample_code_review, context)
        
        # Assertions
        assert "vulnerabilities" in result
        assert len(result["vulnerabilities"]) == 1
        assert result["vulnerabilities"][0]["severity"] == "HIGH"
        assert result["vulnerabilities"][0]["category"] == "reentrancy"
        assert result["total_vulnerabilities"] == 1
        assert result["high_risk_count"] == 1
    
    @pytest.mark.asyncio
    async def test_static_analysis_detection(self, security_analyzer, sample_code_review):
        """Test static analysis pattern detection"""
        vulnerabilities = security_analyzer._perform_static_analysis(sample_code_review.source_code)
        
        # Should detect reentrancy pattern
        reentrancy_vulns = [v for v in vulnerabilities if v["category"] == "reentrancy"]
        assert len(reentrancy_vulns) > 0
        assert reentrancy_vulns[0]["severity"] == "HIGH"
    
    def test_pattern_severity_mapping(self, security_analyzer):
        """Test severity mapping for vulnerability patterns"""
        assert security_analyzer._get_pattern_severity("reentrancy") == "HIGH"
        assert security_analyzer._get_pattern_severity("integer_overflow") == "HIGH"
        assert security_analyzer._get_pattern_severity("access_control") == "HIGH"
        assert security_analyzer._get_pattern_severity("unchecked_external_call") == "MEDIUM"
        assert security_analyzer._get_pattern_severity("logic_bomb") == "CRITICAL"
    
    def test_function_name_extraction(self, security_analyzer):
        """Test function name extraction from source code"""
        source_code = """
pragma solidity ^0.8.0;
contract Test {
    function testFunction() public {
        // code here
    }
}
        """.strip()
        
        function_name = security_analyzer._extract_function_name(source_code, 3)
        assert function_name == "testFunction"
    
    @pytest.mark.asyncio
    async def test_validate_input(self, security_analyzer):
        """Test input validation"""
        # Valid code review
        valid_review = CodeReview(
            source_code="contract Test {}",
            network=BlockchainNetwork.ETHEREUM
        )
        assert security_analyzer.validate_input(valid_review) is True
        
        # Invalid code review (no source code)
        invalid_review = CodeReview(
            network=BlockchainNetwork.ETHEREUM
        )
        assert security_analyzer.validate_input(invalid_review) is False
        
        # Empty source code
        empty_review = CodeReview(
            source_code="   ",
            network=BlockchainNetwork.ETHEREUM
        )
        assert security_analyzer.validate_input(empty_review) is False


class TestCodeQualityAnalyzer:
    """Test cases for CodeQualityAnalyzer"""
    
    @pytest.mark.asyncio
    async def test_analyze_quality_metrics(self, quality_analyzer, sample_code_review):
        """Test quality analysis"""
        # Mock AI response
        mock_response = """
{
    "quality_score": 75.5,
    "quality_grade": "B+",
    "issues": [
        {
            "category": "documentation",
            "description": "Missing function documentation",
            "severity": "medium",
            "recommendation": "Add NatSpec comments for all public functions"
        }
    ],
    "recommendations": [
        "Add comprehensive documentation",
        "Improve function naming consistency"
    ],
    "best_practices": [
        "Use explicit function visibility",
        "Add input validation"
    ]
}
        """
        quality_analyzer.llm_service.generate_response.return_value = mock_response
        
        # Analyze code
        context = await quality_analyzer.prepare_context(sample_code_review)
        result = await quality_analyzer.analyze(sample_code_review, context)
        
        # Assertions
        assert "overall_score" in result
        assert "quality_grade" in result
        assert result["overall_score"] == 75.5
        assert result["quality_grade"] == "B+"
    
    def test_static_metrics_calculation(self, quality_analyzer):
        """Test static code metrics calculation"""
        source_code = """
pragma solidity ^0.8.0;
contract TestContract {
    uint public value;
    
    function function1() public {
        value = 1;
    }
    
    function function2() public {
        value = 2;
    }
}
        """.strip()
        
        metrics = quality_analyzer._calculate_static_metrics(source_code)
        
        assert metrics["total_lines"] > 0
        assert metrics["code_lines"] > 0
        assert metrics["function_count"] == 2
        assert metrics["average_function_length"] > 0
    
    def test_function_analysis(self, quality_analyzer):
        """Test function analysis"""
        source_code = """
contract Test {
    function shortFunction() public { }
    function longerFunction() public {
        uint x = 1;
        uint y = 2;
        uint z = x + y;
    }
}
        """.strip()
        
        functions = quality_analyzer._analyze_functions(source_code)
        
        assert functions["function_count"] == 2
        assert functions["average_function_length"] > 0
        assert len(functions["functions"]) == 2
    
    def test_complexity_analysis(self, quality_analyzer):
        """Test cyclomatic complexity analysis"""
        source_code = """
contract Test {
    function testFunction() public {
        if (true) {
            for (uint i = 0; i < 10; i++) {
                if (i > 5) {
                    break;
                }
            }
        }
    }
}
        """.strip()
        
        complexity = quality_analyzer._analyze_complexity(source_code)
        
        assert complexity["cyclomatic_complexity"] > 1
        assert "complexity_level" in complexity
        assert "maintainability_index" in complexity
    
    def test_standards_compliance(self, quality_analyzer):
        """Test Solidity standards compliance check"""
        # Code without pragma
        code_without_pragma = """
contract Test {
    function test() public {}
}
        """.strip()
        
        compliance = quality_analyzer._check_standards_compliance(code_without_pragma)
        
        assert compliance["follows_standards"] is False
        assert len(compliance["standards_violations"]) > 0
        assert any("pragma" in violation for violation in compliance["standards_violations"])
        
        # Code with pragma
        code_with_pragma = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;
contract Test {
    function test() public {}
}
        """.strip()
        
        compliance = quality_analyzer._check_standards_compliance(code_with_pragma)
        
        assert compliance["follows_standards"] is True
    
    def test_overall_score_calculation(self, quality_analyzer):
        """Test overall quality score calculation"""
        metrics = {
            "maintainability_index": 80,
            "comment_coverage": 60,
            "cyclomatic_complexity": 5,
            "follows_standards": True,
            "average_function_length": 15
        }
        
        score, grade = quality_analyzer._calculate_overall_score(metrics)
        
        assert 0 <= score <= 100
        assert grade in ["A+", "A", "B+", "B", "C+", "C", "D", "F"]


class TestAnalysisOrchestrator:
    """Test cases for CodeAnalysisOrchestrator"""
    
    @pytest.mark.asyncio
    async def test_prepare_analysis_context(self):
        """Test analysis context preparation"""
        from app.services.code_analysis.analysis_orchestrator import CodeAnalysisOrchestrator
        
        orchestrator = CodeAnalysisOrchestrator()
        code_review = CodeReview(
            source_code="contract Test {}",
            network=BlockchainNetwork.ETHEREUM,
            language="solidity",
            analysis_mode="thorough"
        )
        
        context = await orchestrator._prepare_analysis_context(code_review)
        
        assert context["network"] == "ethereum"
        assert context["language"] == "solidity"
        assert context["analysis_mode"] == "thorough"
        assert context["line_count"] > 0
        assert context["char_count"] > 0
    
    def test_confidence_score_calculation(self):
        """Test confidence score calculation"""
        from app.services.code_analysis.analysis_orchestrator import CodeAnalysisOrchestrator
        
        orchestrator = CodeAnalysisOrchestrator()
        
        # Results with high confidence
        results = {
            "security": {
                "analysis_data": {
                    "vulnerabilities": [
                        {"confidence": 0.9},
                        {"confidence": 0.8}
                    ]
                }
            },
            "quality": {
                "analysis_data": {
                    "overall_score": 85
                }
            }
        }
        
        confidence = orchestrator._calculate_confidence_score(results)
        assert 0 <= confidence <= 1
        assert confidence > 0.5  # Should be relatively high


class TestBlockchainExplorerService:
    """Test cases for BlockchainExplorerService"""
    
    @pytest.mark.asyncio
    async def test_contract_source_fetching(self):
        """Test contract source code fetching"""
        from app.services.code_analysis.blockchain_explorer import BlockchainExplorerService
        
        service = BlockchainExplorerService()
        
        # Mock successful API response
        mock_response_data = {
            "status": "1",
            "result": [{
                "ContractName": "TestContract",
                "CompilerVersion": "v0.8.0+commit.c7dfd78e",
                "SourceCode": "pragma solidity ^0.8.0; contract TestContract {}"
            }]
        }
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            result = await service.get_contract_source(
                "0x1234567890123456789012345678901234567890",
                "ethereum"
            )
            
            assert result is not None
            assert result["contract_name"] == "TestContract"
            assert result["is_verified"] is True
            assert "pragma solidity" in result["source_code"]
    
    def test_source_code_cleaning(self):
        """Test source code cleaning from explorer response"""
        from app.services.code_analysis.blockchain_explorer import BlockchainExplorerService
        
        service = BlockchainExplorerService()
        
        # Test single file contract
        single_file = "pragma solidity ^0.8.0; contract Test {}"
        cleaned = service._clean_source_code(single_file)
        assert cleaned == single_file
        
        # Test multi-file JSON format
        multi_file_json = """{
            "sources": {
                "contracts/Test.sol": {
                    "content": "pragma solidity ^0.8.0; contract Test {}"
                },
                "contracts/Helper.sol": {
                    "content": "pragma solidity ^0.8.0; contract Helper {}"
                }
            }
        }"""
        
        cleaned = service._clean_source_code(multi_file_json)
        assert "pragma solidity ^0.8.0; contract Test {}" in cleaned
        assert "pragma solidity ^0.8.0; contract Helper {}" in cleaned
    
    def test_address_validation(self):
        """Test contract address validation"""
        from app.services.code_analysis.blockchain_explorer import BlockchainExplorerService
        
        service = BlockchainExplorerService()
        
        # Valid addresses
        valid_addresses = [
            "0x1234567890123456789012345678901234567890",
            "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd"
        ]
        
        for addr in valid_addresses:
            assert service.validate_address(addr) is False  # Will return False without API call
        
        # Invalid addresses
        invalid_addresses = [
            "0x123",  # Too short
            "1234567890123456789012345678901234567890",  # Missing 0x
            "0xGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNO",  # Invalid characters
            ""  # Empty
        ]
        
        for addr in invalid_addresses:
            assert service.validate_address(addr) is False


@pytest.mark.asyncio
async def test_end_to_end_analysis_flow():
    """Test end-to-end analysis flow"""
    # This would be a comprehensive integration test
    # For now, we'll test the basic flow structure
    
    from app.services.code_analysis.analysis_orchestrator import CodeAnalysisOrchestrator
    
    orchestrator = CodeAnalysisOrchestrator()
    
    # Test that all analyzers are initialized
    assert len(orchestrator.analyzers) == 5
    assert "security" in orchestrator.analyzers
    assert "quality" in orchestrator.analyzers
    assert "architecture" in orchestrator.analyzers
    assert "gas" in orchestrator.analyzers
    assert "compliance" in orchestrator.analyzers


if __name__ == "__main__":
    pytest.main([__file__])
