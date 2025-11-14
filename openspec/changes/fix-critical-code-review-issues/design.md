# Technical Design: Critical Code Review Fixes

## Context

This change addresses five critical issues discovered during a comprehensive code review of the Web3search platform, focusing on the recent security and Deep Research SSE implementation. The issues span multiple layers of the architecture (frontend, workers-api, backend) and affect security, functionality, and maintainability.

### Background
- Recent commits added Deep Research streaming via SSE but the feature is non-functional
- Security middleware was implemented but never activated
- Telemetry stores sensitive user data in plaintext
- No automated test coverage for workers-api layer
- Conversation helpers duplicated across multiple files

### Constraints
- Must maintain backward compatibility for existing non-SSE endpoints
- Frontend and backend must be deployed simultaneously to avoid API breakage
- Cannot break existing telemetry data collection (only modify what's stored)
- Must work within current Cloudflare Workers and Supabase infrastructure

### Stakeholders
- End users: Need functional Deep Research streaming
- Security team: Require privacy compliance and attack surface reduction
- Development team: Need maintainable code and test coverage
- Operations: Need reliable deployments without regressions

---

## Goals / Non-Goals

### Goals
1. **Make SSE streaming functional** - Users can access Deep Research with real-time progress updates
2. **Eliminate privacy risks** - Stop storing sensitive user data in telemetry
3. **Activate security protections** - Wire middleware to actually protect the backend
4. **Establish test foundation** - Add critical test coverage for workers-api
5. **Reduce code duplication** - Centralize conversation management utilities

### Non-Goals
- Rewriting the entire SSE implementation (keep existing logic, just fix the transport)
- Migrating away from EventSource (prefer standard browser APIs)
- Full test coverage of all features (focus on new/critical paths only)
- Refactoring unrelated code quality issues
- Performance optimization (unless blocking functionality)

---

## Decisions

### Decision 1: SSE Endpoint Transport Method

**Choice**: Convert SSE endpoint to GET with query parameters

**Rationale**:
- EventSource API only supports GET requests (W3C specification)
- Query parameters are sufficient for current use case (query string, conversation ID)
- Avoids need to rewrite frontend to use fetch + ReadableStream (more complex)
- Maintains standard SSE patterns (EventSource is the canonical client)

**Alternatives Considered**:
1. ❌ **Switch frontend to fetch + ReadableStream**
   - More complex client-side implementation
   - Requires manual SSE parsing and reconnection logic
   - Loses built-in EventSource features (auto-reconnect, message parsing)

2. ❌ **Use POST with hidden iframe trick**
   - Hacky workaround, not maintainable
   - Poor browser support and security implications

3. ✅ **GET with query parameters** (Selected)
   - Standard SSE pattern
   - Minimal code changes
   - Works with all browsers

**Implementation**:
```typescript
// Backend: workers-api/src/routes/chat.ts
chat.get('/deep-research/stream',
  createRateLimitMiddleware({...}),
  async (c) => {
    const query = c.req.query('query')
    const conversation_id = c.req.query('conversation_id')
    // ... existing SSE logic
  }
)

// Frontend: frontend/src/services/api.ts
const deepResearchStreamReal = (request: DeepResearchRequest): EventSource => {
  const queryParams = new URLSearchParams({
    query: request.query,
    ...(request.conversation_id && { conversation_id: request.conversation_id }),
  })
  const url = `${api.defaults.baseURL}/api/v1/chat/deep-research/stream?${queryParams}`
  return new EventSource(url)
}
```

**Edge Cases**:
- Very long query strings (>2048 chars): Add validation and return 414 URI Too Long
- Special characters in query: Ensure proper URL encoding
- Missing required query params: Return 400 Bad Request before opening SSE stream

---

### Decision 2: Telemetry Data Storage

**Choice**: Remove `responseBody` field entirely, store only metadata

**Rationale**:
- Full responses contain sensitive user data (prompts, outputs, potential PII)
- Metadata (token counts, status codes) sufficient for monitoring and billing
- Reduces storage costs and GDPR compliance risk
- No legitimate use case for full response body in production telemetry

**Alternatives Considered**:
1. ❌ **Truncate to first 100 characters**
   - Still risks leaking sensitive info in preview
   - Inconsistent usefulness (first 100 chars may not be meaningful)

2. ❌ **Hash the response body**
   - Useless for debugging (can't read hashed content)
   - Still stores unnecessary data

3. ❌ **Store with encryption**
   - Adds complexity (key management, rotation)
   - Still vulnerable if encryption keys compromised
   - Doesn't address "why store it at all" question

4. ✅ **Remove entirely, keep metadata** (Selected)
   - Simplest solution
   - Zero privacy risk
   - Sufficient for operational needs

**Implementation**:
```typescript
// workers-api/src/lib/telemetry.ts
await trackAPICall({
  // ... other fields

  // REMOVED: responseBody: responseBody,

  // ADDED: Response metadata only
  responseMetadata: {
    bodyLength: responseBody?.length || 0,
    contentType: result.data?.headers.get('content-type'),
    hasError: !!result.error,
  },

  completionTokens,
  finishReason,
  // ... rest of metadata
})
```

**Data Migration**:
- No schema change required (column can remain, just don't populate)
- Consider running cleanup script to null out historical `responseBody` values (GDPR Right to Erasure)
- Update Supabase RLS policies if needed to prevent future writes to that column

---

### Decision 3: Middleware Activation

**Choice**: Create `backend/app/main.py` with FastAPI app initialization

**Rationale**:
- Standard FastAPI pattern requires explicit app instance and middleware registration
- Middleware classes are implemented but orphaned
- Need centralized app entrypoint for deployment and testing

**Alternatives Considered**:
1. ❌ **Implement protections in Cloudflare Workers instead**
   - Workers already have rate limiting
   - But backend still exists and needs protection
   - Don't leave security gaps

2. ❌ **Delete the middleware classes**
   - Defeats purpose of protections
   - Backend would remain vulnerable

3. ✅ **Create proper FastAPI app entrypoint** (Selected)
   - Standard Python web app pattern
   - Enables testing and extension
   - Activates existing middleware code

**Implementation**:
```python
# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.middleware.request_size_limiter import RequestSizeLimiterMiddleware
from app.middleware.sql_injection_protection import SQLInjectionProtectionMiddleware
from app.api.v1 import analytics, reports

app = FastAPI(
    title="Web3search Backend API",
    version="1.0.0",
)

# Security middleware (order matters - from outermost to innermost)
app.add_middleware(RequestSizeLimiterMiddleware)
app.add_middleware(SQLInjectionProtectionMiddleware)
app.add_middleware(CORSMiddleware, allow_origins=["*"])  # TODO: Restrict in production

# Routes
app.include_router(analytics.router, prefix="/api/v1/analytics")
app.include_router(reports.router, prefix="/api/v1/reports")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

**Testing Strategy**:
- Unit test each middleware in isolation
- Integration test middleware stack with FastAPI TestClient
- Verify middleware order (size limit must come before SQL injection check)

---

### Decision 4: Test Framework and Coverage

**Choice**: Use Vitest for workers-api, focus on critical paths first

**Rationale**:
- Vitest is TypeScript-native, fast, and works well with Cloudflare Workers
- Start with high-value tests (SSE, rate limiting, security) rather than 100% coverage
- Set realistic initial threshold (60%) and increase over time

**Alternatives Considered**:
1. ❌ **Jest**
   - Slower than Vitest
   - More configuration for TypeScript/ESM

2. ❌ **No tests, rely on manual testing**
   - Unacceptable for security and critical features
   - High regression risk

3. ✅ **Vitest with focused coverage** (Selected)
   - Fast, modern, TypeScript-friendly
   - Pragmatic approach (test what matters most)

**Implementation**:
```typescript
// workers-api/vitest.config.ts
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      lines: 60,
      functions: 60,
      branches: 60,
      statements: 60,
    },
  },
})
```

**Test Priorities** (in order):
1. SSE streaming endpoint (GET method, query params, stream format)
2. Rate limiting middleware (limit enforcement, window reset, key generation)
3. Conversation helpers (conversation creation, message persistence, error handling)
4. Input validation (query length, required fields, special characters)

---

### Decision 5: Code Deduplication Strategy

**Choice**: Extract to `workers-api/src/lib/conversation.ts` shared module

**Rationale**:
- Single source of truth reduces drift
- Easier to add features and fix bugs
- Testable in isolation
- Follows standard module organization pattern

**Alternatives Considered**:
1. ❌ **Leave duplicated, document to keep in sync**
   - Unrealistic, will drift over time
   - Doesn't solve the root problem

2. ❌ **Create base class for routes to inherit**
   - Over-engineered for simple helper functions
   - Harder to test and reason about

3. ✅ **Shared utility module** (Selected)
   - Simple, clear, testable
   - Standard pattern in TypeScript projects

**Implementation**:
```typescript
// workers-api/src/lib/conversation.ts
import { SupabaseClient } from '@supabase/supabase-js'

