# API Specification Delta

## MODIFIED Requirements

### Requirement: API 健康检查增强

健康检查端点 MUST 验证所有关键依赖的连接状态，部署在 Cloudflare Workers 上。

#### Scenario: 健康检查包含 Supabase 状态
**Given** Cloudflare Workers 已部署
**When** 客户端请求 `GET /api/v1/health`
**Then** 响应包含 Supabase 数据库连接状态
**And** 如果数据库连接失败，返回 503 状态码
**And** 响应体包含 `{"status": "degraded", "database": "disconnected", "timestamp": "<ISO8601>"}`

#### Scenario: 健康检查包含缓存状态
**Given** Workers 已启用 KV 缓存（免费层）
**When** 客户端请求 `GET /api/v1/health`
**Then** 响应包含缓存系统状态
**And** 如果缓存不可用但数据库正常，返回 200 状态码（降级运行）
**And** 响应体包含 `{"status": "degraded", "cache": "disconnected", "cache_enabled": false}`

#### Scenario: 健康检查响应时间要求
**Given** 所有依赖正常连接
**When** 客户端请求 `GET /api/v1/health`
**Then** 响应时间 < 500ms（Workers 边缘节点）
**And** 返回 200 状态码
**And** 响应体包含 `{"status": "healthy", "database": "connected", "cache": "connected", "region": "<cloudflare-region>", "version": "1.0.0"}`

### Requirement: API 错误响应标准化

所有 API 端点 MUST 返回标准化的错误响应格式，使用 Hono 框架的错误处理。

#### Scenario: 500 错误包含追踪信息
**Given** API 端点发生内部错误
**When** 客户端请求任何 API 端点
**Then** 返回 500 状态码
**And** 响应体包含 `{"error": {"code": "INTERNAL_ERROR", "message": "<user-friendly-message>", "trace_id": "<uuid>", "status": 500}}`
**And** 不暴露敏感的堆栈跟踪或内部实现细节
**And** 堆栈跟踪记录到 Workers 日志（不返回给客户端）

#### Scenario: 404 错误返回友好消息
**Given** API 端点不存在
**When** 客户端请求不存在的端点（如 `/api/v1/nonexistent`）
**Then** 返回 404 状态码
**And** 响应体包含 `{"error": {"code": "NOT_FOUND", "message": "Endpoint not found", "status": 404}}`
**And** 日志记录包含请求路径以便调试

### Requirement: API 端点日志记录

所有 API 端点 MUST 记录请求和响应的关键信息到 Cloudflare Workers 日志系统。

#### Scenario: 请求日志包含关键信息
**Given** 客户端请求任何 API 端点
**When** 请求到达 Workers
**Then** 记录以下信息到控制台：
 - 请求时间戳
 - 请求方法和路径
 - 客户端 IP（从 `request.headers.get('CF-Connecting-IP')`）
 - 请求 ID（生成 UUID）
 - Cloudflare 边缘节点位置（从 `request.cf.colo`）
**And** 日志级别为 INFO

#### Scenario: 错误日志包含详细信息
**Given** API 端点处理请求时发生错误
**When** 捕获异常
**Then** 记录以下信息到错误日志：
 - 错误时间戳
 - 请求 ID
 - 错误类型和消息
 - 完整堆栈跟踪
 - 请求参数（脱敏后）
**And** 日志级别为 ERROR
**And** 如果配置了 Sentry，发送错误到 Sentry for Workers

### Requirement: API 环境变量验证

API 服务启动时 MUST 验证所有必需的环境变量（Cloudflare Workers Secrets）。

#### Scenario: Workers 启动时验证环境变量
**Given** Workers 正在初始化
**When** 处理第一个请求
**Then** 验证以下变量存在且非空：
 - SUPABASE_URL
 - SUPABASE_ANON_KEY
 - OPENROUTER_API_KEY
**And** 如果任何必需变量缺失，返回 500 错误
**And** 记录缺失的变量名称（不记录值）

#### Scenario: 验证 Supabase URL 格式
**Given** SUPABASE_URL 环境变量已设置
**When** 验证环境变量
**Then** 确认格式为 `https://<project-id>.supabase.co`
**And** 如果格式错误，记录警告并尝试连接
**And** 如果连接失败，返回 500 错误

## ADDED Requirements

### Requirement: OpenRouter API 集成

API MUST 正确集成 OpenRouter，支持流式和非流式 AI 响应。

#### Scenario: 调用 OpenRouter API
**Given** Workers 已配置 OPENROUTER_API_KEY
**When** 请求 OpenRouter API（https://openrouter.ai/api/v1/chat/completions）
**Then** 使用正确的请求头：
 - Authorization: Bearer <OPENROUTER_API_KEY>
 - HTTP-Referer: https://web3search.pages.dev
 - X-Title: Web3search
