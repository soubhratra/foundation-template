"""Shared fixtures for the api_keys test suite.

The top-level import in __init__.py causes collection to fail with ImportError
until apps.api_keys is implemented — correct RED state before Phase 28 ships.
"""

import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def api_user(db):
    """A user who will own API keys."""
    return User.objects.create_user(
        username="apikeyuser",
        email="apikeyuser@example.com",
        password="testpass123",  # pragma: allowlist secret
    )


@pytest.fixture
def api_key(db, api_user):
    """A live APIKey belonging to api_user with read+write scopes."""
    from apps.api_keys.models import APIKey

    raw_key, stored_prefix, key_hash = APIKey.generate_key()
    key = APIKey.objects.create(
        user=api_user,
        prefix=stored_prefix,
        key_hash=key_hash,
        scopes=["read", "write"],
        name="Test Key",
        is_active=True,
    )
    key._raw_key = raw_key  # attached for tests that need to send the Bearer token
    return key


@pytest.fixture
def revoked_api_key(db, api_user):
    """An inactive APIKey belonging to api_user."""
    from apps.api_keys.models import APIKey

    raw_key, stored_prefix, key_hash = APIKey.generate_key()
    key = APIKey.objects.create(
        user=api_user,
        prefix=stored_prefix,
        key_hash=key_hash,
        scopes=["read"],
        name="Revoked Key",
        is_active=False,
    )
    key._raw_key = raw_key
    return key


@pytest.fixture
def org_for_apikey(db, api_user):
    """An Organization where api_user is a member — for org-scoped key tests."""
    from apps.orgs.models import Membership, Organization

    org = Organization.objects.create(name="API Key Org", slug="api-key-org", owner=api_user)
    Membership.objects.create(user=api_user, org=org, role="admin")
    return org
