# 扩容指南

Web3 Search API 扩容策略和实施指南。

## 扩容决策

### 何时扩容

**CPU指标**:
- 持续使用率 > 70%
- P95响应时间 > 目标值150%
- 队列积压明显

**内存指标**:
- 使用率 > 80%
- 频繁OOM错误
- Swap使用量高

**数据库指标**:
- 连接池经常耗尽
- 慢查询增多
- CPU使用率 > 80%

## 垂直扩容

### Railway升级

```bash
# 查看当前配置
railway status

# 升级plan
# Dashboard → Settings → Change Plan
# Starter ($5) → Developer ($20) → Team ($50)
```

配置对比:
- Starter: 512MB RAM, 0.5 vCPU
- Developer: 8GB RAM, 8 vCPU
- Team: 32GB RAM, 16 vCPU

### Render升级

```bash
# Dashboard → Settings → Instance Type
# Free → Starter ($7) → Standard ($25) → Pro ($85)
```

## 水平扩容

### 负载均衡配置

```python
# 部署多个实例
# Render: Settings → Scaling → Instance Count = 3

# Nginx配置（如自托管）
upstream backend {
    server api1.example.com;
    server api2.example.com;
    server api3.example.com;
}
```

### 数据库扩容

```sql
-- 1. 读写分离
PRIMARY_DB = "postgresql://master/db"
REPLICA_DB = "postgresql://replica/db"

-- 2. 连接池调优
POOL_SIZE = 20  # 从10增加
MAX_OVERFLOW = 80  # 从40增加

-- 3. 分区表
CREATE TABLE reports_2025_01 PARTITION OF reports
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
```

### Redis扩容

```bash
# 1. 增加内存
# Railway: Redis设置中选择更大plan

# 2. Redis Cluster（未来）
# 分片策略：按key前缀分片

# 3. 多级缓存
# L1: 本地内存 (1分钟)
# L2: Redis (10分钟)
```

## 性能优化

### 代码优化

```python
# 1. 并发请求
async with asyncio.TaskGroup() as tg:
    price_task = tg.create_task(get_price(symbol))
    social_task = tg.create_task(get_social(symbol))

# 2. 连接池复用
session = aiohttp.ClientSession(
    connector=aiohttp.TCPConnector(limit=100)
)

# 3. 批量操作
await db.execute(insert(Report).values(reports))  # 批量插入
```

### 缓存策略

```python
# 1. 增加缓存时间
CACHE_TTL = {
    "price": 300,  # 5分钟
    "hotspots": 900,  # 15分钟
    "reports": 3600,  # 1小时
}

# 2. 预热缓存
@app.on_event("startup")
async def warmup():
    symbols = ["BTC", "ETH", "SOL"]
    for symbol in symbols:
        await get_price_data(symbol)
```

## 成本优化

### 资源使用监控

```bash
# 1. 查看资源使用趋势
# Railway Dashboard → Metrics

# 2. 识别资源浪费
# - 空闲时间资源使用
# - 低流量时段
# - 冗余服务

# 3. 自动缩放（Render）
# Settings → Auto-Scale
# Min: 1, Max: 3
```

### 成本预估

| 组件 | 免费 | 小型 | 中型 | 大型 |
|------|------|------|------|------|
| API服务 | $0 | $7 | $25 | $85 |
| PostgreSQL | $0 | $7 | $25 | $250 |
| Redis | $0 | $5 | $15 | $50 |
| **总计** | **$0** | **$19** | **$65** | **$385** |

---

**版本**: v1.0.0
**最后更新**: 2025-01-27
