# Tasks: Migrate to Cloudflare Workers + Supabase

## Week 1: 搭建基础架构（Day 1-5）

### Day 1-2: Supabase 项目设置和数据库迁移

#### Supabase 项目创建
- [x] 创建 Supabase 账户（如果没有）
- [x] 创建新的 Supabase 项目（选择最近的区域）
- [x] 获取 Supabase 项目 URL 和 anon key
- [x] 获取 Supabase 数据库连接字符串（PostgreSQL）
- [x] 配置 Supabase 项目设置（时区、备份策略）

#### 数据库 Schema 导出
- [x] 连接到现有 Render PostgreSQL 数据库
- [x] 导出数据库 schema（使用 `pg_dump --schema-only`）
- [x] 导出数据库数据（使用 `pg_dump --data-only` 或 `COPY TO`）
- [x] 检查导出文件的完整性和大小
- [x] 备份导出文件到安全位置（本地 + 云存储）

#### Supabase 数据库迁移
- [x] 在 Supabase 中创建数据库 schema（执行 schema.sql）
- [x] 验证表结构、索引、约束是否正确
- [x] 导入数据到 Supabase（使用 Supabase CLI 或 SQL）
- [x] 验证数据完整性（行数、关键记录检查）
- [x] 创建必要的数据库索引优化查询性能
- [x] 配置 Row Level Security (RLS) 策略（如果需要）

#### 数据验证
- [x] 比对 Render 和 Supabase 数据库的表数量
- [x] 比对关键表的行数（users、messages、reports 等）
- [x] 抽样检查数据准确性（随机 100 条记录）
- [x] 测试关键查询在 Supabase 上的性能
- [x] 记录迁移报告（成功/失败的表、行数统计）

### Day 3-4: Cloudflare Workers 项目搭建

#### Cloudflare 账户和项目设置
- [x] 确认 Cloudflare 账户管理员权限
- [x] 在 Cloudflare Dashboard 中创建新 Workers 项目
- [x] 安装 Wrangler CLI：`npm install -g wrangler`
- [x] 登录 Wrangler：`wrangler login`
- [x] 初始化 Workers 项目：`wrangler init web3search-api`

#### 项目结构搭建
- [x] 安装 Hono 框架：`npm install hono`
- [x] 安装 Supabase 客户端：`npm install @supabase/supabase-js`
- [x] 创建项目目录结构：
  ```
  src/
    ├── index.ts          # 入口文件
    ├── routes/           # 路由定义
    ├── middlewares/      # 中间件（日志、认证等）
    ├── services/         # 业务逻辑
    ├── utils/            # 工具函数
    └── types/            # TypeScript 类型定义
  ```
- [x] 配置 TypeScript（tsconfig.json）
- [x] 配置 ESLint 和 Prettier

#### Supabase 客户端配置
- [x] 创建 Supabase 客户端初始化模块（`src/lib/supabase.ts`）
- [x] 配置 Supabase 连接（使用环境变量）
- [x] 实现数据库连接测试函数
- [x] 添加错误处理和重试逻辑

#### 环境变量配置
- [x] 在 Cloudflare Workers 中配置环境变量（通过 Dashboard 或 wrangler.toml）：
  - SUPABASE_URL
  - SUPABASE_ANON_KEY
  - SUPABASE_SERVICE_ROLE_KEY（如果需要）
  - OPENROUTER_API_KEY
  - ENVIRONMENT=production
- [x] 创建 `.dev.vars` 文件用于本地开发
- [x] 测试环境变量是否正确注入

#### 健康检查端点实现
- [x] 实现 `/api/v1/health` 端点（Hono 路由）
- [x] 健康检查包含以下信息：
  - 服务状态（healthy/degraded/unhealthy）
  - Supabase 数据库连接状态
  - 响应时间戳
  - 服务版本号
  - 运行时间（uptime）
- [x] 添加数据库连接验证（执行简单查询：`SELECT 1`）
- [x] 实现错误处理（数据库连接失败返回 503）

#### 本地开发和测试
- [x] 启动本地开发服务器：`wrangler dev`
- [x] 测试健康检查端点：`curl http://localhost:8787/api/v1/health`
- [x] 验证 Supabase 连接是否工作
- [x] 测试错误场景（断开数据库连接）

