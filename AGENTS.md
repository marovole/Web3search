# AGENTS.md - Web3search AI Assistant Guide

Instructions for AI coding agents working in this codebase.

## Quick Reference

### Project Structure
```
Web3search/                    # Monorepo root
├── frontend/                  # React 18 + Vite + TailwindCSS
├── workers-api/               # Cloudflare Workers + Hono (main API)
├── convex/                    # Convex database schema and functions
├── openspec/                  # Spec-driven development
└── supabase/                  # Legacy - Database migrations (deprecated)
```

### Build/Test Commands

**Frontend** (`cd frontend`):
```bash
npm run dev              # Start dev server at localhost:5173
npm run build            # Production build
npm run lint             # ESLint check
npm run lint:fix         # ESLint auto-fix
npm run type-check       # TypeScript check (tsconfig.build.json)
npm test                 # Run all Jest tests
npm test -- --watch      # Watch mode
npm test -- path/to/file.test.tsx  # Run single test file
npm run test:coverage    # Run with coverage
npm run test:e2e         # Playwright E2E tests
```

**Workers API** (`cd workers-api`):
```bash
npm run dev              # Start local worker at localhost:8787
npm run deploy           # Deploy to Cloudflare
npm run test             # Run Vitest tests
npm run test -- path/to/file.test.ts  # Run single test
npm run test:watch       # Watch mode
npm run type-check       # TypeScript check
npm run lint             # ESLint check
```

**Root** (from repo root):
```bash
npm run build            # Build frontend
npm run test             # Run frontend tests
npm run lint             # Lint frontend
```

---

## Code Style Guidelines

### TypeScript Configuration
- **Strict mode enabled** in both frontend and workers-api
- Path alias: `@/*` maps to `./src/*`
- Target: ES2020 (frontend), ES2022 (workers-api)
- No implicit any, strict null checks enabled

### Naming Conventions
| Type | Convention | Example |
|------|------------|---------|
| Files | kebab-case | `chat-interface.tsx`, `model-routing.ts` |
| React Components | PascalCase | `ChatInterface`, `MessageList` |
| Functions | camelCase | `handleModeChange`, `fetchPriceData` |
| Constants | UPPER_SNAKE_CASE | `MAX_RETRIES`, `API_BASE_URL` |
| Types/Interfaces | PascalCase | `Message`, `ChatMode`, `Env` |
| CSS classes | kebab-case | `message-bubble`, `btn-primary` |

### Import Organization
```typescript
// 1. React and framework imports
import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'

// 2. Third-party libraries
import { Hono } from 'hono'
import * as Sentry from '@sentry/react'

// 3. Internal types (use 'type' import)
import type { Message, ChatMode } from '../../types'
import type { Env } from './types/env'

// 4. Internal modules (use path alias)
import { quickChat } from '@/services/api'
import { cn } from '@/lib/utils'

// 5. Components
import ModeSwitch from './ModeSwitch'
import MessageList from './MessageList'
```

### Type Safety Rules
**NEVER use these patterns:**
```typescript
// Forbidden - will be flagged in code review
as any
@ts-ignore
@ts-expect-error
// eslint-disable-next-line @typescript-eslint/no-explicit-any
```

**Instead:**
- Define proper types
- Use type guards
- Use `unknown` with runtime checks
- Prefix unused variables with `_`

### Error Handling
```typescript
// Frontend - use try/catch with Sentry
try {
  const result = await apiCall()
} catch (error) {
  Sentry.captureException(error)
  // Handle gracefully with user feedback
}

// Workers API - return structured errors
return c.json({
  error: {
    code: 'VALIDATION_ERROR',
    message: 'Invalid input',
    status: 400,
  },
}, 400)
```

### React Component Patterns
```typescript
// Prefer functional components with explicit types
interface MyComponentProps {
  title: string
  onClick: () => void
}

const MyComponent: React.FC<MyComponentProps> = ({ title, onClick }) => {
  // State declarations first
  const [isLoading, setIsLoading] = useState(false)
  
  // Refs
  const inputRef = useRef<HTMLInputElement>(null)
  
  // Effects
  useEffect(() => {
    // Effect logic
  }, [dependency])
  
  // Handlers
  const handleClick = useCallback(() => {
    onClick()
  }, [onClick])
  
  // Render
  return (
    <button onClick={handleClick} className="btn-primary">
      {title}
    </button>
  )
}
```

