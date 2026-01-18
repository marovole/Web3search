import { mutation } from "./_generated/server";
import { v } from "convex/values";

const SEED_PROJECTS = [
  { symbol: "BTC", name: "Bitcoin", coingeckoId: "bitcoin", description: "The first and largest cryptocurrency", blockchain: "bitcoin", categories: ["cryptocurrency", "store-of-value"] },
  { symbol: "ETH", name: "Ethereum", coingeckoId: "ethereum", description: "Decentralized platform for smart contracts", blockchain: "ethereum", categories: ["cryptocurrency", "smart-contracts", "defi"] },
  { symbol: "SOL", name: "Solana", coingeckoId: "solana", description: "High-performance blockchain for decentralized apps", blockchain: "solana", categories: ["cryptocurrency", "smart-contracts", "layer-1"] },
  { symbol: "BNB", name: "BNB", coingeckoId: "binancecoin", description: "Native token of the BNB Chain", blockchain: "bnb-chain", categories: ["cryptocurrency", "exchange-token"] },
  { symbol: "XRP", name: "XRP", coingeckoId: "ripple", description: "Digital payment protocol and cryptocurrency", blockchain: "ripple", categories: ["cryptocurrency", "payments"] },
  { symbol: "ADA", name: "Cardano", coingeckoId: "cardano", description: "Proof-of-stake blockchain platform", blockchain: "cardano", categories: ["cryptocurrency", "smart-contracts", "layer-1"] },
  { symbol: "DOGE", name: "Dogecoin", coingeckoId: "dogecoin", description: "Meme-inspired cryptocurrency", blockchain: "dogecoin", categories: ["cryptocurrency", "meme"] },
  { symbol: "AVAX", name: "Avalanche", coingeckoId: "avalanche-2", description: "Fast, low-cost smart contract platform", blockchain: "avalanche", categories: ["cryptocurrency", "smart-contracts", "layer-1"] },
  { symbol: "DOT", name: "Polkadot", coingeckoId: "polkadot", description: "Multi-chain network protocol", blockchain: "polkadot", categories: ["cryptocurrency", "interoperability", "layer-0"] },
  { symbol: "MATIC", name: "Polygon", coingeckoId: "matic-network", description: "Ethereum scaling solution", blockchain: "polygon", categories: ["cryptocurrency", "layer-2", "scaling"] },
  { symbol: "LINK", name: "Chainlink", coingeckoId: "chainlink", description: "Decentralized oracle network", blockchain: "ethereum", categories: ["cryptocurrency", "oracle", "defi"] },
  { symbol: "UNI", name: "Uniswap", coingeckoId: "uniswap", description: "Decentralized exchange protocol", blockchain: "ethereum", categories: ["cryptocurrency", "dex", "defi"] },
  { symbol: "SHIB", name: "Shiba Inu", coingeckoId: "shiba-inu", description: "Meme token ecosystem", blockchain: "ethereum", categories: ["cryptocurrency", "meme"] },
  { symbol: "LTC", name: "Litecoin", coingeckoId: "litecoin", description: "Peer-to-peer cryptocurrency", blockchain: "litecoin", categories: ["cryptocurrency", "payments"] },
  { symbol: "ATOM", name: "Cosmos", coingeckoId: "cosmos", description: "Internet of blockchains", blockchain: "cosmos", categories: ["cryptocurrency", "interoperability"] },
  { symbol: "ARB", name: "Arbitrum", coingeckoId: "arbitrum", description: "Ethereum Layer 2 scaling solution", blockchain: "arbitrum", categories: ["cryptocurrency", "layer-2", "scaling"] },
  { symbol: "OP", name: "Optimism", coingeckoId: "optimism", description: "Ethereum Layer 2 scaling solution", blockchain: "optimism", categories: ["cryptocurrency", "layer-2", "scaling"] },
  { symbol: "APT", name: "Aptos", coingeckoId: "aptos", description: "Layer 1 blockchain using Move language", blockchain: "aptos", categories: ["cryptocurrency", "layer-1"] },
  { symbol: "SUI", name: "Sui", coingeckoId: "sui", description: "Layer 1 blockchain for digital assets", blockchain: "sui", categories: ["cryptocurrency", "layer-1"] },
  { symbol: "NEAR", name: "NEAR Protocol", coingeckoId: "near", description: "Sharded, developer-friendly blockchain", blockchain: "near", categories: ["cryptocurrency", "layer-1"] },
];

export const seedProjects = mutation({
  args: {},
  handler: async (ctx) => {
    let inserted = 0;
    let skipped = 0;

    for (const project of SEED_PROJECTS) {
      const existing = await ctx.db
        .query("projects")
        .withIndex("by_symbol", (q) => q.eq("symbol", project.symbol))
        .first();

      if (!existing) {
        await ctx.db.insert("projects", {
          symbol: project.symbol,
          name: project.name,
          coingeckoId: project.coingeckoId,
          description: project.description,
          blockchain: project.blockchain,
          categories: project.categories,
          tags: [],
          firstSeen: Date.now(),
          lastUpdated: Date.now(),
        });
        inserted++;
      } else {
        skipped++;
      }
    }

    return { inserted, skipped, total: SEED_PROJECTS.length };
  },
});

export const clearProjects = mutation({
  args: {},
  handler: async (ctx) => {
    const projects = await ctx.db.query("projects").collect();
    for (const project of projects) {
      await ctx.db.delete(project._id);
    }
    return { deleted: projects.length };
  },
});
