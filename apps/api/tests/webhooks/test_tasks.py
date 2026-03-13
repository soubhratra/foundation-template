"""Tests for Celery tasks: deliver_webhook, circuit breaker, cleanup.

HOOK-01: HMAC header, retry behaviour, 7-retry exhaustion.
HOOK-04: circuit breaker auto-disables endpoint + sends email; resets on success.
"""

import pytest


@pytest.mark.django_db
def test_deliver_webhook_success_2xx(delivery):
    """deliver_webhook marks delivery as success when endpoint returns HTTP 2xx."""
    pytest.fail("RED — not yet implemented")


@pytest.mark.django_db
def test_deliver_webhook_retries_on_failure(delivery):
    """deliver_webhook retries up to 7 times when endpoint returns non-2xx."""
    pytest.fail("RED — not yet implemented")


@pytest.mark.django_db
def test_hmac_signature_header_present(delivery):
    """deliver_webhook sends X-Webhook-Signature header with sha256= prefix."""
    pytest.fail("RED — not yet implemented")


@pytest.mark.django_db
def test_deliver_webhook_records_attempt(delivery):
    """deliver_webhook creates a WebhookDeliveryAttempt record for each HTTP call."""
    pytest.fail("RED — not yet implemented")


@pytest.mark.django_db
def test_deliver_webhook_headers_present(delivery):
    """deliver_webhook sends X-Webhook-Id and X-Webhook-Timestamp headers."""
    pytest.fail("RED — not yet implemented")


# HOOK-04: circuit breaker


@pytest.mark.django_db
def test_circuit_breaker_disables_after_5_failures(endpoint):
    """Endpoint is auto-disabled after 5 consecutive fully-exhausted delivery failures."""
    pytest.fail("RED — not yet implemented")


@pytest.mark.django_db
def test_circuit_breaker_sends_email(endpoint):
    """Auto-disabling an endpoint sends an email notification to the org admin."""
    pytest.fail("RED — not yet implemented")


@pytest.mark.django_db
def test_circuit_breaker_resets_on_success(endpoint):
    """A successful delivery resets consecutive_failures to 0 on the endpoint."""
    pytest.fail("RED — not yet implemented")


@pytest.mark.django_db
def test_cleanup_task_removes_old_deliveries(delivery):
    """Cleanup task deletes WebhookDelivery records older than retention window."""
    pytest.fail("RED — not yet implemented")
