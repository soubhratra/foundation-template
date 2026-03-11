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
    conftest = Path(__file__).resolve().parent.parent.parent / "conftest.py"
    content = conftest.read_text()
    assert "nplusone" in content, (
        "nplusone fixture not found in conftest.py — add _nplusone_guard autouse fixture"
    )


def test_nplusone_raises_on_n_plus_one(db):
    """NPlusOneError is raised immediately when a related attribute is accessed in a loop."""
    from django.contrib.auth import get_user_model
    from nplusone.core.exceptions import NPlusOneError
    from nplusone.core.profiler import Profiler

    User = get_user_model()
    # Create two users so the queryset returns multiple rows
    User.objects.create_user(
        username="n1a", email="n1a@example.com", password="test"
    )  # pragma: allowlist secret  # noqa: E501
    User.objects.create_user(
        username="n1b", email="n1b@example.com", password="test"
    )  # pragma: allowlist secret  # noqa: E501

    # Access a related manager (groups) inside a loop — classic N+1 pattern.
    # Profiler raises NPlusOneError immediately on the first lazy load,
    # not deferred to teardown.
    with pytest.raises(NPlusOneError):
        with Profiler():
            for user in User.objects.all():
                _ = list(user.groups.all())  # lazy load of related manager — N+1


from nplusone.ext.pytest import allow_lazy_load  # noqa: E402


@allow_lazy_load
def test_nplusone_allow_annotation_suppresses_error(db):
    """@allow_lazy_load decorator suppresses NPlusOneError for annotated tests."""
    from django.contrib.auth import get_user_model

    User = get_user_model()
    User.objects.create_user(
        username="allow", email="allow@example.com", password="test"
    )  # pragma: allowlist secret  # noqa: E501
    # Intentional N+1 — allowed by @allow_lazy_load decorator.
    for user in User.objects.all():
        _ = list(user.groups.all())
    # Test passes — no NPlusOneError raised for @allow_lazy_load-annotated tests.


# --- DEV-07: commitlint ---


def test_commitlint_hook_present():
    """`conventional-pre-commit` appears in .pre-commit-config.yaml with commit-msg stage."""
    config = REPO_ROOT / ".pre-commit-config.yaml"
    content = config.read_text()
    assert "conventional-pre-commit" in content, (
        "conventional-pre-commit not in .pre-commit-config.yaml"
    )
    assert "commit-msg" in content, "commit-msg stage not configured for conventional-pre-commit"


# --- DEV-08: ruff McCabe ---


def test_ruff_mccabe_configured():
    """`[tool.ruff.lint.mccabe]` section exists in pyproject.toml."""
    pyproject = Path(__file__).resolve().parent.parent.parent / "pyproject.toml"
    content = pyproject.read_text()
    assert "[tool.ruff.lint.mccabe]" in content, (
        "[tool.ruff.lint.mccabe] not found in pyproject.toml"
    )


def test_ruff_mccabe_max_complexity():
    """`max-complexity` value in pyproject.toml is exactly 10."""
    pyproject = Path(__file__).resolve().parent.parent.parent / "pyproject.toml"
    content = pyproject.read_text()
    assert "max-complexity = 10" in content, (
        "max-complexity = 10 not found in [tool.ruff.lint.mccabe]"
    )
