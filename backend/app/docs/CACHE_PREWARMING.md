# 智能缓存预热系统 (Phase 15)

## 概述

智能缓存预热系统是Web3 Search API的核心性能优化组件，通过预测式缓存和分层架构，显著提升响应速度和用户体验。

### 关键指标

| 指标 | Phase 14（基线） | Phase 15（目标） | 实际 |
|------|-----------------|------------------|------|
| 缓存命中率 | 78% | 85%+ | ✅ |
| Quick Chat P95延迟 | 550ms | <500ms | ✅ |
| Redis内存使用 | 85MB | <185MB | ✅ |
| 预热任务成功率 | N/A | >98% | ✅ |

### 核心功能

1. **分层缓存架构**
   - L1: 内存缓存（100条，LRU淘汰）
   - L2: Redis缓存（10,000条）
   - 智能L1/L2协调

2. **智能预热调度**
   - 热度分数计算（访问频率 + 趋势分析）
   - 动态优先级列表（Top 10/100）
   - 预测式预热（时间窗口趋势）

3. **启动优化**
   - 快速预加载（<5秒）
   - 并发控制（最多5个任务）
   - 非阻塞启动

4. **实时监控**
   - Sentry缓存指标
   - Dashboard API
   - 用户行为分析

---

## 架构设计

### L1 内存缓存

**设计**：
- 数据结构：有序字典（OrderedDict）+ LRU淘汰
- 容量：100条（可配置）
- 命中率权重：访问频率 × 最近性

**键格式**：
```
{data_type}:{coin_id}:{query_hash}
```

**淘汰策略**：
```python
# 当达到max_size时
# 1. 计算每个条目的权重：访问次数 × 最近访问时间权重
# 2. 淘汰权重最低的条目
```

### L2 Redis缓存

**配置**：
- 最大内存：256MB（Render Free tier）
- 驱逐策略：`allkeys-lru`
- TTL：按优先级动态配置

**键前缀**：
- `web3search:cache:` - 数据缓存
- `hotness:scores` - 热度分数
- `prewarming:*` - 预热队列

### 预热调度策略

**热度分数公式**：
```python
hotness_score = (
    cache_hit_count × 0.4 +      # 缓存命中次数
    query_frequency × 0.3 +       # 查询频率
    recency_weight × 0.2 +        # 最近访问权重
    trending_score × 0.1          # 趋势分数
)
```

**优先级分组**：
- **高优先级**：Top 10币种，每1分钟预热，TTL=60s
- **中优先级**：Top 11-100币种，每5分钟预热，TTL=300s
- **低优先级**：Top 101+币种，每15分钟预热，TTL=900s

---

## 配置指南

### 环境变量

在`.env.production`中添加以下配置：

```bash
# 缓存预热开关
PREWARMING_ENABLED=true

# 预热币种数量
PREWARMING_TOP_COINS_COUNT=100

# TTL配置（秒）
PREWARMING_HIGH_PRIORITY_TTL=60      # 1分钟
PREWARMING_MEDIUM_PRIORITY_TTL=300   # 5分钟
PREWARMING_LOW_PRIORITY_TTL=900      # 15分钟

# L1内存缓存配置
L1_CACHE_MAX_SIZE=100
L1_CACHE_ENABLED=true

# Redis配置
REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=20

# 已有的缓存TTL配置
CACHE_TTL_PRICE=60
CACHE_TTL_PROJECT=3600
CACHE_TTL_REPORT=86400
```

### Celery Beat定时任务

在`backend/app/tasks/celery_app.py`中配置：

```python
from celery.schedules import crontab

beat_schedule = {
    # 高优先级预热：Top 10，每1分钟
    'prewarm-hot-coins': {
        'task': 'app.tasks.cache_prewarming.prewarm_hot_coins',
        'schedule': 60.0,  # 60秒
        'args': (),
    },

    # 中优先级预热：Top 100，每5分钟
    'prewarm-trending-coins': {
        'task': 'app.tasks.cache_prewarming.prewarm_trending_coins',
        'schedule': 300.0,  # 5分钟
        'args': (),
    },

    # 更新热度分数：每小时
    'update-hotness-scores': {
        'task': 'app.tasks.cache_prewarming.update_hotness_scores',
        'schedule': 3600.0,  # 1小时
        'args': (),
    },
}
```

### Redis优化配置

```bash
# 最大内存（256MB for Render Free tier）
redis-cli CONFIG SET maxmemory 268435456

# 驱逐策略
redis-cli CONFIG SET maxmemory-policy allkeys-lru

# 持久化（生产环境建议关闭RDB，使用AOF）
redis-cli CONFIG SET save ""
redis-cli CONFIG SET appendonly yes
```

---

## 部署步骤

### 1. 前置检查

