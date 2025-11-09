# 后台任务队列设置指南

本文档说明如何设置和部署 Week 3 Day 13-14 的后台任务队列系统。

## 系统架构

我们采用**混合方案**：
- **Supabase pg_cron**：执行纯 SQL 任务（数据清理、统计聚合）
- **Cloudflare Cron Triggers**：执行跨系统任务（健康检查、KV 清理）

## 任务列表

### pg_cron 任务（在数据库内执行）

| 任务名称 | 调度时间 | 描述 |
|---------|---------|------|
| `data-cleanup-old-conversations` | 每天 UTC 02:05 | 删除 30 天前的旧对话 |
| `daily-stats-aggregation` | 每天 UTC 02:15 | 生成每日统计指标 |
| `daily-hot-queries` | 每天 UTC 02:20 | 统计每日热门查询 Top 10 |
| `cleanup-failed-tasks` | 每周日 UTC 03:00 | 清理 7 天前的失败任务记录 |
| `cleanup-old-healthcheck-events` | 每天 UTC 03:30 | 清理 7 天前的健康检查记录 |

### Cloudflare Cron 任务（在 Workers 中执行）

| 任务名称 | 调度时间 | 描述 |
|---------|---------|------|
| 健康检查 | 每 5 分钟 | 检查 Supabase、OpenRouter、KV 的可用性 |
| KV 缓存清理 | 每小时 | 清理过期的深度研究缓存 |

## 部署步骤

### 1. 应用数据库迁移

首先需要创建必要的数据库表。

#### 方法 A：使用 Supabase CLI（推荐）

```bash
# 1. 安装 Supabase CLI（如果还没安装）
npm install -g supabase

# 2. 登录 Supabase
supabase login

# 3. 链接到你的 Supabase 项目
supabase link --project-ref hxxnkbxyjhhorfeodiji

# 4. 应用迁移
supabase db push

# 5. 验证迁移
supabase db dump --schema public
```

#### 方法 B：手动执行 SQL

1. 打开 Supabase Dashboard
2. 进入 **SQL Editor**
3. 执行 `supabase/migrations/20251109_create_background_tasks.sql`
4. 执行 `supabase/migrations/20251109_setup_pg_cron_jobs.sql`

### 2. 启用 pg_cron 扩展

1. 打开 Supabase Dashboard
2. 进入 **Database** → **Extensions**
3. 搜索 **pg_cron**
4. 点击 **Enable**

