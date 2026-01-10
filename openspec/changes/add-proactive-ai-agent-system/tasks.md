# Tasks: Add Proactive AI Agent System

## Phase 1: 用户认证与订阅系统 (Week 1-2)

### 1.1 Supabase Auth 集成
- [ ] 1.1.1 启用 Supabase Auth (Dashboard 配置)
- [x] 1.1.2 创建 `user_profiles` 表迁移文件
- [x] 1.1.3 配置 RLS 策略 (`auth.uid() = id`)
- [x] 1.1.4 创建 `user_quotas` 表迁移文件
- [x] 1.1.5 实现 Auth middleware (`workers-api/src/middlewares/auth.ts`)
- [x] 1.1.6 实现 `/api/v1/auth/me` 端点
- [x] 1.1.7 实现 `/api/v1/users/profile` GET/PATCH 端点
- [x] 1.1.8 前端 Auth Context (`frontend/src/contexts/AuthContext.tsx`)
- [x] 1.1.9 前端 Supabase Client 配置
- [x] 1.1.10 登录页面 UI (`frontend/src/pages/LoginPage.tsx`)
- [x] 1.1.11 注册页面 UI (`frontend/src/pages/SignupPage.tsx`)
- [x] 1.1.12 受保护路由 HOC (`frontend/src/components/ProtectedRoute.tsx`)
- [x] 1.1.13 Header 用户菜单组件 (`frontend/src/components/Layout/UserMenu.tsx`)
- [ ] 1.1.14 集成测试: Auth 流程

### 1.2 订阅付费系统 (Stripe)
- [ ] 1.2.1 创建 Stripe 账户和产品 (Free/Pro/Team)
- [ ] 1.2.2 配置 Stripe 价格 (月付/年付)
- [ ] 1.2.3 添加 Stripe Secret 到 Cloudflare Secrets
- [x] 1.2.4 实现 `/api/v1/billing/checkout` 端点
- [x] 1.2.5 实现 `/api/v1/billing/portal` 端点
- [x] 1.2.6 实现 `/api/v1/billing/webhook` 端点
- [x] 1.2.7 Webhook 处理: `checkout.session.completed`
- [x] 1.2.8 Webhook 处理: `customer.subscription.updated`
- [x] 1.2.9 Webhook 处理: `customer.subscription.deleted`
- [x] 1.2.10 订阅状态同步到 `user_profiles.plan`
- [x] 1.2.11 前端升级页面 UI (`frontend/src/pages/UpgradePage.tsx`)
- [x] 1.2.12 前端定价组件 (`frontend/src/components/Billing/PricingTable.tsx`)
- [ ] 1.2.13 集成测试: 订阅流程

### 1.3 配额系统
- [x] 1.3.1 实现配额检查 middleware
- [x] 1.3.2 实现 `/api/v1/users/quota` 端点
- [x] 1.3.3 创建配额重置 Cron (每日 `0 0 * * *`)
- [x] 1.3.4 创建配额重置 Cron (每月 `0 0 1 * *`)
- [x] 1.3.5 配额限制常量定义 (`lib/quota-limits.ts`)
- [x] 1.3.6 前端配额显示组件 (`frontend/src/components/Billing/QuotaUsage.tsx`)
- [ ] 1.3.7 配额耗尽提示和升级引导
- [ ] 1.3.8 集成测试: 配额执行

## Phase 2: Watchlist 与 Agent 框架 (Week 3)

### 2.1 Watchlist
- [x] 2.1.1 创建 `watchlist` 表迁移文件
- [x] 2.1.2 配置 RLS 策略
- [x] 2.1.3 实现 `/api/v1/watchlist` GET 端点 (列表)
- [x] 2.1.4 实现 `/api/v1/watchlist` POST 端点 (添加)
- [x] 2.1.5 实现 `/api/v1/watchlist/:id` DELETE 端点
- [x] 2.1.6 实现 `/api/v1/watchlist/:id` PATCH 端点
- [x] 2.1.7 代币搜索组件 (CoinGecko autocomplete)
- [x] 2.1.8 Watchlist 管理页面 (`frontend/src/pages/WatchlistPage.tsx`)
- [x] 2.1.9 Watchlist 卡片组件
- [x] 2.1.10 实时价格更新 (polling 每30秒)
- [x] 2.1.11 Watchlist 配额检查
- [ ] 2.1.12 集成测试: Watchlist CRUD

