"""
关键API端点性能优化脚本
针对具体端点实施性能优化措施
"""

import asyncio
import time
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from functools import wraps, lru_cache
import aiohttp
import aioredis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, Index
from contextlib import asynccontextmanager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class EndpointMetrics:
    """端点性能指标"""
    endpoint: str
    avg_response_time: float
    p95_response_time: float
    p99_response_time: float
    error_rate: float
    throughput: float
    cache_hit_rate: float = 0.0
    optimization_score: float = 0.0

@dataclass
class OptimizationAction:
    """优化动作"""
    action_type: str
    description: str
    implementation_code: str
    expected_improvement: float
    implementation_cost: str
    priority: int

class CriticalEndpointOptimizer:
    """关键端点优化器"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client: Optional[aioredis.Redis] = None
        self.optimization_cache = {}
        
    async def initialize(self):
        """初始化优化器"""
        try:
            self.redis_client = aioredis.from_url(self.redis_url)
            await self.redis_client.ping()
            logger.info("✅ Redis connected for optimization")
        except Exception as e:
            logger.warning(f"⚠️ Redis connection failed: {e}")
    
    async def optimize_quick_chat_endpoint(self) -> Dict[str, Any]:
        """优化Quick Chat端点"""
        logger.info("🚀 Optimizing Quick Chat endpoint...")
        
        optimizations = []
        
        # 1. 响应缓存优化
        cache_optimization = OptimizationAction(
            action_type="response_caching",
            description="实现智能响应缓存，缓存常见问题答案",
            implementation_code=self._get_quick_chat_cache_code(),
            expected_improvement=60.0,
            implementation_cost="low",
            priority=1
        )
        optimizations.append(cache_optimization)
        
        # 2. AI模型调用优化
        ai_optimization = OptimizationAction(
            action_type="ai_model_optimization",
            description="优化AI模型调用，使用更快的模型和并行处理",
            implementation_code=self._get_ai_optimization_code(),
            expected_improvement=35.0,
            implementation_cost="medium",
            priority=2
        )
        optimizations.append(ai_optimization)
        
        # 3. 数据预加载优化
        preload_optimization = OptimizationAction(
            action_type="data_preloading",
            description="预加载热门币种数据，减少实时查询延迟",
            implementation_code=self._get_preload_optimization_code(),
            expected_improvement=25.0,
            implementation_cost="medium",
            priority=3
        )
        optimizations.append(preload_optimization)
        
        # 4. 连接池优化
        connection_optimization = OptimizationAction(
            action_type="connection_pooling",
            description="优化数据库和外部API连接池配置",
            implementation_code=self._get_connection_pool_code(),
            expected_improvement=15.0,
            implementation_cost="low",
            priority=4
        )
        optimizations.append(connection_optimization)
        
        return {
            "endpoint": "/api/v1/chat/quick-chat",
            "optimizations": [asdict(opt) for opt in optimizations],
            "total_expected_improvement": sum(opt.expected_improvement for opt in optimizations),
            "implementation_priority": "critical"
        }
    
    async def optimize_deep_research_endpoint(self) -> Dict[str, Any]:
        """优化Deep Research端点"""
        logger.info("🔬 Optimizing Deep Research endpoint...")
        
        optimizations = []
        
        # 1. 并行数据处理
        parallel_optimization = OptimizationAction(
            action_type="parallel_processing",
            description="并行执行各个维度的数据收集和分析",
            implementation_code=self._get_parallel_processing_code(),
            expected_improvement=45.0,
            implementation_cost="high",
            priority=1
        )
        optimizations.append(parallel_optimization)
        
        # 2. 分层缓存策略
        cache_optimization = OptimizationAction(
            action_type="layered_caching",
            description="实现分层缓存，缓存中间分析结果",
            implementation_code=self._get_layered_cache_code(),
            expected_improvement=30.0,
            implementation_cost="medium",
            priority=2
        )
        optimizations.append(cache_optimization)
        
        # 3. 流式响应优化
        streaming_optimization = OptimizationAction(
            action_type="streaming_optimization",
            description="优化流式响应，提前返回部分结果",
            implementation_code=self._get_streaming_optimization_code(),
            expected_improvement=20.0,
            implementation_cost="medium",
            priority=3
        )
        optimizations.append(streaming_optimization)
        
        return {
            "endpoint": "/api/v1/chat/deep-research",
            "optimizations": [asdict(opt) for opt in optimizations],
            "total_expected_improvement": sum(opt.expected_improvement for opt in optimizations),
            "implementation_priority": "critical"
        }
    
    async def optimize_autocomplete_endpoint(self) -> Dict[str, Any]:
        """优化搜索自动补全端点"""
        logger.info("🔍 Optimizing Autocomplete endpoint...")
        
        optimizations = []
        
        # 1. 搜索索引优化
        index_optimization = OptimizationAction(
            action_type="search_index",
            description="建立专门的搜索索引，支持模糊匹配和前缀搜索",
            implementation_code=self._get_search_index_code(),
            expected_improvement=70.0,
            implementation_cost="medium",
            priority=1
        )
        optimizations.append(index_optimization)
        
        # 2. 结果缓存优化
        cache_optimization = OptimizationAction(
            action_type="result_caching",
            description="缓存热门搜索结果，减少重复查询",
            implementation_code=self._get_autocomplete_cache_code(),
            expected_improvement=85.0,
            implementation_cost="low",
            priority=2
        )
        optimizations.append(cache_optimization)
        
        # 3. 前端预加载优化
        preload_optimization = OptimizationAction(
            action_type="frontend_preload",
            description="前端预加载热门币种数据，实现即时响应",
            implementation_code=self._get_frontend_preload_code(),
            expected_improvement=90.0,
            implementation_cost="low",
            priority=3
        )
        optimizations.append(preload_optimization)
        
        return {
            "endpoint": "/api/v1/search/autocomplete",
            "optimizations": [asdict(opt) for opt in optimizations],
            "total_expected_improvement": sum(opt.expected_improvement for opt in optimizations),
            "implementation_priority": "high"
        }
    
    async def optimize_trending_endpoint(self) -> Dict[str, Any]:
        """优化市场热点端点"""
        logger.info("📈 Optimizing Trending endpoint...")
        
        optimizations = []
        
        # 1. 数据预计算优化
        precompute_optimization = OptimizationAction(
            action_type="data_precompute",
            description="预计算热点分数，定期更新缓存",
            implementation_code=self._get_precompute_code(),
            expected_improvement=80.0,
            implementation_cost="medium",
            priority=1
        )
        optimizations.append(precompute_optimization)
        
        # 2. 增量更新优化
        incremental_optimization = OptimizationAction(
            action_type="incremental_update",
            description="实现增量更新机制，避免全量重计算",
            implementation_code=self._get_incremental_update_code(),
            expected_improvement=40.0,
            implementation_cost="high",
            priority=2
        )
        optimizations.append(incremental_optimization)
        
        # 3. 数据压缩优化
        compression_optimization = OptimizationAction(
            action_type="data_compression",
            description="压缩响应数据，减少传输时间",
            implementation_code=self._get_compression_code(),
            expected_improvement=25.0,
            implementation_cost="low",
            priority=3
        )
        optimizations.append(compression_optimization)
        
        return {
            "endpoint": "/api/v1/trending/hotspots",
            "optimizations": [asdict(opt) for opt in optimizations],
            "total_expected_improvement": sum(opt.expected_improvement for opt in optimizations),
            "implementation_priority": "high"
        }
    
    def _get_quick_chat_cache_code(self) -> str:
        """Quick Chat缓存优化代码"""
        return '''
# Quick Chat智能缓存实现
import aioredis
import json
import hashlib
from typing import Dict, Any, Optional

class QuickChatCache:
    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client
        self.cache_ttl = 300  # 5分钟
    
    def _generate_cache_key(self, query: str) -> str:
        """生成缓存键"""
        # 标准化查询
        normalized = query.strip().lower()
        # 生成哈希
        return f"quickchat:{hashlib.md5(normalized.encode()).hexdigest()}"
    
    async def get_cached_response(self, query: str) -> Optional[Dict[str, Any]]:
        """获取缓存响应"""
        cache_key = self._generate_cache_key(query)
        try:
            cached_data = await self.redis.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            logger.warning(f"Cache get failed: {e}")
        return None
    
    async def cache_response(self, query: str, response: Dict[str, Any]):
        """缓存响应"""
        cache_key = self._generate_cache_key(query)
        try:
            await self.redis.setex(
                cache_key,
                self.cache_ttl,
                json.dumps(response, default=str)
            )
        except Exception as e:
            logger.warning(f"Cache set failed: {e}")
    
    async def get_common_questions(self) -> Dict[str, str]:
        """获取常见问题缓存"""
        common_key = "quickchat:common_questions"
        try:
            cached = await self.redis.get(common_key)
            if cached:
                return json.loads(cached)
        except:
            pass
        
        # 预定义常见问题
        common_questions = {
            "what is bitcoin": "Bitcoin (BTC) is the first decentralized cryptocurrency...",
            "btc price": "Bitcoin current price and market information...",
            "ethereum": "Ethereum (ETH) is a smart contract platform...",
            # 更多常见问题...
        }
        
        # 缓存常见问题
        try:
            await self.redis.setex(common_key, 3600, json.dumps(common_questions))
        except:
            pass
        
        return common_questions

# 在Quick Chat端点中使用
@router.post("/quick-chat")
async def optimized_quick_chat(request: QuickChatRequest):
    # 检查缓存
    cached_response = await quick_chat_cache.get_cached_response(request.query)
    if cached_response:
        return QuickChatResponse(**cached_response, cached=True)
    
    # 检查常见问题
    common_questions = await quick_chat_cache.get_common_questions()
    normalized_query = request.query.strip().lower()
    if normalized_query in common_questions:
        response = {
            "content": common_questions[normalized_query],
            "query_type": "common",
            "cached": True
        }
        await quick_chat_cache.cache_response(request.query, response)
        return QuickChatResponse(**response)
    
    # 执行正常流程...
    result = await quick_chat_engine.chat(query=request.query)
    
    # 缓存结果
    response_data = {
        "content": result["content"],
        "symbol": result.get("symbol"),
        "query_type": result["metadata"]["query_type"],
        "response_time": result["metadata"]["response_time"],
        "model": result["metadata"]["model"]
    }
    
    await quick_chat_cache.cache_response(request.query, response_data)
    
    return QuickChatResponse(**response_data)
'''
    
    def _get_ai_optimization_code(self) -> str:
        """AI模型优化代码"""
        return '''
# AI模型调用优化
import asyncio
from typing import List, Dict, Any

class OptimizedAIModelCaller:
    def __init__(self):
        self.model_pool = {
            "fast": "claude-3.5-haiku",      # 快速模型
            "balanced": "claude-3.5-sonnet",  # 平衡模型
            "deep": "claude-3.5-opus"        # 深度模型
        }
        self.request_queue = asyncio.Queue(maxsize=100)
        self.semaphore = asyncio.Semaphore(10)  # 并发限制
    
    async def call_model_optimized(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """优化的模型调用"""
        # 1. 选择最适合的模型
        model_type = self._select_optimal_model(query, context)
        model = self.model_pool[model_type]
        
        # 2. 预处理请求
        optimized_query = self._preprocess_query(query, context)
        
        # 3. 并行获取上下文数据
        context_tasks = self._get_context_tasks(query)
        context_data = await asyncio.gather(*context_tasks, return_exceptions=True)
        
        # 4. 调用模型
        async with self.semaphore:
            response = await self._call_model_with_timeout(
                model, optimized_query, context_data, timeout=2.5
            )
        
        # 5. 后处理响应
        optimized_response = self._postprocess_response(response)
        
        return optimized_response
    
    def _select_optimal_model(self, query: str, context: Dict[str, Any]) -> str:
        """选择最优模型"""
        query_length = len(query)
        
        if query_length < 50 and "price" in query.lower():
            return "fast"  # 简单价格查询使用快速模型
        elif query_length < 200:
            return "balanced"  # 中等复杂度使用平衡模型
        else:
            return "deep"  # 复杂查询使用深度模型
    
    def _preprocess_query(self, query: str, context: Dict[str, Any]) -> str:
        """查询预处理"""
        # 提取关键词
        keywords = self._extract_keywords(query)
        
        # 构建优化提示
        optimized_prompt = f"""
        Answer this cryptocurrency question concisely: {query}
        
        Keywords: {', '.join(keywords)}
        Context: {context.get('market_data', {})}
        
        Provide a direct, informative answer under 200 words.
        """
        
        return optimized_prompt.strip()
    
    async def _get_context_tasks(self, query: str) -> List[asyncio.Task]:
        """获取上下文数据任务"""
        tasks = []
        
        # 并行获取市场数据
        if "price" in query.lower() or "market" in query.lower():
            tasks.append(self._get_market_data_async(query))
        
        # 并行获取新闻数据
        if "news" in query.lower() or "recent" in query.lower():
            tasks.append(self._get_news_data_async(query))
        
        return tasks
    
    async def _call_model_with_timeout(self, model: str, query: str, context: List, timeout: float) -> Dict[str, Any]:
        """带超时的模型调用"""
        try:
            return await asyncio.wait_for(
                self._actual_model_call(model, query, context),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            # 超时降级到缓存或默认响应
            return self._get_fallback_response(query)
    
    def _get_fallback_response(self, query: str) -> Dict[str, Any]:
        """降级响应"""
        return {
            "content": "I'm processing your request. Please try again in a moment.",
            "model": "fallback",
            "response_time": 0.1,
            "cached": False
        }

# 在Quick Chat服务中使用
optimized_caller = OptimizedAIModelCaller()

async def quick_chat_engine_optimized(query: str) -> Dict[str, Any]:
    """优化的Quick Chat引擎"""
    start_time = time.time()
    
    # 获取上下文
    context = await get_quick_context(query)
    
    # 调用优化的AI模型
    result = await optimized_caller.call_model_optimized(query, context)
    
    # 添加性能指标
    result["metadata"] = {
        "response_time": (time.time() - start_time) * 1000,
        "model": result.get("model", "unknown"),
        "query_type": classify_query_type(query)
    }
    
    return result
'''
    
    def _get_parallel_processing_code(self) -> str:
        """并行处理优化代码"""
        return '''
# Deep Research并行处理优化
import asyncio
from typing import Dict, List, Any
from concurrent.futures import ThreadPoolExecutor

class ParallelResearchEngine:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.analysis_stages = [
            "market_analysis",
            "technical_analysis", 
            "sentiment_analysis",
            "onchain_analysis",
            "tokenomics_analysis",
            "risk_analysis"
        ]
    
    async def research_parallel(self, query: str, symbol: str) -> Dict[str, Any]:
        """并行执行研究分析"""
        start_time = time.time()
        
        # 1. 并行收集基础数据
        data_tasks = [
            self._collect_market_data(symbol),
            self._collect_news_data(symbol),
            self._collect_social_data(symbol),
            self._collect_onchain_data(symbol)
        ]
        
        market_data, news_data, social_data, onchain_data = await asyncio.gather(
            *data_tasks, return_exceptions=True
        )
        
        # 2. 并行执行各维度分析
        analysis_tasks = []
        for stage in self.analysis_stages:
            task = self._run_analysis_stage(stage, {
                "query": query,
                "symbol": symbol,
                "market_data": market_data,
                "news_data": news_data,
                "social_data": social_data,
                "onchain_data": onchain_data
            })
            analysis_tasks.append(task)
        
        # 3. 等待所有分析完成
        analysis_results = await asyncio.gather(
            *analysis_tasks, return_exceptions=True
        )
        
        # 4. 合并结果
        sections = {}
        for i, result in enumerate(analysis_results):
            if not isinstance(result, Exception):
                stage_name = self.analysis_stages[i]
                sections[stage_name] = result
        
        # 5. 生成综合结论
        conclusion = await self._generate_conclusion(sections)
        
        generation_time = time.time() - start_time
        
        return {
            "symbol": symbol,
            "query": query,
            "sections": sections,
            "conclusion": conclusion,
            "generation_time": generation_time,
            "data_sources": ["CoinGecko", "Twitter", "Reddit", "Etherscan"],
            "models_used": ["claude-3.5-sonnet", "llama-3.1-70b"],
            "timestamp": datetime.now().isoformat()
        }
    
    async def _run_analysis_stage(self, stage: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """运行单个分析阶段"""
        try:
            if stage == "market_analysis":
                return await self._analyze_market_data(data)
            elif stage == "technical_analysis":
                return await self._analyze_technical_indicators(data)
            elif stage == "sentiment_analysis":
                return await self._analyze_sentiment(data)
            elif stage == "onchain_analysis":
                return await self._analyze_onchain_metrics(data)
            elif stage == "tokenomics_analysis":
                return await self._analyze_tokenomics(data)
            elif stage == "risk_analysis":
                return await self._analyze_risks(data)
        except Exception as e:
            logger.error(f"Analysis stage {stage} failed: {e}")
            return {"error": str(e), "stage": stage}
    
    async def _analyze_market_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """市场数据分析"""
        market_data = data.get("market_data", {})
        
        # 使用线程池执行CPU密集型计算
        loop = asyncio.get_event_loop()
        analysis = await loop.run_in_executor(
            self.executor,
            self._calculate_market_metrics,
            market_data
        )
        
        return {
            "market_overview": analysis["overview"],
            "price_analysis": analysis["price"],
            "volume_analysis": analysis["volume"],
            "market_position": analysis["position"]
        }
    
    def _calculate_market_metrics(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """计算市场指标（CPU密集型）"""
        # 实际的市场指标计算逻辑
        price = market_data.get("price", 0)
        volume = market_data.get("volume_24h", 0)
        market_cap = market_data.get("market_cap", 0)
        
        return {
            "overview": f"Current price: ${price:,.2f}",
            "price": {"current": price, "change_24h": market_data.get("price_change_24h", 0)},
            "volume": {"24h": volume, "trend": "increasing"},
            "position": {"market_cap_rank": market_data.get("market_cap_rank", 0)}
        }

# 在Deep Research端点中使用
parallel_engine = ParallelResearchEngine()

@router.post("/deep-research")
async def optimized_deep_research(request: DeepResearchRequest):
    """优化的深度研究端点"""
    try:
        # 使用并行引擎执行研究
        result = await parallel_engine.research_parallel(
            query=request.query,
            symbol=request.symbol
        )
        
        # 生成报告
        markdown_content = report_generator.generate_markdown(result)
        title = report_generator.generate_title(result)
        quality_score = report_generator.calculate_quality_score(result)
        
        return DeepResearchResponse(
            report_id=0,  # 保存后获取实际ID
            symbol=result["symbol"],
            query=request.query,
            tldr=result.get("tldr", ""),
            sections=result["sections"],
            conclusion=result["conclusion"],
            markdown_content=markdown_content,
            data_sources=result["data_sources"],
            models_used=result["models_used"],
            generation_time=result["generation_time"],
            quality_score=quality_score,
            timestamp=result["timestamp"],
            session_id=request.session_id or str(uuid.uuid4())
        )
        
    except Exception as e:
        logger.error(f"Deep Research error: {e}")
        raise HTTPException(status_code=500, detail=f"Research failed: {str(e)}")
'''
    
    def _get_search_index_code(self) -> str:
        """搜索索引优化代码"""
        return '''
# 搜索索引优化
from sqlalchemy import text, Index
from typing import List, Dict, Any
import asyncio

class OptimizedSearchIndex:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.search_cache = {}
    
    async def create_search_indexes(self):
        """创建搜索优化索引"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_coins_symbol_trgm ON coins USING gin(symbol gin_trgm_ops)",
            "CREATE INDEX IF NOT EXISTS idx_coins_name_trgm ON coins USING gin(name gin_trgm_ops)",
            "CREATE INDEX IF NOT EXISTS idx_coins_symbol_lower ON coins(lower(symbol))",
            "CREATE INDEX IF NOT EXISTS idx_coins_name_lower ON coins(lower(name))",
            "CREATE INDEX IF NOT EXISTS idx_coins_market_cap_rank ON coins(market_cap_rank)"
        ]
        
        for index_sql in indexes:
            try:
                await self.db.execute(text(index_sql))
                await self.db.commit()
                logger.info(f"✅ Created index: {index_sql.split('idx_')[1].split(' ')[0]}")
            except Exception as e:
                logger.warning(f"⚠️ Index creation failed: {e}")
    
    async def search_optimized(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """优化的搜索实现"""
        # 1. 检查缓存
        cache_key = f"search:{query.lower()}:{limit}"
        if cache_key in self.search_cache:
            return self.search_cache[cache_key]
        
        # 2. 构建优化查询
        search_query = text("""
            SELECT 
                coingecko_id,
                symbol,
                name,
                market_cap_rank,
                thumb,
                -- 相似度评分
                CASE 
                    WHEN lower(symbol) = lower(:query_exact) THEN 100
                    WHEN lower(symbol) LIKE lower(:query_start) THEN 90
                    WHEN name % :query THEN 80
                    WHEN symbol % :query THEN 70
                    WHEN lower(name) LIKE lower(:query_contains) THEN 60
                    ELSE 50
                END as similarity_score
            FROM coins 
            WHERE 
                lower(symbol) = lower(:query_exact)
                OR lower(symbol) LIKE lower(:query_start)
                OR name % :query
                OR symbol % :query
                OR lower(name) LIKE lower(:query_contains)
            ORDER BY 
                similarity_score DESC,
                market_cap_rank ASC
            LIMIT :limit
        """)
        
        params = {
            "query_exact": query,
            "query_start": f"{query}%",
            "query": query,
            "query_contains": f"%{query}%",
            "limit": limit
        }
        
        result = await self.db.execute(search_query, params)
        coins = [dict(row._mapping) for row in result]
        
        # 3. 缓存结果
        self.search_cache[cache_key] = coins
        
        return coins
    
    async def get_popular_coins(self) -> List[Dict[str, Any]]:
        """获取热门币种（用于前端预加载）"""
        cache_key = "popular_coins"
        if cache_key in self.search_cache:
            return self.search_cache[cache_key]
        
        query = text("""
            SELECT coingecko_id, symbol, name, market_cap_rank, thumb
            FROM coins 
            WHERE market_cap_rank <= 100
            ORDER BY market_cap_rank ASC
            LIMIT 50
        """)
        
        result = await self.db.execute(query)
        popular_coins = [dict(row._mapping) for row in result]
        
        # 缓存1小时
        self.search_cache[cache_key] = popular_coins
        
        return popular_coins

# 在搜索端点中使用
search_index = OptimizedSearchIndex(db_session)

@router.get("/search/autocomplete")
async def optimized_autocomplete_search(
    q: str = Query(..., min_length=1, max_length=100),
    limit: int = Query(default=10, ge=1, le=20)
):
    """优化的自动补全搜索"""
    
    # 输入验证和标准化
    if not q or len(q.strip()) < 1:
        raise HTTPException(status_code=400, detail="Invalid search query")
    
    query = q.strip()
    
    # 执行优化搜索
    results = await search_index.search_optimized(query, limit)
    
    # 转换为响应格式
    items = [AutocompleteItem(**result) for result in results]
    
    return AutocompleteResponse(results=items, count=len(items))

@router.get("/search/popular")
async def get_popular_searches():
    """获取热门搜索（前端预加载）"""
    popular_coins = await search_index.get_popular_coins()
    return {"popular_coins": popular_coins}
'''
    
    def _get_precompute_code(self) -> str:
        """数据预计算优化代码"""
        return '''
# 热点数据预计算优化
import asyncio
import schedule
from datetime import datetime, timedelta
from typing import Dict, List, Any

class HotspotPrecomputer:
    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client
        self.update_interval = 900  # 15分钟
        self.is_running = False
    
    async def start_precompute_service(self):
        """启动预计算服务"""
        self.is_running = True
        
        # 立即执行一次
        await self.precompute_hotspots()
        
        # 设置定时任务
        schedule.every(15).minutes.do(self._schedule_precompute)
        
        # 运行调度器
        while self.is_running:
            schedule.run_pending()
            await asyncio.sleep(60)
    
    def _schedule_precompute(self):
        """调度预计算任务"""
        asyncio.create_task(self.precompute_hotspots())
    
    async def precompute_hotspots(self):
        """预计算热点数据"""
        try:
            start_time = time.time()
            logger.info("🔄 Starting hotspot precomputation...")
            
            # 1. 并行收集各维度数据
            data_tasks = [
                self._collect_twitter_data(),
                self._collect_reddit_data(),
                self._collect_price_data(),
                self._collect_volume_data(),
                self._collect_news_data()
            ]
            
            twitter_data, reddit_data, price_data, volume_data, news_data = await asyncio.gather(
                *data_tasks, return_exceptions=True
            )
            
            # 2. 计算热点分数
            hotspots = await self._calculate_hotspot_scores(
                twitter_data, reddit_data, price_data, volume_data, news_data
            )
            
            # 3. 缓存结果
            await self._cache_hotspot_results(hotspots)
            
            computation_time = time.time() - start_time
            logger.info(f"✅ Hotspot precomputation completed in {computation_time:.2f}s")
            
        except Exception as e:
            logger.error(f"❌ Hotspot precomputation failed: {e}")
    
    async def _calculate_hotspot_scores(self, twitter_data, reddit_data, price_data, volume_data, news_data) -> List[Dict[str, Any]]:
        """计算热点分数"""
        hotspots = []
        
        # 获取所有币种
        all_symbols = set()
        for data in [twitter_data, reddit_data, price_data, volume_data, news_data]:
            if isinstance(data, dict):
                all_symbols.update(data.keys())
        
        # 计算每个币种的热点分数
        for symbol in all_symbols:
            scores = {
                "twitter": self._normalize_score(twitter_data.get(symbol, 0), 0, 1000),
                "reddit": self._normalize_score(reddit_data.get(symbol, 0), 0, 500),
                "price": self._normalize_price_score(price_data.get(symbol, {})),
                "volume": self._normalize_score(volume_data.get(symbol, 0), 0, 1000000000),
                "news": self._normalize_score(news_data.get(symbol, 0), 0, 100)
            }
            
            # 计算总分（加权）
            total_score = (
                scores["twitter"] * 0.25 +
                scores["reddit"] * 0.20 +
                scores["price"] * 0.30 +
                scores["volume"] * 0.15 +
                scores["news"] * 0.10
            )
            
            if total_score > 20:  # 只包含有一定热度的币种
                hotspots.append({
                    "symbol": symbol,
                    "total_score": total_score,
                    "scores_breakdown": scores,
                    "timestamp": datetime.now().isoformat()
                })
        
        # 按分数排序
        hotspots.sort(key=lambda x: x["total_score"], reverse=True)
        
        return hotspots[:50]  # 返回前50个热点
    
    def _normalize_score(self, value: float, min_val: float, max_val: float) -> float:
        """标准化分数到0-100"""
        if max_val == min_val:
            return 0
        return min(100, max(0, (value - min_val) / (max_val - min_val) * 100))
    
    def _normalize_price_score(self, price_data: Dict[str, Any]) -> float:
        """标准化价格变化分数"""
        if not price_data:
            return 0
        
        price_change = abs(price_data.get("price_change_24h", 0))
        # 价格变化越大分数越高
        return min(100, price_change * 10)  # 10%变化 = 100分
    
    async def _cache_hotspot_results(self, hotspots: List[Dict[str, Any]]):
        """缓存热点结果"""
        try:
            # 缓存完整热点列表
            await self.redis.setex(
                "hotspots:full",
                self.update_interval,
                json.dumps(hotspots, default=str)
            )
            
            # 缓存前10个热点（用于快速响应）
            await self.redis.setex(
                "hotspots:top10",
                self.update_interval,
                json.dumps(hotspots[:10], default=str)
            )
            
            # 缓存各币种分数
            for hotspot in hotspots:
                await self.redis.setex(
                    f"hotspot:{hotspot['symbol']}",
                    self.update_interval,
                    json.dumps(hotspot, default=str)
                )
            
            logger.info(f"💾 Cached {len(hotspots)} hotspots")
            
        except Exception as e:
            logger.error(f"Cache failed: {e}")
    
    async def get_cached_hotspots(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取缓存的热点数据"""
        try:
            if limit == 10:
                cached_data = await self.redis.get("hotspots:top10")
            else:
                cached_data = await self.redis.get("hotspots:full")
            
            if cached_data:
                hotspots = json.loads(cached_data)
                return hotspots[:limit]
                
        except Exception as e:
            logger.warning(f"Cache get failed: {e}")
        
        return []

# 在热点端点中使用
hotspot_precomputer = HotspotPrecomputer(redis_client)

@router.get("/trending/hotspots")
async def get_hotspots_optimized(
    limit: int = Query(default=10, ge=1, le=50),
    force_refresh: bool = Query(default=False)
):
    """优化的热点端点"""
    
    if force_refresh:
        # 强制刷新
        await hotspot_precomputer.precompute_hotspots()
    
    # 获取缓存的热点数据
    hotspots = await hotspot_precomputer.get_cached_hotspots(limit)
    
    if not hotspots:
        # 缓存未命中，实时计算
        hotspots = await hotspot_precomputer.precompute_hotspots()
        hotspots = hotspots[:limit]
    
    # 转换为响应格式
    items = [HotspotItem(**hotspot) for hotspot in hotspots]
    
    return HotspotsResponse(
        hotspots=items,
        count=len(items),
        updated_at=datetime.utcnow().isoformat()
    )
'''
    
    def _get_autocomplete_cache_code(self) -> str:
        """自动补全缓存代码"""
        return '''
# 自动补全缓存优化
class AutocompleteCache:
    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client
        self.popular_searches = {}
    
    async def cache_search_result(self, query: str, results: List[Dict[str, Any]]):
        """缓存搜索结果"""
        cache_key = f"autocomplete:{query.lower()}"
        
        # 根据查询热度设置不同的TTL
        ttl = 3600 if query.lower() in self.popular_searches else 1800
        
        try:
            await self.redis.setex(
                cache_key,
                ttl,
                json.dumps(results, default=str)
            )
        except Exception as e:
            logger.warning(f"Cache set failed: {e}")
    
    async def get_cached_result(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """获取缓存结果"""
        cache_key = f"autocomplete:{query.lower()}"
        
        try:
            cached_data = await self.redis.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            logger.warning(f"Cache get failed: {e}")
        
        return None
'''
    
    def _get_frontend_preload_code(self) -> str:
        """前端预加载代码"""
        return '''
// 前端预加载优化
class SearchPreloader {
    constructor() {
        this.popularCoins = [];
        this.searchIndex = new Map();
        this.isLoaded = false;
    }
    
    async preloadPopularCoins() {
        try {
            const response = await fetch('/api/v1/search/popular');
            const data = await response.json();
            
            this.popularCoins = data.popular_coins;
            this.buildSearchIndex();
            this.isLoaded = true;
            
            console.log(`✅ Preloaded ${this.popularCoins.length} popular coins`);
        } catch (error) {
            console.error('❌ Preload failed:', error);
        }
    }
    
    buildSearchIndex() {
        this.popularCoins.forEach(coin => {
            const symbol = coin.symbol.toLowerCase();
            const name = coin.name.toLowerCase();
            
            // 按符号索引
            this.searchIndex.set(symbol, coin);
            
            // 按名称索引
            this.searchIndex.set(name, coin);
            
            // 部分匹配索引
            for (let i = 1; i <= symbol.length; i++) {
                const prefix = symbol.substring(0, i);
                if (!this.searchIndex.has(prefix)) {
                    this.searchIndex.set(prefix, []);
                }
                this.searchIndex.get(prefix).push(coin);
            }
        });
    }
    
    instantSearch(query) {
        if (!this.isLoaded || !query) return [];
        
        const lowerQuery = query.toLowerCase();
        
        // 精确匹配
        if (this.searchIndex.has(lowerQuery)) {
            const result = this.searchIndex.get(lowerQuery);
            return Array.isArray(result) ? result.slice(0, 5) : [result];
        }
        
        // 前缀匹配
        const matches = [];
        for (const [key, value] of this.searchIndex) {
            if (key.startsWith(lowerQuery) && Array.isArray(value)) {
                matches.push(...value);
            }
        }
        
        // 去重并限制结果
        const uniqueMatches = matches.filter((coin, index, self) =>
            index === self.findIndex(c => c.symbol === coin.symbol)
        );
        
        return uniqueMatches.slice(0, 10);
    }
}

// 在应用启动时预加载
const searchPreloader = new SearchPreloader();
searchPreloader.preloadPopularCoins();

// 在搜索组件中使用
function handleSearchInput(query) {
    // 立即返回预加载结果
    const instantResults = searchPreloader.instantSearch(query);
    
    if (instantResults.length > 0) {
        showSearchResults(instantResults);
        return;
    }
    
    // 如果预加载没有结果，调用API
    if (query.length >= 2) {
        debouncedApiSearch(query);
    }
}
'''
    
    def _get_incremental_update_code(self) -> str:
        """增量更新代码"""
        return '''
# 增量更新优化
class IncrementalHotspotUpdater:
    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client
        self.last_update = {}
    
    async def incremental_update(self):
        """增量更新热点数据"""
        try:
            # 获取上次更新时间
            last_update_key = "hotspots:last_update"
            last_update_time = await self.redis.get(last_update_key)
            
            if not last_update_time:
                # 首次更新，执行全量计算
                await self.full_update()
                return
            
            # 获取增量数据
            incremental_data = await self._fetch_incremental_data(last_update_time)
            
            if incremental_data:
                # 更新受影响的币种
                await self._update_affected_coins(incremental_data)
                
                # 更新时间戳
                await self.redis.set(last_update_key, datetime.now().isoformat())
                
                logger.info(f"✅ Incremental update completed for {len(incremental_data)} coins")
            
        except Exception as e:
            logger.error(f"❌ Incremental update failed: {e}")
    
    async def _fetch_incremental_data(self, since_time: str) -> Dict[str, Any]:
        """获取增量数据"""
        # 实现增量数据获取逻辑
        # 这里需要根据具体数据源实现
        return {}
'''
    
    def _get_compression_code(self) -> str:
        """数据压缩代码"""
        return '''
# 响应数据压缩优化
import gzip
import json
from fastapi import Response

class CompressedResponse:
    @staticmethod
    def compress_json(data: Dict[str, Any]) -> Response:
        """压缩JSON响应"""
        json_str = json.dumps(data, separators=(',', ':'))
        compressed = gzip.compress(json_str.encode('utf-8'))
        
        return Response(
            content=compressed,
            media_type="application/json",
            headers={
                "Content-Encoding": "gzip",
                "Content-Length": str(len(compressed))
            }
        )
    
    @staticmethod
    def optimize_data_structure(data: Dict[str, Any]) -> Dict[str, Any]:
        """优化数据结构"""
        # 移除不必要的字段
        if "hotspots" in data:
            for hotspot in data["hotspots"]:
                # 移除冗余数据
                hotspot.pop("detailed_metrics", None)
                hotspot.pop("raw_data", None)
        
        # 使用更短的键名
        if "hotspots" in data:
            data["h"] = data.pop("hotspots")
            for item in data["h"]:
                item["s"] = item.pop("symbol")
                item["n"] = item.pop("name")
                item["sc"] = item.pop("total_score")
        
        return data

# 在端点中使用
@router.get("/trending/hotspots")
async def get_hotspots_compressed(limit: int = 10):
    """压缩的热点端点"""
    hotspots = await get_hotspots_data(limit)
    
    # 优化数据结构
    optimized_data = {
        "hotspots": hotspots,
        "count": len(hotspots),
        "updated_at": datetime.utcnow().isoformat()
    }
    
    optimized_data = CompressedResponse.optimize_data_structure(optimized_data)
    
    # 返回压缩响应
    return CompressedResponse.compress_json(optimized_data)
'''
    
    def _get_layered_cache_code(self) -> str:
        """分层缓存代码"""
        return '''
# 分层缓存策略
class LayeredCache:
    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client
        self.memory_cache = {}
        self.cache_layers = {
            "memory": {"ttl": 300, "size": 1000},      # 5分钟，1000条
            "redis": {"ttl": 3600, "size": 10000},     # 1小时，10000条
            "disk": {"ttl": 86400, "size": 100000}     # 24小时，100000条
        }
    
    async def get(self, key: str) -> Optional[Any]:
        """分层获取缓存"""
        # 1. 内存缓存
        if key in self.memory_cache:
            item = self.memory_cache[key]
            if time.time() - item["timestamp"] < self.cache_layers["memory"]["ttl"]:
                return item["data"]
            else:
                del self.memory_cache[key]
        
        # 2. Redis缓存
        try:
            cached_data = await self.redis.get(key)
            if cached_data:
                data = json.loads(cached_data)
                # 提升到内存缓存
                self._set_memory_cache(key, data)
                return data
        except:
            pass
        
        # 3. 磁盘缓存（如果需要）
        # 实现磁盘缓存逻辑
        
        return None
    
    async def set(self, key: str, data: Any, layer: str = "redis"):
        """分层设置缓存"""
        if layer == "memory":
            self._set_memory_cache(key, data)
        elif layer == "redis":
            await self._set_redis_cache(key, data)
            # 同时设置内存缓存
            self._set_memory_cache(key, data)
    
    def _set_memory_cache(self, key: str, data: Any):
        """设置内存缓存"""
        if len(self.memory_cache) >= self.cache_layers["memory"]["size"]:
            # LRU淘汰
            oldest_key = min(self.memory_cache.keys(), 
                           key=lambda k: self.memory_cache[k]["timestamp"])
            del self.memory_cache[oldest_key]
        
        self.memory_cache[key] = {
            "data": data,
            "timestamp": time.time()
        }
    
    async def _set_redis_cache(self, key: str, data: Any):
        """设置Redis缓存"""
        try:
            await self.redis.setex(
                key,
                self.cache_layers["redis"]["ttl"],
                json.dumps(data, default=str)
            )
        except Exception as e:
            logger.warning(f"Redis cache set failed: {e}")
'''
    
    def _get_streaming_optimization_code(self) -> str:
        """流式优化代码"""
        return '''
# 流式响应优化
import asyncio
from fastapi.responses import StreamingResponse
import json

class StreamingOptimizedResearch:
    def __init__(self):
        self.chunk_size = 1000  # 每次发送的字符数
    
    async def stream_research_results(self, query: str, symbol: str):
        """流式返回研究结果"""
        try:
            # 发送开始信号
            yield self._format_sse_data({
                "type": "start",
                "message": f"Starting research on {symbol}...",
                "progress": 0
            })
            
            # 并行执行研究
            research_task = asyncio.create_task(
                self._execute_research(query, symbol)
            )
            
            # 流式发送进度
            while not research_task.done():
                await self._send_progress_updates(symbol)
                await asyncio.sleep(2)
            
            # 获取最终结果
            result = await research_task
            
            # 流式发送结果
            yield self._format_sse_data({
                "type": "result",
                "data": result,
                "progress": 100,
                "done": True
            })
            
        except Exception as e:
            yield self._format_sse_data({
                "type": "error",
                "message": str(e),
                "done": True
            })
    
    def _format_sse_data(self, data: Dict[str, Any]) -> str:
        """格式化SSE数据"""
        return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
    
    async def _send_progress_updates(self, symbol: str):
        """发送进度更新"""
        progress_data = {
            "type": "progress",
            "message": f"Analyzing {symbol}...",
            "progress": 50  # 实际应该基于真实进度
        }
        yield self._format_sse_data(progress_data)

# 在流式端点中使用
streaming_research = StreamingOptimizedResearch()

@router.get("/deep-research/stream")
async def deep_research_stream_optimized(
    query: str,
    symbol: str,
    conversation_id: Optional[str] = None
):
    """优化的流式深度研究"""
    
    async def generate():
        async for chunk in streaming_research.stream_research_results(query, symbol):
            yield chunk
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*"
        }
    )
'''
    
    def _get_connection_pool_code(self) -> str:
        """连接池优化代码"""
        return '''
# 连接池优化
import aioredis
import aiohttp
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

class OptimizedConnectionPools:
    def __init__(self):
        self.redis_pool = None
        self.http_pool = None
        self.db_engine = None
    
    async def initialize_pools(self):
        """初始化连接池"""
        # Redis连接池
        self.redis_pool = aioredis.ConnectionPool.from_url(
            "redis://localhost:6379",
            max_connections=20,
            retry_on_timeout=True
        )
        
        # HTTP连接池
        connector = aiohttp.TCPConnector(
            limit=100,
            limit_per_host=20,
            ttl_dns_cache=300,
            use_dns_cache=True,
        )
        
        self.http_pool = aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=30)
        )
        
        # 数据库连接池
        self.db_engine = create_async_engine(
            "postgresql+asyncpg://user:pass@localhost/db",
            pool_size=20,
            max_overflow=30,
            pool_pre_ping=True,
            pool_recycle=3600
        )
        
        logger.info("✅ Connection pools initialized")
    
    async def get_redis_client(self):
        """获取Redis客户端"""
        return aioredis.Redis(connection_pool=self.redis_pool)
    
    async def get_http_session(self):
        """获取HTTP会话"""
        return self.http_pool
    
    async def get_db_session(self):
        """获取数据库会话"""
        async_session = sessionmaker(
            self.db_engine, class_=AsyncSession, expire_on_commit=False
        )
        return async_session()

# 全局连接池实例
connection_pools = OptimizedConnectionPools()
'''
    
    async def generate_optimization_report(self) -> Dict[str, Any]:
        """生成优化报告"""
        logger.info("📊 Generating comprehensive optimization report...")
        
        # 分析所有关键端点
        quick_chat_opt = await self.optimize_quick_chat_endpoint()
        deep_research_opt = await self.optimize_deep_research_endpoint()
        autocomplete_opt = await self.optimize_autocomplete_endpoint()
        trending_opt = await self.optimize_trending_endpoint()
        
        # 计算总体优化潜力
        all_optimizations = [
            quick_chat_opt, deep_research_opt, 
            autocomplete_opt, trending_opt
        ]
        
        total_expected_improvement = sum(
            opt["total_expected_improvement"] for opt in all_optimizations
        )
        
        # 按优先级排序优化动作
        all_actions = []
        for opt in all_optimizations:
            all_actions.extend(opt["optimizations"])
        
        all_actions.sort(key=lambda x: x["priority"])
        
        # 生成实施计划
        implementation_plan = self._generate_implementation_plan(all_actions)
        
        report = {
            "analysis_timestamp": datetime.now().isoformat(),
            "summary": {
                "total_endpoints_analyzed": len(all_optimizations),
                "total_optimization_actions": len(all_actions),
                "total_expected_improvement": total_expected_improvement,
                "high_priority_actions": len([a for a in all_actions if a["priority"] <= 2]),
                "implementation_complexity": self._calculate_complexity(all_actions)
            },
            "endpoint_optimizations": all_optimizations,
            "prioritized_actions": all_actions[:10],  # 前10个最高优先级
            "implementation_plan": implementation_plan,
            "estimated_roi": self._calculate_roi(all_actions),
            "next_steps": self._get_next_steps(all_actions)
        }
        
        return report
    
    def _generate_implementation_plan(self, actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成实施计划"""
        phases = {
            "phase_1": {
                "name": "Quick Wins (1-2 weeks)",
                "actions": [a for a in actions if a["implementation_cost"] == "low"],
                "expected_impact": "20-30% performance improvement"
            },
            "phase_2": {
                "name": "Core Optimizations (3-4 weeks)",
                "actions": [a for a in actions if a["implementation_cost"] == "medium"],
                "expected_impact": "40-60% performance improvement"
            },
            "phase_3": {
                "name": "Advanced Features (4-6 weeks)",
                "actions": [a for a in actions if a["implementation_cost"] == "high"],
                "expected_impact": "60-80% performance improvement"
            }
        }
        
        return phases
    
    def _calculate_complexity(self, actions: List[Dict[str, Any]]) -> str:
        """计算实施复杂度"""
        low_count = len([a for a in actions if a["implementation_cost"] == "low"])
        medium_count = len([a for a in actions if a["implementation_cost"] == "medium"])
        high_count = len([a for a in actions if a["implementation_cost"] == "high"])
        
        if high_count > len(actions) / 2:
            return "high"
        elif medium_count > len(actions) / 2:
            return "medium"
        else:
            return "low"
    
    def _calculate_roi(self, actions: List[Dict[str, Any]]) -> Dict[str, float]:
        """计算投资回报率"""
        total_improvement = sum(a["expected_improvement"] for a in actions)
        total_cost = sum(
            1 if a["implementation_cost"] == "low" else
            3 if a["implementation_cost"] == "medium" else
            5 for a in actions
        )
        
        return {
            "performance_roi": total_improvement / total_cost if total_cost > 0 else 0,
            "development_cost_score": total_cost,
            "expected_benefit": total_improvement
        }
    
    def _get_next_steps(self, actions: List[Dict[str, Any]]) -> List[str]:
        """获取下一步行动"""
        high_priority = [a for a in actions if a["priority"] <= 2]
        
        steps = [
            f"Implement {high_priority[0]['action_type']} for {high_priority[0].get('endpoint', 'critical endpoint')}",
            "Set up performance monitoring and baseline measurements",
            "Create development branch for optimization implementation",
            "Establish testing framework for performance validation",
            "Schedule regular performance reviews and optimization iterations"
        ]
        
        return steps[:5]

async def main():
    """主函数 - 运行端点优化分析"""
    print("🚀 Starting Critical API Endpoint Optimization Analysis...")
    
    # 初始化优化器
    optimizer = CriticalEndpointOptimizer()
    await optimizer.initialize()
    
    # 生成优化报告
    report = await optimizer.generate_optimization_report()
    
    # 保存报告
    with open("endpoint_optimization_report.json", "w") as f:
        json.dump(report, f, indent=2, default=str)
    
    # 打印摘要
    print("\n" + "="*60)
    print("📊 ENDPOINT OPTIMIZATION ANALYSIS RESULTS")
    print("="*60)
    
    summary = report["summary"]
    print(f"Endpoints Analyzed: {summary['total_endpoints_analyzed']}")
    print(f"Optimization Actions: {summary['total_optimization_actions']}")
    print(f"Expected Improvement: {summary['total_expected_improvement']:.1f}%")
    print(f"High Priority Actions: {summary['high_priority_actions']}")
    print(f"Implementation Complexity: {summary['implementation_complexity']}")
    
    print("\n🎯 Top 3 Optimization Actions:")
    for i, action in enumerate(report["prioritized_actions"][:3], 1):
        print(f"{i}. {action['action_type']} - {action['expected_improvement']:.1f}% improvement")
        print(f"   {action['description']}")
    
    print("\n📈 Implementation Plan:")
    for phase_name, phase in report["implementation_plan"].items():
        print(f"   {phase['name']}: {len(phase['actions'])} actions")
        print(f"   Expected Impact: {phase['expected_impact']}")
    
    print("\n💡 Next Steps:")
    for step in report["next_steps"]:
        print(f"   • {step}")
    
    print(f"\n📁 Detailed report saved to: endpoint_optimization_report.json")

if __name__ == "__main__":
    asyncio.run(main())
