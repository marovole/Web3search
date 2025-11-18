# 监控集成部署指南

本文档介绍如何完成 Sentry 和 Google Analytics 监控的最终配置和部署。

## 前置条件

- ✅ 后端 Sentry SDK 已集成（toucan-js）
- ✅ 前端 Sentry SDK 已集成（@sentry/react）
- ✅ Google Analytics 延迟加载已实现
- ✅ 所有代码已提交到 Git
- ⚠️ 需要创建 Sentry 项目和 GA4 property

---

## 第一步：创建 Sentry 项目

### 1.1 后端 Sentry（Workers API）

1. **登录 Sentry**
   - 访问 https://sentry.io/
   - 登录或创建账号

2. **创建项目**
   - 选择 "Create Project"
   - Platform: **JavaScript** → **Cloudflare Workers**
   - Project name: `web3search-workers-api`
   - Team: 选择你的团队

3. **获取 DSN**
   - 复制 DSN，格式类似：`https://xxxxx@o123456.ingest.sentry.io/7891011`

4. **配置环境变量**
   ```bash
   cd workers-api
   wrangler secret put SENTRY_DSN
   # 粘贴上面复制的 DSN
   
   # 可选：配置性能监控采样率（默认 0.1 = 10%）
   wrangler secret put SENTRY_TRACES_SAMPLE_RATE
   # 输入：0.1
   ```

5. **测试错误上报**
   ```bash
   # 部署后端
   wrangler publish --env production
   
   # 触发一个测试错误
   curl -X POST https://web3search-api.marovole.workers.dev/api/v1/chat/test-error
   
   # 检查 Sentry Dashboard 是否收到错误
   ```

### 1.2 前端 Sentry（Frontend）

1. **创建项目**
   - Platform: **JavaScript** → **React**
   - Project name: `web3search-frontend`
   - Team: 选择你的团队

2. **获取 DSN**
   - 复制 DSN

3. **更新环境变量**
   ```bash
   cd frontend
   
   # 编辑 .env.production
   nano .env.production
   
   # 替换 <YOUR_SENTRY_DSN_HERE> 为真实 DSN
   VITE_SENTRY_DSN=https://xxxxx@o123456.ingest.sentry.io/7891012
   ```

4. **构建和测试**
   ```bash
   # 本地测试
   npm run build
   npm run preview
   
   # 访问 http://localhost:4173
   # 打开浏览器控制台，应该看到：
   # [Sentry] Initialized successfully
   
   # 触发测试错误（打开浏览器控制台执行）
   throw new Error('Test error for Sentry')
   
   # 检查 Sentry Dashboard 是否收到错误
   ```

---

## 第二步：创建 Google Analytics 4 Property

### 2.1 创建 GA4 Property

1. **访问 Google Analytics**
   - https://analytics.google.com/

2. **创建 Property**
   - Admin → Create Property
   - Property name: `Web3search`
   - Time zone: 选择你的时区
   - Currency: 选择货币

3. **创建数据流**
   - Platform: **Web**
   - Website URL: `https://web3search.pages.dev`
   - Stream name: `Web3search Frontend`

4. **获取 Measurement ID**
   - 复制 Measurement ID，格式：`G-XXXXXXXXXX`

### 2.2 配置前端

1. **更新环境变量**
   ```bash
   cd frontend
   nano .env.production
   
   # 替换 G-XXXXXXXXXX 为真实 Measurement ID
   VITE_GA_MEASUREMENT_ID=G-XXXXXXXXXX
   ```

2. **测试 GA 集成**
   ```bash
   npm run build
   npm run preview
   
   # 访问网站，打开浏览器控制台
   # 应该看到：
   # Google Analytics initialized with ID: G-XXXXXXXXXX
   
   # 访问 GA 实时报告，检查是否收到事件
   # https://analytics.google.com/ → Reports → Realtime
   ```

---

## 第三步：部署到生产环境

### 3.1 后端部署

```bash
cd workers-api

# 确保所有秘密已配置
wrangler secret list

# 应该看到：
# - SENTRY_DSN
# - OPENROUTER_API_KEY
# - SUPABASE_URL
# - SUPABASE_ANON_KEY
# ...

# 部署到生产环境
wrangler publish --env production

# 验证部署
curl https://web3search-api.marovole.workers.dev/api/v1/health
```

### 3.2 前端部署

```bash
cd frontend

# 确认环境变量配置正确
cat .env.production

# 提交代码到 Git
git add .
git commit -m "feat(monitoring): 完成 Sentry 和 GA 监控集成

- 后端集成 toucan-js (Cloudflare Workers Sentry SDK)
- 前端集成 @sentry/react
- 实现 PII 过滤（URL、email、IP、tokens）
- 优化 GA 脚本延迟加载
- 添加类型化事件定义

相关: Task 5.1, 5.2, 5.3"

# 推送到 main 分支（触发 Cloudflare Pages 自动部署）
git push origin main

# 检查部署状态
# https://dash.cloudflare.com/pages
```

