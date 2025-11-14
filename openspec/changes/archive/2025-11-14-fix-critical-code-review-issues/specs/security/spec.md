# Security Specification Deltas

## ADDED Requirements

### Requirement: Telemetry Data Privacy
The system **SHALL** collect only non-sensitive metadata in telemetry to prevent privacy breaches and comply with data protection regulations.

#### Scenario: API Response Storage Restrictions
- **WHEN** tracking API calls for monitoring and billing purposes
- **THEN** the system must NOT store full API response bodies
- **AND** must NOT store user prompts or model-generated content
- **AND** must NOT store any personally identifiable information (PII)
- **AND** may only store aggregated metadata:
  - Response body length (bytes)
  - Content type
  - Token counts (prompt tokens, completion tokens)
  - Status codes and finish reasons
  - Error flags (hasError boolean)
- **AND** any logs containing sensitive data must have short TTL (<7 days)

**Implementation**: `workers-api/src/lib/telemetry.ts:181`

**Rationale**: Storing full response bodies creates severe privacy risks:
- User queries may contain sensitive personal or financial information
- Model outputs may inadvertently include PII from training data
- Database breaches would expose complete conversation history
- GDPR/CCPA compliance requires data minimization
- Service-role Supabase key compromise would leak all telemetry data

#### Scenario: Historical Data Cleanup
- **WHEN** implementing telemetry privacy changes
- **THEN** evaluate need for historical data cleanup
- **AND** if required by legal/compliance team, null out existing `responseBody` values
- **AND** document data retention policy
- **AND** implement automated data expiration (e.g., 30-day TTL for detailed telemetry)
- **AND** preserve aggregated metrics for business intelligence

#### Scenario: Debugging Without Sensitive Data
- **WHEN** developers need to debug API integration issues
- **THEN** use structured logging at DEBUG level (not persisted long-term)
- **AND** implement request sampling (1% of requests log full bodies to separate audit table)
- **AND** audit table must have strict access controls (ops team only)
- **AND** audit table must have automatic 7-day expiration
- **AND** production logs must never contain full response bodies

**Migration**: Existing telemetry data may need cleanup. Coordinate with legal team to determine GDPR Right to Erasure obligations.

---

### Requirement: Backend Security Middleware Activation
The system **SHALL** activate all implemented security middleware to protect the backend API from common attacks.

#### Scenario: Request Size Limiting
- **WHEN** the backend API receives an HTTP request
- **THEN** the request size limiter middleware must be active
- **AND** must reject requests exceeding 10MB payload size
- **AND** must return HTTP 413 Payload Too Large
- **AND** must include error message: "Request body exceeds maximum size limit"
- **AND** must log oversized request attempts for security monitoring
- **AND** must apply to all endpoints (no exceptions)

**Implementation**: `backend/app/middleware/request_size_limiter.py` must be registered via `app.add_middleware(RequestSizeLimiterMiddleware)`

**Rationale**: Large payloads can cause:
- Denial of Service (DoS) through resource exhaustion
- Memory overflow attacks
- Slow HTTP attacks (slowloris)
- Database overload from massive inserts

#### Scenario: SQL Injection Protection
- **WHEN** the backend API processes requests with user input
- **THEN** SQL injection protection middleware must be active
- **AND** must scan request bodies and query parameters for SQL injection patterns
- **AND** must block requests containing suspicious patterns:
  - `UNION SELECT`
  - `'; DROP TABLE`
  - `OR 1=1`
  - `<script>`, `javascript:`, `onerror=`
  - Other common injection vectors
- **AND** must return HTTP 400 Bad Request for blocked requests
- **AND** must log attempted injection attacks
- **AND** must not leak detection logic in error messages (use generic "Invalid input")

**Implementation**: `backend/app/middleware/sql_injection_protection.py` must be registered via `app.add_middleware(SQLInjectionProtectionMiddleware)`

**Rationale**: Even with parameterized queries, defense in depth requires input validation to catch:
- ORM bypasses
- Raw SQL queries (if any)
- XSS attempts in stored data
- NoSQL injection variants

