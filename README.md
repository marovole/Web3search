# Web3 Search - 加密货币AI搜索引擎

> 专注于加密货币领域的AI驱动研究平台，对标 asksurf.ai

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![React 18](https://img.shields.io/badge/react-18-blue.svg)](https://reactjs.org/)

## 项目简介

Web3 Search 是一个开源、免费、专业级的加密货币AI搜索引擎，为投资者提供机构级分析报告。

### 核心特性

- 🤖 **双模式交互**
  - **Quick Chat**: 快速问答，3秒响应
  - **Deep Research**: 深度研究报告，15-30秒生成3000-5000字机构级报告

- 📊 **六维深度分析**
  - TL;DR（核心判断 + 置信度）
  - 时间窗分析（24h/7d/30d）
  - 社媒情绪分析
  - 技术面分析
  - 基本面分析
  - 竞品对比

- 💰 **零AI成本**
  - 使用 OpenRouter 免费模型（qwen3-235b, deepseek-r1等）
  - 月部署成本 < $10

- 🌍 **多源数据采集**
  - CoinGecko / CoinMarketCap（价格数据）
  - Etherscan / BSCScan（链上数据）
  - Twitter / Reddit（社交媒体）
  - CryptoPanic（新闻资讯）

## 技术栈

### 后端
- **Python 3.11** + **FastAPI**
- **PostgreSQL 15** + **Redis 7** + **ChromaDB**
- **Celery** (后台任务)
- **OpenRouter API** (AI分析)

### 前端
- **React 18** + **TypeScript**
- **Vite** + **TailwindCSS**
- **Recharts** (数据可视化)

### 部署

- **Backend**: Railway (PostgreSQL + Redis + FastAPI)
- **Frontend**: Vercel (React SSR)
- **CI/CD**: GitHub Actions

## 快速开始

### 前置要求

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- OpenRouter API Key (免费注册: https://openrouter.ai)

### 本地开发

#### 1. 克隆项目

```bash
git clone https://github.com/your-username/Web3search.git
cd Web3search
```

#### 2. 配置环境变量

```bash
# 复制环境变量模板
cp backend/.env.example backend/.env

# 编辑.env文件，至少需要配置:
# - OPENROUTER_API_KEY (必需)
# - DATABASE_URL (默认使用Docker PostgreSQL)
# - REDIS_URL (默认使用Docker Redis)
```

#### 3. 启动开发环境

```bash
# 使用一键启动脚本
bash scripts/dev.sh

# 或手动启动
docker-compose up -d postgres redis
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

#### 4. 访问服务

- API文档: http://localhost:8000/docs
- API健康检查: http://localhost:8000/health
- ReDoc文档: http://localhost:8000/redoc

### 运行测试

```bash
# 运行所有测试
bash scripts/test.sh

# 或手动运行
cd backend
pytest tests/ -v

# 生成覆盖率报告
pytest tests/ --cov=app --cov-report=html
```

## API使用示例

### Quick Chat（快速问答）

```bash
curl -X POST http://localhost:8000/api/v1/quick-chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "BTC现在的价格是多少？",
    "stream": false
  }'
```

**响应:**
```json
{
  "content": "比特币（BTC）当前价格为 $67,234.56，24小时上涨 2.3%...",
  "symbol": "BTC",
  "query_type": "crypto_lookup",
  "response_time": 2.8,
  "model": "qwen/qwen3-30b-a3b:free"
}
```

### Deep Research（深度研究）

```bash
curl -X POST http://localhost:8000/api/v1/deep-research \
  -H "Content-Type: application/json" \
  -d '{
    "query": "请帮我深度分析以太坊的当前状况",
    "symbol": "ETH"
  }'
