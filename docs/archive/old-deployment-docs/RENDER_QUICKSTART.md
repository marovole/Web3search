# 🚀 Render快速部署指南（5分钟）

本指南将帮助您在5分钟内将Web3加密货币AI搜索引擎部署到Render。

## 📋 准备工作

- ✅ Git仓库已初始化（已完成）
- ✅ Render配置文件已创建（render.yaml）
- ⏳ GitHub账户（用于登录Render）
- ⏳ OpenRouter API Key（免费获取：https://openrouter.ai）

## 🎯 部署步骤

### 步骤1: 推送代码到GitHub（2分钟）

#### 方式A: 使用自动化脚本（推荐）

```bash
# 运行GitHub推送脚本
bash scripts/push-to-github.sh
```

脚本会自动：
1. 检查Git状态
2. 引导您创建GitHub仓库
3. 配置远程仓库
4. 推送所有代码

#### 方式B: 手动推送

```bash
# 1. 在GitHub创建新仓库
# 访问 https://github.com/new
# 仓库名: Web3search
# 可见性: Public（重要！）

# 2. 添加远程仓库（替换成您的用户名）
git remote add origin https://github.com/您的用户名/Web3search.git

# 3. 推送代码
git push -u origin main
```

**⚠️ 重要**：仓库必须是 **Public**（公开），Render免费计划不支持私有仓库。

---

### 步骤2: 在Render创建账户（30秒）

1. 访问 https://render.com
2. 点击右上角 **"Get Started"**
3. 选择 **"Sign up with GitHub"**
4. 授权Render访问您的GitHub账户

**无需信用卡**，完全免费！

---

### 步骤3: 部署Blueprint（2分钟）

#### 3.1 创建Blueprint

1. 登录后，点击 **"New +"** 按钮
2. 选择 **"Blueprint"**
3. 在仓库列表中找到 **"Web3search"**
   - 如果没看到，点击 **"Configure account"** 授权访问
4. 点击 **"Connect"**

#### 3.2 Render自动检测配置

Render会自动读取 `render.yaml` 文件，您会看到：

```
✅ web3search-api (Web Service)
✅ web3search-worker (Worker) [可选]
✅ web3search-db (PostgreSQL)
✅ web3search-redis (Redis)
```

#### 3.3 应用配置

1. 在预览页面确认所有服务
2. 点击底部的 **"Apply"** 按钮
3. 等待服务创建（约30秒）

---

### 步骤4: 配置OpenRouter API Key（30秒）

这是唯一需要手动配置的环境变量！

1. 在Render Dashboard找到 **"web3search-api"** 服务
2. 点击进入服务详情页
3. 选择左侧 **"Environment"** 标签
4. 点击 **"Add Environment Variable"**
5. 填写：
   - **Key**: `OPENROUTER_API_KEY`
   - **Value**: `你的OpenRouter API Key`（格式：`sk-or-v1-xxxxx...`）
6. 点击 **"Save Changes"**

#### 如何获取OpenRouter API Key？

1. 访问 https://openrouter.ai
2. 使用GitHub/Google账户登录
3. 点击右上角头像 → **"Keys"**
4. 点击 **"Create Key"**
5. 复制生成的Key（以 `sk-or-v1-` 开头）

**✨ 所有模型都是免费的，API成本 = $0/月！**

---

### 步骤5: 等待部署完成（2-5分钟）

#### 监控部署进度

1. 在 **"web3search-api"** 服务页面
2. 选择 **"Logs"** 标签
3. 观察部署日志

**成功标志**：
```
✅ 数据库连接成功
✅ Application startup complete
✅ Uvicorn running on http://0.0.0.0:10000
```

#### 获取部署URL

部署成功后，您会在页面顶部看到：
```
https://web3search-api.onrender.com
```

---

### 步骤6: 验证部署（30秒）

#### 测试健康检查

在浏览器访问或使用curl：
```bash
curl https://web3search-api.onrender.com/health
```

