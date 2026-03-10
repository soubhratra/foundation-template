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
from apps.billing.tasks import generate_invoice_pdf

from .schemas import (
    BillingStatusOut,
    CheckoutSessionIn,
    CheckoutSessionOut,
    InvoiceListOut,
    InvoiceOut,
    PdfTaskOut,
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
        result = self.service.get_status(request.user)
        return BillingStatusOut(**result)

    @route.get("/subscription", response=SubscriptionDetailOut, url_name="billing-subscription")
    def get_subscription(self, request):
        """Full subscription detail for the /billing page."""
        detail = self.service.get_subscription_detail(request.user)
        return SubscriptionDetailOut(**detail)

    @route.get("/invoices", response=InvoiceListOut, url_name="billing-invoices")
    def list_invoices(self, request, limit: int = 10):
        """Paginated payment history (newest-first, default limit=10)."""
        raw_invoices = self.service.list_invoices(request.user, limit=limit)
        # Map provider field names to schema field names.
        # StripeAdapter returns hosted_invoice_url; schema field is invoice_url.
        invoices = [
            InvoiceOut(
                invoice_id=inv["invoice_id"],
                amount=inv["amount"],
                currency=inv["currency"],
                status=inv["status"],
                created=inv["created"],
                invoice_url=inv.get("hosted_invoice_url") or inv.get("invoice_url"),
            )
            for inv in raw_invoices
        ]
        return InvoiceListOut(invoices=invoices, total=len(invoices))

    @route.post(
        "/subscription/change",
        response=SubscriptionDetailOut,
        url_name="billing-change",
    )
    def change_plan(self, request, payload: PlanChangeIn):
        """Upgrade or downgrade subscription to a different plan."""
        # BillingService.upgrade_subscription handles both upgrade and downgrade paths
        # at the adapter level — the adapter sets proration_behavior accordingly.
        self.service.upgrade_subscription(request.user, payload.plan_id, payload.billing_period)
        detail = self.service.get_subscription_detail(request.user)
        return SubscriptionDetailOut(**detail)

    @route.post(
        "/subscription/cancel",
        response=BillingStatusOut,
        url_name="billing-cancel",
    )
    def cancel_subscription(self, request):
        """Cancel subscription at period end (sets cancel_at_period_end=True)."""
        self.service.cancel_subscription(request.user)
        result = self.service.get_status(request.user)
        return BillingStatusOut(**result)

    @route.post(
        "/subscription/reactivate",
        response=BillingStatusOut,
        url_name="billing-reactivate",
    )
    def reactivate_subscription(self, request):
        """Reactivate a pending-cancellation subscription."""
        self.service.reactivate_subscription(request.user)
        result = self.service.get_status(request.user)
        return BillingStatusOut(**result)

    @route.post(
        "/portal-session",
        response=PortalSessionOut,
        url_name="billing-portal",
    )
    def create_portal_session(self, request):
        """Create a Stripe Customer Portal session and return the redirect URL."""
        result = self.service.create_portal_session(request.user)
        return PortalSessionOut(portal_url=result["portal_url"])

    @route.post(
        "/subscription/subscribe",
        response=CheckoutSessionOut,
        url_name="billing-subscribe",
    )
    def subscribe_plan(self, request, payload: CheckoutSessionIn):
        """Create a Stripe Checkout session for a new subscription (free-tier users).

        Unlike /subscription/change which requires an active subscription, this
        endpoint calls create_checkout_session which only needs the Customer record.
        The Customer record is guaranteed to exist via the post_save auto-create signal.
        """
        result = self.service.create_checkout_session(
            user=request.user,
            plan_id=payload.plan_id,
            billing_period=payload.billing_period,
            success_url=payload.success_url,
            cancel_url=payload.cancel_url,
        )
        return CheckoutSessionOut(
            checkout_url=result["checkout_url"],
            session_id=result.get("session_id", ""),
        )

    @route.post(
        "/proration-preview",
        response=ProrationPreviewOut,
        url_name="billing-proration-preview",
    )
    def preview_proration(self, request, payload: ProrationPreviewIn):
        """Preview charge amounts before committing a plan change."""
        result = self.service.preview_proration(
            request.user, payload.plan_id, payload.billing_period
        )
        return ProrationPreviewOut(**result)

    @route.post(
        "/invoices/{payment_id}/pdf",
        response=PdfTaskOut,
        url_name="billing-invoice-pdf",
    )
    def request_invoice_pdf(self, request, payment_id: int):
        """Enqueue PDF generation. Returns task_id for polling. Never blocks."""
        invoice_data = self.service.get_payment_for_pdf(request.user, payment_id)
        task = generate_invoice_pdf.delay(invoice_data)
        return PdfTaskOut(task_id=task.id, status="pending")

    @route.get(
        "/invoices/pdf-status/{task_id}",
        url_name="billing-pdf-status",
    )
    def get_pdf_status(self, request, task_id: str):
        """Poll PDF generation status.

        When status=success, returns base64-encoded PDF bytes in pdf_base64 field.
        The response shape varies by state so no typed `response=` schema is used —
        Django Ninja serializes plain dicts as JSON.
        """
        import base64

        from celery.result import AsyncResult

        result = AsyncResult(task_id)
        if result.state == "SUCCESS":
            pdf_bytes = result.result
            return {"status": "success", "pdf_base64": base64.b64encode(pdf_bytes).decode()}
        if result.state == "FAILURE":
            return self.create_response(request, {"status": "failed"}, status_code=500)
        return {"status": result.state.lower()}
