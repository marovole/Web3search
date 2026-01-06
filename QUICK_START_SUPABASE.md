# Supabase 快速恢复指南

## 步骤 1：创建新 Supabase 项目

1. 访问 https://supabase.com/dashboard
2. 点击 **New Project**
3. 填写：
   - Name: `web3search`
   - Password: 生成并保存密码
4. 点击 **Create new project**

## 步骤 2：运行初始化脚本

在 Supabase Dashboard 中：
1. 进入 **SQL Editor**
2. 打开文件 `supabase/init.sql`
3. 点击 **Run** 执行

或者使用 Supabase CLI：
```bash
supabase link --project-ref your-project-ref
supabase db push
```

## 步骤 3：更新环境变量

### 获取项目凭证

在项目设置 → API 中获取：
- `SUPABASE_URL` - 例如 `https://xxxxx.supabase.co`
- `SUPABASE_ANON_KEY` - 匿名密钥

### 更新 Cloudflare Workers

```bash
cd workers-api
npx wrangler secret put SUPABASE_URL
npx wrangler secret put SUPABASE_ANON_KEY
```

### 更新 Frontend

修改 `frontend/.env.production`:
```bash
VITE_SUPABASE_URL=https://xxxxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR...
```

## 步骤 4：重新部署

```bash
cd workers-api
npx wrangler deploy --env production
```

## 验证

```bash
# 检查 API 健康状态
curl https://web3search-api.marovole.workers.dev/api/v1/health

# 检查数据库连接
curl https://web3search-api.marovole.workers.dev/api/v1/health/ready
```

## 已创建的表

| 表名 | 用途 |
|------|------|
| `conversations` | 聊天会话 |
| `messages` | 聊天消息 |
| `deep_research_tasks` | 深度研究任务 |
| `reports` | 研究报告 |
| `api_calls_telemetry` | API 调用监控 |
| `healthcheck_events` | 健康检查记录 |

## 文件位置

- 初始化脚本: `supabase/init.sql`
- 完整迁移: `supabase/migrations/`
