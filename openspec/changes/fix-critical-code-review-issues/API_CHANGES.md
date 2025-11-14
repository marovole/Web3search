# API Changes: Deep Research SSE Endpoint

## Summary

The Deep Research streaming endpoint has been refactored from POST to GET to enable compatibility with the browser's EventSource API.

## Breaking Change

### Before (Non-functional)
```
POST /api/v1/chat/deep-research/stream
Content-Type: application/json

{
  "query": "What is Bitcoin?",
  "conversation_id": "optional-uuid",
  "model": "optional-model-id"
}
```

**Issue**: EventSource only supports GET requests, making this endpoint unreachable from browsers.

### After (Fixed)
```
GET /api/v1/chat/deep-research/stream?query=What%20is%20Bitcoin%3F&conversation_id=optional-uuid&model=optional-model-id
```

## Request Parameters

| Parameter | Type | Required | Max Length | Description |
|-----------|------|----------|------------|-------------|
| `query` | string | Yes | 2000 chars | Research question or topic |
| `conversation_id` | string | No | - | Existing conversation UUID to continue |
| `model` | string | No | - | Model ID to use (defaults to deep-research primary model) |

## Response Format

### Success (200 OK)
```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive

data: {"type":"progress","stage":"data_collection","content":"正在准备研究计划..."}

data: {"type":"progress","stage":"analysis","content":"正在分析数据源..."}

data: {"type":"content","section":"answer","content":"Bitcoin is a decentralized..."}

data: {"type":"complete","content":"Research completed successfully","session_id":"conv-uuid"}

event: done
data: {"status":"completed"}
```

### Error Responses

#### Missing Query (400)
```json
{
  "error": {
    "code": "MISSING_QUERY",
    "message": "Query parameter \"query\" is required",
    "status": 400
  }
}
```

#### Query Too Long (414)
```json
{
  "error": {
    "code": "URI_TOO_LONG",
    "message": "Query exceeds maximum length of 2000 characters",
    "status": 414
  }
}
```

#### Invalid Model (400)
```json
{
  "error": {
    "code": "INVALID_MODEL",
    "message": "Model \"invalid-model\" not found",
    "status": 400
  }
}
```

#### Rate Limit Exceeded (429)
```json
{
  "error": {
    "code": "RATE_LIMITED",
    "message": "Too many requests. Please retry later.",
    "status": 429
  }
}
```

**Rate Limit**: 5 requests per 24 hours per IP address

## SSE Event Types

| Event Type | Description | Fields |
|------------|-------------|--------|
| `progress` | Research pipeline progress update | `type`, `stage`, `content` |
| `content` | Research result content sections | `type`, `section`, `content` |
| `complete` | Research finished successfully | `type`, `content`, `session_id` |
| `error` | Error occurred during research | `type`, `content` |
| `done` | Stream termination marker | `status` |

## Client Implementation

### JavaScript (EventSource)
```javascript
const query = encodeURIComponent("What is Bitcoin?")
const url = `${API_BASE}/api/v1/chat/deep-research/stream?query=${query}`

const eventSource = new EventSource(url)

eventSource.addEventListener('message', (event) => {
  const data = JSON.parse(event.data)

  switch (data.type) {
    case 'progress':
      console.log(`[${data.stage}] ${data.content}`)
      break
    case 'content':
      console.log(`[${data.section}]`, data.content)
      break
    case 'complete':
      console.log('Research complete:', data.session_id)
      eventSource.close()
      break
    case 'error':
      console.error('Research error:', data.content)
      eventSource.close()
      break
  }
})

eventSource.addEventListener('error', (error) => {
  console.error('SSE connection error:', error)
  eventSource.close()
})
```

### Python (sseclient)
```python
import sseclient
import requests
import json
from urllib.parse import urlencode

params = urlencode({'query': 'What is Bitcoin?'})
url = f'{API_BASE}/api/v1/chat/deep-research/stream?{params}'

response = requests.get(url, stream=True, headers={'Accept': 'text/event-stream'})
client = sseclient.SSEClient(response)

for event in client.events():
    if event.data:
        data = json.loads(event.data)
        print(f"[{data.get('type')}] {data.get('content', '')}")

        if data.get('type') == 'complete':
            break
```

## Migration Guide

### Frontend Changes Required

**Before**:
```typescript
const response = await fetch('/api/v1/chat/deep-research/stream', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query: 'What is Bitcoin?' })
})
```

**After**:
```typescript
const params = new URLSearchParams({ query: 'What is Bitcoin?' })
const url = `/api/v1/chat/deep-research/stream?${params}`
const eventSource = new EventSource(url)
```

### Query Length Validation

**Frontend Validation** (recommended):
```javascript
const MAX_QUERY_LENGTH = 2000

function validateQuery(query) {
  if (!query || query.trim().length === 0) {
    throw new Error('Query is required')
  }
  if (query.length > MAX_QUERY_LENGTH) {
    throw new Error(`Query exceeds ${MAX_QUERY_LENGTH} characters`)
  }
  return query.trim()
}
```

## Deployment Notes

- **Breaking Change**: Frontend and backend must be deployed simultaneously
- **Backward Compatibility**: Other (non-SSE) endpoints remain unchanged
- **URL Encoding**: Ensure all query parameters are properly URL-encoded
- **Connection Timeout**: Cloudflare Workers has a 15-second idle timeout (handled by server-side keep-alive heartbeats)

## Security Considerations

- **Input Validation**: Query length strictly enforced at 2000 characters
- **Rate Limiting**: 5 requests per IP per 24 hours
- **SQL Injection**: All queries are parameterized (no SQL injection risk)
- **XSS Prevention**: SSE responses are JSON-encoded (no script injection risk)

## Testing Checklist

- [x] Query parameter validation (missing, empty, too long)
- [x] SSE content-type header set correctly
- [x] EventSource connection successful
- [x] Progress events received in order
- [x] Rate limiting enforced
- [x] Error responses formatted correctly
- [ ] Long-running research completes successfully
- [ ] Connection resilience (auto-reconnect on disconnect)

---

**Last Updated**: 2025-11-14
**Change Proposal**: `fix-critical-code-review-issues`
**Status**: Implemented