export async function ensureConversationExists(
  supabase: SupabaseClient,
  userId: string | null
): Promise<string> {
  // Unified implementation with error handling
}

export async function persistMessage(
  supabase: SupabaseClient,
  conversationId: string,
  role: 'user' | 'assistant',
  content: string
): Promise<void> {
  // Unified implementation
}

// ... other shared helpers
```

**Migration Path**:
1. Create new module with extracted functions
2. Add comprehensive unit tests
3. Update `chat.ts` to import and use new module (test)
4. Update `chat-v2.ts` to import and use new module (test)
5. Update `deep-research.ts` to import and use new module (test)
6. Remove duplicated implementations

---

## Risks / Trade-offs

### Risk 1: SSE Query String Length Limits

**Description**: Deep Research queries might exceed URL length limits (2048 chars in some browsers/proxies)

**Mitigation**:
- Add validation on frontend and backend (reject queries >2000 chars with clear error)
- Document limitation in API docs
- Future: Consider hybrid approach (short queries via GET, long queries POST to create session, then GET to stream with session ID)

**Trade-off**: Simplicity vs. flexibility (accepting short-term limitation for quick fix)

---

### Risk 2: Simultaneous Deployment Requirement

**Description**: Frontend and backend must be deployed together to avoid API contract breakage

**Mitigation**:
- Use feature flags to gradually roll out SSE changes
- Add API version negotiation (frontend checks backend version before using new endpoint)
- Document deployment order in runbook

**Trade-off**: Deployment complexity vs. avoiding intermediate broken state

---

### Risk 3: Telemetry Data Loss for Debugging

**Description**: Removing response bodies eliminates potential debugging information

**Mitigation**:
- Enhance structured logging (log request/response at DEBUG level, not persisted long-term)
- Add sampling for detailed telemetry (1% of requests log full bodies to separate audit table with TTL)
- Improve error messages to include relevant context without full responses

**Trade-off**: Debug convenience vs. privacy and compliance

---

### Risk 4: Test Coverage Threshold Too Low

**Description**: 60% coverage may miss important edge cases

**Mitigation**:
- Focus on critical paths first (SSE, auth, security)
- Gradually increase threshold (60% → 70% → 80%) over subsequent quarters
- Require 100% coverage for new security-related code

**Trade-off**: Pragmatism vs. perfection (better to have some tests than get blocked on 100%)

---

## Migration Plan

### Phase 1: Critical Fixes (Week 1)
1. **Day 1-2**: SSE endpoint refactoring
   - Backend: Change POST → GET in `chat.ts:215`
   - Frontend: Verify query parameter serialization
   - Test: Manual testing with browser devtools

2. **Day 3-4**: Telemetry cleanup
   - Update `telemetry.ts` to remove `responseBody`
   - Deploy to staging and verify metrics still collected
   - (Optional) Run cleanup script on production DB

3. **Day 5**: Coordinated deployment
   - Deploy backend first (GET endpoint is additive, doesn't break existing)
   - Deploy frontend immediately after
   - Monitor error rates and SSE connection success

**Rollback**:
- Frontend: Revert to previous version (GET still works with old code)
- Backend: Keep new version (backward compatible)

---

### Phase 2: Security & Testing (Week 2)
1. **Day 1-3**: Middleware activation
   - Create `backend/app/main.py`
   - Wire up security middleware
   - Add integration tests
   - Deploy to staging

2. **Day 4-5**: Test framework setup
   - Install Vitest in workers-api
   - Write SSE endpoint tests
   - Configure CI to run tests
   - Enforce coverage threshold

**Rollback**:
- Middleware: Remove from app startup if causing issues
- Tests: Safe to add incrementally (no runtime impact)

---

### Phase 3: Code Quality (Week 3)
1. **Day 1-2**: Extract conversation helpers
   - Create `lib/conversation.ts`
   - Add unit tests for helpers

2. **Day 3-5**: Migrate route files
   - Update one file at a time (chat.ts → chat-v2.ts → deep-research.ts)
   - Test after each migration
   - Remove old implementations

**Rollback**:
- Safe (behavioral no-op if done correctly)
- Revert individual commits if issues found

---

## Open Questions

1. **Query length limit**: What's the longest reasonable Deep Research query?
   - Action: Analyze production logs to determine 95th percentile query length
   - Decision: Set limit at 99th percentile + buffer

2. **Telemetry cleanup**: Should we delete historical `responseBody` data?
   - Action: Consult legal/compliance team on GDPR requirements
   - Decision: Implement if required, document retention policy

3. **Backend deployment**: Is `backend/` currently deployed? Where?
   - Action: Check deployment configs (Render, Docker, etc.)
   - Decision: If not deployed, deprioritize middleware activation

4. **Test coverage**: What's acceptable initial coverage for workers-api?
   - Action: Review with team lead
   - Decision: 60% seems reasonable for first pass, document plan to increase

5. **Feature flags**: Do we have feature flag infrastructure?
   - Action: Check for existing flag system (LaunchDarkly, custom, etc.)
   - Decision: If yes, use flags for gradual rollout; if no, skip for now
