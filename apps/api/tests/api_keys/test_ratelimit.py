"""Tests for ApiKeyRateLimitMiddleware — per-key rate limiting and X-RateLimit-* headers.

Requirements: AKEY-02.

CRITICAL: test_isolation_settings autouse fixture globally sets RATELIMIT_ENABLE=False.
All tests in this file must override it with settings.RATELIMIT_ENABLE = True.
Use LocMemCache as the cache backend (already configured by test_isolation_settings).
"""

import pytest
from django.http import HttpResponse
from django.test import RequestFactory, override_settings


@pytest.mark.django_db
class TestApiKeyRateLimitHeaders:
    @override_settings(RATELIMIT_ENABLE=True)
    def test_headers_on_normal_response(self, api_key):
        """Normal (non-rate-limited) responses include all three X-RateLimit-* headers."""
        from apps.api_keys.middleware import ApiKeyRateLimitMiddleware

        factory = RequestFactory()
        request = factory.get("/api/v1/some-endpoint/")
        request.api_key = api_key  # type: ignore[attr-defined]

        def get_response(req):
            return HttpResponse("ok", status=200)

        middleware = ApiKeyRateLimitMiddleware(get_response)
        response = middleware(request)

        assert "X-RateLimit-Limit" in response
        assert "X-RateLimit-Remaining" in response
        assert "X-RateLimit-Reset" in response
        assert response.status_code == 200

    @override_settings(RATELIMIT_ENABLE=True)
    def test_rate_limit_returns_429_with_headers(self, api_key, settings):
        """Requests exceeding the rate limit return 429 with X-RateLimit-* headers."""
        from django.core.cache import cache

        from apps.api_keys.middleware import ApiKeyRateLimitMiddleware

        # Set a very low rate limit for testing
        settings.API_KEY_RATE_LIMIT = "1/m"  # pragma: allowlist secret
        cache.clear()

        factory = RequestFactory()

        def get_response(req):
            return HttpResponse("ok", status=200)

        middleware = ApiKeyRateLimitMiddleware(get_response)

        # First request should pass
        request1 = factory.get("/api/v1/some-endpoint/")
        request1.api_key = api_key  # type: ignore[attr-defined]
        response1 = middleware(request1)
        assert response1.status_code == 200

        # Second request should be rate-limited
        request2 = factory.get("/api/v1/some-endpoint/")
        request2.api_key = api_key  # type: ignore[attr-defined]
        response2 = middleware(request2)
        assert response2.status_code == 429
        assert "X-RateLimit-Limit" in response2
        assert "X-RateLimit-Remaining" in response2
        assert "X-RateLimit-Reset" in response2
        assert response2["X-RateLimit-Remaining"] == "0"

    @override_settings(RATELIMIT_ENABLE=True)
    def test_no_headers_on_session_request(self):
        """Session-authenticated requests (no api_key) pass through without RL headers."""
        from apps.api_keys.middleware import ApiKeyRateLimitMiddleware

        factory = RequestFactory()
        request = factory.get("/api/v1/some-endpoint/")
        # No request.api_key set

        def get_response(req):
            return HttpResponse("ok", status=200)

        middleware = ApiKeyRateLimitMiddleware(get_response)
        response = middleware(request)
        assert response.status_code == 200
        assert "X-RateLimit-Limit" not in response
