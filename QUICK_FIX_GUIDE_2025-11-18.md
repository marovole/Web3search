# Web3search 快速修复指南

**问题**: 前端无法连接后端API，所有功能失效  
**修复时间**: 预计 30 分钟  
**优先级**: P0 - 立即修复

---

## 🔧 立即修复步骤

### 1. 修复前端 API 配置

**方法 1: Cloudflare Pages 控制台**
1. 登录 [Cloudflare Pages Dashboard](https://dash.cloudflare.com/pages)
2. 选择 `web3search` 项目
3. 进入 `Settings` → `Environment variables`
4. 添加/更新以下环境变量：
   ```
   VITE_API_BASE_URL=https://web3search-api.marovole.workers.dev
   ```

**方法 2: 使用 wrangler CLI**
```bash
# 设置 Cloudflare Pages 环境变量
npx wrangler pages project create --project-name web3search
npx wrangler pages secret put VITE_API_BASE_URL
# 输入: https://web3search-api.marovole.workers.dev
```

### 2. 重新部署前端

```bash
# 进入前端目录
cd /Users/marovole/GitHub/Web3search/frontend

# 构建生产版本
npm run build

# 提交更改（如果需要）
git add . && git commit -m "fix: 更新API配置为新的Workers URL"
git push origin main
```

### 3. 验证修复

**方法 1: 自动化测试**
```bash
cd /Users/marovole/GitHub/Web3search
node production-test-2025.js
```

**方法 2: 手动浏览器测试**
1. 访问 https://web3search.pages.dev
2. 打开浏览器开发者工具
3. 检查控制台，确认没有 API 连接错误
4. 测试搜索功能："输入 bitcoin"
5. 测试聊天功能："输入 What is Bitcoin?"

**预期结果**:
- ✅ 控制台显示正确的 API URL
- ✅ 搜索自动完成工作
- ✅ 聊天功能返回响应
- ✅ 深度研究功能正常

---

## 🔄 部署后验证清单

- [ ] 页面正常加载
- [ ] 控制台无 API 连接错误
- [ ] 搜索自动完成工作
- [ ] Quick Chat 功能正常
- [ ] Deep Research 功能正常
- [ ] 市场热点数据加载
- [ ] 响应时间 < 3秒
- [ ] 无 JavaScript 错误

---

## 🆘 故障排除

### 如果仍然无法连接：

1. **检查环境变量是否生效**
   ```bash
   curl -s https://web3search.pages.dev | grep -i "web3search-api"
   ```

2. **清除浏览器缓存**
   - 硬刷新: Ctrl+Shift+R (Windows/Linux) 或 Cmd+Shift+R (Mac)
   - 或者在开发者工具中禁用缓存

3. **检查 Cloudflare Pages 部署状态**
   - 查看 GitHub Actions 构建日志
   - 确认部署成功

4. **验证后端 API 仍正常**
   ```bash
   curl -s https://web3search-api.marovole.workers.dev/api/v1/health
   ```

---

## 📞 联系信息

如遇问题无法解决：
- 项目维护者: marovole
- 邮箱: vole@lucky365vip.cc
- GitHub: https://github.com/marovole/Web3search

---

**修复完成后**: 系统将完全可用，所有功能恢复正常！ 🎉
