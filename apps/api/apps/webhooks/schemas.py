"""Request/response schema classes for all webhook endpoints.

Schema separation:
- EndpointCreateOut: returned ONLY on POST /endpoints — includes `secret` (signing_key shown once)
- EndpointOut: returned for list, get, update — does NOT include `secret`
- RotateSecretOut: returned ONLY on POST /rotate-secret — includes new `secret`
- DeliveryOut: paginated list with attempt_count (annotated, not stored)
- DeliveryDetailOut: full delivery detail including all attempts
"""

from datetime import datetime

from ninja import Schema
from pydantic import field_validator

# ---------------------------------------------------------------------------
# Endpoint schemas
# ---------------------------------------------------------------------------


class EndpointIn(Schema):
    """Request body for creating a new webhook endpoint."""

    url: str
    name: str = ""
    event_types: list[str]

    @field_validator("url")
    @classmethod
    def url_must_be_https(cls, v: str) -> str:
        if not v.startswith("https://"):
            raise ValueError("Webhook endpoint URL must use HTTPS (http:// not allowed).")
        return v

    @field_validator("event_types")
    @classmethod
    def event_types_must_not_be_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("event_types must contain at least one event type.")
        return v


class EndpointOut(Schema):
    """Returned for list, get, update, delete — no secret field."""

    id: str
    url: str
    name: str
    event_types: list[str]
    is_active: bool
    consecutive_failures: int
    created_at: datetime

    @staticmethod
    def from_orm_endpoint(ep: object) -> "EndpointOut":
        return EndpointOut(
            id=str(ep.id),  # type: ignore[attr-defined]
            url=ep.url,  # type: ignore[attr-defined]
            name=ep.name,  # type: ignore[attr-defined]
            event_types=ep.event_types,  # type: ignore[attr-defined]
            is_active=ep.is_active,  # type: ignore[attr-defined]
            consecutive_failures=ep.consecutive_failures,  # type: ignore[attr-defined]
            created_at=ep.created_at,  # type: ignore[attr-defined]
        )


class EndpointCreateOut(Schema):
    """Returned ONLY from POST /endpoints — includes secret shown once.

    secret == endpoint.signing_key (the raw HMAC key used for delivery signing).
    Recipients store this value and use it to verify HMAC-SHA256 signatures
    on each incoming webhook. It is not returned by any subsequent read endpoint.
    """

    id: str
    url: str
    name: str
    event_types: list[str]
    is_active: bool
    created_at: datetime
    secret: str  # Raw signing_key — used by recipients for HMAC verification


class EndpointUpdateIn(Schema):
    """Request body for PATCH /endpoints/{id}."""

    url: str | None = None
    name: str | None = None
    event_types: list[str] | None = None
    is_active: bool | None = None

    @field_validator("url")
    @classmethod
    def url_must_be_https(cls, v: str | None) -> str | None:
        if v is not None and not v.startswith("https://"):
            raise ValueError("Webhook endpoint URL must use HTTPS.")
        return v


class RotateSecretOut(Schema):
    """Returned from POST /endpoints/{id}/rotate-secret — new secret shown once.

    secret == new endpoint.signing_key. Not returned again after this response.
    """

    id: str
    secret: str  # New raw signing_key — not returned again


# ---------------------------------------------------------------------------
# Delivery schemas
# ---------------------------------------------------------------------------


class AttemptOut(Schema):
    """A single HTTP attempt for a delivery."""

    attempt_number: int
    http_status_code: int | None
    response_body: str
    duration_ms: int | None
    attempted_at: datetime
    error_message: str


class DeliveryOut(Schema):
    """Delivery summary for paginated list — includes attempt_count (computed via annotation)."""

    id: str
    event_type: str
    status: str
    created_at: datetime
    attempt_count: int  # Annotated on queryset: Count("attempts")

    @staticmethod
    def from_orm_delivery(d: object) -> "DeliveryOut":
        return DeliveryOut(
            id=str(d.id),  # type: ignore[attr-defined]
            event_type=d.event_type,  # type: ignore[attr-defined]
            status=d.status,  # type: ignore[attr-defined]
            created_at=d.created_at,  # type: ignore[attr-defined]
            attempt_count=(
                d.attempt_count  # type: ignore[attr-defined]
                if hasattr(d, "attempt_count")
                else d.attempts.count()  # type: ignore[attr-defined]
            ),
        )


class DeliveryDetailOut(Schema):
    """Full delivery detail including all attempts."""

    id: str
    event_type: str
    status: str
    request_body: dict
    created_at: datetime
    attempts: list[AttemptOut]
