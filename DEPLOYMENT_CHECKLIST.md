# ✅ Cloudflare 部署检查清单

## 📋 已准备就绪

### ✅ 代码配置（已完成）
- [x] Cloudflare Pages配置文件（_redirects, _headers）
- [x] Cloudflare Workers项目结构
- [x] GitHub Actions CI/CD工作流
- [x] 前端构建脚本和依赖
- [x] 后端CORS配置更新
- [x] TypeScript类型检查通过
- [x] 生产构建测试通过

### ✅ 账号信息（已获取）
- [x] Cloudflare Account ID: (已配置到 workers/wrangler.toml)
- [x] Cloudflare API Token: (已提供，需配置到 GitHub Secrets)

---

## 🚀 下一步操作（需手动完成）

### 步骤1：配置 GitHub Secrets（5分钟）

1. **打开 GitHub 仓库设置**
   ```
   访问：https://github.com/marovole/Web3search/settings/secrets/actions
   ```

2. **添加第一个 Secret**
   - 点击 **New repository secret**
   - Name: `CLOUDFLARE_ACCOUNT_ID`
   - Secret: `[您的 Account ID - 32位字符]`
   - 点击 **Add secret**

3. **添加第二个 Secret**
   - 点击 **New repository secret**
   - Name: `CLOUDFLARE_API_TOKEN`
   - Secret: `[您的 API Token]`
   - 点击 **Add secret**

✅ **完成后应该看到两个 Secrets：**
   - `CLOUDFLARE_ACCOUNT_ID`
   - `CLOUDFLARE_API_TOKEN`

---

### 步骤2：推送代码到 GitHub（1分钟）

```bash
cd /Users/marovole/GitHub/Web3search
git push origin main
```

这将触发自动部署！

---

### 步骤3：创建 Cloudflare Pages 项目（5分钟）

#### 选项A：通过 Cloudflare Dashboard（推荐）

1. **访问 Cloudflare Pages**
   ```
   https://dash.cloudflare.com/[YOUR_ACCOUNT_ID]/pages
   ```
   或直接访问：https://dash.cloudflare.com/ 然后点击 **Workers & Pages**

2. **创建项目**
   - 点击 **Create a project**
   - 选择 **Connect to Git**

3. **连接 GitHub**
   - 授权 Cloudflare 访问 GitHub
   - 选择仓库：`marovole/Web3search`

4. **配置构建设置**
   ```
   Project name: web3search
   Production branch: main
   Framework preset: Vite
   Build command: cd frontend && npm install && npm run build
   Build output directory: frontend/dist
   Root directory: (留空)
   ```

5. **配置环境变量**
   点击 **Environment variables (advanced)**，添加：
   ```
   VITE_ENVIRONMENT = production
   VITE_API_BASE_URL = https://web3search-api.onrender.com
   VITE_USE_MOCK_API = false
   VITE_ENABLE_PERFORMANCE_MONITORING = true
   VITE_DEBUG_MODE = false
   ```

6. **保存并部署**
   - 点击 **Save and Deploy**
   - 等待3-5分钟完成首次构建

#### 选项B：通过 Wrangler CLI（开发者选项）

```bash
cd frontend

# 安装 wrangler（如未安装）
npm install -g wrangler

# 登录 Cloudflare
wrangler login

# 部署到 Cloudflare Pages
npm run cf:deploy

# 或手动部署
wrangler pages deploy dist --project-name=web3search
```

---

### 步骤4：验证部署（2分钟）

#### 等待部署完成后：

1. **获取部署 URL**
   - Cloudflare Pages Dashboard 会显示
   - 格式：`https://web3search.pages.dev`

2. **测试前端**
   ```bash
   curl https://web3search.pages.dev
   ```
   应该返回 HTML 内容

3. **测试 API 代理**
   ```bash
   curl https://web3search.pages.dev/api/health
   ```
   应该返回：
   ```json
   {
     "status": "healthy",
     "database": "connected",
     "redis": "connected"
   }
   ```

4. **测试 Quick Chat（可选）**
   ```bash
   curl -X POST https://web3search.pages.dev/api/v1/chat/quick \
     -H "Content-Type: application/json" \
     -d '{"query": "What is Bitcoin?", "stream": false}'
   ```

5. **浏览器访问**
   ```
   https://web3search.pages.dev
   ```
   应该能看到完整的前端界面

---

### 步骤5：更新后端 CORS（2分钟）

1. **登录 Render Dashboard**
   ```
   https://dashboard.render.com/
   ```

2. **选择后端服务**
   - 找到 `web3search-api` 服务

3. **更新环境变量**
   - 找到 `CORS_ORIGINS` 环境变量
   - 当前值：
     ```
     https://web3search.pages.dev,https://web3search.ai,https://www.web3search.ai,https://api.web3search.ai
     ```
   - 确认包含 `https://web3search.pages.dev`