### 2.2 Agent 执行引擎
- [x] 2.2.1 创建 `agent_tasks` 表迁移文件
- [x] 2.2.2 创建 `agent_runs` 表迁移文件
- [x] 2.2.3 配置 RLS 策略
- [x] 2.2.4 Agent Engine 核心类 (`workers-api/src/lib/agent-engine.ts`)
- [x] 2.2.5 ReAct 循环实现
- [x] 2.2.6 Tool Registry 框架 (`workers-api/src/lib/agent-tools.ts`)
- [x] 2.2.7 实现 `/api/v1/agents/tasks` GET 端点
- [x] 2.2.8 实现 `/api/v1/agents/tasks` POST 端点
- [x] 2.2.9 实现 `/api/v1/agents/tasks/:id` GET/PATCH/DELETE
- [x] 2.2.10 实现 `/api/v1/agents/tasks/:id/pause` POST
- [x] 2.2.11 实现 `/api/v1/agents/tasks/:id/resume` POST
- [x] 2.2.12 实现 `/api/v1/agents/tasks/:id/runs` GET
- [x] 2.2.13 Agent 任务配额检查
- [ ] 2.2.14 单元测试: Agent Engine

## Phase 3: 价格预警与风险监控 Agent (Week 4-5)

### 3.1 价格预警 Agent
- [x] 3.1.1 注册价格检查 Cron Trigger (`*/5 * * * *`)
- [x] 3.1.2 实现批量价格获取 (CoinGecko batch API)
- [x] 3.1.3 实现条件评估逻辑 (`evaluatePriceCondition`)
- [x] 3.1.4 实现价格预警任务处理器
- [x] 3.1.5 价格预警配置类型定义
- [x] 3.1.6 价格预警配置 UI 组件
- [ ] 3.1.7 快捷创建: "提醒我当 X 跌破 $Y"
- [ ] 3.1.8 集成测试: 价格预警触发

### 3.2 风险监控 Agent
- [x] 3.2.1 复用 ScamMeter 评分逻辑
- [x] 3.2.2 存储历史评分用于变化检测
- [x] 3.2.3 实现评分变化检测逻辑
- [x] 3.2.4 实现 Red Flag 增量检测
- [x] 3.2.5 风险监控任务处理器
- [x] 3.2.6 风险监控配置 UI 组件
- [ ] 3.2.7 集成测试: 风险预警触发

## Phase 4: 新闻速报与推送通知 (Week 5-6)

### 4.1 浏览器推送基础设施
- [x] 4.1.1 生成 VAPID 密钥对 (需要运行时通过 wrangler secret 配置)
- [x] 4.1.2 存储 VAPID 私钥到 Cloudflare Secrets (已添加到 env.ts)
- [x] 4.1.3 创建 `push_subscriptions` 表迁移文件 (已存在于 20260109_create_watchlist_agent_tables.sql)
- [x] 4.1.4 前端 Service Worker 注册 (`frontend/public/sw.js`)
- [x] 4.1.5 前端推送订阅逻辑 (`frontend/src/lib/push.ts`)
- [x] 4.1.6 后端 web-push 集成 (`workers-api/src/lib/push.ts`)
- [x] 4.1.7 实现 `/api/v1/push/subscribe` POST 端点
- [x] 4.1.8 实现 `/api/v1/push/unsubscribe` DELETE 端点
- [x] 4.1.9 实现 `/api/v1/push/test` POST 端点
- [x] 4.1.10 前端推送权限请求 UI (`frontend/src/components/Settings/PushNotificationSettings.tsx`)
- [ ] 4.1.11 集成测试: 推送发送和接收

### 4.2 新闻速报 Agent
- [x] 4.2.1 CryptoPanic API 集成 (`workers-api/src/lib/cryptopanic.ts`)
- [x] 4.2.2 新闻过滤逻辑 (按 watchlist 代币)
- [x] 4.2.3 LLM 新闻摘要生成
- [x] 4.2.4 注册新闻速报 Cron (`0 * * * *` 每小时)
- [x] 4.2.5 新闻速报任务处理器
- [x] 4.2.6 新闻速报配置 UI
- [ ] 4.2.7 集成测试: 新闻速报推送

### 4.3 通知中心
- [x] 4.3.1 创建 `notifications` 表迁移文件 (in 20260109_create_watchlist_agent_tables.sql)
- [x] 4.3.2 配置 RLS 策略
- [x] 4.3.3 实现 `/api/v1/notifications` GET 端点
- [x] 4.3.4 实现 `/api/v1/notifications/:id/read` PATCH 端点
- [x] 4.3.5 实现 `/api/v1/notifications/read-all` POST 端点
- [x] 4.3.6 实现 `/api/v1/notifications/:id` DELETE 端点
- [x] 4.3.7 通知中心页面 (`frontend/src/pages/NotificationsPage.tsx`)
- [x] 4.3.8 通知列表组件 (integrated in NotificationsPage)
- [x] 4.3.9 Header 未读通知徽章 (`frontend/src/components/Notifications/NotificationBadge.tsx`)
- [x] 4.3.10 通知下拉预览组件 (`frontend/src/components/Notifications/NotificationDropdown.tsx`)
- [ ] 4.3.11 集成测试: 通知 CRUD

