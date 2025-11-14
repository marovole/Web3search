# Deployment Specification Deltas

## ADDED Requirements

### Requirement: Workers-API Test Coverage
The workers-api layer **SHALL** have automated test coverage to prevent regressions and ensure reliability.

#### Scenario: Test Framework Setup
- **WHEN** setting up test infrastructure for workers-api
- **THEN** use Vitest as the test framework
- **AND** configure coverage reporting with minimum thresholds:
  - Lines: 60%
  - Functions: 60%
  - Branches: 60%
  - Statements: 60%
- **AND** generate coverage reports in CI pipeline
- **AND** fail builds if coverage falls below threshold

**Implementation**: Create `workers-api/vitest.config.ts`:
```typescript
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

#### Scenario: SSE Endpoint Testing
- **WHEN** testing Deep Research SSE endpoints
- **THEN** verify GET method acceptance
- **AND** test query parameter parsing
- **AND** validate query length limits (reject >2000 chars)
- **AND** verify SSE content-type header
- **AND** test SSE event format and streaming
- **AND** verify rate limiting enforcement

**Test Location**: `workers-api/src/routes/__tests__/chat.test.ts`

**Example Test**:
```typescript
describe('Deep Research SSE', () => {
  it('should accept GET requests with query params', async () => {
    const res = await app.request(
      '/api/v1/chat/deep-research/stream?query=test'
    )
    expect(res.status).toBe(200)
    expect(res.headers.get('content-type')).toContain('text/event-stream')
  })

  it('should reject queries exceeding 2000 characters', async () => {
    const longQuery = 'a'.repeat(2001)
    const res = await app.request(
      `/api/v1/chat/deep-research/stream?query=${longQuery}`
    )
    expect(res.status).toBe(414)
  })
})
```

#### Scenario: Rate Limiting Tests
- **WHEN** testing rate limiting middleware
- **THEN** verify limit enforcement (reject after N requests)
- **AND** test window reset (allow requests after expiry)
- **AND** verify key generation from IP address
- **AND** test different scopes (per-IP, per-user)
- **AND** verify graceful degradation when KV unavailable

**Test Location**: `workers-api/src/middlewares/__tests__/rateLimit.test.ts`

#### Scenario: Conversation Helper Tests
- **WHEN** testing conversation management utilities
- **THEN** test conversation creation
- **AND** test conversation reuse
- **AND** test message persistence
- **AND** test error handling (database failures, invalid inputs)
- **AND** mock Supabase client for isolation

**Test Location**: `workers-api/src/lib/__tests__/conversation.test.ts` (after extracting helpers)

#### Scenario: Test Coverage Reporting
- **WHEN** running tests in CI pipeline
- **THEN** generate coverage report
- **AND** upload to CI artifacts for review
- **AND** fail build if coverage < threshold
- **AND** display coverage badge in README
- **AND** track coverage trends over time

**CI Configuration** (GitHub Actions):
```yaml
- name: Run tests
  run: |
    cd workers-api
    pnpm test:coverage

- name: Check coverage threshold
  run: |
    cd workers-api
    pnpm test:coverage --reporter=json --outputFile=coverage.json
    # Fail if coverage < 60%

- name: Upload coverage
  uses: actions/upload-artifact@v3
  with:
    name: coverage-report
    path: workers-api/coverage/
```

---

### Requirement: Backend Security Middleware Testing
The backend **SHALL** have automated tests for security middleware to verify protection mechanisms.

#### Scenario: Request Size Limiter Tests
- **WHEN** testing request size limiting
- **THEN** verify legitimate requests (<10MB) pass through
- **AND** verify oversized requests (>10MB) are rejected with 413
- **AND** verify error message is user-friendly
- **AND** verify security logging captures attempts
- **AND** test with various content types (JSON, multipart/form-data)

**Test Location**: `backend/app/middleware/__tests__/request_size_limiter_test.py`

**Example Test**:
```python
def test_request_size_limiter_rejects_large_payload():
    client = TestClient(app)
    large_payload = "x" * (11 * 1024 * 1024)  # 11MB
    response = client.post("/api/v1/analytics", json={"data": large_payload})

    assert response.status_code == 413
    assert "exceeds maximum size" in response.json()["error"]["message"]
