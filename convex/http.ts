import { httpRouter } from "convex/server";
import { httpAction } from "./_generated/server";
import { api } from "./_generated/api";
import { auth } from "./auth";

const http = httpRouter();

auth.addHttpRoutes(http);

http.route({
  path: "/api/health",
  method: "GET",
  handler: httpAction(async () => {
    return new Response(
      JSON.stringify({
        status: "ok",
        timestamp: new Date().toISOString(),
        service: "convex",
      }),
      {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }
    );
  }),
});

http.route({
  path: "/api/v1/health",
  method: "GET",
  handler: httpAction(async (ctx) => {
    try {
      const healthData = {
        status: "healthy",
        timestamp: new Date().toISOString(),
        version: "2.0.0",
        database: "convex",
        services: {
          database: { status: "ok" },
        },
      };

      return new Response(JSON.stringify(healthData), {
        status: 200,
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*",
        },
      });
    } catch (error) {
      return new Response(
        JSON.stringify({
          status: "error",
          message: error instanceof Error ? error.message : "Unknown error",
        }),
        {
          status: 500,
          headers: { "Content-Type": "application/json" },
        }
      );
    }
  }),
});

http.route({
  path: "/api/v1/chat/quick-chat",
  method: "POST",
  handler: httpAction(async (ctx, request) => {
    try {
      const body = await request.json();
      const { query, conversation_id, client_session_id } = body;

      if (!query) {
        return new Response(
          JSON.stringify({ error: "Query is required" }),
          { status: 400, headers: { "Content-Type": "application/json" } }
        );
      }

      return new Response(
        JSON.stringify({
          answer: "This endpoint is being migrated to Convex. Please use the Convex React hooks for real-time functionality.",
          conversation_id: conversation_id || "temp-" + Date.now(),
          model: "convex-placeholder",
        }),
        {
          status: 200,
          headers: {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
          },
        }
      );
    } catch (error) {
      return new Response(
        JSON.stringify({ error: "Invalid request body" }),
        { status: 400, headers: { "Content-Type": "application/json" } }
      );
    }
  }),
});

http.route({
  path: "/api/v1/chat/quick-chat",
  method: "OPTIONS",
  handler: httpAction(async () => {
    return new Response(null, {
      status: 204,
      headers: {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
      },
    });
  }),
});

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, PATCH, DELETE, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization",
};

http.route({
  path: "/api/v1/deep-research",
  method: "OPTIONS",
  handler: httpAction(async () => new Response(null, { status: 204, headers: corsHeaders })),
});

http.route({
  path: "/api/v1/deep-research",
  method: "POST",
  handler: httpAction(async (ctx, request) => {
    try {
      const body = await request.json();
      const { query, externalId, researchDepth, maxSources, focusAreas, modelId, modelProvider, clientSessionId, metadata, tags } = body;

      if (!query) {
        return new Response(
          JSON.stringify({ error: { code: "MISSING_QUERY", message: "Field 'query' is required", status: 400 } }),
          { status: 400, headers: { "Content-Type": "application/json", ...corsHeaders } }
        );
      }

      const taskExternalId = externalId || crypto.randomUUID();
      
      const createArgs: Record<string, unknown> = {
        externalId: taskExternalId,
        query,
        researchDepth: researchDepth || "standard",
        maxSources: maxSources || 10,
        focusAreas: focusAreas || [],
        modelId: modelId || "default",
        metadata: metadata || {},
      };
      
      if (clientSessionId) {
        createArgs.clientSessionId = clientSessionId;
      }
      
      const taskId = await ctx.runMutation(api.deepResearch.create, createArgs as Parameters<typeof api.deepResearch.create>[1]);

      return new Response(
        JSON.stringify({
          task_id: taskExternalId,
          internal_id: taskId,
          status: "pending",
          message: "Research task created",
        }),
        { status: 202, headers: { "Content-Type": "application/json", ...corsHeaders } }
      );
    } catch (error) {
      console.error("Failed to create deep research task:", error);
      return new Response(
        JSON.stringify({ error: { code: "CREATE_ERROR", message: error instanceof Error ? error.message : "Failed to create task", status: 500 } }),
        { status: 500, headers: { "Content-Type": "application/json", ...corsHeaders } }
      );
    }
  }),
});

http.route({
  path: "/api/v1/deep-research/by-external-id",
  method: "OPTIONS",
  handler: httpAction(async () => new Response(null, { status: 204, headers: corsHeaders })),
});

