import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

export const list = query({
  args: {
    userId: v.id("users"),
  },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("holdings")
      .withIndex("by_user", (q) => q.eq("userId", args.userId))
      .collect();
  },
});

export const get = query({
  args: { id: v.id("holdings") },
  handler: async (ctx, args) => {
    return await ctx.db.get(args.id);
  },
});

export const add = mutation({
  args: {
    userId: v.id("users"),
    tokenId: v.string(),
    symbol: v.string(),
    name: v.string(),
    quantity: v.number(),
    averageBuyPrice: v.optional(v.number()),
    coingeckoId: v.optional(v.string()),
    logoUrl: v.optional(v.string()),
    notes: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("holdings")
      .withIndex("by_user_token", (q) =>
        q.eq("userId", args.userId).eq("tokenId", args.tokenId)
      )
      .unique();

    if (existing) {
      const newQuantity = existing.quantity + args.quantity;
      const totalCost =
        (existing.totalCost ?? 0) +
        (args.averageBuyPrice ?? 0) * args.quantity;
      const newAverageBuyPrice = newQuantity > 0 ? totalCost / newQuantity : 0;

      await ctx.db.patch(existing._id, {
        quantity: newQuantity,
        averageBuyPrice: newAverageBuyPrice,
        totalCost,
        lastUpdated: Date.now(),
      });
      return existing._id;
    }

    const totalCost = (args.averageBuyPrice ?? 0) * args.quantity;
    return await ctx.db.insert("holdings", {
      ...args,
      totalCost,
      lastUpdated: Date.now(),
    });
  },
});

export const update = mutation({
  args: {
    id: v.id("holdings"),
    quantity: v.optional(v.number()),
    averageBuyPrice: v.optional(v.number()),
    currentPrice: v.optional(v.number()),
    notes: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    const holding = await ctx.db.get(args.id);
    if (!holding) {
      throw new Error("Holding not found");
    }

    const updates: Record<string, unknown> = {};
    
    if (args.quantity !== undefined) {
      updates.quantity = args.quantity;
    }
    if (args.averageBuyPrice !== undefined) {
      updates.averageBuyPrice = args.averageBuyPrice;
    }
    if (args.currentPrice !== undefined) {
      updates.currentPrice = args.currentPrice;
    }
    if (args.notes !== undefined) {
      updates.notes = args.notes;
    }

    const quantity = args.quantity ?? holding.quantity;
    const avgPrice = args.averageBuyPrice ?? holding.averageBuyPrice ?? 0;
    const currentPrice = args.currentPrice ?? holding.currentPrice ?? 0;

    updates.totalCost = avgPrice * quantity;
    updates.currentValue = currentPrice * quantity;
    updates.profitLoss = updates.currentValue - updates.totalCost;
    updates.profitLossPercent =
      updates.totalCost > 0
        ? ((updates.profitLoss as number) / (updates.totalCost as number)) * 100
        : 0;
    updates.lastUpdated = Date.now();

    await ctx.db.patch(args.id, updates);
    return await ctx.db.get(args.id);
  },
});

export const remove = mutation({
  args: { id: v.id("holdings") },
  handler: async (ctx, args) => {
    await ctx.db.delete(args.id);
  },
});

export const getPortfolioSummary = query({
  args: { userId: v.id("users") },
  handler: async (ctx, args) => {
    const holdings = await ctx.db
      .query("holdings")
      .withIndex("by_user", (q) => q.eq("userId", args.userId))
      .collect();

    const totalValue = holdings.reduce((sum, h) => sum + (h.currentValue ?? 0), 0);
    const totalCost = holdings.reduce((sum, h) => sum + (h.totalCost ?? 0), 0);
    const totalProfitLoss = totalValue - totalCost;
    const totalProfitLossPercent = totalCost > 0 ? (totalProfitLoss / totalCost) * 100 : 0;

    return {
      holdings,
      totalValue,
      totalCost,
      totalProfitLoss,
      totalProfitLossPercent,
      holdingsCount: holdings.length,
    };
  },
});