```

**响应:**
```json
{
  "report_id": 1,
  "symbol": "ETH",
  "tldr": "以太坊是第二大加密货币...",
  "sections": {
    "overview": "## 项目概览\n...",
    "technical_analysis": "## 技术分析\n...",
    "market_analysis": "## 市场分析\n...",
    "community_analysis": "## 社区分析\n...",
    "risk_assessment": "## 风险评估\n...",
    "competitor_analysis": "## 竞品分析\n..."
  },
  "markdown_content": "# ETH 深度研究报告\n...",
  "generation_time": 25.6,
  "quality_score": 85
}
```

### 获取报告列表

```bash
curl http://localhost:8000/api/v1/reports?page=1&page_size=10&symbol=BTC
```

## 生产部署

### Railway部署（推荐）

1. **准备Railway账号**
   - 注册: https://railway.app
   - 连接GitHub仓库

2. **创建新项目**
   ```bash
   # 安装Railway CLI
   npm install -g @railway/cli

   # 登录
   railway login

   # 初始化项目
   railway init
   ```

3. **添加服务**
   - PostgreSQL 15
   - Redis 7
   - Python Backend (本项目)

4. **配置环境变量**
   ```bash
   railway variables set OPENROUTER_API_KEY=your_key_here
   railway variables set ENVIRONMENT=production
   railway variables set DEBUG=false
   ```

5. **部署**
   ```bash
   railway up
   ```

### Docker部署

```bash
# 构建镜像
docker build -t web3search-backend ./backend

# 运行容器
docker run -d \
  -p 8000:8000 \
  -e DATABASE_URL=your_database_url \
  -e REDIS_URL=your_redis_url \
  -e OPENROUTER_API_KEY=your_api_key \
  web3search-backend
```

## 项目结构

```
Web3search/
├── backend/                 # Python后端
│   ├── app/
│   │   ├── api/            # API路由
│   │   │   ├── v1/
│   │   │   │   ├── chat.py          # Quick Chat & Deep Research
│   │   │   │   └── reports.py       # 报告查询
│   │   │   └── middleware/
│   │   │       └── rate_limit.py    # 速率限制
│   │   ├── core/           # 核心配置
│   │   │   ├── config.py            # 环境变量配置
│   │   │   ├── database.py          # 数据库连接
│   │   │   └── redis_client.py      # Redis客户端
│   │   ├── models/         # 数据库模型
│   │   │   ├── project.py           # 项目&快照
│   │   │   ├── report.py            # 研究报告
│   │   │   └── conversation.py      # 对话历史
│   │   ├── services/       # 业务逻辑
│   │   │   ├── collectors/          # 数据采集器
│   │   │   │   ├── coingecko.py
│   │   │   │   ├── etherscan.py
│   │   │   │   ├── twitter.py
│   │   │   │   ├── reddit.py
│   │   │   │   └── cryptopanic.py
│   │   │   ├── research_engine/     # 研究引擎
│   │   │   │   ├── quick_chat.py
│   │   │   │   └── deep_research.py
│   │   │   ├── report/              # 报告生成
│   │   │   ├── llm.py              # LLM客户端
│   │   │   ├── data_aggregator.py  # 数据聚合
│   │   │   └── prompt_manager.py   # 提示词管理
│   │   ├── schemas/        # API数据模型
│   │   ├── tasks/          # Celery后台任务
│   │   └── main.py         # FastAPI应用入口
│   ├── tests/              # 测试文件
│   ├── requirements.txt    # Python依赖
│   └── .env.example        # 环境变量示例
├── frontend/               # React前端（待开发）
├── prompts/                # AI提示词模板
│   ├── system_prompts.yaml
│   └── deep_research.yaml
├── scripts/                # 开发脚本
│   ├── dev.sh             # 开发环境启动
│   ├── test.sh            # 测试运行
│   └── start.sh           # 生产启动
├── docker-compose.yml      # Docker配置
├── Dockerfile             # Docker镜像
├── railway.json           # Railway配置
└── README.md              # 项目文档
```

## 开发指南

### 添加新的数据源

1. 在`app/services/collectors/`创建新的采集器
2. 继承基类或实现标准接口
3. 在`data_aggregator.py`中集成
4. 更新提示词模板

### 添加新的分析维度

1. 在`prompts/deep_research.yaml`添加新模板
2. 在`deep_research.py`添加生成逻辑
3. 更新`report_generator.py`格式化
4. 更新API响应schema

### 自定义LLM模型

编辑`app/services/llm.py`的`ModelConfig`类：

```python
class ModelConfig:
    QUICK_CHAT = "your/model:free"
    DEEP_RESEARCH_SUMMARY = "your/model:free"
    DEEP_RESEARCH_ANALYSIS = "your/model:free"
