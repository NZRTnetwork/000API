# nzrt-x402

Pay-per-query access to the NZRT knowledge vault — [x402](https://x402.org) micropayments on Base mainnet. Includes an MCP server for Claude Desktop.

Live at **https://api.nzrtnetwork.com**

## What it is

An AI agent calls an endpoint. The server returns HTTP 402 with payment details. The agent pays $0.005 USDC on Base, retries with proof, and gets the knowledge back. No account. No API key. No subscription. Agent pays at request time.

```
AI agent  →  GET /app/ncl/search?q=users
          ←  402 X-Payment-Required: <base64>
          →  pay $0.005 USDC on Base
          →  retry with X-Payment header
          ←  200 { results: [...] }
```

## Pricing

$0.005 USDC per request, settled on Base mainnet (eip155:8453).

## Endpoints

| Path | Description | Auth |
|------|-------------|------|
| `GET /app/health` | Status, network, price | Free |
| `GET /app/wiki/search?q=` | Full-text search across all vault | x402 |
| `GET /app/wiki/note?section=&file=` | Fetch any vault note | x402 |
| `GET /app/<domain>/search?q=` | Search a specific domain | x402 |
| `GET /app/<domain>/note?section=&file=` | Fetch note from a domain | x402 |

## Knowledge Topics

| Topic | Code | Content |
|--------|------|---------|
| `bch` | 000BCH | x402 protocol, USDC, Base network, wallet setup, smart contracts |
| `dol` | 000DOL | Dolibarr ERP: CRM, invoicing, HR, products, agent REST API patterns |
| `git` | 000GIT | GitHub repos, workflows, deploy pipelines, agent scripts |
| `k8s` | 000K8S | Minikube, Kagent orchestration, agent deployments |
| `ncl` | 000NCL | Nextcloud: setup, agent folders, WebDAV, OCS API, user management |
| `wor` | 000WOR | WordPress: ICS site, NCS site, REST API, Kadence, WP agent patterns |

Each topic exposes folder-level `section=` values — see `https://api.nzrtnetwork.com/<domain>/` for the section reference.

## Example

```bash
# Search all vault content
curl -i "https://api.nzrtnetwork.com/app/wiki/search?q=x402"

# Fetch a specific note (after x402 payment)
curl -i "https://api.nzrtnetwork.com/app/bch/note?section=01+-+Core+Concepts&file=Ethereum+%26+Base+Network"

# Check API status (free)
curl "https://api.nzrtnetwork.com/app/health"
```

## MCP server (Claude Desktop)

The agent pays each query automatically from its own wallet — no account, no API key. It exposes two tools: `search_wiki` and `get_wiki_note`.

```bash
cd mcp-server
npm install
npm run build
```

Add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "nzrt-wiki": {
      "command": "node",
      "args": ["/path/to/mcp-server/dist/index.js"],
      "env": { "EVM_PRIVATE_KEY": "0x<your-wallet-key>" }
    }
  }
}
```

The wallet must hold USDC on Base mainnet; each query settles $0.005.

## Contact

nathan@nzrtnetwork.com  
[nzrtnetwork.com](https://nzrtnetwork.com)
