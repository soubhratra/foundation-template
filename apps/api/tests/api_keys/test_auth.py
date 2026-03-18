"""Tests for ApiKeyAuth HttpBearer backend and RequireScope permission class.

Requirements: AKEY-01 (scope enforcement, session-only rejection), AKEY-03 (usage tracking).
"""

import pytest
from django.test import RequestFactory

from apps.api_keys.auth import ApiKeyAuth, RequireScope


@pytest.mark.django_db
class TestApiKeyAuth:
    @pytest.mark.req("AKEY-02")
    def test_valid_key_authenticates_user(self, api_key, api_user):
        auth = ApiKeyAuth()
        factory = RequestFactory()
        request = factory.get("/")
        result = auth.authenticate(request, api_key._raw_key)
        assert result == api_user

    @pytest.mark.req("AKEY-02")
    def test_invalid_key_returns_none(self, api_user):
        auth = ApiKeyAuth()
        factory = RequestFactory()
        request = factory.get("/")
        result = auth.authenticate(request, "ft_notarealkey")
        assert result is None

    @pytest.mark.req("AKEY-02")
    def test_revoked_key_returns_none(self, revoked_api_key):
        auth = ApiKeyAuth()
        factory = RequestFactory()
        request = factory.get("/")
        result = auth.authenticate(request, revoked_api_key._raw_key)
        assert result is None

    @pytest.mark.req("AKEY-02")
    def test_authenticate_sets_request_api_key(self, api_key):
        auth = ApiKeyAuth()
        factory = RequestFactory()
        request = factory.get("/")
        auth.authenticate(request, api_key._raw_key)
        assert hasattr(request, "api_key")
        assert request.api_key.prefix == api_key.prefix

    @pytest.mark.req("AKEY-03")
    def test_last_used_at_updated(self, api_key):
        auth = ApiKeyAuth()
        factory = RequestFactory()
        request = factory.get("/")
        assert api_key.last_used_at is None
        auth.authenticate(request, api_key._raw_key)
        api_key.refresh_from_db()
        assert api_key.last_used_at is not None

    @pytest.mark.req("AKEY-03")
    def test_usage_count_incremented(self, api_key):
        auth = ApiKeyAuth()
        factory = RequestFactory()
        request = factory.get("/")
        assert api_key.usage_count == 0
        auth.authenticate(request, api_key._raw_key)
        api_key.refresh_from_db()
        assert api_key.usage_count == 1

    @pytest.mark.req("AKEY-03")
    def test_usage_count_increments_on_each_request(self, api_key):
        auth = ApiKeyAuth()
        factory = RequestFactory()
        for _ in range(3):
            request = factory.get("/")
            auth.authenticate(request, api_key._raw_key)
        api_key.refresh_from_db()
        assert api_key.usage_count == 3


@pytest.mark.django_db
class TestRequireScope:
    @pytest.mark.req("AKEY-01")
    def test_require_scope_rejects_session_request(self):
        """Session-only requests (no request.api_key) must be rejected with 403."""
        from django.core.exceptions import PermissionDenied

        factory = RequestFactory()
        request = factory.get("/")
        # No request.api_key set — simulates session auth
        perm = RequireScope("read")
        with pytest.raises(PermissionDenied):
            perm.has_permission(request, None)

    @pytest.mark.req("AKEY-01")
    def test_require_scope_rejects_wrong_scope(self, api_key):
        """Key with only 'read' scope must be rejected when 'admin' is required."""
        from django.core.exceptions import PermissionDenied

        factory = RequestFactory()
        request = factory.get("/")
        # api_key fixture has scopes=["read", "write"] — not "admin"
        request.api_key = api_key  # type: ignore[attr-defined]
        perm = RequireScope("admin")
        with pytest.raises(PermissionDenied):
            perm.has_permission(request, None)

    @pytest.mark.req("AKEY-01")
    def test_require_scope_passes_with_correct_scope(self, api_key):
        factory = RequestFactory()
        request = factory.get("/")
        request.api_key = api_key  # type: ignore[attr-defined]
        perm = RequireScope("read")
        assert perm.has_permission(request, None) is True
