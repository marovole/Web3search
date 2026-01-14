import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";
import { authTables } from "@convex-dev/auth/server";

/**
 * Web3search Convex Schema
 * Complete database schema migrated from Supabase PostgreSQL
 */
export default defineSchema({
  ...authTables,
  // ============================================
  // User System Tables
  // ============================================

  /**
   * Users - Core user identity
   * Linked to Convex Auth via tokenIdentifier
   */
  users: defineTable({
    email: v.optional(v.string()),
    username: v.optional(v.string()),
    name: v.optional(v.string()),
    image: v.optional(v.string()),
    tokenIdentifier: v.string(), // External auth provider ID
    emailVerified: v.optional(v.boolean()),
    isActive: v.optional(v.boolean()),
    isSuperuser: v.optional(v.boolean()),
    lastLoginAt: v.optional(v.number()),
    deletedAt: v.optional(v.number()),
  })
    .index("by_token", ["tokenIdentifier"])
    .index("by_email", ["email"]),

  /**
   * User Profiles - Extended user data
   */
  userProfiles: defineTable({
    userId: v.id("users"),
    plan: v.union(v.literal("free"), v.literal("pro"), v.literal("team")),
    riskPreference: v.optional(
      v.union(
        v.literal("conservative"),
        v.literal("moderate"),
        v.literal("aggressive")
      )
    ),
    onboardingCompleted: v.optional(v.boolean()),
    stripeCustomerId: v.optional(v.string()),
    metadata: v.optional(v.any()),
  }).index("by_user", ["userId"]),

  /**
   * User Quotas - Usage limits
   */
  userQuotas: defineTable({
    userId: v.id("users"),
    watchlistCount: v.number(),
    watchlistLimit: v.number(),
    agentCount: v.number(),
    agentLimit: v.number(),
    deepResearchDaily: v.number(),
    deepResearchDailyLimit: v.number(),
    deepResearchMonthly: v.number(),
    deepResearchMonthlyLimit: v.number(),
    quickChatDaily: v.number(),
    quickChatDailyLimit: v.number(),
    lastResetDaily: v.optional(v.number()),
    lastResetMonthly: v.optional(v.number()),
  }).index("by_user", ["userId"]),

  /**
   * User Preferences - Settings and preferences
   */
  userPreferences: defineTable({
    userId: v.id("users"),
    preferences: v.any(), // JSON object for flexible preferences
  }).index("by_user", ["userId"]),

  // ============================================
  // Conversation System Tables
  // ============================================

  /**
   * Conversations - Chat sessions
   */
  conversations: defineTable({
    userId: v.optional(v.id("users")),
    clientSessionId: v.optional(v.string()),
    title: v.optional(v.string()),
    summary: v.optional(v.string()),
    metadata: v.optional(v.any()),
    modelPreset: v.optional(v.string()),
    modelConfig: v.optional(v.any()),
    status: v.union(
      v.literal("active"),
      v.literal("archived"),
      v.literal("closed")
    ),
    isArchived: v.optional(v.boolean()),
    totalMessages: v.number(),
    totalUserMessages: v.number(),
    tokenUsage: v.optional(v.any()),
    lastMessageAt: v.optional(v.number()),
    deletedAt: v.optional(v.number()),
  })
    .index("by_user", ["userId"])
    .index("by_session", ["clientSessionId"])
    .index("by_user_updated", ["userId", "lastMessageAt"]),

  /**
   * Messages - Chat messages
   */
  messages: defineTable({
    conversationId: v.id("conversations"),
    parentMessageId: v.optional(v.id("messages")),
    userId: v.optional(v.id("users")),
    role: v.union(
      v.literal("system"),
      v.literal("user"),
      v.literal("assistant"),
      v.literal("tool")
    ),
    status: v.union(
      v.literal("pending"),
      v.literal("streaming"),
      v.literal("completed"),
      v.literal("failed")
    ),
    segmentIndex: v.optional(v.number()),
    isFinal: v.optional(v.boolean()),
    content: v.optional(v.string()),
    contentDelta: v.optional(v.any()),
    contentJson: v.optional(v.any()),
    metadata: v.optional(v.any()),
    model: v.optional(v.string()),
    modelParameters: v.optional(v.any()),
    toolName: v.optional(v.string()),
    toolCallId: v.optional(v.string()),
    errorMessage: v.optional(v.string()),
    tokenCountPrompt: v.optional(v.number()),
    tokenCountCompletion: v.optional(v.number()),
    deletedAt: v.optional(v.number()),
  })
    .index("by_conversation", ["conversationId"]),

  // ============================================
  // Agent System Tables
  // ============================================

  /**
   * Agent Tasks - Background AI tasks
   */
  agentTasks: defineTable({
    userId: v.id("users"),
    name: v.string(),
    description: v.optional(v.string()),
    type: v.union(
      v.literal("price_alert"),
      v.literal("risk_monitor"),
      v.literal("news_brief"),
      v.literal("portfolio_health"),
      v.literal("opportunity_finder"),
      v.literal("custom")
    ),
    status: v.union(
      v.literal("active"),
      v.literal("paused"),
      v.literal("completed"),
      v.literal("failed"),
      v.literal("cancelled")
    ),
    config: v.any(),
    schedule: v.optional(v.string()),
    nextRunAt: v.optional(v.number()),
    lastRunAt: v.optional(v.number()),
    runCount: v.number(),
    successCount: v.number(),
    failureCount: v.number(),
    expiresAt: v.optional(v.number()),
    metadata: v.optional(v.any()),
  })
    .index("by_user", ["userId"])
    .index("by_user_status", ["userId", "status"])
    .index("by_status", ["status"])
    .index("by_next_run", ["nextRunAt"]),

  /**
   * Agent Runs - Task execution history
   */
  agentRuns: defineTable({
    taskId: v.id("agentTasks"),
    userId: v.id("users"),
    status: v.union(
      v.literal("running"),
      v.literal("completed"),
      v.literal("failed"),
      v.literal("cancelled")
    ),
    startedAt: v.number(),
    completedAt: v.optional(v.number()),
    durationMs: v.optional(v.number()),
    input: v.optional(v.any()),
    output: v.optional(v.any()),
    steps: v.optional(v.array(v.any())),
    errorMessage: v.optional(v.string()),
    errorCode: v.optional(v.string()),
    tokensUsed: v.optional(v.number()),
    apiCallsMade: v.optional(v.number()),
    triggeredBy: v.union(
      v.literal("schedule"),
      v.literal("manual"),
      v.literal("condition"),
      v.literal("webhook")
    ),
    notificationSent: v.optional(v.boolean()),
    metadata: v.optional(v.any()),
  })
    .index("by_task", ["taskId"])
    .index("by_user", ["userId"])
    .index("by_task_status", ["taskId", "status"]),

  /**
   * Agent Conversations - AI agent chat
   */
  agentConversations: defineTable({
    userId: v.id("users"),
    conversationId: v.string(),
    role: v.union(v.literal("user"), v.literal("assistant")),
    content: v.string(),
    intent: v.optional(v.any()),
    taskResult: v.optional(v.any()),
    metadata: v.optional(v.any()),
  })
    .index("by_user", ["userId"])
    .index("by_conversation", ["conversationId"]),

  // ============================================
  // Research System Tables
  // ============================================

  /**
   * Deep Research Tasks - Long-running research jobs
   */
  deepResearchTasks: defineTable({
    userId: v.optional(v.id("users")),
    clientSessionId: v.optional(v.string()),
    conversationId: v.optional(v.id("conversations")),
    query: v.string(),
    status: v.union(
      v.literal("pending"),
      v.literal("running"),
      v.literal("completed"),
      v.literal("failed"),
      v.literal("cancelled")
    ),
    researchDepth: v.union(
      v.literal("quick"),
      v.literal("standard"),
      v.literal("comprehensive")
    ),
    maxSources: v.number(),
    focusAreas: v.optional(v.array(v.string())),
    modelId: v.optional(v.string()),
    modelProvider: v.optional(
      v.union(
        v.literal("qwen"),
        v.literal("deepseek"),
        v.literal("anthropic"),
        v.literal("openai")
      )
    ),
    temperature: v.optional(v.number()),
    result: v.optional(v.any()),
    summary: v.optional(v.string()),
    answer: v.optional(v.string()),
    sources: v.optional(v.array(v.any())),
    citations: v.optional(v.array(v.any())),
    progressPercent: v.number(),
    currentStep: v.optional(v.string()),
    stepsCompleted: v.number(),
    totalSteps: v.number(),
    tokensPrompt: v.optional(v.number()),
    tokensCompletion: v.optional(v.number()),
    costUsd: v.optional(v.number()),
    startedAt: v.optional(v.number()),
    completedAt: v.optional(v.number()),
    durationMs: v.optional(v.number()),
    errorCode: v.optional(v.string()),
    errorMessage: v.optional(v.string()),
    retryCount: v.optional(v.number()),
    expiresAt: v.optional(v.number()),
    metadata: v.optional(v.any()),
    tags: v.optional(v.array(v.string())),
  })
    .index("by_user", ["userId"])
    .index("by_session", ["clientSessionId"])
    .index("by_status", ["status"])
    .index("by_conversation", ["conversationId"]),

  /**
   * Reports - Generated research reports
   */
  reports: defineTable({
    projectId: v.optional(v.id("projects")),
    conversationId: v.optional(v.id("conversations")),
    userId: v.optional(v.id("users")),
    reportType: v.union(v.literal("quick_chat"), v.literal("deep_research")),
    status: v.union(
      v.literal("pending"),
      v.literal("processing"),
      v.literal("completed"),
      v.literal("failed")
    ),
    query: v.string(),
    title: v.optional(v.string()),
    contentMarkdown: v.optional(v.string()),
    tldr: v.optional(v.string()),
    sections: v.optional(v.any()),
    dataSources: v.optional(v.any()),
    modelsUsed: v.optional(v.any()),
    generationTimeSeconds: v.optional(v.number()),
    tokenUsage: v.optional(v.any()),
    qualityScore: v.optional(v.number()),
    errorMessage: v.optional(v.string()),
    pdfPath: v.optional(v.string()),
    shareToken: v.optional(v.string()),
    shareEnabled: v.optional(v.boolean()),
    shareExpiresAt: v.optional(v.number()),
    symbol: v.optional(v.string()),
    completedAt: v.optional(v.number()),
  })
    .index("by_user", ["userId"])
    .index("by_share_token", ["shareToken"])
    .index("by_symbol", ["symbol"]),

  // ============================================
  // Portfolio Tables
  // ============================================

  /**
   * Watchlist - User's tracked tokens
   */
  watchlist: defineTable({
    userId: v.id("users"),
    tokenId: v.string(),
    symbol: v.string(),
    name: v.string(),
    coingeckoId: v.optional(v.string()),
    logoUrl: v.optional(v.string()),
    notes: v.optional(v.string()),
    tags: v.optional(v.array(v.string())),
    alertSettings: v.optional(v.any()),
    position: v.number(),
  })
    .index("by_user", ["userId"])
    .index("by_user_token", ["userId", "tokenId"])
    .index("by_user_position", ["userId", "position"]),

  /**
   * Holdings - User's portfolio holdings
   */
  holdings: defineTable({
    userId: v.id("users"),
    tokenId: v.string(),
    symbol: v.string(),
    name: v.string(),
    coingeckoId: v.optional(v.string()),
    logoUrl: v.optional(v.string()),
    quantity: v.number(),
    averageBuyPrice: v.optional(v.number()),
    totalCost: v.optional(v.number()),
    currentPrice: v.optional(v.number()),
    currentValue: v.optional(v.number()),
    profitLoss: v.optional(v.number()),
    profitLossPercent: v.optional(v.number()),
    lastUpdated: v.optional(v.number()),
    notes: v.optional(v.string()),
    metadata: v.optional(v.any()),
  })
    .index("by_user", ["userId"])
    .index("by_user_token", ["userId", "tokenId"]),

  /**
   * Portfolio Diagnoses - AI portfolio analysis
   */
  portfolioDiagnoses: defineTable({
    userId: v.id("users"),
    taskId: v.optional(v.id("agentTasks")),
    diagnosis: v.any(),
    riskScore: v.optional(v.number()),
    recommendations: v.optional(v.array(v.any())),
    analyzedAt: v.number(),
    metadata: v.optional(v.any()),
  }).index("by_user", ["userId"]),

  /**
   * Portfolio Snapshots - Historical portfolio state
   */
  portfolioSnapshots: defineTable({
    userId: v.id("users"),
    totalValue: v.number(),
    holdings: v.array(v.any()),
    metrics: v.optional(v.any()),
    snapshotAt: v.number(),
  })
    .index("by_user", ["userId"])
    .index("by_user_time", ["userId", "snapshotAt"]),

  // ============================================
  // Recommendations Tables
  // ============================================

  /**
   * Recommendations - AI-generated suggestions
   */
  recommendations: defineTable({
    userId: v.id("users"),
    type: v.union(
      v.literal("buy"),
      v.literal("sell"),
      v.literal("hold"),
      v.literal("research")
    ),
    tokenId: v.optional(v.string()),
    symbol: v.optional(v.string()),
    title: v.string(),
    description: v.string(),
    reasoning: v.optional(v.string()),
    confidence: v.optional(v.number()),
    priority: v.union(v.literal("low"), v.literal("medium"), v.literal("high")),
    status: v.union(
      v.literal("pending"),
      v.literal("viewed"),
      v.literal("acted"),
      v.literal("dismissed")
    ),
    sourceTaskId: v.optional(v.id("agentTasks")),
    expiresAt: v.optional(v.number()),
    metadata: v.optional(v.any()),
  })
    .index("by_user", ["userId"])
    .index("by_user_status", ["userId", "status"]),

  /**
   * Recommendation History - Track recommendation actions
   */
  recommendationHistory: defineTable({
    recommendationId: v.id("recommendations"),
    userId: v.id("users"),
    action: v.union(
      v.literal("viewed"),
      v.literal("clicked"),
      v.literal("acted"),
      v.literal("dismissed")
    ),
    metadata: v.optional(v.any()),
  })
    .index("by_recommendation", ["recommendationId"])
    .index("by_user", ["userId"]),

  // ============================================
  // Notification Tables
  // ============================================

  /**
   * Notifications - User notifications
   */
  notifications: defineTable({
    userId: v.id("users"),
    type: v.union(
      v.literal("price_alert"),
      v.literal("risk_alert"),
      v.literal("news_brief"),
      v.literal("portfolio_update"),
      v.literal("system"),
      v.literal("promo")
    ),
    title: v.string(),
    body: v.string(),
    data: v.optional(v.any()),
    sourceType: v.optional(v.string()),
    sourceId: v.optional(v.string()),
    readAt: v.optional(v.number()),
    dismissedAt: v.optional(v.number()),
    priority: v.union(
      v.literal("low"),
      v.literal("normal"),
      v.literal("high"),
      v.literal("urgent")
    ),
    expiresAt: v.optional(v.number()),
    pushSent: v.optional(v.boolean()),
    pushSentAt: v.optional(v.number()),
  })
    .index("by_user", ["userId"])
    .index("by_user_unread", ["userId", "readAt"]),

  /**
   * Push Subscriptions - Web push notification subscriptions
   */
  pushSubscriptions: defineTable({
    userId: v.id("users"),
    endpoint: v.string(),
    p256dh: v.string(),
    auth: v.string(),
    userAgent: v.optional(v.string()),
    isActive: v.boolean(),
    lastUsedAt: v.optional(v.number()),
    failureCount: v.optional(v.number()),
  })
    .index("by_user", ["userId"])
    .index("by_endpoint", ["endpoint"]),

  // ============================================
  // Subscription/Billing Tables
  // ============================================

  /**
   * Subscriptions - Stripe subscriptions
   */
  subscriptions: defineTable({
    userId: v.id("users"),
    stripeSubscriptionId: v.string(),
    stripeCustomerId: v.string(),
    stripePriceId: v.string(),
    status: v.string(),
    currentPeriodStart: v.number(),
    currentPeriodEnd: v.number(),
    cancelAtPeriodEnd: v.optional(v.boolean()),
    canceledAt: v.optional(v.number()),
    metadata: v.optional(v.any()),
  })
    .index("by_user", ["userId"])
    .index("by_stripe_subscription", ["stripeSubscriptionId"]),

  // ============================================
  // Project/Token Data Tables
  // ============================================

  /**
   * Projects - Cryptocurrency projects
   */
  projects: defineTable({
    symbol: v.string(),
    name: v.string(),
    coingeckoId: v.optional(v.string()),
    description: v.optional(v.string()),
    website: v.optional(v.string()),
    whitepaperUrl: v.optional(v.string()),
    blockchain: v.optional(v.string()),
    contractAddresses: v.optional(v.any()),
    twitterHandle: v.optional(v.string()),
    telegramUrl: v.optional(v.string()),
    discordUrl: v.optional(v.string()),
    redditUrl: v.optional(v.string()),
    categories: v.optional(v.array(v.string())),
    tags: v.optional(v.array(v.string())),
    firstSeen: v.optional(v.number()),
    lastUpdated: v.optional(v.number()),
  })
    .index("by_symbol", ["symbol"])
    .index("by_coingecko", ["coingeckoId"]),

  /**
   * Project Snapshots - Historical market data
   */
  projectSnapshots: defineTable({
    projectId: v.id("projects"),
    priceUsd: v.optional(v.number()),
    priceBtc: v.optional(v.number()),
    marketCap: v.optional(v.number()),
    totalVolume24h: v.optional(v.number()),
    circulatingSupply: v.optional(v.number()),
    totalSupply: v.optional(v.number()),
    maxSupply: v.optional(v.number()),
    priceChange24h: v.optional(v.number()),
    priceChange7d: v.optional(v.number()),
    priceChange30d: v.optional(v.number()),
    marketCapRank: v.optional(v.number()),
    holderCount: v.optional(v.number()),
    totalTransactions: v.optional(v.number()),
    transactionCount24h: v.optional(v.number()),
    activeAddresses24h: v.optional(v.number()),
    twitterFollowers: v.optional(v.number()),
    twitterMentions24h: v.optional(v.number()),
    redditSubscribers: v.optional(v.number()),
    redditActiveUsers: v.optional(v.number()),
    sentimentScore: v.optional(v.number()),
    sentimentVolume: v.optional(v.number()),
    rawMarketData: v.optional(v.any()),
    rawOnchainData: v.optional(v.any()),
    rawSocialData: v.optional(v.any()),
    snapshotAt: v.number(),
  })
    .index("by_project", ["projectId"])
    .index("by_project_time", ["projectId", "snapshotAt"]),

  // ============================================
  // Multi-Agent System Tables
  // ============================================

  /**
   * Multi-Agent Tasks - Coordinated agent tasks
   */
  multiAgentTasks: defineTable({
    userId: v.optional(v.id("users")),
    clientSessionId: v.optional(v.string()),
    query: v.string(),
    status: v.union(
      v.literal("pending"),
      v.literal("running"),
      v.literal("completed"),
      v.literal("failed"),
      v.literal("cancelled")
    ),
    priority: v.union(v.literal("low"), v.literal("normal"), v.literal("high")),
    agentTypes: v.array(v.string()),
    context: v.optional(v.any()),
    results: v.optional(v.any()),
    aggregatedResult: v.optional(v.any()),
    startedAt: v.optional(v.number()),
    completedAt: v.optional(v.number()),
    errorMessage: v.optional(v.string()),
    metadata: v.optional(v.any()),
  })
    .index("by_user", ["userId"])
    .index("by_status", ["status"]),

  // ============================================
  // System Tables
  // ============================================

  /**
   * Healthcheck Events - System health logs
   */
  healthcheckEvents: defineTable({
    checkName: v.string(),
    status: v.union(v.literal("ok"), v.literal("error"), v.literal("warning")),
    latencyMs: v.optional(v.number()),
    errorMessage: v.optional(v.string()),
    metadata: v.optional(v.any()),
  }).index("by_check", ["checkName"]),

  /**
   * API Telemetry - API call tracking
   */
  apiTelemetry: defineTable({
    endpoint: v.string(),
    method: v.string(),
    statusCode: v.number(),
    responseTimeMs: v.optional(v.number()),
    userId: v.optional(v.id("users")),
    ipAddress: v.optional(v.string()),
    userAgent: v.optional(v.string()),
    metadata: v.optional(v.any()),
  })
    .index("by_endpoint", ["endpoint"])
    .index("by_user", ["userId"]),
});
