# Add Test Coverage for Reports and Trending Routes

## Why
Reports (`/api/v1/reports/generate`) and trending (`/api/v1/trending/hotspots`) routes are core delivery paths but currently lack regression test suites. This means regressions in streaming report generation, token calculation, or hotspot ranking can reach production without notice. Without automated tests, refactors and feature additions become risky.

当前报告生成和趋势分析路由缺少测试覆盖，这些是核心功能路径，回归问题可能直接影响生产环境。

## What Changes
- Add Vitest test suite for `/api/v1/reports/generate` covering:
  - Valid streaming flow with multiple sections
  - Invalid payloads (missing topic, invalid sections)
  - Token usage calculation accuracy
  - OpenRouter API failure handling
  - Supabase persistence behaviors
- Add Vitest test suite for `/api/v1/trending/hotspots` covering:
  - Keyword extraction and frequency counting
  - Cache hits/misses and force_refresh parameter
  - Supabase query failures
  - Category classification logic
- Integrate test suites into existing CI/CD pipeline
- Update test coverage tracking (from 188 to ~200+ tests)

## Impact
- **Affected specs**: `report-generation`, `analytics`
- **Affected code**:
  - `workers-api/src/routes/reports.ts` (367 lines, 0% test coverage)
  - `workers-api/src/routes/trending.ts` (136 lines, 0% test coverage)
  - New files: `workers-api/tests/routes/reports.test.ts`, `workers-api/tests/routes/trending.test.ts`
- **Benefits**:
  - Prevents regressions in report streaming and token calculation
  - Enables confident refactoring of report generation logic
  - Validates Supabase integration and error handling
  - Ensures trending hotspot algorithm stability
- **Risks**: None - pure additive change (no behavior modifications)