```

#### Scenario: SQL Injection Protection Tests
- **WHEN** testing SQL injection protection
- **THEN** verify legitimate requests pass through
- **AND** verify malicious patterns are blocked:
  - `UNION SELECT`
  - `'; DROP TABLE`
  - `OR 1=1`
  - `<script>`, `javascript:`
- **AND** verify error code is 400 Bad Request
- **AND** verify error message doesn't leak detection logic
- **AND** verify security logging captures attempts

**Test Location**: `backend/app/middleware/__tests__/sql_injection_protection_test.py`

#### Scenario: Middleware Integration Tests
- **WHEN** testing complete middleware stack
- **THEN** verify middleware execution order is correct
- **AND** verify middleware chain doesn't break on exceptions
- **AND** verify response headers are set correctly
- **AND** verify CORS, size limit, and injection protection work together

**Test Location**: `backend/tests/integration/test_middleware_stack.py`

---

### Requirement: End-to-End SSE Testing
The system **SHALL** have end-to-end tests for SSE streaming functionality.

#### Scenario: Deep Research E2E Test
- **WHEN** running E2E tests for Deep Research
- **THEN** test complete user flow:
  1. Navigate to Deep Research page
  2. Enter query (within length limit)
  3. Submit and verify SSE connection opens
  4. Verify progress events received
  5. Verify final result displayed
  6. Verify connection closes gracefully
- **AND** use Playwright or similar E2E framework
- **AND** test in real browser environment (Chrome, Firefox)

**Test Location**: `frontend/tests/e2e/deep-research.spec.ts` or `tests/e2e/deep-research-sse.spec.ts`

**Example Test**:
```typescript
test('Deep Research streaming works end-to-end', async ({ page }) => {
  await page.goto('/deep-research')

  await page.fill('[data-testid="query-input"]', 'What is Bitcoin?')
  await page.click('[data-testid="submit-button"]')

  // Wait for SSE connection and first progress event
  await page.waitForSelector('[data-testid="progress-indicator"]', {
    state: 'visible',
    timeout: 5000,
  })

  // Verify progress updates appear
  const progressText = await page.textContent('[data-testid="progress-stage"]')
  expect(progressText).toContain('searching')

  // Wait for final result (max 60s for Deep Research)
  await page.waitForSelector('[data-testid="result-content"]', {
    state: 'visible',
    timeout: 60000,
  })

  const result = await page.textContent('[data-testid="result-content"]')
  expect(result.length).toBeGreaterThan(100) // Verify meaningful content
})
```

#### Scenario: Query Length Validation E2E
- **WHEN** testing query length limits
- **THEN** enter query exceeding 2000 characters
- **AND** verify submit button is disabled
- **AND** verify error message displayed
- **AND** verify character counter shows red
- **AND** shorten query and verify submit is re-enabled

#### Scenario: Rate Limiting E2E
- **WHEN** testing rate limiting behavior
- **THEN** submit 5 Deep Research requests rapidly
- **AND** verify 6th request is rejected with 429
- **AND** verify error message shows "Too many requests"
- **AND** verify retry countdown displayed

---

### Requirement: CI/CD Pipeline Enhancement
The CI/CD pipeline **SHALL** run all tests and enforce quality gates before deployment.

#### Scenario: Pull Request Checks
- **WHEN** a pull request is created
- **THEN** run all unit tests (frontend, backend, workers-api)
- **AND** run integration tests
- **AND** generate coverage reports
- **AND** fail if coverage drops below threshold
- **AND** run linter and type checker
- **AND** block merge if any check fails

