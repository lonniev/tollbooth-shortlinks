# Tollbooth Shortlinks

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Version](https://img.shields.io/badge/version-0.1.0-blue)](https://github.com/lonniev/tollbooth-shortlinks)
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
Val Town HTTP handler does the 302 redirect with zero interstitial.

## How It Works

```
MCP Server                    Shortlinks MCP              Val Town
    |                              |                         |
    |-- create_shortlink(url) ---->|                         |
    |<-- brave-otter-finds-gold ---|                         |
    |                              |                         |
    |  (patron clicks short URL)   |                         |
    |                              |    GET /brave-otter-..  |
    |                              |<------------------------|
    |                              |    Neon lookup           |
    |                              |-- 302 redirect -------->|
    |                              |                         |
    |        (24h later)           |                         |
    |                              |  link expires silently   |
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
export NEON_SHORTLINKS_URL="postgres://user:pass@ep-xyz.us-east-2.aws.neon.tech/shortlinks"
python -c "from server import mcp; mcp.run()"
```

## Deploy to FastMCP Horizon

The `.fastmcp.yaml` at the repo root is ready for `fastmcp deploy`.

## DPYC Identity

Tollbooth Shortlinks is registered as an **Advocate** in the DPYC Honor Chain.
Peer MCP servers discover its URL via registry lookup:

```python
from tollbooth import resolve_service_by_name

shortlinks_url = resolve_service_by_name("tollbooth-shortlinks")
redirect_base  = resolve_service_by_name("tollbooth-shortlinks-redirect")
```

## Related Repos

The Tollbooth DPYC™ ecosystem:

| Repo | Role |
|------|------|
| [tollbooth-dpyc](https://github.com/lonniev/tollbooth-dpyc) | The wheel -- operator-side credit ledger, BTCPay client, tool gating, constraint engine |
| [tollbooth-authority](https://github.com/lonniev/tollbooth-authority) | The institution -- fee collection, Schnorr signing, purchase certification |
| [dpyc-oracle](https://github.com/lonniev/dpyc-oracle) | The oracle -- Honor Chain governance, membership, ban elections |
| [dpyc-community](https://github.com/lonniev/dpyc-community) | The registry -- governance data, operator catalog, community rules |
| [schwab-mcp](https://github.com/lonniev/schwab-mcp) | Charles Schwab brokerage MCP -- trading, quotes, portfolio access |
| [excalibur-mcp](https://github.com/lonniev/excalibur-mcp) | eXcalibur -- formatted posting to X (Twitter) |
| [thebrain-mcp](https://github.com/lonniev/thebrain-mcp) | Personal Brain MCP -- thought graphs, knowledge management |
| [tollbooth-sample](https://github.com/lonniev/tollbooth-sample) | Reference operator -- weather API with full Tollbooth wiring |
| **tollbooth-shortlinks** (this repo) | Community utility -- ephemeral short URLs for OAuth flows |
| [tollbooth-oauth2-collector](https://github.com/lonniev/tollbooth-oauth2-collector) | OAuth2 callback collector -- browser-based token exchange |
| [pricing-studio](https://github.com/lonniev/pricing-studio) | macOS/iOS app -- operator dashboard and pricing model editor |

## License

Apache-2.0. See [LICENSE](LICENSE) for details.
