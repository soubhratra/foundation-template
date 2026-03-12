"""Conftest for GDPR accounts tests.

Patches ninja.testing module to:
1. Replace TestClient with ninja_extra's TestClient (supports ControllerBase classes).
2. Add a force_login() method so the RED test stubs (written using Django-style test
   client API) work without modification.

Background:
- The RED tests (Plan 01) use `from ninja.testing import TestClient` but pass
  a ControllerBase subclass to it. ninja's plain TestClient doesn't handle this —
  only ninja_extra's TestClient does.
- Both TestClients lack force_login(). We add it via NinjaClientBase patching
  so it's available on both.

force_login(user) sets request.user on every subsequent request, with
is_authenticated=True mirroring the real user object.
"""

import pytest


def _force_login(self, user):
    """Set the authenticated user on this test client instance.

    Mimics Django's Client.force_login() for ninja.testing.TestClient usage.
    Subsequent requests built by this client will have request.user = user.
    """
    self._forced_user = user


def _make_build_request_with_user(original_build_request):
    """Wrap _build_request to inject the forced user if set."""

    def _build_request(self, method, path, data, request_params):
        request = original_build_request(self, method, path, data, request_params)
        if hasattr(self, "_forced_user") and self._forced_user is not None:
            # Assign the real Django User object directly. is_authenticated is
            # a property on Django's AbstractBaseUser — no setter needed.
            request.user = self._forced_user
        return request

    return _build_request


@pytest.fixture(autouse=True, scope="session")
def patch_ninja_testclient_force_login():
    """Autouse session fixture: patch ninja.testing.TestClient for GDPR tests.

    - Replaces ninja.testing.TestClient with ninja_extra's TestClient
      so ControllerBase subclasses are handled correctly.
    - Adds force_login() to NinjaClientBase so test stubs can authenticate.
    """
    import ninja.testing as ninja_testing
    from ninja.testing.client import NinjaClientBase
    from ninja_extra.testing import TestClient as NinjaExtraTestClient

    # Replace ninja's TestClient with ninja_extra's (supports ControllerBase)
    ninja_testing.TestClient = NinjaExtraTestClient

    # Add force_login to NinjaClientBase (shared base for both TestClients)
    if not hasattr(NinjaClientBase, "force_login"):
        NinjaClientBase.force_login = _force_login
        NinjaClientBase._build_request = _make_build_request_with_user(
            NinjaClientBase._build_request
        )


# ---------------------------------------------------------------------------
# RBAC fixtures — admin_user and member_user (Phase 22)
# ---------------------------------------------------------------------------


@pytest.fixture
def admin_user(db):
    """A user who is a member of the 'admin' Django Group.

    Requires migration 0003_seed_roles to have run so that the 'admin'
    Group exists. The fixture will fail (RED) until that migration exists.
    """
    from django.contrib.auth import get_user_model
    from django.contrib.auth.models import Group

    UserModel = get_user_model()
    user = UserModel.objects.create_user(
        username="rbac_admin",
        email="admin@test.com",
        password="testpass123",  # pragma: allowlist secret
    )
    admin_group = Group.objects.get(name="admin")  # seeded by migration 0003
    user.groups.add(admin_group)
    return user


@pytest.fixture
def member_user(db):
    """A user who is a member of the 'member' Django Group only.

    Requires migration 0003_seed_roles to have run so that the 'member'
    Group exists. The fixture will fail (RED) until that migration exists.
    """
    from django.contrib.auth import get_user_model
    from django.contrib.auth.models import Group

    UserModel = get_user_model()
    user = UserModel.objects.create_user(
        username="rbac_member",
        email="member@test.com",
        password="testpass123",  # pragma: allowlist secret
    )
    member_group = Group.objects.get(name="member")  # seeded by migration 0003
    user.groups.add(member_group)
    return user
