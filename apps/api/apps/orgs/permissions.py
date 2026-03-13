"""Permission classes for org-scoped endpoints.

Security boundary for all org-scoped API endpoints. Must be applied in
the correct order — see IsOrgAdmin docstring for composition rules.
"""

from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpRequest
from ninja_extra import ControllerBase
from ninja_extra.permissions import BasePermission

from apps.orgs.models import Membership, Organization


class IsOrgMember(BasePermission):
    """Allow access only to authenticated members of the org identified by org_slug.

    Extracts `org_slug` from the URL kwargs, looks up the Organization,
    then verifies the request user has a Membership row.

    On success, sets ``request.org`` to the Organization instance so that
    downstream permissions (e.g. IsOrgAdmin) can read it without re-querying.

    Both "org not found" and "user not a member" raise Http404 — this
    ensures non-members cannot discover whether an org exists (security by
    obscurity, intentional).
    """

    def has_permission(self, request: HttpRequest, controller: ControllerBase) -> bool:
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False

        org_slug: str = request.resolver_match.kwargs.get("org_slug", "")

        try:
            org = Organization.objects.get(slug=org_slug)
        except Organization.DoesNotExist:
            raise Http404 from None

        membership = Membership.objects.filter(org=org, user=user).first()
        if membership is None:
            raise Http404

        request.org = org  # type: ignore[attr-defined]
        return True


class IsOrgAdmin(BasePermission):
    """Allow access only to org admins (role owner or admin).

    COMPOSITION RULE — CRITICAL:
    IsOrgAdmin MUST be composed after IsOrgMember. It reads ``request.org``
    which IsOrgMember sets. Using IsOrgAdmin alone will cause it to return
    False (programming error guard) and silently deny all requests.

    Correct usage on admin endpoints::

        permissions=[IsAuthenticated, IsOrgMember, IsOrgAdmin]

    NEVER use ``permissions=[IsAuthenticated, IsOrgAdmin]`` — ``request.org``
    will not be set and all requests will be denied with no useful error.
    """

    def has_permission(self, request: HttpRequest, controller: ControllerBase) -> bool:
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False

        org = getattr(request, "org", None)
        if not isinstance(org, Organization):
            # IsOrgMember was not in the permission chain (programming error) or
            # this is a direct test of IsOrgAdmin. Fall back to org_slug lookup.
            org_slug: str = request.resolver_match.kwargs.get("org_slug", "")
            try:
                org = Organization.objects.get(slug=org_slug)
            except Organization.DoesNotExist:
                return False

        admin_membership = Membership.objects.filter(
            org=org, user=user, role__in=[Membership.Role.OWNER, Membership.Role.ADMIN]
        ).first()

        if admin_membership is None:
            raise PermissionDenied

        return True
