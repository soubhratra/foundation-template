import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def user(db):
    """A basic authenticated User instance."""
    return User.objects.create_user(
        username="billingtest",
        email="billingtest@example.com",
        password="testpass123",
    )


@pytest.fixture
def customer(user):
    """A Customer linked to the test user.

    Uses importorskip so this fixture is skipped if the billing module
    is not yet installed — Wave 1 enables it.
    """
    billing_models = pytest.importorskip("apps.billing.models")
    customer, _ = billing_models.Customer.objects.get_or_create(user=user)
    return customer


# ---------------------------------------------------------------------------
# StubAdapter — in-memory implementation of PaymentAdapter for unit tests.
# Returns deterministic dicts; no network calls, no Django settings required.
# ---------------------------------------------------------------------------

from apps.billing.adapters import PaymentAdapter  # noqa: E402


class StubAdapter(PaymentAdapter):
    """Test double for PaymentAdapter. All methods return predictable dicts."""

    def create_customer(self, user_id: str, email: str) -> dict:
        return {"provider_customer_id": "cus_stub"}

    def create_checkout_session(
        self, customer_id, price_id, mode, success_url, cancel_url, trial_days=0
    ) -> dict:
        return {
            "checkout_url": "https://checkout.example.com",
            "session_id": "cs_test_stub",
            "price_id": price_id,
            "mode": mode,
        }

    def create_portal_session(self, customer_id, return_url) -> dict:
        return {"portal_url": "https://portal.example.com"}

    def cancel_subscription(self, subscription_id, cancel_at_period_end=True) -> dict:
        return {
            "subscription_id": subscription_id,
            "status": "active",
            "cancel_at_period_end": cancel_at_period_end,
        }

    def modify_subscription(
        self, subscription_id, new_price_id, proration_behavior="create_prorations"
    ) -> dict:
        return {
            "subscription_id": subscription_id,
            "status": "active",
            "proration_behavior": proration_behavior,
            "new_price_id": new_price_id,
        }

    def construct_webhook_event(self, payload, signature_header, webhook_secret) -> dict:
        return {"id": "evt_stub", "type": "test.event", "data": {}}

    def record_usage(self, meter_event_name, customer_id, value, identifier=None) -> dict:
        return {"identifier": identifier or "stub_identifier"}

    def list_invoices(self, customer_id, limit=10) -> list:
        return []

    def preview_proration(self, subscription_id, new_price_id, proration_date=None) -> dict:
        return {
            "amount_due_now": 500,
            "next_invoice_total": 1000,
            "proration_date": 1700000000,
            "currency": "usd",
        }

    def get_usage_summary(self, subscription_item_id) -> dict:
        return {
            "total_usage": 42,
            "period_start": 1700000000,
            "period_end": 1702678400,
        }


@pytest.fixture
def stub_adapter():
    """A StubAdapter instance for unit testing BillingService."""
    return StubAdapter()


@pytest.fixture
def plan_mapping(db):
    """A PlanProviderMapping for plan_id='pro', billing_period='monthly'."""
    from apps.billing.models import PlanProviderMapping

    mapping, _ = PlanProviderMapping.objects.get_or_create(
        plan_id="pro",
        provider="stub",
        billing_period="monthly",
        defaults={"price_id": "price_pro_monthly", "is_active": True},
    )
    return mapping


@pytest.fixture
def subscription(db, user):
    """A Customer + active Subscription for the test user."""
    from apps.billing.models import Customer, Subscription, SubscriptionStatus

    cust, _ = Customer.objects.get_or_create(
        user=user,
        defaults={"stripe_customer_id": "cus_stub_customer"},
    )
    sub, _ = Subscription.objects.get_or_create(
        customer=cust,
        defaults={
            "stripe_subscription_id": "sub_stub",
            "status": SubscriptionStatus.ACTIVE,
            "cancel_at_period_end": False,
        },
    )
    return sub


@pytest.fixture
def billing_service(stub_adapter):
    """BillingService wired with StubAdapter — no network calls."""
    from apps.billing.services import BillingService

    return BillingService(adapter=stub_adapter)
