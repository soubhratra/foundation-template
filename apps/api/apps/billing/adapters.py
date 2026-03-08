"""
Payment adapter interface and concrete implementations.

PaymentAdapter defines a domain-centric interface — no provider-specific types
leak into the abstract layer. StripeAdapter implements the full protocol using
the Stripe Python SDK v14 StripeClient pattern.

To swap providers: change BILLING_ADAPTER in Django settings to point to a
different concrete class. No other code changes required.
"""

import abc
from typing import Any

from django.conf import settings


class PaymentAdapter(abc.ABC):
    """Abstract base class for payment provider adapters.

    All method signatures use domain-centric types (str, dict, list[dict]).
    No provider-specific types appear in this interface.

    Implementing a new provider:
      1. Subclass PaymentAdapter
      2. Implement all abstract methods
      3. Set BILLING_ADAPTER = "your.module.YourAdapter" in Django settings
    """

    @abc.abstractmethod
    def create_customer(self, user_id: str, email: str) -> dict[str, Any]:
        """Create a customer record with the payment provider.

        Returns a dict with at minimum: {"provider_customer_id": str}
        """

    @abc.abstractmethod
    def create_checkout_session(
        self,
        customer_id: str,
        price_id: str,
        mode: str,
        success_url: str,
        cancel_url: str,
        trial_days: int = 0,
    ) -> dict[str, Any]:
        """Create a hosted checkout session for subscription or one-time payment.

        Args:
            customer_id: Provider customer ID (e.g. from create_customer)
            price_id: Provider price ID to charge
            mode: "subscription" or "payment"
            success_url: Redirect URL after successful checkout
            cancel_url: Redirect URL if user cancels
            trial_days: Number of trial days (0 = no trial)

        Returns a dict with at minimum: {"checkout_url": str, "session_id": str}
        """

    @abc.abstractmethod
    def create_portal_session(
        self,
        customer_id: str,
        return_url: str,
    ) -> dict[str, Any]:
        """Create a customer self-service portal session.

        Returns a dict with at minimum: {"portal_url": str}
        """

    @abc.abstractmethod
    def cancel_subscription(
        self,
        subscription_id: str,
        cancel_at_period_end: bool = True,
    ) -> dict[str, Any]:
        """Cancel a subscription immediately or at period end.

        Returns a dict with updated subscription state.
        """

    @abc.abstractmethod
    def modify_subscription(
        self,
        subscription_id: str,
        new_price_id: str,
        proration_behavior: str = "create_prorations",
    ) -> dict[str, Any]:
        """Upgrade or downgrade a subscription to a new price.

        Returns a dict with updated subscription state.
        """

    @abc.abstractmethod
    def construct_webhook_event(
        self,
        payload: bytes,
        signature_header: str,
        webhook_secret: str,
    ) -> dict[str, Any]:
        """Verify webhook signature and construct the event from raw payload.

        Raises ValueError if signature verification fails.
        Returns a dict representing the provider event.
        """

    @abc.abstractmethod
    def record_usage(
        self,
        meter_event_name: str,
        customer_id: str,
        value: int,
        identifier: str | None = None,
    ) -> dict[str, Any]:
        """Record a metered usage event.

        Args:
            meter_event_name: Name of the meter (e.g. "api_calls")
            customer_id: Provider customer ID
            value: Usage quantity to record
            identifier: Idempotency key to prevent duplicate events

        Returns a dict confirming the recorded event.
        """

    @abc.abstractmethod
    def list_invoices(
        self,
        customer_id: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """List invoices for a customer.

        Returns a list of invoice dicts, each with at minimum:
        {"invoice_id": str, "amount": int, "currency": str, "status": str, "created": int}
        """

    @abc.abstractmethod
    def preview_proration(
        self,
        subscription_id: str,
        new_price_id: str,
        proration_date: int | None = None,
    ) -> dict[str, Any]:
        """Preview proration amounts for a subscription change.

        Args:
            subscription_id: Provider subscription ID
            new_price_id: Target price ID to switch to
            proration_date: Unix timestamp to use for proration calculation (default: now)

        Returns: {
            "amount_due_now": int,       # cents owed immediately
            "next_invoice_total": int,   # cents on next renewal
            "proration_date": int,       # unix timestamp used for calculation
            "currency": str,
        }
        """

    @abc.abstractmethod
    def get_usage_summary(
        self,
        subscription_item_id: str,
    ) -> dict[str, Any]:
        """Retrieve aggregated usage for the current billing period.

        Args:
            subscription_item_id: Provider subscription item ID (e.g. "si_xxx")

        Returns: {
            "total_usage": int,
            "period_start": int,   # unix timestamp
            "period_end": int,     # unix timestamp
        }
        """

    @abc.abstractmethod
    def retrieve_subscription(
        self,
        subscription_id: str,
    ) -> dict[str, Any]:
        """Retrieve a subscription from the payment provider.

        Args:
            subscription_id: Provider subscription ID (e.g. "sub_xxx")

        Returns a dict with at minimum: {"current_price_id": str}
        """

    @abc.abstractmethod
    def reactivate_subscription(
        self,
        subscription_id: str,
    ) -> dict[str, Any]:
        """Undo a pending cancellation by setting cancel_at_period_end=False.

        Call this when a user had previously requested cancellation at period
        end and now wants to keep their subscription. No plan change occurs.

        Returns a dict with updated subscription state.
        """


class StripeAdapter(PaymentAdapter):
    """Stripe implementation of PaymentAdapter using Stripe Python SDK v14.

    Uses StripeClient(api_key=...) per SDK v14 conventions.
    The api_key is never set globally — each instance owns its own client.
    """

    def __init__(self) -> None:
        import stripe as stripe_sdk

        self._client = stripe_sdk.StripeClient(
            api_key=settings.STRIPE_SECRET_KEY,
        )

    def create_customer(self, user_id: str, email: str) -> dict[str, Any]:
        customer = self._client.customers.create(
            params={
                "email": email,
                "metadata": {"user_id": user_id},
            }
        )
        return {"provider_customer_id": customer.id}

    def create_checkout_session(
        self,
        customer_id: str,
        price_id: str,
        mode: str,
        success_url: str,
        cancel_url: str,
        trial_days: int = 0,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "customer": customer_id,
            "mode": mode,
            "line_items": [{"price": price_id, "quantity": 1}],
            "success_url": success_url,
            "cancel_url": cancel_url,
        }
        if trial_days > 0 and mode == "subscription":
            params["subscription_data"] = {"trial_period_days": trial_days}
        session = self._client.checkout.sessions.create(params=params)
        return {"checkout_url": session.url, "session_id": session.id}

    def create_portal_session(
        self,
        customer_id: str,
        return_url: str,
    ) -> dict[str, Any]:
        session = self._client.billing_portal.sessions.create(
            params={"customer": customer_id, "return_url": return_url}
        )
        return {"portal_url": session.url}

    def cancel_subscription(
        self,
        subscription_id: str,
        cancel_at_period_end: bool = True,
    ) -> dict[str, Any]:
        if cancel_at_period_end:
            subscription = self._client.subscriptions.update(
                subscription_id,
                params={"cancel_at_period_end": True},
            )
        else:
            subscription = self._client.subscriptions.cancel(subscription_id)
        return {
            "subscription_id": subscription.id,
            "status": subscription.status,
            "cancel_at_period_end": subscription.cancel_at_period_end,
        }

    def modify_subscription(
        self,
        subscription_id: str,
        new_price_id: str,
        proration_behavior: str = "create_prorations",
    ) -> dict[str, Any]:
        subscription = self._client.subscriptions.retrieve(subscription_id)
        item_id = subscription.items.data[0].id
        updated = self._client.subscriptions.update(
            subscription_id,
            params={
                "items": [{"id": item_id, "price": new_price_id}],
                "proration_behavior": proration_behavior,
            },
        )
        return {
            "subscription_id": updated.id,
            "status": updated.status,
        }

    def construct_webhook_event(
        self,
        payload: bytes,
        signature_header: str,
        webhook_secret: str,
    ) -> dict[str, Any]:
        import stripe as stripe_sdk

        try:
            event = self._client.construct_event(
                payload=payload,
                sig_header=signature_header,
                secret=webhook_secret,
            )
        except stripe_sdk.SignatureVerificationError as exc:
            raise ValueError(f"Webhook signature verification failed: {exc}") from exc
        return dict(event)

    def record_usage(
        self,
        meter_event_name: str,
        customer_id: str,
        value: int,
        identifier: str | None = None,
    ) -> dict[str, Any]:
        """Record usage via Stripe Meter Events v2 API."""
        params: dict[str, Any] = {
            "event_name": meter_event_name,
            "payload": {
                "stripe_customer_id": customer_id,
                "value": str(value),
            },
        }
        if identifier:
            params["identifier"] = identifier
        event = self._client.v2.billing.meter_events.create(params=params)
        return {"identifier": getattr(event, "identifier", None)}

    def list_invoices(
        self,
        customer_id: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        response = self._client.invoices.list(params={"customer": customer_id, "limit": limit})
        return [
            {
                "invoice_id": inv.id,
                "amount": inv.amount_paid,
                "currency": inv.currency,
                "status": inv.status,
                "created": inv.created,
                "hosted_invoice_url": inv.hosted_invoice_url,
                "invoice_pdf": inv.invoice_pdf,
            }
            for inv in response.data
        ]

    def preview_proration(
        self,
        subscription_id: str,
        new_price_id: str,
        proration_date: int | None = None,
    ) -> dict[str, Any]:
        """Preview proration amounts by creating an invoice preview via Stripe."""
        import time

        effective_proration_date = proration_date or int(time.time())

        # Retrieve the current subscription to find the item ID.
        subscription = self._client.subscriptions.retrieve(subscription_id)
        item_id = subscription.items.data[0].id

        preview = self._client.invoices.create_preview(
            params={
                "customer": subscription.customer,
                "subscription": subscription_id,
                "subscription_details": {
                    "items": [{"id": item_id, "price": new_price_id}],
                    "proration_behavior": "create_prorations",
                },
                "subscription_proration_date": effective_proration_date,
            }
        )

        # Sum proration line items for "amount_due_now".
        proration_lines = [line for line in preview.lines.data if getattr(line, "proration", False)]
        amount_due_now = sum(line.amount for line in proration_lines)

        return {
            "amount_due_now": amount_due_now,
            "next_invoice_total": preview.total,
            "proration_date": effective_proration_date,
            "currency": preview.currency,
        }

    def retrieve_subscription(
        self,
        subscription_id: str,
    ) -> dict[str, Any]:
        """Retrieve a Stripe subscription and return the current price ID."""
        subscription = self._client.subscriptions.retrieve(subscription_id)
        try:
            current_price_id = subscription.items.data[0].price.id
        except (IndexError, AttributeError):
            current_price_id = None
        return {"current_price_id": current_price_id}

    def reactivate_subscription(
        self,
        subscription_id: str,
    ) -> dict[str, Any]:
        """Undo pending cancellation by setting cancel_at_period_end=False."""
        subscription = self._client.subscriptions.update(
            subscription_id,
            params={"cancel_at_period_end": False},
        )
        return {
            "subscription_id": subscription.id,
            "status": subscription.status,
            "cancel_at_period_end": subscription.cancel_at_period_end,
        }

    def get_usage_summary(
        self,
        subscription_item_id: str,
    ) -> dict[str, Any]:
        """Retrieve aggregated usage for a metered subscription item."""
        response = self._client.subscription_items.list_usage_record_summaries(
            subscription_item_id,
            params={"limit": 1},
        )
        if not response.data:
            return {"total_usage": 0, "period_start": 0, "period_end": 0}

        summary = response.data[0]
        return {
            "total_usage": summary.total_usage,
            "period_start": summary.period.start,
            "period_end": summary.period.end,
        }
