# Changelog

All notable changes to this project will be documented in this file.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

Changes not yet released live in `changelog.d/`, one file per change — see the README there for why, and `scripts/changelog.py` for what folds them in at release time.

## [0.2.2] — 2026-11-25

### Changed

- Refreshed dependencies (Renovate lock-file maintenance and package updates).

## [0.2.1] — 2026-11-19

### Changed

- Python 3.11 is now the minimum, so every install gets the patched dnspython 2.9.

- The shortlink redirect moved from Val Town, which is shutting down, to a Cloudflare Worker at https://go.tollbooth-dpyc.com, and new links use that address.
- A change to `worker/redirect.js` on main deploys it and checks an unknown slug gets the "Link Not Found" page. It needs the `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` repo secrets, and the Worker secret `NEON_SHORTLINKS_URL`.

- The MCP Registry listing carries a title (Tollbooth Shortlinks) and a link to https://cafe.tollbooth-dpyc.com/products/tollbooth-shortlinks.

### Fixed

- The "Link Not Found" page declares UTF-8, so its apostrophe renders instead of mojibake (`â€™`).

## [0.2.0] — 2026-10-21

### Changed

- The README now matches the code: deploy config is `fastmcp.json`, peers find the service through the Oracle (`default_oracle_client().resolve_service`) since `resolve_service_by_name` is gone, the redirect diagram shows Val Town doing the lookup, `SHORTLINK_REDIRECT_BASE` is documented, and the related-repo table lists goodearth, beesknees, roastify, ChartRemotely and tollbooth-web.

- Dependencies refreshed to current releases (mcp/fastmcp 1.26.0/3.4.7 → 2.3.0/4.1.0; frontend minor/patch). No service stays on old transitive versions.

## [0.1.0] — 2026-04-02

- feat: ephemeral word-based URL shortener for Tollbooth/DPYC OAuth flows — short, human-readable codes that expire on a 24h TTL with no tracking
- feat: val.town-hosted endpoint with Neon-backed storage (`NEON_SHORTLINKS_URL`)
- docs: README + Apache-2.0 LICENSE
- DPYC role: registered as a community **Advocate** (shared utility, unmonetized)
