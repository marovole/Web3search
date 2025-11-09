# Deployment Specification Delta

## MODIFIED Requirements

### Requirement: Cloudflare Pages 环境变量配置

Cloudflare Pages 构建 MUST 在构建时注入所有必需的环境变量，指向新的 Cloudflare Workers API。

#### Scenario: 构建时注入生产环境变量
**Given** Cloudflare Pages 触发生产环境构建
**When** 执行构建命令 `npm run build`
**Then** 所有 VITE_* 环境变量已设置：
 - VITE_ENVIRONMENT=production
 - VITE_API_BASE_URL=https://web3search-api.workers.dev
 - VITE_USE_MOCK_API=false
 - VITE_ENABLE_SENTRY=false
 - VITE_ENABLE_ANALYTICS=false
 - VITE_ENABLE_PERFORMANCE_MONITORING=true
 - VITE_DEBUG_MODE=false
**And** 构建产物中包含正确的环境变量值
**And** 不包含 .env 文件（仅使用注入的变量）

#### Scenario: 构建时验证必需环境变量
**Given** Cloudflare Pages 开始构建
**When** 执行构建前检查
**Then** 验证以下环境变量存在：
 - VITE_API_BASE_URL
 - VITE_ENVIRONMENT
**And** 如果任何必需变量缺失，构建失败并显示清晰的错误消息
**And** 错误消息指出缺失的变量名称

#### Scenario: 预览环境使用不同的 API URL
**Given** Cloudflare Pages 触发预览环境构建
**When** 执行构建命令
**Then** 使用预览环境的 API URL（如果配置）
**Or** 使用生产 API URL 作为默认值
**And** 构建产物标记为预览版本

## ADDED Requirements

### Requirement: Cloudflare Workers 项目部署

Cloudflare Workers MUST 正确配置和部署，作为新的后端 API 服务。

#### Scenario: Workers 项目初始化
**Given** 开发者准备部署 Workers 后端
**When** 使用 Wrangler CLI 初始化项目：`wrangler init web3search-api`
**Then** 项目包含以下文件：
 - wrangler.toml（配置文件）
 - src/index.ts（入口文件）
 - package.json
 - tsconfig.json
**And** 安装必需的依赖：hono、@supabase/supabase-js

#### Scenario: wrangler.toml 配置
**Given** Workers 项目已初始化
**When** 配置 wrangler.toml 文件
**Then** 包含以下配置：
```toml
name = "web3search-api"
main = "src/index.ts"
compatibility_date = "2024-01-01"

[env.production]
workers_dev = false
route = "web3search-api.workers.dev/*"

[[kv_namespaces]]
binding = "CACHE"
id = "<KV_NAMESPACE_ID>"
```
**And** 配置兼容性标志（如果需要）
**And** 配置环境变量绑定

#### Scenario: Workers 环境变量配置
**Given** Workers 项目准备部署
**When** 在 Cloudflare Dashboard 或通过 wrangler 配置环境变量
**Then** 配置以下变量：
 - SUPABASE_URL
 - SUPABASE_ANON_KEY
 - SUPABASE_SERVICE_ROLE_KEY（如果需要）
 - OPENROUTER_API_KEY
 - ENVIRONMENT=production
**And** 环境变量存储在 Cloudflare Secrets（不在代码中）
**And** 本地开发使用 `.dev.vars` 文件

#### Scenario: 首次部署 Workers
**Given** Workers 项目配置完成
**When** 执行部署命令：`wrangler deploy`
**Then** Workers 成功部署到 Cloudflare 边缘网络
**And** 返回部署 URL：`https://web3search-api.workers.dev`
**And** 健康检查端点可访问：`curl https://web3search-api.workers.dev/api/v1/health`
**And** 返回 200 状态码

#### Scenario: 自定义域名配置
**Given** Workers 已部署到默认 URL
**When** 配置自定义域名（如 api.web3search.com）
**Then** 在 Cloudflare Dashboard 中添加 Workers Route
**And** 绑定域名到 Workers
**And** 配置 SSL/TLS（自动或 Let's Encrypt）
**And** 自定义域名可访问 API

### Requirement: Supabase 数据库迁移和配置

Supabase MUST 正确配置并从现有 Render 数据库迁移数据。