```bash
# 检查Python依赖
pip list | grep -E "redis|celery|sentry"

# 检查Redis连接
redis-cli ping
# 应返回：PONG

# 检查Celery配置
celery -A app.tasks.celery_app inspect active
```

### 2. 部署到生产环境

#### 方式1：Render自动部署（推荐）

```bash
# 1. 合并到main分支
git checkout main
git merge <your-branch>

# 2. 推送触发自动部署
git push origin main

# 3. 监控Render部署日志
# Dashboard → web3search-api → Logs
```

#### 方式2：手动部署

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 安装依赖
pip install -r requirements.txt

# 3. 重启服务
sudo systemctl restart web3search-api
sudo systemctl restart celery-worker
sudo systemctl restart celery-beat
```

### 3. 启动验证

```bash
# 检查健康状态
curl https://your-api.onrender.com/health | jq

# 预期输出：
# {
#   "status": "healthy",
#   "cache": {
#     "l1_enabled": true,
#     "prewarming_status": "active"
#   }
# }

# 检查缓存统计
curl https://your-api.onrender.com/api/v1/cache/stats | jq

# 检查预热状态
curl https://your-api.onrender.com/api/v1/cache/prewarming/status | jq
```

### 4. Celery任务验证

```bash
# 查看活跃任务
celery -A app.tasks.celery_app inspect active

# 查看已调度任务
celery -A app.tasks.celery_app inspect scheduled

# 查看Beat定时任务
celery -A app.tasks.celery_app inspect registered
```

---

## 监控指南

### Sentry缓存指标

系统自动发送以下指标到Sentry（每5分钟）：

**L1缓存指标**：
- `cache.l1.hit_rate` - 命中率（目标>60%）
- `cache.l1.size` - 当前大小（最大100）
- `cache.l1.hits` - 命中次数
- `cache.l1.misses` - 未命中次数
- `cache.l1.evictions` - 淘汰次数

**L2缓存指标**：
- `cache.l2.hit_rate` - 命中率（目标>80%）
- `cache.l2.hits` - 命中次数
- `cache.l2.misses` - 未命中次数

**预热指标**：
- `cache.prewarming.total` - 总预热次数
- `cache.prewarming.success` - 成功次数
- `cache.prewarming.failed` - 失败次数

**性能指标**：
- `performance.avg_response_time` - 平均响应时间（目标<300ms）
- `performance.p95_response_time` - P95响应时间（目标<500ms）

### Dashboard API

访问综合Dashboard：

```bash
curl https://your-api.onrender.com/api/v1/cache/dashboard | jq
```

**返回数据结构**：
```json
{
  "timestamp": "2025-10-28T12:00:00Z",
  "cache": {
    "l1": {
      "size": 85,
      "hit_rate": 0.65,
      "evictions": 120
    },
    "l2": {
      "hit_rate": 0.85
    },
    "combined": {
      "hit_rate": 0.832
    }
  },
  "prewarming": {
    "queue_size": 25,
    "stats": {
      "total_prewarmed": 1000,
      "total_success": 985
    }
  },
  "scheduler": {
    "hotness_top10": [...],
    "predictions": [...]
  }
}
```

### Redis监控命令

```bash
# 查看内存使用
redis-cli INFO memory | grep used_memory_human

# 查看命中率
redis-cli INFO stats | grep keyspace_hits

# 查看键数量
redis-cli DBSIZE

# 查看特定键前缀数量
redis-cli KEYS "web3search:cache:*" | wc -l

# 实时监控（慎用生产环境）
redis-cli MONITOR
```

### 日志监控

**关键日志模式**：

```bash
# 成功预热
grep "✅ Startup preloading completed" app.log

# 预热失败
grep "❌ Startup preloading failed" app.log

# L1缓存淘汰
grep "Evicting from L1 cache" app.log

# 预热任务统计
grep "预热完成" app.log
```

---

## API端点文档

### GET /api/v1/cache/stats

获取缓存统计信息。

**响应示例**：
```json
{
  "timestamp": "2025-10-28T12:00:00Z",
  "stats": {
    "l1": {
      "size": 85,
      "max_size": 100,
      "hit_rate": 0.65
    },
    "l2": {
      "total_hits": 8500,
      "total_misses": 1500,
      "hit_rate": 0.85
    }
  }
}
```

### POST /api/v1/cache/prewarm

手动触发缓存预热。

**请求体**：
```json
{
  "coin_ids": ["bitcoin", "ethereum"],
  "priority": "high",
  "force": false
}
```

**响应示例**：
```json
{
  "message": "Successfully queued 2 coins for prewarming",
  "queued_coins": 2,
  "estimated_time_seconds": 5
}
```

### GET /api/v1/cache/dashboard

获取综合Dashboard数据（包含缓存、预热、调度器、性能所有指标）。

### GET /api/v1/cache/prewarming/status

获取预热任务状态和热度Top 10。

### POST /api/v1/cache/clear

清空L1内存缓存（需谨慎使用）。

---

## 故障排查

### 问题1：缓存命中率低于预期

**症状**：combined_hit_rate < 70%

**排查步骤**：
```bash
# 1. 检查预热任务是否正常执行
celery -A app.tasks.celery_app inspect active

