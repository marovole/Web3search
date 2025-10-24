# 🚀 生产环境部署指南

本指南将帮助您将Web3加密货币AI搜索引擎部署到Railway生产环境。

## 📋 部署前准备

### 1. 账户注册
- Railway账户: https://railway.app (支持GitHub登录)
- OpenRouter API Key: https://openrouter.ai (免费注册)

### 2. 必需工具
✅ Git (已安装)
✅ Railway CLI 4.6.3 (已安装)

## 🎯 方式一：使用Railway CLI部署（推荐）

### 步骤1: 登录Railway

在终端执行：
```bash
railway login
```

这将打开浏览器，完成GitHub授权后返回终端。

### 步骤2: 创建新项目

```bash
# 创建Railway项目
railway init

# 当提示选择时:
# - 选择 "Empty Project"
# - 输入项目名称: web3-search-api
```

### 步骤3: 添加数据库服务

```bash
# 添加PostgreSQL
railway add --database postgres

# 添加Redis
railway add --database redis
```

Railway会自动创建并注入以下环境变量：
- `DATABASE_URL` - PostgreSQL连接字符串
- `REDIS_URL` - Redis连接字符串

### 步骤4: 配置环境变量

```bash
# 设置生产环境
railway variables set ENVIRONMENT=production

# 设置OpenRouter API Key（必需！）
railway variables set OPENROUTER_API_KEY=你的实际key

# 设置CORS（如果有前端域名）
railway variables set CORS_ORIGINS=https://your-frontend.vercel.app

# 设置日志级别
railway variables set LOG_LEVEL=INFO
railway variables set DEBUG=false
```

**🔑 重要提示：请替换 `你的实际key` 为您的真实OpenRouter API Key！**

### 步骤5: 部署应用

```bash
# 部署到Railway
railway up

# 查看部署日志
railway logs
```

部署完成后，Railway会自动：
1. 检测 `railway.json` 配置
2. 执行构建命令: `cd backend && pip install -r requirements.txt`
3. 运行启动脚本: `bash scripts/start.sh`
4. 等待数据库连接并运行迁移
5. 启动Uvicorn生产服务器（4 workers）

### 步骤6: 获取部署URL

```bash
# 生成公开域名
railway domain

# 查看服务状态
railway status
```

您将获得类似的URL: `https://web3-search-api.railway.app`

### 步骤7: 验证部署

```bash
# 测试健康检查
curl https://你的域名.railway.app/health

# 查看API文档
open https://你的域名.railway.app/docs
```

期望输出：
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "version": "1.0.0"
}
```

## 🌐 方式二：使用Railway Web控制台部署

### 步骤1: 推送代码到GitHub

如果您还没有GitHub仓库：

```bash
# 在GitHub创建新仓库: Web3search
# 然后执行：

git remote add origin https://github.com/你的用户名/Web3search.git
git push -u origin main
```

### 步骤2: 在Railway创建项目

1. 访问 https://railway.app/dashboard
2. 点击 **"New Project"**
3. 选择 **"Deploy from GitHub repo"**
4. 授权GitHub并选择 `Web3search` 仓库
5. Railway会自动检测配置并开始部署

### 步骤3: 添加数据库

在Railway项目面板：
1. 点击 **"+ New"**
2. 选择 **"Database" → "Add PostgreSQL"**
3. 再次点击 **"+ New"**
4. 选择 **"Database" → "Add Redis"**

### 步骤4: 配置环境变量

在Railway项目的 **"Variables"** 标签页添加：

| 变量名 | 值 | 说明 |
|--------|-----|------|
| `ENVIRONMENT` | `production` | 环境标识 |
| `OPENROUTER_API_KEY` | `你的实际key` | ⚠️ 必需 |
| `CORS_ORIGINS` | `https://your-frontend.vercel.app` | 前端域名 |
| `DEBUG` | `false` | 关闭调试模式 |
| `LOG_LEVEL` | `INFO` | 日志级别 |

**注意：`DATABASE_URL` 和 `REDIS_URL` 由Railway自动注入，无需手动添加。**

### 步骤5: 触发重新部署

1. 环境变量配置完成后
2. 在 **"Deployments"** 标签页点击 **"Redeploy"**
3. 等待构建和部署完成（约2-3分钟）

### 步骤6: 配置自定义域名

1. 在 **"Settings"** 标签页找到 **"Domains"**
2. 点击 **"Generate Domain"** 获取Railway域名
3. 或添加自定义域名并配置DNS

## 🔧 高级配置

### 配置Celery Worker和Beat（可选）

如果需要后台任务（数据收集、定时任务），需要添加额外的服务：

#### 方法1: 使用Procfile（推荐）

Railway会自动检测 `Procfile` 并创建多个服务：
- `web`: API服务器
- `worker`: Celery任务处理器
- `beat`: Celery定时调度器

在Railway控制台启用这些服务：
1. 进入项目 **"Settings" → "Deploy"**
2. 在 **"Procfile Command"** 下拉菜单选择要运行的服务
3. 为每个服务创建独立的Railway服务实例

#### 方法2: 手动配置启动命令

如果只需要API服务器，保持默认配置即可。

### 配置数据库迁移

首次部署后，如果需要运行Alembic迁移：

```bash
# 通过Railway CLI执行
railway run alembic upgrade head
```

