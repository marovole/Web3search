# API Specification

## Purpose
Define the API architecture, endpoints, and security mechanisms for the Web3search Cloudflare Workers backend. Focus on practical, production-ready features that are actually implemented.

定义 Web3search Cloudflare Workers 后端的 API 架构、端点和安全机制。专注于实际实现的、生产就绪的功能。

## Current Implementation Status

**Implemented Features** ✅:
- CORS middleware with origin whitelisting
- Rate limiting (KV-backed sliding window)
- Request logging and monitoring
- Error handling with structured responses
- CoinGecko price data integration
- OpenRouter AI integration with streaming
- Supabase database integration

**Planned for Future** 🔮:
- API key authentication
- JWT token-based user authentication
- Request signature verification
- Role-based access control (RBAC)

## Requirements

### Requirement: CORS Configuration
The system **SHALL** implement strict CORS policies to prevent unauthorized cross-origin requests.

#### Scenario: Origin Whitelist Validation
- **WHEN** a request arrives with an Origin header
- **THEN** the system must validate against the allowed origins list
- **AND** allowed origins include:
  - `https://web3search.pages.dev` (production)
  - `*.web3search.pages.dev` (preview deployments)
  - `http://localhost:*` (development only)
- **AND** requests from unauthorized origins must be rejected with 403
- **AND** preflight OPTIONS requests must be handled correctly

**Implementation**: `workers-api/src/middlewares/cors.ts`

#### Scenario: CORS Headers Configuration
- **WHEN** responding to allowed origin requests
- **THEN** must set `Access-Control-Allow-Origin` to the specific origin
- **AND** must set `Access-Control-Allow-Methods` to supported HTTP methods
- **AND** must set `Access-Control-Allow-Headers` for Content-Type and Authorization
- **AND** must set `Access-Control-Allow-Credentials: true`
- **AND** must set `Access-Control-Max-Age: 86400` (24 hours)

### Requirement: Rate Limiting
All API endpoints **SHALL** implement rate limiting to prevent abuse and ensure fair usage.

#### Scenario: KV-Backed Sliding Window
- **WHEN** a request is received
- **THEN** extract client identifier (IP address from `cf-connecting-ip` header)
- **AND** calculate current time window ID
- **AND** check request count in Cloudflare KV for this window
- **AND** if count >= limit, return 429 with Retry-After header
- **AND** if count < limit, increment counter and allow request
- **AND** add rate limit headers to response:
  - `X-RateLimit-Limit`: Maximum requests allowed
  - `X-RateLimit-Remaining`: Requests remaining in window

**Implementation**: `workers-api/src/middlewares/rate-limit.ts`

#### Scenario: Graceful Degradation
- **WHEN** KV storage is unavailable or fails
- **THEN** log warning and allow request to proceed
- **AND** do not block legitimate requests due to infrastructure issues
- **AND** rate limiting resumes when KV is restored

**Example Configuration**:
```typescript
createRateLimitMiddleware({
  scope: 'chat-ip-hour',
  limit: 10,
  windowSeconds: 3600,
})
```

### Requirement: Error Handling
The system **SHALL** provide consistent, secure error responses that don't leak sensitive information.

#### Scenario: Structured Error Response
- **WHEN** an error occurs during request processing
- **THEN** return JSON response with standardized error structure:
  ```json
  {
    "error": {
      "code": "ERROR_CODE",
      "message": "User-friendly message",
      "status": 400
    }
  }
  ```
- **AND** HTTP status code must match error.status
- **AND** error messages must be user-friendly, not technical
- **AND** sensitive information (stack traces, DB errors) must be logged only

**Implementation**: `workers-api/src/index.ts` (global error handler)

#### Scenario: Common Error Codes
- `INVALID_JSON`: Malformed JSON in request body (400)
- `MISSING_QUERY`: Required field missing (400)
- `QUERY_TOO_LONG`: Input exceeds maximum length (400)
- `RATE_LIMITED`: Too many requests (429)
- `NOT_FOUND`: Endpoint not found (404)
- `INTERNAL_ERROR`: Unhandled server error (500)
- `OPENROUTER_ERROR`: Upstream AI provider error (502)

