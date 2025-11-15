# Extend Search API with Tavily and Serper Providers

## Why
The search aggregation layer currently depends solely on Brave Search API (`workers-api/src/lib/search-providers.ts:46-94`). This creates a single point of failure: if Brave rate-limits, returns errors, or has downtime, all search functionality becomes unavailable. Adding Tavily and Serper providers improves resilience through failover and increases search quality through result diversity.

当前搜索功能仅依赖Brave Search API，存在单点故障风险。添加Tavily和Serper提供者可以提升可靠性和搜索结果多样性。

## What Changes
- Implement Tavily Search API integration in `search-providers.ts`:
  - API endpoint: `https://api.tavily.com/search`
  - Result normalization to `NormalizedSearchResult` format
  - Rate limit and error handling
- Implement Serper Search API integration in `search-providers.ts`:
  - API endpoint: `https://google.serper.dev/search`
  - Result normalization to `NormalizedSearchResult` format
  - Rate limit and error handling
- Enhance `fetchSearchResultsForQueries()` to support provider priority and failover:
  - Try Brave first (fastest, already integrated)
  - Fallback to Tavily on Brave failure
  - Fallback to Serper on Tavily failure
- Add telemetry for provider usage tracking (which provider answered, latency, errors)
- Update environment types to include `TAVILY_API_KEY` and `SERPER_API_KEY` (already done in `src/types/env.ts:20-21`)
- Add comprehensive tests for new providers and failover logic

## Impact
- **Affected specs**: `api`
- **Affected code**:
  - `workers-api/src/lib/search-providers.ts:132-138` (TODO comments to be replaced with implementations)
  - `workers-api/src/routes/deep-research.ts` (uses `searchSources()`)
  - `workers-api/tests/routes/chat.test.ts` (mock needs updating for new providers)
  - New tests: `workers-api/tests/lib/search-providers.test.ts`
- **Benefits**:
  - **Resilience**: Search remains available if one provider fails
  - **Quality**: Diverse results from multiple sources
  - **Performance**: Can optimize by using fastest provider per region
  - **Cost**: Can distribute load across free tiers of multiple providers
- **Risks**:
  - API key management complexity (3 providers to configure)
  - Slight latency increase if failover occurs (mitigated by caching)
  - API cost if free tiers are exceeded (can be monitored via telemetry)
