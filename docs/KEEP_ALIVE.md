# Web3search Keep-Alive Cron 配置

由于 Supabase 有空闲自动回收机制，需要定时访问数据库以保持服务活跃。

## 方案一：Cloudflare Workers Cron（内置）

### 状态检查

```bash
# 查看已部署的 cron 触发器
npx wrangler deployment list --environment production

# 或查看 cron 触发器配置
npx wrangler trigger list --environment production
```

### 定时任务配置

在 `workers-api/wrangler.toml` 中已配置：

| 频率 | 用途 |
|------|------|
| `*/5 * * * *` | 健康检查（5分钟） |
| `*/10 * * * *` | Supabase 保活（10分钟） |
| `0 * * * *` | KV 缓存清理（1小时） |

### 激活 Cron 触发器

```bash
# 部署后自动激活 cron
npx wrangler deploy --env production

# 手动查看 cron 状态
npx wrangler trigger list

# 如果 cron 未激活，使用 wrangler.toml 配置会自动生效
```

## 方案二：GitHub Actions（外部保活）

GitHub Actions 工作流已配置在 `.github/workflows/keep-alive-cron.yml`

### 自动激活

1. push 到 main 分支后工作流会自动部署
2. schedule 会每 10 分钟自动运行

### 手动触发

```bash
# 通过 GitHub CLI 触发
gh workflow run keep-alive-cron.yml

# 或在 GitHub 网页手动触发
# https://github.com/marovole/Web3search/actions/workflows/keep-alive-cron.yml
```

## 方案三：外部 Cron 服务

### 使用 EasyCron（免费套餐）

1. 注册 https://www.easycron.com
2. 添加 Cron Job：
   - URL: `https://web3search-api.marovole.workers.dev/api/v1/health/ping`
   - Schedule: `*/10 * * * *`
   - HTTP Method: `GET`

### 使用 Healthchecks.io

1. 注册 https://healthchecks.io
2. 创建检查项目，获取 ping URL
3. 添加 Cron Job 调用 ping URL

### 本地脚本

```bash
# 设置可执行权限
chmod +x scripts/keep-alive.sh

# 设置环境变量
export WEB3SEARCH_API_URL="https://web3search-api.marovole.workers.dev"

# 测试运行
./scripts/keep-alive.sh

# 添加到系统 crontab
crontab -e
# 添加：*/10 * * * * /path/to/Web3search/scripts/keep-alive.sh
```

## 监控

### 查看健康状态

```bash
# 完整健康检查（缓存）
curl https://web3search-api.marovole.workers.dev/api/v1/health

# 轻量级 ping
curl https://web3search-api.marovole.workers.dev/api/v1/health/ping

# 就绪检查
curl https://web3search-api.marovole.workers.dev/api/v1/health/ready

# 存活检查
curl https://web3search-api.marovole.workers.dev/api/v1/health/live
```

### Supabase 项目状态

访问 Supabase Dashboard 检查项目状态：
https://supabase.com/dashboard/project/[project-id]

## 故障排除

### Cron 不运行

1. 检查 wrangler.toml 配置是否正确
2. 确保 Workers 已部署
3. 查看 Cloudflare Dashboard → Workers & Pages → Triggers

### Supabase 仍然休眠

1. 确保 cron 频率 ≤ 10 分钟
2. 使用外部 Cron 服务作为备份
3. 检查 Supabase 项目是否有活动监控设置

### 数据库连接失败

1. 检查环境变量中的 SUPABASE_URL 和 ANON_KEY
2. 验证 Supabase 项目是否仍在运行
3. 查看 Workers 日志：`npx wrangler tail`
