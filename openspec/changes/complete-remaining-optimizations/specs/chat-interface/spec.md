# Chat Interface Specification - Phase 14 Deltas

## MODIFIED Requirements

### Requirement: Quick Chat Response Generation
The system SHALL generate quick and accurate cryptocurrency-related answers using AI model (OpenRouter) with P95 response time ≤3 seconds and accuracy ≥80%. The system SHALL implement query caching, parallel data fetching, and optimized prompt engineering to ensure high performance and quality.

系统必须使用AI模型（OpenRouter）生成快速、准确的加密货币相关回答，响应时间≤3秒（P95），精度≥80%。回答应基于实时市场数据、技术指标和社交情绪，提供简洁明确的分析。系统必须实现查询缓存、并行数据获取和优化的Prompt工程，确保高性能和高质量。

**性能目标**：
- P95延迟: ≤1.5秒（优化后，原为2.5秒）
- 缓存命中率: ≥60%
- 精度: ≥80%（基于用户反馈）

#### Scenario: Quick Chat with cache hit
- **WHEN** 用户提问"BTC价格如何？"
- **AND** 相同查询在10分钟内已有缓存
- **THEN** 系统从Redis获取缓存结果
- **AND** 返回答案，响应时间<100ms
- **AND** 记录日志："quick_chat_cache_hit"

#### Scenario: Quick Chat with cache miss
- **WHEN** 用户提问"BTC技术分析"
- **AND** 缓存中无相关结果
- **THEN** 系统并行调用3个数据源（CoinGecko、Etherscan、Twitter）
- **AND** 数据获取完成时间<1秒
- **THEN** 构建Prompt（system + few-shot + data + query）
- **AND** 调用OpenRouter API（gemini-flash-1.5）
- **AND** 流式返回答案（SSE）
- **AND** 完整答案存入Redis（TTL 10分钟）
- **AND** 总响应时间<1.5秒

#### Scenario: Streaming response
- **WHEN** 用户发起Quick Chat请求（stream=true）
- **THEN** 系统建立SSE连接
- **AND** 每50ms发送一个chunk
- **AND** 前端显示打字机效果
- **AND** 最后发送"[DONE]"信号
- **AND** 关闭SSE连接

### Requirement: Prompt Engineering
The system SHALL use optimized prompt templates with clear system instructions, relevant few-shot examples, and structured output format.

系统必须使用优化的Prompt模板，包含clear system instructions、relevant few-shot examples和structured output format。

**Prompt组成**：
1. **System Prompt**: 定义AI角色、任务目标、输出要求
2. **Few-shot Examples**: 3-5个相关示例（动态选择）
3. **Context Data**: 实时市场数据、技术指标、社交情绪
4. **User Query**: 用户提问

#### Scenario: Technical analysis query with relevant examples
- **WHEN** 用户提问"BTC的RSI指标如何？"
- **THEN** 系统识别查询类型为"technical_analysis"
- **AND** 从示例库选择3个技术分析相关示例
- **AND** 构建Prompt包含：
  - System: "你是加密货币技术分析专家..."
  - Examples: RSI/MACD/MA示例
  - Data: BTC当前RSI=65, MACD=+500
  - Query: "BTC的RSI指标如何？"
- **THEN** 生成精确回答

#### Scenario: Sentiment analysis query with relevant examples
- **WHEN** 用户提问"市场对ETH的情绪如何？"
- **THEN** 系统识别查询类型为"sentiment_analysis"
- **AND** 选择2个情绪分析示例
- **AND** 构建Prompt包含Twitter/Reddit数据
- **THEN** 生成情绪分析报告

## ADDED Requirements

### Requirement: Query Result Caching
The system SHALL use Redis to cache Quick Chat query results to reduce redundant computations and API calls.

系统必须使用Redis缓存Quick Chat查询结果，减少重复计算和API调用。

**缓存策略**：
- **Key格式**: `quick_chat:{hash(query + symbol)}`
- **TTL**: 600秒（10分钟）
- **失效策略**: 时间过期自动删除
- **缓存内容**: 完整答案 + metadata（生成时间、数据源、token消耗）

