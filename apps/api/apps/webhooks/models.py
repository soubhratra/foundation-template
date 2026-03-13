"""Webhook models: WebhookEndpoint, WebhookDelivery, WebhookDeliveryAttempt."""

from __future__ import annotations

import hashlib
import secrets
import uuid

from django.core.exceptions import ValidationError
from django.db import models


class WebhookEndpoint(models.Model):
    """A registered endpoint that receives webhook events for an org."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    org = models.ForeignKey(
        "orgs.Organization",
        on_delete=models.CASCADE,
        related_name="webhook_endpoints",
    )
    url = models.URLField(max_length=2048)
    name = models.CharField(max_length=255, blank=True, default="")
    event_types = models.JSONField(default=list)
    # Raw secret — HMAC key for delivery signing. Returned to org admin once at creation.
    signing_key = models.CharField(max_length=64, blank=True, default="")
    # SHA-256 hex of signing_key — stored for secure lookup without exposing raw key in logs.
    secret_hash = models.CharField(max_length=64, blank=True, default="")
    is_active = models.BooleanField(default=True)
    consecutive_failures = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "webhooks_endpoint"
        indexes = [
            models.Index(fields=["org", "is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.name or self.url} ({self.org_id})"

    def clean(self) -> None:
        if self.url and not self.url.startswith("https://"):
            raise ValidationError({"url": "Webhook endpoint URL must use HTTPS."})

    @staticmethod
    def generate_secret() -> tuple[str, str, str]:
        """Return (raw_secret, signing_key, secret_hash).

        signing_key == raw_secret (the value used as HMAC key and returned to org admin once).
        secret_hash == SHA-256 hex of raw_secret (stored for secure lookup).
        Store both fields; return signing_key as EndpointCreateOut.secret.
        """
        raw = secrets.token_hex(32)
        hashed = hashlib.sha256(raw.encode()).hexdigest()
        return raw, raw, hashed


class DeliveryStatus(models.TextChoices):
    PENDING = "pending"
    RETRYING = "retrying"
    SUCCESS = "success"
    FAILED = "failed"


class WebhookDelivery(models.Model):
    """A single delivery event — one per endpoint per fire_webhook_event() call."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    endpoint = models.ForeignKey(
        WebhookEndpoint,
        on_delete=models.CASCADE,
        related_name="deliveries",
    )
    event_type = models.CharField(max_length=255)
    status = models.CharField(
        max_length=20,
        choices=DeliveryStatus.choices,
        default=DeliveryStatus.PENDING,
    )
    request_body = models.JSONField()  # Full payload snapshot (includes webhook_version)
    request_headers = models.JSONField(default=dict)  # Headers snapshot
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "webhooks_delivery"
        indexes = [
            models.Index(fields=["endpoint", "-created_at"]),  # For paginated delivery history
        ]


class WebhookDeliveryAttempt(models.Model):
    """One HTTP attempt for a delivery (retries create additional attempts)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    delivery = models.ForeignKey(
        WebhookDelivery,
        on_delete=models.CASCADE,
        related_name="attempts",
    )
    attempt_number = models.IntegerField()
    http_status_code = models.IntegerField(null=True, blank=True)  # null for network errors
    # Truncated at 10 KB in the task layer before saving.
    response_body = models.TextField(blank=True, default="")
    response_headers = models.JSONField(default=dict)
    duration_ms = models.IntegerField(null=True, blank=True)
    attempted_at = models.DateTimeField(auto_now_add=True)
    error_message = models.TextField(blank=True, default="")  # Network/timeout errors

    _RESPONSE_BODY_MAX_CHARS = 10_240

    def save(self, *args, **kwargs) -> None:  # type: ignore[override]
        # Truncate response_body at 10 KB to avoid storing large payloads in DB.
        if self.response_body and len(self.response_body) > self._RESPONSE_BODY_MAX_CHARS:
            self.response_body = self.response_body[: self._RESPONSE_BODY_MAX_CHARS]
        super().save(*args, **kwargs)

    class Meta:
        db_table = "webhooks_delivery_attempt"
        ordering = ["attempt_number"]
