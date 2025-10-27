# 部署指南

Web3 Search API 完整部署指南，覆盖Railway、Render和Vercel平台。

## 目录

1. [部署概览](#部署概览)
2. [Railway部署](#railway部署)
3. [Render部署](#render部署)
4. [Vercel部署前端](#vercel部署前端)
5. [环境变量配置](#环境变量配置)
6. [数据库初始化](#数据库初始化)
7. [部署验证](#部署验证)
8. [回滚流程](#回滚流程)

---

## 部署概览

### 架构组件

```
┌─────────────┐     ┌──────────────┐     ┌────────────┐
│   Frontend  │────▶│   Backend    │────▶│  Database  │
│   (Vercel)  │     │ (Render/Rwy) │     │(PostgreSQL)│
└─────────────┘     └──────────────┘     └────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │    Redis     │
                    │   (Cache)    │
                    └──────────────┘
```

### 部署平台对比

| 特性 | Railway | Render | Vercel |
|------|---------|--------|--------|
| **后端** | ✅ 推荐 | ✅ 推荐 | ❌ 不支持 |
| **前端** | ✅ 支持 | ✅ 支持 | ✅ 最佳 |
| **数据库** | ✅ 内置 | ✅ 内置 | ❌ 需外部 |
| **Redis** | ✅ 内置 | ✅ 内置 | ❌ 需外部 |
| **自动部署** | ✅ | ✅ | ✅ |
| **免费额度** | $5/月 | ✅ | ✅ |
| **价格** | $$ | $$ | $ |

---

## Railway部署

### 前置条件

```bash
# 1. 安装Railway CLI
npm install -g @railway/cli

# 2. 登录Railway
railway login

# 3. 创建项目
railway init
```

### 步骤1：创建后端服务

```bash
cd backend

# 1. 链接到Railway项目
railway link

# 2. 添加PostgreSQL
railway add -d postgres

# 3. 添加Redis
railway add -d redis

# 4. 部署后端
railway up
```

### 步骤2：配置环境变量

```bash
# 方法1：通过CLI
railway variables set OPENROUTER_API_KEY=sk-or-v1-xxx
railway variables set COINGECKO_API_KEY=CG-xxx
railway variables set ETHERSCAN_API_KEY=xxx

# 方法2：通过Dashboard
# 1. 访问railway.app
# 2. 选择项目 → Variables
# 3. 添加所有必需变量
```

必需环境变量：
```bash
# 数据库（自动生成）
DATABASE_URL=postgresql://...
REDIS_URL=redis://...

# API Keys
OPENROUTER_API_KEY=sk-or-v1-xxx
COINGECKO_API_KEY=CG-xxx
ETHERSCAN_API_KEY=xxx
TWITTER_BEARER_TOKEN=xxx
REDDIT_CLIENT_ID=xxx
REDDIT_CLIENT_SECRET=xxx

# 可选
SENTRY_DSN=https://xxx@sentry.io/xxx
SLACK_WEBHOOK_URL=https://hooks.slack.com/xxx
```

### 步骤3：初始化数据库

```bash
# 等待服务部署完成后
DEPLOY_URL=$(railway status --json | jq -r '.service.url')

# 初始化数据库表
curl -X POST "$DEPLOY_URL/admin/init-db"

# 验证表创建
curl "$DEPLOY_URL/admin/tables"
```

### 步骤4：配置自定义域名

```bash
# 1. 通过Dashboard
# Settings → Domains → Generate Domain

# 2. 或使用CLI
railway domain
```

### Railway配置文件

创建`railway.toml`:
```toml
[build]
builder = "nixpacks"
buildCommand = "pip install -r requirements.txt"

[deploy]
startCommand = "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 3
```

---

## Render部署

### 前置条件

1. 创建Render账号：https://render.com
2. 连接GitHub仓库

### 步骤1：创建Web Service

1. **访问Dashboard** → New → Web Service
2. **连接仓库**: 选择GitHub仓库
3. **配置服务**:
   ```yaml
   Name: web3search-api
   Region: Oregon (US West)
   Branch: main
   Root Directory: backend
   Runtime: Python 3.11
   Build Command: pip install -r requirements.txt
   Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
4. **选择Plan**: Free或Starter ($7/月)

### 步骤2：创建PostgreSQL数据库

1. **New** → PostgreSQL
2. **配置数据库**:
   ```yaml
   Name: web3search-db
   Database: web3search
   User: admin
   Region: Oregon (US West)
   Plan: Free或Starter
   ```
3. **获取连接信息**: Internal Database URL

### 步骤3：创建Redis实例

1. **New** → Redis
2. **配置Redis**:
   ```yaml
   Name: web3search-redis
   Region: Oregon (US West)
   Plan: Free或Starter
   ```
3. **获取连接URL**: Internal Redis URL

### 步骤4：配置环境变量

在Web Service的Environment中添加：

```bash
# 数据库（从PostgreSQL和Redis中复制）
DATABASE_URL=postgresql://user:pass@host/db
REDIS_URL=redis://user:pass@host:6379

# API Keys
OPENROUTER_API_KEY=sk-or-v1-xxx
COINGECKO_API_KEY=CG-xxx
ETHERSCAN_API_KEY=xxx
TWITTER_BEARER_TOKEN=xxx
REDDIT_CLIENT_ID=xxx
REDDIT_CLIENT_SECRET=xxx

# Sentry
SENTRY_DSN=https://xxx@sentry.io/xxx
SLACK_WEBHOOK_URL=https://hooks.slack.com/xxx

# 应用配置
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
```

### 步骤5：触发部署

1. **Manual Deploy** → Deploy Latest Commit
2. **查看日志**: Logs标签页
3. **等待健康检查**: 检查/health端点

### Render配置文件

创建`render.yaml`:
```yaml
services:
  - type: web
    name: web3search-api
    env: python
    region: oregon
    plan: starter
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /health
    autoDeploy: true
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: web3search-db
          property: connectionString
      - key: REDIS_URL
        fromDatabase:
          name: web3search-redis
          property: connectionString
      - key: OPENROUTER_API_KEY
        sync: false
      - key: ENVIRONMENT
        value: production

databases:
  - name: web3search-db
    plan: starter
    databaseName: web3search
    region: oregon

  - name: web3search-redis
    plan: starter
    region: oregon
```

---

## Vercel部署前端

### 步骤1：准备前端项目

```bash
cd frontend

# 1. 配置API URL
# 编辑.env.production
NEXT_PUBLIC_API_URL=https://web3search-api.onrender.com
NEXT_PUBLIC_WS_URL=wss://web3search-api.onrender.com

# 2. 测试构建
npm run build
```

### 步骤2：连接Vercel

```bash
# 1. 安装Vercel CLI
npm install -g vercel

# 2. 登录
vercel login

# 3. 部署
vercel --prod
```

### 步骤3：配置环境变量

```bash
# 通过CLI
vercel env add NEXT_PUBLIC_API_URL production

# 或通过Dashboard
# Settings → Environment Variables
```

### 步骤4：配置自定义域名

1. **Settings** → Domains
2. **Add** → 输入域名
3. **配置DNS**: 添加CNAME记录指向vercel app

### Vercel配置文件

创建`vercel.json`:
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "devCommand": "npm run dev",
  "installCommand": "npm install",
  "framework": "nextjs",
  "regions": ["sfo1"],
  "env": {
    "NEXT_PUBLIC_API_URL": "https://web3search-api.onrender.com"
  }
}
```

---

## 环境变量配置

### 必需变量

```bash
# 数据库
DATABASE_URL=postgresql://user:pass@host:5432/dbname
REDIS_URL=redis://user:pass@host:6379

# LLM API
OPENROUTER_API_KEY=sk-or-v1-xxx  # 必需

# 数据源API
COINGECKO_API_KEY=CG-xxx         # 可选，但推荐
ETHERSCAN_API_KEY=xxx            # 可选
TWITTER_BEARER_TOKEN=xxx         # 可选
REDDIT_CLIENT_ID=xxx             # 可选
REDDIT_CLIENT_SECRET=xxx         # 可选
CRYPTOPANIC_API_KEY=xxx          # 可选

# 监控
SENTRY_DSN=https://xxx@sentry.io/xxx  # 可选但强烈推荐
SLACK_WEBHOOK_URL=https://hooks.slack.com/xxx  # 可选

# 应用配置
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
API_TITLE="Web3 Search API"
API_VERSION="1.0.0"
```

### 获取API Keys

1. **OpenRouter** (必需):
   - 访问: https://openrouter.ai/keys
   - 注册并创建API Key
   - 每月$5免费额度

2. **CoinGecko** (推荐):
   - 访问: https://www.coingecko.com/en/api
   - 申请免费API Key
   - 50次/分钟限制

3. **Etherscan** (可选):
   - 访问: https://etherscan.io/apis
   - 注册并创建API Key
   - 5次/秒限制

4. **Sentry** (推荐):
   - 访问: https://sentry.io
   - 创建项目并获取DSN
   - 免费5000 events/月

---

## 数据库初始化

### 方法1：使用管理端点（首次部署）

```bash
# 初始化所有表
curl -X POST "https://your-api.onrender.com/admin/init-db"

# 验证表创建
curl "https://your-api.onrender.com/admin/tables"

# 预期响应
{
  "success": true,
  "tables": ["reports", "conversations", "messages", "projects", "project_snapshots"]
}
```

### 方法2：使用Alembic迁移（生产推荐）

```bash
# 1. 生成迁移
alembic revision --autogenerate -m "Initial tables"

# 2. 应用迁移
alembic upgrade head

# 3. 查看迁移历史
alembic history

# 4. 回滚（如需）
alembic downgrade -1
```

### 方法3：手动SQL

```sql
-- 连接数据库
psql $DATABASE_URL

-- 创建表（示例）
CREATE TABLE IF NOT EXISTS reports (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    query TEXT NOT NULL,
    title TEXT,
    report_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    content_markdown TEXT,
    tldr TEXT,
    sections JSONB,
    data_sources TEXT[],
    models_used TEXT[],
    generation_time_seconds FLOAT,
    quality_score INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- 创建索引
CREATE INDEX idx_reports_symbol ON reports(symbol);
CREATE INDEX idx_reports_created_at ON reports(created_at DESC);
```

---

## 部署验证

### 健康检查

```bash
# 1. 基础健康检查
curl https://your-api.onrender.com/health

# 预期响应
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected",
  "redis": "connected"
}

# 2. 数据库健康检查
curl https://your-api.onrender.com/api/v1/health/database

# 3. 依赖检查
curl https://your-api.onrender.com/api/v1/health/dependencies
```

### API功能测试

```bash
# 1. Quick Chat
curl -X POST "https://your-api.onrender.com/api/v1/chat/quick-chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is Bitcoin?"}'

# 2. 搜索自动补全
curl "https://your-api.onrender.com/api/v1/search/autocomplete?q=btc"

# 3. 热点追踪
curl "https://your-api.onrender.com/api/v1/trending/hotspots?limit=5"

# 4. 报告列表
curl "https://your-api.onrender.com/api/v1/reports?page=1&page_size=10"
```

### 性能验证

```bash
# 1. 响应时间测试
time curl https://your-api.onrender.com/api/v1/chat/quick-chat \
  -X POST -H "Content-Type: application/json" \
  -d '{"query": "What is Ethereum?"}'

# 预期：< 5秒

# 2. 并发测试
ab -n 100 -c 10 https://your-api.onrender.com/health

# 3. 负载测试
siege -c 50 -t 1M https://your-api.onrender.com/health
```

---

## 回滚流程

### Railway回滚

```bash
# 1. 查看部署历史
railway logs --tail 100

# 2. 回滚到上一版本
cd backend
git reset --hard HEAD~1
railway up --yes

# 3. 验证回滚
curl https://your-railway-app.railway.app/health
```

### Render回滚

1. **Dashboard** → Service → Manual Deploy
2. **选择之前的commit** → Deploy
3. **监控日志** → Logs标签页
4. **验证健康状态**

### Git回滚（通用）

```bash
# 1. 查看提交历史
git log --oneline -10

# 2. 回滚到特定commit
git revert <commit-hash>

# 3. 推送更改
git push origin main

# 4. 等待自动部署
# Railway/Render会自动检测并部署
```

### 数据库回滚

```bash
# 使用Alembic回滚迁移
alembic downgrade -1

# 或回滚到特定版本
alembic downgrade <revision>

# 查看当前版本
alembic current
```

---

## 监控部署

### Railway监控

```bash
# 1. 查看实时日志
railway logs

# 2. 查看指标
railway status

# 3. 查看环境变量
railway variables
```

### Render监控

1. **Dashboard** → Service → Logs
2. **Events**: 查看部署历史
3. **Metrics**: CPU/内存使用情况

### Sentry集成

部署完成后检查Sentry:
1. 访问Sentry Dashboard
2. 确认错误追踪正常
3. 检查Performance监控数据

---

## 故障排查

常见部署问题：

1. **构建失败**
   ```bash
   # 检查requirements.txt
   # 确保所有依赖版本兼容
   pip install -r requirements.txt
   ```

2. **健康检查超时**
   ```bash
   # 增加启动时间
   # Railway: healthcheckTimeout = 300
   # Render: Health Check Grace Period = 300s
   ```

3. **环境变量缺失**
   ```bash
   # 列出所有环境变量
   railway variables  # Railway
   # 或在Render Dashboard中检查
   ```

4. **数据库连接失败**
   ```bash
   # 测试连接字符串
   psql $DATABASE_URL -c "SELECT version();"
   ```

---

## 参考资源

- [Railway文档](https://docs.railway.app/)
- [Render文档](https://render.com/docs)
- [Vercel文档](https://vercel.com/docs)
- [故障排查指南](./TROUBLESHOOTING.md)

---

**版本**: v1.0.0
**最后更新**: 2025-01-27
**维护者**: Web3Search DevOps Team
