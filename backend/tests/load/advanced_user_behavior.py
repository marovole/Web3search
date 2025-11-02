"""
真实用户行为模拟脚本
模拟不同类型用户的实际使用模式
"""

import random
import time
import json
from locust import HttpUser, task, between, events
from datetime import datetime, timedelta
import uuid

class UserBehavior:
    """用户行为基类"""
    
    def __init__(self, user):
        self.user = user
        self.session_id = str(uuid.uuid4())
        self.last_activity = datetime.now()
        
    def think_time(self, min_seconds=1, max_seconds=5):
        """模拟用户思考时间"""
        time.sleep(random.uniform(min_seconds, max_seconds))
        
    def browse_time(self):
        """模拟用户浏览时间"""
        time.sleep(random.uniform(3, 10))
        
    def should_perform_action(self, probability=0.3):
        """根据概率决定是否执行某个动作"""
        return random.random() < probability

class CasualUserBehavior(UserBehavior):
    """休闲用户行为模式 - 偶尔查询，浏览时间长"""
    
    def __init__(self, user):
        super().__init__(user)
        self.query_frequency = 0.2  # 20%概率进行查询
        
    def generate_simple_query(self):
        """生成简单查询"""
        queries = [
            "What is Bitcoin?",
            "How is Ethereum doing today?",
            "Tell me about Solana",
            "What are NFTs?",
            "Explain DeFi simply",
            "Best crypto to buy now?",
            "Is blockchain safe?",
            "How to start with crypto?"
        ]
        return random.choice(queries)
    
    def simulate_session(self):
        """模拟一次会话"""
        # 浏览首页
        self.user.client.get("/", name="Homepage")
        self.browse_time()
        
        # 可能进行搜索
        if self.should_perform_action(self.query_frequency):
            query = self.generate_simple_query()
            self.perform_quick_chat(query)
            
        # 查看热点
        if self.should_perform_action(0.4):
            self.get_hotspots()
            
        # 浏览更多内容
        self.browse_time()

class PowerUserBehavior(UserBehavior):
    """高级用户行为模式 - 频繁查询，使用高级功能"""
    
    def __init__(self, user):
        super().__init__(user)
        self.query_frequency = 0.7  # 70%概率进行查询
        self.deep_research_frequency = 0.1  # 10%概率进行深度研究
        
    def generate_advanced_query(self):
        """生成高级查询"""
        queries = [
            "Compare Ethereum vs Solana scalability solutions",
            "Analyze Uniswap V3 vs V2 liquidity provision",
            "Explain Layer 2 rollup technologies and their trade-offs",
            "What are the risks of yield farming in DeFi?",
            "How do smart contract audits work?",
            "Analyze the impact of institutional crypto adoption",
            "What are cross-chain bridges and their security risks?",
            "Explain tokenomics and valuation models for DeFi protocols",
            "How does MEV (Maximal Extractable Value) work?",
            "What are the regulatory challenges for crypto exchanges?"
        ]
        return random.choice(queries)
    
    def simulate_session(self):
        """模拟一次会话"""
        # 快速查询
        if self.should_perform_action(self.query_frequency):
            query = self.generate_advanced_query()
            self.perform_quick_chat(query)
            self.think_time(1, 3)
            
        # 深度研究
        if self.should_perform_action(self.deep_research_frequency):
            symbol = random.choice(["BTC", "ETH", "SOL", "UNI", "AAVE"])
            self.perform_deep_research(symbol)
            
        # 查看市场数据
        if self.should_perform_action(0.6):
            self.get_market_data()
            
        # 搜索自动补全
        if self.should_perform_action(0.5):
            self.search_autocomplete()

