"""
Tests for Phase 17: Dev-Time Security Gates.

DEV-01: detect-secrets baseline blocks secret commits
DEV-02: bandit blocks HIGH-severity Python security findings
DEV-03: pip-audit + pnpm audit block known-CVE dependencies in CI
DEV-06: django-debug-toolbar renders in development, absent elsewhere
"""

import pytest

# --- DEV-01: detect-secrets ---


def test_secrets_baseline_exists():
    """`.secrets.baseline` file exists at repo root (created by detect-secrets scan)."""
    pytest.fail(
        "RED: .secrets.baseline not yet created — turns GREEN in Plan 17-03"
        " (run: detect-secrets scan > .secrets.baseline)"
    )


# --- DEV-02: bandit ---


def test_bandit_available():
    """bandit is installed as a dev dep and `uv run bandit --version` exits 0."""
    pytest.fail(
        "RED: bandit not installed as dev dep — turns GREEN in Plan 17-03"
        " (adds bandit to pyproject.toml dev dependencies)"
    )


def test_bandit_clean():
    """`bandit -r apps/ -lll -x tests/` exits 0 (no HIGH-severity findings in codebase)."""
    pytest.fail(
        "RED: bandit not installed, cannot run scan — turns GREEN in Plan 17-03"
        " (installs bandit and verifies no HIGH findings in apps/)"
    )


# --- DEV-03: pip-audit ---


def test_pip_audit_available():
    """pip-audit is installed as a dev dep and `uv run pip-audit --version` exits 0."""
    pytest.fail(
        "RED: pip-audit not installed as dev dep — turns GREEN in Plan 17-03"
        " (adds pip-audit to pyproject.toml dev dependencies)"
    )


# --- DEV-06: django-debug-toolbar ---


def test_ddt_not_in_base_settings():
    """`debug_toolbar` does NOT appear in base.py INSTALLED_APPS (file-level check)."""
    pytest.fail(
        "RED: debug_toolbar not yet added to development.py — turns GREEN in Plan 17-03"
        " (adds DDT only to development.py INSTALLED_APPS, verifies base.py stays clean)"
    )


def test_ddt_not_in_production_settings():
    """`debug_toolbar` does NOT appear in production.py INSTALLED_APPS (file-level check)."""
    pytest.fail(
        "RED: debug_toolbar not yet added to development.py — turns GREEN in Plan 17-03"
        " (adds DDT only to development.py INSTALLED_APPS, verifies production.py stays clean)"
    )


def test_ddt_in_development_settings():
    """`debug_toolbar` IS in INSTALLED_APPS when loaded via development settings."""
    pytest.fail(
        "RED: debug_toolbar not yet in development.py INSTALLED_APPS — turns GREEN in Plan 17-03"
        " (adds debug_toolbar to development.py INSTALLED_APPS)"
    )


def test_ddt_url_accessible_in_debug():
    """`/__debug__/` URL resolves (not 500) when DEBUG=True."""
    pytest.fail(
        "RED: debug_toolbar URLs not yet registered in urls.py — turns GREEN in Plan 17-03"
        " (registers debug_toolbar_urls() in urls.py under if settings.DEBUG)"
    )
