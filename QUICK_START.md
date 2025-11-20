# 🚀 Web3search 快速启动指南

本指南帮助你在 **5-10分钟内** 完成配置并投入使用。

## 📋 前置条件检查

✅ 后端API已部署到Cloudflare Workers
✅ 前端已部署到Cloudflare Pages
✅ Supabase数据库已创建
✅ 基本环境变量已配置

## ⚠️ 当前状态

根据测试，系统存在以下问题：

### 🔴 数据库表未创建
- **症状**: API返回500错误
- **原因**: Supabase数据库缺少必要的表
- **影响**: 所有功能无法使用

## 🔧 立即修复步骤

### 步骤1: 创建数据库表（必须）

有两种方式：

#### 方式A: 使用Supabase Dashboard（推荐，5分钟）

1. 打开 [Supabase Dashboard](https://supabase.com/dashboard)
2. 选择项目：`hxxnkbxyjhhorfeodiji`
3. 点击左侧菜单 "SQL Editor"
4. 复制并执行 `supabase/migrations/APPLY_ALL_MIGRATIONS.sql`
5. 点击 "Run" 执行SQL

**验证**: 在Table Editor中应该看到以下表：
- `projects`
- `conversations`
- `messages`
- `reports`
- `background_tasks`
- `deep_research_tasks`
- `api_calls_telemetry`

#### 方式B: 使用Supabase CLI（3分钟）

```bash
# 安装Supabase CLI（如果还没安装）
npm install -g supabase

# 登录
supabase login

# 连接到项目
supabase link --project-ref hxxnkbxyjhhorfeodiji

# 应用所有迁移
supabase db push

# 验证
supabase db diff
```

### 步骤2: 配置搜索API密钥（可选，但强烈推荐）

搜索功能需要至少一个搜索提供商API密钥。

**快速获取（5分钟）**:

1. **Brave Search**（推荐）
   - 访问: https://brave.com/search/api/
   - 注册免费账户
   - 获取API Key
   - 配置:
   ```bash
   cd workers-api
   echo "your-brave-api-key" | wrangler secret put BRAVE_SEARCH_API_KEY
   ```

2. **或者使用其他提供商**
   - 详见: `docs/API_KEYS_GUIDE.md`

### 步骤3: 重新部署（1分钟）

```bash
cd workers-api
npm run deploy
```

### 步骤4: 验证功能（2分钟）

```bash
# 回到项目根目录
cd ..

# 运行测试脚本
./scripts/test-production.sh
```

**预期结果**: 所有测试通过 ✅

## ✅ 完整配置检查清单

完成以下步骤即可使用:

- [x] 1. 配置Supabase环境变量（已完成）
- [x] 2. 配置OpenRouter API Key（已完成）
- [ ] 3. **创建数据库表（必须完成）**
- [ ] 4. 配置搜索API密钥（推荐）
- [ ] 5. 重新部署
- [ ] 6. 验证功能

## 🎯 如果仍然失败

### 快速诊断

```bash
# 测试liveness（应该返回 {"alive":true}）
curl https://web3search-api.marovole.workers.dev/api/v1/health/live

# 测试health（应该返回JSON，不是error code: 500）
curl https://web3search-api.marovole.workers.dev/api/v1/health
```

### 常见问题

#### Q1: health端点返回 500 错误
- **原因**: 数据库表未创建
- **解决**: 执行步骤1创建数据库表

#### Q2: 搜索功能返回空结果
- **原因**: 缺少搜索API密钥
- **解决**: 执行步骤2配置API密钥
- **临时方案**: 可以使用Chat功能，搜索功能可以暂时跳过

#### Q3: Chat功能无响应
- **原因**: OpenRouter API Key未生效
- **解决**: 重新配置并部署
  ```bash
  cd workers-api
  echo "your-openrouter-key" | wrangler secret put OPENROUTER_API_KEY
  npm run deploy
  ```

## 📞 需要帮助？

1. **查看日志**:
   ```bash
   cd workers-api
   wrangler tail
   ```

2. **详细文档**:
   - API密钥获取: `docs/API_KEYS_GUIDE.md`
   - 故障排查: `docs/TROUBLESHOOTING.md`
   - 部署文档: `docs/DEPLOYMENT.md`

3. **联系支持**:
   - GitHub Issues: https://github.com/marovole/Web3search/issues
   - Email: vole@lucky365vip.cc

## 🎉 完成后

访问以下URL开始使用:

- **前端应用**: https://web3search.pages.dev
- **API文档**: https://web3search-api.marovole.workers.dev/

功能验证：
- ✅ 打开首页
- ✅ 输入查询（如"Bitcoin"）
- ✅ 选择Quick Chat或Deep Research
- ✅ 查看AI响应

**预计完成时间**: 5-10分钟（取决于网络速度）

祝你使用愉快！🚀
