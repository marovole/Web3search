# API Spec Delta

## MODIFIED Requirements

### Requirement: TypeScript类型安全
Workers API **SHALL** 确保所有TypeScript代码通过严格类型检查，无编译错误，以保障代码质量和运行时安全。

#### Scenario: 环境变量类型完整性
- **WHEN** 代码引用环境变量（如 SENTRY_DSN, OPENROUTER_CIRCUIT_STATE）
- **THEN** `Env` 接口必须声明所有实际使用的绑定
- **AND** 可选绑定使用 `?:` 标记（如 `SENTRY_DSN?: string`）
- **AND** 必选绑定不使用 `?:` 标记（如 `CACHE: KVNamespace`）
- **AND** 包含以下字段:
  - `SUPABASE_URL: string`
  - `SUPABASE_ANON_KEY: string`
  - `OPENROUTER_API_KEY: string`
  - `CACHE: KVNamespace`
  - `OPENROUTER_CIRCUIT_STATE?: KVNamespace`
  - `SENTRY_DSN?: string`
  - `CLIENT_SESSION_ID?: string`
  - `BRAVE_SEARCH_API_KEY?: string`
  - `TAVILY_API_KEY?: string`
  - `SERPER_API_KEY?: string`

#### Scenario: KV Namespace 安全访问
- **WHEN** 代码访问 `env.CACHE` 或其他可选 KV namespace
- **THEN** 必须先检查是否 undefined
- **AND** 未绑定时记录警告日志并优雅降级
- **AND** Cron handlers 在 CACHE 未绑定时返回 503 状态码
- **EXAMPLE**:
  ```typescript
  if (!env.CACHE) {
    console.warn('[cron] CACHE not bound, skipping health check')
    return new Response('CACHE unavailable', { status: 503 })
  }
  await env.CACHE.put(key, value)
  ```

#### Scenario: OpenRouter Payload 类型匹配
- **WHEN** 调用 OpenRouter API (Deep Research, Chat)
- **THEN** payload 的 `messages` 字段必须使用 `ChatCompletionMessage[]` 类型
- **AND** `role` 字段必须使用 `ChatRole` 类型（不能是 `string`）
- **AND** 类型断言明确（如 `role: 'system' as ChatRole`）
- **EXAMPLE**:
  ```typescript
  const messages: ChatCompletionMessage[] = [
    { role: 'system' as ChatRole, content: systemPrompt },
    { role: 'user' as ChatRole, content: query }
  ]
  const payload: OpenRouterPayload = { model, messages, ...options }
  ```

#### Scenario: SSE 事件接口完整性
- **WHEN** 定义 SSE 事件接口（ResearchProgressEvent, ResearchStepEvent）
- **THEN** 所有继承 `ResearchSSEvent` 的接口 `data` 字段必须包含 `timestamp: string`
- **AND** `ResearchProgress` 和 `ResearchStepData` 接口添加 `timestamp` 字段
- **EXAMPLE**:
  ```typescript
  export interface ResearchProgress {
    task_id: string
    step: string
    progress: number
    timestamp: string  // 新增
  }
  ```

#### Scenario: Request Body 类型扩展
- **WHEN** 定义 API request body 接口（如 ChatRequestBody）
- **THEN** 接口必须包含所有实际使用的可选字段
- **AND** `ChatRequestBody` 添加 `temperature?: number` 和 `max_tokens?: number`
- **EXAMPLE**:
  ```typescript
  export interface ChatRequestBody {
    messages: ChatMessage[]
    stream?: boolean
    temperature?: number    // 新增
    max_tokens?: number     // 新增
  }
  ```

#### Scenario: Resilience 配置类型完整性
- **WHEN** 定义 `RetryConfig` 接口
- **THEN** 接口必须包含 `timeoutMs: number` 字段
- **AND** 所有使用 `withRetry` 的地方传递完整配置
- **EXAMPLE**:
  ```typescript
  export interface RetryConfig {
    maxAttempts: number
    baseDelayMs: number
    maxDelayMs: number
    timeoutMs: number  // 新增
  }
  ```

#### Scenario: Telemetry 返回类型正确性
- **WHEN** `buildTelemetryData` 函数声明为 async
- **THEN** 返回类型必须是 `Promise<TelemetryData>`（不是 `TelemetryData`）
- **EXAMPLE**:
  ```typescript
  async function buildTelemetryData(...): Promise<TelemetryData> {
    // ...
  }
  ```

## ADDED Requirements

### Requirement: Deep Research 路由注册
Workers API **SHALL** 确保所有 Deep Research 端点正确注册并可访问，支持 SSE 流式研究响应。

#### Scenario: SSE 端点路由注册
- **WHEN** 注册 Deep Research 路由
- **THEN** `/api/v1/deep-research/stream` 端点必须正确注册到 Hono app
- **AND** 路由 handler 返回 SSE 响应（Content-Type: text/event-stream）
- **AND** 中间件不拦截该路由
- **AND** 测试验证端点返回 200 状态码（不是 404）

#### Scenario: 路由测试覆盖
- **WHEN** 测试 Deep Research 功能
- **THEN** 必须包含以下测试用例:
  - 有效查询参数返回 200
  - 缺少查询参数返回 400
  - 查询超长（> 2000字符）返回 414
  - Content-Type 为 text/event-stream
- **AND** 所有测试通过（不返回 404）

### Requirement: API 性能基准
Workers API **SHALL** 定义并监控性能 SLO（Service Level Objectives），确保响应时间符合用户体验标准。

#### Scenario: 健康检查性能 SLO
- **WHEN** 客户端请求 `/api/v1/health`
- **THEN** P95 响应时间 < 300ms
- **AND** P99 响应时间 < 500ms
- **AND** 成功率 > 99.9%
- **AND** 性能指标记录到监控系统

#### Scenario: 搜索 API 性能 SLO
- **WHEN** 客户端请求搜索相关端点（autocomplete, search）
- **THEN** P95 响应时间 < 500ms
- **AND** P99 响应时间 < 1000ms
- **AND** 缓存命中时 < 100ms

#### Scenario: Deep Research 首字节时间
- **WHEN** 客户端请求 Deep Research SSE 流
- **THEN** 首字节响应时间（TTFB）< 1000ms
- **AND** SSE 事件流式发送，无长时间阻塞
- **AND** 超时设置合理（> 30s）

### Requirement: 测试覆盖率标准
Workers API **SHALL** 保持高测试覆盖率，确保代码质量和回归预防。

#### Scenario: 单元测试覆盖率
- **WHEN** 运行 `npm test -- --coverage`
- **THEN** 语句覆盖率（Statements）> 80%
- **AND** 分支覆盖率（Branches）> 75%
- **AND** 函数覆盖率（Functions）> 80%
- **AND** 行覆盖率（Lines）> 80%

#### Scenario: 关键路径端到端测试
- **WHEN** 测试核心功能
- **THEN** 必须包含以下端到端测试:
  - Deep Research 完整流程（plan → search → analyze → report）
  - Quick Chat 对话流程
  - 搜索提供商 failover 流程
  - 错误处理和重试机制
- **AND** 所有端到端测试在 CI 环境通过

#### Scenario: 测试失败零容忍
- **WHEN** 提交代码到主分支
- **THEN** 所有测试必须通过（0 failed）
- **AND** CI pipeline 在测试失败时阻止合并
- **AND** 修复失败测试的 PR 优先级最高
