# analytics Spec Delta

## ADDED Requirements

### Requirement: Test Coverage for Trending Hotspots Endpoint
The analytics capability **SHALL** include comprehensive test coverage for `/api/v1/trending/hotspots` endpoint to ensure keyword extraction, frequency counting, caching, and error handling remain stable across changes.

#### Scenario: Trending response structure and accuracy
- **WHEN** Supabase returns recent messages with known keyword occurrences
- **THEN** tests verify keyword extraction from message content (case-insensitive)
- **AND** verify frequency counting is accurate across all messages
- **AND** verify results are sorted by count in descending order
- **AND** verify limit parameter correctly restricts result count
- **AND** verify response structure matches specification:
  ```json
  {
    "hotspots": [
      {"id": 1, "keyword": "bitcoin", "count": 42, "trend": "up", "category": "Layer 1"}
    ],
    "count": 10,
    "updated_at": "ISO8601 timestamp"
  }
  ```

#### Scenario: Keyword category classification
- **WHEN** keywords are extracted from messages
- **THEN** tests verify `getCategoryForKeyword()` correctly classifies each keyword:
  - Layer 1: bitcoin, btc, ethereum, eth, solana, sol, cardano, ada, avalanche, avax, polkadot, dot
  - DeFi: defi, uniswap, uni, yield, liquidity, staking, dex
  - Infrastructure: chainlink, link, polygon, matic, smart contract
  - Trends: nft, dao, web3, metaverse, cefi
- **AND** verify "Other" category is assigned to unrecognized keywords
- **AND** verify category assignment is case-insensitive

#### Scenario: Cache behavior and TTL
- **WHEN** first request for hotspots with limit=10
- **THEN** tests verify Supabase query is executed
- **AND** verify result is stored in KV cache with key `trending:hotspots:10`
- **AND** verify cache TTL is set to 900 seconds (15 minutes)
- **WHEN** second request with same limit and no force_refresh
- **THEN** tests verify cached data is returned without Supabase query
- **WHEN** request includes `force_refresh=true`
- **THEN** tests verify cache is bypassed and fresh data is fetched

#### Scenario: Parameter handling
- **WHEN** no limit parameter is provided
- **THEN** tests verify default limit of 10 is used
- **WHEN** custom limit is provided (e.g., 5, 20)
- **THEN** tests verify correct number of hotspots returned
- **AND** verify cache keys are unique per limit value

#### Scenario: Error handling and edge cases
- **WHEN** Supabase query fails with database error
- **THEN** tests verify 500 response with error code DATABASE_ERROR
- **AND** verify error message is user-friendly
- **WHEN** Supabase returns empty message list
- **THEN** tests verify response contains empty hotspots array
- **AND** verify status code is 200 (not an error condition)
- **WHEN** KV cache contains malformed JSON
- **THEN** tests verify cache is skipped and fresh data is fetched
- **AND** verify no error is thrown

## ADDED Requirements

### Requirement: Mocking Infrastructure for Trending Tests
The test suite **SHALL** provide reusable mock implementations for Supabase and KV cache to enable deterministic testing of trending hotspot flows.

#### Scenario: Supabase message mocking
- **WHEN** tests need to simulate Supabase message queries
- **THEN** provide mock function that returns configurable message arrays with content field
- **AND** support both success scenarios (with messages) and failure scenarios (database errors)
- **AND** allow inspection of query parameters (table, select, order, limit)

#### Scenario: KV cache mocking
- **WHEN** tests need to simulate caching behavior
- **THEN** provide in-memory KV implementation with get/put/delete methods
- **AND** support cache hits (return stored data) and misses (return null)
- **AND** support TTL verification for expiration testing
- **AND** allow injection of malformed data for error path testing

#### Scenario: Test data fixtures
- **WHEN** tests need sample message data
- **THEN** provide fixture with realistic crypto-related message content
- **AND** ensure fixture covers all keyword categories for classification testing
- **AND** make fixture easily customizable for different test scenarios
