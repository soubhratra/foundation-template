"""API controllers for the orgs B2B module.

Three controllers — all use prefix="/org":
- OrgController: org CRUD (create, get, update, delete)
- MembershipController: member listing, role changes, removal, ownership transfer
- InvitationController: send, revoke, and accept invite

Controllers are thin — all business logic delegates to service classes in
apps/orgs/services.py. Registered automatically via api.auto_discover_controllers()
in config/urls.py.
"""

from allauth.headless.contrib.ninja.security import jwt_token_auth
from django.http import Http404
from ninja.security import SessionAuth
from ninja_extra import ControllerBase, api_controller, route
from ninja_extra.permissions import IsAuthenticated

from apps.orgs.permissions import IsOrgAdmin, IsOrgMember
from apps.orgs.schemas import (
    AcceptInviteOut,
    InviteIn,
    InviteOut,
    MemberOut,
    OrgIn,
    OrgOut,
    OrgUpdateIn,
    RoleUpdateIn,
    TransferOwnershipIn,
)
from apps.orgs.services import InvitationService, MembershipService, OrgService

# ------------------------------------------------------------------
# Org CRUD
# ------------------------------------------------------------------


@api_controller(
    "/org",
    tags=["Organizations"],
    auth=[SessionAuth(), jwt_token_auth],
)
class OrgController(ControllerBase):
    """Handles org creation, retrieval, update, and deletion."""

    @route.post("/", response={201: OrgOut}, permissions=[IsAuthenticated], url_name="org-create")
    def create_org(self, request, body: OrgIn):
        """Create a new org and make the requesting user its owner."""
        org = OrgService.create_org(name=body.name, slug=body.slug, owner=request.user)
        return 201, OrgOut(
            id=org.pk,
            name=org.name,
            slug=org.slug,
            created_at=org.created_at,
        )

    @route.get(
        "/{org_slug}/",
        response=OrgOut,
        permissions=[IsAuthenticated, IsOrgMember],
        url_name="org-detail",
    )
    def get_org(self, request, org_slug: str):
        """Return org detail. IsOrgMember sets request.org."""
        org = request.org  # type: ignore[attr-defined]
        return OrgOut(
            id=org.pk,
            name=org.name,
            slug=org.slug,
            created_at=org.created_at,
        )

    @route.patch(
        "/{org_slug}/",
        response=OrgOut,
        permissions=[IsAuthenticated, IsOrgMember, IsOrgAdmin],
        url_name="org-update",
    )
    def update_org(self, request, org_slug: str, body: OrgUpdateIn):
        """Update org fields (currently only name)."""
        org = request.org  # type: ignore[attr-defined]
        if body.name is not None:
            org.name = body.name
            org.save(update_fields=["name", "updated_at"])
        return OrgOut(
            id=org.pk,
            name=org.name,
            slug=org.slug,
            created_at=org.created_at,
        )

    @route.delete(
        "/{org_slug}/",
        response={204: None},
        permissions=[IsAuthenticated, IsOrgMember, IsOrgAdmin],
        url_name="org-delete",
    )
    def delete_org(self, request, org_slug: str):
        """Delete the org (service enforces owner-only)."""
        from apps.orgs.models import Membership
        from apps.orgs.services import PermissionDeniedError

        org = request.org  # type: ignore[attr-defined]
        membership = Membership.objects.filter(
            org=org, user=request.user, role=Membership.Role.OWNER
        ).first()
        if not membership:
            raise PermissionDeniedError("Only the org owner can delete the organization.")
        org.delete()
        return 204, None


# ------------------------------------------------------------------
# Membership management
# ------------------------------------------------------------------


