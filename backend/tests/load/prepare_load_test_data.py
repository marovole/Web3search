"""
负载测试数据准备脚本
生成测试数据、预热缓存、准备测试环境
"""

import os
import json
import time
import random
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any
import asyncio
import aiohttp

class LoadTestDataPreparer:
    """负载测试数据准备器"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_data = {}
        
    def prepare_all_data(self):
        """准备所有测试数据"""
        print("🚀 Starting load test data preparation...")
        
        # 1. 生成测试查询数据
        self.generate_test_queries()
        
        # 2. 生成用户会话数据
        self.generate_user_sessions()
        
        # 3. 预热缓存
        self.warm_up_cache()
        
        # 4. 验证API端点
        self.verify_endpoints()
        
        # 5. 生成测试报告
        self.generate_preparation_report()
        
        print("✅ Load test data preparation completed!")
        
    def generate_test_queries(self):
        """生成测试查询数据"""
        print("\n📝 Generating test queries...")
        
        queries = {
            "simple_queries": [
                "What is Bitcoin?",
                "How is Ethereum today?", 
                "Tell me about Solana",
                "What are NFTs?",
                "Explain DeFi",
                "Best crypto to buy?",
                "Is blockchain safe?",
                "How to start crypto?",
                "What is staking?",
                "Explain smart contracts"
            ],
            
            "advanced_queries": [
                "Compare Ethereum vs Solana scalability",
                "Analyze Uniswap V3 vs V2 liquidity",
                "Explain Layer 2 rollup technologies",
                "DeFi yield farming risks analysis",
                "Smart contract security best practices",
                "Cross-chain bridge security risks",
                "MEV extraction mechanisms",
                "DAO governance models comparison",
                "Stablecoin mechanisms analysis",
                "Institutional crypto adoption trends"
            ],
            
            "trading_queries": [
                "Bitcoin price analysis today",
                "Ethereum technical analysis",
                "Should I buy Solana now?",
                "Uniswap price prediction",
                "AAVE investment analysis",
                "Chainlink market outlook",
                "Polygon trading signals",
                "Arbitrum price targets",
                "Optimism market analysis",
                "Avalanche trading opportunities"
            ],
            
            "research_queries": [
                "DeFi ecosystem comprehensive analysis",
                "Layer 2 scaling solutions deep dive",
                "Cross-chain interoperability research",
                "DAO governance mechanisms study",
                "NFT market dynamics analysis",
                "Stablecoin design comparison",
                "Blockchain oracle systems research",
                "Privacy-preserving technologies in crypto",
                "Environmental impact of consensus mechanisms",
                "Regulatory landscape for digital assets"
            ]
        }
        
        # 保存查询数据
        with open("test_queries.json", "w") as f:
            json.dump(queries, f, indent=2)
            
        self.test_data["queries"] = queries
        print(f"✅ Generated {len(queries)} query categories")
        
    def generate_user_sessions(self):
        """生成用户会话数据"""
        print("\n👥 Generating user sessions...")
        
        user_types = ["casual", "power", "trader", "researcher"]
        sessions = []
        
        # 生成1000个模拟用户会话
        for i in range(1000):
            session = {
                "session_id": f"session_{i:04d}",
                "user_type": random.choice(user_types),
                "start_time": datetime.now().isoformat(),
                "queries_per_session": random.randint(1, 20),
                "session_duration": random.randint(60, 1800),  # 1-30分钟
                "device_type": random.choice(["desktop", "mobile", "tablet"]),
                "location": random.choice(["US", "EU", "Asia", "Other"])
            }
            sessions.append(session)
            
        # 保存会话数据
        with open("user_sessions.json", "w") as f:
            json.dump(sessions, f, indent=2)
            
        self.test_data["sessions"] = sessions
        print(f"✅ Generated {len(sessions)} user sessions")
        
    def warm_up_cache(self):
        """预热缓存"""
        print("\n🔥 Warming up cache...")
        
        if not self.test_data.get("queries"):
            print("❌ No queries available for cache warmup")
            return
            
        success_count = 0
        total_count = 0
        
        # 预热简单查询缓存
        for query in self.test_data["queries"]["simple_queries"][:20]:
            try:
                response = self.session.post(
                    f"{self.base_url}/api/v1/chat/quick-chat",
                    json={"query": query, "conversation_id": None},
                    timeout=10
                )
                total_count += 1
                if response.status_code == 200:
                    success_count += 1
                    print(f"✅ Cached: {query[:30]}...")
                time.sleep(0.1)  # 避免过快请求
            except Exception as e:
                print(f"❌ Failed to cache: {query[:30]}... - {e}")
                
        # 预热热点数据
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/trending/hotspots?limit=20",
                timeout=10
            )
            total_count += 1
            if response.status_code == 200:
                success_count += 1
                print("✅ Cached hotspots data")
        except Exception as e:
            print(f"❌ Failed to cache hotspots: {e}")
            
        # 预热市场数据
        symbols = ["BTC", "ETH", "SOL", "UNI", "AAVE"]
        for symbol in symbols:
            try:
                response = self.session.get(
                    f"{self.base_url}/api/v1/market/data?symbol={symbol}",
                    timeout=10
                )
                total_count += 1
                if response.status_code == 200:
                    success_count += 1
                    print(f"✅ Cached market data: {symbol}")
                time.sleep(0.1)
            except Exception as e:
                print(f"❌ Failed to cache market data {symbol}: {e}")
                
        print(f"✅ Cache warmup completed: {success_count}/{total_count} successful")
        
    def verify_endpoints(self):
        """验证API端点"""
        print("\n🔍 Verifying API endpoints...")
        
        endpoints = [
            {"method": "GET", "path": "/health", "name": "Health Check"},
            {"method": "GET", "path": "/api/v1/trending/hotspots?limit=5", "name": "Hotspots"},
            {"method": "GET", "path": "/api/v1/search/autocomplete?q=BTC", "name": "Autocomplete"},
            {"method": "GET", "path": "/api/v1/market/data?symbol=BTC", "name": "Market Data"},
        ]
        
        results = []
        
        for endpoint in endpoints:
            try:
                start_time = time.time()
                if endpoint["method"] == "GET":
                    response = self.session.get(
                        f"{self.base_url}{endpoint['path']}",
                        timeout=10
                    )
                elif endpoint["method"] == "POST":
                    response = self.session.post(
                        f"{self.base_url}{endpoint['path']}",
                        json={"query": "Test query", "conversation_id": None},
                        timeout=10
                    )
                    
                duration = (time.time() - start_time) * 1000
                
                result = {
                    "name": endpoint["name"],
                    "method": endpoint["method"],
                    "path": endpoint["path"],
                    "status_code": response.status_code,
                    "response_time_ms": duration,
                    "success": response.status_code == 200
                }
                
                results.append(result)
                
                if result["success"]:
                    print(f"✅ {endpoint['name']}: {duration:.0f}ms")
                else:
                    print(f"❌ {endpoint['name']}: HTTP {response.status_code}")
                    
            except Exception as e:
                result = {
                    "name": endpoint["name"],
                    "method": endpoint["method"],
                    "path": endpoint["path"],
                    "status_code": 0,
                    "response_time_ms": 0,
                    "success": False,
                    "error": str(e)
                }
                results.append(result)
                print(f"❌ {endpoint['name']}: {e}")
                
        # 保存验证结果
        with open("endpoint_verification.json", "w") as f:
            json.dump(results, f, indent=2)
            
        self.test_data["endpoint_verification"] = results
        
        success_rate = sum(1 for r in results if r["success"]) / len(results) * 100
        print(f"✅ Endpoint verification completed: {success_rate:.1f}% success rate")
        
    def generate_preparation_report(self):
        """生成准备报告"""
        print("\n📊 Generating preparation report...")
        
        report = {
            "preparation_time": datetime.now().isoformat(),
            "base_url": self.base_url,
            "test_data_summary": {
                "query_categories": len(self.test_data.get("queries", {})),
                "user_sessions": len(self.test_data.get("sessions", [])),
                "endpoints_verified": len(self.test_data.get("endpoint_verification", []))
            },
            "endpoint_status": {
                "total": len(self.test_data.get("endpoint_verification", [])),
                "successful": sum(1 for e in self.test_data.get("endpoint_verification", []) if e.get("success", False)),
                "failed": sum(1 for e in self.test_data.get("endpoint_verification", []) if not e.get("success", False))
            }
        }
        
        # 计算成功率
        if report["endpoint_status"]["total"] > 0:
            report["endpoint_status"]["success_rate"] = (
                report["endpoint_status"]["successful"] / report["endpoint_status"]["total"] * 100
            )
        else:
            report["endpoint_status"]["success_rate"] = 0
            
        # 保存报告
        with open("preparation_report.json", "w") as f:
            json.dump(report, f, indent=2)
            
        print(f"✅ Preparation report generated")
        print(f"   - Query categories: {report['test_data_summary']['query_categories']}")
        print(f"   - User sessions: {report['test_data_summary']['user_sessions']}")
        print(f"   - Endpoints verified: {report['test_data_summary']['endpoints_verified']}")
        print(f"   - Success rate: {report['endpoint_status']['success_rate']:.1f}%")

class AsyncLoadTestDataPreparer:
    """异步负载测试数据准备器"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        
    async def warm_up_cache_async(self, queries: List[str], concurrency: int = 10):
        """异步预热缓存"""
        print(f"🔥 Async cache warmup with {concurrency} concurrent requests...")
        
        semaphore = asyncio.Semaphore(concurrency)
        
        async def warm_query(query: str):
            async with semaphore:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            f"{self.base_url}/api/v1/chat/quick-chat",
                            json={"query": query, "conversation_id": None},
                            timeout=aiohttp.ClientTimeout(total=10)
                        ) as response:
                            if response.status == 200:
                                print(f"✅ Cached: {query[:30]}...")
                                return True
                            else:
                                print(f"❌ Failed: {query[:30]}... - HTTP {response.status}")
                                return False
                except Exception as e:
                    print(f"❌ Error: {query[:30]}... - {e}")
                    return False
                    
        # 执行并发预热
        tasks = [warm_query(query) for query in queries[:50]]
        results = await asyncio.gather(*tasks)
        
        success_count = sum(results)
        print(f"✅ Async cache warmup completed: {success_count}/{len(results)} successful")
        
        return success_count, len(results)

