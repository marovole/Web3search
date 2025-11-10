# 🆓 Render.com 免费部署指南

Render.com是Railway的免费替代方案，提供慷慨的免费计划，非常适合小型项目和原型开发。

## 📊 Render vs Railway 对比

| 特性 | Render免费计划 | Railway免费计划 |
|------|---------------|----------------|
| 项目数量 | ✅ 无限 | ⚠️ 2个 |
| PostgreSQL | ✅ 免费（90天数据保留） | ⚠️ 需付费 |
| Redis | ✅ 免费（25MB） | ⚠️ 需付费 |
| 自动休眠 | ⚠️ 15分钟闲置后休眠 | ✅ 持续运行 |
| 冷启动时间 | ⚠️ 30-50秒 | ✅ 即时响应 |
| 月度额度 | ✅ 750小时/月 | ✅ $5额度/月 |
| HTTPS | ✅ 自动 | ✅ 自动 |

**推荐使用场景**：
- ✅ 开发和测试环境
- ✅ 个人项目和原型
- ✅ 低流量应用
- ⚠️ 不适合需要快速响应的生产环境（因为冷启动）

## 🚀 方式一：使用Render控制台部署（推荐）

### 步骤1: 推送代码到GitHub

```bash
# 如果还没有GitHub仓库
# 1. 在GitHub创建新仓库: https://github.com/new
# 2. 仓库名: Web3search
# 3. 选择Public（Render免费计划要求）

# 添加远程仓库
git remote add origin https://github.com/你的用户名/Web3search.git

# 推送代码
git push -u origin main
```

### 步骤2: 连接Render

1. 访问 https://render.com
2. 使用GitHub账户登录
3. 授权Render访问您的GitHub仓库

### 步骤3: 创建Blueprint部署

Render会自动检测 `render.yaml` 配置文件：

1. 点击 **"New +"** → **"Blueprint"**
2. 选择 **"Web3search"** 仓库
3. Render自动检测到 `render.yaml`
4. 点击 **"Apply"**

Render会自动创建：
- ✅ `web3search-api` - FastAPI Web服务
- ✅ `web3search-worker` - Celery Worker（可选）
- ✅ `web3search-db` - PostgreSQL数据库
- ✅ `web3search-redis` - Redis缓存

### 步骤4: 配置环境变量

在Render控制台，进入 `web3search-api` 服务：

1. 点击 **"Environment"** 标签
2. 添加 **OPENROUTER_API_KEY**：
   - Key: `OPENROUTER_API_KEY`
   - Value: `你的实际OpenRouter API Key`
3. 点击 **"Save Changes"**

其他环境变量（`DATABASE_URL`, `REDIS_URL`）会自动注入。

### 步骤5: 等待部署完成

- 首次部署需要 5-8 分钟
- 查看 **"Logs"** 标签监控进度
- 看到 "Application startup complete" 表示成功

### 步骤6: 获取部署URL

部署完成后，您会得到类似的URL：
```
https://web3search-api.onrender.com
```

### 步骤7: 测试API

```bash
# 健康检查
curl https://web3search-api.onrender.com/health

# 查看API文档
open https://web3search-api.onrender.com/docs
```

## 🛠️ 方式二：使用render.yaml自动部署

项目已包含 `render.yaml` 配置文件，推送到GitHub后Render会自动识别。

### render.yaml配置说明

```yaml
services:
  # Web服务：FastAPI应用
  - type: web
    name: web3search-api
    plan: free          # 免费计划

  # Worker服务：Celery后台任务（可选）
  - type: worker
    name: web3search-worker
    plan: free

databases:
  # PostgreSQL：项目数据存储
  - name: web3search-db
    plan: free

  # Redis：缓存和会话
  - name: web3search-redis
    plan: free
```

## ⚙️ 高级配置

### 禁用自动休眠（需付费）

免费计划的服务会在15分钟无活动后休眠。如需保持持续运行：

1. 升级到 **Starter Plan**（$7/月）
2. 在服务设置中关闭 **"Auto-Suspend"**

### 或使用Keep-Alive服务（免费）

使用外部服务定期ping您的API保持唤醒：

