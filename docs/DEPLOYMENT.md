# Web3search 部署指南

本文档说明如何部署 Web3search 到生产环境。

## 部署架构

```
用户 → Cloudflare Pages (前端+代理) → Render (后端 API)
```

### 关键配置

1. **API 基础 URL**: `https://web3search-api.onrender.com` (不包含 /api 路径)
2. **API 代理**: 所有 `/api/*` 请求通过 Cloudflare Functions 转发
3. **SPA 路由**: `/* → /index.html` 支持前端路由

## 快速部署

### 1. 前端部署 (Cloudflare Pages)

```bash
cd frontend
npm run build
npx wrangler pages deploy dist --project-name=web3search
```

### 2. 后端部署 (Render)

参考后端 README.md

### 3. 部署验证

```bash
node scripts/smoke-test.js
```

## 环境变量

**前端 (frontend/.env.production)**:
```bash
VITE_API_BASE_URL=https://web3search-api.onrender.com
VITE_ENVIRONMENT=production
VITE_USE_MOCK_API=false
```

## 详细文档

完整部署指南请参考: [在线文档](#)
