"""Shared fixtures for the webhooks test suite.

The top-level import in __init__.py causes collection to fail with ImportError
until apps.webhooks is implemented — correct RED state before Phase 27 ships.
"""

import pytest
from django.contrib.auth import get_user_model

from apps.orgs.models import Membership, Organization

User = get_user_model()


@pytest.fixture
def org_owner(db):
    """A user who owns the test org."""
    return User.objects.create_user(
        username="webhookowner",
        email="owner@example.com",
        password="testpass123",  # pragma: allowlist secret
    )


@pytest.fixture
def org(db, org_owner):
    """An Organization instance owned by org_owner."""
    return Organization.objects.create(
        name="Test Org",
        slug="test-org",
        owner=org_owner,
    )


@pytest.fixture
def org_admin(db, org):
    """A second user with ADMIN membership in the test org."""
    user = User.objects.create_user(
        username="webhookadmin",
        email="admin@example.com",
        password="testpass123",  # pragma: allowlist secret
    )
    Membership.objects.create(org=org, user=user, role=Membership.Role.ADMIN)
    return user


@pytest.fixture
def endpoint(db, org, org_admin):
    """A WebhookEndpoint belonging to the test org."""
    from apps.webhooks.models import WebhookEndpoint

    raw, signing_key, secret_hash = WebhookEndpoint.generate_secret()
    return WebhookEndpoint.objects.create(
        org=org,
        url="https://example.com/hooks",
        name="Test Hook",
        event_types=["user.created"],
        signing_key=signing_key,
        secret_hash=secret_hash,
    )


@pytest.fixture
def delivery(db, endpoint):
    """A WebhookDelivery in pending state for the test endpoint."""
    from apps.webhooks.models import WebhookDelivery

    return WebhookDelivery.objects.create(
        endpoint=endpoint,
        event_type="user.created",
        status="pending",
        request_body={
            "webhook_version": "v1",
            "event_type": "user.created",
            "data": {},
        },
        request_headers={},
    )