def create_test_environment_script():
    """创建测试环境设置脚本"""
    script_content = """#!/bin/bash
# 负载测试环境设置脚本

set -e

echo "🚀 Setting up load test environment..."

# 创建必要的目录
mkdir -p reports
mkdir -p logs
mkdir -p data

# 检查Python依赖
echo "📦 Checking Python dependencies..."
pip install locust==2.20.0 gevent==23.7.0 requests aiohttp

# 检查系统资源
echo "💻 Checking system resources..."
echo "Available memory: $(free -h | grep '^Mem:' | awk '{print $7}')"
echo "CPU cores: $(nproc)"
echo "Disk space: $(df -h . | tail -1 | awk '{print $4}')"

# 检查文件描述符限制
echo "📁 Checking file descriptor limits..."
echo "Current ulimit: $(ulimit -n)"
if [ $(ulimit -n) -lt 65536 ]; then
    echo "⚠️  Warning: File descriptor limit is low. Consider running:"
    echo "   ulimit -n 65536"
fi

# 检查网络配置
echo "🌐 Checking network configuration..."
echo "Port range: $(sysctl net.ipv4.ip_local_port_range | cut -d'=' -f2)"

# 验证API服务
echo "🔍 Verifying API service..."
if curl -f -s http://localhost:8000/health > /dev/null; then
    echo "✅ API service is running"
else
    echo "❌ API service is not responding"
    echo "   Please start the API service before running load tests"
    exit 1
fi

# 准备测试数据
echo "📝 Preparing test data..."
python prepare_load_test_data.py

echo "✅ Load test environment setup completed!"
echo ""
echo "🎯 Next steps:"
echo "1. Run basic test: locust -f locustfile.py --host=http://localhost:8000"
echo "2. Run advanced test: locust -f advanced_user_behavior.py --host=http://localhost:8000"
echo "3. Run scenario test: python load_test_config.py"
"""
    
    with open("setup_test_environment.sh", "w") as f:
        f.write(script_content)
        
    os.chmod("setup_test_environment.sh", 0o755)
    print("✅ Created setup_test_environment.sh")

if __name__ == "__main__":
    import sys
    
    # 检查命令行参数
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    print(f"🎯 Preparing load test data for: {base_url}")
    
    # 创建数据准备器
    preparer = LoadTestDataPreparer(base_url)
    
    # 准备所有数据
    preparer.prepare_all_data()
    
    # 创建环境设置脚本
    create_test_environment_script()
    
    print("\n🎉 Load test data preparation completed!")
    print("📁 Generated files:")
    print("   - test_queries.json")
    print("   - user_sessions.json") 
    print("   - endpoint_verification.json")
    print("   - preparation_report.json")
    print("   - setup_test_environment.sh")
    print("\n🚀 Ready to run load tests!")
