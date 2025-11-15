# Analytics Spec Delta

## ADDED Requirements

### Requirement: Sentry 错误监控
系统 **SHALL** 集成 Sentry 进行实时错误追踪和性能监控。

#### Scenario: 后端 Sentry 集成
- **WHEN** Workers API 发生错误或异常
- **THEN** 错误自动上报到 Sentry
- **AND** 包含错误堆栈、请求上下文、用户信息
- **AND** 设置环境标签（production, development）
- **AND** SENTRY_DSN 通过 wrangler secrets 配置

#### Scenario: 前端 Sentry 集成
- **WHEN** 前端应用发生 JavaScript 错误
- **THEN** 错误自动上报到 Sentry
- **AND** 捕获 unhandled promise rejections
- **AND** 记录用户操作路径（breadcrumbs）
- **AND** 采样率设置合理（production: 10%，避免超出配额）

### Requirement: Google Analytics 用户行为追踪
前端应用 **SHALL** 集成 Google Analytics 4 追踪用户行为和使用模式。

#### Scenario: 页面浏览追踪
- **WHEN** 用户访问应用页面
- **THEN** 记录页面浏览事件（page_view）
- **AND** 收集页面路径、标题、referrer
- **AND** 追踪停留时间和跳出率

#### Scenario: 功能使用追踪
- **WHEN** 用户使用核心功能（搜索、聊天、Deep Research）
- **THEN** 记录自定义事件（search, chat, deep_research）
- **AND** 追踪功能使用频率和成功率
- **AND** 分析用户流程和转化漏斗

### Requirement: 关键指标告警
系统 **SHALL** 监控关键指标并在异常时发送告警。

#### Scenario: 错误率告警
- **WHEN** 错误率超过阈值（> 5% in 5 minutes）
- **THEN** 发送告警到 Slack 或邮件
- **AND** 包含错误详情和影响范围
- **AND** 提供快速响应建议

#### Scenario: 性能告警
- **WHEN** API 响应时间 P95 > 1000ms 持续 5 分钟
- **THEN** 发送性能降级告警
- **AND** 包含慢请求样本和可能原因
- **AND** 触发自动调查流程（检查数据库、缓存、外部API）
