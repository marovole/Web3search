# Security Specification Delta

## MODIFIED Requirements

### Requirement: 安全系统初始化健壮性

安全系统（CSP、XSS 防护）MUST 包含完善的空值检查和错误处理，避免初始化失败。

#### Scenario: 安全系统初始化失败时降级
**Given** 安全系统正在初始化
**When** 初始化过程中发生错误（如依赖未加载、配置缺失）
**Then** 捕获错误并记录到日志
**And** 应用仍然正常启动（降级为基础安全级别）
**And** 显示警告提示："部分安全功能不可用"

#### Scenario: CSP 管理器空值检查
**Given** CSP 管理器初始化
**When** 访问配置对象或依赖项
**Then** 在访问前检查是否为 null 或 undefined
**And** 如果依赖缺失，使用默认配置继续初始化
**And** 记录警告日志说明使用默认配置

#### Scenario: XSS 防护管理器空值检查
**Given** XSS 防护管理器初始化
**When** 检查输入数据或配置
**Then** 在访问前检查是否为 null 或 undefined
**And** 对于缺失的配置，使用安全的默认值
**And** 不因配置缺失而导致初始化失败

### Requirement: CSP 配置优化

Content Security Policy MUST 通过 HTTP 响应头配置（Cloudflare Pages），保护前端免受 XSS 攻击。

#### Scenario: 使用 HTTP 响应头配置 CSP
**Given** Cloudflare Pages 部署配置
**When** 配置响应头（通过 `_headers` 文件）
**Then** 包含 Content-Security-Policy 响应头
**And** CSP 指令包含：
 - default-src 'self'
 - script-src 'self'
 - style-src 'self' 'unsafe-inline'
 - img-src 'self' data: https:
 - connect-src 'self' https://web3search-api.workers.dev https://*.supabase.co
 - font-src 'self'
 - frame-ancestors 'none'
**And** 不使用 meta 标签配置 CSP

#### Scenario: CSP 违规报告配置
**Given** CSP 响应头配置
**When** 设置报告 URI
**Then** 包含 report-uri 指令指向报告收集端点（Workers 端点）
**And** 或使用 report-to 指令配置报告组
**And** CSP 违规事件发送到监控系统（Sentry 或自定义端点）

### Requirement: 环境变量安全验证

应用启动时 MUST 验证敏感环境变量未意外暴露到客户端。

#### Scenario: 检查客户端不包含服务器密钥
**Given** 前端构建完成
**When** 检查构建产物
**Then** 构建产物不包含以下敏感变量：
 - SUPABASE_URL（公开，但不应包含 SERVICE_ROLE_KEY）
 - SUPABASE_SERVICE_ROLE_KEY
 - OPENROUTER_API_KEY
 - 任何包含 "SECRET" 或 "PASSWORD" 的变量
**And** 如果发现敏感变量，构建失败并显示安全警告

#### Scenario: 仅暴露 VITE_ 前缀的环境变量
**Given** 前端构建过程
**When** 注入环境变量到构建产物
**Then** 仅包含以 VITE_ 开头的环境变量
**And** 其他环境变量保留在服务器端（Workers Secrets）
**And** 构建工具配置明确定义允许暴露的变量

## ADDED Requirements

### Requirement: Cloudflare Workers 安全配置

Workers MUST 正确配置安全措施，保护 API 免受攻击。

#### Scenario: 速率限制保护（使用 KV 免费层）
**Given** Workers 接收 API 请求
**When** 检查请求频率（使用 Cloudflare KV）
**Then** 实施以下速率限制：
 - 每个 IP：20 请求/分钟
 - 聊天 API：10 请求/小时（未认证用户）
**And** 使用 KV 键：`rate_limit:{ip}:{hour}` 或 `rate_limit:{ip}:{minute}`
**And** TTL 自动过期（1 小时或 1 分钟）
**And** 超过限制返回 429 Too Many Requests
**And** 响应头包含 Retry-After
**And** 注意：KV 最终一致性可能导致边界情况误差（可接受的安全折衷）

