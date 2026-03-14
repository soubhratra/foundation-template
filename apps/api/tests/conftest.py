"""Pytest configuration and shared fixtures."""

import functools
import sys
import types

import pytest
from django.contrib.auth import get_user_model

User = get_user_model()

# ---------------------------------------------------------------------------
# nplusone: autouse N+1 guard + synthetic nplusone.ext.pytest module
#
# nplusone>=1.0 dropped the pytest plugin (nplusone.ext.pytest). We implement
# equivalent behaviour here and register a synthetic module so test files can
# still do `from nplusone.ext.pytest import allow_lazy_load`.
# ---------------------------------------------------------------------------

_allow_lazy_load_tests: set[str] = set()


def allow_lazy_load(fn):
    """Decorator: mark a test as intentionally allowing N+1 queries.

    Use sparingly. Each usage should have a comment explaining why the N+1
    is acceptable (e.g., small fixed dataset, non-hot path).
    """
    _allow_lazy_load_tests.add(fn.__qualname__)

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)

    return wrapper


_synthetic_ext = types.ModuleType("nplusone.ext")
_synthetic_pytest = types.ModuleType("nplusone.ext.pytest")
_synthetic_pytest.allow_lazy_load = allow_lazy_load  # type: ignore[attr-defined]
sys.modules.setdefault("nplusone.ext", _synthetic_ext)
sys.modules["nplusone.ext.pytest"] = _synthetic_pytest


_NPLUSONE_WHITELIST = [
    # APIKey.org is eagerly loaded via select_related("org") in list_for_user()
    # to prevent N+1 queries when serializing org_slug. Tests that use keys
    # without an org assignment correctly don't touch the org field — this is
    # not an N+1, the eager load is correct for production paths with org keys.
    {"label": "unused_eager_load", "model": "APIKey", "field": "org"},
]


@pytest.fixture(autouse=True)
def _nplusone_guard(request):
    """Autouse fixture: raise NPlusOneError on N+1 queries in all tests.

    Skipped for tests decorated with @allow_lazy_load.
    """
    from nplusone.core.profiler import Profiler

    if request.node.function.__qualname__ in _allow_lazy_load_tests:
        yield
        return

    with Profiler(whitelist=_NPLUSONE_WHITELIST):
        yield


@pytest.fixture(autouse=True)
def test_isolation_settings(settings):
    """Disable rate limiting and use fast in-memory cache in all tests.

    Rate limiting is disabled via RATELIMIT_ENABLE (django-ratelimit's official flag).
    LocMemCache is used instead of Redis so tests have no Redis dependency in CI.
    Security headers middleware remains ACTIVE — tests can assert headers are present.
    """
    settings.RATELIMIT_ENABLE = False
    settings.CACHES = {
        "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
        "sessions": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
    }


@pytest.fixture(scope="session", autouse=True)
def enable_pgvector_for_tests(django_db_setup, django_db_blocker):
    """Install pgvector extension in test database before migrations run."""
    # This runs after test database is created but we need to ensure extension exists
    # The migrations will handle creating it via IF NOT EXISTS
    pass


@pytest.fixture
def api_client(db):
    """Provide Django test client for API testing."""
    from django.test import Client

    return Client()


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
        first_name="Test",
        last_name="User",
    )


@pytest.fixture
def authenticated_client(api_client, user):
    """Provide authenticated API client."""
    api_client.force_login(user=user)
    return api_client
