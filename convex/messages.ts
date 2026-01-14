import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

export const list = query({
  args: {
    conversationId: v.id("conversations"),
    limit: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    const limit = args.limit ?? 100;
    return await ctx.db
      .query("messages")
      .withIndex("by_conversation", (q) => q.eq("conversationId", args.conversationId))
      .order("asc")
      .take(limit);
  },
});

export const getRecent = query({
  args: {
    conversationId: v.id("conversations"),
    limit: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    const limit = args.limit ?? 20;
    const messages = await ctx.db
      .query("messages")
      .withIndex("by_conversation", (q) => q.eq("conversationId", args.conversationId))
      .order("desc")
      .take(limit);
    return messages.reverse();
  },
});

export const get = query({
  args: { id: v.id("messages") },
  handler: async (ctx, args) => {
    return await ctx.db.get(args.id);
  },
});

export const send = mutation({
  args: {
    conversationId: v.id("conversations"),
    role: v.union(v.literal("system"), v.literal("user"), v.literal("assistant"), v.literal("tool")),
    content: v.string(),
    userId: v.optional(v.id("users")),
    model: v.optional(v.string()),
    metadata: v.optional(v.any()),
  },
  handler: async (ctx, args) => {
    const messageId = await ctx.db.insert("messages", {
      conversationId: args.conversationId,
      role: args.role,
      content: args.content,
      userId: args.userId,
      model: args.model,
      metadata: args.metadata,
      status: "completed",
      isFinal: true,
    });

    const conversation = await ctx.db.get(args.conversationId);
    if (conversation) {
      await ctx.db.patch(args.conversationId, {
        totalMessages: conversation.totalMessages + 1,
        totalUserMessages:
          args.role === "user"
            ? conversation.totalUserMessages + 1
            : conversation.totalUserMessages,
        lastMessageAt: Date.now(),
      });
    }

    return messageId;
  },
});

export const startStreaming = mutation({
  args: {
    conversationId: v.id("conversations"),
    role: v.union(v.literal("assistant"), v.literal("tool")),
    model: v.optional(v.string()),
    metadata: v.optional(v.any()),
  },
  handler: async (ctx, args) => {
    return await ctx.db.insert("messages", {
      conversationId: args.conversationId,
      role: args.role,
      content: "",
      model: args.model,
      metadata: args.metadata,
      status: "streaming",
      isFinal: false,
    });
  },
});

export const appendContent = mutation({
  args: {
    id: v.id("messages"),
    content: v.string(),
  },
  handler: async (ctx, args) => {
    const message = await ctx.db.get(args.id);
    if (!message) {
      throw new Error("Message not found");
    }
    await ctx.db.patch(args.id, {
      content: (message.content ?? "") + args.content,
    });
  },
});

export const finishStreaming = mutation({
  args: {
    id: v.id("messages"),
    tokenCountPrompt: v.optional(v.number()),
    tokenCountCompletion: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    await ctx.db.patch(args.id, {
      status: "completed",
      isFinal: true,
      tokenCountPrompt: args.tokenCountPrompt,
      tokenCountCompletion: args.tokenCountCompletion,
    });

    const message = await ctx.db.get(args.id);
    if (message) {
      const conversation = await ctx.db.get(message.conversationId);
      if (conversation) {
        await ctx.db.patch(message.conversationId, {
          totalMessages: conversation.totalMessages + 1,
          lastMessageAt: Date.now(),
        });
      }
    }
  },
});

export const markFailed = mutation({
  args: {
    id: v.id("messages"),
    errorMessage: v.string(),
  },
  handler: async (ctx, args) => {
    await ctx.db.patch(args.id, {
      status: "failed",
      errorMessage: args.errorMessage,
    });
  },
});
