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

    @pytest.mark.req("AKEY-01")
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

    @pytest.mark.req("AKEY-01")
    def test_list_keys_does_not_include_raw_key(self, client, api_user, api_key):
        """GET /api/v1/me/api-keys/ does not expose raw key field."""
        self._login(client, api_user)
        response = client.get("/api/v1/me/api-keys/")
        assert response.status_code == 200
        data = response.json()
        results = data.get("results", data) if isinstance(data, dict) else data
        for key_record in results:
            assert "key" not in key_record

    @pytest.mark.req("AKEY-01")
    def test_revoke_key_sets_inactive(self, client, api_user, api_key):
        """DELETE /api/v1/me/api-keys/{id}/ sets is_active=False."""

        self._login(client, api_user)
        response = client.delete(f"/api/v1/me/api-keys/{api_key.id}/")
        assert response.status_code == 204
        api_key.refresh_from_db()
        assert api_key.is_active is False

    @pytest.mark.req("AKEY-01")
    def test_revoked_key_auth_returns_401(self, client, api_user, revoked_api_key):
        """Attempting to use a revoked key for authentication returns 401."""
        response = client.get(
            "/api/v1/me/api-keys/",
            HTTP_AUTHORIZATION=f"Bearer {revoked_api_key._raw_key}",
        )
        assert response.status_code in (401, 403)

    @pytest.mark.req("AKEY-01", "AKEY-03")
    def test_create_key_invalid_scope_returns_422(self, client, api_user):
        """POST with an unknown scope returns 422 validation error."""
        self._login(client, api_user)
        response = client.post(
            "/api/v1/me/api-keys/",
            data={"name": "Bad Key", "scopes": ["nonexistent_scope"]},
            content_type="application/json",
        )
        assert response.status_code == 422

    @pytest.mark.req("AKEY-01", "AKEY-03")
    def test_create_key_empty_scopes_returns_422(self, client, api_user):
        """POST with empty scopes list returns 422."""
        self._login(client, api_user)
        response = client.post(
            "/api/v1/me/api-keys/",
            data={"name": "Empty", "scopes": []},
            content_type="application/json",
        )
        assert response.status_code == 422

    @pytest.mark.req("AKEY-03")
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

    @pytest.mark.req("AKEY-01", "AUDIT-01")
    def test_create_key_with_org_slug(self, client, api_user, org_for_apikey):
        """POST /me/api-keys/ with org_slug returns 201 with org_slug in response (AUDIT-01)."""
        self._login(client, api_user)
        response = client.post(
            "/api/v1/me/api-keys/",
            data={"name": "Org Key", "scopes": ["read"], "org_slug": org_for_apikey.slug},
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.json()
        assert data.get("org_slug") == org_for_apikey.slug

    @pytest.mark.req("AKEY-01", "AUDIT-01")
    def test_create_key_event_in_audit_log(self, client, api_user, org_for_apikey):
        """APIKey create event appears in org audit log when org_slug provided (AUDIT-01)."""
        from apps.audit.selectors import get_audit_log_page

        self._login(client, api_user)
        client.post(
            "/api/v1/me/api-keys/",
            data={"name": "Audit Key", "scopes": ["read"], "org_slug": org_for_apikey.slug},
            content_type="application/json",
        )
        items, _ = get_audit_log_page(org=org_for_apikey)
        actions = [item.action for item in items]
        assert "api_key.created" in actions, f"Expected api_key.created in audit log; got {actions}"

    @pytest.mark.req("AKEY-01", "AUDIT-01")
    def test_revoke_key_event_in_audit_log(self, client, api_user, org_for_apikey):
        """APIKey revoke event appears in org audit log (AUDIT-01)."""
        # Create key directly with org association so org_id is in context
        import pghistory

        from apps.api_keys.models import APIKey
        from apps.audit.selectors import get_audit_log_page

        raw_key, stored_prefix, key_hash = APIKey.generate_key()
        with pghistory.context(user=api_user.pk, org_id=str(org_for_apikey.id)):
            key = APIKey.objects.create(
                user=api_user,
                org=org_for_apikey,
                prefix=stored_prefix,
                key_hash=key_hash,
                scopes=["read"],
                name="Revoke Test",
                is_active=True,
            )

        self._login(client, api_user)
        response = client.delete(f"/api/v1/me/api-keys/{key.id}/")
        assert response.status_code == 204

        items, _ = get_audit_log_page(org=org_for_apikey)
        actions = [item.action for item in items]
        assert "api_key.updated" in actions, f"Expected api_key.updated in audit log; got {actions}"

    @pytest.mark.req("AKEY-01")
    def test_create_key_without_org_slug_still_works(self, client, api_user):
        """POST /me/api-keys/ without org_slug returns 201 with org_slug=null (AUDIT-01)."""
        self._login(client, api_user)
        response = client.post(
            "/api/v1/me/api-keys/",
            data={"name": "Personal Key", "scopes": ["read"]},
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.json()
        assert "org_slug" in data
        assert data["org_slug"] is None
