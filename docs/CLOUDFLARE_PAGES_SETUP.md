# Cloudflare Pages 部署配置指南

本文档说明如何配置 Cloudflare Pages 以正确部署 Web3search 前端。

## 🚀 快速配置

### 1. 在 Cloudflare Dashboard 中创建项目

1. 登录 [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. 进入 **Workers & Pages** 页面
3. 点击 **Create application** → **Pages** → **Connect to Git**
4. 选择 GitHub 仓库: `marovole/Web3search`
5. 点击 **Begin setup**

### 2. 配置构建设置

在 **Build settings** 页面配置以下内容：

| 配置项 | 值 |
|--------|-----|
| **Framework preset** | None |
| **Build command** | `npm run build` |
| **Build output directory** | `frontend/dist` |
| **Root directory** | (留空) |

### 3. 配置环境变量

在 **Environment variables** 部分添加:

| 变量名 | 值 | 说明 |
|--------|-----|------|
| `NODE_VERSION` | `18` | Node.js 版本 |
| `VITE_API_BASE_URL` | `https://web3search-api.onrender.com` | 后端 API 地址 |
| `VITE_ENVIRONMENT` | `production` | 环境类型 |
| `VITE_USE_MOCK_API` | `false` | 禁用 Mock API |

### 4. 保存并部署

点击 **Save and Deploy**，等待构建完成。

---

## 📋 详细配置说明

### 项目结构

```
Web3search/
├── package.json          # 根目录 package.json (新增)
├── wrangler.toml        # Cloudflare Pages 配置 (新增)
├── frontend/            # 前端代码目录
│   ├── package.json     # 前端 package.json
│   ├── dist/           # 构建输出 (自动生成)
│   ├── public/
│   │   └── _redirects  # 重定向规则
│   └── functions/
│       └── _middleware.ts  # API 代理
└── scripts/
    └── smoke-test.js   # 部署后烟雾测试
```

### 构建流程

1. **安装依赖**: Cloudflare Pages 在根目录执行 `npm install`
2. **运行构建**: 执行 `npm run build` → `cd frontend && npm run build`
3. **输出检查**: 检查 `frontend/dist` 目录
4. **部署**: 上传 `frontend/dist` 到 CDN

### 环境变量详解

#### NODE_VERSION
- **必需**: 是
- **说明**: 指定 Node.js 版本
- **推荐值**: `18` (LTS 版本)

#### VITE_API_BASE_URL
- **必需**: 是
- **说明**: 后端 API 基础 URL
- **生产环境**: `https://web3search-api.onrender.com`
- **注意**: 不要包含 `/api` 路径前缀

#### VITE_ENVIRONMENT
- **必需**: 是
- **说明**: 应用运行环境
- **可选值**: `development`, `staging`, `production`
- **生产环境**: `production`

#### VITE_USE_MOCK_API
- **必需**: 否
- **说明**: 是否使用 Mock API
- **生产环境**: `false`

---

## 🔧 高级配置

### 自定义域名

1. 在 Cloudflare Pages 项目页面
2. 进入 **Custom domains** 标签
3. 点击 **Set up a custom domain**
4. 输入域名并按照指示配置 DNS

### 分支预览

Cloudflare Pages 自动为每个分支创建预览环境:

- **生产分支**: `main` → `https://web3search.pages.dev`
- **预览分支**: `dev` → `https://dev.web3search.pages.dev`
- **PR 预览**: 自动为 PR 创建临时预览环境

### Functions (API 代理)

项目已包含 Functions 配置:

**文件**: `frontend/functions/_middleware.ts`

**功能**:
- 代理所有 `/api/*` 请求到后端
- 自动添加 CORS 头部
- 处理请求转发

**测试**:
```bash
# 测试 API 代理
curl https://web3search.pages.dev/api/health
```

---

## 🐛 故障排除

### 问题 1: 构建失败 - 找不到 package.json

**错误信息**:
```
npm error enoent Could not read package.json
```

**解决方案**:
- 确保根目录存在 `package.json` ✅
- 确保 `package.json` 包含 `build` 脚本 ✅

### 问题 2: 构建失败 - 模块未找到

**错误信息**:
```
Error: Cannot find module 'xxx'
```

**解决方案**:
1. 检查 `frontend/package.json` 依赖项
2. 在本地运行 `cd frontend && npm ci && npm run build` 测试
3. 确保 `package-lock.json` 已提交

### 问题 3: 页面显示 404

**可能原因**:
- `_redirects` 文件未正确配置
- SPA 路由规则缺失

**解决方案**:
检查 `frontend/public/_redirects`:
```
/api/v1/*  https://web3search-api.onrender.com/api/v1/:splat  200
/*         /index.html                                         200
```

### 问题 4: API 请求失败

**可能原因**:
- CORS 配置错误
- API 代理未工作
- 后端 URL 配置错误

**解决方案**:
1. 检查环境变量 `VITE_API_BASE_URL`
2. 验证 Functions 中间件正常工作
3. 查看浏览器控制台日志

---

## ✅ 部署验证清单

部署完成后，运行以下检查:

- [ ] 访问首页: https://web3search.pages.dev
- [ ] 检查构建日志无错误
- [ ] 运行烟雾测试:
  ```bash
  FRONTEND_URL=https://web3search.pages.dev \
  BACKEND_URL=https://web3search-api.onrender.com \
  node scripts/smoke-test.js
  ```
- [ ] 测试 Quick Chat 功能
- [ ] 测试页面导航 (/history, /watchlist)
- [ ] 检查浏览器控制台无错误
- [ ] 验证 API 请求通过代理正常工作

---

## 📚 相关文档

- [部署指南](./DEPLOYMENT.md)
- [故障排除指南](./TROUBLESHOOTING.md)
- [Cloudflare Pages 官方文档](https://developers.cloudflare.com/pages/)
- [Cloudflare Functions 文档](https://developers.cloudflare.com/pages/platform/functions/)

---

## 🔄 更新部署

推送代码到 `main` 分支会自动触发部署:

```bash
git add .
git commit -m "feat: 添加新功能"
git push origin main
```

查看部署状态:
- Cloudflare Dashboard → Pages → 项目 → Deployments
- 或查看 GitHub Actions (如果配置了 webhook)

---

**最后更新**: 2025-11-08
