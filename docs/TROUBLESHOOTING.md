# Web3search 故障排除指南

本文档提供常见问题的诊断和解决方案。

## 目录
- [生产环境问题](#生产环境问题)
- [API 调用失败](#api-调用失败)
- [页面导航问题](#页面导航问题)
- [CORS 错误](#cors-错误)
- [性能问题](#性能问题)

---

## 生产环境问题

### 问题：页面显示 404 错误

**症状**：
- 访问 `/history` 或 `/watchlist` 显示 404
- 刷新页面后丢失当前路由

**诊断步骤**：

1. 检查 `_redirects` 文件配置 (Cloudflare Pages):
   ```bash
   cat frontend/public/_redirects
   ```

2. 验证 SPA 路由规则是否存在：
   ```
   /*  /index.html  200
   ```

3. 检查 Cloudflare Pages 部署日志

**解决方案**：

✅ **方案 1**: 确保 `_redirects` 文件包含 SPA 路由规则
```
# API 代理规则 (必须在前面)
/api/v1/*  https://web3search-api.onrender.com/api/v1/:splat  200

# SPA 路由支持 (必须在最后)
/*  /index.html  200
```

✅ **方案 2**: 清除 Cloudflare Pages 缓存并重新部署
```bash
# 在 Cloudflare Dashboard 中触发重新部署
```

---

## API 调用失败

### 问题：API 请求返回 404

**症状**：
- Quick Chat 功能无响应
- 浏览器控制台显示 `404 Not Found`
- 网络面板显示 API 请求失败

**诊断步骤**：

1. 打开浏览器开发者工具 → Network 标签页
2. 发送一个 Quick Chat 请求
3. 查看实际请求的 URL

**常见错误模式**：

❌ **错误**: 路径重复
```
https://web3search-api.onrender.com/api/v1/api/v1/chat/quick-chat
                                      ^^^^^^^^ 重复了!
```

❌ **错误**: 缺少 API 前缀
```
https://web3search.pages.dev/chat/quick-chat
                            ^^^^^^^^ 缺少 /api/v1
```

✅ **正确**:
```
https://web3search-api.onrender.com/api/v1/chat/quick-chat
```

**解决方案**：

1. 检查 `frontend/src/utils/env.ts` 配置：
   ```typescript
   // ✅ 正确: 基础 URL 不包含 /api
   API_BASE_URL = 'https://web3search-api.onrender.com'

   // ❌ 错误: 基础 URL 包含 /api
   API_BASE_URL = 'https://web3search-api.onrender.com/api'
   ```

2. 检查浏览器控制台日志：
   ```
   ✅ API Configuration: https://web3search-api.onrender.com (Environment: production)
   ❌ API_BASE_URL contains API path! This will cause path duplication.
   ```

3. 如果看到路径重复错误，代码会自动修复。刷新页面后应该正常。

---

### 问题：API 请求超时

**症状**：
- Quick Chat 请求超过 30 秒无响应
- 浏览器控制台显示超时错误

**诊断步骤**：

1. 检查后端健康状态：
   ```bash
   curl https://web3search-api.onrender.com/api/health
   ```

2. 查看 Render 服务状态（如果使用 Render）

3. 运行烟雾测试：
   ```bash
   node scripts/smoke-test.js
   ```

**解决方案**：

✅ **方案 1**: 后端可能在冷启动，等待 30-60 秒后重试

✅ **方案 2**: 检查后端日志查看具体错误

✅ **方案 3**: 如果是 LLM API 限流，等待几分钟后重试

---

## 页面导航问题

### 问题：点击导航按钮无反应

**症状**：
- 点击"历史记录"或"监控列表"按钮没有跳转
- 控制台有 JavaScript 错误

**诊断步骤**：

1. 打开浏览器开发者工具 → Console 标签页
2. 查找 React Router 相关错误
3. 检查是否有懒加载失败的错误

**解决方案**：

✅ **方案 1**: 清除浏览器缓存并刷新

✅ **方案 2**: 检查网络连接，确保静态资源可以加载

✅ **方案 3**: 检查 React Router 配置:
```typescript
// frontend/src/App.tsx
<Route path="/history" element={
  <Suspense fallback={<AdaptiveSkeleton pageType="history" />}>
    <HistoryPage />
  </Suspense>
} />
```

---

## CORS 错误

### 问题：浏览器显示 CORS 错误

**症状**：
```
Access to XMLHttpRequest at 'https://web3search-api.onrender.com/api/v1/chat/quick-chat'
from origin 'https://web3search.pages.dev' has been blocked by CORS policy
```

**诊断步骤**：

1. 检查请求响应头：
   ```bash
   curl -I -H "Origin: https://web3search.pages.dev" \
     https://web3search-api.onrender.com/api/health
   ```

2. 查找 `Access-Control-Allow-Origin` 响应头

**解决方案**：

✅ **方案 1**: 通过前端代理访问 API（推荐）
- 生产环境应该通过 `/api/*` 代理访问
- Cloudflare Pages Functions 会自动添加 CORS 头

✅ **方案 2**: 检查 `functions/_middleware.ts`:
```typescript
// 确保添加了 CORS 头部
headers.set('Access-Control-Allow-Origin', '*');
headers.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
```

✅ **方案 3**: 检查后端 CORS 配置（如果直接访问后端）

---

## 性能问题

### 问题：页面加载很慢

**症状**：
- 首次加载超过 5 秒
- Lighthouse 性能分数低于 70

**诊断步骤**：

1. 运行 Lighthouse 审计：
   ```bash
   cd frontend
   npm run lighthouse
   ```

2. 检查 Network 面板，找出慢的资源

3. 检查是否启用了代码分割：
   ```typescript
   // 应该使用 React.lazy
   const ChatPage = React.lazy(() => import('./pages/ChatPage'))
   ```

**解决方案**：

✅ **方案 1**: 启用 Gzip/Brotli 压缩（Cloudflare Pages 默认启用）

✅ **方案 2**: 检查图片大小，使用 WebP 格式

✅ **方案 3**: 启用 CDN 缓存:
```
# _headers 文件
/assets/*
  Cache-Control: public, max-age=31536000, immutable
```

---

## 调试工具

### 1. 烟雾测试

快速验证部署是否成功：

```bash
# 测试生产环境
FRONTEND_URL=https://web3search.pages.dev \
BACKEND_URL=https://web3search-api.onrender.com \
node scripts/smoke-test.js
```

### 2. 查看 API 配置日志

打开浏览器控制台，查找以下日志：

```
✅ API Configuration: https://web3search-api.onrender.com (Environment: production, isProduction: true)
🌐 Final API Configuration: {hostname: "web3search.pages.dev", isProduction: true, apiBaseUrl: "https://web3search-api.onrender.com", ...}
[API] Quick Chat Request: https://web3search-api.onrender.com/api/v1/chat/quick-chat
```

### 3. Playwright E2E 测试

运行完整的端到端测试：

```bash
cd frontend
npm run test:e2e
```

生产环境测试：
```bash
cd frontend
TEST_ENV=production FRONTEND_URL=https://web3search.pages.dev npm run test:e2e
```

---

## 获取帮助

如果问题仍未解决：

1. **查看日志**:
   - Cloudflare Pages: Functions 日志
   - Render: 应用日志
   - 浏览器: 开发者工具控制台

2. **运行完整诊断**:
   ```bash
   # 烟雾测试
   node scripts/smoke-test.js

   # E2E 测试
   cd frontend && npm run test:e2e
   ```

3. **创建 Issue**:
   - GitHub: https://github.com/marovole/Web3search/issues
   - 包含: 错误信息、浏览器版本、重现步骤

---

## 相关文档

- [部署指南](../frontend/DEPLOYMENT_GUIDE.md)
- [测试指南](../frontend/TESTING_GUIDE.md)
- [API 文档](../backend/README.md)
