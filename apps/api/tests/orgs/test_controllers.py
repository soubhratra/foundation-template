"""Controller-level tests for the orgs app.

Covers:
- ORG-05: Cross-org access returns 404 for non-members
"""

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

User = get_user_model()


@pytest.mark.req("ORG-05")
@pytest.mark.django_db
def test_cross_org_access_forbidden(db, org, org_owner):
    """ORG-05: GET /api/v1/org/{slug}/members/ returns 404 for a non-member user."""
    # Create a user who is NOT a member of the test org
    outsider = User.objects.create_user(
        username="outsider",
        email="outsider@example.com",
        password="testpass123",  # pragma: allowlist secret
    )

    client = Client()
    client.force_login(outsider)

    response = client.get(f"/api/v1/org/{org.slug}/members/")

    assert response.status_code == 404, (
        f"Non-member should receive 404 for org {org.slug!r} members endpoint, "
        f"got {response.status_code}"
    )
