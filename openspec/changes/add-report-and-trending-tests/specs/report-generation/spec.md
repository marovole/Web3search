# report-generation Spec Delta

## ADDED Requirements

### Requirement: Test Coverage for Streaming Report Generation
The report-generation capability **SHALL** be backed by comprehensive automated tests that exercise `/api/v1/reports/generate` endpoint to catch regressions in streaming, validation, token accounting, and database persistence.

#### Scenario: Valid streaming report generation
- **WHEN** the endpoint receives a well-formed request with topic and 3 sections
- **THEN** tests assert that the SSE stream emits events in correct order:
  - One `report_start` event with topic and section metadata
  - One `ReportStreamChunk` event per section (3 total) with `section_id`, `section_title`, `delta`, and `is_complete=true`
  - One `progress_update` event per section showing completion percentage
  - One `report_complete` event with `tokens_used`, `content`, and `generation_time_ms`
- **AND** verify stream closes with `event: done`

#### Scenario: Request validation failures
- **WHEN** requests have invalid payloads (missing topic, missing sections, sections without id/title)
- **THEN** tests verify appropriate error responses with correct status codes (400) and error structures
- **AND** verify error codes match documentation (INVALID_JSON, INVALID_REQUEST, INVALID_SECTION)

#### Scenario: Token usage calculation accuracy
- **WHEN** OpenRouter returns usage data in responses
- **THEN** tests mock OpenRouter responses with known token counts
- **AND** verify `normalizeOpenRouterUsage()` correctly extracts prompt_tokens, completion_tokens, total_tokens
- **AND** verify token accumulation across multiple sections is accurate
- **AND** verify `tokens_used` field in `report_complete` event matches accumulated total
- **AND** verify Supabase metadata.tokens_used matches when `save_to_database=true`

#### Scenario: OpenRouter failure handling
- **WHEN** OpenRouter API fails (network error, 500 response, timeout)
- **THEN** tests verify `section_error` event is emitted with error message
- **AND** verify report generation continues with remaining sections
- **AND** verify error is logged appropriately

#### Scenario: Supabase persistence behaviors
- **WHEN** `save_to_database=true` in request body
- **THEN** tests verify Supabase `insert` is called with correct structure:
  - topic, sections, content, metadata (model, tokens_used, generation_time_ms)
- **AND** verify `report_id` is returned in `report_complete` event
- **WHEN** `save_to_database=false` or omitted
- **THEN** tests verify no Supabase insert occurs and `report_id` is null
- **WHEN** Supabase save fails
- **THEN** tests verify error is logged but report generation completes

## ADDED Requirements

### Requirement: Mocking Infrastructure for Report Tests
The test suite **SHALL** provide reusable mock implementations for OpenRouter and Supabase to enable deterministic testing of report generation flows.

#### Scenario: OpenRouter mock responses
- **WHEN** tests need to simulate OpenRouter API calls
- **THEN** provide mock functions that return configurable responses with:
  - Success: valid message content with usage data
  - Failure: network errors, HTTP 500 responses
  - Timeout: delayed responses for timeout testing
- **AND** mock responses must match OpenRouter API response structure

#### Scenario: Supabase mock database
- **WHEN** tests need to simulate Supabase operations
- **THEN** provide mock client with verifiable `insert`, `select`, `update` methods
- **AND** allow inspection of arguments passed to mocked methods
- **AND** simulate both success and failure scenarios

#### Scenario: Test helper reusability
- **WHEN** writing multiple report tests
- **THEN** extract common setup logic (mock creation, request builders) into shared helpers
- **AND** ensure helpers are maintainable and well-documented
