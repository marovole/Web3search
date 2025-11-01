"""
End-to-end tests for Code Review API
"""
import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import json
from datetime import datetime

from app.main import app
from app.models.code_review import BlockchainNetwork, CodeReviewStatus


@pytest.fixture
def client():
    """Test client for the API"""
    return TestClient(app)


@pytest.fixture
async def async_client():
    """Async test client for the API"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_contract_code():
    """Sample Solidity contract for testing"""
    return """
pragma solidity ^0.8.19;

// SPDX-License-Identifier: MIT
contract TestContract {
    mapping(address => uint) public balances;
    address public owner;
    
    constructor() {
        owner = msg.sender;
    }
    
    function deposit() public payable {
        balances[msg.sender] += msg.value;
    }
    
    function withdraw(uint amount) public {
        require(balances[msg.sender] >= amount, "Insufficient balance");
        (bool success,) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed");
        balances[msg.sender] -= amount;
    }
    
    function getBalance() public view returns (uint) {
        return balances[msg.sender];
    }
}
    """.strip()


@pytest.fixture
def sample_contract_address():
    """Sample contract address for testing"""
    return "0x1234567890123456789012345678901234567890"


class TestCodeReviewAPI:
    """End-to-end tests for code review API endpoints"""
    
    @pytest.mark.asyncio
    async def test_create_code_review_with_source_code(self, async_client, sample_contract_code):
        """Test creating a code review with source code"""
        
        # Mock the analysis orchestrator to avoid actual AI calls
        with patch('app.services.code_analysis.analysis_orchestrator.CodeAnalysisOrchestrator.run_analysis') as mock_analysis:
            mock_analysis.return_value = None
            
            response = await async_client.post("/api/v1/code-review/analyze", json={
                "source_code": sample_contract_code,
                "network": "ethereum",
                "contract_name": "TestContract",
                "file_name": "TestContract.sol",
                "language": "solidity",
                "analysis_mode": "quick"
            })
            
            assert response.status_code == 200
            
            data = response.json()
            assert "id" in data
            assert data["status"] == "pending"
            assert data["network"] == "ethereum"
            assert data["language"] == "solidity"
            assert data["analysis_mode"] == "quick"
            assert data["contract_name"] == "TestContract"
    
    @pytest.mark.asyncio
    async def test_create_code_review_with_contract_address(self, async_client, sample_contract_address):
        """Test creating a code review with contract address"""
        
        # Mock blockchain explorer service
        mock_contract_data = {
            "is_verified": True,
            "contract_name": "VerifiedContract",
            "source_code": sample_contract_code,
            "compiler_version": "v0.8.19+commit.7df6a131"
        }
        
        with patch('app.services.code_analysis.blockchain_explorer.BlockchainExplorerService.get_contract_source') as mock_explorer, \
             patch('app.services.code_analysis.analysis_orchestrator.CodeAnalysisOrchestrator.run_analysis') as mock_analysis:
            
            mock_explorer.return_value = mock_contract_data
            mock_analysis.return_value = None
            
            response = await async_client.post("/api/v1/code-review/analyze", json={
                "contract_address": sample_contract_address,
                "network": "ethereum",
                "analysis_mode": "thorough"
            })
            
            assert response.status_code == 200
            
            data = response.json()
            assert "id" in data
            assert data["status"] == "pending"
            assert data["contract_address"] == sample_contract_address
            assert data["network"] == "ethereum"
    
    @pytest.mark.asyncio
    async def test_create_code_review_validation_errors(self, async_client):
        """Test validation errors when creating code review"""
        
        # Test missing both source_code and contract_address
        response = await async_client.post("/api/v1/code-review/analyze", json={
            "network": "ethereum"
        })
        
        assert response.status_code == 400
        assert "Either source_code or contract_address must be provided" in response.json()["detail"]
        
        # Test invalid contract address format
        response = await async_client.post("/api/v1/code-review/analyze", json={
            "contract_address": "invalid_address",
            "network": "ethereum"
        })
        
        assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_get_code_review(self, async_client, sample_contract_code):
        """Test retrieving a code review"""
        
        # First create a code review
        with patch('app.services.code_analysis.analysis_orchestrator.CodeAnalysisOrchestrator.run_analysis'):
            create_response = await async_client.post("/api/v1/code-review/analyze", json={
                "source_code": sample_contract_code,
                "network": "ethereum"
            })
            
            review_id = create_response.json()["id"]
            
            # Then retrieve it
            response = await async_client.get(f"/api/v1/code-review/{review_id}")
            
            assert response.status_code == 200
            
            data = response.json()
            assert data["id"] == review_id
            assert "status" in data
            assert "created_at" in data
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_code_review(self, async_client):
        """Test retrieving a non-existent code review"""
        
        response = await async_client.get("/api/v1/code-review/nonexistent-id")
        
        assert response.status_code == 404
        assert "Code review not found" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_get_vulnerabilities(self, async_client, sample_contract_code):
        """Test retrieving vulnerabilities for a code review"""
        
        # Create a code review
        with patch('app.services.code_analysis.analysis_orchestrator.CodeAnalysisOrchestrator.run_analysis'):
            create_response = await async_client.post("/api/v1/code-review/analyze", json={
                "source_code": sample_contract_code,
                "network": "ethereum"
            })
            
            review_id = create_response.json()["id"]
            
            # Get vulnerabilities (should be empty initially)
            response = await async_client.get(f"/api/v1/code-review/{review_id}/vulnerabilities")
            
            assert response.status_code == 200
            assert isinstance(response.json(), list)
    
    @pytest.mark.asyncio
    async def test_get_vulnerabilities_with_filter(self, async_client, sample_contract_code):
        """Test retrieving vulnerabilities with severity filter"""
        
        # Create a code review
        with patch('app.services.code_analysis.analysis_orchestrator.CodeAnalysisOrchestrator.run_analysis'):
            create_response = await async_client.post("/api/v1/code-review/analyze", json={
                "source_code": sample_contract_code,
                "network": "ethereum"
            })
            
            review_id = create_response.json()["id"]
            
            # Get critical vulnerabilities only
            response = await async_client.get(f"/api/v1/code-review/{review_id}/vulnerabilities?severity=critical")
            
            assert response.status_code == 200
            assert isinstance(response.json(), list)
    
    @pytest.mark.asyncio
    async def test_get_quality_metrics(self, async_client, sample_contract_code):
        """Test retrieving quality metrics for a code review"""
        
        # Create a code review
        with patch('app.services.code_analysis.analysis_orchestrator.CodeAnalysisOrchestrator.run_analysis'):
            create_response = await async_client.post("/api/v1/code-review/analyze", json={
                "source_code": sample_contract_code,
                "network": "ethereum"
            })
            
            review_id = create_response.json()["id"]
            
            # Get quality metrics
            response = await async_client.get(f"/api/v1/code-review/{review_id}/quality-metrics")
            
            # Should return 404 since no analysis has been completed yet
            assert response.status_code in [200, 404]
    
    @pytest.mark.asyncio
    async def test_get_analysis_results(self, async_client, sample_contract_code):
        """Test retrieving detailed analysis results"""
        
        # Create a code review
        with patch('app.services.code_analysis.analysis_orchestrator.CodeAnalysisOrchestrator.run_analysis'):
            create_response = await async_client.post("/api/v1/code-review/analyze", json={
                "source_code": sample_contract_code,
                "network": "ethereum"
            })
            
            review_id = create_response.json()["id"]
            
            # Get analysis results
            response = await async_client.get(f"/api/v1/code-review/{review_id}/analysis-results")
            
            assert response.status_code == 200
            assert isinstance(response.json(), list)
    
    @pytest.mark.asyncio
    async def test_get_review_summary(self, async_client, sample_contract_code):
        """Test retrieving comprehensive review summary"""
        
        # Create a code review
        with patch('app.services.code_analysis.analysis_orchestrator.CodeAnalysisOrchestrator.run_analysis'):
            create_response = await async_client.post("/api/v1/code-review/analyze", json={
                "source_code": sample_contract_code,
                "network": "ethereum"
            })
            
            review_id = create_response.json()["id"]
            
            # Get summary
            response = await async_client.get(f"/api/v1/code-review/{review_id}/summary")
            
            assert response.status_code == 200
            
            data = response.json()
            assert "review_id" in data
            assert "status" in data
            assert "vulnerability_summary" in data
            assert "quality_summary" in data
            assert "analysis_summary" in data
    
    @pytest.mark.asyncio
    async def test_stream_analysis_progress(self, async_client, sample_contract_code):
        """Test streaming analysis progress using SSE"""
        
        # Create a code review
        with patch('app.services.code_analysis.analysis_orchestrator.CodeAnalysisOrchestrator.run_analysis'):
            create_response = await async_client.post("/api/v1/code-review/analyze", json={
                "source_code": sample_contract_code,
                "network": "ethereum"
            })
            
            review_id = create_response.json()["id"]
            
            # Test SSE endpoint
            response = await async_client.get(f"/api/v1/code-review/{review_id}/stream")
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
    
    @pytest.mark.asyncio
    async def test_retry_analysis(self, async_client, sample_contract_code):
        """Test retrying a failed analysis"""
        
        # Create a code review
        with patch('app.services.code_analysis.analysis_orchestrator.CodeAnalysisOrchestrator.run_analysis'):
            create_response = await async_client.post("/api/v1/code-review/analyze", json={
                "source_code": sample_contract_code,
                "network": "ethereum"
            })
            
            review_id = create_response.json()["id"]
            
            # Retry analysis
            with patch('app.services.code_analysis.analysis_orchestrator.CodeAnalysisOrchestrator.run_analysis') as mock_retry:
                mock_retry.return_value = None
                
                response = await async_client.post(f"/api/v1/code-review/{review_id}/retry")
                
                assert response.status_code == 200
                assert "Analysis retry started" in response.json()["message"]
    
    @pytest.mark.asyncio
    async def test_delete_code_review(self, async_client, sample_contract_code):
        """Test deleting a code review"""
        
        # Create a code review
        with patch('app.services.code_analysis.analysis_orchestrator.CodeAnalysisOrchestrator.run_analysis'):
            create_response = await async_client.post("/api/v1/code-review/analyze", json={
                "source_code": sample_contract_code,
                "network": "ethereum"
            })
            
            review_id = create_response.json()["id"]
            
            # Delete the code review
            response = await async_client.delete(f"/api/v1/code-review/{review_id}")
            
            assert response.status_code == 200
            assert "Code review deleted successfully" in response.json()["message"]
            
            # Verify it's deleted
            get_response = await async_client.get(f"/api/v1/code-review/{review_id}")
            assert get_response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_verify_contract(self, async_client, sample_contract_address):
        """Test contract verification endpoint"""
        
        # Mock blockchain explorer service
        mock_verification_data = {
            "is_verified": True,
            "contract_name": "VerifiedContract",
            "compiler_version": "v0.8.19+commit.7df6a131",
            "source_code": "pragma solidity ^0.8.19; contract VerifiedContract {}"
        }
        
        with patch('app.services.code_analysis.blockchain_explorer.BlockchainExplorerService.get_contract_source') as mock_explorer:
            mock_explorer.return_value = mock_verification_data
            
            response = await async_client.get(
                f"/api/v1/code-review/contracts/{sample_contract_address}/verify",
                params={"network": "ethereum"}
            )
            
            assert response.status_code == 200
            
            data = response.json()
            assert data["contract_address"] == sample_contract_address
            assert data["network"] == "ethereum"
            assert data["is_verified"] is True
            assert data["contract_name"] == "VerifiedContract"
    
    @pytest.mark.asyncio
    async def test_verify_unverified_contract(self, async_client, sample_contract_address):
        """Test verification of unverified contract"""
        
        # Mock blockchain explorer service returning None (unverified)
        with patch('app.services.code_analysis.blockchain_explorer.BlockchainExplorerService.get_contract_source') as mock_explorer:
            mock_explorer.return_value = None
            
            response = await async_client.get(
                f"/api/v1/code-review/contracts/{sample_contract_address}/verify",
                params={"network": "ethereum"}
            )
            
            assert response.status_code == 200
            
            data = response.json()
            assert data["contract_address"] == sample_contract_address
            assert data["network"] == "ethereum"
            assert data["is_verified"] is False
            assert data["source_code"] is None


class TestCodeReviewIntegration:
    """Integration tests for complete code review workflow"""
    
    @pytest.mark.asyncio
    async def test_complete_analysis_workflow(self, async_client, sample_contract_code):
        """Test complete analysis workflow from submission to results"""
        
        review_id = None
        
        try:
            # Step 1: Submit code for analysis
            with patch('app.services.code_analysis.analysis_orchestrator.CodeAnalysisOrchestrator.run_analysis') as mock_analysis:
                mock_analysis.return_value = None
                
                response = await async_client.post("/api/v1/code-review/analyze", json={
                    "source_code": sample_contract_code,
                    "network": "ethereum",
                    "analysis_mode": "thorough"
                })
                
                assert response.status_code == 200
                data = response.json()
                review_id = data["id"]
                assert data["status"] == "pending"
            
            # Step 2: Check analysis status
            response = await async_client.get(f"/api/v1/code-review/{review_id}")
            assert response.status_code == 200
            assert response.json()["id"] == review_id
            
            # Step 3: Get summary (should show pending status)
            response = await async_client.get(f"/api/v1/code-review/{review_id}/summary")
            assert response.status_code == 200
            summary = response.json()
            assert summary["status"] == "pending"
            
            # Step 4: Verify we can access all endpoints
            response = await async_client.get(f"/api/v1/code-review/{review_id}/vulnerabilities")
            assert response.status_code == 200
            
            response = await async_client.get(f"/api/v1/code-review/{review_id}/analysis-results")
            assert response.status_code == 200
            
        finally:
            # Cleanup: Delete the test review
            if review_id:
                await async_client.delete(f"/api/v1/code-review/{review_id}")
    
    @pytest.mark.asyncio
    async def test_contract_address_workflow(self, async_client, sample_contract_address):
        """Test workflow starting with contract address"""
        
        review_id = None
        
        try:
            # Step 1: Verify contract first
            mock_contract_data = {
                "is_verified": True,
                "contract_name": "VerifiedContract",
                "source_code": sample_contract_code,
                "compiler_version": "v0.8.19+commit.7df6a131"
            }
            
            with patch('app.services.code_analysis.blockchain_explorer.BlockchainExplorerService.get_contract_source') as mock_explorer, \
                 patch('app.services.code_analysis.analysis_orchestrator.CodeAnalysisOrchestrator.run_analysis') as mock_analysis:
                
                mock_explorer.return_value = mock_contract_data
                mock_analysis.return_value = None
                
                # Step 2: Submit contract address for analysis
                response = await async_client.post("/api/v1/code-review/analyze", json={
                    "contract_address": sample_contract_address,
                    "network": "ethereum",
                    "analysis_mode": "quick"
                })
                
                assert response.status_code == 200
                data = response.json()
                review_id = data["id"]
                assert data["contract_address"] == sample_contract_address
                assert data["status"] == "pending"
            
            # Step 3: Verify the review was created correctly
            response = await async_client.get(f"/api/v1/code-review/{review_id}")
            assert response.status_code == 200
            review_data = response.json()
            assert review_data["contract_address"] == sample_contract_address
            
        finally:
            # Cleanup
            if review_id:
                await async_client.delete(f"/api/v1/code-review/{review_id}")
    
    @pytest.mark.asyncio
    async def test_error_handling(self, async_client):
        """Test error handling in various scenarios"""
        
        # Test invalid review ID
        response = await async_client.get("/api/v1/code-review/invalid-id")
        assert response.status_code == 404
        
        # Test invalid contract address format
        response = await async_client.post("/api/v1/code-review/analyze", json={
            "contract_address": "invalid",
            "network": "ethereum"
        })
        assert response.status_code == 400
        
        # Test invalid network
        response = await async_client.post("/api/v1/code-review/analyze", json={
            "source_code": "contract Test {}",
            "network": "invalid_network"
        })
        assert response.status_code == 422  # Validation error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