或者在 `scripts/start.sh` 中已自动包含迁移逻辑（第37-40行）。

### 监控和日志

#### 实时日志
```bash
# 查看所有日志
railway logs

# 跟踪实时日志
railway logs --follow
```

#### Web控制台
1. 在Railway项目面板点击 **"Logs"**
2. 实时查看应用输出
3. 支持搜索和过滤

### 扩容配置

如果流量增大，可以调整资源：

1. 进入 **"Settings" → "Resources"**
2. 调整 **"Memory"** 和 **"CPU"**
3. 修改 `scripts/start.sh` 中的 `--workers` 参数：
   ```bash
   # 当前: 4 workers
   # 高流量: 8-16 workers
   --workers ${WORKERS:-8}
   ```

## 🧪 测试部署

### 1. 健康检查
```bash
curl https://你的域名.railway.app/health
```

### 2. Quick Chat测试
```bash
curl -X POST https://你的域名.railway.app/api/v1/quick-chat \
  -H "Content-Type: application/json" \
  -d '{"query": "BTC现在的价格是多少？"}'
```

### 3. Deep Research测试
```bash
curl -X POST https://你的域名.railway.app/api/v1/deep-research \
  -H "Content-Type: application/json" \
  -d '{"query": "分析以太坊的技术和市场表现", "symbol": "ETH"}'
```

## 🐛 常见问题排查

### 问题1: 部署失败 - "Database connection timeout"

**原因**: PostgreSQL服务未就绪或DATABASE_URL未注入

**解决方案**:
```bash
# 检查环境变量
railway variables

# 确保看到 DATABASE_URL 和 REDIS_URL
# 如果没有，重新添加数据库服务
railway add --database postgres
```

### 问题2: API响应500错误

**原因**: OpenRouter API Key未配置或无效

**解决方案**:
```bash
# 检查OPENROUTER_API_KEY
railway variables get OPENROUTER_API_KEY

# 重新设置（注意替换为真实key）
railway variables set OPENROUTER_API_KEY=sk-or-v1-xxxxx
```

### 问题3: CORS错误

**原因**: 前端域名未添加到CORS白名单

**解决方案**:
```bash
# 添加前端域名
railway variables set CORS_ORIGINS=https://your-frontend.vercel.app,https://another-domain.com
```

### 问题4: 构建超时

**原因**: 依赖安装时间过长

**解决方案**:
1. 检查 `backend/requirements.txt` 是否包含不必要的包
2. 在Railway控制台增加构建超时时间：
   - **Settings → Deploy → Build Timeout**: 设置为 15-20分钟

### 问题5: 内存不足

**原因**: 默认512MB内存不足

**解决方案**:
1. **Settings → Resources → Memory**: 调整为1GB或更高
2. 减少Uvicorn workers数量（修改 `scripts/start.sh`）

## 📊 成本估算

### Railway定价（2025年1月）

**免费套餐**:
- $5 免费额度/月
- 512MB RAM
- 1GB磁盘
- 无限带宽

**按需付费**:
- PostgreSQL: $5-10/月（共享实例）
- Redis: $5-10/月（共享实例）
- Web服务: $5-20/月（取决于使用量）

**预估月成本**: $10-30/月（小规模生产环境）

### OpenRouter成本

使用的所有模型均为免费模型：
- `qwen/qwen3-30b-a3b:free`
- `qwen/qwen3-235b-a22b:free`
- `deepseek/deepseek-r1-0528:free`
- `openai/gpt-oss-20b:free`

**AI成本**: $0/月 ✅

## 🔐 安全建议

### 1. 环境变量保护
- ✅ 已配置：`.env` 文件已加入 `.gitignore`
- ⚠️ 确保不要将 `.env.production` 中的真实密钥提交到Git

### 2. API密钥轮换
- 定期更新OpenRouter API Key
- 使用Railway Secrets管理敏感信息

### 3. 速率限制
- ✅ 已实现：Quick Chat 10次/分钟，Deep Research 3次/小时
- 可根据需要在 `backend/app/api/middleware/rate_limit.py` 调整

### 4. HTTPS
- ✅ Railway自动提供HTTPS证书
- 所有请求强制使用HTTPS

## 📞 获取帮助

### Railway支持
- 文档: https://docs.railway.app
- Discord: https://discord.gg/railway
- 状态页面: https://status.railway.app

### 项目资源
- API文档: `https://你的域名.railway.app/docs`
- GitHub仓库: https://github.com/你的用户名/Web3search
- OpenSpec文档: `openspec/` 目录

---

## ✅ 部署检查清单

完成以下步骤以确保部署成功：

- [ ] Railway账户已注册并登录
- [ ] OpenRouter API Key已获取
- [ ] Git仓库已提交所有代码
- [ ] Railway项目已创建
- [ ] PostgreSQL数据库已添加
- [ ] Redis数据库已添加
- [ ] 环境变量已正确配置（特别是OPENROUTER_API_KEY）
- [ ] 应用已部署并启动成功
- [ ] 公开域名已生成
- [ ] 健康检查API返回正常
- [ ] Quick Chat API测试通过
- [ ] Deep Research API测试通过
- [ ] 日志中无严重错误
- [ ] CORS配置正确（如果有前端）

全部完成后，您的Web3加密货币AI搜索引擎已成功部署到生产环境！🎉
