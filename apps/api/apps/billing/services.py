"""
BillingService — all billing operations.

Controllers call this exclusively; no ORM or adapter access in controllers.

Usage:
    service = BillingService()           # uses BILLING_ADAPTER from settings
    service = BillingService(adapter=stub)  # testable without Stripe
"""

import logging
from typing import Any

from apps.billing.models import Customer, PlanProviderMapping, Subscription
from apps.core.exceptions import ServiceError

logger = logging.getLogger(__name__)


class BillingService:
    """Orchestrates all billing operations via a PaymentAdapter.

    Dependency-injection pattern: pass `adapter=` in tests to avoid
    touching Django settings or making real HTTP calls to Stripe.
    """

    def __init__(self, adapter: Any = None) -> None:
        if adapter is None:
            from .utils import get_adapter

            self._adapter = get_adapter()
        else:
            self._adapter = adapter

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_customer(self, user: Any) -> Customer:
        """Return the billing Customer for a user, or raise ServiceError."""
        try:
            return user.billing_customer
        except Customer.DoesNotExist as exc:
            raise ServiceError(
                code="no_customer",
                message="No billing customer record found.",
                status_code=404,
            ) from exc

    def _get_provider_name(self) -> str:
        """Derive provider name from adapter class name (e.g. StripeAdapter → 'stripe')."""
        return type(self._adapter).__name__.lower().replace("adapter", "")

    def _resolve_price_id(self, plan_id: str, billing_period: str) -> str:
        """Look up the provider price_id from PlanProviderMapping."""
        try:
            mapping = PlanProviderMapping.objects.get(
                plan_id=plan_id,
                provider=self._get_provider_name(),
                billing_period=billing_period,
                is_active=True,
            )
            return mapping.price_id
        except PlanProviderMapping.DoesNotExist as exc:
            raise ServiceError(
                code="no_price_mapping",
                message=f"No active price mapping for plan={plan_id} period={billing_period}",
                status_code=400,
            ) from exc

    # ------------------------------------------------------------------
    # Subscription lifecycle
    # ------------------------------------------------------------------

    def create_checkout_session(
        self,
        user: Any,
        plan_id: str,
        billing_period: str,
        success_url: str,
        cancel_url: str,
        trial_days: int = 0,
    ) -> dict[str, Any]:
        """Create a hosted subscription checkout session."""
        customer = self._get_customer(user)
        price_id = self._resolve_price_id(plan_id, billing_period)
        return self._adapter.create_checkout_session(
            customer_id=customer.stripe_customer_id,
            price_id=price_id,
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
            trial_days=trial_days,
        )

    def upgrade_subscription(
        self,
        user: Any,
        new_plan_id: str,
        billing_period: str = "monthly",
    ) -> dict[str, Any]:
        """Upgrade to a higher plan with immediate proration."""
        customer = self._get_customer(user)
        sub: Subscription = customer.subscription
        new_price_id = self._resolve_price_id(new_plan_id, billing_period)
        return self._adapter.modify_subscription(
            subscription_id=sub.stripe_subscription_id,
            new_price_id=new_price_id,
            proration_behavior="create_prorations",
        )

    def downgrade_subscription(
        self,
        user: Any,
        new_plan_id: str,
        billing_period: str = "monthly",
    ) -> dict[str, Any]:
        """Downgrade to a lower plan, issuing an invoice for remaining credit."""
        customer = self._get_customer(user)
        sub: Subscription = customer.subscription
        new_price_id = self._resolve_price_id(new_plan_id, billing_period)
        return self._adapter.modify_subscription(
            subscription_id=sub.stripe_subscription_id,
            new_price_id=new_price_id,
            proration_behavior="always_invoice",
        )

    def cancel_subscription(
        self,
        user: Any,
        cancel_at_period_end: bool = True,
    ) -> dict[str, Any]:
        """Cancel a subscription, optionally at the end of the billing period.

        Persists cancel_at_period_end to the local Subscription record so the
        UI can reflect pending cancellation without an extra Stripe round-trip.
        """
        customer = self._get_customer(user)
        sub: Subscription = customer.subscription
        result = self._adapter.cancel_subscription(
            subscription_id=sub.stripe_subscription_id,
            cancel_at_period_end=cancel_at_period_end,
        )
        sub.cancel_at_period_end = cancel_at_period_end
        sub.save(update_fields=["cancel_at_period_end", "updated_at"])
        return result

    def reactivate_subscription(
        self,
        user: Any,
        plan_id: str,
        billing_period: str = "monthly",
    ) -> dict[str, Any]:
        """Reactivate a canceled subscription by restoring an active price."""
        customer = self._get_customer(user)
        sub: Subscription = customer.subscription
        new_price_id = self._resolve_price_id(plan_id, billing_period)
        return self._adapter.modify_subscription(
            subscription_id=sub.stripe_subscription_id,
            new_price_id=new_price_id,
            proration_behavior="create_prorations",
        )

    def preview_proration(
        self,
        user: Any,
        new_plan_id: str,
        billing_period: str = "monthly",
    ) -> dict[str, Any]:
        """Return proration preview amounts before committing a plan change."""
        customer = self._get_customer(user)
        sub: Subscription = customer.subscription
        new_price_id = self._resolve_price_id(new_plan_id, billing_period)
        return self._adapter.preview_proration(
            subscription_id=sub.stripe_subscription_id,
            new_price_id=new_price_id,
        )

    # ------------------------------------------------------------------
    # One-time payments
    # ------------------------------------------------------------------

    def create_one_time_payment(
        self,
        user: Any,
        price_id: str,
        success_url: str,
        cancel_url: str,
    ) -> dict[str, Any]:
        """Create a one-time payment checkout session (mode='payment')."""
        customer = self._get_customer(user)
        return self._adapter.create_checkout_session(
            customer_id=customer.stripe_customer_id,
            price_id=price_id,
            mode="payment",
            success_url=success_url,
            cancel_url=cancel_url,
        )

    # ------------------------------------------------------------------
    # Metered usage
    # ------------------------------------------------------------------

    def record_usage(
        self,
        user: Any,
        meter_event_name: str,
        value: int,
        identifier: str | None = None,
    ) -> dict[str, Any]:
        """Record a metered usage event for the user's customer ID."""
        customer = self._get_customer(user)
        return self._adapter.record_usage(
            meter_event_name=meter_event_name,
            customer_id=customer.stripe_customer_id,
            value=value,
            identifier=identifier,
        )

    def get_usage_summary(
        self,
        user: Any,
        subscription_item_id: str,
    ) -> dict[str, Any]:
        """Return aggregated usage for the current billing period."""
        return self._adapter.get_usage_summary(
            subscription_item_id=subscription_item_id,
        )

    # ------------------------------------------------------------------
    # Customer portal & invoices
    # ------------------------------------------------------------------

    def create_portal_session(
        self,
        user: Any,
        return_url: str,
    ) -> dict[str, Any]:
        """Create a self-service billing portal session."""
        customer = self._get_customer(user)
        return self._adapter.create_portal_session(
            customer_id=customer.stripe_customer_id,
            return_url=return_url,
        )

    def list_invoices(
        self,
        user: Any,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Return the most recent invoices for the user's customer."""
        customer = self._get_customer(user)
        return self._adapter.list_invoices(
            customer_id=customer.stripe_customer_id,
            limit=limit,
        )
