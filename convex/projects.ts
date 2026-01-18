import { query, mutation } from "./_generated/server";
import { v } from "convex/values";

export const list = query({
  args: {
    limit: v.optional(v.number()),
    filters: v.optional(v.array(v.object({
      field: v.string(),
      op: v.string(),
      value: v.any(),
    }))),
    orFilters: v.optional(v.array(v.object({
      field: v.string(),
      op: v.string(),
      value: v.any(),
    }))),
    orderBy: v.optional(v.object({
      field: v.string(),
      order: v.union(v.literal("asc"), v.literal("desc")),
    })),
  },
  handler: async (ctx, args) => {
    const limit = args.limit ?? 50;
    let results = await ctx.db.query("projects").take(limit * 10);

    if (args.orFilters && args.orFilters.length > 0) {
      results = results.filter((project) => {
        return args.orFilters!.some((filter) => {
          const fieldValue = project[filter.field as keyof typeof project];
          if (fieldValue === undefined || fieldValue === null) return false;
          
          const searchValue = String(filter.value).toLowerCase();
          const projectValue = String(fieldValue).toLowerCase();
          
          switch (filter.op) {
            case "ilike":
              return projectValue.includes(searchValue.replace(/%/g, ""));
            case "eq":
              return projectValue === searchValue;
            default:
              return false;
          }
        });
      });
    }

    if (args.filters && args.filters.length > 0) {
      results = results.filter((project) => {
        return args.filters!.every((filter) => {
          const fieldValue = project[filter.field as keyof typeof project];
          if (fieldValue === undefined) return false;
          
          switch (filter.op) {
            case "eq":
              return fieldValue === filter.value;
            case "neq":
              return fieldValue !== filter.value;
            default:
              return true;
          }
        });
      });
    }

    if (args.orderBy) {
      results.sort((a, b) => {
        const aVal = a[args.orderBy!.field as keyof typeof a];
        const bVal = b[args.orderBy!.field as keyof typeof b];
        if (aVal === undefined || aVal === null) return 1;
        if (bVal === undefined || bVal === null) return -1;
        const comparison = String(aVal).localeCompare(String(bVal));
        return args.orderBy!.order === "desc" ? -comparison : comparison;
      });
    }

    return results.slice(0, limit);
  },
});

export const get = query({
  args: { id: v.id("projects") },
  handler: async (ctx, args) => {
    return await ctx.db.get(args.id);
  },
});

export const getBySymbol = query({
  args: { symbol: v.string() },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("projects")
      .withIndex("by_symbol", (q) => q.eq("symbol", args.symbol.toUpperCase()))
      .first();
  },
});

export const search = query({
  args: {
    query: v.string(),
    limit: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    const limit = args.limit ?? 10;
    const searchTerm = args.query.toLowerCase();
    
    const allProjects = await ctx.db.query("projects").take(500);
    
    const filtered = allProjects.filter((project) => {
      const symbol = (project.symbol || "").toLowerCase();
      const name = (project.name || "").toLowerCase();
      return symbol.includes(searchTerm) || name.includes(searchTerm);
    });

    filtered.sort((a, b) => {
      const aSymbol = (a.symbol || "").toLowerCase();
      const bSymbol = (b.symbol || "").toLowerCase();
      const aExact = aSymbol === searchTerm ? 0 : 1;
      const bExact = bSymbol === searchTerm ? 0 : 1;
      if (aExact !== bExact) return aExact - bExact;
      
      const aStarts = aSymbol.startsWith(searchTerm) ? 0 : 1;
      const bStarts = bSymbol.startsWith(searchTerm) ? 0 : 1;
      return aStarts - bStarts;
    });

    return filtered.slice(0, limit);
  },
});

export const create = mutation({
  args: {
    symbol: v.string(),
    name: v.string(),
    coingeckoId: v.optional(v.string()),
    description: v.optional(v.string()),
    website: v.optional(v.string()),
    blockchain: v.optional(v.string()),
    categories: v.optional(v.array(v.string())),
    tags: v.optional(v.array(v.string())),
  },
  handler: async (ctx, args) => {
    return await ctx.db.insert("projects", {
      symbol: args.symbol.toUpperCase(),
      name: args.name,
      coingeckoId: args.coingeckoId,
      description: args.description,
      website: args.website,
      blockchain: args.blockchain,
      categories: args.categories,
      tags: args.tags,
      firstSeen: Date.now(),
      lastUpdated: Date.now(),
    });
  },
});

export const upsert = mutation({
  args: {
    symbol: v.string(),
    name: v.string(),
    coingeckoId: v.optional(v.string()),
    description: v.optional(v.string()),
    website: v.optional(v.string()),
    blockchain: v.optional(v.string()),
    categories: v.optional(v.array(v.string())),
    tags: v.optional(v.array(v.string())),
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("projects")
      .withIndex("by_symbol", (q) => q.eq("symbol", args.symbol.toUpperCase()))
      .first();

    if (existing) {
      await ctx.db.patch(existing._id, {
        name: args.name,
        coingeckoId: args.coingeckoId ?? existing.coingeckoId,
        description: args.description ?? existing.description,
        website: args.website ?? existing.website,
        blockchain: args.blockchain ?? existing.blockchain,
        categories: args.categories ?? existing.categories,
        tags: args.tags ?? existing.tags,
        lastUpdated: Date.now(),
      });
      return existing._id;
    }

    return await ctx.db.insert("projects", {
      symbol: args.symbol.toUpperCase(),
      name: args.name,
      coingeckoId: args.coingeckoId,
      description: args.description,
      website: args.website,
      blockchain: args.blockchain,
      categories: args.categories,
      tags: args.tags,
      firstSeen: Date.now(),
      lastUpdated: Date.now(),
    });
  },
});
