"""Shared fixtures for org test suite.

Imports from apps.orgs.models at module top level — collection will fail with
ImportError until the orgs app is implemented (correct RED state).
"""

import pytest
from django.contrib.auth import get_user_model

from apps.orgs.models import Invitation, Membership, Organization

User = get_user_model()


@pytest.fixture
def org_owner(db):
    """A user who will own the test org."""
    return User.objects.create_user(
        username="orgowner",
        email="owner@example.com",
        password="testpass123",  # pragma: allowlist secret
    )


@pytest.fixture
def org(db, org_owner):
    """An Organization instance."""
    return Organization.objects.create(
        name="Acme Corp",
        slug="acme",
        owner=org_owner,
    )


@pytest.fixture
def org_membership(db, org, org_owner):
    """A Membership linking org_owner to org with role='owner'."""
    return Membership.objects.create(
        org=org,
        user=org_owner,
        role="owner",
    )


@pytest.fixture
def invitation(db, org, org_owner):
    """A pending Invitation for the test org."""
    from datetime import timedelta

    from django.utils import timezone

    return Invitation.objects.create(
        org=org,
        invited_by=org_owner,
        email="invitee@example.com",
        expires_at=timezone.now() + timedelta(hours=72),
    )
