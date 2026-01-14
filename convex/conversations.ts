import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

export const list = query({
  args: {
    userId: v.optional(v.id("users")),
    clientSessionId: v.optional(v.string()),
    limit: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    const limit = args.limit ?? 50;

    if (args.userId) {
      return await ctx.db
        .query("conversations")
        .withIndex("by_user", (q) => q.eq("userId", args.userId))
        .order("desc")
        .take(limit);
    }

    if (args.clientSessionId) {
      return await ctx.db
        .query("conversations")
        .withIndex("by_session", (q) => q.eq("clientSessionId", args.clientSessionId))
        .order("desc")
        .take(limit);
    }

    return [];
  },
});

export const get = query({
  args: { id: v.id("conversations") },
  handler: async (ctx, args) => {
    return await ctx.db.get(args.id);
  },
});

export const create = mutation({
  args: {
    userId: v.optional(v.id("users")),
    clientSessionId: v.optional(v.string()),
    title: v.optional(v.string()),
    modelPreset: v.optional(v.string()),
    modelConfig: v.optional(v.any()),
  },
  handler: async (ctx, args) => {
    return await ctx.db.insert("conversations", {
      userId: args.userId,
      clientSessionId: args.clientSessionId,
      title: args.title,
      modelPreset: args.modelPreset,
      modelConfig: args.modelConfig,
      status: "active",
      totalMessages: 0,
      totalUserMessages: 0,
    });
  },
});

export const update = mutation({
  args: {
    id: v.id("conversations"),
    title: v.optional(v.string()),
    summary: v.optional(v.string()),
    status: v.optional(v.union(v.literal("active"), v.literal("archived"), v.literal("closed"))),
    isArchived: v.optional(v.boolean()),
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

export const incrementMessageCount = mutation({
  args: {
    id: v.id("conversations"),
    isUserMessage: v.boolean(),
  },
  handler: async (ctx, args) => {
    const conversation = await ctx.db.get(args.id);
    if (!conversation) {
      throw new Error("Conversation not found");
    }

    await ctx.db.patch(args.id, {
      totalMessages: conversation.totalMessages + 1,
      totalUserMessages: args.isUserMessage
        ? conversation.totalUserMessages + 1
        : conversation.totalUserMessages,
      lastMessageAt: Date.now(),
    });
  },
});