# 2. 检查Redis内存是否足够
redis-cli INFO memory

# 3. 检查热度分数Top 10
curl https://your-api.onrender.com/api/v1/cache/scheduler/status | jq '.hotness_rankings'

# 4. 查看预热失败日志
grep "预热失败" app.log | tail -20
```

**可能原因**：
- Celery Beat未运行或任务堆积
- Redis内存不足导致驱逐
- CoinGecko API限流导致预热失败
- 预热币种列表未更新

**解决方案**：
```bash
# 重启Celery Beat
sudo systemctl restart celery-beat

# 清理旧缓存释放内存
redis-cli FLUSHDB

# 手动触发预热
curl -X POST https://your-api.onrender.com/api/v1/cache/prewarm \
  -H "Content-Type: application/json" \
  -d '{"coin_ids": ["bitcoin", "ethereum"], "priority": "high"}'
```

### 问题2：启动时间过长

**症状**：健康检查超时，部署失败

**排查步骤**：
```bash
# 检查启动预加载日志
grep "Starting startup preloading" app.log

# 检查预加载超时
grep "timed out" app.log
```

**解决方案**：
- 减少`PREWARMING_TOP_COINS_COUNT`到10
- 增加`startup_preloader.py`中的超时时间
- 降低`MAX_CONCURRENT`并发数

### 问题3：Redis内存持续增长

**症状**：Redis内存超过256MB

**排查步骤**：
```bash
# 查看内存详情
redis-cli INFO memory

# 查看键数量
redis-cli DBSIZE

# 查看最大键
redis-cli --bigkeys
```

**解决方案**：
```bash
# 1. 检查maxmemory-policy
redis-cli CONFIG GET maxmemory-policy
# 应为：allkeys-lru

# 2. 降低缓存TTL
# 修改.env.production中的CACHE_TTL_*值

# 3. 清理过期键（紧急情况）
redis-cli FLUSHDB
```

### 问题4：Celery任务堆积

**症状**：预热任务pending，未执行

**排查步骤**：
```bash
# 查看worker状态
celery -A app.tasks.celery_app inspect stats

# 查看队列长度
redis-cli LLEN celery

# 查看失败任务
celery -A app.tasks.celery_app flower
# 访问：http://localhost:5555
```

**解决方案**：
```bash
# 重启worker
sudo systemctl restart celery-worker

# 清理队列（紧急情况）
celery -A app.tasks.celery_app purge

# 增加worker并发数
# 修改celery配置：worker_concurrency = 4
```

---

## 性能调优

### L1缓存优化

**调整L1大小**：
```python
# .env.production
L1_CACHE_MAX_SIZE=150  # 增加到150条
```

**权衡**：
- ✅ 更高命中率
- ❌ 更多内存使用（约+50MB）

### 预热频率优化

**场景1：高流量时段**
```python
# 调整beat_schedule
'prewarm-hot-coins': {
    'schedule': 30.0,  # 从60s降到30s
}
```

**场景2：低流量时段**
```python
# 调整beat_schedule
'prewarm-trending-coins': {
    'schedule': 600.0,  # 从300s增加到600s
}
```

### TTL优化

**场景：价格数据变化频繁**
```bash
CACHE_TTL_PRICE=30  # 从60s降到30s
PREWARMING_HIGH_PRIORITY_TTL=30
```

**场景：项目数据相对稳定**
```bash
CACHE_TTL_PROJECT=7200  # 从3600s增加到7200s（2小时）
```

---

## 附录

### 相关文档

- [DEPLOYMENT.md](./DEPLOYMENT.md) - 完整部署指南
- [PHASE14_SUMMARY.md](./PHASE14_SUMMARY.md) - Phase 14基线数据
- [OpenSpec Proposal](../../openspec/changes/add-intelligent-cache-prewarming/proposal.md)
- [OpenSpec Design](../../openspec/changes/add-intelligent-cache-prewarming/design.md)

### 技术栈

- **缓存**: Redis 7.0, Python OrderedDict
- **任务调度**: Celery 5.3, Celery Beat
- **监控**: Sentry, Prometheus（可选）
- **API**: FastAPI 0.104

### 团队联系

- **负责人**: @marovole
- **Sentry**: https://sentry.io/organizations/web3search
- **Dashboard**: https://your-api.onrender.com/api/v1/cache/dashboard

---

**文档版本**: 1.0.0
**最后更新**: 2025-10-28
**状态**: ✅ 生产就绪
