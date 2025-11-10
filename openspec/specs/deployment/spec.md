# Deployment Specification

## Purpose
Define the deployment architecture and processes for Web3search on Cloudflare's edge platform. Document automated deployment workflows, environment configuration, and production best practices.

定义 Web3search 在 Cloudflare 边缘平台上的部署架构和流程。记录自动化部署工作流、环境配置和生产最佳实践。

## Architecture Overview

### Current Stack
- **Frontend**: Cloudflare Pages (React + Vite)
- **Backend**: Cloudflare Workers (TypeScript)
- **Database**: Supabase PostgreSQL (hosted)
- **Cache**: Cloudflare KV (edge storage)
- **AI**: OpenRouter API
- **Price Data**: CoinGecko API

### Key Benefits
- 🌍 Global edge distribution (300+ locations)
- ⚡ Sub-50ms latency worldwide
- 📈 Automatic scaling (0-∞ requests)
- 💰 Zero cost (free tier sufficient)
- 🔐 Built-in DDoS protection
- 🚀 Git-based automatic deployments

## Requirements

### Requirement: Cloudflare Pages Frontend Deployment
The frontend **SHALL** be deployed to Cloudflare Pages with automatic deployments from Git.

#### Scenario: Automatic Production Deployment
- **WHEN** code is pushed to `main` branch
- **THEN** Cloudflare Pages automatically triggers build
- **AND** executes `npm run build` to build React app
- **AND** build completes in < 3 minutes
- **AND** deploys to production URL: `https://web3search.pages.dev`
- **AND** deployment is atomic (no partial updates)
- **AND** build logs visible in Cloudflare dashboard

**Implementation**: GitHub integration in Cloudflare Pages dashboard

#### Scenario: Preview Deployment for Pull Requests
- **WHEN** a Pull Request is created or updated
- **THEN** Cloudflare Pages creates preview deployment
- **AND** preview URL format: `https://[commit-hash].web3search.pages.dev`
- **AND** preview URL posted as PR comment
- **AND** each commit triggers new preview build
- **AND** preview deleted when PR is closed/merged

#### Scenario: Environment Variables Configuration
- **WHEN** building frontend on Cloudflare Pages
- **THEN** load environment variables from dashboard
- **AND** production variables:
  - `VITE_API_BASE_URL`: `https://web3search-api.marovole.workers.dev`
  - `VITE_ENVIRONMENT`: `production`
  - `VITE_ENABLE_SENTRY`: `true`
- **AND** preview variables can override production (e.g., staging API)
- **AND** secrets are encrypted at rest
- **AND** build-time variables prefixed with `VITE_`

#### Scenario: Deployment Rollback
- **WHEN** new deployment causes critical issues
- **THEN** navigate to Cloudflare Pages dashboard
- **AND** select previous successful deployment
- **AND** click "Rollback to this deployment"
- **AND** rollback completes in < 1 minute
- **AND** traffic automatically routed to previous version
- **AND** rollback event logged in deployment history

### Requirement: Cloudflare Workers Backend Deployment
The backend API **SHALL** be deployed to Cloudflare Workers using Wrangler CLI.

#### Scenario: Manual Production Deployment
- **WHEN** developer runs `npm run deploy` in `workers-api/` directory
- **THEN** Wrangler CLI bundles TypeScript code
- **AND** uploads Worker to Cloudflare edge network
- **AND** deployment completes in < 30 seconds
- **AND** new version available at: `https://web3search-api.marovole.workers.dev`
- **AND** zero-downtime deployment (traffic switches atomically)
- **AND** previous version retained for quick rollback

**Implementation**: `workers-api/wrangler.toml` configuration

#### Scenario: Worker Secrets Management
- **WHEN** deploying Worker that requires API keys
- **THEN** secrets must be set via Wrangler CLI:
  ```bash
  npx wrangler secret put SUPABASE_URL
  npx wrangler secret put SUPABASE_ANON_KEY
  npx wrangler secret put OPENROUTER_API_KEY
  ```
- **AND** secrets encrypted and stored in Cloudflare
- **AND** accessible via `env.SECRET_NAME` in Worker code
- **AND** never logged or exposed in responses
- **AND** can be updated without redeployment

