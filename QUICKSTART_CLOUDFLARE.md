# 🚀 Cloudflare Pages 快速部署指南

## ⚡ 5分钟快速开始

### 前置条件
- ✅ Cloudflare账号
- ✅ GitHub仓库推送权限  
- ✅ Cloudflare API Token（从Cloudflare Dashboard获取）

---

## 步骤1：创建Cloudflare Pages项目（2分钟）

1. 访问 https://dash.cloudflare.com/
2. 点击 **Pages** → **Create a project** → **Connect to Git**
3. 选择仓库：`marovole/Web3search`
4. 配置构建：

```
项目名称: web3search
生产分支: main
框架预设: Vite
构建命令: cd frontend && npm install && npm run build
输出目录: frontend/dist
Node版本: 18
```

5. 点击 **Save and Deploy**

---

## 步骤2：配置环境变量（1分钟）

在Cloudflare Pages项目设置中添加：

```env
VITE_ENVIRONMENT=production
VITE_API_BASE_URL=https://web3search-api.onrender.com
VITE_USE_MOCK_API=false
VITE_ENABLE_PERFORMANCE_MONITORING=true
VITE_DEBUG_MODE=false
```

---

## 步骤3：配置GitHub Actions自动部署（1分钟）

在GitHub仓库添加Secrets：

1. **Settings** → **Secrets and variables** → **Actions**
2. 添加两个secrets：
   - `CLOUDFLARE_API_TOKEN`: 从Cloudflare Dashboard获取（需要Pages:Edit权限）
   - `CLOUDFLARE_ACCOUNT_ID`: 从Cloudflare Dashboard右侧栏获取

**获取API Token步骤**：
- Cloudflare Dashboard → My Profile → API Tokens
- Create Token → Edit Cloudflare Workers template
- 或使用已有的Token

---

## 步骤4：验证部署（1分钟）

部署完成后：

```bash
# 测试前端
curl https://web3search.pages.dev

# 测试API代理
curl https://web3search.pages.dev/api/health
```

---

## ✅ 完成！

您的应用现已部署到：
- **生产URL**: https://web3search.pages.dev
- **预览URL**: 每个PR自动生成

---

## 📚 详细文档

查看完整指南：[CLOUDFLARE_DEPLOYMENT.md](./CLOUDFLARE_DEPLOYMENT.md)

---

## 🆘 遇到问题？

### 构建失败
```bash
# 检查构建日志
cd frontend
npm run type-check
npm run build
```

### API无法连接
- 确认后端运行：`curl https://web3search-api.onrender.com/health`
- 检查CORS配置包含：`https://web3search.pages.dev`

### 环境变量不生效
- 确保变量名以 `VITE_` 开头
- 在Cloudflare Pages重新部署

---

## 🎉 下一步

- [ ] 配置自定义域名
- [ ] 启用Worker边缘缓存
- [ ] 配置性能监控
- [ ] 运行负载测试

**支持**: 查看 [故障排查章节](./CLOUDFLARE_DEPLOYMENT.md#故障排查)
