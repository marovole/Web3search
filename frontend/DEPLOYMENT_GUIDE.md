# Web3Search 前端部署指南

## 快速部署

### 1. Cloudflare Pages 自动部署

**推荐方式**：通过 Git 集成自动部署

1. 连接 GitHub 仓库到 Cloudflare Pages
2. 配置构建设置：
   ```
   构建命令: npm run build
   输出目录: dist
   Root 目录: frontend
   ```
3. 配置环境变量（在 Cloudflare Pages Dashboard）：
   - `VITE_API_BASE_URL`: https://web3search-api.workers.dev

4. **自动部署触发**：
   - 推送到 `main` 分支自动部署到生产环境
   - 推送到其他分支自动生成预览环境

**生产环境**: https://web3search.pages.dev

### 2. 手动部署

如果需要手动部署到其他平台：

```bash
# 1. 安装依赖
cd frontend
npm ci

# 2. 构建生产版本
npm run build

# 3. 上传 dist/ 目录到静态托管服务
#    - Cloudflare Pages (推荐)
#    - Netlify
#    - GitHub Pages
#    - Nginx / Apache
```

## 部署状态检查

### ✅ 已完成的验证项目
- [x] TypeScript 编译无错误
- [x] 前端构建成功
- [x] 所有核心组件已实现
- [x] 响应式设计完成
- [x] 安全头配置完成
- [x] 性能监控集成完成
- [x] Cloudflare Pages 自动部署配置完成

### ⚠️ 需要手动处理的项目
- [ ] 后端 API 连接测试（需要启动后端服务）
- [ ] 安全漏洞修复（npm audit fix --force）
- [ ] CSP 响应头配置（Cloudflare Pages _headers 文件）

## 环境变量配置

### Cloudflare Pages 环境变量

在 Cloudflare Pages Dashboard 中配置：

**生产环境**：
```
VITE_API_BASE_URL=https://web3search-api.workers.dev
```

**预览环境**（可选）：
```
VITE_API_BASE_URL=https://web3search-api-dev.workers.dev
```

### 本地开发环境

创建 `.env.local` 文件：
```bash
VITE_API_BASE_URL=http://localhost:8000
```

## 安全注意事项

发现以下安全漏洞，需要手动修复：

1. **esbuild <=0.24.2** - 中等风险
   - 影响：开发服务器请求安全
   - 修复：运行 `npm audit fix --force`

2. **prismjs <1.30.0** - 中等风险
   - 影响：DOM Clobbering 漏洞
   - 修复：运行 `npm audit fix --force`

## 性能指标

- **构建包大小**: 13MB（包含所有资源）
- **主要 chunks**:
  - syntax-vendor: 873KB（代码高亮库）
  - vendor: 768KB（第三方库）
  - react-vendor: 486KB（React相关）
- **加载优化**: 已实现代码分割和懒加载
- **CDN 加速**: Cloudflare 全球边缘节点

## 部署后验证

部署完成后，请验证：

### 1. 功能测试
- 访问主页，检查所有页面加载
- 测试聊天功能
- 验证用户注册/登录
- 测试搜索功能

### 2. 性能测试
- 检查首屏加载时间（目标 < 2s）
- 测试 API 响应速度
- 验证移动端体验
- 使用 Lighthouse 进行性能评分

### 3. 安全测试
- 检查 HTTPS 强制访问
- 验证 CSP 策略生效
- 测试 XSS 防护
- 检查浏览器控制台无错误

## 故障排除

### 常见问题

#### 1. API 连接失败
**症状**：前端无法连接到后端 API

**解决方案**：
- 检查环境变量配置（`VITE_API_BASE_URL`）
- 验证后端服务状态
- 确认 CORS 配置：
  ```typescript
  // workers-api/src/index.ts
  const corsHeaders = {
    'Access-Control-Allow-Origin': 'https://web3search.pages.dev',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  }
  ```

#### 2. 构建失败
**症状**：`npm run build` 失败

**解决方案**：
- 运行 `npm ci` 重新安装依赖
- 检查 TypeScript 类型错误：`npm run type-check`
- 清理构建缓存：`rm -rf dist node_modules/.vite`
- 检查 Node.js 版本（推荐 v18+）

#### 3. Cloudflare Pages 部署失败
**症状**：Cloudflare Pages 构建失败

**解决方案**：
- 检查构建日志（Cloudflare Pages Dashboard）
- 验证构建命令和输出目录配置
- 检查环境变量是否正确设置
- 确认 Root 目录设置为 `frontend`

#### 4. 页面加载缓慢
**症状**：首屏加载时间过长

**解决方案**：
- 启用 Cloudflare CDN 缓存
- 检查资源大小（使用 `npm run build:analyze`）
- 优化图片资源（使用 WebP 格式）
- 启用 Gzip/Brotli 压缩

## Cloudflare Pages 配置

### 构建配置

```yaml
Build command: npm run build
Build output directory: dist
Root directory: frontend
Node version: 18
```

### 自定义域名

在 Cloudflare Pages Dashboard 中添加自定义域名：

1. 进入项目设置
2. 点击 "Custom domains"
3. 添加域名（例如：`web3search.com`）
4. Cloudflare 会自动配置 DNS

### 响应头配置

创建 `public/_headers` 文件（待实施）：

```
/*
  X-Frame-Options: DENY
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: geolocation=(), microphone=(), camera=()
```

## 监控和日志

### Cloudflare Web Analytics

在 Cloudflare Dashboard 中启用 Web Analytics：
1. 进入项目设置
2. 点击 "Web Analytics"
3. 启用分析功能

### 部署历史

查看部署历史和回滚：
1. 进入 Cloudflare Pages Dashboard
2. 选择 "Deployments"
3. 查看所有部署记录
4. 可以回滚到任意历史版本

### 实时日志

查看实时日志：
```bash
# 使用 wrangler CLI（Cloudflare Workers CLI）
npx wrangler pages deployment tail
```

## 联系支持

如遇到部署问题，请参考：
- [Cloudflare Pages 官方文档](https://developers.cloudflare.com/pages/)
- [项目 README.md](./README.md)
- [GitHub Issues](https://github.com/marovole/Web3search/issues)
- [OpenSpec 提案](../openspec/changes/fix-critical-production-issues/proposal.md)

## 更新日志

- **2025-11-09**: 从 Vercel 迁移到 Cloudflare Pages
  - 移除 Vercel 相关配置
  - 更新部署指南为 Cloudflare Pages
  - 添加自动部署配置说明
