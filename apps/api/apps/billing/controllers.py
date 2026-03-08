"""
Billing API controller.

All endpoints delegate to BillingService — no ORM access here.
Registered automatically via api.auto_discover_controllers() in config/urls.py.
"""

from allauth.headless.contrib.ninja.security import jwt_token_auth
from ninja.security import SessionAuth
from ninja_extra import ControllerBase, api_controller, route
from ninja_extra.permissions import IsAuthenticated

from apps.billing.services import BillingService

from .schemas import (
    BillingStatusOut,
    InvoiceListOut,
    PlanChangeIn,
    PortalSessionOut,
    ProrationPreviewIn,
    ProrationPreviewOut,
    SubscriptionDetailOut,
)


@api_controller(
    "/billing",
    tags=["Billing"],
    permissions=[IsAuthenticated],
    auth=[SessionAuth(), jwt_token_auth],
)
class BillingController(ControllerBase):
    def __init__(self):
        self.service = BillingService()

    @route.get("/status", response=BillingStatusOut, url_name="billing-status")
    def get_status(self, request):
        """Lightweight status check — used by dashboard past-due banner."""
        raise NotImplementedError("implement in plan 02")

    @route.get("/subscription", response=SubscriptionDetailOut, url_name="billing-subscription")
    def get_subscription(self, request):
        """Full subscription detail for the /billing page."""
        raise NotImplementedError("implement in plan 02")

    @route.get("/invoices", response=InvoiceListOut, url_name="billing-invoices")
    def list_invoices(self, request, limit: int = 10):
        """Paginated payment history (newest-first, default limit=10)."""
        raise NotImplementedError("implement in plan 02")

    @route.post(
        "/subscription/change",
        response=SubscriptionDetailOut,
        url_name="billing-change",
    )
    def change_plan(self, request, payload: PlanChangeIn):
        """Upgrade or downgrade subscription to a different plan."""
        raise NotImplementedError("implement in plan 02")

    @route.post(
        "/subscription/cancel",
        response=BillingStatusOut,
        url_name="billing-cancel",
    )
    def cancel_subscription(self, request):
        """Cancel subscription at period end (sets cancel_at_period_end=True)."""
        raise NotImplementedError("implement in plan 02")

    @route.post(
        "/subscription/reactivate",
        response=BillingStatusOut,
        url_name="billing-reactivate",
    )
    def reactivate_subscription(self, request):
        """Reactivate a pending-cancellation subscription."""
        raise NotImplementedError("implement in plan 02")

    @route.post(
        "/portal-session",
        response=PortalSessionOut,
        url_name="billing-portal",
    )
    def create_portal_session(self, request):
        """Create a Stripe Customer Portal session and return the redirect URL."""
        raise NotImplementedError("implement in plan 02")

    @route.post(
        "/proration-preview",
        response=ProrationPreviewOut,
        url_name="billing-proration-preview",
    )
    def preview_proration(self, request, payload: ProrationPreviewIn):
        """Preview charge amounts before committing a plan change."""
        raise NotImplementedError("implement in plan 02")