#### 部署到 Cloudflare Workers
- [x] 配置 wrangler.toml（路由、环境变量、兼容性设置）
- [x] 首次部署：`wrangler deploy`
- [x] 验证部署成功（检查 Workers Dashboard）
- [x] 测试生产环境健康检查：`curl https://web3search-api.workers.dev/api/v1/health`
- [x] 配置自定义域名（如果需要）

### Day 5: 实现只读 API

#### 搜索自动完成 API 迁移
- [x] 分析现有 Python `/api/v1/search/autocomplete` 实现
- [x] 创建 TypeScript 版本的路由处理器（`src/routes/search.ts`）
- [x] 实现自动完成逻辑：
  - 从 Supabase 查询匹配的关键词
  - 支持模糊搜索（LIKE 或全文搜索）
  - 限制返回结果数量（最多 10 条）
- [x] 添加输入验证（查询长度、特殊字符过滤）
- [x] 实现错误处理（数据库查询失败、超时）

#### Cloudflare KV 缓存配置
- [x] 在 Cloudflare Dashboard 创建 KV 命名空间：`web3search_cache`
- [x] 绑定 KV 到 Workers（在 wrangler.toml 中配置）
- [x] 创建缓存工具模块（`src/utils/cache.ts`）
- [x] 实现缓存读取函数（带 TTL 检查）
- [x] 实现缓存写入函数（设置过期时间）

#### 自动完成 API 缓存集成
- [x] 在自动完成 API 中集成 KV 缓存
- [x] 实现缓存策略：
  - 缓存热门查询（访问频率 > 10 次/小时）
  - TTL 设置为 1 小时
  - 缓存键格式：`autocomplete:{query}`
- [x] 实现缓存命中统计（用于监控）
- [x] 测试缓存性能（响应时间对比）

#### API 测试和验证
- [x] 单元测试：测试自动完成逻辑（使用 Vitest）
- [x] 集成测试：测试 Supabase 查询
- [x] 性能测试：测试缓存命中和未命中场景
- [x] 边界测试：空查询、超长查询、特殊字符
- [x] 部署到生产环境
- [x] 验证生产环境功能：`curl https://web3search-api.workers.dev/api/v1/search/autocomplete?q=bitcoin`

#### Trending API 迁移（可选）
- [ ] 分析现有 `/api/v1/trending` 实现
- [ ] 创建 TypeScript 版本的路由处理器
- [ ] 从 Supabase 查询趋势数据（按热度排序）
- [ ] 实现缓存（TTL 15 分钟）
- [ ] 测试和部署

---

## Week 2: 迁移核心 API（Day 6-10）

### Day 6-7: OpenRouter API 集成

#### OpenRouter SDK 集成
- [ ] 研究 OpenRouter API 文档（https://openrouter.ai/docs）
- [ ] 安装 HTTP 客户端库（如果需要自定义）或使用 fetch
- [ ] 创建 OpenRouter 客户端模块（`src/lib/openrouter.ts`）
- [ ] 实现 API 调用函数：
  - 支持流式响应（Server-Sent Events）
  - 支持非流式响应
  - 配置超时时间（30 秒）
- [ ] 配置 OpenRouter API Key（从环境变量读取）

#### 流式响应处理
- [ ] 实现 SSE（Server-Sent Events）响应格式
- [ ] 创建流式数据处理函数：
  - 解析 OpenRouter 返回的 JSON 流
  - 转换为前端期望的格式
  - 处理流中断和错误
- [ ] 实现流式响应超时处理
- [ ] 测试流式响应（本地开发环境）

#### 错误处理和重试逻辑
- [ ] 实现 OpenRouter API 错误处理：
  - 401 未授权（API Key 错误）
  - 429 速率限制（超过配额）
  - 500 服务器错误
  - 网络超时
- [ ] 实现指数退避重试（最多 3 次）
- [ ] 记录错误日志（包含请求 ID、错误类型、重试次数）
- [ ] 实现降级处理（OpenRouter 不可用时返回友好错误）

#### OpenRouter 模型配置
- [ ] 配置默认模型（如 `anthropic/claude-3.5-sonnet`）
- [ ] 支持模型选择（通过请求参数）
- [ ] 配置模型参数：
  - temperature: 0.7
  - max_tokens: 4000
  - top_p: 0.9
- [ ] 实现成本追踪（记录 token 使用量）

### Day 8-9: 迁移聊天 API

