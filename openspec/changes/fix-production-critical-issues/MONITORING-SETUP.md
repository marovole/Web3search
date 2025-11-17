# 监控配置指南

本指南将帮助你配置 Sentry 和 Google Analytics 监控。

## 📋 配置清单

### 1️⃣ Sentry 后端项目（workers-api）

#### 创建项目
1. 访问 [Sentry Dashboard](https://sentry.io/)
2. 创建新项目：
   - Platform: **Cloudflare Workers**（如果没有选项，选择 **Node.js**）
   - Project Name: `web3search-api`
   - Alert Frequency: **On every new issue**
3. 复制 **DSN** (格式: `https://xxx@xxx.ingest.sentry.io/xxx`)

#### 配置环境变量
在 Cloudflare Workers Dashboard 或使用 wrangler 命令：

```bash
# 方法 1: 使用 wrangler CLI（推荐）
cd workers-api
wrangler secret put SENTRY_DSN
# 粘贴你的 DSN，按 Enter

# 可选：配置采样率（默认生产环境 0.1）
wrangler secret put SENTRY_TRACES_SAMPLE_RATE
# 输入: 0.1

# 确保环境变量已设置
wrangler secret put ENVIRONMENT
# 输入: production
```

```bash
# 方法 2: 在 Cloudflare Dashboard 手动配置
# 1. 访问 Cloudflare Workers Dashboard
# 2. 选择 web3search-api worker
# 3. Settings > Variables and Secrets
# 4. 添加以下 secrets:
#    - SENTRY_DSN = <你的后端 DSN>
#    - ENVIRONMENT = production
#    - SENTRY_TRACES_SAMPLE_RATE = 0.1 (可选)
```

#### 验证配置
```bash
# 触发一个测试错误
curl -X POST https://web3search-api.onrender.com/api/v1/test-error

# 在 Sentry Dashboard 检查是否收到错误报告
# Issues > 应该看到新的错误事件，包含：
# - environment: production
# - requestId: <UUID>
# - serverLocation: <Cloudflare Colo>
```

---

### 2️⃣ Sentry 前端项目（frontend）

#### 创建项目
1. 访问 [Sentry Dashboard](https://sentry.io/)
2. 创建新项目：
   - Platform: **React**
   - Project Name: `web3search-frontend`
   - Alert Frequency: **On every new issue**
3. 复制 **DSN** (格式: `https://xxx@xxx.ingest.sentry.io/xxx`)

#### 配置环境变量
编辑 `frontend/.env.production`：

```bash
# Sentry 配置
VITE_ENABLE_SENTRY=true
VITE_SENTRY_DSN=<你的前端 DSN>
VITE_SENTRY_ENVIRONMENT=production

# 应用信息（用于 Release 跟踪）
VITE_APP_NAME=web3search
VITE_APP_VERSION=1.0.0

# Google Analytics（稍后配置）
VITE_ENABLE_ANALYTICS=true
VITE_GA_MEASUREMENT_ID=<稍后填写>

# API 端点
VITE_API_URL=https://web3search-api.onrender.com
```

#### 验证配置
```bash
# 1. 构建前端
cd frontend
npm run build

# 2. 部署到 Cloudflare Pages（自动触发）
git add .env.production
git commit -m "feat: configure Sentry frontend monitoring"
git push origin main

# 3. 打开生产环境网站
# https://web3search.pages.dev

# 4. 打开浏览器开发者工具 Console
# 应该看到: "[Sentry] Initialized successfully"

# 5. 测试错误捕获（在 Console 执行）
window.Sentry?.captureMessage('Test message from browser', 'info')

# 6. 在 Sentry Dashboard 检查
# Issues > 应该看到 "Test message from browser"
# - environment: production
# - release: web3search@1.0.0
# - PII 已过滤（无 email/IP/token）
```

---

### 3️⃣ Google Analytics 4

#### 创建 GA4 Property
1. 访问 [Google Analytics](https://analytics.google.com/)
2. Admin > Create Property:
   - Property Name: `Web3Search`
   - Time Zone: `Asia/Shanghai` 或你的时区
   - Currency: `CNY` 或你的货币
3. Create a **Web** Data Stream:
   - Website URL: `https://web3search.pages.dev`
   - Stream Name: `Web3Search Production`
4. 复制 **Measurement ID** (格式: `G-XXXXXXXXXX`)

#### 配置环境变量
更新 `frontend/.env.production`：

```bash
# Google Analytics
VITE_ENABLE_ANALYTICS=true
VITE_GA_MEASUREMENT_ID=<你的 Measurement ID>
```

#### 验证配置
```bash
# 1. 重新构建和部署
cd frontend
npm run build
git add .env.production
git commit -m "feat: configure Google Analytics"
git push origin main

# 2. 打开生产环境网站
# https://web3search.pages.dev

# 3. 检查网络请求
# 打开浏览器开发者工具 > Network
# 应该看到请求:
# - https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX
# - https://www.google-analytics.com/g/collect (page_view 事件)

# 4. 在 GA Dashboard 检查实时数据
# Reports > Realtime
# 应该看到你的访问（30秒内）

# 5. 测试自定义事件（在 Console 执行）
gtag('event', 'test_event', {
  event_category: 'test',
  event_label: 'manual_test'
})

# 6. 在 GA DebugView 检查（需要启用 debug 模式）
# Admin > Data Streams > Web3Search Production > Configure tag settings
# Enable "Enhanced measurement" + "Debug mode"
```

---

## 🔔 配置告警规则（Task 5.4）

### Sentry 告警

#### 错误率告警
1. 访问 Sentry Dashboard
2. 选择项目 > **Alerts** > **Create Alert Rule**
3. 配置规则：
   - Alert Name: `High Error Rate - Production`
   - Environment: `production`
   - Conditions:
     - **Error count** is greater than `10` in `1 minute`
     - OR **Error rate** is greater than `5%` in `5 minutes`
   - Actions:
     - Send notification to **Slack** (需要先集成 Slack)
     - OR Email to team

#### 性能告警
1. 创建新 Alert Rule
2. 配置：
   - Alert Name: `Slow API Response - Production`
   - Environment: `production`
   - Conditions:
     - **Transaction duration (P95)** is greater than `2000ms` in `5 minutes`
   - Actions:
     - Send notification to **Slack**

### Cloudflare Workers 告警

#### 方法 1: 使用 Cloudflare Email Alerts（免费）
1. 访问 Cloudflare Dashboard
2. **Workers & Pages** > 选择 `web3search-api`
3. **Settings** > **Alerts**
4. 启用告警：
   - **Script Errors**: 当脚本错误率 > 5% 时发送邮件
   - **High CPU Usage**: 当 CPU 时间 > 10ms 时发送邮件

#### 方法 2: 使用 Cloudflare Workers Analytics API（高级）
创建自定义脚本定期检查指标并发送 Slack 通知：

```bash
# 创建告警脚本（需要 Cloudflare API Token）
# workers-api/scripts/check-alerts.sh
```

### Slack 集成（推荐）

#### 配置 Sentry + Slack
1. Sentry Dashboard > **Settings** > **Integrations**
2. 搜索 **Slack** > **Install**
3. 授权 Slack workspace
4. 配置通知频道（如 `#web3search-alerts`）

#### 配置 Cloudflare + Slack（需要 Cloudflare Workers Paid Plan）
1. 创建 Slack Incoming Webhook
2. 在 Workers 中使用 webhook 发送告警

---

## ✅ 验证清单

### Sentry 后端
- [ ] DSN 已配置到 Cloudflare Workers secrets
- [ ] 访问 `/health` 端点，Sentry 收到性能追踪
- [ ] 触发错误，Sentry 收到错误报告
- [ ] 错误包含 `environment`, `requestId`, `serverLocation` 标签
- [ ] PII 已过滤（IP 掩码、无敏感数据）

### Sentry 前端
- [ ] DSN 已配置到 `.env.production`
- [ ] 浏览器 Console 显示 "[Sentry] Initialized successfully"
- [ ] 发送测试消息，Sentry 收到
- [ ] Release 标签正确（`web3search@1.0.0`）
- [ ] PII 已过滤（无 email/IP/token）

### Google Analytics
- [ ] Measurement ID 已配置到 `.env.production`
- [ ] 网络请求包含 `gtag.js` 和 `g/collect`
- [ ] GA Realtime 显示当前用户
- [ ] `page_view` 事件正常发送
- [ ] 自定义事件可以追踪

### 告警规则
- [ ] Sentry 错误率告警已配置（> 5%）
- [ ] Sentry 性能告警已配置（P95 > 2s）
- [ ] Cloudflare Workers 告警已启用
- [ ] Slack 集成已配置（可选）
- [ ] 收到测试告警通知

---

## 🎯 下一步

完成监控配置后：
1. 运行烟雾测试验证所有功能
2. 监控生产环境 24 小时
3. 根据实际数据调整告警阈值
4. 继续 Task 6: 提升测试覆盖率

---

## 📚 参考文档

- [Sentry Cloudflare Workers SDK](https://docs.sentry.io/platforms/javascript/guides/cloudflare/)
- [Sentry React SDK](https://docs.sentry.io/platforms/javascript/guides/react/)
- [Google Analytics 4 Setup](https://support.google.com/analytics/answer/9304153)
- [Cloudflare Workers Alerts](https://developers.cloudflare.com/workers/observability/alerts/)
