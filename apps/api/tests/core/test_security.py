"""
Tests for Phase 16: Security Hardening.

SEC-01: Rate limiting on auth endpoints
SEC-02: Security headers (Django + Next.js) — turned GREEN by Plan 16-03
SEC-03: Redis cache + session backend
"""

import pytest
from django.test import override_settings

# --- SEC-01: Rate Limiting ---


def test_rate_limit_returns_429(client):
    """Auth endpoints return HTTP 429 after exceeding the configured rate limit."""
    # Enable rate limiting for this test (autouse fixture disables it globally).
    # Use 1/m so 2 requests trigger the limit without needing 5 real requests.
    with override_settings(RATELIMIT_ENABLE=True, RATELIMIT_AUTH_LOGIN="1/m"):
        # First request — should pass (within limit)
        client.post(
            "/api/v1/auth/browser/v1/auth/login",
            data={"username": "x", "password": "y"},
            content_type="application/json",
        )
        # Second request — should be rate limited (exceeds 1/m)
        response = client.post(
            "/api/v1/auth/browser/v1/auth/login",
            data={"username": "x", "password": "y"},
            content_type="application/json",
        )
    assert response.status_code == 429


def test_rate_limit_retry_after_header(client):
    """HTTP 429 response includes a Retry-After header."""
    with override_settings(RATELIMIT_ENABLE=True, RATELIMIT_AUTH_LOGIN="1/m"):
        client.post(
            "/api/v1/auth/browser/v1/auth/login",
            data={},
            content_type="application/json",
        )
        response = client.post(
            "/api/v1/auth/browser/v1/auth/login",
            data={},
            content_type="application/json",
        )
    assert response.status_code == 429
    assert response.get("Retry-After") == "60"


def test_rate_limit_uses_redis_cache():
    """Rate limiting uses the 'default' Redis cache backend (not LocMemCache)."""
    # Import base settings directly (bypass test isolation fixture override).
    import config.settings.base as base_settings

    assert "RedisCache" in base_settings.CACHES["default"]["BACKEND"]
    assert base_settings.RATELIMIT_USE_CACHE == "default"


# --- SEC-02: Security Headers (turned GREEN by Plan 16-03) ---


def test_csp_header_present(client):
    """Every Django response includes a Content-Security-Policy header."""
    pytest.fail("RED: CSPMiddleware not yet installed (Plan 16-03)")


def test_hsts_header_production(client):
    """Production settings include Strict-Transport-Security header."""
    pytest.fail("RED: SECURE_HSTS_SECONDS not yet set in production.py (Plan 16-03)")


def test_x_frame_options_header(client):
    """Every Django response includes X-Frame-Options: DENY."""
    pytest.fail("RED: X_FRAME_OPTIONS not yet explicitly set (Plan 16-03)")


def test_referrer_policy_header(client):
    """Every Django response includes Referrer-Policy: strict-origin-when-cross-origin."""
    pytest.fail("RED: SECURE_REFERRER_POLICY not yet set (Plan 16-03)")


# --- SEC-03: Redis Cache + Session Backend ---


def test_default_cache_is_redis():
    """Default cache backend is RedisCache (not LocMemCache) in non-test environments."""
    import config.settings.base as base_settings

    assert "RedisCache" in base_settings.CACHES["default"]["BACKEND"], (
        "Expected django_redis.cache.RedisCache as default backend, "
        f"got: {base_settings.CACHES['default']['BACKEND']}"
    )


def test_session_cache_is_redis():
    """Session engine uses cache backend pointing at Redis sessions alias."""
    import config.settings.base as base_settings

    assert base_settings.SESSION_ENGINE == "django.contrib.sessions.backends.cache"
    assert base_settings.SESSION_CACHE_ALIAS == "sessions"
    assert "RedisCache" in base_settings.CACHES["sessions"]["BACKEND"]
