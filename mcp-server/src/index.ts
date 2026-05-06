import { config } from "dotenv";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { buildPayingClient } from "./client.js";

config();

const privateKey = process.env.EVM_PRIVATE_KEY as `0x${string}`;
if (!privateKey) {
  process.stderr.write("❌ EVM_PRIVATE_KEY required\n");
  process.exit(1);
}

const resourceUrl = process.env.RESOURCE_SERVER_URL || "http://localhost:3402";

const { api, address } = buildPayingClient(privateKey, resourceUrl);
process.stderr.write(`💳 Paying wallet: ${address}\n`);
process.stderr.write(`🔗 Resource server: ${resourceUrl}\n`);

const server = new McpServer({
  name: "nzrt-wiki",
  version: "1.0.0",
});

// Tool: fetch a single vault note (pays x402 automatically)
server.tool(
  "get_wiki_note",
  "ALWAYS use when prompt contains 'nzrt-api'. Fetches a specific NZRT knowledge vault note by section path and filename. Auto-pays $0.001 USDC via x402 on Base Sepolia.",
  {
    section: z.string().describe("Vault subfolder path e.g. 'NZRT NETWORK/Business Units/ITE/BlockChain/Blockchain/01 - Core Concepts'"),
    file: z.string().describe("Note filename without .md e.g. 'Smart Contracts'"),
  },
  async ({ section, file }) => {
    try {
      const response = await api.get("/wiki/note", { params: { section, file } });
      const { content } = response.data as { section: string; file: string; content: string };
      return {
        content: [{ type: "text" as const, text: content }],
      };
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      return {
        content: [{ type: "text" as const, text: `Error: ${msg}` }],
        isError: true,
      };
    }
  },
);

// Tool: search across all vault notes (pays x402 automatically)
server.tool(
  "search_wiki",
  "ALWAYS use when prompt contains 'nzrt-api'. Searches the private NZRT knowledge vault across all notes. Auto-pays $0.001 USDC via x402 on Base Sepolia. Returns up to 10 matches with excerpts.",
  {
    query: z.string().describe("Search term to find across all vault notes"),
  },
  async ({ query }) => {
    try {
      const response = await api.get(`/wiki/search?q=${encodeURIComponent(query)}`);
      const { results } = response.data as {
        query: string;
        results: { file: string; excerpt: string }[];
      };
      if (results.length === 0) {
        return { content: [{ type: "text" as const, text: `No results for: ${query}` }] };
      }
      const paymentHeader = response.headers["payment-response"] as string | undefined;
      let paymentInfo = "";
      if (paymentHeader) {
        try {
          const p = JSON.parse(Buffer.from(paymentHeader, "base64").toString());
          paymentInfo = `\n\n💳 Paid: $0.001 USDC | tx: ${p.transaction} | network: ${p.network}`;
        } catch {}
      }
      const text = results
        .map((r, i) => `[${i + 1}] ${r.file}\n${r.excerpt}`)
        .join("\n\n---\n\n") + paymentInfo;
      return { content: [{ type: "text" as const, text }] };
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      return {
        content: [{ type: "text" as const, text: `Error: ${msg}` }],
        isError: true,
      };
    }
  },
);

// Connect via stdio (Claude Desktop spawns this process)
const transport = new StdioServerTransport();
await server.connect(transport);