#### 聊天 API 路由创建
- [ ] 分析现有 Python `/api/v1/chat/quick-chat` 实现
- [ ] 创建 TypeScript 版本的路由处理器（`src/routes/chat.ts`）
- [ ] 定义请求/响应类型：
  ```typescript
  interface ChatRequest {
    query: string;
    conversation_id?: string;
    model?: string;
    stream?: boolean;
  }
  ```
- [ ] 实现请求验证（query 非空、长度限制）

#### 消息历史存储
- [ ] 在 Supabase 中创建 `conversations` 表（如果不存在）
- [ ] 在 Supabase 中创建 `messages` 表（如果不存在）
- [ ] 实现消息保存函数：
  - 保存用户消息
  - 保存 AI 响应
  - 关联 conversation_id
  - 记录时间戳
- [ ] 实现对话历史检索函数（获取最近 10 条消息）

#### 聊天逻辑实现
- [ ] 实现聊天流程：
  1. 验证请求参数
  2. 检索对话历史（如果有 conversation_id）
  3. 构建 OpenRouter 请求（包含上下文）
  4. 调用 OpenRouter API
  5. 保存 AI 响应到数据库
  6. 返回响应给前端
- [ ] 实现流式响应模式
- [ ] 实现非流式响应模式
- [ ] 添加系统提示词（System Prompt）配置

#### 速率限制实现（使用 KV）
- [ ] 使用 Cloudflare KV 实现速率限制（免费方案）
- [ ] 创建速率限制器类（`src/lib/rate-limiter.ts`）
- [ ] 实现 KV 键格式：`rate_limit:{ip}:{hour}` → 请求计数
- [ ] 配置限制规则：
  - 每个 IP：10 请求/小时（聊天 API）
  - 每个 IP：20 请求/分钟（全局）
- [ ] 使用 KV TTL 自动过期（1 小时或 1 分钟）
- [ ] 返回速率限制响应头：`X-RateLimit-Limit`, `X-RateLimit-Remaining`
- [ ] 超过限制返回 429 错误
- [ ] 注意：KV 最终一致性，接受轻微误差（边界情况）

#### 聊天 API 测试
- [ ] 单元测试：测试请求验证、消息保存
- [ ] 集成测试：测试 OpenRouter 调用、数据库保存
- [ ] 流式响应测试（使用 curl 或 Postman）
- [ ] 速率限制测试（模拟高频请求）
- [ ] 部署到生产环境
- [ ] 验证生产环境功能

### Day 10: 实现缓存层（使用 KV + Supabase）

#### Cloudflare KV 缓存配置
- [ ] 确认 KV 命名空间已创建（Week 1 Day 5 已创建）
- [ ] 创建缓存工具模块（`src/utils/cache.ts`）
- [ ] 实现 KV 缓存读取函数（带 TTL 检查）
- [ ] 实现 KV 缓存写入函数（设置过期时间）
- [ ] 处理 KV 操作错误（缓存失败不影响功能）

#### 聊天上下文缓存策略
- [ ] 设计缓存策略：
  - **热数据**：KV 缓存最近 10 条对话（conversation_id 为键）
  - **持久化**：Supabase 存储完整对话历史
  - **读取顺序**：优先 Supabase（保证数据一致性），KV 作为辅助
- [ ] 实现缓存键格式：`chat:{conversation_id}` → JSON 消息数组
- [ ] TTL 设置为 1 小时
- [ ] 接受 KV 最终一致性（秒级延迟可接受）

#### 搜索结果缓存
- [ ] 实现搜索自动完成缓存：
  - 缓存热门查询结果（访问频率 > 10 次/小时）
  - 键格式：`autocomplete:{query}`
  - TTL: 1 小时
- [ ] 实现趋势数据缓存（如果有）：
  - 缓存趋势列表
  - TTL: 15 分钟

#### 缓存集成到聊天 API
- [ ] 在聊天 API 中优先从 Supabase 读取对话历史（保证一致性）
- [ ] 异步更新 KV 缓存（不阻塞响应）
- [ ] 实现缓存失败降级（直接查询 Supabase）

#### 缓存性能优化和监控
- [ ] 测试缓存命中率（目标 > 70%，KV 为辅助缓存）
- [ ] 测试响应时间（Supabase 查询 < 500ms）
- [ ] 优化缓存键设计（避免冲突）
- [ ] 实现缓存统计（记录命中/未命中次数）
- [ ] 监控 KV 配额使用（100k 读/天，1k 写/天）

