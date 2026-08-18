// One-shot x402 buyer: makes a single paid request to the live API and prints the
// settlement tx. Run locally with your funded Base-mainnet wallet key — the key is
// read from EVM_PRIVATE_KEY at runtime and never stored.
//
//   cd mcp-server
//   $env:EVM_PRIVATE_KEY="0x<your funded wallet key>"
//   node pay-once.mjs
//
// The wallet needs a little USDC on Base mainnet (gas is sponsored by CDP; no ETH needed).
import axios from "axios";
import { x402Client, wrapAxiosWithPayment } from "@x402/axios";
import { ExactEvmScheme } from "@x402/evm/exact/client";
import { privateKeyToAccount } from "viem/accounts";

const key = process.env.EVM_PRIVATE_KEY;
if (!key) { console.error("Set EVM_PRIVATE_KEY first."); process.exit(1); }
const baseURL = process.env.RESOURCE_SERVER_URL || "https://api.nzrtnetwork.com/app";

const signer = privateKeyToAccount(key);
const client = new x402Client();
client.register("eip155:*", new ExactEvmScheme(signer));   // Base mainnet = eip155:8453
const api = wrapAxiosWithPayment(axios.create({ baseURL }), client);

console.error(`Payer:    ${signer.address}`);
console.error(`Resource: ${baseURL}`);
console.error(`Paying $0.001 USDC on Base mainnet ...\n`);

try {
  const r = await api.get("/wiki/search", { params: { q: "x402" } });
  console.log("HTTP", r.status);
  const ph = r.headers["x-payment-response"] || r.headers["payment-response"];
  if (ph) {
    const p = JSON.parse(Buffer.from(ph, "base64").toString());
    console.log(`SETTLED  success=${p.success}  network=${p.network}  payer=${p.payer}`);
    console.log(`tx:       ${p.transaction}`);
    console.log(`Basescan: https://basescan.org/tx/${p.transaction}`);
  } else {
    console.log("No payment-response header. Headers:", Object.keys(r.headers).join(", "));
  }
  console.log("\nData:", JSON.stringify(r.data).slice(0, 300));
} catch (e) {
  console.error("ERROR", e?.response?.status ?? "", e?.response?.data ?? e.message);
}