## Phase 5: 持仓诊断与机会发现 Agent (Week 6-7)

### 5.1 持仓诊断 Agent
- [x] 5.1.1 持仓数据模型设计
- [x] 5.1.2 持仓输入 UI (手动添加)
- [x] 5.1.3 持仓列表页面
- [x] 5.1.4 诊断报告生成逻辑
- [x] 5.1.5 诊断报告模板 (资产配置、相关性、表现)
- [x] 5.1.6 注册每周诊断 Cron (`0 9 * * 1`)
- [x] 5.1.7 持仓诊断任务处理器
- [x] 5.1.8 诊断报告展示组件
- [ ] 5.1.9 集成测试: 持仓诊断生成

### 5.2 机会发现 Agent
- [x] 5.2.1 用户偏好分析逻辑
- [x] 5.2.2 项目推荐算法 (基于偏好和市场热度)
- [x] 5.2.3 机会发现任务处理器
- [x] 5.2.4 推荐卡片 UI 组件
- [x] 5.2.5 推荐列表页面
- [x] 5.2.6 推荐反馈收集 (喜欢/不喜欢)
- [x] 5.2.7 集成测试: 推荐生成

## Phase 6: 对话式 Agent (Week 7-9)

### 6.1 Intent 解析系统
- [x] 6.1.1 Intent 类型定义 (`types/agent-intent.ts`)
- [x] 6.1.2 Intent Parser Prompt 设计
- [x] 6.1.3 Intent 解析函数 (`parseAgentIntent`)
- [x] 6.1.4 条件验证逻辑 (`validateIntentConditions`)
- [x] 6.1.5 任务自动创建逻辑
- [x] 6.1.6 置信度阈值处理 (< 0.8 需确认)
- [x] 6.1.7 单元测试: Intent 解析

### 6.2 对话式交互
- [x] 6.2.1 实现 `/api/v1/agents/conversation` POST 端点
- [x] 6.2.2 实现 `/api/v1/agents/conversation/stream` GET 端点 (SSE)
- [x] 6.2.3 Agent 对话页面 (`frontend/src/pages/AgentChatPage.tsx`)
- [x] 6.2.4 对话消息组件
- [x] 6.2.5 任务确认对话框
- [x] 6.2.6 任务创建成功反馈
- [x] 6.2.7 对话历史存储
- [x] 6.2.8 对话配额检查
- [ ] 6.2.9 集成测试: 对话式创建任务

## Phase 7: Agent Activity Log (Week 9-10)

### 7.1 Activity Log
- [x] 7.1.1 扩展 Glass Box Panel 组件
- [x] 7.1.2 Agent 执行事件类型定义
- [x] 7.1.3 实时执行日志 SSE 流
- [x] 7.1.4 历史执行日志查询
- [x] 7.1.5 日志筛选和搜索
- [x] 7.1.6 Agent Dashboard 页面 (`frontend/src/pages/AgentDashboardPage.tsx`)
- [x] 7.1.7 Agent 状态概览组件
- [x] 7.1.8 执行统计图表
- [ ] 7.1.9 集成测试: Activity Log

## Phase 8: 测试与优化 (Week 10-11)

### 8.1 测试
- [x] 8.1.1 单元测试: Agent Engine (覆盖率 > 80%)
- [x] 8.1.2 单元测试: Intent Parser
- [x] 8.1.3 单元测试: 配额系统
- [ ] 8.1.4 集成测试: Auth 流程
- [ ] 8.1.5 集成测试: 订阅流程
- [ ] 8.1.6 集成测试: Agent 生命周期
- [ ] 8.1.7 E2E 测试: 用户注册到创建第一个 Agent
- [ ] 8.1.8 E2E 测试: 价格预警触发通知
- [ ] 8.1.9 负载测试: Cron 任务批量处理

### 8.2 优化
- [x] 8.2.1 批量 API 调用优化 (减少外部请求)
- [x] 8.2.2 通知合并逻辑 (防止骚扰)
- [x] 8.2.3 缓存策略优化
- [x] 8.2.4 数据库索引优化

### 8.3 文档
- [x] 8.3.1 用户指南: Agent 功能介绍
- [x] 8.3.2 用户指南: 对话式 Agent 使用示例
- [ ] 8.3.3 API 文档更新
- [ ] 8.3.4 开发者文档: Agent 扩展指南
