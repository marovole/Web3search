# Implementation Tasks

## Phase 1: P0 紧急修复 (Week 1)

### 1. 修复 TypeScript 编译错误
- [x] 1.1 更新 `workers-api/src/types/env.ts` Env 接口
  - 添加 `OPENROUTER_CIRCUIT_STATE?: KVNamespace`
  - 添加 `SENTRY_DSN?: string`
  - 添加 `CLIENT_SESSION_ID?: string`
  - 添加搜索提供商 API keys（BRAVE, TAVILY, SERPER）
- [x] 1.2 添加 env.CACHE 安全检查
  - 修改 `workers-api/src/index.ts` cron handlers (行 149-205)
  - 在使用 env.CACHE 前检查 undefined
  - 返回 503 状态码当 CACHE 未绑定
- [x] 1.3 修复 OpenRouter Payload 类型
  - 修改 `workers-api/src/routes/deep-research.ts` (行 592, 687, 745)
  - messages 使用 `ChatCompletionMessage[]` 类型
  - role 字段使用 `as ChatRole` 类型断言
- [x] 1.4 添加 SSE 事件 timestamp 字段
  - 修改 `workers-api/src/types/deep-research.ts`
  - `ResearchProgress` 添加 `timestamp: string`
  - `ResearchStepData` 添加 `timestamp: string`
  - 修改 `streamDeepResearch` emit 函数自动添加 timestamp
- [x] 1.5 扩展 ChatRequestBody 接口
  - 修改 `workers-api/src/routes/chat-v2.ts`
  - 添加 `temperature?: number`
  - 添加 `max_tokens?: number`
- [x] 1.6 修复 RetryConfig 接口
  - 修改 `workers-api/src/lib/resilience.ts`
  - 添加 `timeoutMs: number` 字段
- [x] 1.7 修复 Telemetry 返回类型
  - 修改 `workers-api/src/lib/telemetry.ts` (行 125)
  - 返回类型改为 `Promise<TelemetryData>`
- [x] 1.8 修复 ReadableStreamController signal 问题
  - 修改 `workers-api/src/lib/streaming.ts` (行 266)
  - 移除或替换 controller.signal 引用
- [x] 1.9 验证 TypeScript 编译
  - 运行 `npx tsc --noEmit` 确保 0 errors
  - 修复所有剩余编译错误

### 2. 诊断和修复前端 SSL 问题
- [x] 2.1 检查 Cloudflare Pages 部署状态
  - **诊断结果**: DNS 解析正常(221.228.32.13), SSL 握手超时
  - **根本原因**: Cloudflare Pages 项目未正确部署或配置
- [x] 2.2 验证 SSL/TLS 配置
  - **测试结果**: `LibreSSL SSL_connect: SSL_ERROR_SYSCALL` (连接超时)
  - **状态**: 需要 Cloudflare Dashboard 访问权限进行修复
- [x] 2.3 检查 DNS 配置
  - **测试结果**: DNS 解析正常 (`nslookup` 返回 221.228.32.13)
  - **状态**: DNS 配置正确,问题在服务器端
- [ ] 2.4 修复 SSL 问题 **[需要手动处理]**
  - **操作步骤**: 登录 Cloudflare Dashboard → Pages → web3search
  - 检查项目是否存在和绑定到正确的 Git 仓库
  - 验证最近的部署状态和日志
  - 如需要,重新连接 GitHub 仓库或手动部署
  - **验证**: `curl -I https://web3search.pages.dev` 返回 200
- [ ] 2.5 添加部署验证脚本
  - 创建 `frontend/scripts/deploy-verify.sh`
  - 自动检查 SSL、DNS、页面加载
  - 集成到 CI/CD 流程

### 3. 修复 Deep Research 路由 404
- [x] 3.1 检查路由注册
  - 确认 `/api/v1/deep-research/stream` 已正确注册 (deep-research.ts:197)
  - 验证路由 handler 返回 SSE 响应
- [x] 3.2 检查中间件拦截
  - CORS 中间件配置正确
  - 中间件不拦截 Deep Research 路由
  - 路由优先级正确
- [x] 3.3 修复测试失败
  - 修复 SSE 事件缺少 timestamp 字段导致的类型错误
  - 所有4个测试通过 (200状态码, text/event-stream)
- [x] 3.4 运行回归测试
  - `npm test -- --run` 所有252个测试通过
  - TypeScript 编译通过 (0 errors)

## Phase 2: P1 高优先级优化 (Week 2)

### 4. 优化 API 性能
- [ ] 4.1 实现健康检查缓存
  - 修改 `workers-api/src/routes/health.ts`
  - 添加 KV 缓存逻辑（键: `health:status`, TTL: 60s）
  - 缓存命中时直接返回（< 100ms）
  - 缓存未命中时执行检查并缓存
