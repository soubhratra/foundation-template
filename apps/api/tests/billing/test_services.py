"""
Unit tests for BillingService.

All tests use StubAdapter injected via BillingService(adapter=stub) —
zero real HTTP calls to Stripe. DB fixtures create minimal ORM state.

Covers: SUB-01–05, PAY-01, USAGE-01–02
"""

import pytest

BillingService = pytest.importorskip("apps.billing.services").BillingService


class TestCreateCheckoutSession:
    """SUB-01: create_checkout_session resolves plan_id → price_id via PlanProviderMapping."""

    def test_create_checkout_session(self, billing_service, subscription, plan_mapping):
        user = subscription.customer.user
        result = billing_service.create_checkout_session(
            user=user,
            plan_id="pro",
            billing_period="monthly",
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel",
        )
        assert result["checkout_url"] == "https://checkout.example.com"
        assert result["session_id"] == "cs_test_stub"
        # Verify the price_id was resolved from PlanProviderMapping, not hardcoded
        assert result["price_id"] == "price_pro_monthly"
        assert result["mode"] == "subscription"

    def test_missing_price_mapping_raises(self, billing_service, user):
        """User with no PlanProviderMapping raises ServiceError.

        Note: Every user auto-gets a Customer via post_save signal, so
        'no_customer' is not a reachable error in normal flow. Testing
        the next error in the chain: missing price mapping.
        """
        from apps.core.exceptions import ServiceError

        # No plan_mapping fixture → PlanProviderMapping does not exist for "unknown_plan"
        with pytest.raises(ServiceError) as exc_info:
            billing_service.create_checkout_session(
                user=user,
                plan_id="unknown_plan",
                billing_period="monthly",
                success_url="https://example.com/success",
                cancel_url="https://example.com/cancel",
            )
        assert exc_info.value.status_code == 400
        assert exc_info.value.code == "no_price_mapping"


class TestUpgradeSubscription:
    """SUB-02: upgrade_subscription calls modify_subscription with create_prorations."""

    def test_upgrade_subscription(self, billing_service, subscription, plan_mapping):
        user = subscription.customer.user
        result = billing_service.upgrade_subscription(
            user=user,
            new_plan_id="pro",
            billing_period="monthly",
        )
        assert result["proration_behavior"] == "create_prorations"
        assert result["new_price_id"] == "price_pro_monthly"
        assert result["subscription_id"] == "sub_stub"


class TestDowngradeSubscription:
    """SUB-03: downgrade_subscription calls modify_subscription with always_invoice."""

    def test_downgrade_subscription(self, billing_service, subscription, plan_mapping):
        user = subscription.customer.user
        result = billing_service.downgrade_subscription(
            user=user,
            new_plan_id="pro",
            billing_period="monthly",
        )
        assert result["proration_behavior"] == "always_invoice"
        assert result["new_price_id"] == "price_pro_monthly"


class TestCancelSubscription:
    """SUB-04: cancel_subscription sets cancel_at_period_end on both adapter and DB."""

    def test_cancel_subscription(self, billing_service, subscription):
        user = subscription.customer.user
        result = billing_service.cancel_subscription(user=user)
        assert result["cancel_at_period_end"] is True

        # Verify DB state persisted
        subscription.refresh_from_db()
        assert subscription.cancel_at_period_end is True


class TestReactivateSubscription:
    """SUB-05: reactivate_subscription undoes cancel_at_period_end (no plan change)."""

    def test_reactivate_subscription(self, billing_service, subscription):
        from apps.billing.models import SubscriptionStatus

        # Set up subscription in a pending-cancellation state.
        subscription.status = SubscriptionStatus.ACTIVE
        subscription.cancel_at_period_end = True
        subscription.save()

        user = subscription.customer.user
        result = billing_service.reactivate_subscription(user=user)
        assert result["subscription_id"] == "sub_stub"
        assert result["cancel_at_period_end"] is False

        # Verify the local DB record was updated.
        subscription.refresh_from_db()
        assert subscription.cancel_at_period_end is False


class TestOneTimePayment:
    """PAY-01: create_one_time_payment creates checkout session in 'payment' mode."""

    def test_one_time_payment(self, billing_service, subscription):
        user = subscription.customer.user
        result = billing_service.create_one_time_payment(
            user=user,
            price_id="price_one_time_99",
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel",
        )
        assert result["mode"] == "payment"
        assert result["checkout_url"] == "https://checkout.example.com"
        assert result["price_id"] == "price_one_time_99"


class TestRecordUsage:
    """USAGE-01: record_usage delegates to adapter with customer's stripe_customer_id."""

    def test_record_usage(self, billing_service, subscription):
        user = subscription.customer.user
        result = billing_service.record_usage(
            user=user,
            meter_event_name="api_calls",
            value=10,
        )
        assert "identifier" in result


class TestGetUsageSummary:
    """USAGE-02: get_usage_summary delegates to adapter."""

    def test_get_usage_summary(self, billing_service, subscription):
        user = subscription.customer.user
        result = billing_service.get_usage_summary(
            user=user,
            subscription_item_id="si_xxx",
        )
        assert result["total_usage"] == 42
        assert "period_start" in result
        assert "period_end" in result


class TestPreviewProration:
    """SUB-02 extended: preview_proration returns proration amounts."""

    def test_preview_proration(self, billing_service, subscription, plan_mapping):
        user = subscription.customer.user
        result = billing_service.preview_proration(
            user=user,
            new_plan_id="pro",
            billing_period="monthly",
        )
        assert "amount_due_now" in result
        assert "next_invoice_total" in result
        assert "proration_date" in result
        assert "currency" in result
        assert isinstance(result["amount_due_now"], int)
