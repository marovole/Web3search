# Cloudflare Pages 配置指南

## 环境变量配置

前端已更新为连接新的 Cloudflare Workers API。需要在 Cloudflare Pages Dashboard 中配置以下环境变量：

### 生产环境变量

在 Cloudflare Pages Dashboard 中设置：

1. 访问: https://dash.cloudflare.com/pages
2. 选择 `web3search` 项目
3. 进入 `Settings` > `Environment variables`
4. 配置 `Production` 环境变量：

```
VITE_ENVIRONMENT=production
VITE_API_BASE_URL=https://web3search-api.marovole.workers.dev
VITE_USE_MOCK_API=false
VITE_ENABLE_SENTRY=false
VITE_ENABLE_ANALYTICS=false
VITE_ENABLE_EXPERIMENTAL_FEATURES=false
VITE_ENABLE_PERFORMANCE_MONITORING=true
VITE_DEBUG_MODE=false
```

### 预览环境变量（可选）

```
VITE_ENVIRONMENT=staging
VITE_API_BASE_URL=https://web3search-api.marovole.workers.dev
VITE_USE_MOCK_API=false
VITE_ENABLE_DEBUG=true
```

## 触发重新部署

配置环境变量后，需要触发重新部署：

### 方法 1: Git Push（推荐）
```bash
git add .
git commit -m "chore: 更新前端 API URL 指向 Cloudflare Workers"
git push
```

Cloudflare Pages 会自动检测到 push 并重新部署。

### 方法 2: 手动触发
1. 在 Cloudflare Pages Dashboard 中
2. 进入 `Deployments` 标签
3. 点击 `Retry deployment` 或创建新部署

## 验证部署

部署完成后验证：

1. 访问生产环境: https://web3search.pages.dev
2. 打开浏览器开发者工具 > Network
3. 测试搜索功能，检查 API 请求是否指向:
   - ✅ `https://web3search-api.marovole.workers.dev`
   - ❌ ~~`https://web3search-api.onrender.com`~~

## API 端点测试

部署后测试以下功能：

### 1. 搜索自动完成
- 在搜索框输入关键词
- 检查网络请求指向 `/api/v1/search/autocomplete`
- 验证响应格式正确

### 2. 聊天功能
- 测试快速聊天
- 检查请求指向 `/api/v1/chat/quick-chat`
- 验证流式响应正常工作

### 3. CORS 验证
- 确认前端域名在 Workers CORS 配置中
- 当前配置: `https://web3search.pages.dev,https://web3search.vercel.app`

## 问题排查

### 如果遇到 CORS 错误

检查 Workers 的 CORS 配置（`workers/wrangler.toml`）:
```toml
[env.production.vars]
CORS_ORIGINS = "https://web3search.pages.dev,https://web3search.vercel.app"
```

### 如果 API 请求失败

1. 检查 Workers API 健康状态:
   ```bash
   curl https://web3search-api.marovole.workers.dev/api/v1/health
   ```

2. 检查浏览器控制台错误

3. 验证环境变量是否正确加载:
   - 在浏览器中查看 `window.location` 和网络请求

## 回滚方案

如果新 API 出现问题，可以快速回滚：

1. 更新环境变量回到旧 API:
   ```
   VITE_API_BASE_URL=https://web3search-api.onrender.com
   ```

2. 触发重新部署

3. 或者直接在代码中回滚 `.env.production`