#### Scenario: Worker Route Configuration
- **WHEN** Worker is deployed
- **THEN** custom domain routing configured in `wrangler.toml`
- **AND** route pattern: `web3search-api.marovole.workers.dev/*`
- **AND** all HTTP methods handled (GET, POST, OPTIONS, etc.)
- **AND** CORS configured to allow frontend origin
- **AND** automatic HTTPS enforcement

### Requirement: Database and External Services
The system **SHALL** integrate with Supabase for PostgreSQL database and use external APIs.

#### Scenario: Supabase Database Connection
- **WHEN** Worker needs to access database
- **THEN** use Supabase client with connection pooling
- **AND** connection string from environment variable
- **AND** row-level security (RLS) policies enforced
- **AND** queries executed via Supabase REST API
- **AND** connection pooling handles high concurrency

**Implementation**: `workers-api/src/lib/supabase.ts`

#### Scenario: CoinGecko API Integration
- **WHEN** user queries cryptocurrency prices
- **THEN** fetch real-time data from CoinGecko free API
- **AND** no API key required (public endpoints)
- **AND** rate limit: ~50 requests/minute
- **AND** graceful handling of rate limit errors
- **AND** timeout after 5 seconds

**Implementation**: `workers-api/src/lib/coingecko.ts`

#### Scenario: OpenRouter AI Integration
- **WHEN** processing chat requests
- **THEN** stream responses from OpenRouter API
- **AND** use API key from Worker secrets
- **AND** support multiple AI models (Claude, GPT, etc.)
- **AND** handle streaming with Server-Sent Events (SSE)
- **AND** retry failed requests with exponential backoff

**Implementation**: `workers-api/src/lib/openrouter.ts`

### Requirement: Edge Caching Strategy
The system **SHALL** use Cloudflare KV for edge caching to improve performance.

#### Scenario: Conversation Data Caching
- **WHEN** storing conversation history
- **THEN** save to Supabase (persistent storage)
- **AND** optionally cache in KV for fast retrieval
- **AND** KV key format: `conv:{conversation_id}`
- **AND** TTL: 24 hours
- **AND** automatic expiration cleanup

#### Scenario: Rate Limit Counter Storage
- **WHEN** tracking API rate limits
- **THEN** use KV as distributed counter
- **AND** key format: `ratelimit:{scope}:{identifier}:{window}`
- **AND** atomic increment operations
- **AND** sliding window algorithm
- **AND** TTL matches rate limit window

**Implementation**: `workers-api/src/middlewares/rate-limit.ts`

### Requirement: Frontend Performance Optimization
The frontend **SHALL** implement performance best practices for fast loading.

#### Scenario: Code Splitting and Lazy Loading
- **WHEN** building production bundle
- **THEN** Vite automatically splits code by route
- **AND** lazy load non-critical components
- **AND** critical CSS inlined in HTML
- **AND** non-critical CSS loaded asynchronously
- **AND** JavaScript modules loaded on demand

#### Scenario: Asset Optimization
- **WHEN** serving static assets
- **THEN** images compressed and optimized
- **AND** use WebP format where supported
- **AND** lazy load images below fold
- **AND** preload critical fonts
- **AND** CSS and JS minified and compressed

#### Scenario: Caching Headers
- **WHEN** Cloudflare Pages serves assets
- **THEN** set `Cache-Control` headers:
  - HTML: `max-age=0, must-revalidate`
  - CSS/JS: `max-age=31536000, immutable` (content-hashed filenames)
  - Images: `max-age=86400`
- **AND** leverage Cloudflare edge caching
- **AND** cache invalidation via version/hash changes

### Requirement: Monitoring and Health Checks
The system **SHALL** implement health checks and monitoring for production reliability.

#### Scenario: Worker Health Endpoint
- **WHEN** accessing `/api/v1/health`
- **THEN** return service status
- **AND** check Supabase connectivity
- **AND** check KV cache availability
- **AND** response time < 500ms
- **AND** status codes:
  - 200: All services healthy
  - 503: One or more services degraded

**Implementation**: `workers-api/src/routes/health.ts`