```

## 性能指标

- **Quick Chat**: < 3秒响应
- **Deep Research**: 15-30秒
- **并发支持**: 100+ QPS (4 workers)
- **月成本**: < $10 (PostgreSQL + Redis)
- **AI成本**: $0 (免费模型)

## 速率限制

- Quick Chat: 10次/分钟
- Deep Research: 3次/小时
- Reports查询: 30次/分钟

超限返回429错误，响应头包含重试信息。

## 故障排查

### 数据库连接失败
```bash
# 检查PostgreSQL是否运行
docker ps | grep postgres

# 查看日志
docker logs web3search-postgres
```

### Redis连接失败
```bash
# 检查Redis是否运行
docker ps | grep redis

# 测试连接
redis-cli ping
```

### API调用失败
```bash
# 检查API密钥
echo $OPENROUTER_API_KEY

# 查看应用日志
docker logs web3search-backend
```

## 贡献指南

欢迎贡献！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 开源协议

本项目采用 MIT 协议 - 查看 [LICENSE](LICENSE) 文件了解详情

## 联系方式

- 项目链接: https://github.com/your-username/Web3search
- 问题反馈: https://github.com/your-username/Web3search/issues

## 致谢

- [OpenRouter](https://openrouter.ai) - 免费LLM API
- [CoinGecko](https://www.coingecko.com) - 加密货币数据
- [FastAPI](https://fastapi.tiangolo.com) - 现代Python Web框架
- [asksurf.ai](https://asksurf.ai) - 产品灵感来源

---

⭐ 如果这个项目对您有帮助，请给我们一个Star！
- **Vercel** (前端，全球CDN)
- **Railway** (后端，$5-10/月)

## 快速开始

### 前置要求
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose (可选)

### 本地开发

#### 1. 克隆仓库
```bash
git clone https://github.com/yourusername/web3search.git
cd web3search
```

#### 2. 后端设置

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp ../.env.example .env
# 编辑 .env 文件，填入你的 API Keys

# 运行开发服务器
uvicorn app.main:app --reload --port 8000
```

访问 http://localhost:8000/docs 查看 API 文档

#### 3. 前端设置

```bash
cd frontend

# 安装依赖
npm install

# 配置环境变量
cp .env.example .env.local
# 编辑 .env.local，设置 VITE_API_URL=http://localhost:8000

# 运行开发服务器
npm run dev
```

访问 http://localhost:3000

#### 4. 使用 Docker Compose（推荐）

