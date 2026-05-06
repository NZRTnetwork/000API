import axios from "axios";
import { x402Client, wrapAxiosWithPayment } from "@x402/axios";
import { ExactEvmScheme } from "@x402/evm/exact/client";
import { privateKeyToAccount } from "viem/accounts";

export function buildPayingClient(privateKey: `0x${string}`, baseURL: string) {
  const signer = privateKeyToAccount(privateKey);
  const client = new x402Client();
  client.register("eip155:*", new ExactEvmScheme(signer));

  const api = wrapAxiosWithPayment(axios.create({ baseURL }), client);
  return { api, address: signer.address };
}