### Requirement: Request Logging
All API requests **SHALL** be logged with relevant metadata for monitoring and debugging.

#### Scenario: Request Metadata Logging
- **WHEN** a request is received
- **THEN** log the following information:
  - HTTP method and path
  - Client IP address (`cf-connecting-ip`)
  - Request ID (generated UUID)
  - Timestamp
  - Response status code
  - Processing duration (ms)
- **AND** use structured logging format (JSON)
- **AND** log to console (visible in Cloudflare Workers logs)

**Implementation**: `workers-api/src/middlewares/logger.ts`

### Requirement: API Route Consistency
The system **SHALL** maintain consistent URL structure across all environments.

#### Scenario: URL Path Validation
- **WHEN** frontend builds API request URLs
- **THEN** no path duplication shall occur (e.g., `/api/api/v1`)
- **AND** production environment uses complete URL (`https://web3search-api.marovole.workers.dev/api/v1/...`)
- **AND** development environment uses relative paths (`/api/v1/...`) with proxy
- **AND** URL construction logic verified through unit tests

#### Scenario: Environment Configuration Testing
- **WHEN** application loads environment configuration
- **THEN** API_BASE_URL is correctly set based on runtime environment
- **AND** production detection checks `window.location.hostname`
- **AND** localhost/127.0.0.1 trigger development mode
- **AND** all other hostnames trigger production mode with full backend URL

**Rationale**: 修复生产环境API URL配置错误，确保前端正确构建API请求路径，避免路径重复（`/api/api/v1`）导致的404错误。

## API Endpoints

### Health Check
- **Endpoint**: `GET /api/v1/health`
- **Purpose**: Verify service status and dependencies
- **Authentication**: None required
- **Response**:
  ```json
  {
    "status": "healthy",
    "timestamp": "2025-01-10T12:00:00Z",
    "services": {
      "supabase": "healthy",
      "openrouter": "healthy",
      "kv_cache": "healthy"
    }
  }
  ```

### Quick Chat
- **Endpoint**: `POST /api/v1/chat/quick-chat`
- **Purpose**: AI-powered crypto question answering with real-time price data
- **Authentication**: None (rate-limited by IP)
- **Rate Limit**: 10 requests per hour per IP
- **Request Body**:
  ```json
  {
    "query": "What is the current price of Bitcoin?",
    "conversation_id": "uuid-optional",
    "model": "anthropic/claude-3.5-sonnet",
    "stream": true
  }
  ```
- **Response** (streaming):
  - Content-Type: `text/event-stream`
  - SSE format with `data:` events
  - Real-time CoinGecko price data injected into context

**Implementation**: `workers-api/src/routes/chat.ts`

### Search Autocomplete
- **Endpoint**: `GET /api/v1/search/autocomplete?q=bitcoin`
- **Purpose**: Cryptocurrency search suggestions
- **Authentication**: None
- **Rate Limit**: 30 requests per minute per IP

### Deep Research (Future)
- **Endpoint**: `POST /api/v1/deep-research`
- **Purpose**: Comprehensive crypto research reports
- **Status**: Planned for future implementation

## Security Considerations

### Transport Security
- All communication over HTTPS (enforced by Cloudflare)
- TLS 1.3 minimum version
- HSTS headers recommended for frontend

### Data Validation
- Input sanitization for all user-provided data
- Maximum query length: 10,000 characters
- JSON schema validation for request bodies

### Secrets Management
- API keys stored in Cloudflare Workers secrets
- Never expose in logs or error messages
- Environment variables encrypted at rest

## Future Enhancements

The following features are planned for future implementation:

1. **User Authentication**: JWT-based user accounts
2. **API Keys**: Developer API keys for third-party integrations
3. **Request Signing**: HMAC-SHA256 signature verification
4. **RBAC**: Role-based permission system
5. **Analytics**: Request metrics and usage tracking
6. **Caching**: Intelligent response caching with cache invalidation
