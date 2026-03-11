"""
RED test stubs for Phase 16: Security Hardening.

These tests MUST fail before Plan 16-02 and 16-03 implementation runs.
Run: cd apps/api && python -m pytest tests/core/test_security.py -x
"""

import pytest

# --- SEC-01: Rate Limiting ---


def test_rate_limit_returns_429(client):
    """Auth endpoints return HTTP 429 after exceeding the configured rate limit."""
    pytest.fail("RED: AuthRateLimitMiddleware not yet implemented (Plan 16-02)")


def test_rate_limit_retry_after_header(client):
    """HTTP 429 response includes a Retry-After header."""
    pytest.fail("RED: ratelimited_error handler not yet implemented (Plan 16-02)")


def test_rate_limit_uses_redis_cache(settings):
    """Rate limit counters use Redis-backed cache (not LocMemCache)."""
    pytest.fail("RED: CACHES['default'] not yet configured as RedisCache (Plan 16-02)")


# --- SEC-02: Security Headers ---


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


def test_default_cache_is_redis(settings):
    """Default cache backend is RedisCache (not LocMemCache) in non-test environments."""
    pytest.fail("RED: CACHES['default'] not yet configured as RedisCache (Plan 16-02)")


def test_session_cache_is_redis(settings):
    """Session engine uses cache backend pointing at Redis sessions alias."""
    pytest.fail("RED: SESSION_ENGINE and SESSION_CACHE_ALIAS not yet set (Plan 16-02)")