#### Scenario: Middleware Initialization and Order
- **WHEN** the FastAPI application starts
- **THEN** security middleware must be registered in the correct order:
  1. Request size limiter (outermost - reject oversized requests first)
  2. SQL injection protection (validate input before processing)
  3. CORS middleware (handle cross-origin policies)
  4. Rate limiting (if implemented at backend layer)
  5. Authentication/authorization (innermost - check user identity)
- **AND** middleware initialization must be verified on application startup
- **AND** application health check must confirm middleware is active

**Implementation**: Create or update `backend/app/main.py`:
```python
from fastapi import FastAPI
from app.middleware.request_size_limiter import RequestSizeLimiterMiddleware
from app.middleware.sql_injection_protection import SQLInjectionProtectionMiddleware

app = FastAPI()

# Security middleware (order matters!)
app.add_middleware(RequestSizeLimiterMiddleware)
app.add_middleware(SQLInjectionProtectionMiddleware)

# ... other middleware and routes
```

#### Scenario: Middleware Testing Requirements
- **WHEN** security middleware is deployed
- **THEN** unit tests must verify each middleware in isolation
- **AND** integration tests must verify middleware stack behavior
- **AND** tests must cover:
  - Legitimate requests pass through
  - Malicious requests are blocked
  - Proper error codes and messages returned
  - Logging captures security events
- **AND** CI/CD pipeline must run security tests on every commit

#### Scenario: Middleware Configuration Management
- **WHEN** configuring security middleware
- **THEN** limits and rules must be configurable via environment variables
- **AND** configuration changes must not require code deployment
- **AND** default values must be secure (deny-by-default)
- **AND** configuration must be validated on startup
- **AND** invalid configuration must prevent application start

**Example Configuration**:
```python
# .env or environment variables
MAX_REQUEST_SIZE_MB=10
SQL_INJECTION_STRICT_MODE=true
SQL_INJECTION_LOG_LEVEL=warning
```

---

### Requirement: Security Middleware Monitoring
The system **SHALL** monitor security middleware effectiveness and attack patterns.

#### Scenario: Attack Detection and Logging
- **WHEN** security middleware blocks a request
- **THEN** log detailed security event including:
  - Timestamp
  - Client IP address
  - Attack type (oversized request, SQL injection, etc.)
  - Blocked payload (truncated, no PII)
  - Endpoint targeted
  - HTTP headers (User-Agent, Referer)
- **AND** security logs must be separate from application logs
- **AND** security logs must be retained for minimum 90 days
- **AND** security logs must be immutable (append-only)

#### Scenario: Security Metrics Collection
- **WHEN** system is operational
- **THEN** collect security metrics:
  - Number of requests blocked per hour/day
  - Attack types distribution
  - Top attacking IP addresses
  - Most targeted endpoints
- **AND** metrics must feed into security dashboard
- **AND** unusual patterns must trigger alerts
- **AND** metrics must be accessible to security team

#### Scenario: Incident Response Integration
- **WHEN** middleware detects coordinated attack (multiple attempts from same IP)
- **THEN** automatically escalate to incident response system
- **AND** consider temporary IP blocking (if infrastructure supports)
- **AND** notify security team via configured channels
- **AND** provide evidence for forensic analysis

---

## MODIFIED Requirements

### Requirement: 敏感数据保护
The system **SHALL** protect sensitive information through encryption, access control, and data minimization practices.

#### Scenario: 敏感数据处理
- **WHEN** 处理敏感信息
- **THEN** 对敏感数据进行加密存储
- **AND** 在传输中使用端到端加密
- **AND** 实施数据脱敏和掩码
- **AND** 限制敏感数据访问权限
- **AND** Telemetry and logs must not contain sensitive data (user prompts, API responses, PII)
- **AND** Implement data minimization - only collect what is strictly necessary
- **AND** Document data retention policies and enforce automatic expiration

#### Scenario: Telemetry Data Minimization
- **WHEN** collecting operational telemetry
- **THEN** store only metadata necessary for monitoring and billing
- **AND** exclude full request/response bodies
- **AND** anonymize or pseudonymize user identifiers where possible
- **AND** implement automatic data expiration (30-day default)
- **AND** provide users with data export and deletion options (GDPR compliance)

**Rationale**: Extends existing sensitive data protection requirement to explicitly cover telemetry, addressing critical privacy vulnerability discovered in code review.
