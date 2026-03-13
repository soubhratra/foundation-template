"""Shared fixtures for the audit test suite.

The top-level import in __init__.py causes collection to fail with ImportError
until apps.audit is implemented — correct RED state before Phase 29 ships.
"""

import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def org_owner(db):
    """A user who owns the test org."""
    return User.objects.create_user(
        username="auditowner",
        email="auditowner@example.com",
        password="testpass123",  # pragma: allowlist secret
    )


@pytest.fixture
def org(db, org_owner):
    """An Organization owned by org_owner."""
    from apps.orgs.models import Organization

    return Organization.objects.create(
        name="Audit Test Org",
        slug="audit-test-org",
        owner=org_owner,
    )


@pytest.fixture
def org_admin(db, org):
    """A second user with ADMIN membership in the test org."""
    from apps.orgs.models import Membership

    user = User.objects.create_user(
        username="auditadmin",
        email="auditadmin@example.com",
        password="testpass123",  # pragma: allowlist secret
    )
    Membership.objects.create(org=org, user=user, role=Membership.Role.ADMIN)
    return user


@pytest.fixture
def org_member(db, org):
    """A user with plain MEMBER membership in the test org."""
    from apps.orgs.models import Membership

    user = User.objects.create_user(
        username="auditmember",
        email="auditmember@example.com",
        password="testpass123",  # pragma: allowlist secret
    )
    Membership.objects.create(org=org, user=user, role=Membership.Role.MEMBER)
    return user


@pytest.fixture
def api_key_instance(db, org_owner):
    """An APIKey for org_owner."""
    from apps.api_keys.models import APIKey

    raw_key, prefix, hashed = APIKey.generate_key()
    return APIKey.objects.create(
        user=org_owner,
        name="Test key",
        prefix=prefix,
        hashed_key=hashed,
        scopes=["read"],
    )


@pytest.fixture
def webhook_endpoint_instance(db, org):
    """A WebhookEndpoint for the test org."""
    from apps.webhooks.models import WebhookEndpoint

    raw_secret, display_secret, hashed = WebhookEndpoint.generate_secret()
    return WebhookEndpoint.objects.create(
        org=org,
        url="https://example.com/hook",
        hashed_secret=hashed,
        display_secret=display_secret,
    )