#### Scenario: 创建 Supabase 项目
**Given** 用户有 Supabase 账户
**When** 创建新项目
**Then** 选择最近的区域（如 ap-northeast-1 for Asia）
**And** 设置项目名称：web3search
**And** 设置数据库密码（强密码）
**And** 项目创建成功，获取连接信息：
 - Project URL（用于 Supabase 客户端）
 - Anon Key（公开 API 密钥）
 - Service Role Key（服务端密钥）
 - Database Connection String（PostgreSQL）

#### Scenario: 导出 Render 数据库 Schema
**Given** 现有 Render PostgreSQL 数据库正在运行
**When** 使用 pg_dump 导出 schema：
```bash
pg_dump -h <render-host> -U <user> -d <database> --schema-only -f schema.sql
```
**Then** 成功导出 schema.sql 文件
**And** 文件包含所有表定义、索引、约束
**And** 验证文件大小和内容完整性

#### Scenario: 导出 Render 数据库数据
**Given** Schema 已成功导出
**When** 使用 pg_dump 导出数据：
```bash
pg_dump -h <render-host> -U <user> -d <database> --data-only -f data.sql
```
**Then** 成功导出 data.sql 文件
**And** 文件包含所有表数据
**And** 备份文件到安全位置（本地 + 云存储）

#### Scenario: 导入 Schema 到 Supabase
**Given** Supabase 项目已创建
**When** 在 Supabase SQL Editor 中执行 schema.sql
**Then** 所有表成功创建
**And** 所有索引和约束已应用
**And** 使用 Supabase Table Editor 验证表结构
**And** 表数量与 Render 数据库一致

#### Scenario: 导入数据到 Supabase
**Given** Schema 已成功导入
**When** 在 Supabase SQL Editor 中执行 data.sql
**Then** 所有数据成功导入
**And** 关键表的行数与 Render 数据库一致
**And** 抽样检查数据准确性（随机 100 条记录）
**And** 记录迁移报告

#### Scenario: 配置 Supabase Row Level Security
**Given** 数据已成功迁移
**When** 配置 RLS 策略（如果需要用户系统）
**Then** 为敏感表启用 RLS
**And** 配置策略：用户只能访问自己的数据
**And** 测试 RLS 策略（尝试未授权访问）

### Requirement: Cloudflare KV 配置（免费缓存层）

Cloudflare KV MUST 正确配置以提供缓存功能（免费层：100k reads/day，1k writes/day）。

#### Scenario: 创建 KV 命名空间
**Given** Workers 项目已存在
**When** 在 Cloudflare Dashboard 创建 KV 命名空间：`web3search_cache`
**Then** 获取 KV 命名空间 ID
**And** 在 wrangler.toml 中绑定 KV：
```toml
[[kv_namespaces]]
binding = "CACHE"
id = "<KV_NAMESPACE_ID>"
```
**And** Workers 代码中可通过 `env.CACHE` 访问 KV

#### Scenario: KV 缓存测试
**Given** KV 命名空间已配置
**When** 通过 Workers 写入测试数据：`await env.CACHE.put("test", "value", { expirationTtl: 60 })`
**Then** 数据成功写入
**And** 读取数据返回正确值：`await env.CACHE.get("test") === "value"`
**And** 60 秒后数据自动过期

#### Scenario: KV 免费层限制监控
**Given** KV 已在生产环境使用
**When** 监控 KV 使用量
**Then** 每日读取次数 < 100,000
**And** 每日写入次数 < 1,000
**And** 如果接近限制（> 80%），发送告警
**And** 优化缓存策略减少写入（延长 TTL，使用 Supabase 持久化）

### Requirement: Supabase Edge Functions 配置（异步任务，免费）

如果需要后台异步任务（如报告生成），Supabase Edge Functions MUST 正确配置和部署。

#### Scenario: 创建 Edge Function 项目结构
**Given** Supabase 项目已创建
**When** 初始化 Edge Functions 项目：`supabase functions new generate-report`
**Then** 创建以下文件结构：
```
supabase/
  functions/
    generate-report/
      index.ts
    _shared/
      supabase.ts
```
**And** index.ts 包含 Deno runtime 代码
**And** 安装必需的 Deno 依赖（import maps）

#### Scenario: Edge Function 实现
**Given** Edge Function 项目已创建
**When** 实现报告生成逻辑（supabase/functions/generate-report/index.ts）
**Then** 函数接收 HTTP POST 请求（JSON body）
**And** 调用 OpenRouter API 生成报告内容
**And** 将结果保存到 Supabase `reports` 表
**And** 更新任务状态为 completed 或 failed
**And** 返回响应（200 成功，500 失败）

