# Web3 Search 部署文档

## 📚 目录

- [概览](#概览)
- [前置要求](#前置要求)
- [后端部署 (Render)](#后端部署-render)
- [前端部署 (Vercel)](#前端部署-vercel)
- [数据库部署 (Render Postgres)](#数据库部署-render-postgres)
- [Redis部署 (Render Redis)](#redis部署-render-redis)
- [环境变量配置](#环境变量配置)
- [部署验证](#部署验证)
- [常见问题](#常见问题)
- [监控与维护](#监控与维护)

---

## 概览

### 架构图

```
┌─────────────────┐
│   Vercel CDN    │ ← 前端静态资源
│  (Frontend)     │
└────────┬────────┘
         │ HTTPS
         ↓
┌─────────────────┐
│  Render API     │ ← 后端API服务
│  (Backend)      │
└────────┬────────┘
         │
    ┌────┴────┐
    ↓         ↓
┌─────────┐ ┌─────────┐
│Postgres │ │  Redis  │
│  (DB)   │ │ (Cache) │
└─────────┘ └─────────┘
```

### 服务清单

| 服务 | 平台 | 类型 | 说明 |
|------|------|------|------|
| 前端 | Vercel | Static Site | Next.js/React应用 |
| 后端 | Render | Web Service | FastAPI服务 |
| 数据库 | Render | PostgreSQL | 主数据库 |
| 缓存 | Render | Redis | 会话和缓存 |

---

## 前置要求

### 账号注册

- ✅ [Render账号](https://render.com) - 后端、数据库、Redis
- ✅ [Vercel账号](https://vercel.com) - 前端部署
- ✅ [GitHub账号](https://github.com) - 代码托管

### 本地工具

```bash
# Git
git --version  # >= 2.0

# Node.js（前端开发）
node --version  # >= 18.0
npm --version   # >= 9.0

# Python（后端开发）
python3 --version  # >= 3.11
pip3 --version     # >= 23.0

# Render CLI（可选）
npm install -g @render/cli

# Vercel CLI（可选）
npm install -g vercel
```

---

## 后端部署 (Render)

### 步骤 1: 创建Web Service

1. 登录 [Render Dashboard](https://dashboard.render.com)
2. 点击 **New** → **Web Service**
3. 连接GitHub仓库: `https://github.com/marovole/Web3search`
4. 配置服务:

```yaml
Name: web3search-api
Region: Oregon (US West)
Branch: main
Root Directory: backend
Runtime: Python 3
Build Command: pip install -r requirements.txt
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### 步骤 2: 选择计划

- **免费计划**: 适合开发测试
  - 512 MB RAM
  - 自动休眠（15分钟无活动）
  - 100 GB带宽/月

- **Starter计划** ($7/月): 适合生产环境
  - 512 MB RAM
  - 无休眠
  - 100 GB带宽/月

### 步骤 3: 配置环境变量

在Render Dashboard中添加环境变量（详见[环境变量配置](#环境变量配置)）

### 步骤 4: 部署

1. 点击 **Create Web Service**
2. 等待构建完成（约3-5分钟）
3. 查看部署日志，确保无错误
4. 访问分配的URL: `https://web3search-api.onrender.com`

### 步骤 5: 自定义域名（可选）

1. 进入Service Settings
2. 点击 **Custom Domains**
3. 添加域名: `api.web3search.com`
4. 配置DNS CNAME记录:
```
CNAME api.web3search.com → web3search-api.onrender.com
```

---

## 前端部署 (Vercel)

### 方法 1: Vercel Dashboard（推荐）

1. 登录 [Vercel Dashboard](https://vercel.com/dashboard)
2. 点击 **Add New** → **Project**
3. 导入GitHub仓库: `marovole/Web3search`
4. 配置项目:

```yaml
Framework Preset: Vite
Root Directory: frontend
Build Command: npm run build
Output Directory: dist
Install Command: npm install
```

5. 配置环境变量（详见[环境变量配置](#环境变量配置)）
6. 点击 **Deploy**
7. 等待部署完成（约2-3分钟）

### 方法 2: Vercel CLI

```bash
# 进入前端目录
cd frontend

# 登录Vercel
npx vercel login

# 部署到生产环境
npx vercel --prod

# 按提示输入:
# ? Set up and deploy "~/Web3search/frontend"? [Y/n] y
# ? Which scope do you want to deploy to? [Your Account]
# ? Link to existing project? [y/N] n
# ? What's your project's name? web3search
# ? In which directory is your code located? ./
```

### 自定义域名

1. 在Vercel Project Settings中
2. 点击 **Domains**
3. 添加域名: `web3search.com` 和 `www.web3search.com`
4. 配置DNS记录（Vercel会自动提示）:
```
A     @             76.76.21.21
CNAME www           cname.vercel-dns.com
```

---

## 数据库部署 (Render Postgres)

### 创建数据库

1. 在Render Dashboard点击 **New** → **PostgreSQL**
2. 配置数据库:

```yaml
Name: web3search-db
Region: Oregon (US West) # 与API服务同区域
PostgreSQL Version: 16
```

3. 选择计划:
   - **Free**: 1 GB存储，90天后删除
   - **Starter** ($7/月): 256 MB RAM，1 GB存储
   - **Standard** ($20/月): 1 GB RAM，10 GB存储

### 获取连接信息

创建完成后，在Database Info中获取:
- **Internal Database URL**: `postgresql://...@dpg-xxx-a/web3search_db`
- **External Database URL**: `postgresql://...@dpg-xxx-a.oregon-postgres.render.com/web3search_db`

### 初始化数据库

```bash
# 本地运行迁移（连接到Render数据库）
export DATABASE_URL="postgresql://...@dpg-xxx-a.oregon-postgres.render.com/web3search_db"

cd backend

# 运行Alembic迁移
alembic upgrade head

# 或者使用Python脚本初始化
python scripts/init_db.py
```

### 数据库备份

**自动备份**（Starter计划及以上）:
- 每日自动备份
- 保留7天
- 可手动恢复

**手动备份**:
```bash
# 导出数据库
pg_dump -Fc $DATABASE_URL > backup.dump

# 恢复数据库
pg_restore -d $DATABASE_URL backup.dump
```

---

## Redis部署 (Render Redis)

### 创建Redis实例

1. 在Render Dashboard点击 **New** → **Redis**
2. 配置:

```yaml
Name: web3search-redis
Region: Oregon (US West)
Plan: Free (25 MB) 或 Starter ($7/月, 256 MB)
```

### 获取连接信息

- **Internal Redis URL**: `redis://red-xxx:6379`
- **External Redis URL**: `rediss://red-xxx.oregon-redis.render.com:6379`

### 测试连接

```bash
# 使用redis-cli测试
redis-cli -u $REDIS_URL ping
# 应返回: PONG
```

---

## 环境变量配置

### 后端环境变量 (Render)

在Render Web Service的Environment中配置:

```bash
# ====================
# 必填变量
# ====================

# 数据库
DATABASE_URL=postgresql://user:pass@dpg-xxx.oregon-postgres.render.com/web3search_db

# Redis
REDIS_URL=rediss://red-xxx.oregon-redis.render.com:6379

# OpenRouter API（免费）
OPENROUTER_API_KEY=sk-or-v1-xxx...

# ====================
# 可选变量
# ====================

# 环境标识
ENVIRONMENT=production

# API Keys（可选的数据源）
COINGECKO_API_KEY=CG-xxx...
ETHERSCAN_API_KEY=xxx...
TWITTER_BEARER_TOKEN=xxx...
REDDIT_CLIENT_ID=xxx...
REDDIT_CLIENT_SECRET=xxx...
CRYPTOPANIC_API_KEY=xxx...

# Sentry错误追踪
SENTRY_DSN=https://xxx@sentry.io/xxx

# 日志级别
LOG_LEVEL=INFO

# CORS（如果前端域名不同）
CORS_ORIGINS=https://web3search.com,https://www.web3search.com

# Celery Worker数量
CELERY_WORKERS=2
```

### 前端环境变量 (Vercel)

在Vercel Project Settings的Environment Variables中配置:

```bash
# API Base URL
VITE_API_URL=https://web3search-api.onrender.com

# 可选：启用分析
VITE_ENABLE_ANALYTICS=true
```

### 获取API Keys

#### OpenRouter API Key（必需，免费）

1. 访问 [OpenRouter](https://openrouter.ai/)
2. 注册账号
3. 进入API Keys页面
4. 创建新API Key
5. **免费额度**: $5 credits

#### CoinGecko API Key（可选）

1. 访问 [CoinGecko API](https://www.coingecko.com/en/api)
2. 免费计划: 10,000 次/月
3. 付费计划: $129/月起

#### Etherscan API Key（可选）

1. 访问 [Etherscan](https://etherscan.io/apis)
2. 免费计划: 5次/秒

#### Twitter API（可选）

1. 访问 [Twitter Developer Portal](https://developer.twitter.com/)
2. 创建App
3. 获取Bearer Token
4. 免费计划: 500,000 tweets/月

---

## 部署验证

### 后端健康检查

```bash
# 检查API状态
curl https://web3search-api.onrender.com/health

# 预期响应:
{
  "status": "healthy",
  "timestamp": "2025-01-26T10:00:00",
  "version": "1.0.0"
}
```

### 测试关键端点

```bash
# 1. Quick Chat
curl -X POST https://web3search-api.onrender.com/api/v1/chat/quick-chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What is Bitcoin?"}'

# 2. 搜索自动补全
curl "https://web3search-api.onrender.com/api/v1/search/autocomplete?q=btc"

# 3. 市场热点
curl "https://web3search-api.onrender.com/api/v1/trending/hotspots?limit=5"
```

### 前端验证

1. 访问前端URL: `https://web3search.vercel.app`
2. 检查页面加载
3. 测试Quick Chat功能
4. 测试搜索自动补全
5. 查看热点面板

### 数据库连接验证

```bash
# 连接到生产数据库
psql $DATABASE_URL

# 检查表
\dt

# 查询报告数量
SELECT COUNT(*) FROM reports;
```

---

## 常见问题

### 后端问题

#### ❌ 问题: Render服务启动失败

**症状**:
```
Error: Failed to bind to $PORT
```

**解决方案**:
确保Start Command使用Render提供的`$PORT`环境变量:
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

---

#### ❌ 问题: 数据库连接超时

**症状**:
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**解决方案**:
1. 确保使用Internal Database URL（同区域更快）
2. 检查数据库是否正在运行
3. 验证`DATABASE_URL`环境变量正确

---

#### ❌ 问题: Redis连接失败

**症状**:
```
redis.exceptions.ConnectionError: Error connecting to Redis
```

**解决方案**:
1. 确保Redis实例正在运行
2. 使用`rediss://`（带SSL）而不是`redis://`
3. 检查`REDIS_URL`环境变量

---

#### ❌ 问题: OpenRouter API限流

**症状**:
```
429 Too Many Requests
```

**解决方案**:
1. 检查OpenRouter账户余额
2. 实现请求队列（已实现）
3. 使用LLM fallback机制（已实现）

---

### 前端问题

#### ❌ 问题: Vercel构建失败

**症状**:
```
Error: Build failed with exit code 1
```

**解决方案**:
1. 检查`package.json`中的依赖
2. 确保`vite.config.ts`配置正确
3. 查看Vercel构建日志获取详细错误

---

#### ❌ 问题: API请求CORS错误

**症状**:
```
Access to fetch at 'https://api.web3search.com' from origin 'https://web3search.com'
has been blocked by CORS policy
```

**解决方案**:
在后端添加前端域名到`CORS_ORIGINS`:
```bash
CORS_ORIGINS=https://web3search.com,https://www.web3search.com
```

---

#### ❌ 问题: 环境变量未生效

**症状**:
前端无法连接到API

**解决方案**:
1. 确保环境变量名以`VITE_`开头
2. 重新部署前端
3. 清除浏览器缓存

---

### 性能问题

#### ❌ 问题: Render免费服务自动休眠

**症状**:
首次请求响应时间 > 30秒

**解决方案**:
- **短期**: 使用定时ping保持唤醒
- **长期**: 升级到Starter计划（$7/月）

```bash
# 使用GitHub Actions定时ping
# .github/workflows/keep-alive.yml
name: Keep Alive
on:
  schedule:
    - cron: '*/14 * * * *'  # 每14分钟
jobs:
  keep-alive:
    runs-on: ubuntu-latest
    steps:
      - run: curl https://web3search-api.onrender.com/health
```

---

#### ❌ 问题: 数据库连接池耗尽

**症状**:
```
sqlalchemy.exc.TimeoutError: QueuePool limit exceeded
```

**解决方案**:
调整连接池配置（`app/core/database.py`）:
```python
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=5,        # 增加到10
    max_overflow=10,    # 增加到20
    pool_timeout=30,
)
```

---

## 监控与维护

### Sentry错误追踪

1. 注册 [Sentry账号](https://sentry.io/)
2. 创建新项目
3. 获取DSN: `https://xxx@sentry.io/xxx`
4. 在Render中设置`SENTRY_DSN`环境变量
5. 查看Sentry Dashboard了解错误

### 日志查看

**Render日志**:
```bash
# 在Render Dashboard
Service → Logs → 实时日志

# 或使用Render CLI
render logs web3search-api --tail
```

**Vercel日志**:
```bash
# 在Vercel Dashboard
Project → Deployments → [最新部署] → Logs

# 或使用Vercel CLI
vercel logs web3search-frontend
```

### 性能监控

**关键指标**:
- 🔥 API响应时间（目标 < 3秒）
- 📊 数据库查询时间（目标 < 100ms）
- 💾 Redis命中率（目标 > 80%）
- 📈 错误率（目标 < 1%）

**工具**:
- Render内置监控（Metrics标签页）
- Sentry性能追踪
- 自定义Grafana仪表板（可选）

### 定期维护

**每周**:
- 检查Sentry错误报告
- 审查API使用量
- 清理旧报告（可选）

**每月**:
- 数据库备份
- 依赖更新（`pip list --outdated`, `npm outdated`）
- 检查账单

**每季度**:
- 安全审计
- 性能优化
- 容量规划

---

## 扩展和优化

### 水平扩展

**后端扩展**:
1. 在Render中增加实例数
2. 配置负载均衡（Render自动）
3. 调整Celery Worker数量

**数据库扩展**:
1. 升级到更大的数据库计划
2. 启用连接池
3. 添加只读副本（Render Plus计划）

### 垂直扩展

**升级计划**:
- Starter → Standard → Pro → Pro Plus

**资源监控**:
```bash
# 检查资源使用
render metrics web3search-api

# 查看数据库大小
psql $DATABASE_URL -c "SELECT pg_size_pretty(pg_database_size(current_database()));"
```

---

## 回滚策略

### Render回滚

1. 进入Service → Deploys
2. 找到上一个成功的部署
3. 点击 **Rollback to this deploy**

### Vercel回滚

1. 进入Project → Deployments
2. 找到上一个生产部署
3. 点击 **Promote to Production**

### 数据库回滚

```bash
# 使用Alembic降级
alembic downgrade -1  # 降级一个版本
alembic downgrade <revision>  # 降级到特定版本

# 从备份恢复
pg_restore -d $DATABASE_URL backup.dump
```

---

## 成本估算

### 最小配置（开发/测试）

| 服务 | 计划 | 费用 |
|------|------|------|
| Render Web Service | Free | $0 |
| Render PostgreSQL | Free | $0 |
| Render Redis | Free | $0 |
| Vercel | Hobby | $0 |
| **总计** | | **$0/月** |

**限制**:
- 服务会自动休眠
- 数据库90天后删除
- 有带宽限制

### 推荐配置（生产环境）

| 服务 | 计划 | 费用 |
|------|------|------|
| Render Web Service | Starter | $7 |
| Render PostgreSQL | Starter | $7 |
| Render Redis | Starter | $7 |
| Vercel | Pro（可选） | $20 |
| OpenRouter API | Free | $0 |
| **总计** | | **$21-41/月** |

**优势**:
- 无休眠
- 持久化存储
- 更高性能
- 更多带宽

---

## 安全最佳实践

### 环境变量安全

- ✅ 永远不要提交`.env`文件到Git
- ✅ 使用强密码和复杂的API密钥
- ✅ 定期轮换敏感凭证
- ✅ 使用Render/Vercel的加密环境变量

### 网络安全

- ✅ 启用HTTPS（Render和Vercel自动）
- ✅ 配置CORS限制
- ✅ 实施速率限制（已实现）
- ✅ 使用防火墙规则（Render自动）

### 数据安全

- ✅ 定期备份数据库
- ✅ 加密敏感数据
- ✅ 实施访问控制（未来）
- ✅ 审计日志记录

---

## 支持与帮助

### 文档

- [Render文档](https://render.com/docs)
- [Vercel文档](https://vercel.com/docs)
- [FastAPI文档](https://fastapi.tiangolo.com/)
- [Vite文档](https://vitejs.dev/)

### 社区

- [GitHub Issues](https://github.com/marovole/Web3search/issues)
- [Render社区](https://community.render.com/)
- [Vercel Discord](https://vercel.com/discord)

---

**文档最后更新**: 2025-01-26
