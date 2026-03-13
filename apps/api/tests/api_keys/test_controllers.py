"""Tests for APIKeyController HTTP endpoints: create, list, revoke.

Requirements: AKEY-01 (create/revoke lifecycle, raw key shown once).
"""

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

User = get_user_model()


@pytest.mark.django_db
class TestAPIKeyController:
    def _login(self, client: Client, user) -> None:
        client.force_login(user)

    def test_create_key_returns_raw_key_once(self, client, api_user):
        """POST /api/v1/me/api-keys/ returns raw key in response body."""
        self._login(client, api_user)
        response = client.post(
            "/api/v1/me/api-keys/",
            data={"name": "My Key", "scopes": ["read"]},
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.json()
        # Raw key must be present in create response
        assert "key" in data
        assert data["key"].startswith("ft_")
        # Prefix stored separately
        assert "prefix" in data
        assert data["prefix"] != data["key"]

    def test_list_keys_does_not_include_raw_key(self, client, api_user, api_key):
        """GET /api/v1/me/api-keys/ does not expose raw key field."""
        self._login(client, api_user)
        response = client.get("/api/v1/me/api-keys/")
        assert response.status_code == 200
        data = response.json()
        results = data.get("results", data) if isinstance(data, dict) else data
        for key_record in results:
            assert "key" not in key_record

    def test_revoke_key_sets_inactive(self, client, api_user, api_key):
        """DELETE /api/v1/me/api-keys/{id}/ sets is_active=False."""

        self._login(client, api_user)
        response = client.delete(f"/api/v1/me/api-keys/{api_key.id}/")
        assert response.status_code == 204
        api_key.refresh_from_db()
        assert api_key.is_active is False

    def test_revoked_key_auth_returns_401(self, client, api_user, revoked_api_key):
        """Attempting to use a revoked key for authentication returns 401."""
        response = client.get(
            "/api/v1/me/api-keys/",
            HTTP_AUTHORIZATION=f"Bearer {revoked_api_key._raw_key}",
        )
        assert response.status_code in (401, 403)

    def test_create_key_invalid_scope_returns_422(self, client, api_user):
        """POST with an unknown scope returns 422 validation error."""
        self._login(client, api_user)
        response = client.post(
            "/api/v1/me/api-keys/",
            data={"name": "Bad Key", "scopes": ["nonexistent_scope"]},
            content_type="application/json",
        )
        assert response.status_code == 422

    def test_create_key_empty_scopes_returns_422(self, client, api_user):
        """POST with empty scopes list returns 422."""
        self._login(client, api_user)
        response = client.post(
            "/api/v1/me/api-keys/",
            data={"name": "Empty", "scopes": []},
            content_type="application/json",
        )
        assert response.status_code == 422

    def test_list_keys_shows_usage_count_and_last_used(self, client, api_user, api_key):
        """GET response includes usage_count and last_used_at fields."""
        self._login(client, api_user)
        response = client.get("/api/v1/me/api-keys/")
        assert response.status_code == 200
        data = response.json()
        results = data.get("results", data) if isinstance(data, dict) else data
        if results:
            record = results[0]
            assert "usage_count" in record
            assert "last_used_at" in record
