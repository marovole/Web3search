import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

export const list = query({
  args: {
    userId: v.id("users"),
    unreadOnly: v.optional(v.boolean()),
    limit: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    const limit = args.limit ?? 50;
    let query = ctx.db
      .query("notifications")
      .withIndex("by_user", (q) => q.eq("userId", args.userId))
      .order("desc");

    const notifications = await query.take(limit);

    if (args.unreadOnly) {
      return notifications.filter((n) => !n.readAt);
    }

    return notifications;
  },
});

export const getUnreadCount = query({
  args: { userId: v.id("users") },
  handler: async (ctx, args) => {
    const notifications = await ctx.db
      .query("notifications")
      .withIndex("by_user", (q) => q.eq("userId", args.userId))
      .collect();
    return notifications.filter((n) => !n.readAt).length;
  },
});

export const create = mutation({
  args: {
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
    priority: v.optional(
      v.union(v.literal("low"), v.literal("normal"), v.literal("high"), v.literal("urgent"))
    ),
    data: v.optional(v.any()),
    sourceType: v.optional(v.string()),
    sourceId: v.optional(v.string()),
    expiresAt: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    return await ctx.db.insert("notifications", {
      ...args,
      priority: args.priority ?? "normal",
    });
  },
});

export const markAsRead = mutation({
  args: { id: v.id("notifications") },
  handler: async (ctx, args) => {
    await ctx.db.patch(args.id, { readAt: Date.now() });
  },
});

export const markAllAsRead = mutation({
  args: { userId: v.id("users") },
  handler: async (ctx, args) => {
    const notifications = await ctx.db
      .query("notifications")
      .withIndex("by_user", (q) => q.eq("userId", args.userId))
      .collect();

    const unread = notifications.filter((n) => !n.readAt);
    for (const notification of unread) {
      await ctx.db.patch(notification._id, { readAt: Date.now() });
    }

    return unread.length;
  },
});

export const dismiss = mutation({
  args: { id: v.id("notifications") },
  handler: async (ctx, args) => {
    await ctx.db.patch(args.id, { dismissedAt: Date.now() });
  },
});

export const remove = mutation({
  args: { id: v.id("notifications") },
  handler: async (ctx, args) => {
    await ctx.db.delete(args.id);
  },
});
