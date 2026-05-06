import axios from "axios";
import { x402Client, wrapAxiosWithPayment } from "@x402/axios";
import { ExactEvmScheme } from "@x402/evm/exact/client";
import { privateKeyToAccount } from "viem/accounts";

const privateKey = "0x2551920cf038fe63b34a4fbe9c78c5166e4338102448086c01742b52def7f86d";
const baseURL = "http://localhost:3402";

const signer = privateKeyToAccount(privateKey);
console.log("Paying address:", signer.address);

const client = new x402Client();
client.register("eip155:*", new ExactEvmScheme(signer));

const raw = axios.create({ baseURL });

// Debug: see raw 402 before wrapper intercepts
raw.interceptors.response.use(
  (r) => r,
  (err) => {
    console.log("[DEBUG raw] status:", err?.response?.status);
    const hdr = err?.response?.headers?.["payment-required"];
    console.log("[DEBUG raw] PAYMENT-REQUIRED:", hdr ? hdr.slice(0, 80) + "..." : "MISSING");
    return Promise.reject(err);
  }
);

const api = wrapAxiosWithPayment(raw, client);

console.log("Calling /wiki/search?q=DeFi ...");
try {
  const res = await api.get("/wiki/search?q=DeFi");
  console.log("SUCCESS:", JSON.stringify(res.data, null, 2));
} catch (err) {
  console.error("FAIL:", err.message);
}
