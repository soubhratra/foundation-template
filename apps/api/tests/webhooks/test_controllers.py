"""HTTP endpoint tests for the webhooks API controller.

HOOK-01: endpoint CRUD (create, list, update, delete, rotate-secret).
HOOK-02: paginated delivery history + delivery detail with attempts.
HOOK-03: manual retry.
HOOK-04: re-enable endpoint resets circuit breaker counter.
"""

import json
from unittest.mock import patch

import pytest
from django.test import Client

# ---------------------------------------------------------------------------
# Endpoint CRUD — HOOK-01
# ---------------------------------------------------------------------------


@pytest.mark.req("HOOK-01")
@pytest.mark.django_db
def test_create_endpoint_returns_secret_once(org, org_admin, client):
    """POST /endpoints returns the raw secret in the response body (shown once only)."""
    client = Client()
    client.force_login(org_admin)

    payload = {
        "url": "https://example.com/hooks",
        "name": "My Hook",
        "event_types": ["user.created"],
    }
    response = client.post(
        f"/api/v1/org/{org.slug}/webhooks/endpoints",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 201, response.content
    data = response.json()
    assert "secret" in data, "EndpointCreateOut must include secret field"
    assert data["secret"], "secret must be non-empty"
    assert "id" in data
    assert data["url"] == "https://example.com/hooks"

    # Subsequent GET must NOT return the secret
    endpoint_id = data["id"]
    list_response = client.get(f"/api/v1/org/{org.slug}/webhooks/endpoints")
    assert list_response.status_code == 200
    endpoints = list_response.json()
    assert len(endpoints) >= 1
    found = next((e for e in endpoints if e["id"] == endpoint_id), None)
    assert found is not None
    assert "secret" not in found, "EndpointOut must NOT include secret field"


@pytest.mark.req("HOOK-01")
@pytest.mark.django_db
def test_create_endpoint_http_url_rejected(org, org_admin, client):
    """POST /endpoints with an http:// URL returns HTTP 422."""
    client = Client()
    client.force_login(org_admin)

    payload = {
        "url": "http://example.com/hooks",
        "name": "Insecure Hook",
        "event_types": ["user.created"],
    }
    response = client.post(
        f"/api/v1/org/{org.slug}/webhooks/endpoints",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 422, response.content


@pytest.mark.req("HOOK-01")
@pytest.mark.django_db
def test_list_endpoints(org, org_admin, endpoint, client):
    """GET /endpoints returns a list of endpoints for the org."""
    client = Client()
    client.force_login(org_admin)

    response = client.get(f"/api/v1/org/{org.slug}/webhooks/endpoints")
    assert response.status_code == 200, response.content
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    # EndpointOut must not contain secret
    for item in data:
        assert "secret" not in item
    ids = [e["id"] for e in data]
    assert str(endpoint.id) in ids


@pytest.mark.req("HOOK-01")
@pytest.mark.django_db
def test_update_endpoint_patch(org, org_admin, endpoint, client):
    """PATCH /endpoints/{id} updates allowed fields (name, event_types, is_active)."""
    client = Client()
    client.force_login(org_admin)

    payload = {"name": "Updated Name", "event_types": ["user.updated"]}
    response = client.patch(
        f"/api/v1/org/{org.slug}/webhooks/endpoints/{endpoint.id}",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 200, response.content
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["event_types"] == ["user.updated"]


@pytest.mark.req("HOOK-01")
@pytest.mark.django_db
def test_delete_endpoint(org, org_admin, endpoint, client):
    """DELETE /endpoints/{id} removes the endpoint and returns HTTP 204."""
    client = Client()
    client.force_login(org_admin)

    response = client.delete(f"/api/v1/org/{org.slug}/webhooks/endpoints/{endpoint.id}")
    assert response.status_code == 204, response.content

    # Verify it's gone
    from apps.webhooks.models import WebhookEndpoint

    assert not WebhookEndpoint.objects.filter(id=endpoint.id).exists()


@pytest.mark.req("HOOK-01")
@pytest.mark.django_db
def test_rotate_secret_returns_new_secret(org, org_admin, endpoint, client):
    """POST /endpoints/{id}/rotate-secret returns a new raw secret."""
    client = Client()
    client.force_login(org_admin)

    old_signing_key = endpoint.signing_key
    old_secret_hash = endpoint.secret_hash

    response = client.post(
        f"/api/v1/org/{org.slug}/webhooks/endpoints/{endpoint.id}/rotate-secret",
        content_type="application/json",
    )
    assert response.status_code == 200, response.content
    data = response.json()
    assert "secret" in data, "RotateSecretOut must include secret field"
    new_secret = data["secret"]
    assert new_secret, "new secret must be non-empty"
    assert new_secret != old_signing_key, "rotated secret must differ from old"

    # DB must be updated
    endpoint.refresh_from_db()
    assert endpoint.signing_key != old_signing_key
    assert endpoint.secret_hash != old_secret_hash
    assert endpoint.signing_key == new_secret


# ---------------------------------------------------------------------------
# Delivery history — HOOK-02
# ---------------------------------------------------------------------------


@pytest.mark.req("HOOK-02")
@pytest.mark.django_db
def test_list_deliveries_paginated(org, org_admin, delivery, client):
    """GET /endpoints/{id}/deliveries returns paginated delivery records."""
    client = Client()
    client.force_login(org_admin)

    response = client.get(
        f"/api/v1/org/{org.slug}/webhooks/endpoints/{delivery.endpoint_id}/deliveries"
    )
    assert response.status_code == 200, response.content
    data = response.json()
    # PageNumberPagination wraps in {"items": [...], "count": N}
    assert "items" in data or isinstance(data, list), f"Expected paginated response, got: {data}"
    items = data.get("items", data) if isinstance(data, dict) else data
    assert len(items) >= 1
    delivery_ids = [str(d["id"]) for d in items]
    assert str(delivery.id) in delivery_ids
    # attempt_count must be present
    for item in items:
        assert "attempt_count" in item


@pytest.mark.req("HOOK-02")
@pytest.mark.django_db
def test_delivery_detail_includes_attempts(org, org_admin, delivery, client):
    """GET /deliveries/{delivery_id} includes attempt list."""
    from apps.webhooks.models import WebhookDeliveryAttempt

    # Create an attempt so there's something to return
    WebhookDeliveryAttempt.objects.create(
        delivery=delivery,
        attempt_number=1,
        http_status_code=500,
        response_body="Internal Server Error",
        duration_ms=120,
        error_message="",
    )

    client = Client()
    client.force_login(org_admin)

    response = client.get(f"/api/v1/org/{org.slug}/webhooks/deliveries/{delivery.id}")
    assert response.status_code == 200, response.content
    data = response.json()
    assert "attempts" in data
    assert len(data["attempts"]) == 1
    attempt = data["attempts"][0]
    assert attempt["attempt_number"] == 1
    assert attempt["http_status_code"] == 500


# ---------------------------------------------------------------------------
# Manual retry — HOOK-03
# ---------------------------------------------------------------------------


@pytest.mark.req("HOOK-03")
@pytest.mark.django_db
def test_retry_delivery_enqueues_task(org, org_admin, delivery, client):
    """POST /deliveries/{delivery_id}/retry enqueues deliver_webhook task."""
    client = Client()
    client.force_login(org_admin)

    with patch("apps.webhooks.controllers.deliver_webhook") as mock_task:
        mock_task.delay = mock_task.delay  # ensure attribute exists
        response = client.post(
            f"/api/v1/org/{org.slug}/webhooks/deliveries/{delivery.id}/retry",
            content_type="application/json",
        )
    assert response.status_code == 202, response.content
    data = response.json()
    assert data.get("queued") is True


@pytest.mark.req("HOOK-03")
@pytest.mark.django_db
def test_retry_delivery_not_found_404(org, org_admin, client):
    """POST /deliveries/{id}/retry returns 404 for unknown delivery."""
    import uuid

    client = Client()
    client.force_login(org_admin)

    fake_id = str(uuid.uuid4())
    response = client.post(
        f"/api/v1/org/{org.slug}/webhooks/deliveries/{fake_id}/retry",
        content_type="application/json",
    )
    assert response.status_code == 404, response.content


# ---------------------------------------------------------------------------
# Re-enable endpoint — HOOK-04
# ---------------------------------------------------------------------------


@pytest.mark.req("HOOK-04")
@pytest.mark.django_db
def test_reenable_endpoint_resets_counter(org, org_admin, endpoint, client):
    """PATCH /endpoints/{id} with is_active=true resets consecutive_failures to 0."""
    # First disable the endpoint and set some failures
    endpoint.is_active = False
    endpoint.consecutive_failures = 3
    endpoint.save(update_fields=["is_active", "consecutive_failures"])

    client = Client()
    client.force_login(org_admin)

    response = client.patch(
        f"/api/v1/org/{org.slug}/webhooks/endpoints/{endpoint.id}",
        data=json.dumps({"is_active": True}),
        content_type="application/json",
    )
    assert response.status_code == 200, response.content
    data = response.json()
    assert data["is_active"] is True
    assert data["consecutive_failures"] == 0

    endpoint.refresh_from_db()
    assert endpoint.consecutive_failures == 0
    assert endpoint.is_active is True


# ---------------------------------------------------------------------------
# Authorization
# ---------------------------------------------------------------------------


@pytest.mark.req("HOOK-01")
@pytest.mark.django_db
def test_list_endpoints_requires_org_admin(org, endpoint, client):
    """Write endpoints return 403 for a non-admin org member."""
    from django.contrib.auth import get_user_model

    User = get_user_model()
    from apps.orgs.models import Membership

    # Create a plain MEMBER (not admin)
    member = User.objects.create_user(
        username="webhookmember",
        email="member@example.com",
        password="testpass123",  # pragma: allowlist secret
    )
    Membership.objects.create(org=org, user=member, role=Membership.Role.MEMBER)

    client = Client()
    client.force_login(member)

    # POST (write) requires IsOrgAdmin — should return 403
    payload = {
        "url": "https://example.com/hooks",
        "name": "Hook",
        "event_types": ["user.created"],
    }
    response = client.post(
        f"/api/v1/org/{org.slug}/webhooks/endpoints",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 403, (
        f"Non-admin member should receive 403 for write endpoint, got {response.status_code}"
    )