#### Week 1-2 验证
- [ ] 运行完整的功能测试（健康检查、搜索、聊天）
- [ ] 性能测试：响应时间 < 500ms（健康检查）、< 2s（聊天）
- [ ] 错误处理测试：数据库断开、OpenRouter 失败
- [ ] 记录 Week 1-2 完成报告

---

## Week 3: 迁移复杂功能（Day 11-15）

### Day 11-12: 报告生成 API 迁移（使用 Supabase Edge Functions）

#### 分析现有报告生成逻辑
- [ ] 审查 Python 版本的报告生成 API
- [ ] 识别计算密集型任务
- [ ] 设计两种方案：Edge Functions 或前端流式生成

#### Supabase Edge Functions 设置
- [ ] 在 Supabase Dashboard 启用 Edge Functions
- [ ] 创建 Edge Function：`generate-report`（使用 Deno runtime）
- [ ] 配置 Edge Function 环境变量（OPENROUTER_API_KEY）
- [ ] 部署 Edge Function 到 Supabase

#### 方案 A：后台异步生成（Edge Functions + pg_cron）
- [ ] 创建报告生成路由（`POST /api/v1/reports/generate`）
- [ ] Workers API 实现：
  1. 验证请求参数（主题、sections）
  2. 创建报告任务记录（Supabase reports 表）
  3. 调用 Supabase Edge Function（异步）
  4. 返回任务 ID 给前端（202 Accepted）
- [ ] Edge Function 实现：
  1. 接收报告任务 ID
  2. 更新状态为 "processing"
  3. 为每个 section 调用 OpenRouter
  4. 分段保存内容到 Supabase
  5. 更新状态为 "completed"
- [ ] 实现任务状态查询端点（`GET /api/v1/reports/{id}`）
- [ ] 使用 pg_cron 定期检查超时任务（可选）

#### 方案 B（推荐）：前端流式生成
- [ ] 简化实现：Workers API 直接流式返回报告内容
- [ ] 前端实时显示生成的每个 section
- [ ] 用户体验更好（无需等待和轮询）
- [ ] 无需 Edge Functions 和复杂的任务队列
- [ ] 生成完成后可选保存到 Supabase

#### 选择并实现方案
- [ ] 评估两种方案的优劣
- [ ] 选择方案 B（前端流式生成）作为首选
- [ ] 如需后台生成，使用方案 A（Edge Functions）

#### 报告 API 测试
- [ ] 测试报告生成请求
- [ ] 测试流式响应（如方案 B）或 Edge Function 调用（如方案 A）
- [ ] 测试任务状态查询（如方案 A）
- [ ] 测试长时间运行任务（> 1 分钟）
- [ ] 测试错误场景（OpenRouter 失败、超时）

### Day 13-14: 后台任务队列实现（使用 Supabase pg_cron）

#### pg_cron 扩展配置
- [ ] 在 Supabase 中启用 pg_cron 扩展：
  ```sql
  CREATE EXTENSION IF NOT EXISTS pg_cron;
  ```
- [ ] 验证 pg_cron 已启用：`SELECT * FROM cron.job;`
- [ ] 了解 pg_cron 限制：
  - 免费层可用
  - 仅支持 SQL 函数调用
  - 需要创建数据库函数来执行任务

#### 数据清理任务（使用 pg_cron）
- [ ] 创建清理函数（`cleanup_old_conversations`）：
  ```sql
  CREATE OR REPLACE FUNCTION cleanup_old_conversations()
  RETURNS void AS $$
  BEGIN
    DELETE FROM messages WHERE conversation_id IN (
      SELECT id FROM conversations WHERE created_at < NOW() - INTERVAL '30 days'
    );
    DELETE FROM conversations WHERE created_at < NOW() - INTERVAL '30 days';
    INSERT INTO task_logs (task_name, status, message)
    VALUES ('cleanup_old_conversations', 'success', 'Cleaned old conversations');
  END;
  $$ LANGUAGE plpgsql;
  ```
- [ ] 配置定时任务（每天凌晨 2 点）：
  ```sql
  SELECT cron.schedule(
    'cleanup-conversations',
    '0 2 * * *',
    'SELECT cleanup_old_conversations();'
  );
  ```
