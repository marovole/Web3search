# Cloudflare Workers 配置指南

## 1. 获取 Supabase API Keys

### 方法一：通过 Supabase Dashboard（推荐）

1. 访问 [Supabase Dashboard](https://supabase.com/dashboard/project/hxxnkbxyjhhorfeodiji/settings/api)
2. 在左侧菜单中选择 **Settings** > **API**
3. 在 **Project API keys** 部分，复制以下密钥：
   - **anon public** key（用于客户端只读操作）
   - **service_role** key（可选，用于管理员操作）

### 方法二：通过 Supabase CLI

```bash
# 1. 登录 Supabase
supabase login

# 2. Link 到项目
supabase link --project-ref hxxnkbxyjhhorfeodiji

# 3. 获取项目信息（会显示 API URL 和 anon key）
supabase status
```

## 2. 更新本地开发环境变量

编辑 `workers/.dev.vars` 文件，替换示例值为真实的 API key：

```bash
# Supabase 匿名密钥（用于只读操作）
SUPABASE_ANON_KEY=你的真实_anon_key

# Supabase 服务角色密钥（可选，用于管理员操作）
# SUPABASE_SERVICE_ROLE_KEY=你的真实_service_role_key
```

## 3. 配置生产环境 Secrets

```bash
# 设置生产环境的 API key（需要先完成 wrangler login）
wrangler secret put SUPABASE_ANON_KEY --env production

# 可选：设置 service role key
# wrangler secret put SUPABASE_SERVICE_ROLE_KEY --env production
```

## 4. 本地测试

```bash
# 启动开发服务器
npm run dev

# 测试 health endpoint
curl http://localhost:8787/api/v1/health
```

预期响应：
```json
{
  "status": "healthy",
  "timestamp": "2025-11-09T01:30:00.000Z",
  "uptimeMs": 5000,
  "version": "workers-dev",
  "supabase": {
    "status": "ok",
    "latencyMs": 150
  }
}
```

## 5. 部署到 Cloudflare

```bash
# 部署到开发环境
wrangler deploy

# 部署到生产环境
npm run deploy:prod
```

## 故障排查

### Supabase 连接失败

如果看到 `"supabase": {"status": "error"}` 响应：

1. **检查 API key 是否正确**
   ```bash
   # 测试 API key 是否有效
   curl "https://hxxnkbxyjhhorfeodiji.supabase.co/rest/v1/projects?select=id&limit=1" \
     -H "apikey: 你的_API_KEY"
   ```

2. **检查环境变量加载**
   ```bash
   # 查看 wrangler dev 启动日志，确认 SUPABASE_ANON_KEY 显示为 "(hidden)"
   ```

3. **检查数据库连接**
   ```bash
   # 使用 psql 测试数据库连接
   export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"
   psql "postgresql://postgres:密码@db.hxxnkbxyjhhorfeodiji.supabase.co:5432/postgres" -c "SELECT 1"
   ```

### Wrangler 版本警告

如果看到 wrangler 版本警告：

```bash
# 在 workers 目录下更新 wrangler
cd workers
npm install --save-dev wrangler@latest
```
