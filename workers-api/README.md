# Web3search API - Cloudflare Workers

Web3search 的后端 API 服务，基于 Cloudflare Workers + Convex 架构。

## 🏗️ 技术栈

- **Runtime**: Cloudflare Workers (Edge Computing)
- **Framework**: Hono (轻量级 Web 框架)
- **Database**: Convex (Serverless Database)
- **Cache**: Cloudflare KV
- **Language**: TypeScript
- **AI**: OpenRouter API

## 📦 安装

```bash
# 安装依赖
npm install

# 或使用 pnpm/yarn
pnpm install
```

## 🚀 开发

### 1. 配置环境变量

复制示例文件并填写实际值：

```bash
cp .dev.vars.example .dev.vars
```

编辑 `.dev.vars` 并填入：
- Convex URL 和 Deploy Key
- OpenRouter API Key
- JWT Secret (用于认证)

### 2. 启动本地开发服务器

```bash
npm run dev
```

服务将在 `http://localhost:8787` 启动。

### 3. 测试 API

```bash
# 健康检查
curl http://localhost:8787/api/v1/health

# 根路由
curl http://localhost:8787/
```

## 📝 可用脚本

```bash
npm run dev              # 启动开发服务器
npm run deploy           # 部署到 Cloudflare Workers
npm run deploy:production # 部署到生产环境
npm run tail             # 查看实时日志
npm run test             # 运行测试
npm run type-check       # TypeScript 类型检查
```

## 🌐 API 端点

### 健康检查
- `GET /api/v1/health` - 服务健康状态
  - 返回数据库、缓存连接状态和响应时间

### 搜索（✅ Week 1 Day 5 已完成）
- `GET /api/v1/search/autocomplete` - 搜索自动完成
  - 查询参数：
    - `q` (必需): 搜索关键词
    - `limit` (可选): 最大结果数量，默认 10，最大 50
  - 示例：`/api/v1/search/autocomplete?q=bit&limit=5`
  - 搜索范围：币种代码 (symbol) 和名称 (name)

### 聊天（Week 2 实现）
- `POST /api/v1/chat/quick-chat` - 快速聊天

### 报告（Week 3 实现）
- `POST /api/v1/reports/generate` - 生成报告
- `GET /api/v1/reports/:id` - 查询报告状态

### AI Agent System

#### Agent Tasks
- `GET /api/v1/agents/tasks` - List user's agent tasks
- `POST /api/v1/agents/tasks` - Create new agent task
- `GET /api/v1/agents/tasks/:id` - Get task details
- `PATCH /api/v1/agents/tasks/:id` - Update task
- `DELETE /api/v1/agents/tasks/:id` - Delete task
- `POST /api/v1/agents/tasks/:id/pause` - Pause task
- `POST /api/v1/agents/tasks/:id/resume` - Resume task
- `GET /api/v1/agents/tasks/:id/runs` - Get task execution history

#### Conversation (AI Chat)
- `POST /api/v1/agents/conversation` - Send message, parse intent
- `GET /api/v1/agents/conversation/stream` - SSE streaming responses
- `GET /api/v1/agents/conversation/history` - Get chat history

#### Activity Log
- `GET /api/v1/agents/activity/dashboard` - Dashboard stats
- `GET /api/v1/agents/activity/logs` - Activity logs with filtering
- `GET /api/v1/agents/activity/stream` - SSE real-time updates

### Notifications
- `GET /api/v1/notifications` - List notifications
- `PATCH /api/v1/notifications/:id/read` - Mark as read
- `POST /api/v1/notifications/read-all` - Mark all read
- `DELETE /api/v1/notifications/:id` - Delete notification

### Push Notifications
- `POST /api/v1/push/subscribe` - Subscribe to push
- `DELETE /api/v1/push/unsubscribe` - Unsubscribe
- `POST /api/v1/push/test` - Send test notification

### Watchlist
- `GET /api/v1/watchlist` - List watchlist items
- `POST /api/v1/watchlist` - Add token to watchlist
- `PATCH /api/v1/watchlist/:id` - Update watchlist item
- `DELETE /api/v1/watchlist/:id` - Remove from watchlist

### Authentication
- `GET /api/v1/auth/me` - Get current user
- `GET /api/v1/users/profile` - Get user profile
- `PATCH /api/v1/users/profile` - Update profile
- `GET /api/v1/users/quota` - Get quota usage

### Billing
- `POST /api/v1/billing/checkout` - Create checkout session
- `POST /api/v1/billing/portal` - Create billing portal session
- `POST /api/v1/billing/webhook` - Stripe webhook handler

## 🔐 部署到 Cloudflare

### 1. 登录 Cloudflare

```bash
npx wrangler login
```

### 2. 创建 KV 命名空间

```bash
npx wrangler kv:namespace create CACHE
npx wrangler kv:namespace create CACHE --preview
```

复制返回的 ID 并更新 `wrangler.toml`。

### 3. 设置 Secrets

```bash
npx wrangler secret put CONVEX_URL
npx wrangler secret put CONVEX_DEPLOY_KEY
npx wrangler secret put OPENROUTER_API_KEY
npx wrangler secret put JWT_SECRET
```

### 4. 部署

```bash
npm run deploy
```

## 📊 监控

查看实时日志：

```bash
npm run tail
```

或访问 Cloudflare Dashboard:
https://dash.cloudflare.com/ → Workers & Pages → web3search-api

## 🏗️ 项目结构

```
workers-api/
├── src/
│   ├── index.ts          # 入口文件
│   ├── routes/           # API 路由
│   │   ├── health.ts     # 健康检查
│   │   ├── search.ts     # 搜索 (Week 1 Day 5)
│   │   ├── chat.ts       # 聊天 (Week 2)
│   │   └── reports.ts    # 报告 (Week 3)
│   ├── middlewares/      # 中间件
│   │   ├── logger.ts     # 日志
│   │   ├── cors.ts       # CORS
│   │   └── auth.ts       # 认证 (Week 3)
│   ├── services/         # 业务逻辑
│   ├── utils/            # 工具函数
│   ├── types/            # TypeScript 类型
│   └── lib/              # 第三方库配置
│       └── supabase.ts   # Convex HTTP 适配器 (Supabase API 兼容层)
├── convex/               # Convex 数据库函数
│   ├── schema.ts         # 数据库 schema
│   ├── users.ts          # 用户相关函数
│   ├── conversations.ts  # 对话相关函数
│   └── ...
├── wrangler.toml         # Cloudflare 配置
├── package.json
└── tsconfig.json
```

## 🧪 测试

```bash
# 运行测试
npm run test

# 监听模式
npm run test:watch
```

## 📚 相关文档

- [Cloudflare Workers Docs](https://developers.cloudflare.com/workers/)
- [Hono Framework](https://hono.dev/)
- [Convex Docs](https://docs.convex.dev/)
- [OpenRouter API](https://openrouter.ai/docs)

## ✅ 数据库迁移进度

- [x] Supabase to Convex 迁移完成
- [x] Convex Schema 定义
- [x] Convex HTTP 适配器 (Supabase API 兼容层)
- [x] TypeScript 类型检查通过
