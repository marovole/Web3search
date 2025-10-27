# 监控指标说明

Web3 Search API 监控指标详细说明，包括含义、正常范围和异常处理。

## 目录

1. [指标概览](#指标概览)
2. [性能指标](#性能指标)
3. [错误指标](#错误指标)
4. [业务指标](#业务指标)
5. [基础设施指标](#基础设施指标)
6. [外部依赖指标](#外部依赖指标)
7. [告警阈值](#告警阈值)
8. [指标查询](#指标查询)

---

## 指标概览

### 监控层级

| 层级 | 工具 | 指标类型 | 数据保留 |
|------|------|----------|----------|
| **应用层** | Sentry | 性能、错误、业务 | 90天 |
| **系统层** | Metrics API | CPU、内存、网络 | 30天 |
| **数据层** | Database Metrics | 连接池、查询性能 | 30天 |
| **缓存层** | Redis INFO | 内存、命中率 | 实时 |

### 指标命名规范

```
<namespace>.<metric_name>.<unit>

示例：
- api.response_time.seconds
- database.connections.active
- cache.hit_rate.percentage
```

---

## 性能指标

### 1. API响应时间

**指标名称**: `api.response_time.seconds`

**含义**: API请求从接收到响应的完整时间

**采集方式**:
```python
from app.core.monitoring import metrics
import time

start = time.time()
# ... 处理请求 ...
duration = time.time() - start

metrics.record_api_call(
    endpoint="/api/v1/chat/quick-chat",
    method="POST",
    status_code=200,
    duration=duration
)
```

**正常范围**:
| 端点 | P50 | P95 | P99 |
|------|-----|-----|-----|
| `/api/v1/chat/quick-chat` | < 1s | < 3s | < 5s |
| `/api/v1/chat/deep-research` | < 20s | < 30s | < 40s |
| `/api/v1/search/autocomplete` | < 200ms | < 500ms | < 1s |
| `/api/v1/trending/hotspots` | < 500ms | < 2s | < 3s |

**异常处理**:
- **P95 > 阈值**: 检查慢查询、外部API延迟
- **持续升高**: 扩容服务器或优化代码
- **突然升高**: 检查是否有突发流量或新部署

**Sentry查询**:
```
Performance → Transactions → 选择端点 → 查看P95延迟
```

### 2. 数据库查询时间

**指标名称**: `database.query_time.milliseconds`

**含义**: 单次数据库查询执行时间

**采集方式**:
```python
# app/core/database.py自动记录
# 通过SQLAlchemy event hooks
```

**正常范围**:
- **简单查询**: < 10ms
- **JOIN查询**: < 50ms
- **复杂查询**: < 200ms

**慢查询阈值**: 500ms

**异常处理**:
```bash
# 1. 查看慢查询日志
tail -f logs/slow_queries.log

# 2. 分析查询计划
psql $DATABASE_URL -c "EXPLAIN ANALYZE <query>"

# 3. 添加索引
psql $DATABASE_URL -c "CREATE INDEX idx_reports_symbol ON reports(symbol);"

# 4. 优化查询
# 减少JOIN、使用子查询、添加WHERE条件
```

### 3. Redis操作延迟

**指标名称**: `redis.latency.milliseconds`

**含义**: Redis GET/SET操作延迟

**正常范围**:
- **本地网络**: < 1ms
- **云服务**: < 10ms
- **跨区域**: < 50ms

**异常处理**:
```bash
# 1. 测试延迟
redis-cli -u $REDIS_URL --latency

# 2. 查看慢日志
redis-cli -u $REDIS_URL SLOWLOG GET 10

# 3. 检查内存使用
redis-cli -u $REDIS_URL INFO memory

# 4. 优化策略
# - 减少value大小
# - 使用pipeline批量操作
# - 启用压缩
```

### 4. LLM推理时间

**指标名称**: `llm.inference_time.seconds`

**含义**: LLM模型响应时间（不包括网络延迟）

**正常范围**:
| 模型 | 正常 | 警告 | 异常 |
|------|------|------|------|
| Claude 3.5 Sonnet | < 5s | 5-10s | > 10s |
| Llama 3.1 70B | < 8s | 8-15s | > 15s |
| Claude 3 Haiku | < 2s | 2-5s | > 5s |

**异常处理**:
```python
# 1. 启用超时和重试
response = await llm_client.chat(
    messages=messages,
    timeout=30,  # 30秒超时
    max_retries=2  # 最多重试2次
)

# 2. 切换到更快的模型
if response_time > 10:
    # 降级到Haiku模型
    model = "anthropic/claude-3-haiku"

# 3. 简化Prompt
# 减少few-shot示例
# 删除不必要的上下文
```

---

## 错误指标

### 5. 错误率

**指标名称**: `api.error_rate.percentage`

**计算公式**:
```
错误率 = (5xx响应数 / 总请求数) × 100%
```

**正常范围**:
- **优秀**: < 0.1%
- **良好**: 0.1% - 1%
- **警告**: 1% - 5%
- **严重**: > 5%

**异常处理**:
```bash
# 1. 查看错误分布
# Sentry → Issues → 按错误类型分组

# 2. 识别Top 3错误
# 优先修复频率最高的错误

# 3. 检查最近部署
git log -5  # 查看最近5次提交
# 如果错误率突增，考虑回滚

# 4. 临时降级
# 禁用有问题的功能或端点
```

### 6. 4xx错误率

**指标名称**: `api.client_error_rate.percentage`

**含义**: 客户端错误（400, 404, 422等）占比

**正常范围**:
- **正常**: < 5%
- **注意**: 5% - 10%
- **异常**: > 10%

**常见原因**:
1. **422 Validation Error** - 客户端参数错误
2. **404 Not Found** - 请求不存在的资源
3. **429 Rate Limit** - 超过速率限制

**处理策略**:
- **422过高**: 改进API文档和错误提示
- **404过高**: 检查是否有无效链接或旧版本客户端
- **429过高**: 考虑调整速率限制或引导用户升级

### 7. 超时错误

**指标名称**: `api.timeout_count`

**正常范围**: < 10次/小时

**异常处理**:
```python
# 1. 增加超时阈值
QUICK_CHAT_TIMEOUT = 10  # 从5s增加到10s

# 2. 优化慢操作
# - 减少外部API调用
# - 并行处理
# - 启用缓存

# 3. 降级策略
try:
    result = await quick_chat_engine.chat(query, timeout=5)
except TimeoutError:
    # 降级：返回缓存结果或简化响应
    result = await get_cached_or_simple_response(query)
```

---

## 业务指标

### 8. 报告生成成功率

**指标名称**: `report.generation_success_rate.percentage`

**计算公式**:
```
成功率 = (成功报告数 / 总请求数) × 100%
```

**正常范围**:
- **优秀**: > 95%
- **良好**: 90% - 95%
- **警告**: 85% - 90%
- **严重**: < 85%

**采集方式**:
```python
from app.core.monitoring import metrics

try:
    report = await deep_research_engine.research(query, symbol)
    metrics.record_report_generation(
        symbol=symbol,
        report_type="deep_research",
        success=True,
        duration=duration,
        sections_count=len(report["sections"])
    )
except Exception as e:
    metrics.record_report_generation(
        symbol=symbol,
        report_type="deep_research",
        success=False,
        duration=duration,
        sections_count=0
    )
```

**失败原因分析**:
```bash
# 查询失败报告
psql $DATABASE_URL -c "
SELECT status, error_message, COUNT(*) as count
FROM reports
WHERE status = 'failed'
  AND created_at > NOW() - INTERVAL '24 hours'
GROUP BY status, error_message
ORDER BY count DESC;
"
```

### 9. 缓存命中率

**指标名称**: `cache.hit_rate.percentage`

**计算公式**:
```
命中率 = (缓存命中次数 / 总查询次数) × 100%
```

**正常范围**:
- **优秀**: > 80%
- **良好**: 60% - 80%
- **一般**: 40% - 60%
- **较差**: < 40%

**采集方式**:
```python
from app.core.monitoring import metrics

# 缓存命中
metrics.record_cache_operation(
    operation="get",
    hit=True,
    key=cache_key,
    duration_ms=duration
)

# 缓存未命中
metrics.record_cache_operation(
    operation="get",
    hit=False,
    key=cache_key,
    duration_ms=duration
)
```

**优化策略**:
```python
# 1. 增加缓存TTL
CACHE_TTL = {
    "price": 600,  # 从300s增加到600s
    "hotspots": 900,  # 从600s增加到900s
}

# 2. 预热热点数据
async def warmup_cache():
    symbols = ["BTC", "ETH", "SOL"]
    for symbol in symbols:
        await get_price_data(symbol)

# 3. 分层缓存
# L1: 内存缓存 (60s)
# L2: Redis缓存 (10min)
```

### 10. 数据源成功率

**指标名称**: `datasource.<source>.success_rate.percentage`

**数据源**:
- `coingecko` - CoinGecko API
- `etherscan` - Etherscan API
- `twitter` - Twitter API
- `reddit` - Reddit API
- `cryptopanic` - CryptoPanic API

**正常范围**: > 95%

**监控Dashboard**:
```python
# 查看各数据源状态
GET /api/v1/health/dependencies

{
  "coingecko": {
    "status": "healthy",
    "success_rate": 98.5,
    "avg_response_time": 250
  },
  "etherscan": {
    "status": "degraded",
    "success_rate": 92.0,
    "avg_response_time": 1200
  }
}
```

**告警配置**:
```json
{
  "name": "数据源失败率高",
  "condition": "datasource.*.success_rate < 90",
  "actions": [
    "切换到fallback数据源",
    "发送Slack通知"
  ]
}
```

---

## 基础设施指标

### 11. CPU使用率

**指标名称**: `system.cpu.usage.percentage`

**正常范围**:
- **正常**: < 60%
- **警告**: 60% - 80%
- **严重**: > 80%

**查看方式**:
```bash
# 实时监控
top

# 历史数据
# Render Dashboard → Metrics → CPU
```

**异常处理**:
```bash
# 1. 识别高CPU进程
ps aux | sort -nrk 3 | head

# 2. 分析CPU profile
python3 -m cProfile -o cpu.prof app/main.py
python3 -m pstats cpu.prof
> sort cumtime
> stats 20

# 3. 扩容
# 升级到更高CPU配置

# 4. 优化代码
# - 减少计算密集型操作
# - 使用异步IO
# - 缓存计算结果
```

### 12. 内存使用率

**指标名称**: `system.memory.usage.percentage`

**正常范围**:
- **正常**: < 70%
- **警告**: 70% - 85%
- **严重**: > 85%

**查看方式**:
```bash
# 实时查看
free -h

# 进程内存
ps aux | sort -nrk 4 | head

# Python内存profiling
pip install memory_profiler
python3 -m memory_profiler app/main.py
```

**异常处理**:
```bash
# 1. 重启服务（临时）
systemctl restart web3search-api

# 2. 检查内存泄漏
# 使用memory_profiler和tracemalloc

# 3. 优化内存使用
# - 限制缓存大小
# - 使用生成器而非列表
# - 及时关闭资源

# 4. 扩容内存
# 升级到更高内存配置
```

### 13. 数据库连接池

**指标名称**:
- `database.pool.active` - 活跃连接数
- `database.pool.idle` - 空闲连接数
- `database.pool.total` - 总连接数

**正常范围**:
```python
# 配置
POOL_SIZE = 10  # 最小连接数
MAX_OVERFLOW = 40  # 最大溢出连接数

# 健康状态
active < 40  # 未达到上限
idle > 2     # 有空闲连接
wait_queue = 0  # 无等待队列
```

**查看方式**:
```bash
# API端点
curl https://web3search-api.onrender.com/api/v1/health/database/pool

{
  "pool_size": 10,
  "max_overflow": 40,
  "active": 5,
  "idle": 5,
  "wait_queue": 0,
  "overflow": 0
}

# 数据库侧查看
psql $DATABASE_URL -c "
SELECT count(*) as connections,
       state
FROM pg_stat_activity
WHERE datname = current_database()
GROUP BY state;
"
```

**异常处理**:
```bash
# 1. 连接池耗尽（active = 50, wait_queue > 0）
# 临时：增加pool_size和max_overflow
# 永久：优化查询，减少连接持有时间

# 2. 连接泄漏（活跃连接持续增长）
# 检查代码中是否正确关闭连接
# 使用with语句或try-finally

# 3. 死锁（wait_queue持续增长）
psql $DATABASE_URL -c "
SELECT pid, now() - query_start AS duration, query
FROM pg_stat_activity
WHERE state = 'active'
ORDER BY duration DESC
LIMIT 10;
"
```

### 14. Redis内存使用

**指标名称**: `redis.memory.used.bytes`

**正常范围**:
```
used_memory < maxmemory * 0.8
```

**查看方式**:
```bash
redis-cli -u $REDIS_URL INFO memory

# 关键指标
used_memory_human: 156.25M
used_memory_peak_human: 200.00M
maxmemory_human: 256.00M
mem_fragmentation_ratio: 1.05
```

**异常处理**:
```bash
# 1. 内存使用过高（> 80%）
# 查看大key
redis-cli -u $REDIS_URL --bigkeys

# 2. 清理过期key
redis-cli -u $REDIS_URL INFO keyspace
# 检查expires比例

# 3. 调整驱逐策略
redis-cli -u $REDIS_URL CONFIG SET maxmemory-policy allkeys-lru

# 4. 扩容Redis
# 升级到更大内存plan
```

---

## 外部依赖指标

### 15. OpenRouter API延迟

**指标名称**: `external.openrouter.latency.seconds`

**正常范围**:
- **正常**: < 5s
- **慢**: 5-10s
- **超时**: > 30s

**监控方式**:
```python
from app.core.monitoring import metrics

start = time.time()
response = await openrouter_client.chat(...)
latency = time.time() - start

metrics.record_external_api_call(
    service="openrouter",
    endpoint="/chat/completions",
    latency=latency,
    status_code=response.status_code
)
```

### 16. CoinGecko API可用性

**指标名称**: `external.coingecko.availability.percentage`

**正常范围**: > 99%

**告警策略**:
```json
{
  "name": "CoinGecko API不可用",
  "condition": "availability < 95% for 5 minutes",
  "actions": [
    "自动切换到CoinMarketCap",
    "通知Slack #alerts频道"
  ]
}
```

---

## 告警阈值

### 告警级别

| 级别 | 响应时间 | 通知方式 |
|------|----------|----------|
| **P0 - 紧急** | < 5分钟 | Slack + Email + SMS |
| **P1 - 重要** | < 1小时 | Slack + Email |
| **P2 - 一般** | < 24小时 | Email |
| **P3 - 信息** | 无要求 | Dashboard |

### 告警规则

```json
[
  {
    "name": "高错误率",
    "level": "P0",
    "condition": "error_rate > 5% for 5 minutes",
    "threshold": 5.0
  },
  {
    "name": "API延迟过高",
    "level": "P1",
    "condition": "p95_latency > 3s for 10 minutes",
    "threshold": 3.0
  },
  {
    "name": "数据库连接池耗尽",
    "level": "P0",
    "condition": "wait_queue > 10",
    "threshold": 10
  },
  {
    "name": "内存使用过高",
    "level": "P1",
    "condition": "memory_usage > 85% for 15 minutes",
    "threshold": 85.0
  },
  {
    "name": "缓存命中率低",
    "level": "P2",
    "condition": "cache_hit_rate < 50% for 1 hour",
    "threshold": 50.0
  }
]
```

---

## 指标查询

### Sentry查询

```python
# 1. 错误率
Discover → Query: event.type:error
Group by: transaction
Time range: Last 24h

# 2. P95延迟
Performance → Transactions → Sort by P95

# 3. 自定义指标
Insights → Custom Metrics → 选择指标
```

### Metrics API

```bash
# 1. 查看所有指标
curl https://web3search-api.onrender.com/api/v1/metrics

# 2. 查看响应时间
curl https://web3search-api.onrender.com/api/v1/metrics/response-time

# 3. 查看缓存统计
curl https://web3search-api.onrender.com/api/v1/metrics/cache

# 4. 查看数据源状态
curl https://web3search-api.onrender.com/api/v1/metrics/data-sources
```

### 数据库查询

```sql
-- 1. 慢查询统计
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
WHERE mean_exec_time > 500
ORDER BY mean_exec_time DESC
LIMIT 20;

-- 2. 表大小
SELECT schemaname, tablename,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- 3. 连接统计
SELECT state, count(*)
FROM pg_stat_activity
WHERE datname = current_database()
GROUP BY state;

-- 4. 锁等待
SELECT blocked_locks.pid AS blocked_pid,
       blocking_locks.pid AS blocking_pid,
       blocked_activity.query AS blocked_query
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity
  ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks
  ON blocking_locks.locktype = blocked_locks.locktype
WHERE NOT blocked_locks.granted;
```

---

## 参考资源

- [监控运维指南](./MONITORING_GUIDE.md)
- [故障排查指南](./TROUBLESHOOTING.md)
- [Sentry文档](https://docs.sentry.io/)
- [PostgreSQL统计信息](https://www.postgresql.org/docs/current/monitoring-stats.html)

---

**版本**: v1.0.0
**最后更新**: 2025-01-27
**维护者**: Web3Search SRE Team