#### Scenario: Scheduled Health Checks (Cron)
- **WHEN** scheduled cron job runs (every 5 minutes)
- **THEN** execute health checks for all services
- **AND** store results in Supabase `healthcheck_events` table
- **AND** send alerts if critical service down
- **AND** track uptime metrics

**Implementation**: `workers-api/src/index.ts` scheduled event handler

#### Scenario: Error Logging
- **WHEN** Worker encounters error
- **THEN** log to Cloudflare Workers Logpush
- **AND** include request ID, timestamp, error message
- **AND** never log sensitive data (passwords, API keys)
- **AND** structured JSON format
- **AND** searchable in Cloudflare dashboard

### Requirement: Deployment Best Practices
All deployments **SHALL** follow security and reliability best practices.

#### Scenario: Environment Separation
- **WHEN** deploying to different environments
- **THEN** maintain separate:
  - Workers (production vs. staging)
  - Pages projects (main vs. preview)
  - Database schemas (production vs. test)
  - API keys (production vs. development)
- **AND** never use production secrets in development
- **AND** test in staging before production deploy

#### Scenario: Zero-Downtime Deployment
- **WHEN** deploying new Worker version
- **THEN** Cloudflare atomic switchover ensures:
  - No requests lost during deployment
  - No partial state visible to users
  - Instant rollback if issues detected
  - < 1 second traffic cutover

#### Scenario: Deployment Verification
- **WHEN** deployment completes
- **THEN** verify:
  1. Health endpoint returns 200
  2. Frontend loads without errors
  3. Chat functionality works end-to-end
  4. No console errors in browser
  5. API responses under 2 seconds
- **AND** rollback if any verification fails

## Deployment Checklist

### Pre-Deployment
- [ ] All tests passing (`npm test`)
- [ ] No TypeScript errors (`npm run type-check`)
- [ ] Environment variables configured
- [ ] Database migrations applied (if any)
- [ ] Secrets updated (if changed)

### Frontend Deployment (Cloudflare Pages)
- [ ] Push to `main` branch
- [ ] Verify build succeeds in dashboard
- [ ] Check preview URL works
- [ ] Merge PR to trigger production deploy
- [ ] Verify production URL: https://web3search.pages.dev

### Backend Deployment (Cloudflare Workers)
- [ ] `cd workers-api`
- [ ] `npm run deploy`
- [ ] Verify deployment success message
- [ ] Test health endpoint: `curl https://web3search-api.marovole.workers.dev/api/v1/health`
- [ ] Test chat endpoint with sample query

### Post-Deployment
- [ ] Monitor error logs for 15 minutes
- [ ] Check health metrics in dashboard
- [ ] Verify rate limiting works
- [ ] Test from multiple geographic locations
- [ ] Update deployment notes

## Production URLs

- **Frontend**: https://web3search.pages.dev
- **Backend API**: https://web3search-api.marovole.workers.dev
- **Health Check**: https://web3search-api.marovole.workers.dev/api/v1/health
- **Cloudflare Dashboard**: https://dash.cloudflare.com

## Troubleshooting

### Issue: Build Fails on Cloudflare Pages
- Check build logs in dashboard
- Verify `package.json` scripts are correct
- Ensure all dependencies in `package.json`
- Check Node.js version compatibility

### Issue: Worker Deployment Timeout
- Check `wrangler.toml` configuration
- Verify account ID and zone ID correct
- Ensure Wrangler authenticated: `npx wrangler login`
- Check bundle size (< 1MB recommended)

### Issue: Environment Variables Not Working
- Verify variables set in Cloudflare dashboard
- Check variable names match code
- Rebuild after changing variables
- For Workers, use `npx wrangler secret put` for sensitive values

### Issue: CORS Errors in Production
- Check allowed origins in `workers-api/src/middlewares/cors.ts`
- Verify frontend URL matches exactly
- Check OPTIONS preflight handled correctly
- Inspect browser DevTools Network tab

## Future Enhancements

1. **CI/CD Pipeline**: GitHub Actions for automated testing and deployment
2. **Multi-Region**: Deploy Workers to specific regions for compliance
3. **A/B Testing**: Cloudflare Workers for percentage-based rollouts
4. **Analytics**: Real User Monitoring (RUM) with Cloudflare Analytics
5. **CDN**: Custom domain with Cloudflare CDN for branding
