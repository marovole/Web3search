# Workers API - AGENTS.md

Cloudflare Workers API built with Hono. Handles all backend logic, AI orchestration, and cron jobs.

## Entry Point

`src/index.ts` - Hono app with routes + scheduled event handler for cron jobs.

## Route Map

| Route | File | Purpose |
|-------|------|---------|
| `/api/v1/health` | `routes/health.ts` | Health check |
| `/api/v1/search` | `routes/search.ts` | Autocomplete via Convex HTTP |
| `/api/v1/chat` | `routes/chat-v2.ts` | Quick chat (v1 redirects to v2) |
| `/api/v1/deep-research` | `routes/deep-research.ts` | Async research tasks |
| `/api/v1/multi-agent` | `routes/multi-agent.ts` | Coordinated multi-agent research |
| `/api/v1/agents` | `routes/agents.ts` | Background AI task management |
| `/api/v1/billing` | `routes/billing.ts` | Stripe integration |
| `/api/v1/notifications` | `routes/notifications.ts` | User notifications |
| `/api/v1/push` | `routes/push.ts` | Web push subscriptions |

## Multi-Agent System

Located in `src/lib/multi-agent/`:

```
multi-agent/
├── coordinator/
│   ├── index.ts          # Main coordinator orchestrates agents
│   ├── task-router.ts    # Routes tasks to appropriate agents
│   ├── result-aggregator.ts  # Combines agent outputs
│   └── context-manager.ts    # Shared context between agents
├── agents/
│   ├── researcher.ts     # Web search and data gathering
│   ├── analyzer.ts       # Data analysis and insights
│   ├── reporter.ts       # Report generation
│   ├── risk-agent.ts     # Risk assessment
│   └── news-agent.ts     # News aggregation
├── types.ts              # Shared types
└── errors.ts             # Error definitions
```

**Pattern**: Coordinator dispatches to specialized agents → aggregates results → returns unified response.

## Deep Research Pipeline

Located in `src/services/deep-research/`:

| Step | File | Purpose |
|------|------|---------|
| 1 | `plan.ts` | Generate research plan |
| 2 | `sources.ts` | Gather sources via search providers |
| 3 | `pipeline.service.ts` | Execute 5-step pipeline |
| 4 | `streaming.service.ts` | SSE streaming with Glass Box |
| 5 | `formatter.service.ts` | Format final output |

## Cron Jobs

Defined in `src/index.ts` scheduled handler:

| Schedule | Tasks |
|----------|-------|
| `*/5 * * * *` | Price alerts, health checks |
| `0 * * * *` | Risk monitor, news brief, KV cleanup |
| `*/10 * * * *` | Supabase keep-alive |
| `0 0 * * *` | Daily quota reset |
| `0 0 1 * *` | Monthly quota reset |
| `0 9 * * 1` | Portfolio health (Monday 9am) |
| `0 10 * * 3` | Opportunity finder (Wednesday 10am) |

## Convex Integration

**CRITICAL**: Use `convex-http.ts` for Convex calls, NOT direct SDK.

```typescript
// src/lib/convex-http.ts
// Calls Convex via HTTP endpoints at .convex.site domain

import { convexHttpClient } from './convex-http'

// CREATE research task
await convexHttpClient.createDeepResearch(env.CONVEX_URL, { query, externalId })

// GET by external ID
await convexHttpClient.getDeepResearchByExternalId(env.CONVEX_URL, externalId)

// SEARCH projects
await convexHttpClient.searchProjects(env.CONVEX_URL, query, limit)
```

**Why HTTP?**: Workers don't have `CONVEX_DEPLOY_KEY` for mutations. HTTP endpoints bypass this.

## Key Libraries

| Library | Usage |
|---------|-------|
| `hono` | Web framework |
| `@sentry/toucan` | Error tracking (Workers-compatible) |
| `openrouter` | AI model gateway |
| `zod` | Request validation |

## Adding New Routes

1. Create `src/routes/my-route.ts`:
```typescript
import { Hono } from 'hono'
import type { Env } from '../types/env'

const app = new Hono<{ Bindings: Env }>()

app.get('/', async (c) => {
  return c.json({ data: 'ok' })
})

export default app
```

2. Register in `src/index.ts`:
```typescript
import myRoutes from './routes/my-route'
app.route('/api/v1/my-route', myRoutes)
```

## Adding New Agent Task Types

1. Add type to `routes/agents.ts` `validTypes` array
2. Add to `lib/intent-parser.ts` if created via chat
3. Create processor in `lib/*-processor.ts`
4. Register in `jobs/scheduled.ts` `runAgentTasks`

## Environment Variables

```typescript
interface Env {
  CONVEX_URL: string        // https://xxx.convex.cloud
  JWT_SECRET: string
  OPENROUTER_API_KEY: string
  BRAVE_SEARCH_API_KEY: string
  TAVILY_API_KEY?: string   // Fallback search
  SERPER_API_KEY?: string   // Fallback search
  CACHE: KVNamespace        // Cloudflare KV binding
}
```

## Testing

```bash
npm run test                    # Run all tests
npm run test -- path/to/file    # Single file
npm run test:watch              # Watch mode
```

Vitest config: `vitest.config.ts`

## Common Patterns

### Error Response
```typescript
return c.json({
  error: {
    code: 'ERROR_CODE',
    message: 'Human readable message',
    status: 400,
  },
}, 400)
```

### Streaming SSE
```typescript
import { streamSSE } from '@/lib/streaming'

return streamSSE(c, async (stream) => {
  await stream.send({ event: 'progress', data: { step: 1 } })
  await stream.send({ event: 'complete', data: result })
})
```

### Auth Middleware
```typescript
import { authMiddleware } from '@/middlewares/auth'

app.use('*', authMiddleware)
// c.get('userId') available in handlers
```