- [ ] 创建 KV 缓存清理任务（通过 Workers 端点 + cron）：
  - 创建 `/api/v1/internal/cleanup-cache` 端点
  - 使用外部 cron 服务（如 cron-job.org 免费）调用端点
  - 或者接受缓存 TTL 自动过期（推荐）

#### 统计任务（使用 pg_cron）
- [ ] 创建每日统计函数（`generate_daily_statistics`）：
  ```sql
  CREATE OR REPLACE FUNCTION generate_daily_statistics()
  RETURNS void AS $$
  BEGIN
    INSERT INTO statistics (date, metric_name, value)
    SELECT
      CURRENT_DATE,
      'api_calls',
      COUNT(*)
    FROM api_logs
    WHERE created_at >= CURRENT_DATE;
    -- 添加其他统计指标...
  END;
  $$ LANGUAGE plpgsql;
  ```
- [ ] 配置定时任务（每天 23:59）：
  ```sql
  SELECT cron.schedule(
    'daily-statistics',
    '59 23 * * *',
    'SELECT generate_daily_statistics();'
  );
  ```
- [ ] 实现 token 使用量统计（从 api_logs 表聚合）
- [ ] 实现活跃用户统计（如果有用户系统）

#### 任务监控
- [ ] 创建任务日志表（`task_logs`）：
  ```sql
  CREATE TABLE task_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_name TEXT NOT NULL,
    status TEXT NOT NULL,
    message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
  );
  ```
- [ ] 每个定时任务函数记录执行结果到 `task_logs`
- [ ] 创建查询视图查看任务执行历史
- [ ] （可选）配置 Supabase Webhooks 发送失败告警到邮件或 Slack

### Day 15: 用户认证（可选）

#### Supabase Auth 配置
- [ ] 在 Supabase 中启用 Auth 功能
- [ ] 配置认证方式（Email + Password 或 OAuth）
- [ ] 配置 JWT 设置（过期时间、刷新令牌）
- [ ] 创建用户表和角色定义

#### Workers 认证中间件
- [ ] 创建认证中间件（`src/middlewares/auth.ts`）
- [ ] 实现 JWT 验证逻辑：
  1. 从 Authorization 头提取 token
  2. 验证 token 有效性（使用 Supabase）
  3. 提取用户信息（user_id、role）
  4. 注入到请求上下文
- [ ] 实现未授权错误处理（返回 401）

#### 保护 API 端点
- [ ] 为需要认证的端点添加中间件
- [ ] 聊天 API 添加用户关联（保存用户 ID）
- [ ] 报告 API 添加权限检查（仅创建者可查看）
- [ ] 测试认证流程（登录、访问保护端点、登出）

#### 认证测试
- [ ] 测试用户注册和登录
- [ ] 测试 JWT 验证
- [ ] 测试未授权访问（返回 401）
- [ ] 测试 token 过期和刷新

#### Week 3 验证
- [ ] 运行完整的功能测试（报告生成、定时任务、认证）
- [ ] 测试队列处理性能
- [ ] 记录 Week 3 完成报告

---

## Week 4: 测试、优化和切换（Day 16-20）

### Day 16-17: 端到端测试

#### E2E 测试环境配置
- [ ] 更新 Playwright 配置（`playwright.config.ts`）
- [ ] 配置测试环境变量指向新 API：
  ```
  VITE_API_BASE_URL=https://web3search-api.workers.dev
  ```
- [ ] 创建测试数据库（Supabase 测试项目）
- [ ] 准备测试数据（种子数据）

#### 前端环境配置更新
- [ ] 更新前端 `.env.production` 文件：
  ```
  VITE_API_BASE_URL=https://web3search-api.workers.dev
  VITE_ENVIRONMENT=production
  VITE_USE_MOCK_API=false
  ```
- [ ] 在 Cloudflare Pages 中配置环境变量
- [ ] 触发前端重新构建
- [ ] 验证前端可以连接新 API

#### E2E 测试执行
- [ ] 运行完整的 E2E 测试套件：`npx playwright test`
- [ ] 测试关键用户流程：
  - 访问首页
  - 进行搜索（自动完成）
  - 发起聊天对话
  - 生成报告（如果实现）
  - 主题切换、设置页面
- [ ] 记录测试结果和失败用例
- [ ] 修复发现的 bug

