# Web3search

**AI-Powered Web3 Research Platform for Decentralized Data Retrieval and Analysis**

> 🌐 **在线体验**: [https://web3search.pages.dev](https://web3search.pages.dev)

---

## 📖 用户指南

### 这是什么？

Web3search 是一款专为加密货币投资者和研究人员打造的 **AI 智能研究助手**。它可以帮助您：

- 快速获取任何加密项目的信息
- 自动识别潜在投资风险
- 生成专业的研究报告

### 两种使用模式

| 模式 | 适用场景 | 响应时间 |
|------|----------|----------|
| **Quick Chat** | 日常问答、查价格、了解概念 | ~3 秒 |
| **Deep Research** | 投资前尽调、全面项目分析 | 30秒-2分钟 |

### 核心功能一览

#### 🔍 深度研究工具

| 功能 | 说明 |
|------|------|
| **Glass Box 透明面板** | 实时查看 AI 的研究过程和数据来源 |
| **ScamMeter 诈骗评估** | 0-100 分风险评分，一眼识别问题项目 |
| **Red Flag 风险仪表盘** | 自动识别并展示项目的潜在风险点 |
| **持币分布分析** | 可视化展示巨鲸持仓和集中度风险 |
| **解锁日历** | 追踪代币 vesting 解锁计划 |
| **对抗性问答** | 从多角度（看多/看空/中立）分析项目 |

#### 💬 智能对话

- 实时加密货币价格查询
- 多轮对话上下文保持
- 流式响应，实时输出

#### 📁 个人管理

- **监控列表** - 收藏关注的项目，一键生成报告
- **历史记录** - 自动保存研究历史，方便回顾
- **报告分享** - 生成分享链接，与他人共享研究成果

### 快速开始

1. 访问 [https://web3search.pages.dev](https://web3search.pages.dev)
2. 选择 **Quick** 或 **Deep Research** 模式
3. 输入您的问题或项目名称
4. 查看 AI 生成的分析结果

> 📚 **详细用户指南**: [docs/USER_GUIDE.md](docs/USER_GUIDE.md)

---

## 🏗️ Architecture

```
┌─────────────────────┐     ┌──────────────────────┐     ┌─────────────┐
│      Frontend       │────▶│    Workers API       │────▶│   Convex    │
│  Cloudflare Pages   │     │ Cloudflare Workers   │     │  Database   │
│  React + Vite       │     │    Hono + TS         │     └─────────────┘
└─────────────────────┘     └──────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
          ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
          │ OpenRouter  │   │   Brave     │   │  CoinGecko  │
          │ AI Gateway  │   │   Search    │   │  Price API  │
          └─────────────┘   └─────────────┘   └─────────────┘
```

---

## 🚀 Deployment Status

| Component | Platform | Production URL | Status |
|-----------|----------|----------------|--------|
| Frontend | Cloudflare Pages | https://web3search.pages.dev | ✅ Live |
| API | Cloudflare Workers | https://web3search-api.marovole.workers.dev | ✅ Live |
| Custom Domain | Cloudflare | api.lulaai.xyz | ✅ Active |
| Database | Convex | Real-time Database | ✅ Active |

### CI/CD Pipeline

| Workflow | Trigger | Description |
|----------|---------|-------------|
| CI/CD Pipeline | push to main/develop | Lint, type-check, tests, build |
| Multi-Environment Deployment | push to main/develop | Auto-deploy to production/staging |

> GitHub Actions 已恢复自动部署。push 到 main 分支会自动触发 CI/CD 和部署流程。

---

## 🤖 AI Model Configuration

All AI requests are routed through [OpenRouter](https://openrouter.ai) for unified access.

| Use Case | Model | Provider | Cost ($/1M tokens) |
|----------|-------|----------|-------------------|
| **Quick Chat** | `deepseek/deepseek-v3.2-speciale` | DeepSeek | $0.50 / $2.18 |
| **Deep Research** | `alibaba/tongyi-deepresearch-30b-a3b` | Alibaba | $0.20 / $0.80 |
| **Fallback** | `openai/gpt-oss-120b:exacto` | OpenAI | $0.10 / $0.30 |

### Routing Strategy

| Scenario | Primary Model | Fallback |
|----------|--------------|----------|
| quick-chat | DeepSeek V3.2 | GPT-OSS-120B |
| deep-research | Tongyi DeepResearch | DeepSeek V3.2 |
| summarization | DeepSeek V3.2 | GPT-OSS-120B |
| code-assist | DeepSeek V3.2 | GPT-OSS-120B |

---

## ✨ Key Features

### Deep Research

- **Glass Box UX** - 透明化研究过程，实时展示 AI 思考链和数据来源
- **Red Flag Dashboard** - 风险预警仪表盘，自动识别项目潜在风险
- **Adversarial Q&A** - 对抗性问答，从多角度审视项目
- **ScamMeter** - 诈骗风险评估，基于多维度指标
- **HolderDistribution** - 持币分布分析，识别巨鲸和集中度风险
- **UnlockCalendar** - 代币解锁日历，追踪 vesting 计划
- **Tokenomics Audit** - 代币经济学深度审计模式
- **Dynamic Market Context** - 实时市场数据自动注入

### Quick Chat

- 实时加密货币价格数据集成
- 多轮对话上下文保持
- 流式响应输出

---

## 📡 API Endpoints

Base URL: `https://web3search-api.marovole.workers.dev/api/v1`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/chat/quick-chat` | POST | AI chat with real-time crypto price data |
| `/deep-research` | POST | Create async deep research task |
| `/deep-research/stream` | GET | SSE streaming with Glass Box feedback |
| `/deep-research/:id` | GET | Get research task status/results |
| `/reports` | POST | Generate structured reports |
| `/health` | GET | Health check |

---

## ⚙️ Tech Stack

### Frontend

| 分类 | 技术 | 版本 | 说明 |
|------|------|------|------|
| **框架** | React | 18.2 | 核心 UI 框架 |
| **语言** | TypeScript | 5.2+ | 类型安全 |
| **构建工具** | Vite | 5.0 | 快速开发服务器和构建 |
| **样式** | TailwindCSS | 3.3 | 原子化 CSS |
| **UI 组件库** | Radix UI | 最新 | 无障碍组件基础 |
| **动画** | Framer Motion | 12.x | 流畅动画效果 |
| **图标** | Lucide React | 0.548 | 图标库 |
| **路由** | React Router | 6.20 | SPA 路由 |
| **表单** | React Hook Form + Zod | 7.x / 4.x | 表单验证 |
| **HTTP 客户端** | Axios | 1.7 | API 请求 |
| **Markdown** | react-markdown | 9.0 | 渲染 Markdown 内容 |
| **日期处理** | date-fns | 4.1 | 日期格式化 |
| **虚拟列表** | @tanstack/react-virtual | 3.13 | 大列表性能优化 |
| **地图** | Leaflet + React Leaflet | 1.9 / 4.2 | 地图可视化 |
| **错误监控** | Sentry | 10.x | 前端错误追踪 |
| **部署** | Cloudflare Pages | - | 自动部署 |

### Backend

| 分类 | 技术 | 版本 | 说明 |
|------|------|------|------|
| **运行时** | Cloudflare Workers | - | 边缘计算 |
| **框架** | Hono | 4.10 | 轻量级 Web 框架 |
| **语言** | TypeScript | 5.7 | 类型安全 |
| **数据库客户端** | Convex | latest | Real-time 数据库访问 |
| **缓存** | Cloudflare KV | - | 边缘键值存储 |
| **错误追踪** | Toucan.js | 4.1 | Workers 环境 Sentry |
| **CLI** | Wrangler | 4.53 | 开发和部署工具 |
| **测试** | Vitest | 2.1 | 单元测试框架 |

### Database

| 服务 | 说明 |
|------|------|
| **Convex** | Real-time 数据库服务 |
| **功能** | 实时订阅、自动 API、TypeScript 原生支持 |

### 测试工具

| 工具 | 用途 |
|------|------|
| **Jest** | 前端单元测试 |
| **Testing Library** | React 组件测试 |
| **Playwright** | E2E 端到端测试 |
| **MSW** | API Mock |
| **Axe** | 无障碍测试 |
| **Vitest** | 后端单元测试 |

---

## 🔌 External APIs / 外部接口

### AI 服务

| 服务 | 用途 | 说明 |
|------|------|------|
| **[OpenRouter](https://openrouter.ai)** | AI 网关 | 统一访问多个 LLM 模型 |
| **Mistral Devstral** | 主要模型 | `mistralai/devstral-2512:free` (免费) |
| **ZhiPu GLM-4.5** | 备选模型 | `z-ai/glm-4.5-air:free` (免费) |

### 搜索服务

| 服务 | 优先级 | 说明 |
|------|--------|------|
| **[Brave Search](https://brave.com/search/api/)** | Primary | 主要搜索提供商 |
| **[Tavily](https://tavily.com)** | Fallback 1 | AI 优化搜索 |
| **[Serper](https://serper.dev)** | Fallback 2 | Google 搜索 API |

### 加密货币数据

| 服务 | 用途 | 免费额度 |
|------|------|----------|
| **[CoinGecko](https://www.coingecko.com/api)** | 价格/市值数据 | 50 次/分钟 |
| **[Etherscan](https://etherscan.io/apis)** | 以太坊链上数据 | 5 次/秒 |
| **[BSCScan](https://bscscan.com/apis)** | BSC 链上数据 | 5 次/秒 |

### 社交媒体数据

| 服务 | 用途 | 免费额度 |
|------|------|----------|
| **Twitter API v2** | 社交情绪分析 | 500K 条/月 |
| **Reddit API** | 社区讨论分析 | 60 次/分钟 |
| **[CryptoPanic](https://cryptopanic.com/developers/api/)** | 加密新闻聚合 | 25 次/日 |

### 监控与分析

| 服务 | 用途 |
|------|------|
| **Sentry** | 错误追踪和性能监控 |
| **Google Analytics 4** | 用户行为分析 |

---

## 🔧 Environment Variables

### Cloudflare Workers (Secrets)

```bash
# Set via: wrangler secret put <NAME>
CONVEX_URL=https://xxx.convex.cloud
CONVEX_DEPLOY_KEY=prod:xxx...
JWT_SECRET=your-jwt-secret
OPENROUTER_API_KEY=sk-or-...
BRAVE_SEARCH_API_KEY=BSA...
TAVILY_API_KEY=tvly-...           # Optional failover
SERPER_API_KEY=...                # Optional failover
```

### Frontend (Cloudflare Pages)

```bash
VITE_API_BASE_URL=https://web3search-api.marovole.workers.dev
VITE_ENABLE_ANALYTICS=true
VITE_GA_MEASUREMENT_ID=G-XXXXXXXX
```

---

## 📦 Local Development

### Prerequisites
- Node.js 18+
- pnpm or npm
- Wrangler CLI (`npm install -g wrangler`)

### Frontend

```bash
cd frontend
npm install
npm run dev          # Start dev server at localhost:5173
npm run build        # Production build
npm run preview      # Preview production build
```

### Workers API

```bash
cd workers-api
npm install
npm run dev          # Start local worker at localhost:8787
npm run deploy       # Deploy to Cloudflare
npm run test         # Run tests
```

---

## 📁 Project Structure

```
Web3search/
├── frontend/                 # React frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── Chat/        # Chat interface
│   │   │   └── Research/    # Deep Research components
│   │   │       ├── GlassBoxPanel.tsx
│   │   │       ├── RedFlagDashboard.tsx
│   │   │       ├── AdversarialQA.tsx
│   │   │       ├── ScamMeter.tsx
│   │   │       ├── HolderDistribution.tsx
│   │   │       └── UnlockCalendar.tsx
│   │   ├── hooks/           # Custom React hooks
│   │   ├── types/           # TypeScript definitions
│   │   │   └── deep-research.ts
│   │   └── lib/             # Utilities
│   └── vite.config.ts
├── workers-api/              # Main Cloudflare Workers API
│   ├── src/
│   │   ├── routes/          # API route handlers
│   │   │   └── deep-research.ts
│   │   ├── lib/
│   │   │   ├── model-routing.ts      # AI model configuration
│   │   │   ├── openrouter.ts         # OpenRouter client
│   │   │   ├── research-prompts.ts   # Research prompt templates
│   │   │   ├── context-builders/     # Market context injection
│   │   │   └── search-providers.ts
│   │   └── middlewares/     # Request middlewares
│   └── wrangler.toml        # Workers configuration
├── .github/
│   ├── workflows/           # Active CI/CD workflows
│   │   ├── ci.yml           # CI/CD Pipeline
│   │   └── deploy.yml       # Multi-Environment Deployment
│   └── workflows-disabled/  # Disabled workflows
├── convex/                   # Convex database schema and functions
└── docs/                     # Documentation
```

---

## 🧩 Compliance & Usage Notice

This repository, **Web3search**, is maintained by **Vole** as a **personal, non-commercial research project**.

- All experiments are conducted **solely for private research and educational purposes**
- No market data is redistributed or shared publicly
- Compliant with all external API providers' terms of service

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

Data usage complies strictly with external API providers' licensing terms.

---

## ✉️ Contact

**Author:** Vole  
**Email:** [vole@lucky365vip.cc](mailto:vole@lucky365vip.cc)  
**Status:** Active Development

---

*Last updated: 2026-01-06*