**期望输出**：
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "version": "1.0.0",
  "environment": "production"
}
```

#### 查看API文档

访问：
```
https://web3search-api.onrender.com/docs
```

您会看到完整的交互式API文档（Swagger UI）。

---

## ✅ 部署完成！

恭喜！您的Web3加密货币AI搜索引擎已成功部署。

### 🔗 快速链接

| 功能 | URL |
|------|-----|
| API文档 | `https://你的域名.onrender.com/docs` |
| 健康检查 | `https://你的域名.onrender.com/health` |
| Render控制台 | https://dashboard.render.com |

### 🧪 测试API

#### 1. Quick Chat（快速对话）

```bash
curl -X POST https://你的域名.onrender.com/api/v1/quick-chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "BTC现在的价格是多少？"
  }'
```

#### 2. Deep Research（深度研究）

```bash
curl -X POST https://你的域名.onrender.com/api/v1/deep-research \
  -H "Content-Type: application/json" \
  -d '{
    "query": "分析以太坊的技术架构和市场表现",
    "symbol": "ETH"
  }'
```

#### 3. 查看报告列表

```bash
curl https://你的域名.onrender.com/api/v1/reports
```

---

## 🔧 高级配置（可选）

### 配置自定义域名

1. 在Render服务页面选择 **"Settings"**
2. 找到 **"Custom Domain"**
3. 添加您的域名（如 `api.yoursite.com`）
4. 在DNS提供商添加CNAME记录

### 禁用Worker服务（节省资源）

如果暂时不需要后台任务（数据收集、定时任务）：

1. 在Render Dashboard找到 **"web3search-worker"**
2. 点击 **"Suspend"** 暂停服务
3. 稍后需要时可以重新启用

### 防止服务休眠

免费计划的服务15分钟无活动会休眠。使用 **UptimeRobot** 保持唤醒：

1. 访问 https://uptimerobot.com（免费）
2. 创建新监控：
   - **Monitor Type**: HTTP(s)
   - **URL**: `https://你的域名.onrender.com/health`
   - **Monitoring Interval**: 5 minutes
3. 服务将永远保持活跃

---

## 📊 资源使用情况

Render免费计划提供：

| 资源 | 配额 | 您的使用 |
|------|------|---------|
| Web Service | 750小时/月 | 1个服务 = 750小时 ✅ |
| PostgreSQL | 256MB | ~50-100MB（估计）✅ |
| Redis | 25MB | ~5-10MB（估计）✅ |
| 带宽 | 100GB/月 | 足够使用 ✅ |

**完全免费，无隐藏费用！**

---

## 🐛 常见问题

### Q1: 首次访问很慢怎么办？

**A**: 免费服务休眠后首次启动需要30-50秒。解决方案：
- 使用UptimeRobot防止休眠（见上方）
- 或者升级到Starter计划（$7/月）

### Q2: API返回500错误

**A**: 检查环境变量配置：
1. 确认 `OPENROUTER_API_KEY` 已正确设置
2. 检查Logs查看详细错误信息
3. 确保数据库和Redis连接正常

### Q3: 数据库连接失败

**A**: 等待数据库完全启动：
- PostgreSQL首次创建需要1-2分钟
- 在Logs中查看 "数据库连接成功" 消息

### Q4: Worker服务报错

**A**: Worker是可选的，主要用于后台任务：
- 如果暂时不需要，可以suspend
- 确保Redis服务已创建并运行
- 检查 `REDIS_URL` 环境变量已注入

---

## 🔄 更新部署

代码更新后重新部署：

```bash
# 1. 提交更改
git add .
git commit -m "feat: 添加新功能"

# 2. 推送到GitHub
git push origin main

# 3. Render自动检测并重新部署（约2分钟）
```

Render会自动监听GitHub仓库，每次推送都会触发自动部署。

---

## 📞 获取帮助

- **Render文档**: https://render.com/docs
- **Render社区**: https://community.render.com
- **项目文档**: README.md
- **详细部署指南**: DEPLOYMENT_RENDER.md

---

## 🎉 下一步

1. **开发前端** - 创建React应用连接此API
2. **配置域名** - 使用自定义域名
3. **监控日志** - 在Render Dashboard查看实时日志
4. **添加功能** - 扩展分析维度和数据源

您的Web3加密货币AI搜索引擎已经在生产环境运行了！🚀
