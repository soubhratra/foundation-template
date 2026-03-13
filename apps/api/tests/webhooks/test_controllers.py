"""HTTP endpoint tests for the webhooks API controller.

HOOK-01: endpoint CRUD (create, list, update, delete, rotate-secret).
HOOK-02: paginated delivery history + delivery detail with attempts.
HOOK-03: manual retry.
HOOK-04: re-enable endpoint resets circuit breaker counter.
"""

import pytest

# ---------------------------------------------------------------------------
# Endpoint CRUD — HOOK-01
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_create_endpoint_returns_secret_once(org, org_admin, client):
    """POST /endpoints returns the raw secret in the response body (shown once only)."""
    pytest.fail("RED — not yet implemented")


@pytest.mark.django_db
def test_create_endpoint_http_url_rejected(org, org_admin, client):
    """POST /endpoints with an http:// URL returns HTTP 400."""
    pytest.fail("RED — not yet implemented")


@pytest.mark.django_db
def test_list_endpoints(org, org_admin, endpoint, client):
    """GET /endpoints returns a list of endpoints for the org."""
    pytest.fail("RED — not yet implemented")


@pytest.mark.django_db
def test_update_endpoint_patch(org, org_admin, endpoint, client):
    """PATCH /endpoints/{id} updates allowed fields (name, event_types, is_active)."""
    pytest.fail("RED — not yet implemented")


@pytest.mark.django_db
def test_delete_endpoint(org, org_admin, endpoint, client):
    """DELETE /endpoints/{id} removes the endpoint and returns HTTP 204."""
    pytest.fail("RED — not yet implemented")


@pytest.mark.django_db
def test_rotate_secret_returns_new_secret(org, org_admin, endpoint, client):
    """POST /endpoints/{id}/rotate-secret returns a new raw secret."""
    pytest.fail("RED — not yet implemented")


# ---------------------------------------------------------------------------
# Delivery history — HOOK-02
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_list_deliveries_paginated(org, org_admin, delivery, client):
    """GET /endpoints/{id}/deliveries returns paginated delivery records."""
    pytest.fail("RED — not yet implemented")


@pytest.mark.django_db
def test_delivery_detail_includes_attempts(org, org_admin, delivery, client):
    """GET /endpoints/{id}/deliveries/{delivery_id} includes attempt list."""
    pytest.fail("RED — not yet implemented")


# ---------------------------------------------------------------------------
# Manual retry — HOOK-03
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_retry_delivery_enqueues_task(org, org_admin, delivery, client):
    """POST /endpoints/{id}/deliveries/{delivery_id}/retry enqueues deliver_webhook task."""
    pytest.fail("RED — not yet implemented")


@pytest.mark.django_db
def test_retry_delivery_not_found_404(org, org_admin, client):
    """POST /endpoints/{id}/deliveries/{delivery_id}/retry returns 404 for unknown delivery."""
    pytest.fail("RED — not yet implemented")


# ---------------------------------------------------------------------------
# Re-enable endpoint — HOOK-04
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_reenable_endpoint_resets_counter(org, org_admin, endpoint, client):
    """PATCH /endpoints/{id} with is_active=true resets consecutive_failures to 0."""
    pytest.fail("RED — not yet implemented")


# ---------------------------------------------------------------------------
# Authorization
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_list_endpoints_requires_org_admin(org, endpoint, client):
    """GET /endpoints returns 403 for a non-admin org member."""
    pytest.fail("RED — not yet implemented")
