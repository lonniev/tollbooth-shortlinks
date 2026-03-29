"""Tests for slug generation and basic tool structure."""

from server import _ADJECTIVES, _NOUNS, _VERBS, _generate_slug


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
