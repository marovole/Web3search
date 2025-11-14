# API Specification Deltas

## MODIFIED Requirements

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
- `URI_TOO_LONG`: Query string exceeds 2000 characters (414)
- `RATE_LIMITED`: Too many requests (429)
- `NOT_FOUND`: Endpoint not found (404)
- `INTERNAL_ERROR`: Unhandled server error (500)
- `OPENROUTER_ERROR`: Upstream AI provider error (502)

---

## ADDED Requirements

### Requirement: Deep Research SSE Streaming
The system **SHALL** provide a Server-Sent Events (SSE) streaming endpoint for Deep Research to deliver real-time progress updates.

#### Scenario: SSE Endpoint Contract
- **GIVEN** the Deep Research SSE endpoint is at `GET /api/v1/chat/deep-research/stream`
- **WHEN** a client initiates an EventSource connection with query parameters
- **THEN** the endpoint must accept GET requests (EventSource only supports GET)
- **AND** query parameters must include:
  - `query` (required, string, max 2000 chars): The research query
  - `conversation_id` (optional, string, UUID): Existing conversation to continue
- **AND** the response must use content-type `text/event-stream`
- **AND** SSE events must follow standard format:
  ```
  event: message
  data: {"type": "progress", "stage": "searching", "content": "..."}

  event: message
  data: {"type": "result", "content": "Final report..."}
  ```

**Implementation**: `workers-api/src/routes/chat.ts:215`

#### Scenario: Query Length Validation
- **WHEN** a request is received with a `query` parameter
- **THEN** the system must validate query length
- **AND** if query length exceeds 2000 characters, return HTTP 414 URI Too Long
- **AND** response must include error message:
  ```json
  {
    "error": {
      "code": "URI_TOO_LONG",
      "message": "Query exceeds maximum length of 2000 characters",
      "status": 414
    }
  }
  ```
- **AND** client should be instructed to shorten the query

**Rationale**: EventSource uses GET requests, which have practical URL length limits imposed by browsers and proxies (typically 2048 chars). Limiting to 2000 chars provides a safe buffer.

#### Scenario: Rate Limiting for SSE
- **WHEN** a client attempts to open an SSE connection
- **THEN** rate limiting must be enforced before opening the stream
- **AND** rate limit scope: `deep-research-ip-day`
- **AND** rate limit: 5 requests per 24 hours per IP address
- **AND** if rate limit exceeded, return HTTP 429 Too Many Requests
- **AND** include `Retry-After` header with seconds until window reset
- **AND** close connection immediately (do not open SSE stream)

**Implementation**: `createRateLimitMiddleware()` in `chat.ts:217`

#### Scenario: EventSource Connection Lifecycle
- **WHEN** an SSE stream is opened successfully
- **THEN** the connection must remain open until research completes
- **AND** send periodic heartbeat events (every 30s) to prevent timeouts
- **AND** handle client disconnect gracefully (stop processing)
- **AND** close stream with event type `done` when research completes
- **AND** close stream with event type `error` if processing fails

#### Scenario: URL Encoding and Special Characters
- **WHEN** query parameters contain special characters
- **THEN** the client must properly URL-encode parameters
- **AND** the server must decode parameters correctly
- **AND** support UTF-8 characters in queries
- **AND** handle spaces, quotes, and punctuation safely

**Breaking Change**: This replaces the previous (non-functional) `POST /api/v1/chat/deep-research/stream` endpoint. The POST version was never reachable from EventSource clients and is being removed.

---

### Requirement: SSE Client Implementation
Frontend clients **SHALL** use the EventSource API to connect to SSE streaming endpoints.

#### Scenario: EventSource Construction
- **WHEN** the frontend initiates a Deep Research request
- **THEN** construct URL with properly encoded query parameters:
  ```typescript
  const queryParams = new URLSearchParams({
    query: request.query,
    ...(request.conversation_id && { conversation_id: request.conversation_id }),
  })
  const url = `${API_BASE_URL}/api/v1/chat/deep-research/stream?${queryParams}`
  const eventSource = new EventSource(url)
  ```
- **AND** validate query length before sending (max 2000 chars)
- **AND** show error if query too long

**Implementation**: `frontend/src/services/api.ts:107`

#### Scenario: EventSource Event Handling
- **WHEN** SSE events are received
- **THEN** listen for `message` events
- **AND** parse event data as JSON
- **AND** handle different event types:
  - `progress`: Update UI with current stage
  - `result`: Display final research report
  - `error`: Show error message and close stream
  - `done`: Close connection gracefully
- **AND** handle connection errors with retry logic
- **AND** close EventSource when component unmounts

#### Scenario: Query Length Validation
- **WHEN** user submits a research query
- **THEN** validate query length on client side
- **AND** if length > 2000 chars, show error message:
  "Query is too long. Please shorten to 2000 characters or less."
- **AND** prevent form submission
- **AND** show character count indicator in UI

---

## REMOVED Requirements

### Requirement: Deep Research (Future)
**Reason**: This placeholder requirement has been replaced by the fully specified "Deep Research SSE Streaming" requirement above. The feature is no longer "future" - it is being implemented as part of this change.

**Migration**: Existing `POST /api/v1/deep-research` endpoint (if any) should be removed. All clients must use the new GET-based SSE streaming endpoint.
