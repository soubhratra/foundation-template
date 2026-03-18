"""
RED test suite for BillingController — Plan 01 scaffold.

All 8 tests are expected to FAIL in this phase because controller methods
raise NotImplementedError (→ 500 response). These tests drive Plan 02
implementation.

Fixtures used:
  - subscription    (from billing conftest.py) — creates Customer + active Subscription
  - authenticated_client (overridden below)    — Django test client logged in as the
                                                  same user that owns the subscription
"""

import json

import pytest
from django.test import Client


@pytest.fixture
def authenticated_client(db, subscription):
    """
    Django test client authenticated as the user who owns the test subscription.

    Overrides the root conftest authenticated_client to ensure the logged-in
    user is the same one whose Customer/Subscription was created by the
    `subscription` fixture.
    """
    client = Client()
    user = subscription.customer.user
    client.force_login(user=user)
    return client


# ---------------------------------------------------------------------------
# GET /api/v1/billing/status
# ---------------------------------------------------------------------------


@pytest.mark.req("BILL-01", "BILL-02")
@pytest.mark.django_db
def test_get_status(authenticated_client, subscription):
    """GET /api/v1/billing/status returns 200 with status, cancel_at_period_end, period_end."""
    response = authenticated_client.get("/api/v1/billing/status")
    assert response.status_code == 200
    data = json.loads(response.content)
    assert "status" in data
    assert "cancel_at_period_end" in data
    assert "current_period_end" in data


# ---------------------------------------------------------------------------
# GET /api/v1/billing/subscription
# ---------------------------------------------------------------------------


@pytest.mark.req("BILL-01", "BILL-02")
@pytest.mark.django_db
def test_get_subscription(authenticated_client, subscription):
    """GET /api/v1/billing/subscription returns 200 with full subscription detail."""
    response = authenticated_client.get("/api/v1/billing/subscription")
    assert response.status_code == 200
    data = json.loads(response.content)
    assert "status" in data
    assert "plan_id" in data
    assert "billing_period" in data
    assert "current_period_end" in data


# ---------------------------------------------------------------------------
# GET /api/v1/billing/invoices
# ---------------------------------------------------------------------------


@pytest.mark.req("BILL-02")
@pytest.mark.django_db
def test_list_invoices(authenticated_client, subscription):
    """GET /api/v1/billing/invoices returns 200 with {invoices, total}."""
    response = authenticated_client.get("/api/v1/billing/invoices")
    assert response.status_code == 200
    data = json.loads(response.content)
    assert "invoices" in data
    assert "total" in data
    assert isinstance(data["invoices"], list)


@pytest.mark.req("BILL-02")
@pytest.mark.django_db
def test_list_invoices_fields(authenticated_client, subscription):
    """Invoice items in the list include all required fields."""
    response = authenticated_client.get("/api/v1/billing/invoices")
    assert response.status_code == 200
    data = json.loads(response.content)
    # When invoices are present each item must have the required fields.
    # StubAdapter.list_invoices returns [], so this test verifies the contract
    # but will also fail due to NotImplementedError in RED phase.
    for invoice in data.get("invoices", []):
        assert "invoice_id" in invoice
        assert "amount" in invoice
        assert "currency" in invoice
        assert "status" in invoice
        assert "created" in invoice
        assert "invoice_url" in invoice


# ---------------------------------------------------------------------------
# POST /api/v1/billing/subscription/change
# ---------------------------------------------------------------------------


@pytest.mark.req("BILL-02")
@pytest.mark.django_db
def test_change_plan(authenticated_client, subscription):
    """POST /api/v1/billing/subscription/change with {plan_id, billing_period} returns 200."""
    payload = json.dumps({"plan_id": "pro", "billing_period": "monthly"})
    response = authenticated_client.post(
        "/api/v1/billing/subscription/change",
        data=payload,
        content_type="application/json",
    )
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# POST /api/v1/billing/subscription/cancel
# ---------------------------------------------------------------------------


@pytest.mark.req("BILL-02")
@pytest.mark.django_db
def test_cancel_subscription(authenticated_client, subscription):
    """POST /api/v1/billing/subscription/cancel returns 200 with cancel_at_period_end=True."""
    response = authenticated_client.post("/api/v1/billing/subscription/cancel")
    assert response.status_code == 200
    data = json.loads(response.content)
    assert data.get("cancel_at_period_end") is True


# ---------------------------------------------------------------------------
# POST /api/v1/billing/portal-session
# ---------------------------------------------------------------------------


@pytest.mark.req("BILL-02")
@pytest.mark.django_db
def test_portal_session(authenticated_client, subscription):
    """POST /api/v1/billing/portal-session returns 200 with {portal_url}."""
    response = authenticated_client.post("/api/v1/billing/portal-session")
    assert response.status_code == 200
    data = json.loads(response.content)
    assert "portal_url" in data
    assert isinstance(data["portal_url"], str)


# ---------------------------------------------------------------------------
# POST /api/v1/billing/proration-preview
# ---------------------------------------------------------------------------


@pytest.mark.req("BILL-02")
@pytest.mark.django_db
def test_proration_preview(authenticated_client, subscription):
    """POST /api/v1/billing/proration-preview returns 200 with proration amounts."""
    payload = json.dumps({"plan_id": "pro", "billing_period": "monthly"})
    response = authenticated_client.post(
        "/api/v1/billing/proration-preview",
        data=payload,
        content_type="application/json",
    )
    assert response.status_code == 200
    data = json.loads(response.content)
    assert "amount_due_now" in data
    assert "next_invoice_total" in data
    assert "proration_date" in data
    assert "currency" in data
