"""
Tests for Phase 18: Dev-Time Quality Gates.

DEV-04: nplusone autouse fixture raises NPlusOneError on N+1 query regressions
DEV-07: conventional-pre-commit hook blocks non-Conventional Commits messages
DEV-08: ruff McCabe complexity gate blocks functions exceeding complexity 10
"""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent


# --- DEV-04: nplusone ---


def test_nplusone_fixture_registered():
    """nplusone autouse fixture is registered in conftest.py."""
    pytest.fail("RED: nplusone autouse fixture not yet in conftest.py — Plan 18-02 adds it")


def test_nplusone_raises_on_n_plus_one():
    """A queryset accessed inside a loop raises NPlusOneError when nplusone is active."""
    pytest.fail(
        "RED: nplusone not installed — Plan 18-02 installs nplusone and registers"
        " autouse fixture; queryset loop will raise NPlusOneError"
    )


def test_nplusone_allow_annotation_suppresses_error():
    """@allow_lazy_load decorator suppresses NPlusOneError for intentional N+1 accesses."""
    pytest.fail(
        "RED: nplusone not installed — Plan 18-02 installs nplusone;"
        " @allow_lazy_load decorator available after install"
    )


# --- DEV-07: commitlint ---


def test_commitlint_hook_present():
    """`conventional-pre-commit` appears in .pre-commit-config.yaml with commit-msg stage."""
    pytest.fail(
        "RED: conventional-pre-commit not yet in .pre-commit-config.yaml"
        " — Plan 18-02 adds commit-msg stage hook"
    )


# --- DEV-08: ruff McCabe ---


def test_ruff_mccabe_configured():
    """`[tool.ruff.lint.mccabe]` section exists in pyproject.toml."""
    pytest.fail("RED: [tool.ruff.lint.mccabe] not yet in pyproject.toml — Plan 18-02 adds it")


def test_ruff_mccabe_max_complexity():
    """`max-complexity` value in pyproject.toml is exactly 10."""
    pytest.fail("RED: max-complexity not yet set — Plan 18-02 sets max-complexity = 10")