#### Bug 修复
- [ ] 修复 API 兼容性问题（请求/响应格式差异）
- [ ] 修复前端集成问题（CORS、超时）
- [ ] 修复数据格式不一致问题
- [ ] 重新运行测试验证修复

#### 回归测试
- [ ] 再次运行完整测试套件
- [ ] 确保测试通过率 > 95%
- [ ] 记录剩余的已知问题（如果有）

### Day 18: 性能测试和优化

#### 性能测试准备
- [ ] 选择性能测试工具（k6、Apache Bench、或 Cloudflare Load Testing）
- [ ] 准备测试脚本（模拟真实用户行为）
- [ ] 配置测试场景：
  - 并发用户数：10、50、100、500
  - 请求类型：健康检查、搜索、聊天

#### 负载测试执行
- [ ] 执行健康检查负载测试（目标：1000 req/s，响应时间 < 100ms）
- [ ] 执行搜索 API 负载测试（目标：500 req/s，响应时间 < 500ms）
- [ ] 执行聊天 API 负载测试（目标：100 req/s，响应时间 < 2s）
- [ ] 记录性能指标：
  - 平均响应时间
  - P95、P99 响应时间
  - 错误率
  - CPU 使用率

#### 性能瓶颈分析
- [ ] 识别慢查询（使用 Supabase 查询分析工具）
- [ ] 分析缓存命中率
- [ ] 检查数据库索引使用情况
- [ ] 分析 OpenRouter API 调用延迟

#### 性能优化
- [ ] 优化数据库查询：
  - 添加缺失的索引
  - 重写慢查询
  - 使用查询缓存
- [ ] 优化缓存策略：
  - 增加热门数据缓存时间
  - 实现缓存预热
- [ ] 优化 Workers 代码：
  - 减少不必要的计算
  - 使用并行处理
  - 优化 JSON 序列化

#### Cloudflare CDN 配置
- [ ] 配置缓存规则（Cache Rules）：
  - 静态响应缓存 5 分钟（如趋势数据）
  - 动态响应不缓存（如聊天）
- [ ] 配置压缩（Brotli、Gzip）
- [ ] 配置 HTTP/3 和 QUIC
- [ ] 测试 CDN 缓存命中率

#### 优化后验证
- [ ] 重新运行负载测试
- [ ] 对比优化前后性能指标
- [ ] 确保性能目标达成：
  - 健康检查 < 100ms
  - 搜索 API < 500ms
  - 聊天 API < 2s（首 token）
- [ ] 记录性能优化报告

### Day 19-20: 灰度发布

#### 灰度发布准备
- [ ] 确认 Render 后端仍在运行（作为备用）
- [ ] 准备流量切换方案（使用 Cloudflare Workers Routes）
- [ ] 配置监控和告警（Cloudflare Analytics + 第三方）
- [ ] 准备回滚计划

#### 监控配置
- [ ] 配置 Cloudflare Workers Analytics
- [ ] 配置日志收集（Logflare 或 Datadog）
- [ ] 配置错误追踪（Sentry for Workers）
- [ ] 配置实时告警（错误率 > 5% 或响应时间 > 3s）
- [ ] 创建监控仪表板（Grafana 或 Cloudflare Dashboard）

#### 10% 流量切换
- [ ] 配置 Cloudflare Workers Routes：
  - 10% 流量 → Cloudflare Workers
  - 90% 流量 → Render (通过 Cloudflare Proxy)
- [ ] 使用 Cloudflare Load Balancer 或自定义路由逻辑
- [ ] 验证流量分配正确
- [ ] 监控 10% 流量的表现（错误率、响应时间）

#### 10% 流量验证
- [ ] 运行 30 分钟，持续监控
- [ ] 检查错误日志（是否有新错误）
- [ ] 对比两套系统的响应时间
- [ ] 检查用户反馈（如果有）
- [ ] 如果正常，继续；如果异常，回滚

#### 50% 流量切换
- [ ] 调整流量分配：50% Workers、50% Render
- [ ] 运行 1 小时，持续监控
- [ ] 对比性能指标
- [ ] 验证缓存和数据库负载
- [ ] 如果正常，继续；如果异常，回滚

#### 100% 流量切换
- [ ] 调整流量分配：100% Workers
- [ ] 运行 24 小时，密切监控
- [ ] 验证所有功能正常
- [ ] 检查错误率和响应时间是否稳定
- [ ] 收集用户反馈

