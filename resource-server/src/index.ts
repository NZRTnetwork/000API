import { config } from "dotenv";
import express from "express";
import { paymentMiddleware, x402ResourceServer } from "@x402/express";
import { ExactEvmScheme } from "@x402/evm/exact/server";
import { HTTPFacilitatorClient } from "@x402/core/server";
import wikiRouter from "./routes/wiki.js";

config();

const evmAddress = process.env.EVM_ADDRESS as `0x${string}`;
if (!evmAddress) {
  console.error("❌ EVM_ADDRESS required — wallet that receives payments");
  process.exit(1);
}

const facilitatorUrl = process.env.FACILITATOR_URL || "https://x402.org/facilitator";
const network = (process.env.NETWORK || "eip155:84532") as `${string}:${string}`; // Base Sepolia testnet
const price = process.env.PRICE_PER_REQUEST || "$0.001";
const port = parseInt(process.env.PORT || "3402", 10);

const facilitatorClient = new HTTPFacilitatorClient({ url: facilitatorUrl });
const resourceServer = new x402ResourceServer(facilitatorClient).register(
  network,
  new ExactEvmScheme(),
);

const app = express();
app.use(express.json());

// Free health check
app.get("/health", (_req, res) => {
  res.json({
    status: "ok",
    network,
    price,
    facilitator: facilitatorUrl,
    endpoints: ["GET /wiki/:section/:file (paid)", "GET /wiki/search?q= (paid)", "GET /health (free)"],
  });
});

// Global payment middleware — matches /wiki/* before routes run
app.use(
  paymentMiddleware(
    {
      "GET /wiki/*": {
        accepts: [
          {
            scheme: "exact",
            price,
            network,
            payTo: evmAddress,
          },
        ],
        description: "NZRT knowledge vault — Obsidian note content",
        mimeType: "application/json",
      },
    },
    resourceServer,
  ),
);

app.use("/wiki", wikiRouter);

app.listen(port, () => {
  console.log(`🚀 NZRT x402 Resource Server running on http://localhost:${port}`);
  console.log(`   Network : ${network}`);
  console.log(`   Price   : ${price} USDC per request`);
  console.log(`   Wallet  : ${evmAddress}`);
  console.log(`   Test    : curl http://localhost:${port}/health`);
});