@api_controller(
    "/org",
    tags=["Organizations"],
    auth=[SessionAuth(), jwt_token_auth],
)
class MembershipController(ControllerBase):
    """Handles membership queries, role changes, removal, and ownership transfer."""

    @route.get(
        "/{org_slug}/members/",
        response=list[MemberOut],
        permissions=[IsAuthenticated, IsOrgMember],
        url_name="org-members-list",
    )
    def list_members(self, request, org_slug: str):
        """Return all members of the org."""
        memberships = MembershipService.list_members(org=request.org)  # type: ignore[attr-defined]
        return [
            MemberOut(
                user_id=m.user_id,
                email=m.user.email,
                role=m.role,
                joined_at=m.created_at,
            )
            for m in memberships
        ]

    @route.patch(
        "/{org_slug}/members/{user_id}/role/",
        response=MemberOut,
        permissions=[IsAuthenticated, IsOrgMember, IsOrgAdmin],
        url_name="org-member-role-update",
    )
    def update_member_role(self, request, org_slug: str, user_id: int, body: RoleUpdateIn):
        """Change a member's role."""
        from django.contrib.auth import get_user_model

        User = get_user_model()
        try:
            target_user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            raise Http404 from None

        membership = MembershipService.update_role(
            org=request.org,  # type: ignore[attr-defined]
            target_user=target_user,
            new_role=body.role,
            acting_user=request.user,
        )
        return MemberOut(
            user_id=membership.user_id,
            email=membership.user.email,
            role=membership.role,
            joined_at=membership.created_at,
        )

    @route.delete(
        "/{org_slug}/members/{user_id}/",
        response={204: None},
        permissions=[IsAuthenticated, IsOrgMember, IsOrgAdmin],
        url_name="org-member-remove",
    )
    def remove_member(self, request, org_slug: str, user_id: int):
        """Remove a member from the org."""
        from django.contrib.auth import get_user_model

        User = get_user_model()
        try:
            target_user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            raise Http404 from None

        MembershipService.remove_member(
            org=request.org,  # type: ignore[attr-defined]
            target_user=target_user,
            acting_user=request.user,
        )
        return 204, None

    @route.post(
        "/{org_slug}/transfer-ownership/",
        response=OrgOut,
        permissions=[IsAuthenticated, IsOrgMember, IsOrgAdmin],
        url_name="org-transfer-ownership",
    )
    def transfer_ownership(self, request, org_slug: str, body: TransferOwnershipIn):
        """Atomically transfer org ownership to another member."""
        from django.contrib.auth import get_user_model

        User = get_user_model()
        try:
            new_owner = User.objects.get(pk=body.new_owner_user_id)
        except User.DoesNotExist:
            raise Http404 from None

        MembershipService.transfer_ownership(
            org=request.org,  # type: ignore[attr-defined]
            current_owner=request.user,
            new_owner=new_owner,
        )
        org = request.org  # type: ignore[attr-defined]
        return OrgOut(
            id=org.pk,
            name=org.name,
            slug=org.slug,
            created_at=org.created_at,
        )


# ------------------------------------------------------------------
# Invitation flow
# ------------------------------------------------------------------


@api_controller(
    "/org",
    tags=["Organizations"],
    auth=[SessionAuth(), jwt_token_auth],
)
class InvitationController(ControllerBase):
    """Handles invitation sending, revocation, and acceptance."""

    @route.post(
        "/{org_slug}/invitations/",
        response={201: InviteOut},
        permissions=[IsAuthenticated, IsOrgMember, IsOrgAdmin],
        url_name="org-invite-send",
    )
    def send_invite(self, request, org_slug: str, body: InviteIn):
        """Send an invitation email to the given address."""
        invitation = InvitationService.invite(
            org=request.org,  # type: ignore[attr-defined]
            invited_by=request.user,
            email=body.email,
        )
        return 201, InviteOut(
            id=invitation.pk,
            invited_email=invitation.email,
            status=invitation.status,
            expires_at=invitation.expires_at,
            created_at=invitation.created_at,
        )

    @route.delete(
        "/{org_slug}/invitations/{invitation_id}/",
        response={204: None},
        permissions=[IsAuthenticated, IsOrgMember, IsOrgAdmin],
        url_name="org-invite-revoke",
    )
    def revoke_invite(self, request, org_slug: str, invitation_id: int):
        """Revoke a pending invitation."""
        InvitationService.revoke(
            invitation_id=invitation_id,
            acting_user=request.user,
            org=request.org,  # type: ignore[attr-defined]
        )
        return 204, None

    @route.get(
        "/invitations/accept/",
        response=AcceptInviteOut,
        # No IsAuthenticated — handles unauthenticated users (stores token in session)
        url_name="org-invite-accept",
    )
    def accept_invite(self, request, token: str):
        """Accept an invitation by token.

        Authenticated users are added as members immediately.
        Unauthenticated users receive a redirect URL and the token is stored
        in their session for pickup after signup (allauth user_signed_up signal).
        """
        from apps.orgs.models import Invitation

        invitation = Invitation.objects.filter(token=token).first()
        if invitation is None:
            raise Http404

        user = getattr(request, "user", None)
        authenticated_user = user if (user and user.is_authenticated) else None

        result = InvitationService.accept(
            invitation=invitation,
            user=authenticated_user,
            request=request,
        )
        return AcceptInviteOut(
            redirect=result.get("redirect"),
            message=result.get("message"),
            status=result.get("status"),
        )