4. **保存并重启**
   - 保存更改
   - 服务会自动重启

---

## 🎯 可选步骤（后续优化）

### 步骤6：部署 Cloudflare Workers（可选，15分钟）

如果需要边缘缓存和更好的性能：

```bash
cd workers

# 安装依赖
npm install

# 登录（如未登录）
npx wrangler login

# wrangler.toml 中的 account_id 已配置

# 创建 KV 命名空间（用于缓存）
npx wrangler kv:namespace create "CACHE"

# 部署 Worker
npm run deploy

# 或部署到生产环境
npm run deploy:prod
```

---

### 步骤7：配置自定义域名（可选，10分钟）

如果有自己的域名（如 `web3search.ai`）：

1. **添加域名到 Cloudflare**
   - Websites → Add a site
   - 输入域名并完成 DNS 迁移

2. **配置 Pages 自定义域名**
   - Pages → web3search → Custom domains
   - 点击 **Set up a custom domain**
   - 输入域名（如 `www.web3search.ai`）
   - Cloudflare 自动配置 DNS

3. **更新后端 CORS**
   - 在 Render 中添加新域名到 `CORS_ORIGINS`

---

## 📊 监控和验证

### GitHub Actions 状态

访问查看自动部署状态：
```
https://github.com/marovole/Web3search/actions
```

应该看到：
- ✅ Deploy to Cloudflare Pages (如果推送了代码)
- 构建和部署日志

### Cloudflare Pages 部署

访问查看部署历史：
```
https://dash.cloudflare.com/[YOUR_ACCOUNT_ID]/pages/view/web3search
```
或通过 Dashboard → Workers & Pages → web3search

每次部署都会显示：
- 构建日志
- 部署状态
- 预览 URL
- 生产 URL

### 性能测试

```bash
# Lighthouse 测试
cd frontend
npm run test:lighthouse

# 或使用在线工具
# https://pagespeed.web.dev/
```

目标评分：
- Performance: > 90
- Accessibility: > 90
- Best Practices: > 90
- SEO: > 90

---

## 🆘 故障排查

### 问题1：GitHub Actions 失败

**检查**：
- Secrets 是否正确配置
- Account ID 和 API Token 是否有效

**解决**：
```bash
# 查看 Actions 日志
https://github.com/marovole/Web3search/actions

# 重新运行失败的工作流
# 点击 Re-run failed jobs
```

### 问题2：Cloudflare 构建失败

**检查**：
- 构建命令是否正确
- 环境变量是否配置
- Node 版本是否正确（应该是 18）

**解决**：
- 查看 Cloudflare Pages 的构建日志
- 确认构建命令：`cd frontend && npm install && npm run build`
- 确认输出目录：`frontend/dist`

### 问题3：API 请求失败（CORS 错误）

**检查**：
```bash
# 测试后端 CORS
curl -H "Origin: https://web3search.pages.dev" \
     -H "Access-Control-Request-Method: POST" \
     -X OPTIONS \
     https://web3search-api.onrender.com/api/v1/chat/quick
```

**解决**：
- 确认 Render 后端的 `CORS_ORIGINS` 包含 Cloudflare Pages URL
- 重启 Render 服务

### 问题4：环境变量不生效

**检查**：
- 变量名是否以 `VITE_` 开头
- 是否在 Cloudflare Pages 设置中配置

**解决**：
- 重新配置环境变量
- 触发重新部署（Retry deployment）

---

## ✅ 完成检查清单

部署完成后，确认以下项目：

- [ ] GitHub Secrets 已配置（2个）
- [ ] 代码已推送到 GitHub
- [ ] Cloudflare Pages 项目已创建
- [ ] 环境变量已配置
- [ ] 首次部署成功
- [ ] 前端 URL 可访问
- [ ] API 代理正常工作
- [ ] Quick Chat 功能正常
- [ ] Deep Research 功能正常
- [ ] 后端 CORS 已更新
- [ ] GitHub Actions 工作流正常
- [ ] 性能测试通过（可选）

---

## 🎉 部署完成！

完成以上步骤后，您的 Web3 Search 将部署到：

**前端**: https://web3search.pages.dev  
**后端**: https://web3search-api.onrender.com  
**全球**: Cloudflare 200+ 数据中心

---

## 📚 相关文档

- [快速开始指南](../QUICKSTART_CLOUDFLARE.md)
- [完整部署指南](../CLOUDFLARE_DEPLOYMENT.md)
- [Account ID 获取指南](./CLOUDFLARE_ACCOUNT_ID_GUIDE.md)
- [故障排查指南](../CLOUDFLARE_DEPLOYMENT.md#故障排查)

---

**创建时间**: 2025-11-04  
**最后更新**: 2025-11-04