- [ ] 4.2 优化数据库连接
  - 检查 Supabase 连接池配置
  - 复用连接而非每次创建
  - 设置合理超时（< 5s）
- [ ] 4.3 监控性能指标
  - 添加响应时间日志（TTFB, Total Time）
  - 记录缓存命中率
  - 监控慢查询（> 1s）
- [ ] 4.4 性能测试验证
  - 测试健康检查响应时间 < 300ms (P95)
  - 测试搜索 API < 500ms (P95)
  - 验证缓存命中率 > 80%

### 5. 启用监控和告警
- [ ] 5.1 配置后端 Sentry
  - 创建 Sentry 项目（Workers API）
  - 获取 DSN: `wrangler secret put SENTRY_DSN`
  - 集成 Sentry SDK 到 Workers
  - 测试错误上报
- [ ] 5.2 配置前端 Sentry
  - 创建 Sentry 项目（Frontend）
  - 更新 `frontend/.env.production`:
    - `VITE_ENABLE_SENTRY=true`
    - `VITE_SENTRY_DSN=<DSN>`
  - 集成 @sentry/react
  - 测试错误捕获和上报
- [ ] 5.3 启用 Google Analytics
  - 创建 GA4 property
  - 更新 `frontend/.env.production`:
    - `VITE_ENABLE_ANALYTICS=true`
    - `VITE_GA_MEASUREMENT_ID=G-XXXXXXXXXX`
  - 集成 gtag.js
  - 测试事件追踪（page_view, search, chat）
- [ ] 5.4 配置告警规则
  - Sentry: 错误率 > 5% 发送 Slack 通知
  - Cloudflare Workers: API 延迟 > 2s 告警
  - 设置 on-call 通知

### 6. 提升测试覆盖率
- [ ] 6.1 修复所有失败测试
  - 确保所有测试通过（0 failed）
  - 修复 chat.test.ts 中的 4 个失败测试
  - 修复其他潜在失败测试
- [ ] 6.2 添加端到端测试
  - 创建 `workers-api/tests/e2e/deep-research.test.ts`
  - 测试完整 Deep Research 流程
  - 测试搜索提供商 failover
  - 测试错误处理和重试
- [ ] 6.3 提升代码覆盖率
  - 运行 `npm test -- --coverage`
  - 目标: Statements > 80%, Branches > 75%, Functions > 80%
  - 为未覆盖代码添加测试
- [ ] 6.4 集成测试到 CI
  - 更新 GitHub Actions workflow
  - 在 PR 时运行所有测试
  - 测试失败时阻止合并
  - 生成覆盖率报告并上传

## Phase 3: 验证和文档 (Week 3)

### 7. 生产环境验证
- [ ] 7.1 部署所有修复到生产环境
  - 部署后端: `wrangler publish --env production`
  - 部署前端: 提交到 main 分支触发自动部署
  - 验证部署成功
- [ ] 7.2 运行 smoke tests
  - 测试前端可访问性（SSL 正常）
  - 测试 API 健康检查 < 300ms
  - 测试搜索功能正常
  - 测试 Deep Research 功能正常
- [ ] 7.3 监控生产指标
  - 检查 Sentry 错误率
  - 查看 GA 用户活跃度
  - 监控 API 响应时间
  - 验证缓存命中率
- [ ] 7.4 压力测试（可选）
  - 模拟高并发请求
  - 验证性能和稳定性
  - 检查 Cloudflare Workers 限制

### 8. 文档更新
- [ ] 8.1 更新部署文档
  - 记录 SSL 修复过程
  - 更新环境变量配置说明
  - 添加 Sentry 和 GA 配置指南
- [ ] 8.2 更新开发文档
  - 记录 TypeScript 类型修复
  - 更新测试运行指南
  - 添加性能优化最佳实践
- [ ] 8.3 创建运维手册
  - 健康检查和监控指南
  - 告警响应流程
  - 常见问题排查
- [ ] 8.4 更新 CHANGELOG
  - 记录所有修复和改进
  - 标注破坏性变更（如有）
  - 添加升级指南

## Notes
- **优先级**: P0 任务必须在 Week 1 完成，P1 任务在 Week 2 完成
- **依赖关系**: 
  - 任务 1.9 依赖 1.1-1.8 全部完成
  - 任务 3.4 依赖 3.1-3.3 完成
  - Phase 2 可以在 Phase 1 完成后并行开始
- **风险缓解**:
  - 每个修复后立即运行测试
  - 逐步部署，优先修复阻塞性问题
  - 保持代码可回滚
- **验证标准**:
  - ✅ TypeScript 编译: 0 errors
  - ✅ 前端可访问: SSL 连接成功
  - ✅ API 性能: 健康检查 < 300ms (P95)
  - ✅ 监控: Sentry 和 GA 正常上报
  - ✅ 测试: 所有测试通过，覆盖率 > 80%