#### Scenario: Cache miss - store result
- **WHEN** 用户提问"BTC价格分析"
- **AND** 缓存未命中
- **THEN** 系统生成答案（耗时1.5秒）
- **AND** 将答案存入Redis
  - key: "quick_chat:a3f8b2c9d..."
  - value: {"answer": "...", "generated_at": "2025-10-26T15:30:00Z", "sources": ["coingecko", "twitter"]}
  - TTL: 600秒
- **AND** 返回答案给用户

#### Scenario: Cache hit - return immediately
- **WHEN** 用户提问"BTC价格分析"（与上次查询相同）
- **AND** 缓存命中（距上次查询5分钟）
- **THEN** 系统从Redis获取答案（<10ms）
- **AND** 返回答案，响应时间<100ms
- **AND** 增加指标："quick_chat.cache_hit"

#### Scenario: Cache expired - regenerate
- **WHEN** 用户提问"BTC价格分析"
- **AND** 缓存已过期（距上次查询15分钟）
- **THEN** 缓存未命中
- **AND** 系统重新生成答案
- **AND** 更新缓存

### Requirement: Few-shot Example Selection
The system SHALL dynamically select most relevant few-shot examples based on user query to improve answer accuracy.

系统必须根据用户查询动态选择最相关的few-shot示例，提高回答精度。

**实现方式**：
- 使用sentence-transformers模型（all-MiniLM-L6-v2）编码查询和示例
- 计算余弦相似度，选择Top-3最相关示例
- 示例库分类：技术分析、情绪分析、风险评估、代币经济学

**示例库规模**：
- 技术分析: 10个示例（MA/RSI/MACD/布林带等）
- 情绪分析: 8个示例（正面/负面/中性情绪）
- 风险评估: 8个示例（高/中/低风险场景）
- 代币经济学: 6个示例（通胀/通缩/供应分析）

#### Scenario: Semantic similarity selection
- **WHEN** 用户提问"ETH的技术指标分析"
- **THEN** 系统编码查询为384维向量
- **AND** 与示例库32个示例计算相似度
- **AND** 选择Top-3示例：
  1. "BTC的MACD指标分析" (相似度0.92)
  2. "ETH的RSI走势如何" (相似度0.89)
  3. "分析SOL的移动平均线" (相似度0.85)
- **AND** 将3个示例插入Prompt
- **AND** 生成时间<50ms

#### Scenario: Category fallback
- **WHEN** 用户提问冷门查询"如何分析DAO治理代币？"
- **AND** 语义相似度都<0.7
- **THEN** 系统选择通用示例（每类1个）
- **AND** 记录日志："few_shot_fallback", max_similarity=0.65

### Requirement: Parallel Data Fetching
The system SHALL call multiple data source APIs in parallel to reduce total response time.

系统必须并行调用多个数据源API，减少总响应时间。

**优化前**（串行）：
- CoinGecko: 500ms
- Etherscan: 600ms
- Twitter: 700ms
- **总计**: 1800ms

**优化后**（并行）：
- asyncio.gather同时调用3个API
- **总计**: max(500, 600, 700) = 700ms
- **提升**: 60%

#### Scenario: Parallel API calls success
- **WHEN** 用户发起Quick Chat请求
- **THEN** 系统并行调用：
  - fetch_market_data(symbol)
  - fetch_chain_data(symbol)
  - fetch_social_data(symbol)
- **AND** 使用asyncio.gather(return_exceptions=True)
- **AND** 所有调用在700ms内完成
- **THEN** 合并数据，生成答案

#### Scenario: Partial failure with parallel calls
- **WHEN** 系统并行调用3个数据源
- **AND** Twitter API超时失败
- **AND** CoinGecko和Etherscan成功
- **THEN** 系统使用可用数据生成答案
- **AND** 在答案中标记："社交数据暂时不可用"
- **AND** 不阻塞整个请求

### Requirement: Response Streaming Optimization
The system SHALL optimize streaming response to provide smoother user experience.