class TraderUserBehavior(UserBehavior):
    """交易者用户行为模式 - 关注市场数据，快速决策"""
    
    def __init__(self, user):
        super().__init__(user)
        self.market_data_frequency = 0.8  # 80%概率查看市场数据
        self.trading_pairs = [
            "BTC/USD", "ETH/USD", "SOL/USD", "UNI/USD", "AAVE/USD",
            "LINK/USD", "MATIC/USD", "ARB/USD", "OP/USD", "AVAX/USD"
        ]
        
    def generate_trading_query(self):
        """生成交易相关查询"""
        queries = [
            "What's the current market sentiment for Bitcoin?",
            "Should I buy Ethereum now?",
            "Analyze Solana price action",
            "What are the key resistance levels for UNI?",
            "Is AAVE a good investment right now?",
            "Market analysis for Chainlink",
            "Polygon technical analysis",
            "Arbitrum price prediction",
            "Optimism market outlook",
            "Avalanche trading opportunities"
        ]
        return random.choice(queries)
    
    def simulate_session(self):
        """模拟一次会话"""
        # 快速查看多个市场数据
        for _ in range(random.randint(2, 5)):
            symbol = random.choice(self.trading_pairs).split('/')[0]
            self.get_market_data(symbol)
            self.think_time(0.5, 2)
            
        # 交易相关查询
        if self.should_perform_action(0.6):
            query = self.generate_trading_query()
            self.perform_quick_chat(query)
            
        # 查看热点
        if self.should_perform_action(0.4):
            self.get_hotspots()

class ResearcherUserBehavior(UserBehavior):
    """研究员用户行为模式 - 深度分析，长期研究"""
    
    def __init__(self, user):
        super().__init__(user)
        self.research_frequency = 0.3  # 30%概率进行深度研究
        self.research_topics = [
            "DeFi ecosystem evolution",
            "Layer 2 scaling solutions comparison",
            "Cross-chain interoperability",
            "DAO governance models",
            "NFT market dynamics",
            "Stablecoin mechanisms",
            "Oracles and their role in DeFi",
            "Privacy in blockchain",
            "Environmental impact of PoW vs PoS",
            "Institutional adoption trends"
        ]
        
    def generate_research_query(self):
        """生成研究查询"""
        topic = random.choice(self.research_topics)
        return f"Provide comprehensive analysis on {topic}"
    
    def simulate_session(self):
        """模拟一次会话"""
        # 深度研究
        if self.should_perform_action(self.research_frequency):
            query = self.generate_research_query()
            self.perform_deep_research(query)
            self.browse_time()  # 研究后长时间浏览
            
        # 相关快速查询
        for _ in range(random.randint(1, 3)):
            if self.should_perform_action(0.7):
                query = self.generate_research_query()
                self.perform_quick_chat(query)
                self.think_time(2, 5)

