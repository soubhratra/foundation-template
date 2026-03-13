"""Service classes for the orgs B2B module.

Provides three service classes:
- OrgService: org creation
- MembershipService: role management and ownership transfer
- InvitationService: email invitation flow with session-based new-user support

Also provides _resolve_org_plan_id() for entitlement resolution.

All services use class methods so callers do not need to instantiate them.
"""

from django.db import transaction

# Re-export ServiceError so callers can do: from apps.orgs.services import ServiceError
from apps.core.exceptions import (  # noqa: F401
    NotFoundError,
    PermissionDeniedError,
    ServiceError,
)

# Session key used to persist a pending invite token across the login/signup flow.
# Stored when an unauthenticated user follows an invite link; consumed by
# consume_pending_invite_on_signup signal after allauth completes signup.
PENDING_INVITE_SESSION_KEY = "pending_invite_token"


class OrgService:
    """Handles org creation."""

    @classmethod
    def create_org(cls, *, name: str, slug: str, owner) -> object:
        """Create an Organization and an owner Membership in a single transaction.

        Args:
            name: Display name for the organization.
            slug: URL-safe identifier; normalized to lowercase.
            owner: User instance who will own the org.

        Returns:
            The created Organization instance.
        """
        from apps.orgs.models import Membership, Organization

        slug = slug.lower()
        with transaction.atomic():
            org = Organization.objects.create(name=name, slug=slug, owner=owner)
            Membership.objects.create(org=org, user=owner, role=Membership.Role.OWNER)
        return org


class MembershipService:
    """Handles membership queries and role management."""

    @classmethod
    def list_members(cls, *, org) -> object:
        """Return all Memberships for an org with user pre-fetched (no N+1)."""
        from apps.orgs.models import Membership

        return Membership.objects.filter(org=org).select_related("user")

    @classmethod
    def update_role(cls, *, org, target_user, new_role: str, acting_user) -> object:
        """Update target_user's role in org.

        Args:
            org: The Organization.
            target_user: The user whose role to change.
            new_role: New role string (owner/admin/member).
            acting_user: The user performing the action (must be owner/admin).

        Returns:
            The updated Membership instance.

        Raises:
            PermissionDeniedError: If acting_user is not owner/admin.
            NotFoundError: If target_user has no Membership in org.
            ServiceError: If attempting to demote the sole owner.
        """
        from apps.orgs.models import Membership

        acting_membership = Membership.objects.filter(
            org=org, user=acting_user, role__in=[Membership.Role.OWNER, Membership.Role.ADMIN]
        ).first()
        if not acting_membership:
            raise PermissionDeniedError("You must be an owner or admin to change roles.")

        target_membership = Membership.objects.filter(org=org, user=target_user).first()
        if not target_membership:
            raise NotFoundError("Target user is not a member of this organization.")

        # Prevent leaving org without an owner
        if target_membership.role == Membership.Role.OWNER and new_role != Membership.Role.OWNER:
            owner_count = Membership.objects.filter(org=org, role=Membership.Role.OWNER).count()
            if owner_count <= 1:
                raise ServiceError(
                    code="ORG_001",
                    message="Cannot demote the sole owner. Transfer ownership first.",
                )

        target_membership.role = new_role
        target_membership.save(update_fields=["role", "updated_at"])
        return target_membership

    @classmethod
    def remove_member(cls, *, org, target_user, acting_user) -> None:
        """Remove target_user from org.

        Args:
            org: The Organization.
            target_user: The user to remove.
            acting_user: The user performing the removal (must be owner/admin).

        Raises:
            PermissionDeniedError: If acting_user is not owner/admin.
            ServiceError: If target_user is the org owner.
        """
        from apps.orgs.models import Membership

        acting_membership = Membership.objects.filter(
            org=org, user=acting_user, role__in=[Membership.Role.OWNER, Membership.Role.ADMIN]
        ).first()
        if not acting_membership:
            raise PermissionDeniedError("You must be an owner or admin to remove members.")

        target_membership = Membership.objects.filter(org=org, user=target_user).first()
        if not target_membership:
            raise NotFoundError("Target user is not a member of this organization.")

        if target_membership.role == Membership.Role.OWNER:
            raise ServiceError(
                code="ORG_002",
                message="Cannot remove the org owner. Transfer ownership first.",
            )

        target_membership.delete()

    @classmethod
    def transfer_ownership(cls, *, org, current_owner, new_owner) -> None:
        """Atomically transfer org ownership from current_owner to new_owner.

        Args:
            org: The Organization.
            current_owner: The current owner user.
            new_owner: The user to promote to owner (must already be a member).

        Raises:
            NotFoundError: If new_owner has no Membership in org.
        """
        from apps.orgs.models import Membership

        new_owner_membership = Membership.objects.filter(org=org, user=new_owner).first()
        if not new_owner_membership:
            raise NotFoundError("New owner must already be a member of this organization.")

        with transaction.atomic():
            Membership.objects.filter(org=org, user=current_owner).update(
                role=Membership.Role.ADMIN
            )
            Membership.objects.filter(org=org, user=new_owner).update(role=Membership.Role.OWNER)