http.route({
  path: "/api/v1/deep-research/by-external-id",
  method: "GET",
  handler: httpAction(async (ctx, request) => {
    try {
      const url = new URL(request.url);
      const externalId = url.searchParams.get("id");

      if (!externalId) {
        return new Response(
          JSON.stringify({ error: { code: "MISSING_ID", message: "Query parameter 'id' is required", status: 400 } }),
          { status: 400, headers: { "Content-Type": "application/json", ...corsHeaders } }
        );
      }

      const task = await ctx.runQuery(api.deepResearch.getByExternalId, { externalId });

      return new Response(
        JSON.stringify({ task }),
        { status: 200, headers: { "Content-Type": "application/json", ...corsHeaders } }
      );
    } catch (error) {
      console.error("Failed to get deep research task:", error);
      return new Response(
        JSON.stringify({ error: { code: "QUERY_ERROR", message: error instanceof Error ? error.message : "Failed to query task", status: 500 } }),
        { status: 500, headers: { "Content-Type": "application/json", ...corsHeaders } }
      );
    }
  }),
});

http.route({
  path: "/api/v1/deep-research/update",
  method: "OPTIONS",
  handler: httpAction(async () => new Response(null, { status: 204, headers: corsHeaders })),
});

http.route({
  path: "/api/v1/deep-research/update",
  method: "PATCH",
  handler: httpAction(async (ctx, request) => {
    try {
      const body = await request.json();
      const { externalId, ...updates } = body;

      if (!externalId) {
        return new Response(
          JSON.stringify({ error: { code: "MISSING_ID", message: "Field 'externalId' is required", status: 400 } }),
          { status: 400, headers: { "Content-Type": "application/json", ...corsHeaders } }
        );
      }

      const task = await ctx.runQuery(api.deepResearch.getByExternalId, { externalId });
      if (!task) {
        return new Response(
          JSON.stringify({ error: { code: "NOT_FOUND", message: "Task not found", status: 404 } }),
          { status: 404, headers: { "Content-Type": "application/json", ...corsHeaders } }
        );
      }

      if (updates.status === "running") {
        await ctx.runMutation(api.deepResearch.start, { id: task._id });
      } else if (updates.status === "completed" && updates.result) {
        await ctx.runMutation(api.deepResearch.complete, { id: task._id, result: updates.result });
      } else if (updates.status === "failed" && updates.error) {
        await ctx.runMutation(api.deepResearch.fail, { id: task._id, error: updates.error });
      } else if (updates.progressPercent !== undefined || updates.currentStep !== undefined) {
        await ctx.runMutation(api.deepResearch.updateProgress, {
          id: task._id,
          progressPercent: updates.progressPercent,
          currentStep: updates.currentStep,
          stepsCompleted: updates.stepsCompleted,
        });
      }

      return new Response(
        JSON.stringify({ success: true }),
        { status: 200, headers: { "Content-Type": "application/json", ...corsHeaders } }
      );
    } catch (error) {
      console.error("Failed to update deep research task:", error);
      return new Response(
        JSON.stringify({ error: { code: "UPDATE_ERROR", message: error instanceof Error ? error.message : "Failed to update task", status: 500 } }),
        { status: 500, headers: { "Content-Type": "application/json", ...corsHeaders } }
      );
    }
  }),
});

http.route({
  path: "/api/v1/projects/search",
  method: "OPTIONS",
  handler: httpAction(async () => new Response(null, { status: 204, headers: corsHeaders })),
});

http.route({
  path: "/api/v1/projects/search",
  method: "GET",
  handler: httpAction(async (ctx, request) => {
    try {
      const url = new URL(request.url);
      const query = url.searchParams.get("q") || "";
      const limitParam = url.searchParams.get("limit");
      const limit = limitParam ? Math.min(parseInt(limitParam, 10), 50) : 10;

      if (!query.trim()) {
        return new Response(
          JSON.stringify({ query: "", count: 0, results: [] }),
          { status: 200, headers: { "Content-Type": "application/json", ...corsHeaders } }
        );
      }

      const results = await ctx.runQuery(api.projects.search, { query, limit });

      return new Response(
        JSON.stringify({
          query,
          count: results.length,
          results: results.map((p: { symbol: string; name: string; coingeckoId?: string; description?: string }) => ({
            symbol: p.symbol,
            name: p.name,
            coingecko_id: p.coingeckoId,
            description: p.description,
          })),
        }),
        { status: 200, headers: { "Content-Type": "application/json", ...corsHeaders } }
      );
    } catch (error) {
      console.error("Failed to search projects:", error);
      return new Response(
        JSON.stringify({ error: { code: "SEARCH_ERROR", message: error instanceof Error ? error.message : "Failed to search", status: 500 } }),
        { status: 500, headers: { "Content-Type": "application/json", ...corsHeaders } }
      );
    }
  }),
});

export default http;
