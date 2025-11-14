# Fix Critical Code Review Issues

## Why

A comprehensive code review revealed five critical issues that severely impact system functionality, security, and reliability:

1. **Critical**: The newly implemented Deep Research SSE streaming endpoint is completely unreachable due to HTTP method mismatch (backend expects POST with JSON body, frontend uses EventSource which only supports GET), rendering the entire streaming feature unusable in production.

2. **High**: Telemetry system stores complete API response bodies (including user prompts and model outputs) in plaintext to Supabase, creating a severe privacy breach risk if the database or service-role key is compromised.

3. **Medium**: Security middleware classes (`RequestSizeLimiterMiddleware` and `SQLInjectionProtectionMiddleware`) are implemented but never connected to the FastAPI application, leaving the backend vulnerable to oversized payloads and SQL injection attacks.

4. **Medium**: The entire `workers-api` layer lacks automated tests, with no `.test.ts` files covering the new SSE handlers, rate limiting, or deep research pipeline, creating high regression risk.

5. **Code Quality**: Conversation management helpers (`ensureConversationExists`, `persistMessage`) are duplicated across three route files (`chat.ts`, `chat-v2.ts`, `deep-research.ts`), causing maintenance overhead and drift between implementations.

## What Changes

- **BREAKING**: Refactor SSE endpoint from POST to GET to enable EventSource compatibility
  - Backend: Change `/deep-research/stream` to accept GET requests with query parameters
  - Frontend: Update request payload serialization to use URL query parameters
  - Update API documentation to reflect new endpoint contract

- **Security**: Remove sensitive data from telemetry storage
  - Stop storing full `responseBody` in API call tracking
  - Store only metadata (token counts, status codes, finish reasons)
  - Add data retention policy documentation

- **Security**: Wire security middleware to FastAPI application
  - Create or locate `backend/app/main.py` entrypoint
  - Register `RequestSizeLimiterMiddleware` and `SQLInjectionProtectionMiddleware`
  - Add integration tests for middleware activation

- **Testing**: Establish test coverage for workers-api
  - Add Vitest test framework configuration
  - Create test suites for SSE streaming, rate limiting, and conversation helpers
  - Set minimum coverage threshold (60%)

- **Refactoring**: Consolidate conversation management utilities
  - Extract shared functions to `workers-api/src/lib/conversation.ts`
  - Update all route files to import from centralized module
  - Add unit tests for extracted utilities

## Impact

### Affected Specs
- `api` - SSE endpoint contract changes (**BREAKING**)
- `security` - Telemetry data handling, middleware integration
- `chat-interface` - Frontend SSE client implementation
- `deployment` - Test coverage requirements and CI pipeline

### Affected Code
- `workers-api/src/routes/chat.ts:215` - SSE endpoint signature
- `workers-api/src/lib/telemetry.ts:181` - Response body storage
- `backend/app/main.py` - Middleware registration (new file may be needed)
- `frontend/src/services/api.ts:107-114` - SSE client implementation
- `workers-api/src/routes/{chat.ts,chat-v2.ts,deep-research.ts}` - Duplicate conversation helpers

### User Impact
- **Immediate**: Deep Research streaming feature will become functional
- **Short-term**: Enhanced security posture and reduced privacy risks
- **Long-term**: Improved code maintainability and test coverage

### Deployment Considerations
- Frontend and backend must be deployed simultaneously to avoid API contract mismatch
- Existing telemetry data cleanup may be required (consider GDPR compliance)
- No database migrations required
- Backward compatibility maintained for non-SSE endpoints