#### Scenario: 部署 Edge Function
**Given** Edge Function 代码已完成
**When** 部署到 Supabase：`supabase functions deploy generate-report`
**Then** 函数成功部署到 Supabase 边缘网络
**And** 获取函数 URL：`https://<project-ref>.supabase.co/functions/v1/generate-report`
**And** 配置环境变量（OPENROUTER_API_KEY）通过 Supabase Secrets
**And** 测试函数调用返回 200

#### Scenario: Workers 调用 Edge Function（异步任务）
**Given** Edge Function 已部署
**When** Workers API 接收报告生成请求
**Then** 创建报告任务记录（status: pending）
**And** 异步调用 Edge Function（不等待响应）：
```typescript
fetch('https://<project-ref>.supabase.co/functions/v1/generate-report', {
  method: 'POST',
  body: JSON.stringify({ report_id, topic }),
  headers: { 'Authorization': `Bearer ${SUPABASE_ANON_KEY}` }
}).catch(err => console.error(err)); // 不阻塞主请求
```
**And** 立即返回任务 ID 给前端（202 Accepted）
**And** 前端轮询任务状态或使用 WebSocket 接收完成通知

#### Scenario: Edge Function 性能测试
**Given** Edge Function 已部署
**When** 发送 10 个并发报告生成请求
**Then** 所有任务在合理时间内完成（< 5 分钟）
**And** 成功率 > 90%
**And** 记录平均响应时间

### Requirement: Supabase pg_cron 配置（定时任务，免费）

Supabase pg_cron MUST 正确配置用于定时任务（数据清理、统计生成等）。

#### Scenario: 启用 pg_cron 扩展
**Given** Supabase 项目已创建
**When** 在 Supabase SQL Editor 中启用 pg_cron：
```sql
CREATE EXTENSION IF NOT EXISTS pg_cron;
```
**Then** pg_cron 扩展成功启用
**And** 验证扩展：`SELECT * FROM cron.job;`
**And** 免费层可用（无额外费用）

#### Scenario: 配置数据清理定时任务
**Given** pg_cron 已启用
**When** 创建清理函数和定时任务：
```sql
-- 创建清理函数
CREATE OR REPLACE FUNCTION cleanup_old_conversations()
RETURNS void AS $$
BEGIN
  DELETE FROM messages WHERE conversation_id IN (
    SELECT id FROM conversations WHERE created_at < NOW() - INTERVAL '30 days'
  );
  DELETE FROM conversations WHERE created_at < NOW() - INTERVAL '30 days';
END;
$$ LANGUAGE plpgsql;

-- 配置每日凌晨 2 点执行
SELECT cron.schedule(
  'cleanup-conversations',
  '0 2 * * *',
  'SELECT cleanup_old_conversations();'
);
```
**Then** 定时任务成功创建
**And** 查看任务列表：`SELECT * FROM cron.job;`
**And** 任务按计划执行

#### Scenario: 配置统计任务
**Given** pg_cron 已启用
**When** 创建统计函数和定时任务：
```sql
CREATE OR REPLACE FUNCTION generate_daily_statistics()
RETURNS void AS $$
BEGIN
  INSERT INTO statistics (date, metric_name, value)
  SELECT CURRENT_DATE, 'api_calls', COUNT(*)
  FROM api_logs WHERE created_at >= CURRENT_DATE;
END;
$$ LANGUAGE plpgsql;

SELECT cron.schedule(
  'daily-statistics',
  '59 23 * * *',
  'SELECT generate_daily_statistics();'
);
```
**Then** 统计任务成功创建
**And** 每天 23:59 自动生成统计数据

#### Scenario: 监控 pg_cron 任务执行
**Given** pg_cron 任务已配置
**When** 查看任务执行历史
**Then** 查询任务日志表（如果已配置）
**And** 验证任务按计划执行
**And** 如果任务失败，检查错误日志并修复

### Requirement: 灰度发布配置

部署 MUST 支持灰度发布，逐步切换流量从 Render 到 Cloudflare Workers。

#### Scenario: 配置流量路由规则
**Given** Cloudflare Workers 和 Render 后端同时运行
**When** 在 Cloudflare Load Balancer 或 Workers 中配置流量分配
**Then** 支持按百分比分配流量：
 - 10% → Cloudflare Workers
 - 90% → Render（通过代理）
**And** 流量分配可动态调整（无需重新部署）
**And** 基于请求头或 Cookie 进行分流（可选）

