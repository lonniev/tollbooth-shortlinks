# Tollbooth Shortlinks

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/python-3.10+-green)](https://python.org)

**Don't Pester Your Customer™** (DPYC™) — Ephemeral, human-friendly short URLs for the Tollbooth ecosystem.

> *The metaphors in this project are drawn with admiration from* The Phantom Tollbooth *by Norton Juster, illustrated by Jules Feiffer (1961). Milo, Tock, the Tollbooth, Dictionopolis, and Digitopolis are creations of Mr. Juster's extraordinary imagination. We just built the payment infrastructure.*

---

## Why This Exists

OAuth Authorization URLs are long, ugly, and hostile to copy-paste:

```
https://api.schwab.com/v1/oauth/authorize?client_id=abc123&redirect_uri=https%3A%2F%2F
fastmcp.cloud%2Foauth%2Fcallback%3Fserver_id%3D...&scope=...&response_type=code&state=...
```

Traditional link shorteners have become opinionated. They inject interstitial
pages, track clicks, require accounts, gate features behind paywalls, or
silently expire links on their own schedule. When an MCP server needs to hand
a patron a one-time URL for an OAuth dance, none of that belongs in the path.

Tollbooth Shortlinks is a **community utility** with no monetization. It turns
any URL into a memorable four-word phrase like `brave-otter-finds-gold`, stores
the mapping in Neon Postgres, and expires it after 24 hours. A companion
Cloudflare Worker does the 302 redirect with zero interstitial.

## How It Works

```
MCP Server / Patron          Shortlinks MCP        Neon        CF Worker
    |                              |                 |              |
    |-- create_shortlink(url) ---->|-- INSERT ------>|              |
    |<-- short_url ----------------|                 |              |
    |                              |                 |              |
    |-- GET /brave-otter-finds-gold ---------------------------->   |
    |                              |                 |<-- lookup ---|
    |<-- 302 redirect ----------------------------------------------|
    |                              |                 |              |
    |        (24h later)           |  expired rows are deleted      |
```

## Tools

| Tool | Description |
|------|-------------|
| `create_shortlink` | Store a URL, get back a memorable slug (or supply your own) |
| `resolve_shortlink` | Look up where a slug points without redirecting |
| `delete_shortlink` | Remove a shortlink before it expires |
| `shortlink_status` | Health check showing active link count and TTL |

All tools are **free** -- no credits, no npub, no Tollbooth ledger required.

## Install

```bash
pip install -e ".[dev]"
```

## Run Locally

```bash
export NEON_SHORTLINKS_URL="<your Neon connection string>"
# optional: the redirect host put in front of each slug (default https://go.tollbooth-dpyc.com)
export SHORTLINK_REDIRECT_BASE="https://go.tollbooth-dpyc.com"
python -c "from server import mcp; mcp.run()"
```

The redirect Worker in `worker/redirect.js` reads the same `NEON_SHORTLINKS_URL`, set as a Worker secret. A change to it on main deploys it (`.github/workflows/deploy-worker.yml`, which needs the `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` repo secrets).

## Deploy to Horizon

The `fastmcp.json` at the repo root is ready for `fastmcp deploy`.

## DPYC Identity

Tollbooth Shortlinks is registered as an **Advocate** in the DPYC Social Contract.
Peer MCP servers discover its URL by asking the Oracle, and `create_shortlink`
returns the full `short_url`, so a peer never needs the redirect host:

```python
from tollbooth.oracle_client import default_oracle_client

svc = await default_oracle_client().resolve_service(name="tollbooth-shortlinks")
shortlinks_url = (svc or {}).get("url", "")
```

Operators built on tollbooth-dpyc get this for free: `tollbooth.shortlinks.create_shortlink(url)`
does the lookup and the call, best-effort.

<!-- dpyc-family -->
## Part of Tollbooth DPYC™

This service is one of the Tollbooth DPYC™ family of MCP servers.
Browse them all in the [MCP catalog](https://cafe.tollbooth-dpyc.com/collections/mcps).
The [DPYC Oracle](https://dpyc-oracle.fastmcp.app/mcp) lists the live network with its free `list_services` tool.

## License

Apache-2.0. See [LICENSE](LICENSE) for details.
