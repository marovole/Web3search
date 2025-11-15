# Search Provider API Keys

This document explains how to obtain API keys for the search providers used in the Web3 Search API.

## Overview

The search aggregation system supports three providers with automatic failover:

1. **Brave Search** (Primary) - Fast, privacy-focused search
2. **Tavily Search** (Failover) - AI-optimized search with relevance scoring
3. **Serper** (Failover) - Google-powered search results

**Failover Priority**: Brave → Tavily → Serper

At least **one provider** must be configured for search functionality to work. For maximum resilience, configure all three.

---

## Brave Search API

### Features
- **Free Tier**: 2,000 queries/month
- **Paid Plans**: Starting at $5/month for 20,000 queries
- **Strengths**: Fast responses, good privacy, web-focused results

### How to Get API Key

1. Visit [Brave Search API](https://brave.com/search/api/)
2. Click "Get Started" or "Sign Up"
3. Create an account with your email
4. Navigate to the API Dashboard
5. Generate a new API key
6. Copy the key (format: `BSA...`)

### Set the Secret

```bash
wrangler secret put BRAVE_SEARCH_API_KEY
# Paste your key when prompted
```

### Test the Integration

```bash
curl -X POST https://your-worker.workers.dev/api/v1/deep-research/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "What is Bitcoin?"}'
```

Check logs for `[search-provider]` entries showing `provider: "brave"`.

---

## Tavily Search API

### Features
- **Free Tier**: 1,000 queries/month
- **Paid Plans**: Starting at $20/month for 10,000 queries
- **Strengths**: AI-optimized results, built-in relevance scoring, research-focused

### How to Get API Key

1. Visit [Tavily AI](https://tavily.com/) or [Tavily Docs](https://docs.tavily.com/)
2. Click "Get API Key" or "Sign Up"
3. Create an account (GitHub/Google/Email)
4. Navigate to the API section in your dashboard
5. Generate a new API key
6. Copy the key (format: `tvly-...`)

### Set the Secret

```bash
wrangler secret put TAVILY_API_KEY
# Paste your key when prompted
```

### Verify Failover

Temporarily disable Brave to test Tavily failover:

```bash
# Remove Brave key temporarily
wrangler secret delete BRAVE_SEARCH_API_KEY

# Make a search request
curl -X POST https://your-worker.workers.dev/api/v1/deep-research/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "Ethereum gas fees"}'

# Check logs - should show provider: "tavily"

# Restore Brave key
wrangler secret put BRAVE_SEARCH_API_KEY
```

---

## Serper (Google Search) API

### Features
- **Free Tier**: 2,500 queries (one-time credit)
- **Paid Plans**: Pay-as-you-go at $5 per 1,000 queries
- **Strengths**: Google-quality results, comprehensive coverage, structured data

### How to Get API Key

1. Visit [Serper.dev](https://serper.dev/)
2. Click "Get API Key" or "Sign Up"
3. Sign in with Google or create an account
4. Navigate to the Dashboard
5. Find your API key (automatically generated)
6. Copy the key (format: alphanumeric string)

### Set the Secret

```bash
wrangler secret put SERPER_API_KEY
# Paste your key when prompted
```

### Test Full Failover Chain

```bash
# Disable Brave and Tavily to test Serper
wrangler secret delete BRAVE_SEARCH_API_KEY
wrangler secret delete TAVILY_API_KEY

# Make a search request
curl -X POST https://your-worker.workers.dev/api/v1/deep-research/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "DeFi protocols comparison"}'

# Check logs - should show provider: "serper"

# Restore keys
wrangler secret put BRAVE_SEARCH_API_KEY
wrangler secret put TAVILY_API_KEY
```

---

## Environment Configuration

### Local Development

For local testing with `wrangler dev`, create a `.dev.vars` file (gitignored):

```bash
# workers-api/.dev.vars
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
OPENROUTER_API_KEY=sk-or-v1-...

# Search Providers (add at least one)
BRAVE_SEARCH_API_KEY=BSA...
TAVILY_API_KEY=tvly-...
SERPER_API_KEY=your-serper-key
```

### Production Deployment

Use Wrangler secrets for production (encrypted):

```bash
# Required
wrangler secret put SUPABASE_URL
wrangler secret put SUPABASE_ANON_KEY
wrangler secret put OPENROUTER_API_KEY

# Search Providers (recommended: all three for resilience)
wrangler secret put BRAVE_SEARCH_API_KEY
wrangler secret put TAVILY_API_KEY
wrangler secret put SERPER_API_KEY
```

---

## Monitoring and Telemetry

### View Provider Usage

Check Cloudflare Workers logs to see which providers are being used:

```bash
wrangler tail
```

Look for structured logs like:

```json
{
  "provider": "brave",
  "query": "What is Bitcoin?",
  "success": true,
  "fromCache": false,
  "ttfbMs": 234,
  "totalMs": 245,
  "statusCode": 200,
  "resultCount": 12
}
```

### Failover Indicators

When failover occurs, you'll see multiple provider attempts:

```json
[
  {
    "provider": "brave",
    "success": false,
    "errorType": "rate_limit",
    "statusCode": 429
  },
  {
    "provider": "tavily",
    "success": true,
    "resultCount": 8
  }
]
```

### Common Issues

1. **"No search API keys configured"**
   - At least one provider key must be set
   - Verify with: `wrangler secret list`

2. **"All providers failed"**
   - Check API key validity
   - Verify rate limits haven't been exceeded
   - Check provider status pages:
     - [Brave Status](https://status.brave.com/)
     - [Tavily Status](https://status.tavily.com/)
     - [Serper Status](https://status.serper.dev/)

3. **High latency**
   - Provider timeout is 5 seconds per provider
   - Failover adds latency (mitigated by caching)
   - Consider upgrading to paid tiers for better performance

---

## Cost Optimization

### Free Tier Limits

| Provider | Free Tier | Overage Cost |
|----------|-----------|--------------|
| Brave    | 2,000/mo  | $0.25/1K     |
| Tavily   | 1,000/mo  | $2.00/1K     |
| Serper   | 2,500 one-time | $5.00/1K |

### Caching Strategy

The search module caches results for **5 minutes** per provider:
- Cache key format: `search:{provider}:{query}`
- Reduces API calls for repeated queries
- Provider-specific isolation

### Recommendations

1. **Development**: Use Brave free tier (2K/month is usually sufficient)
2. **Production**: Configure all three providers for resilience
3. **High-traffic**: Monitor usage via telemetry, upgrade as needed
4. **Budget-conscious**: Start with Brave + Serper (4.5K free queries)

---

## Advanced Configuration

### Custom Timeout

Default provider timeout is 5 seconds. To modify:

Edit `workers-api/src/lib/search-providers.ts`:

```typescript
const PROVIDER_TIMEOUT_MS = 10_000 // 10 seconds
```

### Provider Priority Order

Default priority: Brave → Tavily → Serper

To change, edit:

```typescript
const PROVIDER_PRIORITY: SearchProvider[] = ['tavily', 'brave', 'serper']
```

### Disable Specific Providers

Simply don't set the API key for that provider. The system will skip it in failover.

---

## Support

- **Brave Search**: [support@brave.com](mailto:support@brave.com)
- **Tavily**: [Tavily Discord](https://discord.gg/tavily) or [support@tavily.com](mailto:support@tavily.com)
- **Serper**: [Serper Support](https://serper.dev/support)
- **Web3 Search Issues**: [GitHub Issues](https://github.com/marovole/Web3search/issues)
