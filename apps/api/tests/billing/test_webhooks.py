"""
Tests for the Stripe webhook view (webhooks.py).
Covers: HOOK-01 (HMAC verification), HOOK-02 (async dispatch)

View contract:
- POST /api/v1/billing/webhooks/ with valid HMAC → 200 immediately
- POST with invalid HMAC → 400
- POST with valid HMAC but broker down → 500
"""

from unittest.mock import MagicMock, patch

import pytest
from django.test import Client


@pytest.fixture
def client():
    return Client()


# The URL that should be registered after Plan 10-01
WEBHOOK_URL = "/api/v1/billing/webhooks/"


class TestWebhookViewStructure:
    """HOOK-01: View exists and rejects requests without a valid signature."""

    @pytest.mark.req("BILL-02")
    @pytest.mark.django_db
    def test_webhook_view_structure(self, client):
        """POST without Stripe-Signature header → 400 (view exists, rejects bad requests)."""
        # No mocking — adapter will be called with empty signature, should raise ValueError
        with patch("apps.billing.webhooks.get_adapter") as mock_get_adapter:
            mock_adapter = MagicMock()
            mock_adapter.construct_webhook_event.side_effect = ValueError("No signature provided")
            mock_get_adapter.return_value = mock_adapter

            response = client.post(
                WEBHOOK_URL,
                data=b'{"id":"evt_test","type":"test"}',
                content_type="application/json",
            )

        assert response.status_code == 400


class TestValidSignatureReturns200:
    """HOOK-01: Valid HMAC signature results in 200 and async dispatch."""

    @pytest.mark.req("BILL-02")
    @pytest.mark.django_db
    def test_valid_signature_returns_200(self, client):
        """Mock adapter returns valid event dict, mock .delay — POST returns 200 immediately."""
        mock_event = {
            "id": "evt_test_123",
            "type": "customer.subscription.created",
            "data": {
                "object": {
                    "id": "sub_test_123",
                    "customer": "cus_test_123",
                    "status": "active",
                }
            },
        }

        with (
            patch("apps.billing.webhooks.get_adapter") as mock_get_adapter,
            patch("apps.billing.webhooks.process_stripe_event") as mock_task,
        ):
            mock_adapter = MagicMock()
            mock_adapter.construct_webhook_event.return_value = mock_event
            mock_get_adapter.return_value = mock_adapter
            mock_task.delay = MagicMock(return_value=None)

            response = client.post(
                WEBHOOK_URL,
                data=b'{"id":"evt_test_123","type":"customer.subscription.created"}',
                content_type="application/json",
                HTTP_STRIPE_SIGNATURE="t=1,v1=abc123",
            )

        assert response.status_code == 200
        mock_task.delay.assert_called_once_with(
            event_id="evt_test_123",
            event_type="customer.subscription.created",
            event_data={
                "id": "sub_test_123",
                "customer": "cus_test_123",
                "status": "active",
            },
        )


class TestInvalidSignatureReturns400:
    """HOOK-01: Invalid HMAC results in 400."""

    @pytest.mark.req("BILL-02")
    @pytest.mark.django_db
    def test_invalid_signature_returns_400(self, client):
        """Mock adapter raises ValueError → POST returns 400."""
        with patch("apps.billing.webhooks.get_adapter") as mock_get_adapter:
            mock_adapter = MagicMock()
            mock_adapter.construct_webhook_event.side_effect = ValueError(
                "Signature verification failed"
            )
            mock_get_adapter.return_value = mock_adapter

            response = client.post(
                WEBHOOK_URL,
                data=b'{"id":"evt_test"}',
                content_type="application/json",
                HTTP_STRIPE_SIGNATURE="t=1,v1=bad_signature",
            )

        assert response.status_code == 400


class TestDispatchFailureReturns500:
    """HOOK-02: Celery dispatch failure → 500 so Stripe will retry."""

    @pytest.mark.req("BILL-02")
    @pytest.mark.django_db
    def test_dispatch_failure_returns_500(self, client):
        """Mock adapter succeeds, mock .delay raises Exception → POST returns 500."""
        mock_event = {
            "id": "evt_test_456",
            "type": "invoice.payment_succeeded",
            "data": {"object": {"id": "in_test_456"}},
        }

        with (
            patch("apps.billing.webhooks.get_adapter") as mock_get_adapter,
            patch("apps.billing.webhooks.process_stripe_event") as mock_task,
        ):
            mock_adapter = MagicMock()
            mock_adapter.construct_webhook_event.return_value = mock_event
            mock_get_adapter.return_value = mock_adapter
            mock_task.delay = MagicMock(side_effect=Exception("Redis connection refused"))

            response = client.post(
                WEBHOOK_URL,
                data=b'{"id":"evt_test_456","type":"invoice.payment_succeeded"}',
                content_type="application/json",
                HTTP_STRIPE_SIGNATURE="t=1,v1=valid_sig",
            )

        assert response.status_code == 500