class InvitationService:
    """Handles the email invitation flow for adding users to orgs."""

    @classmethod
    def invite(cls, *, org, invited_by, email: str) -> object:
        """Send an invitation email to email to join org.

        - Raises ServiceError if email is already an active member.
        - Revokes any existing PENDING invitation for (org, email) before creating a new one.
        - Sends the invitation email via send_email().

        Args:
            org: The Organization to invite the user to.
            invited_by: The User sending the invitation.
            email: The email address to invite.

        Returns:
            The created Invitation instance.

        Raises:
            ServiceError: If email is already an active member.
        """
        from apps.notifications.utils import send_email
        from apps.orgs.models import Invitation, Membership

        email = email.lower().strip()

        # Check if email is already an active member
        already_member = Membership.objects.filter(org=org, user__email__iexact=email).exists()
        if already_member:
            raise ServiceError(
                code="ORG_003",
                message="This email address is already a member of the organization.",
            )

        # Revoke any existing pending invitation for the same (org, email) pair
        Invitation.objects.filter(
            org=org, email__iexact=email, status=Invitation.Status.PENDING
        ).update(status=Invitation.Status.REVOKED)

        # Create new invitation
        invitation = Invitation.objects.create(
            org=org,
            email=email,
            token=Invitation.generate_token(),
            expires_at=Invitation.make_expiry(),
            invited_by=invited_by,
        )

        send_email(
            to=invitation.email,
            template_name="org_invitation.html",
            context={
                "org_name": org.name,
                "accept_url": f"https://app.example.com/accept-invite?token={invitation.token}",
                "expires_hours": 72,
            },
        )

        return invitation

    @classmethod
    def accept(cls, *, invitation, user=None, request=None) -> dict:
        """Accept an invitation.

        If user is None or unauthenticated: store token in session and signal redirect.
        If user email doesn't match invitation email: raise ServiceError.
        If email matches: mark ACCEPTED, create Membership(role=member).

        Args:
            invitation: The Invitation instance to accept.
            user: Authenticated User (or None for unauthenticated).
            request: Django request (optional, used for session when user is None).

        Returns:
            dict with {"status": "accepted"} on success or {"redirect": "..."} for anon users.

        Raises:
            ServiceError: If invitation is invalid, email mismatch, or already a member.
        """
        from django.db import IntegrityError

        from apps.orgs.models import Invitation, Membership

        if not invitation.is_valid():
            raise ServiceError(
                code="ORG_004",
                message="This invitation has expired or has already been used.",
            )

        if user is None or (hasattr(user, "is_authenticated") and not user.is_authenticated):
            if request is not None:
                request.session[PENDING_INVITE_SESSION_KEY] = invitation.token
            return {"redirect": "/signup?invite_pending=1"}

        # Email match check (case-insensitive)
        if user.email.lower() != invitation.email.lower():
            raise ServiceError(
                code="ORG_005",
                message="This invitation was sent to a different email address.",
            )

        with transaction.atomic():
            invitation.status = Invitation.Status.ACCEPTED
            invitation.save(update_fields=["status"])
            try:
                Membership.objects.create(
                    org=invitation.org, user=user, role=Membership.Role.MEMBER
                )
            except IntegrityError:
                raise ServiceError(
                    code="ORG_006",
                    message="You are already a member of this organization.",
                    status_code=409,
                ) from None

        return {"status": "accepted"}

    @classmethod
    def store_pending_invite(cls, *, request, token: str) -> None:
        """Store an invite token in the session for post-signup pickup.

        Called when an unauthenticated user accesses an invite link.
        The token is consumed by the user_signed_up signal after allauth signup.

        Args:
            request: Django request with a writable session.
            token: The invitation token string.
        """
        request.session[PENDING_INVITE_SESSION_KEY] = token

    @classmethod
    def revoke(cls, *, invitation_id: int, acting_user, org) -> None:
        """Revoke a pending invitation.

        Args:
            invitation_id: Primary key of the Invitation.
            acting_user: User performing the revocation (must be owner/admin).
            org: The Organization (scopes the lookup).

        Raises:
            NotFoundError: If no such invitation exists in org.
            PermissionDeniedError: If acting_user is not owner/admin.
        """
        from apps.orgs.models import Invitation, Membership

        invitation = Invitation.objects.filter(id=invitation_id, org=org).first()
        if not invitation:
            raise NotFoundError("Invitation not found.")

        acting_membership = Membership.objects.filter(
            org=org, user=acting_user, role__in=[Membership.Role.OWNER, Membership.Role.ADMIN]
        ).first()
        if not acting_membership:
            raise PermissionDeniedError("You must be an owner or admin to revoke invitations.")

        invitation.status = Invitation.Status.REVOKED
        invitation.save(update_fields=["status"])


def _resolve_org_plan_id(org) -> str | None:
    """Return the active plan_id for an org's subscription, or None if no subscription.

    Used by has_org_feature() in core/entitlements.py to gate features on org plan.
    Uses lazy imports inside function to avoid circular import between orgs and billing.

    Note: The billing Subscription model links to user-based Customer, not OrgCustomer.
    This function returns None until a per-org Subscription model exists (Phase 27+).
    OrgCustomer records the stripe_customer_id for the org; when org billing is wired
    up it will allow lookup via stripe_customer_id matching.
    """
    try:
        from apps.orgs.models import OrgCustomer

        org_customer = OrgCustomer.objects.get(org=org)
        if not org_customer.stripe_customer_id:
            return None

        # Attempt lookup via billing Subscription model if it supports org customers.
        # The current Subscription model links to user-based Customer; this will
        # return None until a per-org subscription is implemented in Phase 27+.
        from apps.billing.models import Subscription

        sub = Subscription.objects.filter(
            customer__stripe_customer_id=org_customer.stripe_customer_id,
            status="active",
        ).first()
        if sub and sub.plan_id:
            return sub.plan_id
    except Exception:
        pass
    return None
