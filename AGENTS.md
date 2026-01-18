# AGENTS.md - Web3search AI Agent Guide

## Architecture Overview

```
Frontend (React+Vite)  →  Workers API (Hono)  →  Convex (Database)
     Cloudflare Pages       Cloudflare Workers      Real-time DB
```

**Key insight**: Workers API calls Convex via HTTP endpoints (`.convex.site`), not deploy key mutations.

## Quick Commands

| Location | Command | Purpose |
|----------|---------|---------|
| `frontend/` | `npm run dev` | Dev server :5173 |
| `frontend/` | `npm run build && npm run type-check` | Verify before commit |
| `workers-api/` | `npm run dev` | Local API :8787 |
| `workers-api/` | `npm run deploy` | Deploy to Cloudflare |
| `convex/` | `npx convex dev` | Sync functions |

## Code Conventions

### TypeScript Strict Mode
- Path alias: `@/*` → `./src/*`
- **FORBIDDEN**: `as any`, `@ts-ignore`, `@ts-expect-error`
- Unused vars: prefix with `_`

### Naming
| Type | Convention | Example |
|------|------------|---------|
| Files | kebab-case | `chat-interface.tsx` |
| Components | PascalCase | `ChatInterface` |
| Functions | camelCase | `handleModeChange` |
| Types | PascalCase | `Message`, `Env` |

### Import Order
```typescript
// 1. React/framework
// 2. Third-party libs
// 3. Internal types (use 'import type')
// 4. Internal modules (use @/ alias)
// 5. Components
```

## Testing

| Package | Framework | Min Coverage |
|---------|-----------|--------------|
| Frontend | Jest + Testing Library | 75% |
| Workers API | Vitest | 60% |

```bash
# Frontend
npm test -- path/to/file.test.tsx

# Workers API
npm run test -- path/to/file.test.ts
```

## Environment Secrets

### Workers API (Cloudflare)
```bash
wrangler secret put CONVEX_URL      # https://xxx.convex.cloud
wrangler secret put JWT_SECRET
wrangler secret put OPENROUTER_API_KEY
wrangler secret put BRAVE_SEARCH_API_KEY
```

### Frontend (Pages)
```
VITE_API_BASE_URL=https://web3search-api.marovole.workers.dev
```

## Key Files

| Purpose | Path |
|---------|------|
| API entry | `workers-api/src/index.ts` |
| Frontend entry | `frontend/src/main.tsx` |
| Convex HTTP | `convex/http.ts` |
| DB Schema | `convex/schema.ts` |
| OpenSpec guide | `openspec/AGENTS.md` |

## Commit Convention

```
<type>(<scope>): <subject>
# Types: feat|fix|docs|style|refactor|test|chore
# Example: feat(chat): add streaming response
```

## Child AGENTS.md Files

- **`workers-api/AGENTS.md`** - API routes, multi-agent system, cron jobs
- **`convex/AGENTS.md`** - Schema, functions, HTTP endpoints
- **`openspec/AGENTS.md`** - Spec-driven development workflow

## Common Pitfalls

1. **Convex HTTP**: Use `.convex.site` domain for HTTP actions, not `.convex.cloud`
2. **Path aliases**: Use `@/` not relative `../../` for deep imports
3. **Type imports**: Use `import type { X }` for type-only imports
4. **Cloudflare Workers**: NO Node.js APIs - Web APIs only
5. **ESLint ignores**: Frontend ignores `src/__tests__`, `src/components/ui`

<!-- OPENSPEC:START -->
# OpenSpec Instructions

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts
- Sounds ambiguous and you need the authoritative spec before coding

<!-- OPENSPEC:END -->
