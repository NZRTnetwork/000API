import axios from "axios";
import { x402Client, wrapAxiosWithPayment } from "@x402/axios";
import { ExactEvmScheme } from "@x402/evm/exact/client";
import { privateKeyToAccount } from "viem/accounts";

const privateKey = process.env.TEST_PRIVATE_KEY; // set TEST_PRIVATE_KEY in env; never commit a real key
const baseURL = "http://localhost:3402";

console.log("Building signer...");
const signer = privateKeyToAccount(privateKey);
console.log("Paying address:", signer.address);

const client = new x402Client();
client.register("eip155:*", new ExactEvmScheme(signer));

const api = wrapAxiosWithPayment(axios.create({ baseURL }), client);

console.log("Calling /wiki/search?q=DeFi ...");
try {
  const res = await api.get("/wiki/search?q=DeFi");
  console.log("SUCCESS:", JSON.stringify(res.data, null, 2));
} catch (err) {
  console.error("FAIL:", err.message);
  if (err.cause) console.error("CAUSE:", err.cause);
}
