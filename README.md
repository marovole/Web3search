# Web3search

**AI-Powered Web3 Research Platform for Decentralized Data Retrieval and Analysis**

---

## 🏗️ Architecture

```
┌─────────────────────┐     ┌──────────────────────┐     ┌─────────────┐
│      Frontend       │────▶│    Workers API       │────▶│  Supabase   │
│  Cloudflare Pages   │     │ Cloudflare Workers   │     │ PostgreSQL  │
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
| Database | Supabase | PostgreSQL + Realtime | ✅ Active |

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
- **Framework**: React 18 + TypeScript
- **Build**: Vite 5
- **Styling**: TailwindCSS
- **UI Components**: Radix UI + custom Research components
- **Deployment**: Cloudflare Pages (auto-deploy on push)

### Backend
- **Runtime**: Cloudflare Workers
- **Framework**: Hono (lightweight web framework)
- **Language**: TypeScript
- **Caching**: Cloudflare KV

### Database
- **Service**: Supabase
- **Engine**: PostgreSQL 15
- **Features**: Row Level Security, Realtime subscriptions

### External Services
- **AI Gateway**: OpenRouter (multi-model routing)
- **Search**: Brave Search (primary), Tavily, Serper (failover)
- **Price Data**: CoinGecko API
- **Analytics**: Google Analytics 4

---

## 🔧 Environment Variables

### Cloudflare Workers (Secrets)

```bash
# Set via: wrangler secret put <NAME>
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...  # Optional
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
├── supabase/                 # Database migrations
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

*Last updated: 2025-12-08*
