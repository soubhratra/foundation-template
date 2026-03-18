"""Permission-level tests for the orgs app.

Covers:
- ORG-03: IsOrgMember raises Http404 for non-members
- ORG-03: IsOrgAdmin raises PermissionDenied for member-role users
"""

from unittest.mock import MagicMock

import pytest
from django.contrib.auth import get_user_model

from apps.orgs.permissions import IsOrgAdmin, IsOrgMember

User = get_user_model()


@pytest.mark.req("ORG-03")
@pytest.mark.django_db
def test_non_member_gets_404(db, org):
    """ORG-03: IsOrgMember.has_permission() raises Http404 for a user not in the org."""
    from django.http import Http404

    non_member = User.objects.create_user(
        username="nonmember",
        email="nonmember@example.com",
        password="testpass123",  # pragma: allowlist secret
    )

    request = MagicMock()
    request.user = non_member
    request.resolver_match = MagicMock()
    request.resolver_match.kwargs = {"org_slug": org.slug}

    permission = IsOrgMember()

    with pytest.raises(Http404):
        permission.has_permission(request=request, controller=None)


@pytest.mark.req("ORG-03")
@pytest.mark.django_db
def test_member_role_admin_endpoint_gets_403(db, org, org_owner):
    """ORG-03: IsOrgAdmin.has_permission() raises PermissionDenied for member-role user."""
    from django.core.exceptions import PermissionDenied

    from apps.orgs.models import Membership

    regular_member = User.objects.create_user(
        username="regularmember",
        email="regularmember@example.com",
        password="testpass123",  # pragma: allowlist secret
    )
    Membership.objects.create(org=org, user=regular_member, role="member")

    request = MagicMock()
    request.user = regular_member
    request.resolver_match = MagicMock()
    request.resolver_match.kwargs = {"org_slug": org.slug}

    permission = IsOrgAdmin()

    with pytest.raises(PermissionDenied):
        permission.has_permission(request=request, controller=None)
