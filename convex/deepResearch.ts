import { action, mutation, query } from "./_generated/server";
import { v } from "convex/values";

const researchStatusValidator = v.union(
  v.literal("pending"),
  v.literal("running"),
  v.literal("completed"),
  v.literal("failed"),
  v.literal("cancelled")
);

const researchDepthValidator = v.union(
  v.literal("quick"),
  v.literal("standard"),
  v.literal("comprehensive")
);

export const list = query({
  args: {
    userId: v.optional(v.id("users")),
    clientSessionId: v.optional(v.string()),
    status: v.optional(researchStatusValidator),
    limit: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    const limit = args.limit ?? 20;

    if (args.userId) {
      const tasks = await ctx.db
        .query("deepResearchTasks")
        .withIndex("by_user", (q) => q.eq("userId", args.userId))
        .order("desc")
        .take(limit);

      if (args.status) {
        return tasks.filter((t) => t.status === args.status);
      }
      return tasks;
    }

    if (args.clientSessionId) {
      const tasks = await ctx.db
        .query("deepResearchTasks")
        .withIndex("by_session", (q) => q.eq("clientSessionId", args.clientSessionId))
        .order("desc")
        .take(limit);

      if (args.status) {
        return tasks.filter((t) => t.status === args.status);
      }
      return tasks;
    }

    return [];
  },
});

export const get = query({
  args: { id: v.id("deepResearchTasks") },
  handler: async (ctx, args) => {
    return await ctx.db.get(args.id);
  },
});

export const create = mutation({
  args: {
    userId: v.optional(v.id("users")),
    clientSessionId: v.optional(v.string()),
    conversationId: v.optional(v.id("conversations")),
    query: v.string(),
    researchDepth: v.optional(researchDepthValidator),
    maxSources: v.optional(v.number()),
    focusAreas: v.optional(v.array(v.string())),
    modelId: v.optional(v.string()),
    modelProvider: v.optional(
      v.union(v.literal("qwen"), v.literal("deepseek"), v.literal("anthropic"), v.literal("openai"))
    ),
    metadata: v.optional(v.any()),
  },
  handler: async (ctx, args) => {
    return await ctx.db.insert("deepResearchTasks", {
      userId: args.userId,
      clientSessionId: args.clientSessionId,
      conversationId: args.conversationId,
      query: args.query,
      status: "pending",
      researchDepth: args.researchDepth ?? "standard",
      maxSources: args.maxSources ?? 10,
      focusAreas: args.focusAreas,
      modelId: args.modelId,
      modelProvider: args.modelProvider,
      progressPercent: 0,
      stepsCompleted: 0,
      totalSteps: 5,
      metadata: args.metadata,
    });
  },
});

export const start = mutation({
  args: { id: v.id("deepResearchTasks") },
  handler: async (ctx, args) => {
    await ctx.db.patch(args.id, {
      status: "running",
      startedAt: Date.now(),
      currentStep: "initializing",
    });
  },
});

export const updateProgress = mutation({
  args: {
    id: v.id("deepResearchTasks"),
    progressPercent: v.number(),
    currentStep: v.optional(v.string()),
    stepsCompleted: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    const updates: Record<string, unknown> = {
      progressPercent: args.progressPercent,
    };

    if (args.currentStep !== undefined) {
      updates.currentStep = args.currentStep;
    }
    if (args.stepsCompleted !== undefined) {
      updates.stepsCompleted = args.stepsCompleted;
    }

    await ctx.db.patch(args.id, updates);
  },
});

export const complete = mutation({
  args: {
    id: v.id("deepResearchTasks"),
    result: v.any(),
    summary: v.optional(v.string()),
    answer: v.optional(v.string()),
    sources: v.optional(v.array(v.any())),
    citations: v.optional(v.array(v.any())),
    tokensPrompt: v.optional(v.number()),
    tokensCompletion: v.optional(v.number()),
    costUsd: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    const task = await ctx.db.get(args.id);
    if (!task) {
      throw new Error("Task not found");
    }

    const completedAt = Date.now();
    await ctx.db.patch(args.id, {
      status: "completed",
      result: args.result,
      summary: args.summary,
      answer: args.answer,
      sources: args.sources,
      citations: args.citations,
      progressPercent: 100,
      stepsCompleted: task.totalSteps,
      currentStep: "completed",
      completedAt,
      durationMs: task.startedAt ? completedAt - task.startedAt : undefined,
      tokensPrompt: args.tokensPrompt,
      tokensCompletion: args.tokensCompletion,
      costUsd: args.costUsd,
    });
  },
});

export const fail = mutation({
  args: {
    id: v.id("deepResearchTasks"),
    errorCode: v.optional(v.string()),
    errorMessage: v.string(),
  },
  handler: async (ctx, args) => {
    const task = await ctx.db.get(args.id);
    if (!task) {
      throw new Error("Task not found");
    }

    const completedAt = Date.now();
    await ctx.db.patch(args.id, {
      status: "failed",
      errorCode: args.errorCode,
      errorMessage: args.errorMessage,
      completedAt,
      durationMs: task.startedAt ? completedAt - task.startedAt : undefined,
      retryCount: (task.retryCount ?? 0) + 1,
    });
  },
});

export const cancel = mutation({
  args: { id: v.id("deepResearchTasks") },
  handler: async (ctx, args) => {
    await ctx.db.patch(args.id, {
      status: "cancelled",
      completedAt: Date.now(),
    });
  },
});