**GitHub Actions Workflow**:
```yaml
name: PR Checks

on: [pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install dependencies
        run: pnpm install

      - name: Run workers-api tests
        run: |
          cd workers-api
          pnpm test:coverage

      - name: Run backend tests
        run: |
          cd backend
          pytest --cov --cov-fail-under=60

      - name: Run frontend tests
        run: |
          cd frontend
          pnpm test

      - name: Run E2E tests
        run: pnpm test:e2e
```

#### Scenario: Pre-Deployment Smoke Tests
- **WHEN** deploying to staging or production
- **THEN** run smoke tests before promoting
- **AND** test critical paths:
  - Health check endpoint
  - Quick Chat
  - Deep Research SSE
  - Search autocomplete
- **AND** revert deployment if smoke tests fail

**Smoke Test Script**: `scripts/smoke-test.js`

---

## MODIFIED Requirements

### Requirement: Deployment Best Practices
Deployment configuration **SHALL** follow security and reliability best practices, **including comprehensive testing before production**.

#### Scenario: Pre-Deployment Checklist
- **WHEN** preparing for production deployment
- **THEN** complete the following checklist:
  - **[ ] All tests passing** (`pnpm test` for all modules)
  - **[ ] Test coverage meets threshold** (≥60% for workers-api, backend)
  - **[ ] Linter passing** (no errors, warnings allowed only with justification)
  - **[ ] Type checking passing** (no TypeScript errors)
  - **[ ] Security audit passing** (`pnpm audit` with no critical/high vulnerabilities)
  - **[ ] E2E tests passing** (Deep Research SSE, user flows)
  - [ ] API keys rotated if needed
  - [ ] Environment variables configured
  - [ ] Database migrations applied (if any)
  - [ ] Rate limits configured appropriately
  - **[ ] Staging deployment successful** (smoke tests passed)
  - **[ ] Security middleware active** (backend size limiter, SQL injection protection)
  - **[ ] Telemetry privacy compliant** (no sensitive data stored)

**Bold items** are new requirements added by this change.

#### Scenario: Post-Deployment Verification
- **WHEN** production deployment completes
- **THEN** verify deployment health:
  - **[ ] Test health endpoint**: `curl https://web3search-api.marovole.workers.dev/api/v1/health`
  - [ ] Test chat endpoint with sample query
  - **[ ] Test SSE streaming**: Manually test Deep Research in browser
  - **[ ] Verify EventSource connection**: Check browser Network tab shows SSE
  - **[ ] Monitor error rates**: Check Cloudflare Analytics for 4xx/5xx spikes
  - **[ ] Verify telemetry**: Confirm no `responseBody` in Supabase telemetry table
  - [ ] Test from multiple geographic locations
  - [ ] Monitor latency and success rates
  - **[ ] Check security logs**: Verify middleware is blocking attacks

**Bold items** are new requirements added by this change.

#### Scenario: Rollback Criteria
- **WHEN** production deployment is completed
- **THEN** monitor for rollback triggers:
  - Error rate >5% (immediate rollback)
  - **SSE connection failure rate >10%** (new)
  - **Rate limit errors >20%** (may indicate configuration issue)
  - **Middleware blocking legitimate requests** (new)
  - Latency >3s for p95 (investigate, consider rollback)
  - User complaints about broken features

---

## Implementation Notes

**Test Infrastructure Dependencies**:
- `workers-api`: Vitest, @vitest/ui (for local coverage viewing)
- `backend`: pytest, pytest-cov, FastAPI TestClient
- `frontend`: Existing Jest/Vitest setup
- `E2E`: Playwright (already installed based on `.playwright-mcp/` directory)

**Coverage Threshold Rationale**:
- Starting at 60% for workers-api (pragmatic first step)
- Plan to increase to 70% in Q2, 80% in Q3
- Critical security code must have 100% coverage

**CI/CD Performance**:
- Parallel test execution to minimize pipeline time
- Cache dependencies between runs
- Skip E2E tests on draft PRs (run only on ready for review)

**Test Data Management**:
- Use test fixtures for consistent data
- Mock external services (OpenRouter, CoinGecko, Supabase)
- Seed test database with representative data
- Clean up test data after runs
