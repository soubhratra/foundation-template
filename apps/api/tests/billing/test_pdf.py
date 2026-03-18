"""
TDD test suite for invoice PDF generation.

Task 1 (RED): test_render_invoice_pdf_returns_bytes, test_render_invoice_pdf_contains_pdf_header
Task 2 (RED): test_pdf_task_is_shared_task, test_request_invoice_pdf_returns_task_id,
test_pdf_polling_pending
"""

import json

import pytest
from django.test import Client

from apps.billing.pdf import render_invoice_pdf

# ---------------------------------------------------------------------------
# Shared invoice_data fixture
# ---------------------------------------------------------------------------

SAMPLE_INVOICE_DATA = {
    "reference": "PAY-1",
    "date": "2026-03-10",
    "customer_email": "a@b.com",
    "description": "Pro Monthly",
    "amount": 29.00,
    "currency": "usd",
}


# ---------------------------------------------------------------------------
# Task 1 — PDF rendering layer tests
# ---------------------------------------------------------------------------


@pytest.mark.req("BILL-03")
def test_render_invoice_pdf_returns_bytes():
    """render_invoice_pdf must return non-empty bytes."""
    result = render_invoice_pdf(SAMPLE_INVOICE_DATA)
    assert isinstance(result, bytes) and len(result) > 0


@pytest.mark.req("BILL-03")
def test_render_invoice_pdf_contains_pdf_header():
    """The returned bytes must start with the PDF magic bytes %PDF."""
    result = render_invoice_pdf(SAMPLE_INVOICE_DATA)
    assert result[:4] == b"%PDF"


# ---------------------------------------------------------------------------
# Task 2 — Celery task tests
# ---------------------------------------------------------------------------


@pytest.mark.req("BILL-03")
def test_pdf_task_is_shared_task():
    """generate_invoice_pdf must be a registered Celery task with a .delay attribute."""
    from apps.billing.tasks import generate_invoice_pdf

    assert hasattr(generate_invoice_pdf, "delay")


# ---------------------------------------------------------------------------
# Task 2 — Controller integration tests
# ---------------------------------------------------------------------------


@pytest.fixture
def payment(db, subscription):
    """A Payment owned by the subscription's customer."""
    from apps.billing.models import Payment

    return Payment.objects.create(
        customer=subscription.customer,
        stripe_payment_intent_id="pi_test",
        amount="29.00",
        currency="usd",
        status="succeeded",
    )


@pytest.fixture
def authenticated_client(db, subscription):
    """Django test client authenticated as the user who owns the test subscription."""
    client = Client()
    user = subscription.customer.user
    client.force_login(user=user)
    return client


@pytest.mark.req("BILL-03")
@pytest.mark.django_db
def test_request_invoice_pdf_returns_task_id(authenticated_client, payment, monkeypatch):
    """POST /billing/invoices/{payment_id}/pdf returns 200 with task_id and status=pending.

    generate_invoice_pdf.delay is mocked to avoid needing a running Redis broker
    in the test environment — this test verifies the controller wiring only.
    """
    from unittest.mock import MagicMock

    import apps.billing.tasks as billing_tasks

    mock_task_result = MagicMock()
    mock_task_result.id = "fake-task-uuid-1234"
    monkeypatch.setattr(billing_tasks.generate_invoice_pdf, "delay", lambda data: mock_task_result)

    response = authenticated_client.post(f"/api/v1/billing/invoices/{payment.pk}/pdf")
    assert response.status_code == 200
    data = json.loads(response.content)
    assert "task_id" in data
    assert data["status"] == "pending"


@pytest.mark.req("BILL-03")
@pytest.mark.django_db
def test_pdf_polling_pending(authenticated_client, monkeypatch):
    """GET /billing/invoices/pdf-status/{task_id} returns {status: pending} when task not done."""
    from unittest.mock import MagicMock

    mock_result = MagicMock()
    mock_result.state = "PENDING"

    import celery.result

    monkeypatch.setattr(celery.result, "AsyncResult", lambda task_id: mock_result)

    response = authenticated_client.get("/api/v1/billing/invoices/pdf-status/fake-task-id")
    assert response.status_code == 200
    data = json.loads(response.content)
    assert data["status"] == "pending"