**UptimeRobot** (https://uptimerobot.com - 免费)：
1. 创建新监控
2. URL: `https://web3search-api.onrender.com/health`
3. 监控间隔: 5分钟
4. 这样服务永远不会休眠

### 配置Celery Worker

如果需要后台任务（数据收集、定时任务）：

1. 在 `render.yaml` 中保留 `worker` 服务
2. 确保Redis已创建
3. Worker会自动连接到同一个Redis实例

### 数据库备份

**PostgreSQL自动备份**：
- 免费计划：7天保留
- 付费计划：30天保留

手动备份：
```bash
# 在Render控制台找到数据库连接字符串
# 然后使用pg_dump
pg_dump $DATABASE_URL > backup.sql
```

## 🐛 常见问题

### 问题1: 服务启动失败 - "Port already in use"

**原因**: Render使用动态端口，代码必须使用 `$PORT` 环境变量

**解决**: 已在 `scripts/start.sh` 中配置：
```bash
--port ${PORT:-8000}
```

### 问题2: 冷启动时间过长

**原因**: 免费服务休眠后首次请求需要重新启动

**解决**:
- 方案A: 使用UptimeRobot保持唤醒（免费）
- 方案B: 升级到Starter计划（$7/月）

### 问题3: 数据库连接超时

**原因**: PostgreSQL启动较慢

**解决**: `scripts/start.sh` 已包含等待逻辑（最多60秒）

### 问题4: Worker无法连接Redis

**原因**: Redis URL未正确传递

**解决**: 在 `render.yaml` 中已配置自动注入：
```yaml
envVars:
  - key: REDIS_URL
    fromDatabase:
      name: web3search-redis
      property: connectionString
```

## 💰 成本对比

### Render免费计划

**完全免费**，包括：
- Web服务: 750小时/月（足够一个服务全月运行）
- PostgreSQL: 免费（90天数据保留，256MB存储）
- Redis: 免费（25MB）

**限制**：
- 15分钟无活动后休眠
- 冷启动需要30-50秒
- 每月750小时限制

### 如果需要升级

**Starter计划**（$7/月/服务）：
- ✅ 无休眠
- ✅ 更多资源（512MB RAM）
- ✅ 更快构建速度

**PostgreSQL付费**（$7/月）：
- ✅ 30天备份保留
- ✅ 1GB存储
- ✅ 更高连接数

## 🔄 从Render迁移到Railway

如果将来需要迁移：

### 1. 导出数据
```bash
# 导出PostgreSQL
pg_dump $RENDER_DATABASE_URL > data_backup.sql

# 导入到Railway
psql $RAILWAY_DATABASE_URL < data_backup.sql
```

### 2. 更新环境变量
- 复制Render的环境变量到Railway
- 更新 `CORS_ORIGINS` 为新域名

### 3. 测试
- 在Railway测试所有API端点
- 确认数据完整性

### 4. 切换DNS
- 更新前端配置指向新的Railway URL
- 验证流量切换

## 📊 性能优化建议

### 1. 减少冷启动影响

**使用UptimeRobot**：
```
监控URL: https://web3search-api.onrender.com/health
间隔: 5分钟
```

### 2. 优化启动时间

在 `render.yaml` 中减少workers数量：
```yaml
startCommand: cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1
```

### 3. 使用CDN缓存静态内容

如果有前端：
- Vercel: 自动CDN
- Cloudflare: 免费CDN

### 4. Redis缓存策略

优化缓存TTL以适应25MB限制：
```python
# backend/app/core/config.py
CACHE_TTL_PRICE = 300       # 5分钟（原60秒）
CACHE_TTL_PROJECT = 7200    # 2小时（原1小时）
CACHE_TTL_REPORT = 86400    # 1天
```

## 🔐 安全建议

### 1. 环境变量管理

✅ 已配置：
- `OPENROUTER_API_KEY` - 在Render控制台设置
- `DATABASE_URL` - 自动注入
- `REDIS_URL` - 自动注入

⚠️ 不要在 `render.yaml` 中硬编码敏感信息

### 2. CORS配置

生产环境应限制CORS：
```yaml
- key: CORS_ORIGINS
  value: https://your-frontend.vercel.app
```

### 3. 速率限制

已实现（无需修改）：
- Quick Chat: 10次/分钟
- Deep Research: 3次/小时

## ✅ 部署检查清单

完成以下步骤确保部署成功：

- [ ] GitHub仓库已创建并推送代码
- [ ] Render账户已注册（使用GitHub登录）
- [ ] Blueprint已创建并应用 `render.yaml`
- [ ] `OPENROUTER_API_KEY` 已在Render控制台配置
- [ ] Web服务部署成功（查看Logs）
- [ ] PostgreSQL数据库已创建
- [ ] Redis缓存已创建
- [ ] 健康检查API返回正常 (`/health`)
- [ ] API文档可访问 (`/docs`)
- [ ] Quick Chat API测试通过
- [ ] 配置UptimeRobot防止休眠（可选）

## 🎯 部署后测试

```bash
# 1. 设置环境变量
export API_URL=https://web3search-api.onrender.com

# 2. 健康检查
curl $API_URL/health

# 3. Quick Chat测试
curl -X POST $API_URL/api/v1/quick-chat \
  -H "Content-Type: application/json" \
  -d '{"query": "BTC现在的价格是多少？"}'

# 4. Deep Research测试
curl -X POST $API_URL/api/v1/deep-research \
  -H "Content-Type: application/json" \
  -d '{
    "query": "分析以太坊的技术和市场表现",
    "symbol": "ETH"
  }'

# 5. 查看报告列表
curl $API_URL/api/v1/reports
```

## 📞 获取帮助

- Render文档: https://render.com/docs
- Render社区: https://community.render.com
- Render状态: https://status.render.com

---

部署到Render后，您的Web3加密货币AI搜索引擎将完全免费运行！🎉
