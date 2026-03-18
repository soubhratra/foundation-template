"""Model-level tests for the orgs app.

Covers:
- ORG-01: Organization slug uniqueness constraint
- BILL-01: OrgCustomer auto-created when Organization is created
- ORG-02 (partial): Invitation.is_valid() returns False after expiry
"""

from datetime import timedelta

import pytest
from django.db import IntegrityError
from django.utils import timezone

from apps.orgs.models import Invitation, Organization, OrgCustomer


@pytest.mark.req("ORG-01")
@pytest.mark.django_db
def test_org_slug_unique(db):
    """ORG-01: Two organizations with the same slug raise IntegrityError."""
    from django.contrib.auth import get_user_model

    User = get_user_model()
    owner = User.objects.create_user(
        username="slugowner",
        email="slugowner@example.com",
        password="testpass123",  # pragma: allowlist secret
    )
    Organization.objects.create(name="First Corp", slug="acme", owner=owner)

    with pytest.raises(IntegrityError):
        Organization.objects.create(name="Second Corp", slug="acme", owner=owner)


@pytest.mark.req("ORG-01")
@pytest.mark.django_db
def test_org_customer_auto_created(db):
    """BILL-01: Creating an Organization automatically creates an OrgCustomer row."""
    from django.contrib.auth import get_user_model

    User = get_user_model()
    owner = User.objects.create_user(
        username="billingowner",
        email="billingowner@example.com",
        password="testpass123",  # pragma: allowlist secret
    )
    org = Organization.objects.create(name="Billing Corp", slug="billing-corp", owner=owner)

    assert hasattr(org, "billing_customer"), (
        "Organization instance should have a 'billing_customer' reverse relation"
    )
    assert OrgCustomer.objects.filter(org=org).exists(), (
        "OrgCustomer row should be auto-created when Organization is created"
    )


@pytest.mark.req("ORG-02")
@pytest.mark.django_db
def test_invitation_is_valid_false_after_expiry(db):
    """ORG-02: Invitation.is_valid() returns False when expires_at is in the past."""
    from django.contrib.auth import get_user_model

    User = get_user_model()
    owner = User.objects.create_user(
        username="inviteowner",
        email="inviteowner@example.com",
        password="testpass123",  # pragma: allowlist secret
    )
    org = Organization.objects.create(name="Invite Corp", slug="invite-corp", owner=owner)
    expired_invitation = Invitation.objects.create(
        org=org,
        invited_by=owner,
        email="expireduser@example.com",
        expires_at=timezone.now() - timedelta(hours=1),
    )

    assert expired_invitation.is_valid() is False, (
        "Invitation.is_valid() should return False when expires_at is in the past"
    )
