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
