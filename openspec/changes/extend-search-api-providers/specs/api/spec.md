# API Spec Delta

## ADDED Requirements

### Requirement: Multi-Provider Search Aggregation
The API capability **SHALL** orchestrate multiple search providers (Brave, Tavily, Serper) to ensure search functionality remains available even when individual providers fail, and to improve search result quality through diversity.

#### Scenario: Tavily Search API integration
- **WHEN** Tavily API key is configured in environment
- **THEN** system can fetch search results from Tavily API (https://api.tavily.com/search)
- **AND** responses are normalized to `NormalizedSearchResult` format with:
  - `id`: `tavily-${query}-${index}`
  - `provider`: `'tavily'`
  - `title`, `snippet`, `url` from Tavily response
  - `relevance_score`: normalized from Tavily's scoring (0-1 range)
  - `accessed_at`: current ISO 8601 timestamp
- **AND** results are cached in KV with 5-minute TTL
- **AND** missing API key logs warning and returns empty array (non-fatal)

#### Scenario: Serper Search API integration
- **WHEN** Serper API key is configured in environment
- **THEN** system can fetch search results from Serper API (https://google.serper.dev/search)
- **AND** responses are normalized to `NormalizedSearchResult` format with:
  - `id`: `serper-${query}-${index}`
  - `provider`: `'serper'`
  - `title`, `snippet`, `url` from Serper organic results
  - `relevance_score`: position-based scoring (1 - index * 0.05, min 0.5)
  - `accessed_at`: current ISO 8601 timestamp
- **AND** results are cached in KV with 5-minute TTL
- **AND** missing API key logs warning and returns empty array (non-fatal)

#### Scenario: Provider failover and resilience
- **WHEN** multiple search providers are configured
- **THEN** system attempts providers in priority order: Brave → Tavily → Serper
- **AND** failover is triggered by:
  - Network errors (ECONNRESET, ETIMEDOUT, ECONNREFUSED)
  - HTTP server errors (500, 502, 503, 504)
  - Rate limit errors (429)
  - Timeouts (> 5 seconds per provider)
  - Empty result arrays
- **AND** system returns results from first successful provider
- **WHEN** all providers fail
- **THEN** system returns empty array and logs comprehensive error details
- **AND** does not throw exception (graceful degradation)

#### Scenario: Provider selection telemetry
- **WHEN** search query is executed
- **THEN** system logs which provider successfully answered the query
- **AND** logs provider latency (request initiation to first byte, total request time)
- **AND** logs error details for failed provider attempts
- **AND** telemetry includes:
  - Query text (truncated for privacy)
  - Selected provider name
  - Latency in milliseconds
  - HTTP status code
  - Error type (if failed)
  - Result count
- **AND** telemetry is structured for easy querying and analysis

#### Scenario: Cache key isolation by provider
- **WHEN** caching search results
- **THEN** cache keys include provider name: `search:${provider}:${query.toLowerCase()}`
- **AND** different providers can have different cached results for same query
- **AND** cache hits return provider-specific results without API calls
- **AND** cache expiration is independent per provider (5 minutes each)

## ADDED Requirements

### Requirement: Search Provider Test Coverage
The search aggregation system **SHALL** have comprehensive test coverage for all providers and failover logic to prevent regressions.

#### Scenario: Tavily provider tests
- **WHEN** testing Tavily integration
- **THEN** tests verify:
  - Successful API call with valid key returns normalized results
  - Missing API key returns empty array with warning
  - Network errors are handled gracefully
  - Rate limit (429) triggers failover
  - Result normalization is accurate (schema, scoring, metadata)
  - Caching works correctly

#### Scenario: Serper provider tests
- **WHEN** testing Serper integration
- **THEN** tests verify same categories as Tavily (successful call, missing key, errors, rate limits, normalization, caching)

#### Scenario: Failover logic tests
- **WHEN** testing provider failover
- **THEN** tests verify:
  - Brave succeeds → returns Brave results, no other providers called
  - Brave fails (network error) → Tavily called and succeeds
  - Brave and Tavily fail → Serper called and succeeds
  - All providers fail → returns empty array, no exception thrown
- **AND** verify telemetry logs all provider attempts
- **AND** verify failover respects timeout limits

#### Scenario: Integration with Deep Research
- **WHEN** Deep Research calls `searchSources(queries, env)`
- **THEN** tests verify failover works end-to-end
- **AND** verify correct provider is selected based on availability
- **AND** verify results are properly formatted for downstream analysis

## MODIFIED Requirements

### Requirement: Search result deduplication
The search aggregation system SHALL deduplicate results by URL **within a single provider's results**, keeping the highest relevance score when duplicates exist.

**Previous behavior**: Deduplication occurred across all providers.

**New behavior**: Since we now use provider failover (not parallel aggregation), deduplication only applies within a single provider's result set. This simplifies logic and respects provider-specific ranking.

#### Scenario: Single-provider deduplication
- **WHEN** a provider returns multiple results with the same URL
- **THEN** system keeps only the result with highest `relevance_score`
- **AND** removes duplicate URLs within that provider's results
- **WHEN** using failover (one provider per query)
- **THEN** cross-provider deduplication is not needed (only one provider succeeds)

#### Scenario: Result sorting maintains provider ranking
- **WHEN** results are returned from any provider
- **THEN** results are sorted by `relevance_score` descending
- **AND** sorting preserves provider's ranking signals
- **AND** deduplication happens before final sorting