#### Scenario: 输入验证和清理
**Given** Workers 接收用户输入（查询、聊天消息等）
**When** 处理请求前
**Then** 验证输入：
 - 检查长度限制（查询 < 10000 字符）
 - 过滤危险字符（SQL 注入、NoSQL 注入）
 - 验证数据类型（UUID、枚举值等）
**And** 如果验证失败，返回 400 Bad Request 并记录尝试

#### Scenario: 防止 SQL 注入
**Given** Workers 查询 Supabase 数据库
**When** 构建 SQL 查询
**Then** 使用参数化查询（Supabase 客户端自动参数化）
**And** 不直接拼接用户输入到 SQL 语句
**And** 使用 Supabase 的安全查询构建器

#### Scenario: API Key 安全存储
**Given** Workers 需要访问 OpenRouter API
**When** 配置 API Key
**Then** API Key 存储在 Cloudflare Secrets（不在代码或 wrangler.toml 中）
**And** 通过 `env.OPENROUTER_API_KEY` 访问
**And** 日志不记录完整的 API Key（仅记录前 4 位）

#### Scenario: CORS 安全配置
**Given** Workers 处理跨域请求
**When** 配置 CORS 策略
**Then** 仅允许来自以下源的请求：
 - https://web3search.pages.dev（生产）
 - https://*.web3search.pages.dev（预览）
**And** 拒绝其他源的请求（返回 403 Forbidden）
**And** 不使用 `Access-Control-Allow-Origin: *`

### Requirement: Supabase Row Level Security (RLS)

Supabase 数据库 MUST 启用 RLS 以保护用户数据（如果实现用户系统）。

#### Scenario: 启用 RLS for 敏感表
**Given** Supabase 包含用户数据表（messages、reports 等）
**When** 配置表安全策略
**Then** 为敏感表启用 RLS：
 - `ALTER TABLE messages ENABLE ROW LEVEL SECURITY;`
 - `ALTER TABLE reports ENABLE ROW LEVEL SECURITY;`
**And** 未启用 RLS 的表拒绝所有访问（默认拒绝）

#### Scenario: 配置 RLS 策略
**Given** RLS 已启用
**When** 创建安全策略
**Then** 配置以下策略：
 - 用户只能读取自己的 messages：
   ```sql
   CREATE POLICY "Users can view own messages"
   ON messages FOR SELECT
   USING (user_id = auth.uid());
   ```
 - 用户只能插入自己的 messages
 - 服务端（使用 SERVICE_ROLE_KEY）可访问所有数据
**And** 测试策略：尝试未授权访问返回空结果

#### Scenario: 使用 Service Role Key 绕过 RLS
**Given** Workers 需要管理员级别访问（如清理任务）
**When** 创建 Supabase 客户端
**Then** 使用 SERVICE_ROLE_KEY 创建客户端：
 - `createClient(url, serviceRoleKey, { auth: { persistSession: false } })`
**And** 仅在后台任务中使用（不暴露给前端）
**And** 记录所有 SERVICE_ROLE 操作到审计日志

### Requirement: 安全日志和审计

Workers MUST 记录安全相关事件，便于审计和事件响应。

#### Scenario: 记录认证失败
**Given** 用户尝试访问受保护的 API（如果实现认证）
**When** 认证失败
**Then** 记录以下信息：
 - 时间戳
 - 客户端 IP
 - 尝试访问的端点
 - 失败原因（token 无效、已过期等）
**And** 如果同一 IP 短时间内多次失败（> 5 次/分钟），标记为可疑活动

#### Scenario: 记录速率限制触发
**Given** 请求触发速率限制
**When** 返回 429 错误
**Then** 记录：
 - 时间戳
 - 客户端 IP
 - 请求端点
 - 当前请求频率
**And** 如果同一 IP 持续触发（> 10 次），考虑临时封禁

#### Scenario: 记录敏感操作
**Given** 执行敏感操作（数据删除、权限变更等）
**When** 操作完成
**Then** 记录到审计日志：
 - 操作类型
 - 操作者（用户 ID 或系统）
 - 受影响的资源
 - 操作时间
 - 操作结果（成功/失败）

## REMOVED Requirements

无移除需求（所有安全相关需求保留或增强）
