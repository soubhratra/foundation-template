"""
Ninja request/response schemas for billing API endpoints.

Field shapes are derived from adapter return types and the Subscription model.
"""

from datetime import datetime

from ninja import Schema


class BillingStatusOut(Schema):
    """Lightweight status response — used by dashboard banner and status endpoint."""

    status: str | None  # SubscriptionStatus value or None if no subscription
    cancel_at_period_end: bool
    current_period_end: datetime | None


class SubscriptionDetailOut(Schema):
    """Full subscription detail for the /billing page."""

    status: str
    cancel_at_period_end: bool
    current_period_start: datetime | None
    current_period_end: datetime | None
    plan_id: str | None  # resolved from PlanProviderMapping
    billing_period: str | None  # "monthly" or "annual"
    stripe_subscription_id: str


class InvoiceOut(Schema):
    """Single invoice record for the payment history table."""

    invoice_id: str
    amount: int  # in cents
    currency: str
    status: str
    created: int  # unix timestamp
    invoice_url: str | None  # Stripe-hosted invoice URL


class InvoiceListOut(Schema):
    """Paginated invoice list response."""

    invoices: list[InvoiceOut]
    total: int


class PlanChangeIn(Schema):
    """Request body for plan upgrade/downgrade."""

    plan_id: str
    billing_period: str  # "monthly" | "annual"


class ProrationPreviewIn(Schema):
    """Request body for proration preview before committing a plan change."""

    plan_id: str
    billing_period: str


class ProrationPreviewOut(Schema):
    """Preview of charges for an upcoming plan change."""

    amount_due_now: int  # in cents
    next_invoice_total: int  # in cents
    proration_date: int  # unix timestamp
    currency: str


class PortalSessionOut(Schema):
    """Response containing the Stripe Customer Portal redirect URL."""

    portal_url: str


class CheckoutSessionIn(Schema):
    """Request body for initiating a Stripe Checkout session (free-tier users)."""

    plan_id: str
    billing_period: str = "monthly"
    success_url: str
    cancel_url: str


class CheckoutSessionOut(Schema):
    """Response containing the Stripe Checkout session redirect URL."""

    checkout_url: str
    session_id: str


class PdfTaskOut(Schema):
    """Response for async PDF generation — contains task ID for polling."""

    task_id: str
    status: str  # always "pending" on initial response