**And** 请求体包含：
 - model: "anthropic/claude-3.5-sonnet"
 - messages: [{role: "user", content: "..."}]
 - stream: true/false
**And** 超时时间设置为 30 秒

#### Scenario: 处理 OpenRouter 流式响应
**Given** 请求 OpenRouter API 并设置 stream=true
**When** OpenRouter 返回 Server-Sent Events (SSE) 流
**Then** Workers 正确解析 SSE 格式：
 - 每行格式为 `data: {json}`
 - 最后一行为 `data: [DONE]`
**And** 将 SSE 流转发给前端
**And** 处理流中断和错误（超时、连接断开）

#### Scenario: OpenRouter 错误处理
**Given** 调用 OpenRouter API
**When** API 返回错误（401、429、500 等）
**Then** 解析错误响应：
 - 401: API Key 无效，返回 500 并记录错误
 - 429: 超过速率限制，返回 429 并建议稍后重试
 - 500: OpenRouter 服务器错误，重试最多 3 次（指数退避）
**And** 记录错误到日志
**And** 返回用户友好的错误消息

### Requirement: 聊天 API 实现

聊天 API (`/api/v1/chat/quick-chat`) MUST 正确处理用户查询并返回 AI 响应。

#### Scenario: 接收聊天请求
**Given** 用户发起聊天请求
**When** POST 到 `/api/v1/chat/quick-chat`，请求体：
```json
{
  "query": "What is Bitcoin?",
  "conversation_id": "uuid-123",
  "model": "anthropic/claude-3.5-sonnet",
  "stream": true
}
```
**Then** 验证请求参数：
 - query: 非空，长度 1-10000 字符
 - conversation_id: 可选，UUID 格式
 - model: 可选，默认为 "anthropic/claude-3.5-sonnet"
 - stream: 可选，默认为 true
**And** 如果验证失败，返回 400 错误

#### Scenario: 检索对话历史
**Given** 请求包含 conversation_id
**When** 查询对话历史
**Then** 优先从 Supabase 读取（保证一致性）：
 - 查询 messages 表：WHERE conversation_id = <id>
 - ORDER BY created_at DESC
 - LIMIT 10
**And** 可选：从 KV 缓存读取辅助（热数据，可能有延迟）
**And** 构建上下文：将历史消息添加到 OpenRouter 请求

#### Scenario: 调用 OpenRouter 并返回响应
**Given** 请求参数已验证，对话历史已检索
**When** 调用 OpenRouter API
**Then** 构建完整的消息数组：
 - 系统提示词（定义 AI 角色）
 - 对话历史（最近 10 条）
 - 当前用户查询
**And** 调用 OpenRouter 并获取响应
**And** 如果 stream=true，返回 SSE 流
**And** 如果 stream=false，返回完整 JSON 响应

#### Scenario: 保存对话到数据库
**Given** AI 响应生成完成
**When** 保存对话
**Then** 插入用户消息到 Supabase messages 表：
 - conversation_id, role="user", content=<query>, created_at
**And** 插入 AI 响应到 messages 表：
 - conversation_id, role="assistant", content=<response>, created_at
**And** 可选：更新 KV 缓存（异步，不阻塞响应）
**And** 如果保存失败，记录错误但不影响响应返回

#### Scenario: 速率限制保护
**Given** 用户频繁发起聊天请求
**When** 检查速率限制（使用 KV 免费层）
**Then** 限制规则：
 - 免费用户：10 请求/小时
 - 每个 IP：20 请求/小时
**And** 使用 KV 键：`rate_limit:{ip}:{hour}` 存储请求计数
**And** TTL 设置为 1 小时（自动过期）
**And** 超过限制返回 429 错误
**And** 响应头包含：X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset
**And** 错误消息提示用户稍后重试
**And** 注意：KV 最终一致性可能导致边界情况误差（可接受）

### Requirement: 搜索自动完成 API

搜索自动完成 API (`/api/v1/search/autocomplete`) MUST 快速返回匹配的搜索建议。

#### Scenario: 接收自动完成请求
**Given** 用户输入搜索关键词
**When** GET `/api/v1/search/autocomplete?q=bitcoin`
**Then** 验证参数：
 - q: 非空，长度 1-100 字符
 - limit: 可选，默认 10，最大 50
**And** 如果验证失败，返回 400 错误

#### Scenario: 查询匹配关键词
**Given** 请求参数已验证
**When** 查询 Supabase 数据库
**Then** 执行查询：
```sql
SELECT keyword, search_count, category
FROM search_keywords
WHERE keyword ILIKE '%<query>%'
ORDER BY search_count DESC, keyword ASC
LIMIT <limit>
```
**And** 查询超时时间设置为 2 秒
**And** 如果超时，返回空数组（不报错）