#### Render 下线
- [ ] 在 100% 流量运行 1 周后，确认稳定
- [ ] 备份 Render 数据库（最后一次）
- [ ] 停止 Render 后端服务（不删除）
- [ ] 保留 Render 服务 2 周（以防需要回滚）
- [ ] 2 周后完全删除 Render 服务

#### 发布后验证
- [ ] 运行完整的冒烟测试
- [ ] 验证所有 API 端点正常
- [ ] 检查数据库数据一致性
- [ ] 验证定时任务正常运行
- [ ] 记录最终发布报告

---

## 并行任务（可在 Week 1-3 完成）

### 前端监控/安全系统修复

#### 监控系统初始化错误修复
- [x] 定位前端监控系统初始化错误（`src/services/userAnalytics.ts`）
  - **根本原因**：JavaScript `this` 绑定问题，解构导出丢失实例上下文
  - **错误源头**：`userAnalytics.ts:538-549` 使用 `export const { startTracking, ... } = userAnalytics`
  - **调用链路**：`monitoring.ts:8` 导入 → 解构导出 → `this` 为 `undefined`
- [x] 修复方案：改用包装函数导出
  ```typescript
  // 使用箭头函数包装保持 this 上下文
  export const startTracking = (userId?: string) => userAnalytics.startTracking(userId)
  export const trackEvent = (eventName, eventType, properties?) =>
    userAnalytics.trackEvent(eventName, eventType, properties)
  // ... 其他 8 个函数同理
  ```
- [x] 实现错误边界（防御性编程，添加类型检查）
- [x] 测试修复后的初始化流程（TypeScript 类型检查通过、构建成功）
- [x] Codex 代码审查通过
- [x] Git 提交：`182da5d` (2025-11-09)

#### 安全系统初始化错误修复
- [x] 定位依赖安全系统初始化错误（`src/services/dependencySecurity.ts`）
  - **根本原因**：上游传递 `undefined` + 下游盲目合并覆盖默认值
  - **错误源头**：`dependencySecurity.ts:294-320` 的 `checkLicenseCompliance()`
  - **调用链路**：`security.ts:112-116` 传递 undefined → `dependencySecurity.ts:146` 合并配置 → 默认数组被覆盖
- [x] 修复方案：双管齐下（上游过滤 + 下游防御）
  - **修复 2.1**：`security.ts` 过滤 undefined 配置值
    ```typescript
    ...(this.config.dependencies.allowedLicenses && {
      allowedLicenses: this.config.dependencies.allowedLicenses
    })
    ```
  - **修复 2.2**：`dependencySecurity.ts` 添加安全读取器
    - 新增 `resolveLicenseList()` 辅助方法
    - 重构 `checkLicenseCompliance()` 使用安全读取器
    - 更新 `generateSecurityReport()` 使用安全读取器
    - 添加 try-catch 错误边界
- [x] 添加空值检查和默认值（resolveLicenseList 提供降级逻辑）
- [x] 实现降级处理（使用 DEFAULT_CONFIG 默认值）
- [x] 测试修复后的初始化流程（TypeScript 类型检查通过、构建成功）
- [x] Codex 代码审查通过
- [x] Git 提交：`182da5d` (2025-11-09)
- [ ] 部署后验证浏览器控制台无错误（待生产环境验证）

#### CSP 响应头配置
- [ ] 在 Cloudflare Pages 中配置 `_headers` 文件：
  ```
  /*
    Content-Security-Policy: default-src 'self'; script-src 'self'; connect-src 'self' https://web3search-api.workers.dev; ...
  ```
- [ ] 测试 CSP 策略（检查浏览器开发者工具）
- [ ] 配置 CSP 违规报告端点
- [ ] 部署并验证

### Vercel 部署移除

#### Vercel 项目删除
- [ ] 登录 Vercel Dashboard
- [ ] 找到 Web3search 前端项目
- [ ] 删除 Vercel 项目（Settings → Advanced → Delete Project）
- [ ] 确认删除
- **注**：Vercel 项目已失效（404），可选择性删除

#### Vercel 配置文件清理
- [x] 检查 `vercel.json` 文件（不存在）
- [x] 检查 `.vercelignore` 文件（不存在）
- [x] 搜索代码中的 Vercel 相关引用
- [x] 移除代码中的 Vercel 特定配置
  - ✅ `package.json`: 删除 vercel 和 vercel:prod 脚本

