"""Integration tests for GET /api/v1/me/api-keys/ping/.

Exercises the full auth chain end-to-end:
ApiKeyAuth -> RequireScope -> ApiKeyRateLimitMiddleware -> usage tracking.

Requirements: AKEY-01, AKEY-02, AKEY-03.
"""

import pytest
from django.core.cache import cache
from django.test import override_settings

from apps.api_keys.models import APIKey


@pytest.mark.django_db
class TestApiKeyPingEndpoint:
    URL = "/api/v1/me/api-keys/ping/"

    def test_valid_key_with_read_scope_returns_200(self, client, api_key):
        # AKEY-01: valid key with correct scope succeeds
        response = client.get(
            self.URL,
            HTTP_AUTHORIZATION=f"Bearer {api_key._raw_key}",
        )
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_valid_key_updates_usage_tracking(self, client, api_key):
        # AKEY-03: last_used_at and usage_count updated on authenticated request
        assert api_key.usage_count == 0
        client.get(self.URL, HTTP_AUTHORIZATION=f"Bearer {api_key._raw_key}")
        api_key.refresh_from_db()
        assert api_key.last_used_at is not None
        assert api_key.usage_count == 1

    def test_wrong_scope_returns_403(self, client, api_user):
        # AKEY-01: RequireScope("read") must reject a key with only "write" scope
        from django.contrib.auth import get_user_model

        User = get_user_model()
        user = User.objects.create_user(
            username="scopetest", email="scopetest@example.com", password="x"
        )
        raw_key, prefix, key_hash = APIKey.generate_key()
        key = APIKey.objects.create(
            user=user,
            prefix=prefix,
            key_hash=key_hash,
            scopes=["write"],  # deliberately missing "read"
            is_active=True,
        )
        key._raw_key = raw_key
        response = client.get(self.URL, HTTP_AUTHORIZATION=f"Bearer {key._raw_key}")
        assert response.status_code == 403

    @override_settings(RATELIMIT_ENABLE=True)
    def test_rate_limit_headers_on_success(self, client, api_key):
        # AKEY-02: X-RateLimit-* headers injected by ApiKeyRateLimitMiddleware
        response = client.get(
            self.URL,
            HTTP_AUTHORIZATION=f"Bearer {api_key._raw_key}",
        )
        assert response.status_code == 200
        assert "X-RateLimit-Limit" in response
        assert "X-RateLimit-Remaining" in response
        assert "X-RateLimit-Reset" in response

    @override_settings(RATELIMIT_ENABLE=True)
    def test_rate_limit_exceeded_returns_429(self, client, api_key, settings):
        # AKEY-02: per-key rate limit enforcement
        settings.API_KEY_RATE_LIMIT = "1/m"  # pragma: allowlist secret
        cache.clear()
        client.get(self.URL, HTTP_AUTHORIZATION=f"Bearer {api_key._raw_key}")
        response = client.get(
            self.URL,
            HTTP_AUTHORIZATION=f"Bearer {api_key._raw_key}",
        )
        assert response.status_code == 429
        assert "X-RateLimit-Remaining" in response
        assert response["X-RateLimit-Remaining"] == "0"

    def test_session_auth_rejected(self, client, api_user):
        # AKEY-01 (success criterion 4): session-only auth must not pass key-only endpoint
        client.force_login(api_user)
        response = client.get(self.URL)
        assert response.status_code in (401, 403)

    def test_invalid_key_returns_401(self, client):
        # Auth failure: invalid Bearer token
        response = client.get(
            self.URL,
            HTTP_AUTHORIZATION="Bearer ft_notarealkey",
        )
        assert response.status_code == 401

    def test_no_auth_returns_401(self, client):
        # Auth failure: no Authorization header at all
        response = client.get(self.URL)
        assert response.status_code in (401, 403)
