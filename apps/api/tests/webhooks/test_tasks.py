"""Tests for Celery tasks: deliver_webhook, circuit breaker, cleanup.

HOOK-01: HMAC header, retry behaviour, 7-retry exhaustion.
HOOK-04: circuit breaker auto-disables endpoint + sends email; resets on success.
"""

from __future__ import annotations

import hashlib
import hmac
from unittest.mock import MagicMock, patch

import pytest
from django.utils import timezone

from apps.webhooks.models import DeliveryStatus, WebhookDelivery, WebhookDeliveryAttempt

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _verify_hmac(signing_key: str, payload_bytes: bytes, timestamp: str, signature: str) -> bool:
    """Re-compute HMAC-SHA256 and compare against signature header value."""
    msg = f"{timestamp}.".encode() + payload_bytes
    expected = hmac.new(signing_key.encode(), msg, hashlib.sha256).hexdigest()
    expected_header = f"sha256={expected}"
    return hmac.compare_digest(expected_header, signature)


def _make_mock_response(status_code: int, text: str = "") -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text
    resp.headers = {}
    return resp


# ---------------------------------------------------------------------------
# HOOK-01: Successful 2xx delivery
# ---------------------------------------------------------------------------


@pytest.mark.req("HOOK-01")
@pytest.mark.django_db(transaction=True)
def test_deliver_webhook_success_2xx(delivery):
    """deliver_webhook marks delivery as success when endpoint returns HTTP 2xx."""
    from apps.webhooks.tasks import deliver_webhook

    mock_response = _make_mock_response(200, "ok")

    with patch("httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_client
        mock_client.post.return_value = mock_response

        deliver_webhook(str(delivery.id))

    delivery.refresh_from_db()
    assert delivery.status == DeliveryStatus.SUCCESS


@pytest.mark.req("HOOK-01")
@pytest.mark.django_db(transaction=True)
def test_deliver_webhook_records_attempt(delivery):
    """deliver_webhook creates a WebhookDeliveryAttempt record for each HTTP call."""
    from apps.webhooks.tasks import deliver_webhook

    mock_response = _make_mock_response(200, "ok")

    with patch("httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_client
        mock_client.post.return_value = mock_response

        deliver_webhook(str(delivery.id))

    assert WebhookDeliveryAttempt.objects.filter(delivery=delivery).count() == 1
    attempt = WebhookDeliveryAttempt.objects.get(delivery=delivery)
    assert attempt.http_status_code == 200
    assert attempt.attempt_number == 1


@pytest.mark.req("HOOK-02")
@pytest.mark.django_db(transaction=True)
def test_deliver_webhook_headers_present(delivery):
    """deliver_webhook sends X-Webhook-Id and X-Webhook-Timestamp headers."""
    from apps.webhooks.tasks import deliver_webhook

    mock_response = _make_mock_response(200)
    captured_headers: dict = {}

    def capture_post(url, content, headers):
        captured_headers.update(headers)
        return mock_response

    with patch("httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_client
        mock_client.post.side_effect = capture_post

        deliver_webhook(str(delivery.id))

    assert "X-Webhook-Id" in captured_headers
    assert "X-Webhook-Timestamp" in captured_headers
    assert captured_headers["X-Webhook-Id"] == str(delivery.id)


@pytest.mark.req("HOOK-02")
@pytest.mark.django_db(transaction=True)
def test_hmac_signature_header_present(delivery):
    """deliver_webhook sends X-Webhook-Signature header with sha256= prefix."""
    from apps.webhooks.tasks import deliver_webhook

    mock_response = _make_mock_response(200)
    captured_headers: dict = {}

    def capture_post(url, content, headers):
        captured_headers.update(headers)
        return mock_response

    with patch("httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_client
        mock_client.post.side_effect = capture_post

        deliver_webhook(str(delivery.id))

    assert "X-Webhook-Signature" in captured_headers
    assert captured_headers["X-Webhook-Signature"].startswith("sha256=")


@pytest.mark.req("HOOK-02")
@pytest.mark.django_db(transaction=True)
def test_hmac_signature_verifiable(delivery):
    """A recipient using endpoint.signing_key can verify the HMAC signature."""
    from apps.webhooks.tasks import deliver_webhook

    mock_response = _make_mock_response(200)
    captured_headers: dict = {}
    captured_body: list[bytes] = []

    def capture_post(url, content, headers):
        captured_headers.update(headers)
        captured_body.append(content)
        return mock_response

    with patch("httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_client
        mock_client.post.side_effect = capture_post

        deliver_webhook(str(delivery.id))

    assert _verify_hmac(
        delivery.endpoint.signing_key,
        captured_body[0],
        captured_headers["X-Webhook-Timestamp"],
        captured_headers["X-Webhook-Signature"],
    ), "HMAC signature could not be verified using endpoint.signing_key"


# ---------------------------------------------------------------------------
# HOOK-01: Retry on failure
# ---------------------------------------------------------------------------


@pytest.mark.req("HOOK-01")
@pytest.mark.django_db(transaction=True)
def test_deliver_webhook_retries_on_failure(delivery):
    """Non-2xx response sets delivery status to 'retrying'."""
    from apps.webhooks.tasks import deliver_webhook

    mock_response = _make_mock_response(500, "error")

    with patch("httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_client
        mock_client.post.return_value = mock_response
        # Prevent actual celery retry — catch the exception raised by non-2xx
        with pytest.raises(Exception, match="Non-2xx"):
            deliver_webhook(str(delivery.id))

    delivery.refresh_from_db()
    assert delivery.status == DeliveryStatus.RETRYING


# ---------------------------------------------------------------------------
# HOOK-04: Circuit breaker
# ---------------------------------------------------------------------------


@pytest.mark.req("HOOK-04")
@pytest.mark.django_db(transaction=True)
def test_circuit_breaker_disables_after_5_failures(endpoint):
    """Endpoint is auto-disabled after 5 consecutive fully-exhausted delivery failures."""
    from apps.webhooks.models import WebhookDelivery
    from apps.webhooks.tasks import _handle_terminal_failure

    # Simulate 5 terminal failures by calling _handle_terminal_failure directly
    for _i in range(5):
        delivery = WebhookDelivery.objects.create(
            endpoint=endpoint,
            event_type="user.created",
            status=DeliveryStatus.PENDING,
            request_body={"webhook_version": "v1", "event_type": "user.created", "data": {}},
        )
        with patch("apps.notifications.utils.send_email"):
            _handle_terminal_failure(delivery, endpoint, "HTTP 500")
        endpoint.refresh_from_db()

    assert not endpoint.is_active
    assert endpoint.consecutive_failures >= 5


@pytest.mark.req("HOOK-04")
@pytest.mark.django_db(transaction=True)
def test_circuit_breaker_sends_email(endpoint, org_admin):
    """Auto-disabling an endpoint sends an email notification to the org admin."""
    from apps.webhooks.models import WebhookDelivery
    from apps.webhooks.tasks import _handle_terminal_failure

    # Pre-set consecutive_failures to threshold - 1 so next failure triggers circuit break
    endpoint.consecutive_failures = 4
    endpoint.save()

    delivery = WebhookDelivery.objects.create(
        endpoint=endpoint,
        event_type="user.created",
        status=DeliveryStatus.PENDING,
        request_body={"webhook_version": "v1", "event_type": "user.created", "data": {}},
    )

    with patch("apps.notifications.utils.send_email") as mock_send:
        _handle_terminal_failure(delivery, endpoint, "HTTP 500")

    assert mock_send.called
    call_kwargs = mock_send.call_args
    # Called with org admin email
    assert call_kwargs.kwargs["to"] == org_admin.email or (
        len(call_kwargs.args) > 0 and call_kwargs.args[0] == org_admin.email
    )
    # Uses correct template
    template_arg = call_kwargs.kwargs.get("template_name") or (
        call_kwargs.args[1] if len(call_kwargs.args) > 1 else None
    )
    assert template_arg == "webhooks/endpoint_disabled.html"


@pytest.mark.req("HOOK-04")
@pytest.mark.django_db(transaction=True)
def test_circuit_breaker_resets_on_success(endpoint):
    """A successful delivery resets consecutive_failures to 0 on the endpoint."""
    from apps.webhooks.tasks import deliver_webhook

    # Pre-set 3 failures on the endpoint
    endpoint.consecutive_failures = 3
    endpoint.save()

    from apps.webhooks.models import WebhookDelivery

    delivery = WebhookDelivery.objects.create(
        endpoint=endpoint,
        event_type="user.created",
        status=DeliveryStatus.PENDING,
        request_body={"webhook_version": "v1", "event_type": "user.created", "data": {}},
    )

    mock_response = _make_mock_response(200)
    with patch("httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_client
        mock_client.post.return_value = mock_response

        deliver_webhook(str(delivery.id))

    endpoint.refresh_from_db()
    assert endpoint.consecutive_failures == 0


# ---------------------------------------------------------------------------
# Cleanup task
# ---------------------------------------------------------------------------


@pytest.mark.req("HOOK-03")
@pytest.mark.django_db(transaction=True)
def test_cleanup_task_removes_old_deliveries(delivery):
    """Cleanup task deletes WebhookDelivery records older than retention window."""
    from apps.webhooks.tasks import webhook_delivery_cleanup

    # Age the delivery past the retention window
    WebhookDelivery.objects.filter(id=delivery.id).update(
        created_at=timezone.now() - timezone.timedelta(days=31)
    )

    result = webhook_delivery_cleanup()

    assert result["deleted"] >= 1
    assert not WebhookDelivery.objects.filter(id=delivery.id).exists()
