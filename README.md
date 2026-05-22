# nzrt-x402

Pay-per-query knowledge API for the NZRT Network vault — powered by [x402](https://x402.org) micropayments on Base.

Live at **https://api.nzrtnetwork.com**

## What it is

An AI agent calls an endpoint. The server returns HTTP 402 with payment details. The agent pays $0.001 USDC on-chain via the x402 facilitator, retries with proof, and gets the knowledge back. No API keys. No subscriptions. Agent pays at request time.

```
AI agent  →  GET /ncl/search?q=users
          ←  402 X-Payment-Required: <base64>
          →  pay $0.001 USDC on Base
          →  retry with X-Payment header
          ←  200 { results: [...] }
```

## Endpoints

| Path | Description | Auth |
|------|-------------|------|
| `GET /health` | Status, network, domains | Free |
| `GET /wiki/search?q=` | Full-text search across all vault | x402 |
| `GET /wiki/note?section=&file=` | Fetch any vault note | x402 |
| `GET /togaf/search?q=` | Search TOGAF / EA content | x402 |
| `GET /togaf/phase?n=&doc=` | Fetch TOGAF ADM phase doc | x402 |
| `GET /<domain>/search?q=` | Search a specific domain | x402 |
| `GET /<domain>/note?section=&file=` | Fetch note from a domain | x402 |

**Available domains:** `ncl` `dol` `wor` `git` `inf` `llm` `bch` `k8s`

## Knowledge Domains

| Domain | Code | Content |
|--------|------|---------|
| `bch` | 000BCH | x402 protocol, USDC, Base network, wallet setup, smart contracts |
| `dol` | 000DOL | Dolibarr ERP: CRM, invoicing, HR, products, agent REST API patterns |
| `git` | 000GIT | GitHub repos, workflows, deploy pipelines, agent scripts |
| `inf` | 000INF | Hosting, subdomains, cPanel, Tailscale VPN, security architecture |
| `k8s` | 000K8S | Minikube, Kagent orchestration, agent deployments |
| `llm` | 000LLM | AI agent roles, task definitions, MCP servers, workflows |
| `ncl` | 000NCL | Nextcloud: setup, agent folders, WebDAV, OCS API, user management |
| `wor` | 000WOR | WordPress: ICS site, NCS site, REST API, Kadence, WP agent patterns |

Each domain has folder-level `section=` values — see `https://api.nzrtnetwork.com/<domain>/` for the full section reference.

## Example

```bash
# Search all vault content
curl -i "https://api.nzrtnetwork.com/app/wiki/search?q=x402"

# Fetch a specific note (after x402 payment)
curl -i "https://api.nzrtnetwork.com/app/bch/note?section=01+-+Core+Concepts&file=Ethereum+%26+Base+Network"

# Check API status (free)
curl "https://api.nzrtnetwork.com/app/health"
```

## Repo structure

```
python-resource-server/   Flask x402 resource server (deployed to Hoopla cPanel)
mcp-server/               TypeScript MCP client (Claude Desktop integration)
resource-server/          TypeScript resource server (experimental)
```

## Setup

### Python resource server

```bash
cd python-resource-server
pip install -r requirements.txt
cp .env.example .env   # fill in values
python app.py
```

`.env` values needed:
```
VAULT_PATH=/path/to/obsidian/vault
EVM_ADDRESS=0x...          # receiving wallet
FACILITATOR_URL=https://x402.org/facilitator
NETWORK=eip155:84532       # Base Sepolia (testnet) or eip155:8453 (mainnet)
PRICE_PER_REQUEST=$0.001
```

### MCP server (Claude Desktop)

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
      "args": ["/path/to/nzrt-x402/mcp-server/dist/index.js"],
      "env": {
        "EVM_PRIVATE_KEY": "0x...",
        "RESOURCE_SERVER_URL": "https://api.nzrtnetwork.com/app"
      }
    }
  }
}
```

The MCP server auto-pays x402 when Claude calls `get_wiki_note` or `search_wiki`.

## Network

- Testnet: Base Sepolia (`eip155:84532`) — current
- Mainnet: Base (`eip155:8453`) — migration in progress

Switch `.env` values to go live:
```
NETWORK=eip155:8453
USDC_CONTRACT=0x833589fcd6edb6e08f4c7c32d4f71b54bda02913
```

## Pricing

`$0.001 USDC` per request. Set via `PRICE_PER_REQUEST` in `.env` — do **not** use cPanel environment variables (lswsgi shell-expands `$` in values).

## Contact

nathan@nzrtnetwork.com  
[nzrtnetwork.com](https://nzrtnetwork.com)
