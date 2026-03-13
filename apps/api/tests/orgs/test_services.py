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


# ---------------------------------------------------------------------------- #
# Phase 32: Webhook wiring + invite URL (RED stubs — Plan 32-02 makes GREEN)
# ---------------------------------------------------------------------------- #


@pytest.mark.django_db
def test_add_member_fires_user_created_for_first_org(db, org, org_owner):
    """HOOK-01: add_member() fires user.created webhook when this is the user's first org."""
    from unittest.mock import patch

    new_user = User.objects.create_user(
        username="newmember_wh1",
        email="newmember_wh1@example.com",
        password="testpass123",  # pragma: allowlist secret
    )

    with patch("apps.orgs.services.fire_webhook_event") as mock_fire:
        MembershipService.add_member(org=org, user=new_user, role="member")

    event_types = [c.args[1] for c in mock_fire.call_args_list]
    assert "user.created" in event_types, (
        f"Expected 'user.created' webhook to fire for first-org member, got: {event_types}"
    )


@pytest.mark.django_db
def test_add_member_fires_org_member_added(db, org, org_owner):
    """HOOK-01: add_member() fires org.member_added webhook on every add."""
    from unittest.mock import patch

    new_user = User.objects.create_user(
        username="newmember_wh2",
        email="newmember_wh2@example.com",
        password="testpass123",  # pragma: allowlist secret
    )

    with patch("apps.orgs.services.fire_webhook_event") as mock_fire:
        MembershipService.add_member(org=org, user=new_user, role="member")

    event_types = [c.args[1] for c in mock_fire.call_args_list]
    assert "org.member_added" in event_types, (
        f"Expected 'org.member_added' webhook to fire, got: {event_types}"
    )


@pytest.mark.django_db
def test_add_member_no_user_created_for_second_org(db, org, org_owner):
    """HOOK-01: add_member() does NOT fire user.created when user already has a membership."""
    from unittest.mock import patch

    from apps.orgs.models import Membership

    new_user = User.objects.create_user(
        username="newmember_wh3",
        email="newmember_wh3@example.com",
        password="testpass123",  # pragma: allowlist secret
    )

    second_org = OrgService.create_org(name="Second Org", slug="second-org", owner=org_owner)

    # Bypass add_member so no webhook fires for the first membership
    Membership.objects.create(org=org, user=new_user, role="member")

    with patch("apps.orgs.services.fire_webhook_event") as mock_fire:
        MembershipService.add_member(org=second_org, user=new_user, role="member")

    event_types = [c.args[1] for c in mock_fire.call_args_list]
    assert "user.created" not in event_types, (
        f"Expected 'user.created' NOT to fire for second-org member, got: {event_types}"
    )
    assert "org.member_added" in event_types, (
        f"Expected 'org.member_added' to fire even for second-org member, got: {event_types}"
    )


@pytest.mark.django_db
def test_invite_accept_url_uses_frontend_url(db, org, org_owner, on_commit_immediately):
    """ORG-02: InvitationService.invite() uses FRONTEND_URL setting for accept_url."""
    from unittest.mock import patch

    from django.test import override_settings

    with override_settings(FRONTEND_URL="https://my-product.example.com"):
        with patch("apps.notifications.utils.send_email") as mock_send:
            InvitationService.invite(
                org=org,
                invited_by=org_owner,
                email="guest@example.com",
            )

    context = mock_send.call_args.kwargs["context"]
    assert context["accept_url"].startswith("https://my-product.example.com"), (
        f"accept_url should use FRONTEND_URL, got: {context['accept_url']}"
    )