#### Scenario: 10% 流量切换
**Given** 灰度发布已配置
**When** 切换 10% 流量到 Workers
**Then** Workers 接收约 10% 的请求
**And** Render 接收约 90% 的请求
**And** 监控显示流量分配正确
**And** 两套系统的错误率和响应时间可对比

#### Scenario: 逐步增加流量
**Given** 10% 流量运行正常
**When** 逐步增加流量：10% → 50% → 100%
**Then** 每次增加后运行稳定观察期（30 分钟 - 1 小时）
**And** 监控错误率、响应时间、数据库负载
**And** 如果发现异常，立即回滚到上一个比例
**And** 最终 100% 流量切换到 Workers

#### Scenario: 回滚机制
**Given** 灰度发布过程中发现问题
**When** 触发回滚操作
**Then** 立即将 100% 流量切回 Render
**And** Workers 停止接收新请求
**And** 记录回滚原因和时间
**And** 回滚在 1 分钟内完成

### Requirement: 部署验证自动化

每次部署后 MUST 自动运行验证脚本，确保服务可用。

#### Scenario: Workers 部署后验证
**Given** Cloudflare Workers 完成部署
**When** 部署钩子触发（wrangler 部署后脚本）
**Then** 自动运行健康检查：
 - 验证 /api/v1/health 返回 200
 - 验证数据库连接状态
 - 验证关键 API 端点可访问
**And** 如果验证失败，发送告警通知
**And** 如果验证失败，自动回滚到上一个版本

#### Scenario: 前端部署后验证
**Given** Cloudflare Pages 完成部署
**When** 部署钩子触发
**Then** 自动运行烟雾测试脚本
**And** 验证以下内容：
 - 页面可访问（返回 200）
 - 关键资源加载成功（JS、CSS）
 - 无 JavaScript 错误
 - API 连接正常（调用健康检查）
**And** 如果验证失败，发送告警通知

#### Scenario: E2E 测试自动触发
**Given** 前后端部署完成
**When** CI/CD 触发 E2E 测试
**Then** 在生产环境运行完整的 Playwright 测试套件
**And** 验证关键用户流程（搜索、聊天）
**And** 测试通过率 > 95%
**And** 如果测试失败，标记部署为不稳定并通知团队

### Requirement: Vercel 部署彻底移除

Vercel 部署 MUST 完全移除，简化部署流程。

#### Scenario: 删除 Vercel 项目
**Given** Vercel 项目仍然存在（但已失效）
**When** 在 Vercel Dashboard 中删除项目
**Then** 确认删除操作
**And** 项目从 Vercel 完全移除
**And** 相关域名解绑

#### Scenario: 移除 Vercel 配置文件
**Given** 代码仓库包含 Vercel 配置
**When** 清理 Vercel 相关文件
**Then** 删除以下文件：
 - vercel.json
 - .vercelignore
**And** 搜索并移除代码中的 Vercel 引用：`grep -r "vercel" .`
**And** 提交更改到 Git

#### Scenario: 移除 CI/CD 中的 Vercel 部署
**Given** CI/CD 包含 Vercel 部署步骤
**When** 清理 .github/workflows/ 文件
**Then** 删除或注释 Vercel 部署步骤
**And** 移除 VERCEL_TOKEN 等 Secrets
**And** 更新 workflow 仅部署到 Cloudflare Pages
**And** 提交更改

#### Scenario: 更新文档移除 Vercel 说明
**Given** 文档包含 Vercel 部署说明
**When** 更新 README.md 和部署文档
**Then** 移除所有 Vercel 相关说明
**And** 添加说明：前端仅部署到 Cloudflare Pages
**And** 保留 Vercel 配置到 Git 历史（以防未来需要）

## REMOVED Requirements

### ~~Requirement: Render 后端健康检查配置~~
**移除原因**: 后端从 Render 迁移到 Cloudflare Workers，Render 相关配置不再需要

### ~~Requirement: Render 服务冷启动优化~~
**移除原因**: Cloudflare Workers 无冷启动问题，不需要优化

### ~~Requirement: Render 环境变量管理~~
**移除原因**: 后端迁移到 Workers，使用 Cloudflare Secrets 管理环境变量

### ~~Requirement: 前端运行时配置简化（hostname 检测）~~
**移除原因**: 保留构建时环境变量注入，不需要移除 hostname 检测（可能有其他用途）

### ~~Requirement: Vercel 部署策略决策（保留或移除）~~
**移除原因**: 已决策彻底移除 Vercel，不需要"决策"需求
