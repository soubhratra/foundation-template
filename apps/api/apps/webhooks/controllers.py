"""Ninja Extra controllers for webhook endpoint CRUD and delivery management.

Two controllers auto-discovered via NinjaExtraAPI.auto_discover_controllers():
- WebhookEndpointController: CRUD for webhook endpoints + rotate-secret + delivery list
- WebhookDeliveryController: delivery detail + manual retry

Permission model:
- All endpoints require IsAuthenticated + IsOrgMember (member can read history)
- Write endpoints (POST/PATCH/DELETE/rotate-secret) require IsOrgAdmin
- IsOrgMember resolves org_slug → sets request.org; IsOrgAdmin reads request.org

Controllers are thin — models/tasks contain business logic.
"""

from typing import Any

from allauth.headless.contrib.ninja.security import jwt_token_auth
from django.db import models
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja.security import SessionAuth
from ninja_extra import ControllerBase, api_controller, route
from ninja_extra.permissions import IsAuthenticated

from apps.orgs.permissions import IsOrgAdmin, IsOrgMember
from apps.webhooks.models import (
    WebhookDelivery,
    WebhookEndpoint,
)
from apps.webhooks.schemas import (
    AttemptOut,
    DeliveryDetailOut,
    DeliveryOut,
    EndpointCreateOut,
    EndpointIn,
    EndpointOut,
    EndpointUpdateIn,
    RotateSecretOut,
)
from apps.webhooks.tasks import deliver_webhook


