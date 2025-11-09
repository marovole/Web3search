# Performance Specification Delta

## MODIFIED Requirements

### Requirement: 监控系统初始化健壮性

性能监控系统 MUST 包含完善的错误处理，确保监控失败不影响应用功能。

#### Scenario: 监控系统初始化失败时降级
**Given** 性能监控系统正在初始化
**When** 初始化过程中发生错误（如 API 不可用、配置错误）
**Then** 捕获错误并记录到控制台
**And** 应用继续正常运行（无监控数据收集）
**And** 不显示错误提示给用户（监控失败对用户透明）

#### Scenario: 监控 API 空值检查
**Given** 监控系统尝试记录性能指标
**When** 访问性能 API 或配置对象
**Then** 在访问前检查是否为 null 或 undefined
**And** 如果 API 不可用，跳过该指标记录
**And** 不因单个指标失败而停止整个监控系统

#### Scenario: 优雅降级到基础监控
**Given** 高级监控功能不可用（如 Sentry、自定义追踪）
**When** 监控系统初始化
**Then** 降级到浏览器原生 Performance API
**And** 仍然收集基础性能指标（页面加载时间、资源加载）
**And** 记录警告说明使用降级模式

### Requirement: 前端性能监控配置

前端 MUST 配置性能监控，收集关键性能指标并发送到监控系统。

#### Scenario: 收集核心 Web Vitals
**Given** 前端页面加载完成
**When** 性能监控系统初始化
**Then** 收集以下 Core Web Vitals：
 - LCP (Largest Contentful Paint) < 2.5s
 - FID (First Input Delay) < 100ms
 - CLS (Cumulative Layout Shift) < 0.1
**And** 如果启用监控 API，发送数据到监控后端
**And** 如果监控 API 不可用，仅本地记录

#### Scenario: 监控 API 响应时间
**Given** 前端发起 API 请求（调用 Cloudflare Workers API）
**When** 请求完成或失败
**Then** 记录以下信息：
 - 请求 URL 和方法
 - 响应时间（毫秒）
 - 响应状态码
 - 是否成功
 - Cloudflare 边缘节点位置（从响应头）
**And** 如果响应时间 > 3 秒，记录为慢查询
**And** 聚合数据定期发送到监控系统

## ADDED Requirements

### Requirement: Cloudflare Workers Analytics 配置

Workers MUST 启用 Analytics 并配置关键性能指标追踪。

#### Scenario: 启用 Workers Analytics
**Given** Workers 已部署到生产环境
**When** 在 Cloudflare Dashboard 启用 Workers Analytics
**Then** Analytics 自动收集以下指标：
 - 请求总数（按时间段）
 - 响应状态码分布（2xx, 4xx, 5xx）
 - 平均响应时间
 - P50, P95, P99 响应时间
 - CPU 时间使用
 - 出站请求数（调用 Supabase、OpenRouter）
**And** 数据保留 30 天（免费）或更长（付费）

#### Scenario: 自定义性能指标追踪
**Given** Workers 处理 API 请求
**When** 记录自定义性能指标
**Then** 使用 `console.time()` 和 `console.timeEnd()` 记录关键操作耗时：
 - Supabase 查询时间
 - OpenRouter API 调用时间
 - 缓存读取/写入时间
**And** 指标显示在 Cloudflare Dashboard
**And** 可通过 GraphQL API 查询历史数据

#### Scenario: 性能告警配置
**Given** Workers Analytics 已启用
**When** 配置性能告警（使用 Cloudflare Notifications）
**Then** 设置以下告警规则：
 - 平均响应时间 > 3s，持续 5 分钟
 - 错误率 > 5%，持续 5 分钟
 - CPU 时间 > 50ms（接近限制）
**And** 告警通过 Email 或 Webhook 发送

### Requirement: 缓存性能监控

缓存系统（Cloudflare KV 免费层）MUST 监控命中率和性能。

#### Scenario: 记录 KV 缓存命中率
**Given** Workers 使用 Cloudflare KV 缓存
**When** 处理缓存请求
**Then** 记录以下指标：
 - 缓存命中次数
 - 缓存未命中次数
 - 命中率 = 命中次数 / 总请求数
**And** 每小时聚合一次统计
**And** 目标命中率 > 80%

#### Scenario: 记录 KV 操作耗时
**Given** Workers 读取或写入 KV 缓存
**When** 操作完成
**Then** 记录操作耗时：
 - KV get: 目标 < 10ms
 - KV put: 目标 < 50ms
**And** 如果耗时超过目标，记录为慢操作

#### Scenario: 监控 KV 免费层使用量
**Given** KV 缓存已在生产使用
**When** 监控每日使用量
**Then** 追踪以下指标：
 - 每日读取次数（限制：100,000/天）
 - 每日写入次数（限制：1,000/天）
 - 存储空间使用量（限制：1 GB）
**And** 如果使用量 > 80% 限制，发送告警
**And** 如果接近限制，优化缓存策略：
 - 延长 TTL 减少写入
 - 优先使用 Supabase 持久化存储

### Requirement: OpenRouter API 性能监控

OpenRouter API 调用 MUST 监控延迟和成功率。

#### Scenario: 记录 OpenRouter 请求延迟
**Given** Workers 调用 OpenRouter API
**When** 请求完成
**Then** 记录以下信息：
 - 首 token 延迟（TTFT: Time To First Token）
 - 总响应时间
 - token 生成速率（tokens/秒）
**And** 目标：TTFT < 2s，总响应时间 < 30s

#### Scenario: 记录 OpenRouter 成功率
**Given** Workers 调用 OpenRouter API
**When** 记录请求结果
**Then** 统计：
 - 成功请求数（200 状态码）
 - 失败请求数（4xx, 5xx 状态码）
 - 成功率 = 成功数 / 总请求数
**And** 目标成功率 > 95%

#### Scenario: 监控 OpenRouter token 使用量
**Given** OpenRouter API 返回 token 使用信息
**When** 解析响应
**Then** 记录：
 - prompt_tokens（输入 tokens）
 - completion_tokens（输出 tokens）
 - total_tokens
**And** 聚合每日/每月 token 使用量
**And** 用于成本分析和配额管理

### Requirement: Supabase 查询性能监控

Supabase 数据库查询 MUST 监控并优化慢查询。

#### Scenario: 记录查询耗时
**Given** Workers 查询 Supabase 数据库
**When** 查询完成
**Then** 记录查询耗时
**And** 如果耗时 > 1 秒，标记为慢查询
**And** 记录慢查询的 SQL 语句（参数化）

#### Scenario: 分析慢查询并优化
**Given** 慢查询已记录
**When** 定期分析慢查询日志（每周）
**Then** 识别常见的慢查询模式
**And** 为慢查询添加数据库索引
**And** 重写低效的查询
**And** 验证优化后查询耗时 < 500ms

#### Scenario: 使用 Supabase 查询分析工具
**Given** Supabase Dashboard 可用
**When** 查看查询性能面板
**Then** 检查以下指标：
 - 最慢的查询
 - 最频繁的查询
 - 索引使用情况
**And** 根据分析结果优化查询

## REMOVED Requirements

### ~~Requirement: 后端启动性能优化~~
**移除原因**: Cloudflare Workers 无启动过程，不需要启动优化

### ~~Requirement: 并行初始化依赖连接~~
**移除原因**: Workers 无启动阶段，每个请求独立连接

### ~~Requirement: 懒加载非关键依赖~~
**移除原因**: Workers 无启动阶段

### ~~Requirement: 数据库连接池预热~~
**移除原因**: Workers 使用 Supabase 客户端，不需要连接池
