"""
Tests for billing data models.
Covers: CUST-01 (Customer model), SUB-06 (SubscriptionStatus + audit fields), PAY-02 (Payment model)
"""

from decimal import Decimal  # noqa: F401 — used in type checks within tests

import pytest

# importorskip skips this entire file if apps.billing.models cannot be imported.
# This handles two cases:
# 1. Module not on disk (ImportError) — Wave 0, billing not yet installed
# 2. Module on disk but app not in INSTALLED_APPS (RuntimeError from Django metaclass)
try:
    billing_models = pytest.importorskip("apps.billing.models")
except RuntimeError as exc:
    pytest.skip(f"apps.billing not registered in INSTALLED_APPS: {exc}", allow_module_level=True)

Customer = billing_models.Customer
Subscription = billing_models.Subscription
Payment = billing_models.Payment
ProcessedWebhookEvent = billing_models.ProcessedWebhookEvent
SubscriptionStatus = billing_models.SubscriptionStatus


class TestCustomerModel:
    """CUST-01: Customer model with OneToOne User link."""

    def test_customer_created_with_user(self, customer, user):
        assert customer.user == user

    def test_customer_stripe_customer_id_blank_by_default(self, customer):
        """stripe_customer_id is populated lazily — blank on creation is valid."""
        assert customer.stripe_customer_id == "" or customer.stripe_customer_id is None

    def test_customer_has_timestamps(self, customer):
        assert customer.created_at is not None
        assert customer.updated_at is not None

    def test_customer_str(self, customer, user):
        assert str(user.email) in str(customer)


class TestSubscriptionStatus:
    """SUB-06: SubscriptionStatus is a Django TextChoices enum with full Stripe-matching values."""

    def test_required_statuses_exist(self):
        required = {
            "active",
            "past_due",
            "canceled",
            "trialing",
            "incomplete",
            "incomplete_expired",
            "unpaid",
        }
        actual = {choice.value for choice in SubscriptionStatus}
        assert required == actual, (
            f"SubscriptionStatus values mismatch.\nExpected: {required}\nGot: {actual}"
        )

    def test_is_text_choices(self):
        from django.db.models import TextChoices

        assert issubclass(SubscriptionStatus, TextChoices)


class TestSubscriptionModel:
    """SUB-06: Subscription model audit fields and cancel_at_period_end."""

    def test_subscription_has_cancel_at_period_end(self):
        field_names = [f.name for f in Subscription._meta.get_fields()]
        assert "cancel_at_period_end" in field_names

    def test_subscription_has_period_timestamps(self):
        field_names = [f.name for f in Subscription._meta.get_fields()]
        assert "current_period_start" in field_names
        assert "current_period_end" in field_names

    def test_subscription_status_uses_enum(self):
        status_field = Subscription._meta.get_field("status")
        assert status_field.choices, "status field must have choices from SubscriptionStatus"


class TestPaymentModel:
    """PAY-02: Payment model records one-time payment with amount and status."""

    def test_payment_has_amount_field(self):
        from django.db.models import DecimalField

        amount_field = Payment._meta.get_field("amount")
        assert isinstance(amount_field, DecimalField)

    def test_payment_has_required_fields(self):
        field_names = [f.name for f in Payment._meta.get_fields()]
        for required in ["stripe_payment_intent_id", "amount", "currency", "status"]:
            assert required in field_names, f"Payment model missing field: {required}"


class TestProcessedWebhookEvent:
    """HOOK-03 prerequisite: ProcessedWebhookEvent unique_together constraint."""

    def test_unique_together_provider_event_id(self):
        unique_together = ProcessedWebhookEvent._meta.unique_together
        # Check either unique_together or UniqueConstraint covers (provider, event_id)
        field_set = {"provider", "event_id"}
        covered = any(set(combo) == field_set for combo in unique_together)
        if not covered:
            constraints = [
                set(c.fields)
                for c in ProcessedWebhookEvent._meta.constraints
                if hasattr(c, "fields")
            ]
            covered = field_set in constraints
        assert covered, "ProcessedWebhookEvent must have unique_together on (provider, event_id)"
