# Cloudflare Pages 部署配置指南

**最后更新**: 2025-11-08  
**状态**: 🔧 需要修复构建配置

---

## 🚨 当前问题

**症状**: 
- ✅ 部署显示成功
- ❌ 访问 `https://web3search.pages.dev` 显示 `ERR_CONNECTION_CLOSED`
- ❌ 页面无法加载

**原因**: 构建配置不正确，导致文件未正确部署

---

## ✅ 正确的构建配置

### 在 Cloudflare Dashboard 中设置

1. **登录 Cloudflare Dashboard**
   - URL: https://dash.cloudflare.com/
   - 进入: Workers 和 Pages → web3search

2. **Settings → Builds & deployments**

   配置如下:

   | 设置项 | 值 |
   |--------|-----|
   | **Framework preset** | `None` 或 `Vite` |
   | **Build command** | `cd frontend && npm ci && npm run build` |
   | **Build output directory** | `frontend/dist` |
   | **Root directory** | 留空 (使用项目根目录) |

3. **Settings → Environment variables**

   添加以下环境变量:

   | 变量名 | 值 | 说明 |
   |--------|-----|------|
   | `NODE_VERSION` | `18` | Node.js 版本 |
   | `VITE_API_BASE_URL` | `/api` | API 基础 URL |
   | `VITE_ENVIRONMENT` | `production` | 环境标识 |

---

## 📁 项目结构

```
Web3search/
├── frontend/              ← 前端代码目录
│   ├── src/              ← React 源代码
│   ├── public/           ← 静态资源
│   │   ├── _redirects   ← Cloudflare Pages 重定向规则
│   │   ├── _headers     ← 安全头部配置
│   │   └── test.html    ← 部署测试页面
│   ├── functions/        ← Cloudflare Pages Functions
│   │   └── _middleware.ts ← API 代理中间件
│   ├── dist/             ← 构建输出 (部署此目录)
│   ├── package.json
│   └── vite.config.ts
└── backend/              ← 后端代码 (独立部署到 Render.com)
```

---

## 🔧 修复步骤

### 步骤 1: 更新 Cloudflare 构建配置

1. 登录 Cloudflare Dashboard
2. 进入项目设置: Workers 和 Pages → web3search → Settings → Builds & deployments
3. 点击 "Configure Production deployments" 或 "Edit configuration"
4. 修改配置:
   ```
   Build command: cd frontend && npm ci && npm run build
   Build output directory: frontend/dist
   Root directory: (留空)
   ```
5. 保存配置

### 步骤 2: 添加环境变量

1. 进入 Settings → Environment variables
2. 点击 "Add variable"
3. 添加:
   - `NODE_VERSION` = `18`
   - `VITE_API_BASE_URL` = `/api`
   - `VITE_ENVIRONMENT` = `production`

### 步骤 3: 触发重新部署

**选项 A: 在 Dashboard 中重试**
1. 进入 Deployments
2. 找到最新的部署
3. 点击 "···" → "Retry deployment"

**选项 B: 推送新提交**
```bash
cd /Users/marovole/GitHub/Web3search
git add .
git commit -m "fix: 修复 Cloudflare Pages 构建配置"
git push origin main
```

### 步骤 4: 验证部署

1. **查看构建日志**:
   - Deployments → 最新部署 → "View build log"
   - 确认构建成功，没有错误

2. **检查部署文件**:
   - 查看日志中是否提到 `frontend/dist` 目录
   - 确认文件被正确上传

3. **测试访问**:
   ```bash
   # 测试部署测试页面
   curl -I https://web3search.pages.dev/test.html
   
   # 应该返回 200 OK
   
   # 测试主页
   curl -I https://web3search.pages.dev/
   
   # 应该返回 200 OK
   ```

4. **浏览器测试**:
   - 访问 `https://web3search.pages.dev/test.html`
   - 应该看到测试页面
   - 访问 `https://web3search.pages.dev/`
   - 应该看到完整的应用界面

---

## 🔍 诊断工具

### 测试基础部署

访问测试页面验证部署:
```
https://web3search.pages.dev/test.html
```

如果测试页面能正常显示，说明基础部署正常，问题可能在于:
- SPA 路由配置
- JavaScript 加载问题
- API 代理配置

### 检查构建日志

关键信息:
```
✔ Building application...
✔ Uploading... (XXX files)
✔ Deployment complete
```

确保看到:
- 构建命令正确执行
- 文件从 `frontend/dist` 上传
- 没有构建错误

### 使用 curl 测试

```bash
# 1. 测试主页
curl -I https://web3search.pages.dev/

# 2. 测试静态资源
curl -I https://web3search.pages.dev/test.html

# 3. 测试 API 代理
curl https://web3search.pages.dev/api/health

# 4. 查看完整响应
curl -v https://web3search.pages.dev/
```

---

## 📊 预期结果

### 成功的部署应该显示:

1. **构建日志**:
   ```
   13:45:32.123 | Cloning repository...
   13:45:35.456 | Installing dependencies...
   13:45:45.789 | Building application...
   13:46:15.012 | Success: Uploading 986 files
   13:46:20.345 | Success: Deployment complete!
   ```

2. **文件列表**:
   ```
   frontend/dist/
   ├── index.html
   ├── _redirects
   ├── _headers
   ├── test.html
   ├── js/
   ├── css/
   └── ...
   ```

3. **访问测试**:
   - ✅ https://web3search.pages.dev/test.html → 显示测试页面
   - ✅ https://web3search.pages.dev/ → 显示应用界面
   - ✅ https://web3search.pages.dev/api/health → 返回后端健康状态

---

## 🆘 故障排除

### 问题 1: 仍然无法访问

**可能原因**:
- 构建配置未保存
- 缓存问题

**解决方案**:
1. 清除浏览器缓存
2. 使用隐私/无痕模式测试
3. 使用 curl 测试（避免浏览器缓存）
4. 在 Cloudflare Dashboard 中 "Purge cache"

### 问题 2: 构建失败

**可能原因**:
- 构建命令路径错误
- 依赖安装失败
- 环境变量缺失

**解决方案**:
1. 检查构建日志的详细错误信息
2. 确认构建命令: `cd frontend && npm ci && npm run build`
3. 确认 NODE_VERSION 环境变量设置为 `18`

### 问题 3: 页面空白但状态码 200

**可能原因**:
- JavaScript 加载失败
- 资源路径错误
- CSP 头部过于严格

**解决方案**:
1. 打开浏览器开发者工具 (F12)
2. 查看 Console 标签的错误信息
3. 查看 Network 标签的资源加载情况
4. 检查 `_headers` 文件中的 CSP 配置

---

## 📝 相关文件

- **前端配置**: `frontend/vite.config.ts`
- **重定向规则**: `frontend/public/_redirects`
- **安全头部**: `frontend/public/_headers`
- **API 代理**: `frontend/functions/_middleware.ts`
- **测试页面**: `frontend/public/test.html`

---

## 🔗 参考文档

- [Cloudflare Pages 文档](https://developers.cloudflare.com/pages/)
- [构建配置](https://developers.cloudflare.com/pages/platform/build-configuration/)
- [重定向和头部](https://developers.cloudflare.com/pages/platform/redirects/)
- [Functions](https://developers.cloudflare.com/pages/platform/functions/)

---

**下一步**: 按照上述步骤修复构建配置后，重新部署并测试访问。
