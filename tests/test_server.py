"""Tests for slug generation and basic tool structure."""

import fastmcp

import server
from server import _ADJECTIVES, _NOUNS, _VERBS, _generate_slug, shortlink_status


def test_slug_format():
    slug = _generate_slug()
    parts = slug.split("-")
    assert len(parts) == 4, f"Expected 4 parts, got {parts}"


def test_slug_uses_word_lists():
    for _ in range(50):
        slug = _generate_slug()
        adj, noun1, verb, noun2 = slug.split("-")
        assert adj in _ADJECTIVES
        assert noun1 in _NOUNS
        assert verb in _VERBS
        assert noun2 in _NOUNS


def test_slugs_vary():
    slugs = {_generate_slug() for _ in range(20)}
    assert len(slugs) > 10, "Slugs should have reasonable variety"


def test_server_advertises_own_version():
    # The MCP handshake must report this service's version, not the FastMCP
    # framework version, so deploy-verify can confirm which build is live.
    assert server.mcp.version == server.__version__
    assert server.mcp.version != fastmcp.__version__


async def test_status_reports_version(monkeypatch):
    # shortlink_status is the deploy-verify probe; it must carry the version
    # even when the database is unreachable.
    monkeypatch.delenv("NEON_SHORTLINKS_URL", raising=False)
    result = await shortlink_status()
    assert result["version"] == server.__version__
