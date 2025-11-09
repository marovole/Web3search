# Week 2 OpenRouter 集成 - 部署指南

## 📋 实施状态

### ✅ 已完成任务（T3-T6 + T10）

**核心库（134KB 代码）**
- ✅ `model-routing.ts` (312行) - 模型路由、权重、降级策略
- ✅ `streaming.ts` (299行) - SSE 流式适配器
- ✅ `resilience.ts` (336行) - 重试/熔断中间件
- ✅ `telemetry.ts` (395行) - 调用遥测和计费日志
- ✅ `chat-v2.ts` (385行) - Quick Chat 增强版 API

**数据库迁移**
- ✅ `20251110_create_api_calls_telemetry.sql` (427行)
  - api_calls 表（22字段，14索引，RLS策略）
  - 3个分析视图 + 2个存储函数

**提交**：8322d1d (30个文件，3817行代码)

## 🚀 立即执行的部署步骤

### 1. 应用数据库迁移 (1分钟)

#### 方法A：使用 Supabase CLI（推荐）
```bash
# 登录到 Supabase
cd /Users/marovole/GitHub/Web3search
supabase login

# 链接并推送迁移
supabase link --project-ref hxxnkbxyjhhorfeodiji
supabase db push
```

#### 方法B：手动执行 SQL
使用 Supabase Dashboard：https://supabase.com/dashboard/project/hxxnkbxyjhhorfeodiji/sql

打开 SQL 编辑器并粘贴 `supabase/migrations/20251110_create_api_calls_telemetry.sql` 的内容，然后执行。

### 2. 注册 Chat-v2 路由 (30秒)

编辑 `workers-api/src/index.ts`：

```typescript
import chatRoutes from './routes/chat'
import chatV2Routes from './routes/chat-v2' // 添加这行

...
app.route('/api/v1/chat', chatRoutes)
app.route('/api/v2/chat', chatV2Routes) // 添加这行
```

### 3. 部署 Workers (1分钟)

```bash
cd /Users/marovole/GitHub/Web3search/workers-api

# 部署到 Cloudflare Workers
npm run deploy

# 或者使用 wrangler
wrangler deploy
```

这将自动部署所有 Worker 端点，包括新的 `/api/v2/chat` 路由。

## 🧪 测试验证

### 测试模型路由
```bash
# 使用 Quick Chat v2 端点
POST https://web3search-api.marovole.workers.dev/api/v2/chat/quick-chat

# 请求体
{
  "query": "What is Bitcoin?",
  "stream": false,
  "use_case": "quick-chat"  // 或 "deep-research", "summarization", "code-assist"
}
```

### 预期响应
```json
{
  "conversation_id": "uuid",
  "message_id": "uuid",
  "content": "Bitcoin is a decentralized digital currency...",
  "model": "qwen/qwen-2.5-72b-instruct",
  "usage": { "prompt_tokens": 100, "completion_tokens": 150 }
}
```

### 验证遥测日志
检查 Supabase Dashboard 中的 `api_calls` 表，应该有：
- 模型信息（model_id, provider, use_case）
- 性能指标（latency_ms, retry_count）
- 成本数据（cost_usd）
- 错误追踪（error_code, circuit_state）

## 📈 监控和告警

### 关键指标

1. **API 调用成功率**
   ```sql
   SELECT
     (COUNT(CASE WHEN response_status BETWEEN 200 AND 299 THEN 1 END) * 100.0 /
      COUNT(*) * 1.0) as success_rate
   FROM api_calls
   WHERE created_at >= NOW() - INTERVAL '1 hour';
   ```

2. **平均延迟（P50, P95, P99）**
   ```sql
   SELECT
     percentile_cont(0.50) WITHIN GROUP (ORDER BY latency_ms) as p50,
     percentile_cont(0.95) WITHIN GROUP (ORDER BY latency_ms) as p95,
     percentile_cont(0.99) WITHIN GROUP (ORDER BY latency_ms) as p99
   FROM api_calls
   WHERE created_at >= NOW() - INTERVAL '1 hour';
   ```

3. **每日成本统计**
   ```sql
   SELECT
     provider,
     SUM(cost_usd) as total_cost
   FROM api_calls
   WHERE created_at >= NOW() - INTERVAL '1 day'
   GROUP BY provider
   ORDER BY total_cost DESC;
   ```

### 告警阈值
- 成功率 < 95%（15 分钟内）
- P99 延迟 > 5000ms（5 分钟内）
- 单个 IP 每日成本 > $10
- 熔断器开启 > 1 小时

## 📊 性能基线

目标指标：
- **端到端延迟**：< 1500ms（P95）
- **流式首字节时间**：< 500ms
- **API 可用性**：99.9%
- **成本效率**：<$0.01/请求（平均）

## 🔄 下一步计划

### 立即（今天）
- [ ] 应用数据库迁移
- [ ] 部署 chat-v2 路由
- [ ] 运行端到端测试

### 本周
- [ ] 实现 Deep Research 异步链路（T11，3h）
- [ ] 前端 SSE 流式支持（T13，4h）
- [ ] T7-T9 测试和文档（3h）

### 下周
- [ ] 缓存层优化（T16-T20）
- [ ] 端到端验证（T21-T23）
- [ ] 生产环境发布

## 🔧 技术债务

1. **数据库表不存在处理**：当前 code 假设有 `api_calls` 表，需要添加 try-catch
2. **Model Config 缺失**：如果 `getModelConfig()` 返回 null，需要优雅降级
3. **流式错误恢复**：SSE 断开时应该自动重连

## 📝 备注

- 当前 Workers 部署使用的是旧版 `/api/v1/chat` 端点
- 新 chat-v2 实现完全向后兼容
- 数据库迁移后自动启用全量遥测
- 建议先在 staging 环境测试后再部署到生产