系统必须优化流式响应，提供更流畅的用户体验。

**优化目标**：
- Chunk间隔: 50ms（原为100ms+不稳定）
- 进度提示: 显示当前阶段（"正在分析价格走势..."）
- 错误提示: 友好的错误消息 + 技术详情

#### Scenario: Smooth streaming with progress
- **WHEN** 用户发起Quick Chat请求
- **THEN** 系统发送进度事件：
  - {"stage": "fetching_data", "progress": 20, "message": "正在获取市场数据..."}
  - {"stage": "analyzing", "progress": 60, "message": "正在分析技术指标..."}
  - {"stage": "generating", "progress": 80, "message": "正在生成答案..."}
- **AND** 开始流式返回答案
- **AND** 每50ms发送一个chunk
- **AND** {"content": "根据技术分析，BTC当前...", "done": false}
- **AND** 最后发送{"content": "[DONE]", "done": true}

#### Scenario: Streaming error handling
- **WHEN** 流式生成过程中API失败
- **THEN** 系统发送错误事件
- **AND** {"error": "数据源暂时不可用，请稍后重试", "details": "CoinGecko API timeout"}
- **AND** 关闭SSE连接
- **AND** 前端显示友好错误提示

### Requirement: Answer Quality Tracking
The system SHALL track answer quality for prompt optimization and model selection.

系统必须追踪回答质量，用于Prompt优化和模型选择。

**追踪指标**：
- **精度**: 用户反馈（👍/👎）
- **完整性**: 答案是否包含所有必要信息
- **速度**: 生成时间
- **Token消耗**: 输入/输出token数

#### Scenario: User feedback positive
- **WHEN** 用户收到Quick Chat答案
- **AND** 用户点击👍按钮
- **THEN** 系统记录反馈：
  - query: "BTC价格分析"
  - answer_id: "qa_12345"
  - feedback: "positive"
  - timestamp: "2025-10-26T15:30:00Z"
- **AND** 增加指标："quick_chat.positive_feedback"

#### Scenario: User feedback negative
- **WHEN** 用户点击👎按钮
- **AND** 用户提交反馈："答案太简短，缺少技术细节"
- **THEN** 系统记录详细反馈
- **AND** 增加指标："quick_chat.negative_feedback"
- **AND** 触发人工审查（如果负面反馈>5%）

### Requirement: Query Deduplication
The system SHALL merge identical concurrent queries to reduce redundant computations.

系统必须合并相同的并发查询，减少重复计算。

**场景**：多个用户同时查询"BTC价格"，只调用一次API和AI模型。

#### Scenario: Concurrent identical queries
- **WHEN** 用户A和用户B同时提问"BTC价格如何？"
- **AND** 两个请求在100ms内到达
- **THEN** 系统检测到重复查询
- **AND** 只执行一次数据获取和AI生成
- **AND** 两个用户都等待同一个结果
- **THEN** 结果生成后，广播给两个用户
- **AND** 记录日志："query_deduplicated", count=2

#### Scenario: Different queries - no deduplication
- **WHEN** 用户A查询"BTC价格"，用户B查询"ETH价格"
- **THEN** 系统不合并，分别处理
- **AND** 两个独立的API调用和AI生成

## Implementation Notes

### Redis缓存实现

```python
# backend/app/core/cache.py
import hashlib
import json
from redis.asyncio import Redis

class QuickChatCache:
    def __init__(self, redis: Redis, ttl: int = 600):
        self.redis = redis
        self.ttl = ttl

    def _make_key(self, query: str, symbol: str) -> str:
        data = f"{query}:{symbol}"
        hash_value = hashlib.md5(data.encode()).hexdigest()
        return f"quick_chat:{hash_value}"

    async def get(self, query: str, symbol: str) -> dict | None:
        key = self._make_key(query, symbol)
        data = await self.redis.get(key)
        if data:
            logger.debug("cache_hit", key=key)
            metrics.incr("quick_chat.cache_hit")
            return json.loads(data)

        logger.debug("cache_miss", key=key)
        metrics.incr("quick_chat.cache_miss")
        return None

    async def set(self, query: str, symbol: str, answer: dict):
        key = self._make_key(query, symbol)
        value = json.dumps({
            "answer": answer,
            "generated_at": datetime.now().isoformat(),
            "ttl": self.ttl
        })
        await self.redis.setex(key, self.ttl, value)
        logger.debug("cache_set", key=key, ttl=self.ttl)
```

