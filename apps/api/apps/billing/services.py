"""
BillingService — all billing operations.

Controllers call this exclusively; no ORM or adapter access in controllers.

Usage:
    service = BillingService()           # uses BILLING_ADAPTER from settings
    service = BillingService(adapter=stub)  # testable without Stripe
"""

import logging
from typing import Any

from apps.billing.models import Customer, Payment, PlanProviderMapping, Subscription
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
    # Read methods — used by controller GET endpoints
    # ------------------------------------------------------------------

    def get_status(self, user: Any) -> dict[str, Any]:
        """Return lightweight subscription status for the dashboard banner.

        Returns all-None sentinel when the user has no subscription rather
        than raising ServiceError — the dashboard must render for users on
        free tier who have no subscription record yet.
        """
        customer = self._get_customer(user)
        try:
            sub = Subscription.objects.get(customer=customer)
            return {
                "status": sub.status,
                "cancel_at_period_end": sub.cancel_at_period_end,
                "current_period_end": sub.current_period_end,
            }
        except Subscription.DoesNotExist:
            return {
                "status": None,
                "cancel_at_period_end": False,
                "current_period_end": None,
            }

    def get_subscription_detail(self, user: Any) -> dict[str, Any]:
        """Return full subscription detail with plan_id resolved from PlanProviderMapping.

        plan_id resolution is non-fatal: if the adapter call or mapping lookup
        fails, plan_id and billing_period are returned as None.
        """
        customer = self._get_customer(user)
        try:
            sub = Subscription.objects.select_related("customer").get(customer=customer)
        except Subscription.DoesNotExist as exc:
            raise ServiceError(
                code="no_subscription",
                message="No active subscription found.",
                status_code=404,
            ) from exc

        plan_id: str | None = None
        billing_period: str | None = None
        try:
            provider_name = self._get_provider_name()
            stripe_sub = self._adapter.retrieve_subscription(sub.stripe_subscription_id)
            current_price_id = stripe_sub.get("current_price_id") or stripe_sub.get("price_id")
            if current_price_id:
                mapping = PlanProviderMapping.objects.filter(
                    provider=provider_name,
                    price_id=current_price_id,
                ).first()
                if mapping:
                    plan_id = mapping.plan_id
                    billing_period = mapping.billing_period
        except Exception:
            pass  # plan_id resolution failure is non-fatal — return None

        return {
            "status": sub.status,
            "cancel_at_period_end": sub.cancel_at_period_end,
            "current_period_start": sub.current_period_start,
            "current_period_end": sub.current_period_end,
            "plan_id": plan_id,
            "billing_period": billing_period,
            "stripe_subscription_id": sub.stripe_subscription_id,
        }

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
    ) -> dict[str, Any]:
        """Undo a pending cancellation by setting cancel_at_period_end=False.

        No plan change occurs — the subscription continues on its current price.
        This is the inverse of cancel_subscription(cancel_at_period_end=True).
        """
        customer = self._get_customer(user)
        sub: Subscription = customer.subscription
        result = self._adapter.reactivate_subscription(
            subscription_id=sub.stripe_subscription_id,
        )
        sub.cancel_at_period_end = False
        sub.save(update_fields=["cancel_at_period_end", "updated_at"])
        return result

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
        return_url: str = "",
    ) -> dict[str, Any]:
        """Create a self-service billing portal session.

        return_url defaults to empty string — the adapter/Stripe accepts this and
        uses the portal's configured default return URL. Controllers may pass an
        explicit URL when the frontend provides one.
        """
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

    def get_payment_for_pdf(self, user: Any, payment_id: int) -> dict[str, Any]:
        """Build invoice_data dict for PDF rendering from a user-owned Payment record.

        Raises ServiceError(404) if the payment does not exist or belongs to another customer.
        """
        customer = self._get_customer(user)
        try:
            payment = customer.payments.get(pk=payment_id)
        except Payment.DoesNotExist as exc:
            raise ServiceError(
                code="not_found",
                message="Payment not found.",
                status_code=404,
            ) from exc
        return {
            "reference": f"PAY-{payment.pk}",
            "date": payment.created_at.strftime("%Y-%m-%d"),
            "customer_email": user.email,
            "description": "Subscription Payment",
            "amount": float(payment.amount),
            "currency": payment.currency,
        }
