"""Tollbooth Shortlinks — ephemeral, human-friendly short URLs.

Stores slug → URL mappings in Neon Postgres with a 24-hour TTL.
Slugs are generated as memorable word phrases (e.g. ``brave-otter-finds-gold``).

A companion Val Town HTTP val handles browser GET requests:
``GET /<slug>`` → Neon lookup → 302 redirect to the original URL.

Uses Neon's SQL-over-HTTP API via httpx — no asyncpg or C extensions.

DPYC Identity
~~~~~~~~~~~~~
This service is registered as an **Advocate** in the DPYC Honor Chain.
Peer MCP servers discover its URL via registry lookup
(``resolve_service_by_name("tollbooth-shortlinks")``).
The browser redirect URL is registered separately as
``resolve_service_by_name("tollbooth-shortlinks-redirect")``.
"""

from __future__ import annotations

import logging
import os
import random
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version
from typing import Any
from urllib.parse import urlparse

import httpx
from fastmcp import FastMCP

logger = logging.getLogger(__name__)

_TTL_SECONDS = 86_400  # 24 hours

# The service advertises its own version so deploy-verify can confirm which
# build is live. Without this, FastMCP reports the framework version instead,
# leaving the deployed sha unverifiable.
try:
    __version__ = _pkg_version("tollbooth-shortlinks")
except PackageNotFoundError:  # not pip-installed (e.g. running from source tree)
    __version__ = "0.1.0"

# ---------------------------------------------------------------------------
# Word-based slug generation
# ---------------------------------------------------------------------------

_ADJECTIVES = [
    "bold", "brave", "bright", "calm", "clever", "cool", "crisp", "dark",
    "eager", "fair", "fast", "fierce", "fine", "fond", "free", "fresh",
    "glad", "gold", "grand", "great", "green", "happy", "keen", "kind",
    "light", "lucky", "mild", "neat", "noble", "plain", "proud", "quick",
    "quiet", "rare", "red", "rich", "safe", "sharp", "shy", "silver",
    "sleek", "slim", "slow", "smart", "smooth", "soft", "steady", "still",
    "strong", "sunny", "sure", "sweet", "swift", "tall", "tame", "thin",
    "true", "vast", "warm", "white", "wide", "wild", "wise", "young",
]

_NOUNS = [
    "ant", "ape", "bass", "bat", "bear", "bee", "bird", "boar", "cat",
    "clam", "cod", "colt", "cow", "crab", "crow", "dart", "deer", "doe",
    "dog", "dove", "duck", "eagle", "eel", "elk", "elm", "fawn", "fish",
    "fly", "fox", "frog", "gem", "goat", "hawk", "hare", "hen", "hog",
    "horse", "jade", "jay", "kite", "lamb", "lark", "leaf", "lynx",
    "mare", "mink", "mole", "moth", "mule", "newt", "oak", "orca",
    "otter", "owl", "ox", "palm", "pear", "pine", "plum", "pony",
    "quail", "ram", "raven", "reed", "robin", "rose", "sage", "seal",
    "shrew", "slug", "snail", "snake", "star", "swan", "toad", "trout",
    "vine", "vole", "wasp", "whale", "wolf", "wren", "yak",
]

_VERBS = [
    "asks", "bakes", "bears", "bends", "bites", "blows", "brings",
    "builds", "burns", "calls", "carves", "casts", "chases", "claims",
    "climbs", "counts", "crafts", "crosses", "cuts", "digs", "draws",
    "drinks", "drops", "eats", "faces", "falls", "feeds", "fills",
    "finds", "flies", "folds", "follows", "forges", "gains", "gets",
    "gives", "goes", "grabs", "grows", "guards", "guides", "has",
    "hears", "helps", "hides", "hits", "holds", "hunts", "joins",
    "jumps", "keeps", "knows", "leads", "learns", "lifts", "likes",
    "lives", "loves", "makes", "maps", "marks", "meets", "mends",
    "moves", "needs", "opens", "owns", "packs", "paints", "picks",
    "plants", "plays", "pulls", "reads", "rides", "rings", "rolls",
    "runs", "saves", "sees", "seeks", "sends", "sews", "shows",
    "sings", "sits", "spins", "takes", "tells", "ties", "tips",
    "tops", "tries", "turns", "walks", "wants", "watches", "wins",
]


def _generate_slug() -> str:
    """Generate a memorable slug like ``brave-otter-finds-gold``."""
    return "-".join([
        random.choice(_ADJECTIVES),
        random.choice(_NOUNS),
        random.choice(_VERBS),
        random.choice(_NOUNS),
    ])


# ---------------------------------------------------------------------------
# MCP server
# ---------------------------------------------------------------------------

mcp = FastMCP(
    "Tollbooth Shortlinks",
    version=__version__,
    instructions=(
        "Tollbooth Shortlinks — ephemeral, human-friendly short URLs. "
        "This is a community utility with no monetization.\n\n"
        "## How It Works\n\n"
        "1. Call `create_shortlink` with any URL to get a memorable slug.\n"
        "2. Share `<redirect-base>/<slug>` with users — they are 302-redirected "
        "to the original URL instantly.\n"
        "3. Links expire automatically after 24 hours.\n\n"
        "## Tools\n\n"
        "- `create_shortlink` — Store a URL and get back a memorable slug.\n"
        "- `resolve_shortlink` — Look up where a slug points (without redirecting).\n"
        "- `delete_shortlink` — Remove a shortlink before it expires.\n"
        "- `shortlink_status` — Health check showing active link count and TTL."
    ),
)

