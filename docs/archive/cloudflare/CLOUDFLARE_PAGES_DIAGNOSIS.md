# Cloudflare Pages 部署问题诊断

**问题**: https://web3search.pages.dev/ 无法访问，但部署记录显示成功

**诊断时间**: 2025-11-08

---

## 🔍 问题分析

### 1. SSL 连接错误
从诊断脚本的输出看，网站返回 SSL 连接错误：
```
LibreSSL SSL_connect: SSL_ERROR_SYSCALL in connection to web3search.pages.dev:443
```

这可能表示：
- Cloudflare Pages 项目未正确部署
- DNS 配置有问题
- SSL 证书未正确配置
- 构建失败但显示为成功

### 2. 已完成的修复

✅ **创建了 `_headers` 文件**
- 位置: `frontend/public/_headers`
- 包含安全头部和缓存策略
- Cloudflare Pages 会自动识别此文件

✅ **更新了 `_redirects` 文件**
- 位置: `frontend/public/_redirects`
- 添加了 API 路由代理
- 确保 SPA 路由正常工作

---

## 📋 需要检查的步骤

### 步骤 1: 检查 Cloudflare Dashboard

1. **登录 Cloudflare Dashboard**
   - 访问: https://dash.cloudflare.com/
   - 进入 **Workers & Pages** → **Pages**

2. **找到 web3search 项目**
   - 点击项目名称进入详情页

3. **检查最新部署状态**
   - 查看 **Deployments** 标签
   - 检查最新部署的状态：
     - ✅ **Success** - 部署成功
     - ❌ **Failed** - 部署失败（查看日志）
     - ⏳ **Building** - 正在构建

### 步骤 2: 检查构建配置

在 Cloudflare Pages 项目设置中，确认以下配置：

**构建设置**:
```
项目名称: web3search
生产分支: main
框架预设: Vite
构建命令: cd frontend && npm install && npm run build
构建输出目录: frontend/dist
根目录: (留空)
Node.js 版本: 18
```

**环境变量**:
```
VITE_ENVIRONMENT=production
VITE_API_BASE_URL=https://web3search-api.onrender.com
VITE_USE_MOCK_API=false
VITE_ENABLE_PERFORMANCE_MONITORING=true
VITE_DEBUG_MODE=false
```

### 步骤 3: 查看构建日志

如果部署失败，查看构建日志中的错误：

1. 点击失败的部署
2. 查看 **Build Logs**
3. 常见错误：
   - **找不到文件**: 检查构建命令路径
   - **依赖安装失败**: 检查 package.json
   - **构建超时**: 增加构建时间限制
   - **内存不足**: 升级构建计划

### 步骤 4: 手动触发重新部署

如果配置正确但网站仍无法访问：

1. **通过 Dashboard**:
   - 进入项目 → **Deployments**
   - 点击 **Retry deployment** 或 **Create deployment**

2. **通过 Git 推送**:
   ```bash
   git add .
   git commit -m "fix: 更新 Cloudflare Pages 配置"
   git push origin main
   ```

3. **通过 Wrangler CLI**:
   ```bash
   cd frontend
   npm run build
   wrangler pages deploy dist --project-name=web3search
   ```

---

## 🔧 常见问题解决方案

### 问题 1: 构建输出目录错误

**症状**: 部署成功但网站返回 404

**解决**:
- 确认构建输出目录为 `frontend/dist`
- 检查 `frontend/dist/index.html` 是否存在
- 确认 `_redirects` 和 `_headers` 文件在构建输出中

### 问题 2: SPA 路由不工作

**症状**: 直接访问路由（如 `/chat`）返回 404

**解决**:
- 确认 `_redirects` 文件包含 `/* /index.html 200`
- 检查文件是否在 `frontend/public/` 目录
- 确认文件被复制到构建输出

### 问题 3: API 请求失败

**症状**: API 请求返回 CORS 错误或 404

**解决**:
- 检查 `_redirects` 文件中的 API 路由配置
- 确认后端 CORS 配置包含 `https://web3search.pages.dev`
- 检查后端服务是否正常运行

### 问题 4: 环境变量未生效

**症状**: 应用使用默认配置而非生产配置

**解决**:
- 确认环境变量名以 `VITE_` 开头
- 在 Cloudflare Pages 设置中重新添加环境变量
- 触发重新部署

---

## 🧪 验证步骤

部署完成后，运行以下命令验证：

```bash
# 1. 检查网站可访问性
curl -I https://web3search.pages.dev

# 2. 检查首页内容
curl https://web3search.pages.dev | head -20

# 3. 检查 API 代理
curl https://web3search.pages.dev/api/health

# 4. 检查 SPA 路由
curl -I https://web3search.pages.dev/chat
```

预期结果：
- ✅ 首页返回 200 状态码和 HTML 内容
- ✅ API 代理返回后端响应
- ✅ SPA 路由返回 200 状态码（不是 404）

---

## 📝 配置文件检查清单

部署前确认以下文件存在且正确：

- [x] `frontend/public/_redirects` - SPA 路由和 API 代理
- [x] `frontend/public/_headers` - 安全头部和缓存策略
- [x] `frontend/vite.config.ts` - 构建配置
- [x] `frontend/package.json` - 依赖和脚本
- [ ] Cloudflare Pages 项目配置正确
- [ ] 环境变量已配置
- [ ] 构建命令和输出目录正确

---

## 🚀 下一步操作

1. **立即检查**: 登录 Cloudflare Dashboard 查看部署状态和日志
2. **修复配置**: 根据日志错误修复构建配置
3. **重新部署**: 触发新的部署
4. **验证访问**: 等待部署完成后验证网站可访问性

---

## 📞 需要帮助？

如果问题仍然存在，请提供：
1. Cloudflare Dashboard 中的构建日志截图
2. 最新部署的状态（成功/失败）
3. 构建日志中的具体错误信息
4. 浏览器控制台中的错误信息（如果有）

---

**最后更新**: 2025-11-08

