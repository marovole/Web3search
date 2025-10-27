# Web3 AI Search Engine

<div align="center">

🚀 **专注于加密货币领域的AI驱动研究平台**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Phase 14 Complete](https://img.shields.io/badge/Phase%2014-Complete%20✓-success.svg)](openspec/changes/archive/)
[![Backend](https://img.shields.io/badge/backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Frontend](https://img.shields.io/badge/frontend-React-61DAFB.svg)](https://reactjs.org/)
[![Deployed on Render](https://img.shields.io/badge/deployed-Render-46e3b7.svg)](https://web3search-api.onrender.com)
[![Deployed on Vercel](https://img.shields.io/badge/deployed-Vercel-000000.svg)](https://frontend-fnkjroe8s-marovole-gmailcoms-projects.vercel.app)
[![Test Coverage](https://img.shields.io/badge/coverage-80%25+-brightgreen.svg)](backend/app/docs/TEST_VALIDATION_REPORT.md)
[![Documentation](https://img.shields.io/badge/docs-14%20files-blue.svg)](backend/app/docs/)

[功能特性](#-功能特性) •
[快速开始](#-快速开始) •
[技术栈](#️-技术栈) •
[API文档](#-api文档) •
[部署](#-部署) •
[贡献指南](#-贡献指南)

</div>

---

## 📖 项目简介

Web3 AI Search Engine 是一个专为加密货币领域打造的智能研究平台，结合了多数据源采集、AI分析和专业报告生成功能。通过OpenRouter免费模型实现零AI成本运营，支持Quick Chat快速问答和Deep Research深度研究两种模式。

### 🎯 核心价值

- **零AI成本**: 使用OpenRouter免费模型（Llama-3.3-70B、Qwen-2.5-72B等）
- **多源数据聚合**: 整合CoinGecko、Etherscan、Twitter、Reddit、CryptoPanic
- **专业报告生成**: 30秒生成10+章节深度研究报告（含TL;DR、技术面、链上数据、竞品对比等）
- **双模式交互**: Quick Chat（3秒响应）+ Deep Research（30秒专业报告）
- **生产级质量**: 完整的错误处理、降级策略、监控告警、负载测试

---

## ✨ 功能特性

### 🤖 AI分析引擎

#### Quick Chat模式（3秒内响应）
- 💬 自然语言问答
- 🔍 价格查询和市场数据
- 📊 项目对比分析
- 🧠 概念解释和教育

#### Deep Research模式（30秒专业报告）
- 📑 **TL;DR生成器** - 一句话投资观点 + 牛熊论点 + 置信度评分
- ⏱️ **时间窗分析器** - 24h/7d/30d多时间框架分析
- 💭 **社媒情绪分析器** - Twitter/Reddit/新闻情绪追踪
- 📈 **技术面分析器** - RSI/MACD/布林带 + 支撑阻力位 + 衍生品市场
- ⛓️ **链上数据分析器** - TVL/协议收入/用户活动/鲸鱼持仓
- 🏆 **竞品对比分析器** - 10大赛道竞品映射 + 估值倍数计算
- 💰 **代币经济学分析器** - 供应结构/解锁时间表/价值捕获路径
- ⚠️ **风险评估生成器** - 5类风险识别 + 催化剂分析 + 情景分析
- 🎯 **结论综合器** - 短中期观点 + 关键跟踪指标 + 整体置信度

### 📊 数据采集层

#### 5个数据源集成
| 数据源 | 功能 | 更新频率 |
|--------|------|----------|
| **CoinGecko** | 价格、市值、成交量、历史数据 | 每1分钟 |
| **Etherscan** | 链上数据、持币分布、交易历史 | 每天凌晨2点 |
| **Twitter** | 社交情绪、热点话题、KOL观点 | 每6小时 |
| **Reddit** | 社区讨论、讨论热度、情绪分布 | 每6小时 |
| **CryptoPanic** | 新闻聚合、新闻情绪分析 | 每30分钟 |

#### Celery定时任务
- 🕐 **每1分钟**: 更新热门币种价格（Top 100）
- 🕑 **每1小时**: 项目快照、热点识别
- 🕕 **每6小时**: 社交数据更新
- 🕗 **每天凌晨2点**: 链上数据更新
- 🕚 **每30分钟**: 新闻采集
- 🕒 **每天凌晨3点**: 清理过期缓存

### 🎨 前端功能

- ✅ **响应式设计** - 支持桌面/平板/移动端
- ✅ **模式切换** - Quick Chat ↔ Deep Research
- ✅ **实时流式输出** - Server-Sent Events（SSE）
- ✅ **报告导出** - Markdown/PDF/分享链接
- ✅ **搜索自动补全** - 300ms防抖 + 键盘导航
- ✅ **市场热点面板** - 5维度综合评分（Twitter 25% + Reddit 20% + 价格 30% + 成交量 15% + 新闻 10%）
- ✅ **项目监控列表** - 最多20项，一键生成报告
- ✅ **报告历史记录** - 最多50条，自动去重
- ✅ **Markdown渲染** - 代码高亮、表格、图表
- ✅ **目录导航** - 自动提取标题、锚点跳转

### 🛡️ 质量保证

#### 错误处理和降级
- ✅ 10+自定义异常类型
- ✅ 4个全局异常处理器
- ✅ 数据源自动降级（主源 → 备用源 → 缓存）
- ✅ LLM模型自动降级（3个免费模型梯度）
- ✅ 自动重试机制（指数退避）
- ✅ 断路器模式（连续失败5次后熔断10分钟）

#### 监控和告警 🆕
- ✅ **Sentry集成** - 错误追踪、性能监控、自定义事件
- ✅ **实时Dashboard** - 响应时间、错误率、数据源成功率
- ✅ **智能告警** - 错误率>5%、P95延迟>3s自动触发
- ✅ **Slack通知** - 关键错误发送到#alerts频道
- ✅ **性能追踪** - trace_operation()装饰器自动记录
- ✅ **指标监控** - 16个关键指标（性能、错误、业务、基础设施）
- ✅ **结构化日志** - JSON格式、request_id追踪、敏感数据脱敏
- ✅ **日志轮转** - 按大小100MB或每天自动轮转

#### 速率限制
- ✅ IP级限流
- ✅ Quick Chat: 10次/分钟
- ✅ Deep Research: 3次/小时
- ✅ 429状态码和Retry-After头

#### 测试覆盖 🆕
- ✅ **单元测试** - 205+测试用例，覆盖率>80%
- ✅ **E2E测试** - 4个完整用户流程（Quick Chat、Deep Research、Search、Reports）
- ✅ **负载测试** - 5个端点性能基准，支持100并发用户
- ✅ **数据源验证** - 4个Fallback机制测试
- ✅ **缓存验证** - 命中率>70%，响应时间提升88-94%
- ✅ **日志质量** - JSON格式、request_id传播、敏感数据脱敏
- ✅ **告警测试** - Sentry集成验证、Slack通知验证

---

## 🛠️ 技术栈

### 后端
- **框架**: FastAPI 0.104.1
- **数据库**: PostgreSQL 17（SQLAlchemy 2.0.23）
- **缓存**: Redis 7
- **任务队列**: Celery 5.3.4 + Celery Beat
- **AI**: OpenRouter（Llama-3.3-70B、Qwen-2.5-72B等免费模型）
- **数据可视化**: Matplotlib 3.8.2、Plotly 5.18.0
- **报告生成**: WeasyPrint 60.1（PDF）、Markdown2 2.4.10

### 前端
- **框架**: React 18 + TypeScript 5.2
- **构建工具**: Vite 5.0
- **路由**: React Router v6
- **样式**: Tailwind CSS 3.3 + Tailwind Typography
- **HTTP客户端**: Axios 1.6
- **Markdown渲染**: react-markdown 9.0 + remark-gfm 4.0
- **代码高亮**: react-syntax-highlighter 15.5

### 测试
- **E2E测试**: Playwright 1.56.1
- **负载测试**: Locust 2.20.0
- **单元测试**: Pytest 7.4.3

### 部署
- **后端**: Render（Web Service + Worker + Beat）
- **前端**: Vercel
- **监控**: Sentry

---

## 🚀 快速开始

### 前置要求

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+

### 1. 克隆仓库

```bash
git clone https://github.com/marovole/Web3search.git
cd Web3search
```

### 2. 后端设置

```bash
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑.env，填入必要的API密钥

# 初始化数据库（方法1：通过API，推荐）
curl -X POST http://localhost:8000/admin/init-db

# 启动API服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 新终端：启动Celery Worker
celery -A app.tasks.celery_app worker -l info -Q high_priority,default,low_priority --concurrency 2

# 新终端：启动Celery Beat（定时任务调度器）
celery -A app.tasks.celery_app beat -l info
```

### 3. 前端设置

```bash
cd frontend

# 安装依赖
npm install

# 配置环境变量
cp .env.example .env.local
# 编辑.env.local，设置VITE_API_BASE_URL

# 启动开发服务器
npm run dev
```

### 4. 访问应用

- **前端**: http://localhost:5173
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

---

## 🔧 环境变量配置

### 后端 (.env)

```bash
# ================================
# 基础配置
# ================================
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# ================================
# 数据库
# ================================
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/web3search
REDIS_URL=redis://localhost:6379/0

# ================================
# OpenRouter API（必需）
# ================================
OPENROUTER_API_KEY=sk-or-v1-xxx

# ================================
# 数据源API Keys
# ================================
COINGECKO_API_KEY=xxx  # 可选，有免费额度
ETHERSCAN_API_KEY=xxx
TWITTER_BEARER_TOKEN=xxx
REDDIT_CLIENT_ID=xxx
REDDIT_CLIENT_SECRET=xxx
CRYPTOPANIC_API_KEY=xxx

# ================================
# Celery
# ================================
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# ================================
# CORS配置
# ================================
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# ================================
# Sentry（可选）
# ================================
SENTRY_DSN=https://xxx@sentry.io/xxx
```

### 前端 (.env.local)

```bash
# API基础URL
VITE_API_BASE_URL=http://localhost:8000

# Mock模式（开发调试用）
VITE_USE_MOCK_API=false
```

---

## 📚 API文档

### Swagger UI
访问 http://localhost:8000/docs 查看交互式API文档。

### 核心端点

#### Chat接口
```bash
# Quick Chat（快速问答）
POST /api/v1/chat/quick-chat
Content-Type: application/json

{
  "query": "What is Bitcoin?",
  "conversation_id": null
}

# Deep Research（深度研究报告）
POST /api/v1/chat/deep-research
Content-Type: application/json

{
  "query": "BTC",
  "conversation_id": null
}

# Deep Research Stream（流式输出）
GET /api/v1/chat/deep-research/stream?query=BTC
```

#### 报告接口
```bash
# 获取报告列表
GET /api/v1/reports/reports?page=1&page_size=10

# 获取单个报告
GET /api/v1/reports/reports/{report_id}

# 创建分享链接
POST /api/v1/reports/reports/{report_id}/share
Content-Type: application/json

{
  "expires_days": 7
}

# 获取分享报告
GET /api/v1/reports/reports/shared/{share_token}
```

#### 搜索接口
```bash
# 自动补全
GET /api/v1/search/autocomplete?q=BTC

# 市场热点
GET /api/v1/trending/hotspots?limit=10&force_refresh=false
```

---

## 🚢 部署

### Render部署（后端）

1. **创建Render账号**并连接GitHub仓库

2. **创建PostgreSQL数据库**
   - 服务类型：PostgreSQL
   - 版本：17
   - 计划：Free

3. **创建Redis实例**
   - 服务类型：Redis
   - 版本：7
   - 计划：Free

4. **创建Web Service**（API）
   - 服务类型：Web Service
   - 构建命令：`pip install -r requirements.txt`
   - 启动命令：`uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - 环境变量：参考`.env.example`

5. **创建Background Worker**（Celery Worker）
   - 服务类型：Background Worker
   - 构建命令：`pip install -r requirements.txt`
   - 启动命令：`celery -A app.tasks.celery_app worker -l info -Q high_priority,default,low_priority --concurrency 2`

6. **创建Cron Job**（Celery Beat）
   - 服务类型：Cron Job
   - 构建命令：`pip install -r requirements.txt`
   - 启动命令：`celery -A app.tasks.celery_app beat -l info`
   - 计划：`@hourly`（或自定义）

7. **初始化数据库表**
   ```bash
   curl -X POST https://your-api.onrender.com/admin/init-db
   ```

### Vercel部署（前端）

1. **安装Vercel CLI**
   ```bash
   npm install -g vercel
   ```

2. **登录Vercel**
   ```bash
   vercel login
   ```

3. **部署到生产环境**
   ```bash
   cd frontend
   vercel --prod --yes
   ```

4. **配置环境变量**（在Vercel Dashboard）
   - `VITE_API_BASE_URL`: https://your-api.onrender.com

详细部署指南：[backend/app/docs/DEPLOYMENT.md](backend/app/docs/DEPLOYMENT.md)

---

## 📖 完整文档 🆕

### API文档
- **[API错误码](backend/app/docs/API_ERRORS.md)** - 40x/50x错误码完整说明
- **[API认证](backend/app/docs/API_AUTH.md)** - 认证和授权机制
- **[API教程](backend/app/docs/API_TUTORIAL.md)** - 常见场景使用示例
- **[API变更日志](backend/app/docs/API_CHANGELOG.md)** - 版本历史和迁移指南

### 运维文档
- **[监控指南](backend/app/docs/MONITORING_GUIDE.md)** - Sentry监控配置和使用
- **[指标说明](backend/app/docs/METRICS.md)** - 16个关键指标定义
- **[故障排查](backend/app/docs/TROUBLESHOOTING.md)** - 20+常见问题解决方案
- **[扩容指南](backend/app/docs/SCALING.md)** - 何时扩容、如何扩容
- **[数据库维护](backend/app/docs/DATABASE_MAINTENANCE.md)** - 备份、恢复、优化

### 开发文档
- **[开发环境设置](backend/app/docs/DEV_SETUP.md)** - 本地开发环境完整配置
- **[代码审查清单](backend/app/docs/CODE_REVIEW.md)** - 代码质量标准
- **[安全最佳实践](backend/app/docs/SECURITY.md)** - API、数据库、依赖安全
- **[测试验证报告](backend/app/docs/TEST_VALIDATION_REPORT.md)** - 完整测试策略

---

## 🧪 测试

### 运行E2E测试
```bash
cd frontend
npm run test              # 运行所有测试
npm run test:ui          # Web UI模式
npm run test:report      # 查看测试报告
```

### 运行负载测试
```bash
cd backend/tests/load

# Web UI模式
locust -f locustfile.py --host=http://localhost:8000

# 无头模式（100用户，60秒）
locust -f locustfile.py --host=http://localhost:8000 \
  --headless --users 100 --spawn-rate 10 --run-time 60s
```

### 运行单元测试
```bash
cd backend
pytest tests/ -v --cov=app --cov-report=html
```

---

## 📊 项目统计 🆕

### 代码量
- **后端**: ~18,000行Python代码（含监控、日志、测试）
- **前端**: ~8,000行TypeScript/React代码
- **测试**: ~4,500行测试代码
- **文档**: ~8,000行Markdown文档（14个文档文件）
- **总计**: ~38,500行代码

### 测试覆盖
- **单元测试**: 205+个测试用例，覆盖率>80%
- **E2E测试**: 4个完整用户流程测试
- **负载测试**: 5个端点性能基准，支持100并发用户
- **集成测试**: 数据源fallback、缓存验证、告警测试

### 性能指标
- **Quick Chat响应**: < 3秒（P95）
- **Deep Research响应**: < 30秒（优化后）
- **Hotspots响应**: < 1秒（P95）
- **Autocomplete响应**: < 500ms（P95）
- **缓存命中提升**: 88-94%响应时间改善

### 质量指标
- **监控覆盖**: 16个关键指标实时追踪
- **告警响应**: 错误率>5%或P95延迟>3s自动触发
- **日志质量**: JSON结构化、request_id追踪、敏感数据脱敏
- **文档完整度**: 14个专业文档（API、运维、开发、测试）

---

## 🤝 贡献指南

我们欢迎各种形式的贡献！

### 如何贡献

1. **Fork本仓库**
2. **创建Feature分支** (`git checkout -b feature/AmazingFeature`)
3. **提交更改** (`git commit -m 'Add some AmazingFeature'`)
4. **推送到分支** (`git push origin feature/AmazingFeature`)
5. **创建Pull Request**

### 代码规范

#### Python（后端）
```bash
# 格式化代码
black app/ tests/

# 排序import
isort app/ tests/

# 静态检查
pylint app/
```

#### TypeScript（前端）
```bash
# 格式化代码
npm run format

# 代码检查
npm run lint
```

### 提交规范

遵循[Conventional Commits](https://www.conventionalcommits.org/)规范：

```
feat: 添加新功能
fix: 修复bug
docs: 文档更新
style: 代码格式调整
refactor: 代码重构
test: 测试相关
chore: 构建/工具配置
```

---

## 📝 许可证

本项目采用MIT许可证。详见 [LICENSE](LICENSE) 文件。

---

## 🙏 致谢

- [OpenRouter](https://openrouter.ai/) - 提供免费AI模型访问
- [CoinGecko](https://www.coingecko.com/) - 加密货币市场数据
- [FastAPI](https://fastapi.tiangolo.com/) - 现代Python Web框架
- [React](https://reactjs.org/) - UI构建库
- [Render](https://render.com/) - 后端部署平台
- [Vercel](https://vercel.com/) - 前端部署平台

---

## 📧 联系方式

- **项目主页**: https://github.com/marovole/Web3search
- **API文档**: https://web3search-api.onrender.com/docs
- **前端应用**: https://frontend-fnkjroe8s-marovole-gmailcoms-projects.vercel.app
- **问题反馈**: https://github.com/marovole/Web3search/issues

---

<div align="center">

Made with ❤️ by the Web3 Search Team

⭐ 如果这个项目对你有帮助，请给一个Star！⭐

**⚠️ 免责声明**: 本项目提供的分析报告仅供参考，不构成投资建议。加密货币投资存在风险，请谨慎决策。

</div>
