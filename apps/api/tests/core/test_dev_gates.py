"""
Tests for Phase 17: Dev-Time Security Gates.

DEV-01: detect-secrets baseline blocks secret commits
DEV-02: bandit blocks HIGH-severity Python security findings
DEV-03: pip-audit + pnpm audit block known-CVE dependencies in CI
DEV-06: django-debug-toolbar renders in development, absent elsewhere
"""

import subprocess
from pathlib import Path

import pytest

# Repo root is 2 levels above apps/api/
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent


# --- DEV-01: detect-secrets ---


@pytest.mark.req("DEV-01")
def test_secrets_baseline_exists():
    """`.secrets.baseline` file exists at repo root (created by detect-secrets scan)."""
    baseline = REPO_ROOT / ".secrets.baseline"
    assert baseline.exists(), f".secrets.baseline not found at {baseline}"


# --- DEV-02: bandit ---


@pytest.mark.req("DEV-02")
def test_bandit_available():
    """bandit is installed as a dev dep and `uv run bandit --version` exits 0."""
    result = subprocess.run(
        ["uv", "run", "bandit", "--version"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"bandit --version failed: {result.stderr}"


@pytest.mark.req("DEV-02")
def test_bandit_clean():
    """`bandit -r apps/ -lll -x tests/` exits 0 (no HIGH-severity findings in codebase)."""
    result = subprocess.run(
        ["uv", "run", "bandit", "-r", "apps/", "-lll", "-x", "tests/"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"bandit found HIGH-severity issues:\n{result.stdout}\n{result.stderr}"
    )


# --- DEV-03: pip-audit ---


@pytest.mark.req("DEV-03", "DEV-05")
def test_pip_audit_available():
    """pip-audit is installed as a dev dep and `uv run pip-audit --version` exits 0."""
    result = subprocess.run(
        ["uv", "run", "pip-audit", "--version"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"pip-audit --version failed: {result.stderr}"


# --- DEV-06: django-debug-toolbar ---


@pytest.mark.req("DEV-06")
def test_ddt_not_in_base_settings():
    """`debug_toolbar` does NOT appear in base.py INSTALLED_APPS (file-level check)."""
    base_py = Path(__file__).resolve().parent.parent.parent / "config" / "settings" / "base.py"
    content = base_py.read_text()
    assert "debug_toolbar" not in content, (
        "debug_toolbar found in base.py — DDT must only be in development.py"
    )


@pytest.mark.req("DEV-06")
def test_ddt_not_in_production_settings():
    """`debug_toolbar` does NOT appear in production.py INSTALLED_APPS (file-level check)."""
    production_py = (
        Path(__file__).resolve().parent.parent.parent / "config" / "settings" / "production.py"
    )
    content = production_py.read_text()
    assert "debug_toolbar" not in content, (
        "debug_toolbar found in production.py — DDT must only be in development.py"
    )


@pytest.mark.req("DEV-06")
def test_ddt_in_development_settings():
    """`debug_toolbar` IS in INSTALLED_APPS when loaded via development settings."""
    from django.conf import settings

    assert "debug_toolbar" in settings.INSTALLED_APPS, (
        "debug_toolbar not in INSTALLED_APPS — add it to development.py"
    )


@pytest.mark.req("DEV-06")
def test_ddt_url_accessible_in_debug():
    """`/__debug__/` URL resolves (not 500) when DEBUG=True."""
    from django.test import Client

    client = Client()
    response = client.get("/__debug__/", follow=True)
    assert response.status_code < 500, (
        f"/__debug__/ returned {response.status_code} — DDT URLs not registered in urls.py"
    )