#### Scenario: 缓存热门查询
**Given** 查询结果已返回
**When** 检查是否为热门查询（search_count > 100）
**Then** 将结果缓存到 Cloudflare KV：
 - key: `autocomplete:<query>`
 - value: JSON.stringify(results)
 - TTL: 1 小时
**And** 下次相同查询优先从缓存读取
**And** 缓存命中时响应时间 < 50ms

#### Scenario: 返回自动完成结果
**Given** 查询完成（从数据库或缓存）
**When** 返回响应
**Then** 响应格式：
```json
{
  "query": "bitcoin",
  "results": [
    {"keyword": "Bitcoin price", "category": "cryptocurrency"},
    {"keyword": "Bitcoin mining", "category": "technology"}
  ],
  "count": 2,
  "cached": true/false
}
```
**And** 状态码 200
**And** 响应时间 < 500ms

### Requirement: 报告生成 API（免费架构）

报告生成 API MUST 支持生成长篇报告。推荐方案 A（流式）或方案 B（Edge Functions）。

#### Scenario: 方案 A（推荐）- 流式生成报告
**Given** 用户请求生成报告
**When** POST `/api/v1/reports/stream`，请求体：
```json
{
  "topic": "Decentralized Finance (DeFi)",
  "sections": ["overview", "protocols", "risks"],
  "model": "anthropic/claude-3.5-sonnet"
}
```
**Then** Workers 立即开始流式生成：
 1. 验证请求参数（topic, sections）
 2. 为每个 section 调用 OpenRouter（流式）
 3. 实时返回 SSE 流给前端
 4. 前端逐段显示生成的内容
**And** 响应类型：text/event-stream
**And** 用户体验更好（无需等待和轮询）
**And** 无需后台任务队列，完全免费

#### Scenario: 方案 B - 使用 Supabase Edge Functions
**Given** 用户请求生成报告
**When** POST `/api/v1/reports/generate`，请求体：
```json
{
  "topic": "DeFi",
  "sections": ["overview", "protocols", "risks"]
}
```
**Then** Workers 执行：
 1. 创建报告任务记录（Supabase reports 表）
 2. 异步调用 Edge Function（不等待响应）：
   ```typescript
   fetch('https://<project>.supabase.co/functions/v1/generate-report', {
     method: 'POST',
     body: JSON.stringify({ report_id, topic, sections })
   }).catch(err => console.error(err));
   ```
 3. 返回 202 Accepted 和报告 ID
**And** Edge Function 后台处理报告生成
**And** 前端轮询报告状态或使用 WebSocket

#### Scenario: 查询报告状态（方案 B）
**Given** 报告任务已创建（方案 B）
**When** GET `/api/v1/reports/<report_id>`
**Then** 查询 Supabase reports 表
**And** 返回报告状态：
```json
{
  "report_id": "<uuid>",
  "topic": "DeFi",
  "status": "processing" | "completed" | "failed",
  "progress": 65,
  "content": "<partial-or-full-content>",
  "created_at": "<ISO8601>",
  "completed_at": "<ISO8601>"
}
```
**And** 如果状态为 "completed"，包含完整内容
**And** 如果状态为 "failed"，包含错误消息

### Requirement: API CORS 配置

API MUST 正确配置 CORS 以支持跨域请求。

#### Scenario: 预检请求处理
**Given** 浏览器发送 OPTIONS 预检请求
**When** Workers 接收到 OPTIONS 请求
**Then** 返回以下响应头：
 - Access-Control-Allow-Origin: https://web3search.pages.dev
 - Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
 - Access-Control-Allow-Headers: Content-Type, Authorization
 - Access-Control-Max-Age: 86400
**And** 返回 204 No Content

#### Scenario: 实际请求 CORS 头
**Given** 浏览器发送实际 API 请求
**When** Workers 处理请求
**Then** 响应包含以下头：
 - Access-Control-Allow-Origin: https://web3search.pages.dev
 - Access-Control-Allow-Credentials: true
**And** 如果请求来自其他域，拒绝访问

## REMOVED Requirements

### ~~Requirement: API 启动预热机制~~
**移除原因**: Cloudflare Workers 无冷启动，不需要预热连接池

### ~~Requirement: 启动时建立数据库连接池~~
**移除原因**: Workers 使用 Supabase 客户端，每个请求独立连接，不需要连接池

### ~~Requirement: 启动时建立 Redis 连接~~
**移除原因**: 使用 Cloudflare KV 替代 Redis，不需要预连接
