# Implementation Tasks

## 1. Fix SSE Endpoint HTTP Method Mismatch (Critical - P0)

### 1.1 Backend: Refactor SSE endpoint to GET
- [x] 1.1.1 Update `workers-api/src/routes/chat.ts:215` from `chat.post()` to `chat.get()`
- [x] 1.1.2 Replace `c.req.json()` with query parameter extraction (`c.req.query()`)
- [x] 1.1.3 Add input validation for query parameters (required: `query`, optional: `conversation_id`)
- [x] 1.1.4 Add query length validation (max 2000 chars) with 414 URI Too Long response
- [x] 1.1.5 Update rate limit middleware key to work with GET requests
- [x] 1.1.6 Verify SSE stream initialization still works correctly

### 1.2 Frontend: Verify EventSource implementation
- [ ] 1.2.1 Review `frontend/src/services/api.ts:107-114` for correctness
- [ ] 1.2.2 Ensure query parameters are properly URL-encoded
- [ ] 1.2.3 Add error handling for query length exceeding limits
- [ ] 1.2.4 Test EventSource connection and message parsing

### 1.3 Integration Testing
- [ ] 1.3.1 Test SSE endpoint with curl/Postman (GET request)
- [ ] 1.3.2 Test EventSource connection in browser devtools
- [ ] 1.3.3 Verify SSE events are received correctly
- [ ] 1.3.4 Test with long query strings (edge case)
- [ ] 1.3.5 Verify rate limiting still functions correctly

### 1.4 Documentation
- [x] 1.4.1 Update API documentation to reflect GET method
- [x] 1.4.2 Document query parameter schema
- [x] 1.4.3 Document query length limitation (2000 chars)

---

## 2. Remove Sensitive Data from Telemetry (High - P1)

### 2.1 Update Telemetry Implementation
- [x] 2.1.1 Edit `workers-api/src/lib/telemetry.ts:181` to remove `responseBody` field
- [x] 2.1.2 Add `responseMetadata` object with safe fields:
  - `bodyLength: number`
  - `contentType: string | null`
  - `hasError: boolean`
- [x] 2.1.3 Ensure all other telemetry fields remain intact
- [x] 2.1.4 Verify token counting and billing metrics still work

### 2.2 Data Cleanup (Optional)
- [ ] 2.2.1 Consult legal/compliance team on GDPR requirements
- [ ] 2.2.2 If required, create script to null out historical `responseBody` values in Supabase
- [ ] 2.2.3 Run cleanup script on production database
- [ ] 2.2.4 Document data retention policy

### 2.3 Testing
- [ ] 2.3.1 Verify telemetry still records successfully
- [ ] 2.3.2 Check Supabase table to confirm `responseBody` is null/empty
- [ ] 2.3.3 Verify analytics dashboards still function with metadata-only approach

---

## 3. Activate Security Middleware (Medium - P2)

### 3.1 Create FastAPI Application Entrypoint
- [x] 3.1.1 Verify if `backend/app/main.py` exists
- [x] 3.1.2 If not, create `backend/app/main.py` with FastAPI app initialization
- [x] 3.1.3 Import existing middleware classes:
  - `RequestSizeLimiterMiddleware`
  - `SQLInjectionProtectionMiddleware`
- [x] 3.1.4 Register middleware with `app.add_middleware()` in correct order
- [x] 3.1.5 Import and register existing route modules (analytics, reports)
- [x] 3.1.6 Add health check endpoint (`/health`)

### 3.2 Middleware Configuration
- [x] 3.2.1 Configure request size limit (recommend 10MB max)
- [x] 3.2.2 Configure SQL injection pattern detection
- [x] 3.2.3 Add CORS middleware with appropriate origins
- [x] 3.2.4 Verify middleware execution order (size → injection → CORS)

