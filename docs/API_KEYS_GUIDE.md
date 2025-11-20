# 🔑 API密钥获取指南

本指南将帮助你快速获取Web3search所需的所有API密钥。

## ✅ 已配置的服务

### Supabase 数据库
- ✅ 已配置
- URL: `https://hxxnkbxyjhhorfeodiji.supabase.co`
- 无需额外操作

### OpenRouter AI服务
- ✅ 已配置
- 无需额外操作

---

## ❌ 需要配置的服务

你需要**至少配置一个搜索提供商**才能使用搜索功能。推荐配置多个作为备份。

### 1. Brave Search API（推荐）⭐

**优势**:
- ✅ 完全免费
- ✅ 每月 2,000 次免费查询
- ✅ 无需信用卡
- ✅ 搜索质量高

**获取步骤**:

1. 访问 [Brave Search API](https://brave.com/search/api/)
2. 点击 "Get Started" 或 "Sign Up"
3. 使用GitHub/Google账号登录
4. 选择 "Free Plan"
5. 创建API密钥
6. 复制API密钥（格式: `BSA...`）

**配置命令**:
```bash
cd workers-api
echo "your-brave-api-key" | wrangler secret put BRAVE_SEARCH_API_KEY
```

---

### 2. Tavily Search API（备选）

**优势**:
- ✅ 免费
- ✅ 每月 1,000 次查询
- ✅ AI优化的搜索结果
- ✅ 支持深度搜索

**获取步骤**:

1. 访问 [Tavily](https://tavily.com/)
2. 点击 "Get API Key"
3. 注册账号（邮箱验证）
4. 在Dashboard创建API密钥
5. 复制API密钥（格式: `tvly-...`）

**配置命令**:
```bash
cd workers-api
echo "your-tavily-api-key" | wrangler secret put TAVILY_API_KEY
```

---

### 3. Serper (Google Search)（备选）

**优势**:
- ✅ 免费
- ✅ 每月 2,500 次查询
- ✅ 使用Google搜索引擎
- ✅ 结果准确度高

**获取步骤**:

1. 访问 [Serper.dev](https://serper.dev/)
2. 点击 "Sign Up"
3. 使用Google账号登录
4. 在Dashboard点击 "API Key"
5. 复制API密钥

**配置命令**:
```bash
cd workers-api
echo "your-serper-api-key" | wrangler secret put SERPER_API_KEY
```

---

## 🚀 快速配置流程

### 方式1: 使用自动配置脚本（推荐）

```bash
cd workers-api
../scripts/quick-setup.sh
```

脚本会引导你完成所有配置。

### 方式2: 手动配置

```bash
cd workers-api

# 配置Supabase（已在.dev.vars中，自动同步到生产）
wrangler secret put SUPABASE_URL
wrangler secret put SUPABASE_ANON_KEY

# 配置OpenRouter（已在.dev.vars中）
wrangler secret put OPENROUTER_API_KEY

# 配置至少一个搜索提供商
wrangler secret put BRAVE_SEARCH_API_KEY
# 或
wrangler secret put TAVILY_API_KEY
# 或
wrangler secret put SERPER_API_KEY
```

---

## 🧪 验证配置

配置完成后，运行测试脚本验证:

```bash
# 在项目根目录执行
./scripts/test-production.sh
```

如果所有测试通过，你将看到:
```
🎉 所有测试通过！系统可以投入使用。

🚀 访问你的应用:
  前端: https://web3search.pages.dev
  API:  https://web3search-api.marovole.workers.dev
```

---

## 📊 API密钥使用量追踪

### Brave Search
- Dashboard: https://api.search.brave.com/app/dashboard
- 查看每日/每月使用量
- 监控剩余配额

### Tavily
- Dashboard: https://app.tavily.com/
- 查看API调用统计
- 升级到付费计划（如需）

### Serper
- Dashboard: https://serper.dev/dashboard
- 实时监控API使用
- 查看历史记录

---

## ⚠️ 重要提示

### 安全性
- ❌ **永远不要**将API密钥提交到Git
- ✅ 只通过 `wrangler secret put` 配置生产环境
- ✅ 本地开发使用 `.dev.vars` 文件（已在 `.gitignore`）

### 配额管理
- 🔔 设置每月配额提醒
- 📊 定期检查使用量
- 🔄 配置多个提供商作为备份

### 故障转移
Web3search自动按以下顺序尝试搜索提供商:
1. Brave Search（主要）
2. Tavily（备份1）
3. Serper（备份2）

**建议**: 配置至少2个提供商以确保高可用性。

---

## 🆘 常见问题

### Q: 我需要配置所有3个搜索提供商吗？
A: 不需要。至少配置1个即可，但建议配置2-3个作为备份。

### Q: 哪个搜索提供商最好？
A: Brave Search - 免费额度最高，搜索质量好，推荐首选。

### Q: API密钥配置后多久生效？
A: 立即生效。配置后运行 `npm run deploy` 重新部署即可。

### Q: 如何更新API密钥？
A: 重新运行 `wrangler secret put KEY_NAME` 即可覆盖旧值。

### Q: 如何查看已配置的密钥？
A: 运行 `wrangler secret list`（注意：出于安全考虑，只显示密钥名称，不显示值）

---

## 📞 需要帮助？

- 📖 查看部署文档: `docs/DEPLOYMENT.md`
- 🐛 报告问题: [GitHub Issues](https://github.com/marovole/Web3search/issues)
- 📧 联系作者: vole@lucky365vip.cc

---

## ✅ 配置检查清单

完成以下步骤后即可投入使用:

- [ ] 获取至少1个搜索提供商API密钥
- [ ] 运行配置脚本或手动配置密钥
- [ ] 运行测试脚本验证配置
- [ ] 所有测试通过
- [ ] 访问前端验证功能正常

**预计时间**: 15-20分钟

祝你使用愉快！🎉
