# Cloudflare Workers 部署指南

## 前置条件

- [x] Wrangler CLI 已安装 (v4.46.0)
- [ ] Cloudflare 账户已登录
- [ ] OpenRouter API Key 已获取

## 部署步骤

### 1. 登录 Cloudflare

```bash
wrangler login
```

在浏览器中完成 OAuth 授权。

### 2. 创建 KV Namespace

```bash
# 创建生产环境 KV namespace
wrangler kv namespace create CACHE --env production

# 创建开发环境 KV namespace
wrangler kv namespace create CACHE --env development
```

记录返回的 namespace ID。

### 3. 更新 wrangler.toml

将 KV namespace ID 更新到 `wrangler.toml`:

```toml
[[kv_namespaces]]
binding = "CACHE"
id = "your-production-kv-id"

[[env.development.kv_namespaces]]
binding = "CACHE"
id = "your-development-kv-id"
```

### 4. 配置 Secrets

```bash
# 配置 Supabase 密钥
wrangler secret put SUPABASE_ANON_KEY --env production
# 粘贴密钥: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# 配置 OpenRouter API Key
wrangler secret put OPENROUTER_API_KEY --env production
# 粘贴密钥: sk-or-v1-...

# (可选) 配置 Supabase Service Role Key
wrangler secret put SUPABASE_SERVICE_ROLE_KEY --env production
```

### 5. 部署到生产环境

```bash
# 部署到生产环境
wrangler deploy --env production

# 或者使用 npm 脚本
npm run deploy
```

### 6. 验证部署

```bash
# 测试健康检查
curl https://web3search-api.b80eef96097fab92f15b574ed5fbb927.workers.dev/api/v1/health

# 测试搜索自动完成
curl "https://web3search-api.b80eef96097fab92f15b574ed5fbb927.workers.dev/api/v1/search/autocomplete?q=bitcoin&limit=5"

# 测试聊天 API (非流式)
curl -X POST "https://web3search-api.b80eef96097fab92f15b574ed5fbb927.workers.dev/api/v1/chat/quick-chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "什么是比特币？", "stream": false}'
```

## 环境变量清单

### 公开变量 (wrangler.toml)
- `APP_VERSION` - 应用版本号
- `CORS_ORIGINS` - 允许的跨域来源
- `SUPABASE_URL` - Supabase 项目 URL
- `SUPABASE_HEALTH_TABLE` - 健康检查使用的表名
- `ENVIRONMENT` - 环境标识 (production/development)

### 机密变量 (Cloudflare Secrets)
- `SUPABASE_ANON_KEY` - Supabase 匿名密钥（必需）
- `OPENROUTER_API_KEY` - OpenRouter API Key（必需）
- `SUPABASE_SERVICE_ROLE_KEY` - Supabase 服务角色密钥（可选）

## 部署后检查

- [ ] 健康检查端点返回 200 OK
- [ ] Supabase 数据库连接正常
- [ ] 搜索自动完成 API 工作正常
- [ ] 聊天 API（流式和非流式）工作正常
- [ ] 速率限制功能生效
- [ ] CORS 配置正确

## 回滚计划

如果部署出现问题：

```bash
# 查看部署历史
wrangler deployments list --env production

# 回滚到上一个版本
wrangler rollback --env production
```

## 监控和日志

```bash
# 实时查看日志
wrangler tail --env production

# 在 Cloudflare Dashboard 查看
# https://dash.cloudflare.com/workers
```

## 自定义域名（可选）

1. 在 Cloudflare Dashboard 添加自定义域名
2. 配置 DNS 记录
3. 更新 wrangler.toml 中的 route 配置