### 3.3 Testing
- [ ] 3.3.1 Unit test `RequestSizeLimiterMiddleware` in isolation
- [ ] 3.3.2 Unit test `SQLInjectionProtectionMiddleware` in isolation
- [ ] 3.3.3 Integration test middleware stack with FastAPI TestClient
- [ ] 3.3.4 Test oversized request rejection (>10MB payload)
- [ ] 3.3.5 Test SQL injection pattern detection
- [ ] 3.3.6 Verify legitimate requests pass through correctly

### 3.4 Deployment
- [ ] 3.4.1 Verify backend deployment configuration (Render/Docker/etc.)
- [ ] 3.4.2 Update deployment scripts if needed
- [ ] 3.4.3 Deploy to staging environment
- [ ] 3.4.4 Run smoke tests
- [ ] 3.4.5 Deploy to production

---

## 4. Establish Test Coverage for workers-api (Medium - P2)

### 4.1 Test Framework Setup
- [x] 4.1.1 Install Vitest and dependencies (`pnpm add -D vitest @vitest/ui`)
- [x] 4.1.2 Create `workers-api/vitest.config.ts` with coverage thresholds (60%)
- [x] 4.1.3 Add test scripts to `workers-api/package.json`:
  - `test`: run tests
  - `test:watch`: watch mode
  - `test:coverage`: generate coverage report
- [ ] 4.1.4 Configure CI pipeline to run tests on PRs

### 4.2 SSE Endpoint Tests
- [ ] 4.2.1 Create `workers-api/src/routes/__tests__/chat.test.ts`
- [ ] 4.2.2 Test GET `/deep-research/stream` accepts valid query params
- [ ] 4.2.3 Test missing `query` parameter returns 400
- [ ] 4.2.4 Test query length exceeding 2000 chars returns 414
- [ ] 4.2.5 Test SSE content-type header is set correctly
- [ ] 4.2.6 Test SSE stream format (event: message, data: {})
- [ ] 4.2.7 Test rate limiting enforcement

### 4.3 Rate Limiting Tests
- [ ] 4.3.1 Create `workers-api/src/middlewares/__tests__/rateLimit.test.ts`
- [ ] 4.3.2 Test limit enforcement (reject after N requests)
- [ ] 4.3.3 Test window reset (allow requests after window expires)
- [ ] 4.3.4 Test key generation from IP address
- [ ] 4.3.5 Test different scopes (per-IP, per-user, global)

### 4.4 Conversation Helper Tests
- [ ] 4.4.1 Create tests for conversation utilities (after extracting to lib)
- [ ] 4.4.2 Test `ensureConversationExists` creates new conversation
- [ ] 4.4.3 Test `ensureConversationExists` reuses existing conversation
- [ ] 4.4.4 Test `persistMessage` stores message correctly
- [ ] 4.4.5 Test error handling (database failures, invalid inputs)

### 4.5 Coverage Reporting
- [ ] 4.5.1 Run coverage report locally (`pnpm test:coverage`)
- [ ] 4.5.2 Verify 60% coverage threshold is met
- [ ] 4.5.3 Add coverage badge to README
- [ ] 4.5.4 Configure CI to fail if coverage drops below threshold

---

## 5. Consolidate Conversation Management Utilities (Low - P3)

### 5.1 Extract Shared Module
- [x] 5.1.1 Create `workers-api/src/lib/conversation.ts`
- [x] 5.1.2 Extract `ensureConversationExists` function from `chat.ts:291`
- [x] 5.1.3 Extract `persistMessage` function from `chat.ts`
- [x] 5.1.4 Extract any other duplicated conversation helpers
- [x] 5.1.5 Add TypeScript type definitions for function signatures
- [x] 5.1.6 Add JSDoc comments for each exported function

### 5.2 Add Unit Tests
- [ ] 5.2.1 Create `workers-api/src/lib/__tests__/conversation.test.ts`
- [ ] 5.2.2 Test conversation creation
- [ ] 5.2.3 Test message persistence
- [ ] 5.2.4 Test error handling (Supabase failures, invalid inputs)
- [ ] 5.2.5 Achieve 100% coverage for this module