### Workers API Route Patterns
```typescript
// Use Hono with typed environment
import { Hono } from 'hono'
import type { Env } from '../types/env'

const app = new Hono<{ Bindings: Env }>()

// Route handlers return Response via context
app.get('/endpoint', async (c) => {
  const data = await fetchData(c.env.CONVEX_URL)
  return c.json({ data })
})

export default app
```

---

## Testing Guidelines

### Frontend (Jest + Testing Library)
```typescript
// File: component.test.tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { MyComponent } from './MyComponent'

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent title="Test" onClick={jest.fn()} />)
    expect(screen.getByText('Test')).toBeInTheDocument()
  })
})
```

### Workers API (Vitest)
```typescript
// File: endpoint.test.ts
import { describe, it, expect, vi } from 'vitest'
import app from '../index'

describe('GET /api/v1/health', () => {
  it('returns healthy status', async () => {
    const res = await app.request('/api/v1/health')
    expect(res.status).toBe(200)
  })
})
```

### Coverage Requirements
- Frontend global: 70% branches, 75% functions/lines
- Security files (tokenManager, inputValidation): 90%
- Workers API: 60% minimum

---

## Git Workflow

### Branch Strategy
- `main` - Production, protected
- `develop` - Development main branch
- `feature/*` - New features
- `bugfix/*` - Bug fixes
- `hotfix/*` - Urgent production fixes

### Commit Messages
```
<type>(<scope>): <subject>

Types: feat|fix|docs|style|refactor|test|chore
Example: feat(chat): add streaming response support
```

---

## OpenSpec Integration

For spec-driven development, reference `openspec/AGENTS.md`:

```bash
openspec list              # View active changes
openspec list --specs      # View specifications
openspec validate --strict # Validate changes
```

**When to create proposals:**
- New features or capabilities
- Breaking changes (API, schema)
- Architecture changes

**Skip proposals for:**
- Bug fixes, typos, formatting
- Dependency updates (non-breaking)
- Configuration changes

---

## Key Files Reference

| Purpose | Path |
|---------|------|
| Frontend entry | `frontend/src/main.tsx` |
| API entry | `workers-api/src/index.ts` |
| Frontend ESLint | `frontend/.eslintrc.cjs` |
| Workers ESLint | `workers-api/eslint.config.js` |
| Frontend TS config | `frontend/tsconfig.json` |
| Workers TS config | `workers-api/tsconfig.json` |
| Jest config | `frontend/jest.config.js` |
| Vitest config | `workers-api/vitest.config.ts` |
| Tailwind config | `frontend/tailwind.config.js` |
| Project context | `openspec/project.md` |

---

## Environment Variables

### Workers API (Cloudflare Secrets)
```bash
wrangler secret put CONVEX_URL
wrangler secret put CONVEX_DEPLOY_KEY
wrangler secret put JWT_SECRET
wrangler secret put OPENROUTER_API_KEY
wrangler secret put BRAVE_SEARCH_API_KEY
```

### Frontend (Cloudflare Pages)
```bash
VITE_API_BASE_URL=https://web3search-api.marovole.workers.dev
```

---

## Common Pitfalls

1. **Path aliases**: Use `@/` not relative `../../` for deep imports
2. **Type imports**: Use `import type { X }` for type-only imports
3. **Unused variables**: Prefix with `_` (e.g., `_unusedParam`)
4. **ESLint ignores**: Frontend ignores `src/__tests__`, `src/components/ui`
5. **Test files**: Excluded from TS build, use separate tsconfig
6. **Cloudflare Workers**: No Node.js APIs, use Web APIs only

---

## CI/CD Pipeline

Automated on push to `main`/`develop`:
1. ESLint check
2. TypeScript type-check
3. Unit tests with coverage
4. Production build
5. Workers API type-check

<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->
