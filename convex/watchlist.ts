import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

export const list = query({
  args: {
    userId: v.id("users"),
  },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("watchlist")
      .withIndex("by_user", (q) => q.eq("userId", args.userId))
      .order("asc")
      .collect();
  },
});

export const get = query({
  args: { id: v.id("watchlist") },
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
    coingeckoId: v.optional(v.string()),
    logoUrl: v.optional(v.string()),
    notes: v.optional(v.string()),
    tags: v.optional(v.array(v.string())),
    alertSettings: v.optional(v.any()),
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("watchlist")
      .withIndex("by_user_token", (q) =>
        q.eq("userId", args.userId).eq("tokenId", args.tokenId)
      )
      .unique();

    if (existing) {
      throw new Error("Token already in watchlist");
    }

    const items = await ctx.db
      .query("watchlist")
      .withIndex("by_user", (q) => q.eq("userId", args.userId))
      .collect();
    const maxPosition = items.length > 0 ? Math.max(...items.map((i) => i.position)) : -1;

    return await ctx.db.insert("watchlist", {
      ...args,
      position: maxPosition + 1,
    });
  },
});

export const update = mutation({
  args: {
    id: v.id("watchlist"),
    notes: v.optional(v.string()),
    tags: v.optional(v.array(v.string())),
    alertSettings: v.optional(v.any()),
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

export const remove = mutation({
  args: { id: v.id("watchlist") },
  handler: async (ctx, args) => {
    await ctx.db.delete(args.id);
  },
});

export const reorder = mutation({
  args: {
    items: v.array(
      v.object({
        id: v.id("watchlist"),
        position: v.number(),
      })
    ),
  },
  handler: async (ctx, args) => {
    for (const item of args.items) {
      await ctx.db.patch(item.id, { position: item.position });
    }
  },
});
