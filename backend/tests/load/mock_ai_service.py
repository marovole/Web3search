"""
Mock AI Service for Load Testing
模拟AI服务，用于负载测试
"""

import time
import random
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import asyncio

app = FastAPI(title="Mock AI Service", version="1.0.0")

class ChatRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    conversation_id: str
    response_time_ms: int

class ResearchRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None

class ResearchResponse(BaseModel):
    report: str
    conversation_id: str
    response_time_ms: int

# 预定义的响应模板
QUICK_RESPONSES = [
    "Bitcoin is the first and most well-known cryptocurrency, created by Satoshi Nakamoto in 2009.",
    "Ethereum is a decentralized platform that enables smart contracts and decentralized applications.",
    "Solana is a high-performance blockchain supporting builders around the world creating crypto apps.",
    "DeFi refers to financial services built on blockchain technology that offer transparency and accessibility.",
    "NFTs are unique digital assets that represent ownership of specific items or content.",
    "Smart contracts are self-executing contracts with the terms of the agreement directly written into code.",
    "Yield farming involves lending or staking cryptocurrency in exchange for interest and fees.",
    "Layer 2 solutions are built on top of existing blockchains to improve scalability and reduce fees.",
    "Staking is the process of participating in transaction validation on proof-of-stake blockchains.",
    "Cross-chain bridges enable the transfer of assets between different blockchain networks."
]

RESEARCH_REPORTS = [
    """
    # Comprehensive Bitcoin Analysis
    
    ## Overview
    Bitcoin (BTC) is the world's first cryptocurrency, created in 2009 by the pseudonymous Satoshi Nakamoto.
    
    ## Key Features
    - Decentralized digital currency
    - Limited supply of 21 million coins
    - Proof-of-work consensus mechanism
    - High security and network effects
    
    ## Market Performance
    - Market capitalization: $500B+
    - 24-hour trading volume: $20B+
    - Price volatility: High
    - Institutional adoption: Increasing
    
    ## Investment Considerations
    - Store of value properties
    - Inflation hedge potential
    - Regulatory uncertainty
    - Environmental concerns
    
    ## Technical Analysis
    - Strong support levels at key price points
    - Network hash rate continues to increase
    - Lightning Network adoption growing
    - Taproot upgrade improving privacy
    
    *Report generated with advanced AI analysis*
    """,
    
    """
    # Ethereum Ecosystem Deep Dive
    
    ## Introduction
    Ethereum is the leading smart contract platform, enabling decentralized applications and DeFi protocols.
    
    ## Technology Stack
    - Ethereum Virtual Machine (EVM)
    - Solidity programming language
    - Proof-of-stake consensus (The Merge)
    - Layer 2 scaling solutions
    
    ## DeFi Ecosystem
    - Total Value Locked: $30B+
    - Major protocols: Uniswap, Aave, Compound
    - Stablecoin integration: USDC, DAI, USDT
    - Yield farming opportunities
    
    ## Upcoming Developments
    - Ethereum 2.0 upgrades
    - Sharding implementation
    - Layer 2 rollup adoption
    - Cross-chain solutions
    
    ## Market Analysis
    - Gas fee optimization strategies
    - Network activity metrics
    - Developer ecosystem growth
    - Enterprise adoption trends
    
    *Comprehensive research analysis completed*
    """,
    
    """
    # Solana Blockchain Research Report
    
    ## Executive Summary
    Solana is a high-performance blockchain designed for scalability, supporting thousands of transactions per second.
    
    ## Technical Architecture
    - Proof-of-History consensus
    - Gulf Stream protocol
    - Turbine block propagation
    - Sealevel parallel processing
    
    ## Performance Metrics
    - Transaction throughput: 65,000 TPS
    - Block time: 400ms
    - Transaction cost: <$0.001
    - Network uptime: 99.9%+
    
    ## Ecosystem Analysis
    - DeFi protocols: Raydium, Serum, Mango
    - NFT platforms: Solanart, Magic Eden
    - Gaming projects: Star Atlas, Aurory
    - Web3 applications: Step Finance, Phantom
    
    ## Competitive Position
    - Speed advantage over competitors
    - Lower transaction costs
    - Growing developer community
    - Institutional partnerships
    
    ## Risk Factors
    - Network outages history
    - Centralization concerns
    - Competition from other L1s
    - Regulatory landscape
    
    *Detailed analysis with actionable insights*
    """
]

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "service": "mock-ai-service"}

@app.post("/api/v1/chat/quick-chat")
async def quick_chat(request: ChatRequest) -> ChatResponse:
    """模拟快速聊天API"""
    start_time = time.time()
    
    # 模拟处理延迟 (1-3秒)
    delay = random.uniform(1.0, 3.0)
    await asyncio.sleep(delay)
    
    # 根据查询关键词选择响应
    query_lower = request.query.lower()
    response_text = random.choice(QUICK_RESPONSES)
    
    # 模拟偶发错误 (1%概率)
    if random.random() < 0.01:
        raise HTTPException(status_code=500, detail="AI service temporarily unavailable")
    
    # 模拟速率限制 (5%概率)
    if random.random() < 0.05:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    processing_time = int((time.time() - start_time) * 1000)
    
    return ChatResponse(
        answer=response_text,
        conversation_id=request.conversation_id or "mock_conversation_123",
        response_time_ms=processing_time
    )

@app.post("/api/v1/chat/deep-research")
async def deep_research(request: ResearchRequest) -> ResearchResponse:
    """模拟深度研究API"""
    start_time = time.time()
    
    # 模拟处理延迟 (20-40秒)
    delay = random.uniform(20.0, 40.0)
    await asyncio.sleep(delay)
    
    # 根据查询内容选择报告
    query_lower = request.query.lower()
    if "bitcoin" in query_lower or "btc" in query_lower:
        report = RESEARCH_REPORTS[0]
    elif "ethereum" in query_lower or "eth" in query_lower:
        report = RESEARCH_REPORTS[1]
    elif "solana" in query_lower or "sol" in query_lower:
        report = RESEARCH_REPORTS[2]
    else:
        report = random.choice(RESEARCH_REPORTS)
    
    # 模拟偶发错误 (2%概率)
    if random.random() < 0.02:
        raise HTTPException(status_code=500, detail="Research service temporarily unavailable")
    
    # 模拟速率限制 (10%概率 - 深度研究限制更严格)
    if random.random() < 0.10:
        raise HTTPException(status_code=429, detail="Research rate limit exceeded")
    
    processing_time = int((time.time() - start_time) * 1000)
    
    return ResearchResponse(
        report=report,
        conversation_id=request.conversation_id or "mock_conversation_456",
        response_time_ms=processing_time
    )

@app.get("/api/v1/models/status")
async def models_status():
    """模型状态端点"""
    return {
        "quick_chat_model": {
            "status": "ready",
            "version": "1.0.0",
            "average_response_time_ms": 2000
        },
        "deep_research_model": {
            "status": "ready", 
            "version": "1.0.0",
            "average_response_time_ms": 30000
        }
    }

@app.get("/metrics")
async def metrics():
    """Prometheus指标端点"""
    return {
        "ai_requests_total": 1000,
        "ai_request_duration_seconds": 2.5,
        "ai_errors_total": 10,
        "ai_rate_limited_total": 50
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