class Web3SearchAdvancedUser(HttpUser):
    """
    高级Web3 Search用户模拟
    支持多种用户行为模式
    """
    
    # 用户类型分布
    USER_TYPES = {
        'casual': 0.4,      # 40% 休闲用户
        'power': 0.3,       # 30% 高级用户  
        'trader': 0.2,      # 20% 交易用户
        'researcher': 0.1   # 10% 研究员用户
    }
    
    # 请求间隔：根据用户类型调整
    wait_time = between(1, 4)
    
    def on_start(self):
        """用户开始时初始化"""
        # 随机分配用户类型
        user_type = random.choices(
            list(self.USER_TYPES.keys()),
            weights=list(self.USER_TYPES.values())
        )[0]
        
        # 根据用户类型设置行为
        if user_type == 'casual':
            self.behavior = CasualUserBehavior(self)
            self.wait_time = between(2, 6)  # 休闲用户间隔较长
        elif user_type == 'power':
            self.behavior = PowerUserBehavior(self)
            self.wait_time = between(1, 3)
        elif user_type == 'trader':
            self.behavior = TraderUserBehavior(self)
            self.wait_time = between(0.5, 2)  # 交易用户间隔较短
        else:  # researcher
            self.behavior = ResearcherUserBehavior(self)
            self.wait_time = between(3, 8)  # 研究员间隔很长
            
        self.user_type = user_type
        
        # 健康检查
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure("Health check failed")
                
        print(f"👤 {user_type.title()} user started (Session: {self.behavior.session_id[:8]})")

    @task(15)
    def simulate_user_session(self):
        """模拟完整的用户会话"""
        try:
            self.behavior.simulate_session()
            self.behavior.last_activity = datetime.now()
        except Exception as e:
            print(f"❌ Session error for {self.user_type}: {e}")
            
    def perform_quick_chat(self, query):
        """执行快速聊天"""
        payload = {
            "query": query,
            "conversation_id": self.behavior.session_id,
        }
        
        start_time = time.time()
        
        with self.client.post(
            "/api/v1/chat/quick-chat",
            json=payload,
            catch_response=True,
            name=f"/api/v1/chat/quick-chat [{self.user_type}]",
        ) as response:
            duration = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "answer" in data and len(data["answer"]) > 0:
                        response.success()
                        # 根据用户类型设置不同的性能期望
                        if self.user_type == 'trader' and duration < 2000:
                            print(f"⚡ {self.user_type}: {duration:.0f}ms (FAST)")
                        elif duration < 3000:
                            print(f"✅ {self.user_type}: {duration:.0f}ms")
                        else:
                            print(f"⚠️ {self.user_type}: {duration:.0f}ms (SLOW)")
                    else:
                        response.failure("Empty answer received")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            elif response.status_code == 429:
                print(f"⚠️ {self.user_type}: Rate limited")
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")
                
    def perform_deep_research(self, topic):
        """执行深度研究"""
        payload = {
            "query": topic,
            "conversation_id": self.behavior.session_id,
        }
        
        start_time = time.time()
        
        with self.client.post(
            "/api/v1/chat/deep-research",
            json=payload,
            timeout=90,
            catch_response=True,
            name=f"/api/v1/chat/deep-research [{self.user_type}]",
        ) as response:
            duration = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "report" in data and len(data["report"]) > 0:
                        response.success()
                        print(f"📊 {self.user_type} research: {duration:.0f}ms")
                    else:
                        response.failure("Empty report received")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            elif response.status_code == 429:
                print(f"⚠️ {self.user_type}: Research rate limited")
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")
                
    def get_hotspots(self):
        """获取热点"""
        with self.client.get(
            "/api/v1/trending/hotspots?limit=10",
            catch_response=True,
            name=f"/api/v1/trending/hotspots [{self.user_type}]",
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "hotspots" in data and len(data["hotspots"]) > 0:
                        response.success()
                    else:
                        response.failure("Empty hotspots list")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Status code: {response.status_code}")
                
    def get_market_data(self, symbol=None):
        """获取市场数据"""
        if not symbol:
            symbols = ["BTC", "ETH", "SOL", "UNI", "AAVE"]
            symbol = random.choice(symbols)
            
        with self.client.get(
            f"/api/v1/market/data?symbol={symbol}",
            catch_response=True,
            name=f"/api/v1/market/data [{self.user_type}]",
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "price" in data or "market_data" in data:
                        response.success()
                    else:
                        response.failure("Missing market data")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Status code: {response.status_code}")
                
    def search_autocomplete(self):
        """搜索自动补全"""
        symbols = ["BTC", "ETH", "SOL", "UNI", "AAVE", "LINK", "MATIC"]
        query = random.choice(symbols)
        
        with self.client.get(
            f"/api/v1/search/autocomplete?q={query}",
            catch_response=True,
            name=f"/api/v1/search/autocomplete [{self.user_type}]",
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "results" in data:
                        response.success()
                    else:
                        response.failure("Missing results field")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Status code: {response.status_code}")

# 事件处理器
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """测试开始时触发"""
    print("\n" + "=" * 60)
    print("🚀 Advanced User Behavior Load Test Starting")
    print("=" * 60)
    print(f"Target: {environment.host}")
    print(f"User Types: Casual(40%), Power(30%), Trader(20%), Researcher(10%)")
    print("=" * 60 + "\n")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """测试结束时触发"""
    print("\n" + "=" * 60)
    print("✅ Advanced User Behavior Load Test Completed")
    print("=" * 60)
    
    stats = environment.stats
    print(f"\n📊 Final Summary:")
    print(f"Total Requests: {stats.total.num_requests}")
    print(f"Failed Requests: {stats.total.num_failures}")
    print(f"Failure Rate: {stats.total.fail_ratio * 100:.2f}%")
    print(f"Avg Response Time: {stats.total.avg_response_time:.0f}ms")
    print(f"RPS: {stats.total.total_rps:.2f}")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║  Advanced User Behavior Simulation                          ║
    ╠══════════════════════════════════════════════════════════════╣
    ║  User Types:                                                ║
    ║  - Casual Users (40%): Light usage, long browse times      ║
    ║  - Power Users (30%): Frequent queries, advanced features  ║
    ║  - Traders (20%): Market data focused, quick decisions     ║
    ║  - Researchers (10%): Deep analysis, long sessions        ║
    ║                                                              ║
    ║  Usage:                                                      ║
    ║     locust -f advanced_user_behavior.py --host=<API_URL>    ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
