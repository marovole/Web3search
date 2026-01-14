import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

export const getByToken = query({
  args: { tokenIdentifier: v.string() },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("users")
      .withIndex("by_token", (q) => q.eq("tokenIdentifier", args.tokenIdentifier))
      .unique();
  },
});

export const getById = query({
  args: { id: v.id("users") },
  handler: async (ctx, args) => {
    return await ctx.db.get(args.id);
  },
});

export const create = mutation({
  args: {
    tokenIdentifier: v.string(),
    email: v.optional(v.string()),
    username: v.optional(v.string()),
    name: v.optional(v.string()),
    image: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("users")
      .withIndex("by_token", (q) => q.eq("tokenIdentifier", args.tokenIdentifier))
      .unique();

    if (existing) {
      return existing._id;
    }

    return await ctx.db.insert("users", {
      ...args,
      isActive: true,
      isSuperuser: false,
    });
  },
});

export const update = mutation({
  args: {
    id: v.id("users"),
    email: v.optional(v.string()),
    username: v.optional(v.string()),
    name: v.optional(v.string()),
    image: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    const { id, ...updates } = args;
    const filteredUpdates = Object.fromEntries(
      Object.entries(updates).filter(([_, v]) => v !== undefined)
    );
    
    if (Object.keys(filteredUpdates).length > 0) {
      await ctx.db.patch(id, filteredUpdates);
    }
    return await ctx.db.get(id);
  },
});

export const getProfile = query({
  args: { userId: v.id("users") },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("userProfiles")
      .withIndex("by_user", (q) => q.eq("userId", args.userId))
      .unique();
  },
});

export const upsertProfile = mutation({
  args: {
    userId: v.id("users"),
    plan: v.optional(v.union(v.literal("free"), v.literal("pro"), v.literal("team"))),
    riskPreference: v.optional(
      v.union(v.literal("conservative"), v.literal("moderate"), v.literal("aggressive"))
    ),
    onboardingCompleted: v.optional(v.boolean()),
    stripeCustomerId: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("userProfiles")
      .withIndex("by_user", (q) => q.eq("userId", args.userId))
      .unique();

    if (existing) {
      const { userId, ...updates } = args;
      const filteredUpdates = Object.fromEntries(
        Object.entries(updates).filter(([_, v]) => v !== undefined)
      );
      await ctx.db.patch(existing._id, filteredUpdates);
      return existing._id;
    }

    return await ctx.db.insert("userProfiles", {
      userId: args.userId,
      plan: args.plan ?? "free",
      riskPreference: args.riskPreference,
      onboardingCompleted: args.onboardingCompleted ?? false,
      stripeCustomerId: args.stripeCustomerId,
    });
  },
});

export const getQuota = query({
  args: { userId: v.id("users") },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("userQuotas")
      .withIndex("by_user", (q) => q.eq("userId", args.userId))
      .unique();
  },
});

export const upsertQuota = mutation({
  args: {
    userId: v.id("users"),
    watchlistCount: v.optional(v.number()),
    agentCount: v.optional(v.number()),
    deepResearchDaily: v.optional(v.number()),
    quickChatDaily: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("userQuotas")
      .withIndex("by_user", (q) => q.eq("userId", args.userId))
      .unique();

    if (existing) {
      const { userId, ...updates } = args;
      const filteredUpdates = Object.fromEntries(
        Object.entries(updates).filter(([_, v]) => v !== undefined)
      );
      await ctx.db.patch(existing._id, filteredUpdates);
      return existing._id;
    }

    return await ctx.db.insert("userQuotas", {
      userId: args.userId,
      watchlistCount: args.watchlistCount ?? 0,
      watchlistLimit: 10,
      agentCount: args.agentCount ?? 0,
      agentLimit: 3,
      deepResearchDaily: args.deepResearchDaily ?? 0,
      deepResearchDailyLimit: 5,
      deepResearchMonthly: 0,
      deepResearchMonthlyLimit: 50,
      quickChatDaily: args.quickChatDaily ?? 0,
      quickChatDailyLimit: 50,
    });
  },
});

export const incrementQuota = mutation({
  args: {
    userId: v.id("users"),
    field: v.union(
      v.literal("watchlistCount"),
      v.literal("agentCount"),
      v.literal("deepResearchDaily"),
      v.literal("quickChatDaily")
    ),
  },
  handler: async (ctx, args) => {
    const quota = await ctx.db
      .query("userQuotas")
      .withIndex("by_user", (q) => q.eq("userId", args.userId))
      .unique();

    if (!quota) {
      throw new Error("Quota not found");
    }

    const currentValue = quota[args.field] ?? 0;
    await ctx.db.patch(quota._id, { [args.field]: currentValue + 1 });
  },
});

/**
 * Cleanup user data - cascade delete all user-related data
 * This is used for GDPR compliance and account deletion
 */
