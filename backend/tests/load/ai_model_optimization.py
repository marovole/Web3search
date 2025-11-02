"""
AI模型调用优化和缓存策略实施
针对Quick Chat和Deep Research的AI模型优化
"""

import asyncio
import time
import json
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from functools import wraps

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelType(Enum):
    """模型类型枚举"""
    FAST = "claude-3.5-haiku"      # 快速模型
    BALANCED = "claude-3.5-sonnet"  # 平衡模型
    DEEP = "claude-3.5-opus"        # 深度模型
    FALLBACK = "fallback"           # 降级模型

@dataclass
class ModelConfig:
    """模型配置"""
    model: str
    timeout: float
    max_tokens: int
    temperature: float
    cost_per_token: float
    expected_response_time: float

@dataclass
class CacheConfig:
    """缓存配置"""
    ttl: int
    max_size: int
    prefix: str
    enabled: bool

class AIModelOptimizer:
    """AI模型优化器"""
    
    def __init__(self):
        self.model_configs = self._initialize_model_configs()
        self.cache_configs = self._initialize_cache_configs()
        self.request_cache = {}
        self.performance_metrics = {}
        self.circuit_breakers = {}
        
    def _initialize_model_configs(self) -> Dict[str, ModelConfig]:
        """初始化模型配置"""
        return {
            "fast": ModelConfig(
                model="claude-3.5-haiku",
                timeout=2.0,
                max_tokens=1000,
                temperature=0.7,
                cost_per_token=0.00025,
                expected_response_time=1.5
            ),
            "balanced": ModelConfig(
                model="claude-3.5-sonnet",
                timeout=3.0,
                max_tokens=2000,
                temperature=0.7,
                cost_per_token=0.00075,
                expected_response_time=2.5
            ),
            "deep": ModelConfig(
                model="claude-3.5-opus",
                timeout=5.0,
                max_tokens=4000,
                temperature=0.5,
                cost_per_token=0.0015,
                expected_response_time=4.0
            ),
            "fallback": ModelConfig(
                model="fallback",
                timeout=0.5,
                max_tokens=500,
                temperature=0.7,
                cost_per_token=0.0,
                expected_response_time=0.1
            )
        }
    
    def _initialize_cache_configs(self) -> Dict[str, CacheConfig]:
        """初始化缓存配置"""
        return {
            "quick_chat": CacheConfig(ttl=300, max_size=1000, prefix="qc", enabled=True),
            "deep_research": CacheConfig(ttl=1800, max_size=500, prefix="dr", enabled=True),
            "common_questions": CacheConfig(ttl=3600, max_size=100, prefix="cq", enabled=True),
            "market_data": CacheConfig(ttl=60, max_size=2000, prefix="md", enabled=True)
        }
    
    def select_optimal_model(self, query: str, context: Dict[str, Any]) -> str:
        """选择最优模型"""
        query_length = len(query)
        query_lower = query.lower()
        
        # 快速查询场景
        if (query_length < 100 and 
            any(keyword in query_lower for keyword in ["price", "what is", "how much", "current"])):
            return "fast"
        
        # 中等复杂度查询
        elif (query_length < 300 and 
              any(keyword in query_lower for keyword in ["explain", "compare", "analysis"])):
            return "balanced"
        
        # 复杂查询
        elif (query_length >= 300 or 
              any(keyword in query_lower for keyword in ["deep", "comprehensive", "detailed"])):
            return "deep"
        
        # 默认平衡模型
        else:
            return "balanced"
    
    def optimize_prompt(self, query: str, context: Dict[str, Any], model_type: str) -> str:
        """优化提示词"""
        model_config = self.model_configs[model_type]
        
        # 根据模型类型调整提示词
        if model_type == "fast":
            return f"""
Answer this cryptocurrency question concisely: {query}

Context: {context.get('market_data', {})}
Provide a direct answer under 100 words.
            """.strip()
        
        elif model_type == "balanced":
            return f"""
Answer this cryptocurrency question: {query}

Context: {context.get('market_data', {})}
Additional info: {context.get('news_data', {})}
Provide a comprehensive answer under 200 words.
            """.strip()
        
        elif model_type == "deep":
            return f"""
Provide a detailed analysis of this cryptocurrency topic: {query}

Context:
- Market Data: {context.get('market_data', {})}
- News: {context.get('news_data', {})}
- Social Sentiment: {context.get('social_data', {})}
- Technical Indicators: {context.get('technical_data', {})}

Provide a thorough analysis with specific details and insights.
            """.strip()
        
        return query
    
    async def call_model_optimized(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """优化的模型调用"""
        start_time = time.time()
        
        try:
            # 1. 选择最优模型
            model_type = self.select_optimal_model(query, context)
            model_config = self.model_configs[model_type]
            
            # 2. 检查熔断器
            if self._is_circuit_breaker_open(model_type):
                logger.warning(f"Circuit breaker open for {model_type}, using fallback")
                model_type = "fallback"
                model_config = self.model_configs[model_type]
            
            # 3. 优化提示词
            optimized_prompt = self.optimize_prompt(query, context, model_type)
            
            # 4. 调用模型（带超时）
            response = await asyncio.wait_for(
                self._actual_model_call(model_config, optimized_prompt),
                timeout=model_config.timeout
            )
            
            # 5. 记录成功指标
            response_time = (time.time() - start_time) * 1000
            self._record_metrics(model_type, response_time, True)
            
            return {
                "content": response["content"],
                "model": model_config.model,
                "response_time": response_time,
                "model_type": model_type,
                "tokens_used": response.get("tokens_used", 0),
                "cost": response.get("tokens_used", 0) * model_config.cost_per_token,
                "cached": False
            }
            
        except asyncio.TimeoutError:
            # 超时处理
            self._record_metrics(model_type, (time.time() - start_time) * 1000, False)
            self._trigger_circuit_breaker(model_type)
            
            logger.warning(f"Model timeout for {model_type}, using fallback")
            return await self._get_fallback_response(query)
        
        except Exception as e:
            # 错误处理
            self._record_metrics(model_type, (time.time() - start_time) * 1000, False)
            logger.error(f"Model call failed: {e}")
            
            return await self._get_fallback_response(query)
    
    async def _actual_model_call(self, config: ModelConfig, prompt: str) -> Dict[str, Any]:
        """实际的模型调用（模拟）"""
        # 模拟AI模型调用延迟
        await asyncio.sleep(config.expected_response_time)
        
        # 模拟响应
        mock_response = {
            "content": f"Based on the query, here's the analysis using {config.model}...",
            "tokens_used": len(prompt.split()) + 50,  # 模拟token使用
            "model": config.model
        }
        
        return mock_response
    
    async def _get_fallback_response(self, query: str) -> Dict[str, Any]:
        """获取降级响应"""
        fallback_config = self.model_configs["fallback"]
        
        # 预定义的常见问题回答
        common_responses = {
            "bitcoin": "Bitcoin (BTC) is the first and largest cryptocurrency with a current market cap of over $800B.",
            "ethereum": "Ethereum (ETH) is the second largest cryptocurrency and a leading smart contract platform.",
            "price": "Cryptocurrency prices are highly volatile and change frequently based on market conditions.",
            "default": "I'm processing your request. For the most current information, please check reliable cryptocurrency data sources."
        }
        
        query_lower = query.lower()
        response_content = common_responses.get("default")
        
        for key, value in common_responses.items():
            if key in query_lower and key != "default":
                response_content = value
                break
        
        return {
            "content": response_content,
            "model": fallback_config.model,
            "response_time": fallback_config.expected_response_time * 1000,
            "model_type": "fallback",
            "tokens_used": 50,
            "cost": 0.0,
            "cached": False,
            "fallback": True
        }
    
    def _is_circuit_breaker_open(self, model_type: str) -> bool:
        """检查熔断器是否开启"""
        breaker = self.circuit_breakers.get(model_type, {"failures": 0, "last_failure": 0, "state": "closed"})
        
        if breaker["state"] == "open":
            # 检查是否应该进入半开状态
            if time.time() - breaker["last_failure"] > 60:  # 60秒后尝试半开
                breaker["state"] = "half_open"
                self.circuit_breakers[model_type] = breaker
                return False
            return True
        
        return False
    
    def _trigger_circuit_breaker(self, model_type: str):
        """触发熔断器"""
        breaker = self.circuit_breakers.get(model_type, {"failures": 0, "last_failure": 0, "state": "closed"})
        
        breaker["failures"] += 1
        breaker["last_failure"] = time.time()
        
        # 失败次数达到阈值时开启熔断器
        if breaker["failures"] >= 5:
            breaker["state"] = "open"
            logger.warning(f"Circuit breaker opened for {model_type}")
        
        self.circuit_breakers[model_type] = breaker
    
    def _record_metrics(self, model_type: str, response_time: float, success: bool):
        """记录性能指标"""
        if model_type not in self.performance_metrics:
            self.performance_metrics[model_type] = {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "total_response_time": 0,
                "response_times": []
            }
        
        metrics = self.performance_metrics[model_type]
        metrics["total_requests"] += 1
        metrics["total_response_time"] += response_time
        metrics["response_times"].append(response_time)
        
        if success:
            metrics["successful_requests"] += 1
        else:
            metrics["failed_requests"] += 1
        
        # 保持最近1000个响应时间样本
        if len(metrics["response_times"]) > 1000:
            metrics["response_times"] = metrics["response_times"][-1000:]

class SmartCacheManager:
    """智能缓存管理器"""
    
    def __init__(self):
        self.cache_store = {}
        self.cache_configs = {
            "quick_chat": {"ttl": 300, "max_size": 1000},
            "deep_research": {"ttl": 1800, "max_size": 500},
            "common_questions": {"ttl": 3600, "max_size": 100},
            "market_data": {"ttl": 60, "max_size": 2000}
        }
        self.access_patterns = {}
    
    def _generate_cache_key(self, query: str, context: Dict[str, Any], cache_type: str) -> str:
        """生成缓存键"""
        # 标准化查询
        normalized_query = query.strip().lower()
        
        # 包含关键上下文信息
        context_hash = ""
        if cache_type == "quick_chat" and "market_data" in context:
            context_hash = hashlib.md5(str(context["market_data"]).encode()).hexdigest()[:8]
        
        # 生成最终键
        key_data = f"{cache_type}:{normalized_query}:{context_hash}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def get_cached_response(self, query: str, context: Dict[str, Any], cache_type: str) -> Optional[Dict[str, Any]]:
        """获取缓存响应"""
        cache_key = self._generate_cache_key(query, context, cache_type)
        
        # 检查缓存是否存在
        if cache_key not in self.cache_store:
            return None
        
        cache_item = self.cache_store[cache_key]
        
        # 检查是否过期
        if time.time() - cache_item["timestamp"] > self.cache_configs[cache_type]["ttl"]:
            del self.cache_store[cache_key]
            return None
        
        # 更新访问模式
        self._update_access_pattern(cache_key)
        
        return {
            "content": cache_item["content"],
            "model": cache_item["model"],
            "response_time": 0.1,  # 缓存命中响应时间
            "cached": True,
            "cache_age": time.time() - cache_item["timestamp"]
        }
    
    async def cache_response(self, query: str, context: Dict[str, Any], response: Dict[str, Any], cache_type: str):
        """缓存响应"""
        cache_key = self._generate_cache_key(query, context, cache_type)
        config = self.cache_configs[cache_type]
        
        # 检查缓存大小限制
        if len(self.cache_store) >= config["max_size"]:
            await self._evict_cache_items(cache_type)
        
        # 存储到缓存
        self.cache_store[cache_key] = {
            "content": response["content"],
            "model": response["model"],
            "timestamp": time.time(),
            "cache_type": cache_type
        }
        
        logger.info(f"Cached response for {cache_type}: {cache_key[:16]}...")
    
    async def _evict_cache_items(self, cache_type: str):
        """淘汰缓存项"""
        # 找到该类型的所有缓存项
        type_items = [
            (key, item) for key, item in self.cache_store.items()
            if item.get("cache_type") == cache_type
        ]
        
        if not type_items:
            return
        
        # 按访问时间排序，删除最旧的25%
        type_items.sort(key=lambda x: x[1].get("last_access", x[1]["timestamp"]))
        
        evict_count = max(1, len(type_items) // 4)
        for i in range(evict_count):
            del self.cache_store[type_items[i][0]]
        
        logger.info(f"Evicted {evict_count} items from {cache_type} cache")
    
    def _update_access_pattern(self, cache_key: str):
        """更新访问模式"""
        if cache_key in self.cache_store:
            self.cache_store[cache_key]["last_access"] = time.time()
    
    async def preload_common_questions(self):
        """预加载常见问题"""
        common_questions = {
            "what is bitcoin": "Bitcoin (BTC) is the first decentralized cryptocurrency, created in 2009 by Satoshi Nakamoto.",
            "what is ethereum": "Ethereum (ETH) is a decentralized smart contract platform and the second largest cryptocurrency.",
            "btc price": "Bitcoin price varies based on market conditions. Check reliable sources for current pricing.",
            "eth price": "Ethereum price fluctuates with market dynamics. Refer to real-time data sources for current information.",
            "how to buy crypto": "You can buy cryptocurrencies through exchanges, brokers, or peer-to-peer platforms using fiat currency.",
            "is crypto safe": "Cryptocurrency investments carry risks including volatility, regulatory changes, and security concerns.",
            "what is blockchain": "Blockchain is a distributed ledger technology that records transactions across multiple computers.",
            "what is mining": "Cryptocurrency mining is the process of validating transactions and adding them to the blockchain."
        }
        
        for query, answer in common_questions.items():
            cache_key = self._generate_cache_key(query, {}, "common_questions")
            
            self.cache_store[cache_key] = {
                "content": answer,
                "model": "preloaded",
                "timestamp": time.time(),
                "cache_type": "common_questions"
            }
        
        logger.info(f"Preloaded {len(common_questions)} common questions")

class OptimizedAIEngine:
    """优化的AI引擎"""
    
    def __init__(self):
        self.model_optimizer = AIModelOptimizer()
        self.cache_manager = SmartCacheManager()
        self.request_queue = asyncio.Queue(maxsize=100)
        self.batch_processor = None
        
    async def initialize(self):
        """初始化引擎"""
        await self.cache_manager.preload_common_questions()
        self.batch_processor = asyncio.create_task(self._batch_processor())
        logger.info("✅ Optimized AI Engine initialized")
    
    async def quick_chat_optimized(self, query: str, session_id: str = None) -> Dict[str, Any]:
        """优化的Quick Chat实现"""
        start_time = time.time()
        
        try:
            # 1. 检查常见问题缓存
            cached_response = await self.cache_manager.get_cached_response(
                query, {}, "common_questions"
            )
            if cached_response:
                return self._build_quick_chat_response(cached_response, session_id)
            
            # 2. 检查查询缓存
            context = await self._get_quick_context(query)
            cached_response = await self.cache_manager.get_cached_response(
                query, context, "quick_chat"
            )
            if cached_response:
                return self._build_quick_chat_response(cached_response, session_id)
            
            # 3. 调用优化的AI模型
            ai_response = await self.model_optimizer.call_model_optimized(query, context)
            
            # 4. 缓存响应
            await self.cache_manager.cache_response(query, context, ai_response, "quick_chat")
            
            # 5. 构建最终响应
            return self._build_quick_chat_response(ai_response, session_id)
            
        except Exception as e:
            logger.error(f"Quick Chat optimized error: {e}")
            return self._build_error_response(str(e))
    
    async def deep_research_optimized(self, query: str, symbol: str) -> Dict[str, Any]:
        """优化的Deep Research实现"""
        start_time = time.time()
        
        try:
            # 1. 检查研究缓存
            context = {"symbol": symbol, "query": query}
            cached_response = await self.cache_manager.get_cached_response(
                f"{query}:{symbol}", context, "deep_research"
            )
            if cached_response:
                return self._build_deep_research_response(cached_response, query, symbol)
            
            # 2. 并行执行研究
            research_result = await self._parallel_research(query, symbol)
            
            # 3. 缓存结果
            await self.cache_manager.cache_response(
                f"{query}:{symbol}", context, research_result, "deep_research"
            )
            
            # 4. 构建响应
            return self._build_deep_research_response(research_result, query, symbol)
            
        except Exception as e:
            logger.error(f"Deep Research optimized error: {e}")
            return self._build_error_response(str(e))
    
    async def _get_quick_context(self, query: str) -> Dict[str, Any]:
        """获取Quick Chat上下文"""
        # 模拟获取市场数据
        context = {
            "market_data": {
                "top_coins": ["BTC", "ETH", "BNB"],
                "market_trend": "bullish"
            }
        }
        
        # 检查是否需要额外上下文
        if "price" in query.lower():
            context["market_data"]["price_info"] = "Real-time price data available"
        
        return context
    
    async def _parallel_research(self, query: str, symbol: str) -> Dict[str, Any]:
        """并行执行研究"""
        # 创建并行任务
        tasks = [
            self._collect_market_data(symbol),
            self._collect_news_data(symbol),
            self._collect_social_data(symbol),
            self._collect_technical_data(symbol)
        ]
        
        # 等待所有任务完成
        market_data, news_data, social_data, technical_data = await asyncio.gather(
            *tasks, return_exceptions=True
        )
        
        # 构建研究上下文
        context = {
            "market_data": market_data if not isinstance(market_data, Exception) else {},
            "news_data": news_data if not isinstance(news_data, Exception) else {},
            "social_data": social_data if not isinstance(social_data, Exception) else {},
            "technical_data": technical_data if not isinstance(technical_data, Exception) else {}
        }
        
        # 调用AI模型生成分析
        ai_response = await self.model_optimizer.call_model_optimized(
            f"Deep research analysis of {symbol}: {query}", context
        )
        
        return {
            "content": ai_response["content"],
            "model": ai_response["model"],
            "sections": {
                "market_overview": "Market data analysis...",
                "sentiment": "Social sentiment analysis...",
                "technical": "Technical indicators analysis...",
                "conclusion": ai_response["content"]
            },
            "data_sources": ["CoinGecko", "Twitter", "Reddit"],
            "generation_time": (time.time() - time.time()) * 1000  # 实际应该计算真实时间
        }
    
    async def _collect_market_data(self, symbol: str) -> Dict[str, Any]:
        """收集市场数据"""
        await asyncio.sleep(0.5)  # 模拟API调用
        return {"price": 45000, "change_24h": 2.5, "volume": 1000000000}
    
    async def _collect_news_data(self, symbol: str) -> List[Dict[str, Any]]:
        """收集新闻数据"""
        await asyncio.sleep(0.8)  # 模拟API调用
        return [{"title": f"Latest news about {symbol}", "sentiment": "positive"}]
    
    async def _collect_social_data(self, symbol: str) -> Dict[str, Any]:
        """收集社交媒体数据"""
        await asyncio.sleep(0.6)  # 模拟API调用
        return {"twitter_mentions": 1000, "reddit_posts": 500, "sentiment_score": 0.7}
    
    async def _collect_technical_data(self, symbol: str) -> Dict[str, Any]:
        """收集技术分析数据"""
        await asyncio.sleep(0.4)  # 模拟API调用
        return {"rsi": 65, "macd": "bullish", "trend": "upward"}
    
    def _build_quick_chat_response(self, ai_response: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """构建Quick Chat响应"""
        return {
            "content": ai_response["content"],
            "symbol": self._extract_symbol(ai_response["content"]),
            "query_type": self._classify_query_type(ai_response["content"]),
            "response_time": ai_response["response_time"],
            "model": ai_response["model"],
            "session_id": session_id or "generated_session_id",
            "cached": ai_response.get("cached", False),
            "optimization_info": {
                "model_type": ai_response.get("model_type", "unknown"),
                "tokens_used": ai_response.get("tokens_used", 0),
                "cost": ai_response.get("cost", 0.0)
            }
        }
    
    def _build_deep_research_response(self, research_result: Dict[str, Any], query: str, symbol: str) -> Dict[str, Any]:
        """构建Deep Research响应"""
        return {
            "symbol": symbol,
            "query": query,
            "tldr": research_result["content"][:200] + "...",
            "sections": research_result["sections"],
            "conclusion": research_result["content"],
            "data_sources": research_result["data_sources"],
            "models_used": [research_result["model"]],
            "generation_time": research_result["generation_time"],
            "quality_score": 85,  # 模拟质量分数
            "timestamp": time.time(),
            "cached": research_result.get("cached", False)
        }
    
    def _build_error_response(self, error_message: str) -> Dict[str, Any]:
        """构建错误响应"""
        return {
            "error": error_message,
            "content": "I apologize, but I'm unable to process your request at the moment. Please try again later.",
            "model": "error",
            "response_time": 0,
            "cached": False
        }
    
    def _extract_symbol(self, content: str) -> Optional[str]:
        """从内容中提取代币符号"""
        import re
        
        # 查找常见的加密货币符号
        symbols = ["BTC", "ETH", "BNB", "ADA", "SOL", "DOT", "AVAX", "MATIC"]
        
        for symbol in symbols:
            if symbol in content.upper():
                return symbol
        
        return None
    
    def _classify_query_type(self, content: str) -> str:
        """分类查询类型"""
        content_lower = content.lower()
        
        if "price" in content_lower:
            return "price"
        elif "market" in content_lower or "trend" in content_lower:
            return "market"
        elif "explain" in content_lower or "how" in content_lower:
            return "explanation"
        elif "compare" in content_lower:
            return "comparison"
        else:
            return "general"
    
    async def _batch_processor(self):
        """批处理器"""
        while True:
            try:
                # 等待批次
                batch = []
                while len(batch) < 10:
                    try:
                        item = await asyncio.wait_for(self.request_queue.get(), timeout=1.0)
                        batch.append(item)
                    except asyncio.TimeoutError:
                        if batch:
                            break
                
                if batch:
                    # 处理批次
                    await self._process_batch(batch)
                    
            except Exception as e:
                logger.error(f"Batch processor error: {e}")
                await asyncio.sleep(1)
    
    async def _process_batch(self, batch: List[Dict[str, Any]]):
        """处理批次"""
        # 这里可以实现批量处理逻辑
        # 例如批量调用AI模型、批量缓存更新等
        logger.info(f"Processing batch of {len(batch)} requests")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        metrics = {
            "model_performance": self.model_optimizer.performance_metrics,
            "cache_stats": {
                "total_cached_items": len(self.cache_manager.cache_store),
                "cache_types": {}
            },
            "circuit_breaker_status": self.model_optimizer.circuit_breakers
        }
        
        # 统计各类型缓存数量
        for key, item in self.cache_manager.cache_store.items():
            cache_type = item.get("cache_type", "unknown")
            if cache_type not in metrics["cache_stats"]["cache_types"]:
                metrics["cache_stats"]["cache_types"][cache_type] = 0
            metrics["cache_stats"]["cache_types"][cache_type] += 1
        
        return metrics

# 使用示例和测试
async def main():
    """主函数 - 演示AI模型优化"""
    print("🚀 Starting AI Model Optimization and Cache Strategy Implementation...")
    
    # 初始化优化的AI引擎
    ai_engine = OptimizedAIEngine()
    await ai_engine.initialize()
    
    # 测试Quick Chat优化
    print("\n📊 Testing Quick Chat Optimization...")
    
    test_queries = [
        "What is Bitcoin?",
        "What is the current price of ETH?",
        "Explain how blockchain works",
        "Compare BTC and ETH"
    ]
    
    for query in test_queries:
        start_time = time.time()
        response = await ai_engine.quick_chat_optimized(query)
        response_time = (time.time() - start_time) * 1000
        
        print(f"\nQuery: {query}")
        print(f"Response Time: {response_time:.0f}ms")
        print(f"Model: {response['model']}")
        print(f"Cached: {response.get('cached', False)}")
        print(f"Content: {response['content'][:100]}...")
    
    # 测试Deep Research优化
    print("\n🔬 Testing Deep Research Optimization...")
    
    research_queries = [
        ("Bitcoin", "BTC"),
        ("Ethereum ecosystem", "ETH")
    ]
    
    for query, symbol in research_queries:
        start_time = time.time()
        response = await ai_engine.deep_research_optimized(query, symbol)
        response_time = (time.time() - start_time) * 1000
        
        print(f"\nResearch: {query} ({symbol})")
        print(f"Response Time: {response_time:.0f}ms")
        print(f"Model: {response['models_used'][0] if response['models_used'] else 'unknown'}")
        print(f"Cached: {response.get('cached', False)}")
        print(f"Quality Score: {response.get('quality_score', 0)}")
    
    # 获取性能指标
    print("\n📈 Performance Metrics:")
    metrics = ai_engine.get_performance_metrics()
    
    print(f"Total Cached Items: {metrics['cache_stats']['total_cached_items']}")
    print(f"Cache Types: {metrics['cache_stats']['cache_types']}")
    
    for model_type, model_metrics in metrics['model_performance'].items():
        if model_metrics['total_requests'] > 0:
            avg_time = model_metrics['total_response_time'] / model_metrics['total_requests']
            success_rate = model_metrics['successful_requests'] / model_metrics['total_requests'] * 100
            print(f"{model_type.upper()}: {avg_time:.0f}ms avg, {success_rate:.1f}% success")
    
    print(f"Circuit Breaker Status: {metrics['circuit_breaker_status']}")
    
    # 保存优化配置
    optimization_config = {
        "model_configs": {k: asdict(v) for k, v in ai_engine.model_optimizer.model_configs.items()},
        "cache_configs": ai_engine.cache_manager.cache_configs,
        "performance_metrics": metrics,
        "implementation_timestamp": time.time()
    }
    
    with open("ai_optimization_config.json", "w") as f:
        json.dump(optimization_config, f, indent=2, default=str)
    
    print("\n✅ AI Model Optimization and Cache Strategy completed!")
    print("📁 Configuration saved to: ai_optimization_config.json")

if __name__ == "__main__":
    asyncio.run(main())