### 3.3 验证部署

1. **检查前端**
   ```bash
   # 访问生产环境
   curl -I https://web3search.pages.dev
   
   # 应该返回 200 OK
   ```

2. **检查监控**
   - Sentry Dashboard: 应该看到新的 sessions
   - GA Realtime: 应该看到活跃用户

---

## 第四步：配置告警规则（可选）

### 4.1 Sentry 告警

1. **访问 Sentry 项目设置**
   - Settings → Alerts

2. **创建告警规则**
   - Alert Name: `High Error Rate`
   - Conditions:
     - When **error count** is **more than** `100` in `1 hour`
     - AND **error rate** is **more than** `5%`
   - Actions:
     - Send notification to **Slack** (需要先集成 Slack)
     - Send email to **你的邮箱**

3. **测试告警**
   - 手动触发一些错误
   - 检查是否收到通知

### 4.2 Cloudflare Workers 告警

1. **访问 Cloudflare Dashboard**
   - Workers & Pages → web3search-api → Logs

2. **设置日志查询告警**（需要 Workers Paid plan）
   - 目前免费计划不支持自动告警
   - 建议：定期查看 Dashboard 监控指标

---

## 第五步：验证和测试

### 5.1 端到端测试

```bash
# 前端测试
cd frontend
npm run test:e2e

# 后端测试
cd workers-api
npm test
```

### 5.2 烟雾测试

```bash
# 测试关键流程
cd frontend
npm run test:smoke

# 检查输出，所有测试应该通过
```

### 5.3 手动测试清单

- [ ] 访问 https://web3search.pages.dev
- [ ] 搜索功能正常
- [ ] Chat 功能正常
- [ ] Deep Research 功能正常
- [ ] 浏览器控制台无错误
- [ ] Sentry Dashboard 显示活跃会话
- [ ] GA Realtime 显示页面浏览

---

## 常见问题

### Q1: Sentry 没有收到任何事件

**检查清单**：
1. DSN 配置正确？
   - 后端：`wrangler secret list` 确认 SENTRY_DSN 存在
   - 前端：`cat .env.production` 确认 VITE_SENTRY_DSN 正确
2. VITE_ENABLE_SENTRY=true？
3. 网络是否可以访问 Sentry？
   ```bash
   curl -I https://o123456.ingest.sentry.io
   ```
4. 浏览器控制台是否显示 Sentry 初始化成功？

### Q2: GA 没有数据

**检查清单**：
1. Measurement ID 配置正确？
2. VITE_ENABLE_ANALYTICS=true？
3. 用户是否同意了 Analytics？（检查 localStorage）
   ```javascript
   localStorage.getItem('analytics_consent')
   ```
4. 浏览器是否阻止了 GA 脚本？（检查 Ad Blocker）
5. GA 实时报告查看方式：
   - https://analytics.google.com/ → Reports → Realtime

### Q3: TypeScript 编译错误

如果遇到 Sentry 相关的类型错误：

```bash
cd frontend
npm install @sentry/react@latest @sentry/tracing@latest
npx tsc --noEmit
```

---

## 性能影响评估

### Bundle Size

- **Sentry**: ~50KB (gzipped)
- **GA**: 延迟加载，不影响初始 bundle

### 性能指标

- **FCP (First Contentful Paint)**: 无影响（GA 延迟加载）
- **TTI (Time to Interactive)**: +10-20ms（Sentry 初始化）
- **LCP (Largest Contentful Paint)**: 无影响

### 网络请求

- **Sentry**: 错误时才发送，平均 < 5 requests/session
- **GA**: 平均 10-15 requests/session

---

## 后续优化建议

1. **配置 Source Maps**
   ```bash
   # 前端 vite.config.ts
   build: {
     sourcemap: true
   }
   
   # 上传到 Sentry
   npm install --save-dev @sentry/vite-plugin
   ```

2. **配置 Replay Session**（Sentry Session Replay）
   - 记录用户交互，帮助调试

3. **自定义事件追踪**
   - 追踪关键业务指标（搜索成功率、Chat 响应时间）

4. **设置性能预算**
   - Lighthouse CI
   - Bundle size limits

---

## 总结

完成以上步骤后，你的 Web3search 应用将具备：

✅ **错误监控**：Sentry 自动捕获前后端错误  
✅ **性能监控**：Core Web Vitals、API 延迟追踪  
✅ **用户分析**：Google Analytics 页面浏览、事件追踪  
✅ **PII 保护**：自动过滤敏感信息  
✅ **生产级配置**：环境隔离、采样率优化  

祝部署顺利！🎉