#### CI/CD 清理
- [x] 检查 `.github/workflows/` 中的 Vercel 部署步骤（无 Vercel workflow）
- [x] 确认无需移除 Vercel 部署 workflow
- [ ] 移除 Vercel 相关的 GitHub Secrets（VERCEL_TOKEN 等）- 可选

#### 文档更新
- [x] 更新 README.md，移除 Vercel 部署说明
  - ✅ 将 "Vercel部署" 改为 "Cloudflare Pages 部署"
  - ✅ 更新 CORS 配置示例
- [x] 完全重写 DEPLOYMENT_GUIDE.md
  - ✅ 从 Vercel CLI 指南改为 Cloudflare Pages 指南
  - ✅ 添加自动部署配置说明
  - ✅ 添加环境变量配置指南
  - ✅ 添加故障排除章节
- [x] 更新 CLOUDFLARE_PAGES_CONFIG.md
  - ✅ CORS 配置中移除 Vercel URL
  - ✅ 仅保留 Cloudflare Pages URL
- [x] 提交文档更改
  - ✅ Git 提交：`ecf8b25` (2025-11-09)

### 测试基础设施改进

#### 烟雾测试脚本更新
- [ ] 定位烟雾测试脚本（`scripts/smoke-test.js` 或类似）
- [ ] 更新测试选择器以匹配当前前端组件
- [ ] 更新 API 端点 URL（指向新 Workers API）
- [ ] 运行烟雾测试验证：`npm run test:smoke`
- [ ] 修复失败的测试

#### 前端单元测试修复
- [ ] 修复 BroadcastChannel polyfill 问题：
  - 安装 polyfill：`npm install broadcast-channel`
  - 在测试设置中导入 polyfill
- [ ] 修复组件超时问题：
  - 增加测试超时时间
  - 使用 `waitFor` 等待异步操作
- [ ] 运行单元测试：`npm test`
- [ ] 目标：测试通过率 > 95%

#### E2E 测试生产环境配置
- [ ] 创建生产环境测试配置文件（`playwright.config.production.ts`）
- [ ] 配置生产环境 URL：
  ```typescript
  use: {
    baseURL: 'https://web3search.pages.dev',
  }
  ```
- [ ] 创建生产测试脚本：`npm run test:e2e:production`
- [ ] 运行生产环境测试验证
- [ ] 配置 CI/CD 自动运行生产测试

#### 测试数据管理
- [ ] 创建测试数据生成脚本（种子数据）
- [ ] 为测试创建独立的 Supabase 项目/schema
- [ ] 配置测试前自动清理和重置数据
- [ ] 实现测试数据隔离（避免污染生产数据）

---

## 最终验证

### 系统功能验证
- [ ] 验证所有 API 端点正常工作（健康检查、搜索、聊天、报告）
- [ ] 验证前端可以正常访问和使用
- [ ] 验证数据库数据完整性
- [ ] 验证缓存系统正常工作
- [ ] 验证定时任务正常执行

### 性能验证
- [ ] 验证响应时间达标：
  - 健康检查 < 100ms
  - 搜索 API < 500ms
  - 聊天 API < 2s
- [ ] 验证缓存命中率 > 80%
- [ ] 验证并发处理能力（100+ 并发请求）

### 安全验证
- [ ] 验证 CSP 配置生效
- [ ] 验证环境变量安全（无敏感信息泄露）
- [ ] 验证 API 速率限制生效
- [ ] 验证认证和授权正常（如果实现）

### 测试验证
- [ ] 前端单元测试通过率 > 95%
- [ ] E2E 测试通过率 100%
- [ ] 烟雾测试通过率 100%
- [ ] 负载测试通过

### 文档验证
- [ ] 更新架构文档（新的 Cloudflare Workers + Supabase 架构）
- [ ] 更新部署文档
- [ ] 更新 API 文档（如果有变化）
- [ ] 记录迁移过程和经验教训

### 最终报告
- [ ] 编写迁移完成报告
- [ ] 记录性能对比（迁移前 vs 迁移后）
- [ ] 记录成本对比（Render vs Cloudflare Workers）
- [ ] 总结遇到的问题和解决方案
- [ ] 提出后续优化建议
