# 监控配置快速启动指南

## 📌 当前状态

### 监控服务状态总览

| 服务 | 状态 | 说明 |
|------|------|------|
| Sentry (后端) | 🔴 **已禁用** | 代码已集成，等待 DSN 配置 |
| Sentry (前端) | 🔴 **已禁用** | 代码已集成，等待 DSN 配置 |
| Google Analytics | 🔴 **已禁用** | 代码已集成，等待 Measurement ID 配置 |

### 禁用状态验证

**前端日志输出**（浏览器 Console）:
```
ℹ️ Sentry错误监控已禁用 (DSN未配置或已禁用)
ℹ️ Google Analytics已禁用 (Measurement ID未配置或已禁用)
```

**后端日志输出**（Cloudflare Workers Logs）:
```
[Sentry] Disabled (SENTRY_DSN not configured)
```

### 当前配置

**前端** (`frontend/.env.production`):
```bash
VITE_ENABLE_SENTRY=false        # 禁用状态
VITE_SENTRY_DSN=                # 空值

VITE_ENABLE_ANALYTICS=false     # 禁用状态
VITE_GA_MEASUREMENT_ID=         # 空值
```

**后端** (Cloudflare Workers):
- ❌ 无 `SENTRY_DSN` secret
- ✅ 代码已集成，条件判断完善

### 如何启用监控

如果您想启用监控服务，请按照下方的 **快速开始** 指南操作。代码已完全就绪，只需配置环境变量即可立即启用。

---

## 🚀 快速开始（5 分钟）

### 选项 1: 使用自动化脚本（推荐）

```bash
# 在项目根目录执行
./scripts/configure-monitoring.sh
```

脚本会交互式地引导你：
1. 配置 Sentry 后端 DSN
2. 配置 Sentry 前端 DSN
3. 配置 Google Analytics Measurement ID
4. 自动更新配置文件

### 选项 2: 手动配置

#### 第 1 步：创建 Sentry 项目

**后端项目**:
1. 访问 https://sentry.io/ → 创建项目
2. Platform: **Cloudflare Workers** (或 Node.js)
3. Name: `web3search-api`
4. 复制 DSN → 配置到 Cloudflare Workers

**前端项目**:
1. 创建新项目
2. Platform: **React**
3. Name: `web3search-frontend`
4. 复制 DSN → 更新 `frontend/.env.production`

#### 第 2 步：创建 Google Analytics Property

1. 访问 https://analytics.google.com/
2. Admin → Create Property → `Web3Search`
3. Create Web Data Stream → `https://web3search.pages.dev`
4. 复制 Measurement ID (G-XXXXXXXXXX)

#### 第 3 步：配置环境变量

**后端 (Cloudflare Workers)**:
```bash
cd workers-api
wrangler secret put SENTRY_DSN
wrangler secret put ENVIRONMENT
wrangler secret put SENTRY_TRACES_SAMPLE_RATE
```

**前端**:
编辑 `frontend/.env.production`:
```bash
VITE_SENTRY_DSN=<你的前端 DSN>
VITE_GA_MEASUREMENT_ID=<你的 Measurement ID>
```

#### 第 4 步：部署并验证

```bash
# 构建前端
cd frontend
npm run build

# 提交并部署
git add .env.production
git commit -m "feat: configure monitoring"
git push origin main

# 验证（等待部署完成 ~2 分钟）
# 1. 访问 https://web3search.pages.dev
# 2. 打开浏览器 Console，应该看到:
#    "[Sentry] Initialized successfully"
# 3. 检查 Sentry Dashboard 是否收到事件
# 4. 检查 GA Realtime 是否显示用户
```

---

## ✅ 验证清单

复制以下清单到你的任务追踪工具：

```markdown
### Sentry 后端
- [ ] 创建 Sentry 项目（web3search-api）
- [ ] 配置 SENTRY_DSN 到 Cloudflare Workers
- [ ] 访问 /health，检查 Sentry 是否收到事件
- [ ] 验证 PII 过滤（IP 掩码）

### Sentry 前端
- [ ] 创建 Sentry 项目（web3search-frontend）
- [ ] 更新 .env.production 中的 VITE_SENTRY_DSN
- [ ] 部署后检查 Console 日志
- [ ] 发送测试消息验证

### Google Analytics
- [ ] 创建 GA4 Property
- [ ] 更新 .env.production 中的 VITE_GA_MEASUREMENT_ID
- [ ] 部署后检查 Network 请求（gtag.js）
- [ ] 在 GA Realtime 查看用户

### 告警规则
- [ ] Sentry 错误率告警 (>5%)
- [ ] Sentry 性能告警 (P95 > 2s)
- [ ] Cloudflare Workers 告警
- [ ] Slack 集成（可选）
```

---

## 🆘 故障排查

### 问题 1: Sentry 未收到事件

**症状**: 部署后 Sentry Dashboard 无数据

**解决方案**:
```bash
# 检查 DSN 是否正确
cd workers-api
wrangler secret list  # 应该看到 SENTRY_DSN

# 检查前端配置
cat frontend/.env.production | grep SENTRY_DSN

# 手动触发测试
# 浏览器 Console 执行:
window.Sentry?.captureMessage('Test message', 'info')
```

### 问题 2: Google Analytics 无数据

**症状**: GA Realtime 不显示用户

**解决方案**:
```bash
# 1. 检查 Measurement ID 格式
cat frontend/.env.production | grep GA_MEASUREMENT_ID
# 应该是 G-XXXXXXXXXX 格式

# 2. 清除浏览器缓存并重新访问

# 3. 检查网络请求
# 打开开发者工具 > Network
# 搜索 "gtag" 或 "google-analytics"
# 应该看到 200 状态码

# 4. 检查 consent
# Console 执行:
localStorage.getItem('ga-consent')
# 应该是 "true"
```

### 问题 3: Workers DSN 配置失败

**症状**: `wrangler secret put` 报错

**解决方案**:
```bash
# 1. 确保已登录
wrangler login

# 2. 确保在正确的目录
cd workers-api

# 3. 检查 wrangler.toml 配置
cat wrangler.toml

# 4. 使用 Dashboard 手动配置
# https://dash.cloudflare.com → Workers → web3search-api
# → Settings → Variables and Secrets
```

---

## 📊 预期结果

配置成功后，你应该看到：

### Sentry Dashboard
- **后端项目**:
  - 每个 API 请求都有 transaction 记录
  - 错误事件包含完整堆栈和上下文
  - 标签: `environment`, `requestId`, `serverLocation`

- **前端项目**:
  - 页面加载性能数据
  - 错误事件包含用户操作历史
  - 标签: `release`, `environment`

### Google Analytics
- **Realtime Report**:
  - 显示当前在线用户
  - 页面浏览量
  - 事件追踪

- **Events**:
  - `page_view`
  - `search_query`
  - `chat_message`
  - `deep_research_start`

---

## 📚 下一步

完成监控配置后：

1. **配置告警规则** → 参考 `MONITORING-SETUP.md`
2. **运行 24 小时** → 收集基线数据
3. **调整阈值** → 根据实际数据优化告警
4. **文档化** → 更新运维手册

详细文档: `MONITORING-SETUP.md`
