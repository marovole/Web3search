# Cloudflare 免费部署指南

**完全免费，无需 GitHub Actions**

---

## 🎯 概述

本项目使用 Cloudflare 的原生部署方案，包括：
- **Cloudflare Workers** (Workers API) - 免费每天 100,000 请求
- **Cloudflare Pages** (Frontend) - 免费每月 500 次构建

---

## ✅ 已完成：GitHub Actions 已禁用

GitHub Actions 工作流已被禁用并备份到 `.github/workflows-disabled/`，以避免使用限制问题。

---

## 📦 方案 1: Workers API（手动部署）

### 当前状态
✅ 已部署并运行: https://web3search-api.marovole.workers.dev

### 手动部署命令
```bash
cd workers-api
npx wrangler deploy
```

### Git 自动部署（可选）

虽然 Cloudflare Workers 没有内置 Git 集成，但你可以使用以下免费方案：

#### 选项 A: 使用 Cloudflare Pages 的 Workers 路由
1. 访问 [Cloudflare Dashboard](https://dash.cloudflare.com)
2. 进入 **Workers & Pages** → **Create Application** → **Pages**
3. 选择 **Connect to Git**
4. 选择你的 GitHub 仓库 `Web3search`
5. 配置构建设置：
   - **Build command**: `cd workers-api && npm install && npm run build`
   - **Build output directory**: `workers-api/dist`
6. 在 **Functions** 标签下配置 Workers 路由

#### 选项 B: 使用 GitHub Actions（轻量级，免费）
创建 `.github/workflows/deploy-workers.yml`:

```yaml
name: Deploy Workers API

on:
  push:
    branches: [ main ]
    paths:
      - 'workers-api/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - name: Deploy to Cloudflare Workers
        run: |
          cd workers-api
          npm ci
          npx wrangler deploy
        env:
          CLOUDFLARE_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}
```

**注意**: 这个工作流非常轻量，在 GitHub 免费层限制内。

---

## 🌐 方案 2: Frontend（Cloudflare Pages Git 集成）

### 配置步骤

1. **登录 Cloudflare Dashboard**
   - 访问: https://dash.cloudflare.com
   - 进入 **Workers & Pages**

2. **创建 Pages 项目**
   - 点击 **Create Application** → **Pages**
   - 选择 **Connect to Git**

3. **连接 GitHub 仓库**
   - 授权 Cloudflare 访问你的 GitHub 账户
   - 选择仓库: `marovole/Web3search`

4. **配置构建设置**
   ```
   Project name: web3search
   Production branch: main
   Build command: cd frontend && npm install && npm run build
   Build output directory: frontend/dist
   Root directory: (leave empty)
   ```

5. **环境变量**（如需要）
   - `VITE_API_BASE_URL`: https://web3search-api.marovole.workers.dev
   - 其他 frontend 需要的环境变量

6. **保存并部署**
   - 点击 **Save and Deploy**
   - Cloudflare 会自动构建和部署

### 自动部署
✅ 配置完成后，每次 push 到 `main` 分支，Cloudflare Pages 会自动：
1. 检测到代码变更
2. 拉取最新代码
3. 运行构建命令
4. 部署到生产环境

### 部署 URL
- **Production**: `https://web3search.pages.dev`
- **Preview**: 每个 PR 会生成独立的预览 URL

---

## 🔗 方案 3: 自定义域名（可选）

### 配置自定义域名

1. 在 Cloudflare Pages 项目设置中：
   - 进入 **Custom domains**
   - 点击 **Set up a custom domain**
   - 输入你的域名（如 `web3search.com`）

2. Cloudflare 会自动配置 DNS 记录

3. 启用 HTTPS（自动）

---

## 🚀 完整部署流程

### 初次设置
1. ✅ Workers API 已部署（手动）
2. ⏳ Frontend 需要配置 Pages Git 集成（5分钟）
3. ⏳ （可选）配置自定义域名

### 日常开发
```bash
# 1. 开发和测试
git checkout -b feature/new-feature
# ... 编写代码 ...
npm test

# 2. 提交代码
git add .
git commit -m "feat: 新功能"
git push origin feature/new-feature

# 3. 创建 Pull Request
# Cloudflare Pages 会自动生成预览 URL

# 4. 合并到 main
# Cloudflare Pages 自动部署到生产环境

# 5. Workers API 需要手动部署（如有更改）
cd workers-api
npx wrangler deploy
```

---

## 🔍 验证部署

### Workers API
```bash
curl https://web3search-api.marovole.workers.dev/api/v1/health
```

预期响应:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-14T...",
  "database": {"status": "connected"},
  "cache": {"status": "available"}
}
```

### Frontend
访问: https://web3search.pages.dev

---

## 📊 成本对比

| 服务 | 方案 | 免费额度 | 成本 |
|------|------|----------|------|
| Workers API | Cloudflare Workers | 100,000 请求/天 | **$0** |
| Frontend | Cloudflare Pages | 500 构建/月 | **$0** |
| Database | Supabase | 500 MB 存储 | **$0** |
| **总计** | - | - | **$0/月** |

vs GitHub Actions（如果收费）: $0.008/分钟 × 每次部署约 5 分钟 × 每天 10 次 = ~$12/月

---

## 🛠️ 故障排查

### Workers API 部署失败
```bash
# 检查 wrangler 配置
cat workers-api/wrangler.toml

# 检查登录状态
npx wrangler whoami

# 重新登录
npx wrangler login
```

### Pages 构建失败
1. 检查 Cloudflare Dashboard 的构建日志
2. 验证构建命令是否正确
3. 确保环境变量已设置

### 域名配置问题
1. 确保域名的 DNS 托管在 Cloudflare
2. 检查 DNS 记录是否正确
3. 等待 DNS 传播（最多 24 小时）

---

## 📚 相关文档

- [Cloudflare Workers 文档](https://developers.cloudflare.com/workers/)
- [Cloudflare Pages 文档](https://developers.cloudflare.com/pages/)
- [Wrangler CLI 文档](https://developers.cloudflare.com/workers/wrangler/)

---

## 📝 更新日志

- **2025-11-14**: 初始版本，禁用 GitHub Actions，改用 Cloudflare 原生部署
- Workers API 已成功部署到生产环境
- Frontend 等待配置 Pages Git 集成

---

**维护者**: @marovole
**最后更新**: 2025-11-14
