# Cloudflare Pages + Workers 部署指南

## 📋 概述

本指南提供将Web3 Search前端部署到Cloudflare Pages以及可选配置Workers边缘层的详细步骤。

---

## 🚀 第一部分：Cloudflare Pages 前端部署

### 前置条件

- ✅ Cloudflare账号
- ✅ GitHub仓库访问权限
- ✅ Cloudflare API Token（已提供）
- ✅ 后端API已在Render上运行

### 步骤1：创建Cloudflare Pages项目

1. 登录 [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. 在左侧菜单选择 **Pages**
3. 点击 **Create a project** → **Connect to Git**
4. 授权Cloudflare访问GitHub账号
5. 选择仓库：`marovole/Web3search`

### 步骤2：配置构建设置

在配置页面填写以下信息：

**项目名称**：
```
web3search
```

**生产分支**：
```
main
```

**框架预设**：
```
Vite
```

**构建命令**：
```
cd frontend && npm install && npm run build
```

**构建输出目录**：
```
frontend/dist
```

**根目录（可选）**：
```
/
```
> 如果设置为 `frontend`，则构建命令改为 `npm install && npm run build`，输出目录改为 `dist`

**Node.js 版本**：
```
18
```

### 步骤3：配置环境变量

在 **Environment variables** 部分添加：

| 变量名 | 值 | 说明 |
|--------|-----|------|
| `VITE_ENVIRONMENT` | `production` | 环境标识 |
| `VITE_API_BASE_URL` | `https://web3search-api.onrender.com` | 后端API地址 |
| `VITE_USE_MOCK_API` | `false` | 禁用Mock API |
| `VITE_ENABLE_SENTRY` | `false` | 禁用Sentry（可选开启） |
| `VITE_ENABLE_ANALYTICS` | `false` | 禁用分析（可选开启） |
| `VITE_ENABLE_PERFORMANCE_MONITORING` | `true` | 启用性能监控 |
| `VITE_DEBUG_MODE` | `false` | 禁用调试模式 |

### 步骤4：触发首次部署

1. 点击 **Save and Deploy**
2. Cloudflare将自动：
   - 克隆仓库
   - 安装依赖
   - 运行构建命令
   - 部署到全球CDN

**预计构建时间**：3-5分钟

### 步骤5：验证部署

部署完成后，您将获得：
- **生产URL**：`https://web3search.pages.dev`
- **预览URL**：`https://<commit-hash>.web3search.pages.dev`

测试部署：
```bash
# 健康检查
curl https://web3search.pages.dev

# 测试API代理
curl https://web3search.pages.dev/api/health
```

---

## 🔧 第二部分：Cloudflare Workers 边缘层（可选）

### 为什么使用Workers？

- **边缘缓存**：在全球CDN节点缓存API响应
- **速率限制**：防止API滥用
- **请求优化**：压缩、转换请求格式
- **安全增强**：添加额外的安全层

### 步骤1：安装Wrangler CLI

```bash
# 全局安装
npm install -g wrangler

# 或在workers目录本地安装
cd workers
npm install
```

### 步骤2：登录Cloudflare

```bash
wrangler login
```

这将打开浏览器进行授权。

### 步骤3：获取Account ID

1. 登录 [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. 在右侧栏找到 **Account ID**
3. 复制Account ID

### 步骤4：配置wrangler.toml

编辑 `workers/wrangler.toml`，替换占位符：

```toml
name = "web3search-worker"
main = "src/index.ts"
compatibility_date = "2025-01-01"
account_id = "<YOUR_ACCOUNT_ID>"  # 替换为实际的Account ID
workers_dev = true
```

### 步骤5：创建KV命名空间（用于缓存）

```bash
cd workers

# 创建生产环境KV
wrangler kv:namespace create "CACHE"

# 创建预览环境KV（可选）
wrangler kv:namespace create "CACHE" --preview
```

记录返回的KV namespace ID，更新 `wrangler.toml`：

```toml
[[kv_namespaces]]
binding = "CACHE"
id = "<YOUR_KV_NAMESPACE_ID>"
preview_id = "<YOUR_PREVIEW_KV_NAMESPACE_ID>"
```

### 步骤6：部署Worker

```bash
cd workers

# 部署到开发环境（测试）
wrangler deploy

# 部署到生产环境
wrangler deploy --env production
```

### 步骤7：配置自定义路由（可选）

如果您有自定义域名，可以配置路由：

1. 在 `wrangler.toml` 中添加：
```toml
[env.production]
route = "api.web3search.ai/*"
```

2. 或在Cloudflare Dashboard中配置：
   - **Workers & Pages** → **web3search-worker**
   - **Triggers** → **Add route**
   - 输入：`api.web3search.ai/*`

### 步骤8：测试Worker

```bash
# 测试健康检查
curl https://web3search-worker.<your-subdomain>.workers.dev/health

# 测试缓存
curl -i https://web3search-worker.<your-subdomain>.workers.dev/api/v1/chat/quick \
  -H "Content-Type: application/json" \
  -d '{"query": "What is Bitcoin?"}'

# 检查X-Cache头，第一次应该是MISS，第二次是HIT
```

---

## 🔄 第三部分：CI/CD 自动化部署

### GitHub Actions配置

已创建 `.github/workflows/cloudflare-deploy.yml`，自动执行：
- TypeScript类型检查
- ESLint代码检查
- 单元测试
- 构建
- 部署到Cloudflare Pages

### 配置GitHub Secrets

在GitHub仓库设置中添加：

1. **Settings** → **Secrets and variables** → **Actions**
2. 添加以下secrets：

| Secret名称 | 值 | 获取方式 |
|------------|-----|----------|
| `CLOUDFLARE_API_TOKEN` | `2Oke144eQdRcMmzKYZRedEPXDVck3Lk9CDJ6W_jM` | 已提供 |
| `CLOUDFLARE_ACCOUNT_ID` | `<Your Account ID>` | Cloudflare Dashboard右侧栏 |

### 触发自动部署

```bash
# 推送到main分支自动触发
git add .
git commit -m "feat: add Cloudflare deployment configuration"
git push origin main

# 或手动触发
# GitHub → Actions → Deploy to Cloudflare Pages → Run workflow
```

---

## 🧪 第四部分：本地测试

### 测试前端构建

```bash
cd frontend

# TypeScript类型检查
npm run type-check

# ESLint检查
npm run lint

# 运行测试
npm run test:ci

# 生产构建
npm run build

# 预览构建结果
npm run preview
```

访问 http://localhost:3000 验证构建结果。

### 测试Cloudflare Pages本地

```bash
cd frontend

# 使用Wrangler预览
npm run cf:preview
```

访问 http://localhost:8788 验证Pages功能。

### 测试Worker本地

```bash
cd workers

# 启动Worker开发服务器
npm run dev
```

访问 http://localhost:8787 验证Worker功能。

---

## 📊 第五部分：性能验证

### Lighthouse测试

```bash
cd frontend

# 运行Lighthouse
npm run test:lighthouse
```

**目标评分**：
- Performance: > 90
- Accessibility: > 90
- Best Practices: > 90
- SEO: > 90

### 端到端测试

```bash
cd frontend

# 设置测试环境变量
export VITE_API_BASE_URL=https://web3search.pages.dev

# 运行E2E测试
npm run test:e2e
```

### 负载测试

```bash
cd backend/tests/load

# 针对Cloudflare Pages前端
python locustfile.py --host=https://web3search.pages.dev
```

---

## 🔐 第六部分：安全配置

### 1. 验证HTTP头部

```bash
curl -I https://web3search.pages.dev
```

检查以下头部是否存在：
- ✅ `X-Frame-Options: DENY`
- ✅ `X-Content-Type-Options: nosniff`
- ✅ `X-XSS-Protection: 1; mode=block`
- ✅ `Referrer-Policy: strict-origin-when-cross-origin`
- ✅ `Content-Security-Policy: ...`

### 2. 配置访问策略（可选）

在Cloudflare Dashboard：
1. **Security** → **WAF**
2. 创建规则：
   - 限制请求频率
   - 阻止恶意IP
   - 地理位置限制

### 3. 启用Bot保护

1. **Security** → **Bots**
2. 启用 **Bot Fight Mode**

---

## 🌐 第七部分：自定义域名（可选）

### 步骤1：添加域名到Cloudflare

1. **Websites** → **Add a site**
2. 输入域名：`web3search.ai`
3. 选择免费计划
4. 更新DNS服务器到Cloudflare提供的地址

### 步骤2：配置Pages自定义域名

1. **Pages** → **web3search** → **Custom domains**
2. 点击 **Set up a custom domain**
3. 输入：`www.web3search.ai` 或 `web3search.ai`
4. Cloudflare自动配置DNS

### 步骤3：启用SSL/TLS

1. **SSL/TLS** → **Overview**
2. 选择 **Full (strict)**
3. 等待SSL证书生成（通常几分钟内完成）

### 步骤4：更新后端CORS

已在 `backend/render.yaml` 中添加域名，需要在Render Dashboard更新：

```
https://web3search.pages.dev,https://web3search.ai,https://www.web3search.ai
```

---

## 📝 第八部分：故障排查

### 构建失败

**问题**：构建命令找不到文件
```
Error: ENOENT: no such file or directory
```

**解决**：
- 检查构建命令中的路径：`cd frontend && ...`
- 或设置根目录为 `frontend`，移除 `cd frontend`

### API请求失败

**问题**：CORS错误
```
Access-Control-Allow-Origin header is missing
```

**解决**：
1. 确认后端CORS配置包含Cloudflare域名
2. 检查 `_redirects` 文件配置是否正确
3. 清除浏览器缓存

### 环境变量未生效

**问题**：运行时无法获取环境变量

**解决**：
1. 确认变量名以 `VITE_` 开头
2. 在Cloudflare Pages设置中重新添加
3. 触发重新部署

### Worker部署失败

**问题**：Account ID错误
```
Error: Unknown Account
```

**解决**：
1. 检查 `wrangler.toml` 中的 `account_id`
2. 运行 `wrangler whoami` 确认登录状态

---

## 📚 参考资源

### Cloudflare文档
- [Pages Documentation](https://developers.cloudflare.com/pages/)
- [Workers Documentation](https://developers.cloudflare.com/workers/)
- [Wrangler CLI](https://developers.cloudflare.com/workers/wrangler/)

### 项目文档
- [前端README](frontend/README.md)
- [测试指南](docs/testing-guide.md)
- [API文档](backend/app/docs/)

### 有用命令

```bash
# Cloudflare Pages
wrangler pages list
wrangler pages deployment list --project-name=web3search

# Cloudflare Workers
wrangler tail web3search-worker
wrangler logs web3search-worker

# 查看部署状态
curl https://web3search.pages.dev/health
```

---

## ✅ 验收清单

部署完成后，确认以下项目：

- [ ] 前端成功部署到Cloudflare Pages
- [ ] 访问 `https://web3search.pages.dev` 正常
- [ ] 所有页面路由正常工作（SPA路由）
- [ ] API请求正确转发到Render后端
- [ ] Quick Chat功能正常
- [ ] Deep Research功能正常
- [ ] 所有安全头部正确配置
- [ ] Lighthouse性能评分 > 90
- [ ] CI/CD自动部署工作流运行成功
- [ ] Worker部署成功（如果配置）
- [ ] 缓存策略生效（如果配置Worker）

---

## 🎉 部署成功！

恭喜！您的Web3 Search前端现已部署到Cloudflare全球CDN网络。

**下一步**：
1. 配置自定义域名（可选）
2. 启用分析和监控
3. 优化缓存策略
4. 进行负载测试

**支持**：
如遇问题，请查看：
- Cloudflare Dashboard日志
- GitHub Actions工作流日志
- 本文档的故障排查部分

---

**文档版本**：1.0.0  
**最后更新**：2025-11-04  
**维护者**：Web3 Search Team