```bash
# 启动所有服务（后端、PostgreSQL、Redis）
docker-compose up

# 后台运行
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## 项目结构

```
web3search/
├── backend/                 # Python 后端
│   ├── app/
│   │   ├── api/v1/         # API 路由
│   │   ├── core/           # 核心配置（数据库、Redis、LLM）
│   │   ├── models/         # 数据库模型
│   │   ├── services/       # 业务逻辑
│   │   │   ├── collectors/ # 数据采集
│   │   │   ├── research_engine/ # AI 分析引擎
│   │   │   └── report/     # 报告生成
│   │   └── schemas/        # Pydantic 模型
│   ├── tasks/              # Celery 定时任务
│   ├── tests/              # 单元测试
│   └── requirements.txt
├── frontend/                # React 前端
│   ├── src/
│   │   ├── components/     # React 组件
│   │   ├── services/       # API 调用
│   │   └── pages/          # 页面
│   └── package.json
├── prompts/                 # AI Prompt 模板
├── docs/                    # 项目文档
├── openspec/                # OpenSpec 规范
├── docker-compose.yml
└── README.md
```

## API 文档

启动后端后，访问以下地址查看交互式 API 文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 主要端点

- `POST /api/v1/chat` - Quick Chat 快速问答
- `POST /api/v1/chat/stream` - SSE 流式响应
- `POST /api/v1/research` - Deep Research 深度研究
- `GET /api/v1/trends/hotspots` - 热点项目排行
- `GET /api/v1/reports/{share_token}` - 获取分享的报告
- `GET /health` - 健康检查

## 环境变量

创建 `.env` 文件（参考 `.env.example`）：

```bash
# OpenRouter API
OPENROUTER_API_KEY=sk-or-xxx

# 数据库
DATABASE_URL=postgresql://user:pass@localhost:5432/web3search
REDIS_URL=redis://localhost:6379

# 数据源 API Keys
COINGECKO_API_KEY=xxx
ETHERSCAN_API_KEY=xxx
TWITTER_BEARER_TOKEN=xxx
REDDIT_CLIENT_ID=xxx
REDDIT_CLIENT_SECRET=xxx

# 应用配置
ENVIRONMENT=development
DEBUG=true
```

## 部署

### Vercel 前端部署

```bash
# 安装 Vercel CLI
npm install -g vercel

# 部署
cd frontend
vercel

# 生产部署
vercel --prod
```

### Railway 后端部署

1. 访问 [Railway.app](https://railway.app)
2. 连接 GitHub 仓库
3. 添加 PostgreSQL 和 Redis 插件
4. 配置环境变量
5. 自动部署

详细部署文档：[docs/deployment.md](docs/deployment.md)

## 测试

```bash
# 后端测试
cd backend
pytest

# 前端测试
cd frontend
npm test

# 端到端测试
npx playwright test
```

## 开发规范

遵循 OpenSpec 规范进行开发，详见：
- [OpenSpec Change Proposal](openspec/changes/add-crypto-ai-search-platform/)
- [项目规范](openspec/project.md)

### 提交规范

```
<type>(<scope>): <subject>

类型: feat/fix/docs/style/refactor/test/chore
示例: feat(data-collector): add CoinGecko API integration
```

## 贡献指南

欢迎贡献！请先阅读 [CONTRIBUTING.md](CONTRIBUTING.md)

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交变更 (`git commit -m 'feat: Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 路线图

- [x] Phase 0: OpenSpec 规范制定
- [ ] Phase 1: 项目基础设施
- [ ] Phase 2: 数据采集层
- [ ] Phase 3: Quick Chat 模式
- [ ] Phase 4: Deep Research 引擎
- [ ] Phase 5: Prompt 工程优化
- [ ] Phase 6: 报告生成系统
- [ ] Phase 7: 前端开发
- [ ] Phase 8: 特色功能
- [ ] Phase 9: 部署与 CI/CD
- [ ] Phase 10: 测试与优化

完整路线图：[openspec/changes/add-crypto-ai-search-platform/tasks.md](openspec/changes/add-crypto-ai-search-platform/tasks.md)

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 致谢

- [asksurf.ai](https://asksurf.ai) - 产品灵感来源
- [OpenRouter](https://openrouter.ai) - 提供免费 LLM 模型
- [CoinGecko](https://www.coingecko.com) - 加密货币数据
- [FastAPI](https://fastapi.tiangolo.com) - 后端框架

## 联系方式

- 项目主页: https://github.com/yourusername/web3search
- 问题反馈: https://github.com/yourusername/web3search/issues

---

**⚠️ 免责声明**: 本项目提供的分析报告仅供参考，不构成投资建议。加密货币投资存在风险，请谨慎决策。