@api_controller(
    "/org/{org_slug}/webhooks/endpoints",
    tags=["webhooks"],
    auth=[SessionAuth(), jwt_token_auth],
    permissions=[IsAuthenticated, IsOrgMember],
)
class WebhookEndpointController(ControllerBase):
    """CRUD for webhook endpoints, secret rotation, and delivery history."""

    @route.post(
        "",
        response={201: EndpointCreateOut},
        permissions=[IsAuthenticated, IsOrgMember, IsOrgAdmin],
        url_name="webhook-endpoint-create",
    )
    def create_endpoint(self, request: HttpRequest, org_slug: str, body: EndpointIn) -> Any:
        """Register a new webhook endpoint.

        Returns the raw secret (signing_key) exactly once in EndpointCreateOut.
        Subsequent GET requests do not return the secret.
        """
        raw_secret, signing_key, secret_hash = WebhookEndpoint.generate_secret()
        endpoint = WebhookEndpoint.objects.create(
            org=request.org,  # type: ignore[attr-defined]
            url=body.url,
            name=body.name,
            event_types=body.event_types,
            signing_key=signing_key,
            secret_hash=secret_hash,
        )
        return 201, EndpointCreateOut(
            id=str(endpoint.id),
            url=endpoint.url,
            name=endpoint.name,
            event_types=endpoint.event_types,
            is_active=endpoint.is_active,
            created_at=endpoint.created_at,
            secret=signing_key,  # signing_key == raw_secret; never returned again
        )

    @route.get(
        "",
        response={200: list[EndpointOut]},
        url_name="webhook-endpoint-list",
    )
    def list_endpoints(self, request: HttpRequest, org_slug: str) -> Any:
        """List all webhook endpoints for the org (no secrets returned)."""
        endpoints = WebhookEndpoint.objects.filter(
            org=request.org  # type: ignore[attr-defined]
        ).order_by("-created_at")
        return 200, [EndpointOut.from_orm_endpoint(ep) for ep in endpoints]

    @route.patch(
        "/{endpoint_id}",
        response={200: EndpointOut},
        permissions=[IsAuthenticated, IsOrgMember, IsOrgAdmin],
        url_name="webhook-endpoint-update",
    )
    def update_endpoint(
        self, request: HttpRequest, org_slug: str, endpoint_id: str, body: EndpointUpdateIn
    ) -> Any:
        """Update endpoint fields.

        Re-enabling (is_active: true) resets consecutive_failures to 0,
        which clears the circuit-breaker counter.
        """
        endpoint = get_object_or_404(
            WebhookEndpoint,
            id=endpoint_id,
            org=request.org,  # type: ignore[attr-defined]
        )
        update_fields: list[str] = []
        if body.url is not None:
            endpoint.url = body.url
            update_fields.append("url")
        if body.name is not None:
            endpoint.name = body.name
            update_fields.append("name")
        if body.event_types is not None:
            endpoint.event_types = body.event_types
            update_fields.append("event_types")
        if body.is_active is not None:
            endpoint.is_active = body.is_active
            update_fields.append("is_active")
            if body.is_active:
                # Re-enabling resets circuit breaker counter (HOOK-04)
                endpoint.consecutive_failures = 0
                update_fields.append("consecutive_failures")
        if update_fields:
            endpoint.save(update_fields=update_fields)
        return 200, EndpointOut.from_orm_endpoint(endpoint)

    @route.delete(
        "/{endpoint_id}",
        response={204: None},
        permissions=[IsAuthenticated, IsOrgMember, IsOrgAdmin],
        url_name="webhook-endpoint-delete",
    )
    def delete_endpoint(self, request: HttpRequest, org_slug: str, endpoint_id: str) -> Any:
        """Delete a webhook endpoint. Associated deliveries are cascade-deleted."""
        endpoint = get_object_or_404(
            WebhookEndpoint,
            id=endpoint_id,
            org=request.org,  # type: ignore[attr-defined]
        )
        endpoint.delete()
        return 204, None

    @route.post(
        "/{endpoint_id}/rotate-secret",
        response={200: RotateSecretOut},
        permissions=[IsAuthenticated, IsOrgMember, IsOrgAdmin],
        url_name="webhook-endpoint-rotate-secret",
    )
    def rotate_secret(self, request: HttpRequest, org_slug: str, endpoint_id: str) -> Any:
        """Generate a new HMAC secret.

        Old secret is immediately invalidated — any in-flight deliveries using
        the old key will fail HMAC verification on the recipient side.
        New secret is returned exactly once in RotateSecretOut.
        """
        endpoint = get_object_or_404(
            WebhookEndpoint,
            id=endpoint_id,
            org=request.org,  # type: ignore[attr-defined]
        )
        _raw_secret, signing_key, secret_hash = WebhookEndpoint.generate_secret()
        endpoint.signing_key = signing_key
        endpoint.secret_hash = secret_hash
        endpoint.save(update_fields=["signing_key", "secret_hash", "updated_at"])
        return 200, RotateSecretOut(id=str(endpoint.id), secret=signing_key)

    @route.get(
        "/{endpoint_id}/deliveries",
        response={200: dict},
        url_name="webhook-endpoint-deliveries",
    )
    def list_deliveries(
        self,
        request: HttpRequest,
        org_slug: str,
        endpoint_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> Any:
        """Paginated delivery history for an endpoint.

        Each delivery includes attempt_count (annotated via COUNT("attempts")).
        Ordered by most recent first. Returns {"items": [...], "count": N}.
        """
        endpoint = get_object_or_404(
            WebhookEndpoint,
            id=endpoint_id,
            org=request.org,  # type: ignore[attr-defined]
        )
        qs = (
            WebhookDelivery.objects.filter(endpoint=endpoint)
            .annotate(attempt_count=models.Count("attempts"))
            .order_by("-created_at")
        )
        count = qs.count()
        offset = (page - 1) * page_size
        items = qs[offset : offset + page_size]
        return 200, {
            "items": [DeliveryOut.from_orm_delivery(d) for d in items],
            "count": count,
        }


@api_controller(
    "/org/{org_slug}/webhooks/deliveries",
    tags=["webhooks"],
    auth=[SessionAuth(), jwt_token_auth],
    permissions=[IsAuthenticated, IsOrgMember],
)
class WebhookDeliveryController(ControllerBase):
    """Delivery detail and manual retry."""

    @route.get(
        "/{delivery_id}",
        response={200: DeliveryDetailOut},
        url_name="webhook-delivery-detail",
    )
    def get_delivery(self, request: HttpRequest, org_slug: str, delivery_id: str) -> Any:
        """Return full delivery detail including all HTTP attempts."""
        delivery = get_object_or_404(
            WebhookDelivery,
            id=delivery_id,
            endpoint__org=request.org,  # type: ignore[attr-defined]
        )
        attempts = [
            AttemptOut(
                attempt_number=a.attempt_number,
                http_status_code=a.http_status_code,
                response_body=a.response_body,
                duration_ms=a.duration_ms,
                attempted_at=a.attempted_at,
                error_message=a.error_message,
            )
            for a in delivery.attempts.all()
        ]
        return 200, DeliveryDetailOut(
            id=str(delivery.id),
            event_type=delivery.event_type,
            status=delivery.status,
            request_body=delivery.request_body,
            created_at=delivery.created_at,
            attempts=attempts,
        )

    @route.post(
        "/{delivery_id}/retry",
        response={202: dict},
        url_name="webhook-delivery-retry",
    )
    def retry_delivery(self, request: HttpRequest, org_slug: str, delivery_id: str) -> Any:
        """Manually enqueue a retry for any delivery.

        Enqueues deliver_webhook.delay() and returns 202 immediately.
        The task handles idempotency — it checks endpoint.is_active before sending.
        """
        delivery = get_object_or_404(
            WebhookDelivery,
            id=delivery_id,
            endpoint__org=request.org,  # type: ignore[attr-defined]
        )
        deliver_webhook.delay(str(delivery.id))
        return 202, {"queued": True, "delivery_id": str(delivery.id)}