### Few-shot示例选择

```python
# backend/app/services/prompt_engine.py
from sentence_transformers import SentenceTransformer
import numpy as np

class FewShotSelector:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.examples = self._load_examples()
        self.embeddings = self.model.encode([ex["query"] for ex in self.examples])

    def select_examples(self, query: str, k: int = 3, min_similarity: float = 0.7) -> list[dict]:
        query_embedding = self.model.encode([query])[0]
        similarities = np.dot(self.embeddings, query_embedding)

        top_k_indices = np.argsort(similarities)[-k:][::-1]
        selected = []

        for idx in top_k_indices:
            if similarities[idx] >= min_similarity:
                selected.append({
                    **self.examples[idx],
                    "similarity": float(similarities[idx])
                })

        # Fallback: 相似度都不够，选择通用示例
        if not selected:
            logger.warning("few_shot_fallback", max_similarity=float(similarities.max()))
            selected = self._get_generic_examples(k)

        return selected
```

### 并行数据获取

```python
# backend/app/services/quick_chat.py
async def fetch_all_data_parallel(symbol: str) -> dict:
    """并行调用所有数据源"""
    results = await asyncio.gather(
        fetch_market_data(symbol),
        fetch_chain_data(symbol),
        fetch_social_data(symbol),
        return_exceptions=True  # 部分失败不影响其他
    )

    market_data, chain_data, social_data = results

    # 处理失败的调用
    if isinstance(market_data, Exception):
        logger.error("market_data_failed", error=str(market_data))
        market_data = None

    if isinstance(chain_data, Exception):
        logger.error("chain_data_failed", error=str(chain_data))
        chain_data = None

    if isinstance(social_data, Exception):
        logger.warning("social_data_failed", error=str(social_data))
        social_data = None

    return {
        "market": market_data,
        "chain": chain_data,
        "social": social_data
    }
```

### 流式响应优化

```python
# backend/app/api/v1/chat.py
from fastapi.responses import StreamingResponse

async def quick_chat_stream(request: QuickChatRequest):
    async def event_generator():
        # 1. 进度：获取数据
        yield f"data: {json.dumps({'stage': 'fetching_data', 'progress': 20})}\n\n"
        data = await fetch_all_data_parallel(request.symbol)

        # 2. 进度：分析
        yield f"data: {json.dumps({'stage': 'analyzing', 'progress': 60})}\n\n"
        prompt = build_prompt(request.query, data, examples)

        # 3. 进度：生成
        yield f"data: {json.dumps({'stage': 'generating', 'progress': 80})}\n\n"

        # 4. 流式生成答案
        async for chunk in openrouter_client.stream(prompt):
            yield f"data: {json.dumps({'content': chunk, 'done': False})}\n\n"
            await asyncio.sleep(0.05)  # 50ms间隔

        # 5. 完成
        yield f"data: {json.dumps({'content': '[DONE]', 'done': True})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

## Testing Requirements

### 单元测试
- 测试缓存命中/未命中逻辑
- 测试Few-shot示例选择（高相似度/低相似度/fallback）
- 测试并行数据获取（全成功/部分失败）
- 测试查询去重（相同查询/不同查询）

### 集成测试
- 端到端Quick Chat流程（含缓存）
- 流式响应完整性验证
- 错误处理（数据源失败、AI失败）

### 性能测试
- 并发100用户查询，P95延迟≤1.5秒
- 缓存命中率≥60%（预热后）
- Few-shot选择延迟<50ms

### A/B测试
- 对比优化前后的回答精度（基于用户反馈）
- 对比不同Few-shot数量的效果（3个 vs 5个）