![启用 pg_cron](https://supabase.com/docs/img/database/extensions.png)

### 3. 验证 pg_cron 任务

运行以下 SQL 查看已配置的定时任务：

```sql
-- 查看所有 cron 任务
SELECT * FROM cron.job;

-- 查看任务运行历史
SELECT *
FROM cron.job_run_details
ORDER BY start_time DESC
LIMIT 20;
```

### 4. 配置 Workers Secrets

Cloudflare Workers Cron 需要以下环境变量：

```bash
# 切换到 workers 目录
cd workers

# 设置 Supabase 密钥
npx wrangler secret put SUPABASE_ANON_KEY
# 输入你的 Supabase Anon Key

# 设置 OpenRouter API 密钥
npx wrangler secret put OPENROUTER_API_KEY
# 输入你的 OpenRouter API Key

# （可选）设置 Supabase Service Role Key（用于完整权限）
npx wrangler secret put SUPABASE_SERVICE_ROLE_KEY
# 输入你的 Supabase Service Role Key
```

### 5. 部署 Workers

```bash
# 部署到生产环境
npm run deploy

# 查看部署后的 cron 任务
npx wrangler deployments list
```

### 6. 触发测试

#### 手动触发 pg_cron 任务

```sql
-- 手动运行数据清理任务（测试用）
DO $$
DECLARE
  v_task_id UUID;
BEGIN
  v_task_id := start_task_run('manual-test-cleanup', 'pg_cron');

  DELETE FROM conversations
  WHERE created_at < NOW() - INTERVAL '60 days';

  PERFORM finish_task_run(v_task_id, 'success', 0);
END $$;
```

#### 手动触发 Cloudflare Cron

```bash
# 通过 wrangler 触发健康检查
npx wrangler dev --test-scheduled

# 或者通过 API 手动触发
curl -X POST "https://web3search-worker.marovole.workers.dev/__scheduled?cron=*/5+*+*+*+*" \
  -H "Authorization: Bearer YOUR_TEST_TOKEN"
```

## 监控和告警

### 查看任务执行历史

```sql
-- 查看最近的任务运行记录
SELECT
  job_name,
  origin,
  status,
  rows_affected,
  duration_ms,
  started_at,
  finished_at,
  error_message
FROM task_runs
ORDER BY started_at DESC
LIMIT 20;

-- 查看失败的任务
SELECT *
FROM task_runs
WHERE status = 'failed'
ORDER BY started_at DESC;
```

### 查看每日统计

```sql
-- 查看最近 7 天的统计数据
SELECT *
FROM daily_metrics
ORDER BY stat_date DESC
LIMIT 7;

-- 查看热门查询
SELECT *
FROM daily_hot_queries
WHERE stat_date = CURRENT_DATE - INTERVAL '1 day'
ORDER BY rank;
```

### 查看健康检查状态

```sql
-- 查看最近的健康检查结果
SELECT
  check_name,
  status,
  latency_ms,
  error_message,
  observed_at
FROM healthcheck_events
ORDER BY observed_at DESC
LIMIT 20;

-- 统计各服务的健康状态
SELECT
  check_name,
  status,
  COUNT(*) as count,
  AVG(latency_ms) as avg_latency_ms
FROM healthcheck_events
WHERE observed_at > NOW() - INTERVAL '1 hour'
GROUP BY check_name, status;
```

## 故障排查

### pg_cron 任务不执行

1. 确认 pg_cron 扩展已启用：
   ```sql
   SELECT * FROM pg_extension WHERE extname = 'pg_cron';
   ```

2. 检查任务配置：
   ```sql
   SELECT * FROM cron.job;
   ```

3. 查看错误日志：
   ```sql
   SELECT *
   FROM cron.job_run_details
   WHERE status = 'failed'
   ORDER BY start_time DESC;
   ```

### Cloudflare Cron 不触发

1. 确认 wrangler.toml 中配置了 cron triggers
2. 检查 Workers 日志：
   ```bash
   npx wrangler tail
   ```

3. 验证环境变量已设置：
   ```bash
   npx wrangler secret list
   ```

### 健康检查失败

查看详细错误信息：

```sql
SELECT *
FROM healthcheck_events
WHERE status IN ('degraded', 'down')
ORDER BY observed_at DESC
LIMIT 10;
```

## 调整任务调度

### 修改 pg_cron 任务时间

```sql
-- 更新任务调度时间
UPDATE cron.job
SET schedule = '0 3 * * *'  -- 新的 cron 表达式
WHERE jobname = 'data-cleanup-old-conversations';
```

### 修改 Cloudflare Cron 时间

编辑 `workers/wrangler.toml`：

```toml
[triggers]
crons = [
  "*/10 * * * *",  # 改为每 10 分钟
  "0 */2 * * *",   # 改为每 2 小时
]
```

然后重新部署：

```bash
npm run deploy
```

## 取消任务

### 取消 pg_cron 任务

```sql
-- 取消特定任务
SELECT cron.unschedule('data-cleanup-old-conversations');

-- 查看剩余任务
SELECT * FROM cron.job;
```

### 移除 Cloudflare Cron

从 `wrangler.toml` 中删除对应的 cron 表达式，然后重新部署。

## 参考资料

- [Supabase pg_cron 文档](https://supabase.com/docs/guides/database/extensions/pg_cron)
- [Cloudflare Cron Triggers 文档](https://developers.cloudflare.com/workers/configuration/cron-triggers/)
- [Cron 表达式语法](https://crontab.guru/)
