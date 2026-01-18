# Convex - AGENTS.md

Real-time database layer using Convex. Handles all persistent data and exposes HTTP endpoints for Workers API.

## Deployments

| Environment | Deployment | Domain |
|-------------|------------|--------|
| Production | `charming-canary-707` | `.convex.cloud` / `.convex.site` |
| Development | `acoustic-spider-126` | `.convex.cloud` / `.convex.site` |

**CRITICAL**: HTTP endpoints use `.convex.site`, queries/mutations use `.convex.cloud`.

## Schema Overview

Defined in `schema.ts`. Key tables:

| Table | Purpose |
|-------|---------|
| `users` | Core user identity (Convex Auth) |
| `userProfiles` | Plan, preferences, Stripe ID |
| `userQuotas` | Usage limits and counters |
| `conversations` | Chat sessions |
| `messages` | Chat messages |
| `deepResearchTasks` | Async research jobs |
| `agentTasks` | Background AI tasks |
| `agentRuns` | Task execution history |
| `watchlist` | User's tracked tokens |
| `holdings` | Portfolio holdings |
| `projects` | Cryptocurrency project data |
| `notifications` | User notifications |
| `pushSubscriptions` | Web push subscriptions |

## HTTP Endpoints

Defined in `http.ts`. Called by Workers API via `.convex.site`:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/deep-research` | POST | Create research task |
| `/api/v1/deep-research/by-external-id` | GET | Get task by external ID |
| `/api/v1/deep-research/update` | PATCH | Update task progress |
| `/api/v1/projects/search` | GET | Search projects for autocomplete |
| `/api/health` | GET | Health check |

### Adding HTTP Endpoints

```typescript
// http.ts
http.route({
  path: "/api/v1/my-endpoint",
  method: "GET",
  handler: httpAction(async (ctx, request) => {
    const result = await ctx.runQuery(api.myFile.myQuery, { arg: "value" })
    return new Response(JSON.stringify(result), {
      headers: { "Content-Type": "application/json", ...corsHeaders }
    })
  }),
})
```

## Function Files

| File | Exports |
|------|---------|
| `deepResearch.ts` | `create`, `get`, `getByExternalId`, `start`, `complete`, `fail`, `updateProgress` |
| `projects.ts` | `search`, `getBySymbol`, `list` |
| `users.ts` | `getByToken`, `create`, `update` |
| `agentTasks.ts` | `create`, `list`, `get`, `update`, `delete`, `pause`, `resume` |
| `notifications.ts` | `create`, `list`, `markRead`, `markAllRead`, `delete` |
| `watchlist.ts` | `add`, `list`, `update`, `remove` |
| `holdings.ts` | `upsert`, `list`, `remove` |
| `seed.ts` | `seedProjects` - Seeds 20 major cryptocurrencies |

## Query/Mutation Patterns

### Query (read-only)
```typescript
import { query } from "./_generated/server"
import { v } from "convex/values"

export const myQuery = query({
  args: { id: v.string() },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("tableName")
      .withIndex("by_id", (q) => q.eq("id", args.id))
      .first()
  },
})
```

### Mutation (write)
```typescript
import { mutation } from "./_generated/server"
import { v } from "convex/values"

export const myMutation = mutation({
  args: { name: v.string() },
  handler: async (ctx, args) => {
    return await ctx.db.insert("tableName", {
      name: args.name,
      createdAt: Date.now(),
    })
  },
})
```

### HTTP Action
```typescript
import { httpAction } from "./_generated/server"
import { api } from "./_generated/api"

export const myHttpAction = httpAction(async (ctx, request) => {
  // Can call queries and mutations
  const result = await ctx.runQuery(api.myFile.myQuery, { id: "123" })
  await ctx.runMutation(api.myFile.myMutation, { name: "test" })
  
  return new Response(JSON.stringify(result))
})
```

## Key Indexes

| Table | Index | Fields |
|-------|-------|--------|
| `deepResearchTasks` | `by_external_id` | `externalId` |
| `deepResearchTasks` | `by_status` | `status` |
| `agentTasks` | `by_user_status` | `userId`, `status` |
| `users` | `by_token` | `tokenIdentifier` |
| `projects` | `by_symbol` | `symbol` |

## CLI Commands

```bash
npx convex dev           # Start dev mode (syncs on file changes)
npx convex deploy        # Deploy to production
npx convex logs          # View function logs
npx convex env set KEY=value  # Set environment variable
```

## Auth Integration

Uses `@convex-dev/auth`. Config in `auth.config.ts`, routes added via:

```typescript
// http.ts
import { auth } from "./auth"
auth.addHttpRoutes(http)
```

## Seeding Data

```bash
# Run seed function to populate projects table
npx convex run seed:seedProjects
```

Seeds 20 major cryptocurrencies (BTC, ETH, SOL, etc.) with metadata.

## Common Patterns

### External ID Pattern
Research tasks use `externalId` (UUID) for external references while keeping Convex `_id` internal:

```typescript
// Create with external ID
const taskId = await ctx.db.insert("deepResearchTasks", {
  externalId: crypto.randomUUID(),
  query: "...",
  // ...
})

// Query by external ID
await ctx.db
  .query("deepResearchTasks")
  .withIndex("by_external_id", (q) => q.eq("externalId", externalId))
  .first()
```

### Timestamps
Use `Date.now()` for all timestamps (stored as numbers):

```typescript
{
  createdAt: Date.now(),
  startedAt: Date.now(),
  completedAt: Date.now(),
}
```
