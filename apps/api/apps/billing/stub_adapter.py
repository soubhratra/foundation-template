"""
StubAdapter — in-memory PaymentAdapter for development and automated testing.

Configured via BILLING_ADAPTER = "apps.billing.stub_adapter.StubAdapter"
in development settings. Returns deterministic dicts; no network calls.
"""

from typing import Any

from apps.billing.adapters import PaymentAdapter


class StubAdapter(PaymentAdapter):
    """Test double for PaymentAdapter. All methods return predictable dicts."""

    def create_customer(self, user_id: str, email: str) -> dict[str, Any]:
        return {"provider_customer_id": "cus_stub"}

    def create_checkout_session(
        self,
        customer_id: str,
        price_id: str,
        mode: str,
        success_url: str,
        cancel_url: str,
        trial_days: int = 0,
    ) -> dict[str, Any]:
        return {
            "checkout_url": "https://checkout.example.com",
            "session_id": "cs_test_stub",
            "price_id": price_id,
            "mode": mode,
        }

    def create_portal_session(self, customer_id: str, return_url: str) -> dict[str, Any]:
        return {"portal_url": "https://portal.example.com"}

    def cancel_subscription(
        self, subscription_id: str, cancel_at_period_end: bool = True
    ) -> dict[str, Any]:
        return {
            "subscription_id": subscription_id,
            "status": "active",
            "cancel_at_period_end": cancel_at_period_end,
        }

    def modify_subscription(
        self,
        subscription_id: str,
        new_price_id: str,
        proration_behavior: str = "create_prorations",
    ) -> dict[str, Any]:
        return {
            "subscription_id": subscription_id,
            "status": "active",
            "proration_behavior": proration_behavior,
            "new_price_id": new_price_id,
        }

    def construct_webhook_event(
        self, payload: bytes, signature_header: str, webhook_secret: str
    ) -> dict[str, Any]:
        return {"id": "evt_stub", "type": "test.event", "data": {}}

    def record_usage(
        self,
        meter_event_name: str,
        customer_id: str,
        value: int,
        identifier: str | None = None,
    ) -> dict[str, Any]:
        return {"identifier": identifier or "stub_identifier"}

    def list_invoices(self, customer_id: str, limit: int = 10) -> list[dict[str, Any]]:
        from apps.billing.models import Customer

        try:
            customer = Customer.objects.get(stripe_customer_id=customer_id)
        except (Customer.DoesNotExist, Customer.MultipleObjectsReturned):
            return []
        return [
            {
                "invoice_id": str(p.id),
                "amount": int(p.amount * 100),
                "currency": p.currency,
                "status": p.status,
                "created": int(p.created_at.timestamp()),
                "invoice_url": None,
            }
            for p in customer.payments.order_by("-created_at")[:limit]
        ]

    def preview_proration(
        self,
        subscription_id: str,
        new_price_id: str,
        proration_date: int | None = None,
    ) -> dict[str, Any]:
        return {
            "amount_due_now": 500,
            "next_invoice_total": 1000,
            "proration_date": 1700000000,
            "currency": "usd",
        }

    def get_usage_summary(self, subscription_item_id: str) -> dict[str, Any]:
        return {
            "total_usage": 42,
            "period_start": 1700000000,
            "period_end": 1702678400,
        }

    def retrieve_subscription(self, subscription_id: str) -> dict[str, Any]:
        """Return a deterministic stub price ID for plan mapping lookups."""
        return {"current_price_id": "price_stub_monthly"}

    def reactivate_subscription(self, subscription_id: str) -> dict[str, Any]:
        """Undo pending cancellation — returns subscription as active."""
        return {
            "subscription_id": subscription_id,
            "status": "active",
            "cancel_at_period_end": False,
        }
