# AI Agent System User Guide

Web3search's AI Agent system proactively monitors your crypto portfolio and sends intelligent notifications.

## Quick Start

1. **Sign Up** - Create an account at [web3search.pages.dev](https://web3search.pages.dev)
2. **Add Tokens** - Go to Watchlist and add tokens you want to monitor
3. **Enable Notifications** - Allow browser push notifications in Settings
4. **Create Agents** - Set up automated monitoring tasks

## Agent Types

### Price Alert Agent
Get notified when token prices hit your targets.

**How to Create:**
1. Go to Agent Chat (`/agent-chat`)
2. Type: "Alert me when BTC drops below $60,000"
3. Confirm the task details

**Supported Conditions:**
- Price above/below threshold
- Percentage change (24h)
- All-time high/low alerts

**Examples:**
- "Notify me when ETH goes above $4,000"
- "Tell me if SOL drops 10% in 24 hours"
- "Alert when DOGE hits $0.50"

### Risk Monitor Agent
Tracks risk score changes for tokens in your watchlist.

**What It Monitors:**
- ScamMeter score changes (+/- 10 points)
- New Red Flags detected
- Holder concentration changes
- Smart contract updates

**Frequency:** Runs every 10 minutes for active watchlist tokens

### News Brief Agent
Delivers summarized crypto news relevant to your interests.

**Delivery Schedule:**
- Hourly summaries (configurable)
- Breaking news alerts
- Filtered by your watchlist tokens

**Customize:**
1. Go to Settings > Notifications
2. Choose news frequency
3. Select token focus areas

### Portfolio Diagnosis Agent
Weekly health check of your portfolio.

**Report Includes:**
- Asset allocation analysis
- Correlation risk assessment
- Performance comparison vs BTC/ETH
- Rebalancing suggestions

**Schedule:** Every Monday at 9 AM (configurable)

### Opportunity Discovery Agent
Finds new investment opportunities based on your preferences.

**Factors Considered:**
- Your existing holdings
- Market trends
- Risk tolerance (inferred from portfolio)
- Historical interests

**Delivery:** Wednesdays at 10 AM

## Chat Interface

### Natural Language Commands

The AI Agent understands natural language. Try these:

**Create Tasks:**
- "Watch BTC and alert me at $100k"
- "Track risk for my watchlist daily"
- "Send me news about DeFi every morning"

**Manage Tasks:**
- "Show my active alerts"
- "Pause all notifications"
- "Delete the SOL price alert"

**Ask Questions:**
- "What agents do I have running?"
- "When will my next news brief arrive?"
- "How many alerts did I get this week?"

### Confirmation Flow

For high-confidence intents (>80%), tasks are created automatically.
For lower confidence, you'll see a confirmation dialog:

```
I understood you want:
- Task: Price Alert
- Token: BTC
- Condition: Price below $60,000

Is this correct? [Confirm] [Cancel]
```

## Notifications

### Browser Push Setup

1. Click the bell icon in the header
2. Click "Enable Notifications"
3. Allow the browser permission prompt
4. Test with "Send Test Notification"

### Notification Types

| Type | Icon | Priority |
|------|------|----------|
| Price Alert | 💰 | High |
| Risk Warning | ⚠️ | High |
| News Brief | 📰 | Medium |
| Portfolio Report | 📊 | Low |
| Opportunity | 💡 | Low |

### Managing Notifications

**View All:** Click notification bell or go to `/notifications`

**Mark as Read:** Click individual notifications or "Mark All Read"

**Preferences:**
- Enable/disable by type
- Set quiet hours
- Choose notification sound

## Agent Dashboard

Access at `/agent-dashboard` to see:

- **Active Tasks** - Running agents and their status
- **Recent Activity** - Latest executions and results
- **Usage Stats** - Quota consumption and trends
- **Execution Log** - Detailed agent run history

## Quotas & Limits

### Free Plan
| Feature | Limit |
|---------|-------|
| Active Agents | 3 |
| Price Alerts | 5 |
| Notifications/day | 20 |
| AI Conversations | 50/month |

### Pro Plan
| Feature | Limit |
|---------|-------|
| Active Agents | 20 |
| Price Alerts | 50 |
| Notifications/day | 100 |
| AI Conversations | Unlimited |

View your usage at Settings > Quota Usage.

## Troubleshooting

### Notifications Not Working

1. Check browser permissions (Settings > Privacy > Notifications)
2. Ensure the site is not in "Block" list
3. Try "Send Test Notification" in Push Settings
4. Check if Do Not Disturb is enabled on your device

### Agent Not Triggering

1. Verify the task is "Active" in Agent Dashboard
2. Check if conditions are correct
3. Review execution logs for errors
4. Ensure you haven't hit quota limits

### Inaccurate Prices

Price data comes from CoinGecko with a 1-minute cache.
For real-time prices, refresh the page or wait for next update.

## Privacy & Data

- **Read-Only** - Agents never execute trades or access wallets
- **Your Data** - Task configurations stored securely in your account
- **No Sharing** - Your watchlist and preferences are private
- **Delete Anytime** - Remove all agent data from Settings

## Support

- **In-App Chat** - Use `/agent-chat` with questions
- **Email** - vole@lucky365vip.cc
- **Docs** - [docs/](./docs/)
