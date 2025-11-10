# 部署验证指南

**提交时间**: 2025-01-26  
**提交哈希**: 9b455a3

---

## ✅ 代码已提交

修复内容已推送到远程仓库，包含以下更改：

1. ✅ Deep Research 错误日志增强
2. ✅ 前端 SPA 路由支持（_redirects 文件）
3. ✅ 部署诊断脚本

---

## 🚀 部署状态

### 自动部署

如果配置了 CI/CD，部署会自动触发：

- **Render (后端)**: 自动检测到 `backend/` 目录的更改并部署
- **Netlify/Vercel (前端)**: 自动检测到 `frontend/` 目录的更改并部署

### 手动部署（如果需要）

**Render 后端**
- 登录 [Render Dashboard](https://dashboard.render.com)
- 找到 `web3search-api` 服务
- 点击 "Manual Deploy" → "Deploy latest commit"

**Netlify 前端**
- 登录 [Netlify Dashboard](https://app.netlify.com)
- 找到项目
- 点击 "Trigger deploy" → "Deploy site"

---

## 🔍 部署后验证

### 1. 等待部署完成

通常需要 3-5 分钟：
- Render: 查看部署日志确认完成
- Netlify: 查看部署状态确认完成

### 2. 运行诊断脚本

部署完成后，运行诊断脚本：

```bash
# 确保安装了 requests 库
pip install requests

# 运行诊断脚本
python scripts/diagnose_deployment.py
```

**脚本会检查：**
- ✅ 后端健康状态
- ✅ API 文档可访问性
- ✅ Deep Research 端点功能
- ✅ 前端路由可用性

**输出示例：**
```
🔍 开始部署诊断...

ℹ️  检查后端健康状态...
✅ 后端健康检查通过: {'status': 'ok'}

ℹ️  测试 Deep Research 端点...
✅ Deep Research 请求成功

ℹ️  检查前端路由...
✅  / -> 200 OK
✅  /chat -> 200 OK
✅  /history -> 200 OK
```

### 3. 手动验证（可选）

**测试 Deep Research**
```bash
curl -X POST https://web3search-api.onrender.com/api/v1/chat/deep-research \
  -H "Content-Type: application/json" \
  -d '{"query": "Bitcoin", "symbol": "BTC"}' \
  -v
```

**测试前端路由**
```bash
# 检查首页
curl -I https://web3search.netlify.app/

# 检查其他路由
curl -I https://web3search.netlify.app/chat
curl -I https://web3search.netlify.app/history
```

---

## 📊 查看错误日志

### Render 后端日志

1. 登录 [Render Dashboard](https://dashboard.render.com)
2. 选择 `web3search-api` 服务
3. 点击 "Logs" 标签
4. 查找以下关键词：
   - `❌ 数据聚合失败`
   - `❌ 数据格式化失败`
   - `❌ Deep Research引擎调用失败`
   - `完整堆栈跟踪`

### Netlify 前端日志

1. 登录 [Netlify Dashboard](https://app.netlify.com)
2. 选择项目
3. 点击 "Functions" 或 "Deploys" 查看日志

---

## 🐛 问题排查

### Deep Research 仍然返回 500

**步骤 1**: 查看 Render 日志
- 查找最新的错误日志
- 查看完整的堆栈跟踪
- 确认错误类型（数据聚合、格式化、LLM调用等）

**步骤 2**: 检查常见问题
- ✅ 外部 API 密钥配置正确
- ✅ 数据库连接正常
- ✅ 服务资源充足（内存、CPU）

**步骤 3**: 运行诊断脚本
```bash
python scripts/diagnose_deployment.py
```
查看详细错误响应

### 前端仍然返回 404

**步骤 1**: 确认 `_redirects` 文件已部署
```bash
# 检查文件是否存在
curl https://web3search.netlify.app/_redirects
```

**步骤 2**: 检查 Netlify 配置
- 确认 `netlify.toml` 配置正确
- 确认构建输出目录包含 `_redirects` 文件

**步骤 3**: 重新部署
- 在 Netlify Dashboard 触发重新部署
- 或推送一个空提交触发部署

---

## ✅ 验证清单

部署完成后，请确认：

- [ ] Render 后端部署成功
- [ ] Netlify/Vercel 前端部署成功
- [ ] 后端健康检查通过 (`/health`)
- [ ] Deep Research 端点返回 200 或明确的错误信息
- [ ] 前端所有路由可访问（返回 200）
- [ ] API 请求正确代理到后端
- [ ] 错误日志包含详细堆栈跟踪

---

## 📞 需要帮助？

如果问题仍然存在：

1. **运行诊断脚本**获取详细报告
2. **查看部署日志**确认部署成功
3. **检查环境变量**配置是否正确
4. **查看错误日志**获取详细错误信息

诊断报告会保存为：`deployment_diagnosis_YYYYMMDD_HHMMSS.json`

---

**下一步**: 等待部署完成 → 运行诊断脚本 → 查看结果

