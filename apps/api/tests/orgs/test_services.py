"""Service-level tests for the orgs app.

Covers:
- ORG-01: OrgService.create_org() creates owner membership
- ORG-02: InvitationService invite flow (send email, token expiry, email mismatch, new user session)
- ORG-04: MembershipService.transfer_ownership() promotes new owner, demotes old owner
"""

import pytest
from django.contrib.auth import get_user_model

from apps.orgs.services import InvitationService, MembershipService, OrgService

User = get_user_model()


@pytest.mark.django_db
def test_create_org_creates_owner_membership(db):
    """ORG-01: OrgService.create_org() creates org and membership with role='owner'."""
    from apps.orgs.models import Membership, Organization

    owner = User.objects.create_user(
        username="serviceowner",
        email="serviceowner@example.com",
        password="testpass123",  # pragma: allowlist secret
    )
    org = OrgService.create_org(name="Service Corp", slug="service-corp", owner=owner)

    assert isinstance(org, Organization)
    assert Membership.objects.filter(org=org, user=owner, role="owner").exists(), (
        "create_org should create a Membership with role='owner'"
    )


@pytest.mark.django_db
def test_invite_sends_email(db, org, org_owner, mailoutbox, on_commit_immediately):
    """ORG-02: InvitationService.invite() sends an email containing the invitation token."""
    invitation = InvitationService.invite(
        org=org,
        invited_by=org_owner,
        email="newmember@example.com",
    )

    assert len(mailoutbox) == 1, "One invitation email should have been sent"
    assert invitation.token is not None
    email_body = mailoutbox[0].body
    assert str(invitation.token) in email_body, (
        "Invitation token should be included in the email body"
    )


@pytest.mark.django_db
def test_invite_token_expiry(db, org, org_owner):
    """ORG-02: Invitation.is_valid() returns False after 72 hours."""
    from datetime import timedelta

    from django.utils import timezone

    from apps.orgs.models import Invitation

    invitation = Invitation.objects.create(
        org=org,
        invited_by=org_owner,
        email="expiry@example.com",
        expires_at=timezone.now() - timedelta(hours=73),
    )

    assert invitation.is_valid() is False, "Invitation should be invalid after 72-hour expiry"


@pytest.mark.django_db
def test_invite_accept_email_mismatch(db, org, org_owner):
    """ORG-02: Accepting an invitation with wrong email raises ServiceError with HTTP 400."""
    from apps.orgs.services import ServiceError

    invitation = InvitationService.invite(
        org=org,
        invited_by=org_owner,
        email="correct@example.com",
    )

    wrong_user = User.objects.create_user(
        username="wronguser",
        email="wrong@example.com",
        password="testpass123",  # pragma: allowlist secret
    )

    with pytest.raises(ServiceError) as exc_info:
        InvitationService.accept(invitation=invitation, user=wrong_user)

    assert exc_info.value.status_code == 400


@pytest.mark.django_db
def test_invite_accept_new_user_session_flow(db, org, org_owner):
    """ORG-02: Accepting when not logged in stores token in session for post-login pickup."""
    from unittest.mock import MagicMock

    invitation = InvitationService.invite(
        org=org,
        invited_by=org_owner,
        email="newuser@example.com",
    )

    # Simulate a request with an anonymous user and a session
    mock_request = MagicMock()
    mock_request.user.is_authenticated = False
    mock_request.session = {}

    InvitationService.store_pending_invite(request=mock_request, token=str(invitation.token))

    assert "pending_invite_token" in mock_request.session, (
        "Pending invite token should be stored in session for unauthenticated user"
    )
    assert mock_request.session["pending_invite_token"] == str(invitation.token)


@pytest.mark.django_db
def test_transfer_ownership(db, org, org_owner, org_membership):
    """ORG-04: transfer_ownership() promotes new owner, demotes old owner to admin."""
    from apps.orgs.models import Membership

    new_owner = User.objects.create_user(
        username="newowner",
        email="newowner@example.com",
        password="testpass123",  # pragma: allowlist secret
    )
    Membership.objects.create(org=org, user=new_owner, role="admin")

    MembershipService.transfer_ownership(org=org, new_owner=new_owner, current_owner=org_owner)

    new_membership = Membership.objects.get(org=org, user=new_owner)
    old_membership = Membership.objects.get(org=org, user=org_owner)

    assert new_membership.role == "owner", "New owner should have role='owner'"
    assert old_membership.role == "admin", "Old owner should be demoted to role='admin'"