export const cleanupUser = mutation({
  args: { userId: v.id("users") },
  handler: async (ctx, args) => {
    const { userId } = args;

    // 1. Delete conversations and their messages
    const conversations = await ctx.db
      .query("conversations")
      .withIndex("by_user", (q) => q.eq("userId", userId))
      .collect();
    for (const conv of conversations) {
      // Delete messages for this conversation
      const messages = await ctx.db
        .query("messages")
        .withIndex("by_conversation", (q) => q.eq("conversationId", conv._id))
        .collect();
      for (const msg of messages) {
        await ctx.db.delete(msg._id);
      }
      await ctx.db.delete(conv._id);
    }

    // 2. Delete agent tasks and their runs
    const agentTasks = await ctx.db
      .query("agentTasks")
      .withIndex("by_user", (q) => q.eq("userId", userId))
      .collect();
    for (const task of agentTasks) {
      // Delete runs for this task
      const runs = await ctx.db
        .query("agentRuns")
        .withIndex("by_task", (q) => q.eq("taskId", task._id))
        .collect();
      for (const run of runs) {
        await ctx.db.delete(run._id);
      }
      await ctx.db.delete(task._id);
    }

    // 3. Delete agent conversations
    const agentConversations = await ctx.db
      .query("agentConversations")
      .withIndex("by_user", (q) => q.eq("userId", userId))
      .collect();
    for (const conv of agentConversations) {
      await ctx.db.delete(conv._id);
    }

    // 4. Delete deep research tasks
    const researchTasks = await ctx.db
      .query("deepResearchTasks")
      .withIndex("by_user", (q) => q.eq("userId", userId))
      .collect();
    for (const task of researchTasks) {
      await ctx.db.delete(task._id);
    }

    // 5. Delete reports
    const reports = await ctx.db
      .query("reports")
      .withIndex("by_user", (q) => q.eq("userId", userId))
      .collect();
    for (const report of reports) {
      await ctx.db.delete(report._id);
    }

    // 6. Delete watchlist
    const watchlistItems = await ctx.db
      .query("watchlist")
      .withIndex("by_user", (q) => q.eq("userId", userId))
      .collect();
    for (const item of watchlistItems) {
      await ctx.db.delete(item._id);
    }

    // 7. Delete holdings
    const holdings = await ctx.db
      .query("holdings")
      .withIndex("by_user", (q) => q.eq("userId", userId))
      .collect();
    for (const holding of holdings) {
      await ctx.db.delete(holding._id);
    }

    // 8. Delete portfolio diagnoses
    const diagnoses = await ctx.db
      .query("portfolioDiagnoses")
      .withIndex("by_user", (q) => q.eq("userId", userId))
      .collect();
    for (const diag of diagnoses) {
      await ctx.db.delete(diag._id);
    }

    // 9. Delete portfolio snapshots
    const snapshots = await ctx.db
      .query("portfolioSnapshots")
      .withIndex("by_user", (q) => q.eq("userId", userId))
      .collect();
    for (const snap of snapshots) {
      await ctx.db.delete(snap._id);
    }

    // 10. Delete recommendations and history
    const recommendations = await ctx.db
      .query("recommendations")
      .withIndex("by_user", (q) => q.eq("userId", userId))
      .collect();
    for (const rec of recommendations) {
      await ctx.db.delete(rec._id);
    }

    const recHistory = await ctx.db
      .query("recommendationHistory")
      .withIndex("by_user", (q) => q.eq("userId", userId))
      .collect();
    for (const hist of recHistory) {
      await ctx.db.delete(hist._id);
    }

    // 11. Delete notifications
    const notifications = await ctx.db
      .query("notifications")
      .withIndex("by_user", (q) => q.eq("userId", userId))
      .collect();
    for (const notif of notifications) {
      await ctx.db.delete(notif._id);
    }

    // 12. Delete push subscriptions
    const pushSubs = await ctx.db
      .query("pushSubscriptions")
      .withIndex("by_user", (q) => q.eq("userId", userId))
      .collect();
    for (const sub of pushSubs) {
      await ctx.db.delete(sub._id);
    }

    // 13. Delete user profile, quota, preferences
    const profile = await ctx.db
      .query("userProfiles")
      .withIndex("by_user", (q) => q.eq("userId", userId))
      .unique();
    if (profile) await ctx.db.delete(profile._id);

    const quota = await ctx.db
      .query("userQuotas")
      .withIndex("by_user", (q) => q.eq("userId", userId))
      .unique();
    if (quota) await ctx.db.delete(quota._id);

    const prefs = await ctx.db
      .query("userPreferences")
      .withIndex("by_user", (q) => q.eq("userId", userId))
      .unique();
    if (prefs) await ctx.db.delete(prefs._id);

    // 14. Finally, soft delete the user (mark as deleted instead of hard delete)
    await ctx.db.patch(userId, { deletedAt: Date.now(), isActive: false });

    return { success: true, cleanedAt: Date.now() };
  },
});