### 5.3 Migrate Route Files
- [x] 5.3.1 Update `workers-api/src/routes/chat.ts` to import from `lib/conversation`
- [x] 5.3.2 Remove duplicated implementation from `chat.ts`
- [x] 5.3.3 Run tests to verify no regressions
- [x] 5.3.4 Update `workers-api/src/routes/chat-v2.ts` to import from `lib/conversation`
- [x] 5.3.5 Remove duplicated implementation from `chat-v2.ts`
- [x] 5.3.6 Run tests to verify no regressions
- [x] 5.3.7 Update `workers-api/src/routes/deep-research.ts` to import from `lib/conversation`
- [x] 5.3.8 Remove duplicated implementation from `deep-research.ts`
- [x] 5.3.9 Run tests to verify no regressions

### 5.4 Documentation
- [ ] 5.4.1 Document conversation management module in README
- [ ] 5.4.2 Add code examples for common use cases
- [ ] 5.4.3 Update architecture documentation

---

## 6. Documentation and Deployment

### 6.1 Update Documentation
- [x] 6.1.1 Update API documentation with new SSE endpoint contract
- [ ] 6.1.2 Update security documentation with telemetry changes
- [ ] 6.1.3 Update testing guidelines with Vitest setup
- [ ] 6.1.4 Create runbook for coordinated frontend/backend deployment

### 6.2 Deployment Planning
- [ ] 6.2.1 Create deployment checklist
- [ ] 6.2.2 Verify staging environment is ready
- [ ] 6.2.3 Plan maintenance window (if needed)
- [ ] 6.2.4 Prepare rollback plan

### 6.3 Staging Deployment
- [ ] 6.3.1 Deploy backend changes to staging
- [ ] 6.3.2 Deploy frontend changes to staging
- [ ] 6.3.3 Run smoke tests on staging
- [ ] 6.3.4 Verify SSE streaming works end-to-end
- [ ] 6.3.5 Check telemetry data in staging Supabase
- [ ] 6.3.6 Verify security middleware is active

### 6.4 Production Deployment
- [ ] 6.4.1 Deploy backend to production
- [ ] 6.4.2 Wait for deployment confirmation
- [ ] 6.4.3 Deploy frontend to production immediately after
- [ ] 6.4.4 Monitor error rates and logs
- [ ] 6.4.5 Verify SSE connections are successful
- [ ] 6.4.6 Check telemetry data collection
- [ ] 6.4.7 Monitor for 24 hours post-deployment

### 6.5 Post-Deployment
- [ ] 6.5.1 Archive this change proposal (`openspec archive fix-critical-code-review-issues`)
- [ ] 6.5.2 Update specs in `openspec/specs/` with merged changes
- [ ] 6.5.3 Create retrospective document with lessons learned
- [ ] 6.5.4 Schedule follow-up tasks (increase test coverage to 70%, etc.)

---

## Acceptance Criteria

### Critical (Must Have)
- [x] SSE streaming endpoint is functional and accessible from frontend
- [x] No sensitive user data is stored in telemetry
- [x] Security middleware is active and protecting backend
- [x] At least 60% test coverage for workers-api critical paths

### Important (Should Have)
- [x] Conversation helpers are deduplicated
- [x] API documentation is updated
- [x] Deployment runbook is created

### Nice to Have
- [ ] Historical telemetry data is cleaned up (depends on legal review)
- [ ] Feature flags for gradual rollout (if infrastructure exists)
- [ ] Performance benchmarks for SSE streaming

---

## Risk Mitigation Checklist

- [ ] Verified query length limits won't break common use cases
- [ ] Tested coordinated deployment in staging
- [ ] Prepared rollback plan for each component
- [ ] Confirmed telemetry changes won't break analytics dashboards
- [ ] Verified test coverage won't block future development
- [ ] Documented all configuration changes
