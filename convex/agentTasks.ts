import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

const taskTypeValidator = v.union(
  v.literal("price_alert"),
  v.literal("risk_monitor"),
  v.literal("news_brief"),
  v.literal("portfolio_health"),
  v.literal("opportunity_finder"),
  v.literal("custom")
);

const taskStatusValidator = v.union(
  v.literal("active"),
  v.literal("paused"),
  v.literal("completed"),
  v.literal("failed"),
  v.literal("cancelled")
);

export const list = query({
  args: {
    userId: v.id("users"),
    status: v.optional(taskStatusValidator),
    limit: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    const limit = args.limit ?? 50;

    if (args.status) {
      return await ctx.db
        .query("agentTasks")
        .withIndex("by_user_status", (q) =>
          q.eq("userId", args.userId).eq("status", args.status!)
        )
        .order("desc")
        .take(limit);
    }

    return await ctx.db
      .query("agentTasks")
      .withIndex("by_user", (q) => q.eq("userId", args.userId))
      .order("desc")
      .take(limit);
  },
});

export const get = query({
  args: { id: v.id("agentTasks") },
  handler: async (ctx, args) => {
    return await ctx.db.get(args.id);
  },
});

export const create = mutation({
  args: {
    userId: v.id("users"),
    name: v.string(),
    description: v.optional(v.string()),
    type: taskTypeValidator,
    config: v.any(),
    schedule: v.optional(v.string()),
    expiresAt: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    return await ctx.db.insert("agentTasks", {
      userId: args.userId,
      name: args.name,
      description: args.description,
      type: args.type,
      status: "active",
      config: args.config,
      schedule: args.schedule,
      expiresAt: args.expiresAt,
      runCount: 0,
      successCount: 0,
      failureCount: 0,
    });
  },
});

export const update = mutation({
  args: {
    id: v.id("agentTasks"),
    name: v.optional(v.string()),
    description: v.optional(v.string()),
    config: v.optional(v.any()),
    schedule: v.optional(v.string()),
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

export const pause = mutation({
  args: { id: v.id("agentTasks") },
  handler: async (ctx, args) => {
    await ctx.db.patch(args.id, { status: "paused" });
  },
});

export const resume = mutation({
  args: { id: v.id("agentTasks") },
  handler: async (ctx, args) => {
    await ctx.db.patch(args.id, { status: "active" });
  },
});

export const remove = mutation({
  args: { id: v.id("agentTasks") },
  handler: async (ctx, args) => {
    const runs = await ctx.db
      .query("agentRuns")
      .withIndex("by_task", (q) => q.eq("taskId", args.id))
      .collect();

    for (const run of runs) {
      await ctx.db.delete(run._id);
    }

    await ctx.db.delete(args.id);
  },
});

export const getRuns = query({
  args: {
    taskId: v.id("agentTasks"),
    limit: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    const limit = args.limit ?? 20;
    return await ctx.db
      .query("agentRuns")
      .withIndex("by_task", (q) => q.eq("taskId", args.taskId))
      .order("desc")
      .take(limit);
  },
});

export const createRun = mutation({
  args: {
    taskId: v.id("agentTasks"),
    userId: v.id("users"),
    triggeredBy: v.union(
      v.literal("schedule"),
      v.literal("manual"),
      v.literal("condition"),
      v.literal("webhook")
    ),
    input: v.optional(v.any()),
  },
  handler: async (ctx, args) => {
    const runId = await ctx.db.insert("agentRuns", {
      taskId: args.taskId,
      userId: args.userId,
      status: "running",
      startedAt: Date.now(),
      triggeredBy: args.triggeredBy,
      input: args.input,
    });

    const task = await ctx.db.get(args.taskId);
    if (task) {
      await ctx.db.patch(args.taskId, {
        runCount: task.runCount + 1,
        lastRunAt: Date.now(),
      });
    }

    return runId;
  },
});

export const completeRun = mutation({
  args: {
    id: v.id("agentRuns"),
    output: v.any(),
    tokensUsed: v.optional(v.number()),
    apiCallsMade: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    const run = await ctx.db.get(args.id);
    if (!run) {
      throw new Error("Run not found");
    }

    const completedAt = Date.now();
    await ctx.db.patch(args.id, {
      status: "completed",
      output: args.output,
      completedAt,
      durationMs: completedAt - run.startedAt,
      tokensUsed: args.tokensUsed,
      apiCallsMade: args.apiCallsMade,
    });

    const task = await ctx.db.get(run.taskId);
    if (task) {
      await ctx.db.patch(run.taskId, {
        successCount: task.successCount + 1,
      });
    }
  },
});

export const failRun = mutation({
  args: {
    id: v.id("agentRuns"),
    errorMessage: v.string(),
    errorCode: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    const run = await ctx.db.get(args.id);
    if (!run) {
      throw new Error("Run not found");
    }

    const completedAt = Date.now();
    await ctx.db.patch(args.id, {
      status: "failed",
      errorMessage: args.errorMessage,
      errorCode: args.errorCode,
      completedAt,
      durationMs: completedAt - run.startedAt,
    });

    const task = await ctx.db.get(run.taskId);
    if (task) {
      await ctx.db.patch(run.taskId, {
        failureCount: task.failureCount + 1,
      });
    }
  },
});