# ---------------------------------------------------------------------------
# Neon SQL-over-HTTP helpers
# ---------------------------------------------------------------------------

_http_client: httpx.AsyncClient | None = None
_neon_endpoint: str | None = None
_schema_ensured = False


async def _get_client() -> httpx.AsyncClient:
    """Lazily create a persistent httpx client for Neon HTTP API."""
    global _http_client, _neon_endpoint, _schema_ensured

    if _http_client is None:
        database_url = os.environ.get("NEON_SHORTLINKS_URL")
        if not database_url:
            raise RuntimeError("NEON_SHORTLINKS_URL environment variable is required")

        parsed = urlparse(database_url)
        _neon_endpoint = f"https://{parsed.hostname}/sql"

        _http_client = httpx.AsyncClient(
            headers={
                "Neon-Connection-String": database_url,
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    if not _schema_ensured:
        _schema_ensured = True
        await _ensure_schema()

    return _http_client


async def _execute(query: str, params: list[Any] | None = None) -> dict[str, Any]:
    """Execute a SQL statement via Neon's HTTP API."""
    client = await _get_client()
    body = {"query": query, "params": params or []}
    resp = await client.post(_neon_endpoint, json=body)
    resp.raise_for_status()
    data = resp.json()

    if isinstance(data, dict) and "message" in data and "rows" not in data:
        raise RuntimeError(f"Neon SQL error: {data['message']}")

    return data


async def _ensure_schema():
    """Create the shortlinks table if it doesn't exist."""
    await _execute("""
        CREATE TABLE IF NOT EXISTS shortlinks (
            slug TEXT PRIMARY KEY,
            url TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)


async def _cleanup_expired():
    """Remove expired rows (older than TTL)."""
    await _execute(
        f"DELETE FROM shortlinks WHERE created_at < NOW() - INTERVAL '{_TTL_SECONDS} seconds'"
    )


# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def create_shortlink(url: str, slug: str | None = None) -> dict[str, Any]:
    """Create an ephemeral short URL that expires after 24 hours.

    Args:
        url: The target URL to redirect to.
        slug: Optional custom slug. If omitted, a memorable phrase is generated
              (e.g. ``brave-otter-finds-gold``).

    Returns:
        Dict with ``slug``, ``url``, and ``expires_in_seconds``.
    """
    try:
        await _cleanup_expired()

        chosen_slug = slug or _generate_slug()

        # Retry with a new slug on collision (generated slugs only)
        for attempt in range(5):
            try:
                await _execute(
                    "INSERT INTO shortlinks (slug, url) VALUES ($1, $2)",
                    [chosen_slug, url],
                )
                break
            except Exception:
                if slug:
                    return {"success": False, "error": f"Slug '{slug}' is already taken."}
                chosen_slug = _generate_slug()
        else:
            return {"success": False, "error": "Could not generate a unique slug."}

        redirect_base = os.environ.get(
            "SHORTLINK_REDIRECT_BASE",
            "https://tollbooth--b4806c182bb411f1b6fe42dde27851f2.web.val.run",
        )
        short_url = f"{redirect_base}/{chosen_slug}"

        logger.info("Created shortlink %s → %s", chosen_slug, url[:80])
        return {
            "success": True,
            "slug": chosen_slug,
            "short_url": short_url,
            "target_url": url,
            "expires_in_seconds": _TTL_SECONDS,
        }
    except Exception as e:
        logger.exception("Failed to create shortlink")
        return {"success": False, "error": str(e)}


@mcp.tool()
async def resolve_shortlink(slug: str) -> dict[str, Any]:
    """Look up where a slug points without redirecting.

    Args:
        slug: The shortlink slug to resolve.

    Returns:
        Dict with ``url`` on success, or ``error`` if not found/expired.
    """
    try:
        await _cleanup_expired()
        result = await _execute(
            "SELECT url FROM shortlinks WHERE slug = $1", [slug]
        )
        rows = result.get("rows", [])
        if not rows:
            return {"found": False, "error": "Not found or expired."}
        return {"found": True, "url": rows[0]["url"]}
    except Exception as e:
        logger.exception("Failed to resolve shortlink")
        return {"found": False, "error": str(e)}


@mcp.tool()
async def delete_shortlink(slug: str) -> dict[str, Any]:
    """Delete a shortlink before it expires.

    Args:
        slug: The shortlink slug to delete.

    Returns:
        Dict with ``success`` key.
    """
    try:
        result = await _execute(
            "DELETE FROM shortlinks WHERE slug = $1 RETURNING slug", [slug]
        )
        rows = result.get("rows", [])
        if not rows:
            return {"success": False, "error": "Not found or already expired."}
        logger.info("Deleted shortlink %s", slug)
        return {"success": True, "message": f"Shortlink '{slug}' deleted."}
    except Exception as e:
        logger.exception("Failed to delete shortlink")
        return {"success": False, "error": str(e)}


@mcp.tool()
async def shortlink_status() -> dict[str, Any]:
    """Health check — shows the number of active shortlinks and TTL."""
    try:
        await _cleanup_expired()
        result = await _execute("SELECT COUNT(*) AS cnt FROM shortlinks")
        count = result["rows"][0]["cnt"] if result.get("rows") else 0
        return {
            "status": "healthy",
            "version": __version__,
            "active_links": count,
            "ttl_seconds": _TTL_SECONDS,
        }
    except Exception as e:
        return {"status": "unhealthy", "version": __version__, "error": str(e)}
