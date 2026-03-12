"""Phase 22 RBAC: RED test stubs for RBAC-01, RBAC-02, RBAC-03.

These tests all FAIL against the current codebase because:
- apps/accounts/permissions.py does not exist (RequireRole not implemented)
- AdminController does not exist in apps/accounts/controllers.py
- Migration 0003_seed_roles does not exist (admin/member Groups not seeded)

Every test uses the import-gate pattern: try/except ImportError inside the test
body with pytest.fail() to produce a readable failure message (not a collection
ERROR that would block other test files).

Pattern established in Phase 20 (social-auth) and Phase 21 (gdpr-baseline).
"""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_or_fail_admin_user(db_fixture_used):
    """Create and return a user in the 'admin' group, or call pytest.fail()."""
    from django.contrib.auth.models import Group

    user = User.objects.create_user(
        username="rbac_admin",
        email="admin@test.com",
        password="testpass123",  # pragma: allowlist secret
    )
    try:
        admin_group = Group.objects.get(name="admin")
    except Group.DoesNotExist:
        pytest.fail(
            "Django Group 'admin' does not exist. "
            "Create migration apps/accounts/migrations/0003_seed_roles.py "
            "that seeds 'admin' and 'member' groups via get_or_create."
        )
    user.groups.add(admin_group)
    return user


def _get_or_fail_member_user(db_fixture_used):
    """Create and return a user in the 'member' group, or call pytest.fail()."""
    from django.contrib.auth.models import Group

    user = User.objects.create_user(
        username="rbac_member",
        email="member@test.com",
        password="testpass123",  # pragma: allowlist secret
    )
    try:
        member_group = Group.objects.get(name="member")
    except Group.DoesNotExist:
        pytest.fail(
            "Django Group 'member' does not exist. "
            "Create migration apps/accounts/migrations/0003_seed_roles.py "
            "that seeds 'admin' and 'member' groups via get_or_create."
        )
    user.groups.add(member_group)
    return user


# ---------------------------------------------------------------------------
# RBAC-01: RequireRole permission class
# ---------------------------------------------------------------------------


class TestRequireRole:
    """RBAC-01: RequireRole("admin") permission class.

    RequireRole is a Django Ninja Extra permission class that checks whether the
    authenticated user is a member of the named Django Group.

    Endpoint: any controller that uses permissions=[RequireRole("admin")]
    Expected behaviours:
    - admin user (member of "admin" group) → HTTP 200
    - authenticated non-admin → HTTP 403
    - unauthenticated → HTTP 403
    """

    @pytest.mark.django_db
    def test_admin_user_passes(self) -> None:
        """Admin user with 'admin' group gets through RequireRole('admin') → 200."""
        try:
            from apps.accounts.permissions import RequireRole  # noqa: F401
        except ImportError:
            pytest.fail(
                "RequireRole not found in apps.accounts.permissions — "
                "create apps/accounts/permissions.py with a RequireRole class "
                "that subclasses ninja_extra.permissions.BasePermission"
            )

        from ninja.testing import TestClient

        try:
            from apps.accounts.controllers import AdminController
        except ImportError:
            pytest.fail(
                "AdminController not found in apps.accounts.controllers — "
                "create AdminController at prefix '/admin/users' "
                "with permissions=[RequireRole('admin')]"
            )

        admin_user = _get_or_fail_admin_user(True)
        client = TestClient(AdminController)
        client.force_login(admin_user)
        response = client.get("/")

        assert response.status_code == 200, (
            f"Expected 200 for admin user, got {response.status_code}. "
            "RequireRole('admin') must allow users who are members of the 'admin' group."
        )

    @pytest.mark.django_db
    def test_non_admin_gets_403(self) -> None:
        """Plain user without 'admin' group → 403 from RequireRole('admin')."""
        try:
            from apps.accounts.permissions import RequireRole  # noqa: F401
        except ImportError:
            pytest.fail(
                "RequireRole not found in apps.accounts.permissions — "
                "create apps/accounts/permissions.py with RequireRole class"
            )

        from ninja.testing import TestClient

        try:
            from apps.accounts.controllers import AdminController
        except ImportError:
            pytest.fail(
                "AdminController not found in apps.accounts.controllers — "
                "create AdminController at prefix '/admin/users'"
            )

        member_user = _get_or_fail_member_user(True)
        client = TestClient(AdminController)
        client.force_login(member_user)
        response = client.get("/")

        assert response.status_code == 403, (
            f"Expected 403 for non-admin user, got {response.status_code}. "
            "RequireRole('admin') must deny users who are NOT in the 'admin' group."
        )

    @pytest.mark.django_db
    def test_unauthenticated_gets_403(self) -> None:
        """Unauthenticated request → 403 from RequireRole('admin')."""
        try:
            from apps.accounts.permissions import RequireRole  # noqa: F401
        except ImportError:
            pytest.fail(
                "RequireRole not found in apps.accounts.permissions — "
                "create apps/accounts/permissions.py with RequireRole class"
            )

        from ninja.testing import TestClient

        try:
            from apps.accounts.controllers import AdminController
        except ImportError:
            pytest.fail(
                "AdminController not found in apps.accounts.controllers — "
                "create AdminController at prefix '/admin/users'"
            )

        client = TestClient(AdminController)
        # No force_login — unauthenticated
        response = client.get("/")

        assert response.status_code == 403, (
            f"Expected 403 for unauthenticated request, got {response.status_code}. "
            "RequireRole('admin') must deny unauthenticated requests."
        )


# ---------------------------------------------------------------------------
# RBAC-02: AdminController endpoints
# ---------------------------------------------------------------------------


class TestAdminController:
    """RBAC-02: AdminController — admin-only user management endpoints.

    AdminController sits at /admin/users and exposes:
    - GET  /          → list all users
    - GET  /{user_id}/roles       → get a user's roles
    - POST /{user_id}/roles       → assign a role to a user
    - DELETE /{user_id}/roles/{role} → remove a role from a user
    """

    @pytest.mark.django_db
    def test_list_users_admin(self) -> None:
        """Admin user calls GET /admin/users → 200."""
        try:
            from apps.accounts.controllers import AdminController
        except ImportError:
            pytest.fail(
                "AdminController not found in apps.accounts.controllers — "
                "create AdminController at prefix '/admin/users' "
                "with GET / listing all users"
            )

        from ninja.testing import TestClient

        admin_user = _get_or_fail_admin_user(True)
        client = TestClient(AdminController)
        client.force_login(admin_user)
        response = client.get("/")

        assert response.status_code == 200, (
            f"Expected 200 for admin user listing users, got {response.status_code}. "
            "GET /admin/users must return 200 for admin users."
        )

    @pytest.mark.django_db
    def test_list_users_non_admin(self) -> None:
        """Member user (non-admin) calls GET /admin/users → 403."""
        try:
            from apps.accounts.controllers import AdminController
        except ImportError:
            pytest.fail(
                "AdminController not found in apps.accounts.controllers — "
                "create AdminController at prefix '/admin/users'"
            )

        from ninja.testing import TestClient

        member_user = _get_or_fail_member_user(True)
        client = TestClient(AdminController)
        client.force_login(member_user)
        response = client.get("/")

        assert response.status_code == 403, (
            f"Expected 403 for non-admin listing users, got {response.status_code}. "
            "GET /admin/users must return 403 for non-admin users."
        )

    @pytest.mark.django_db
    def test_assign_role(self) -> None:
        """Admin assigns 'member' role to another user via POST /{user_id}/roles → 200."""
        try:
            from apps.accounts.controllers import AdminController
        except ImportError:
            pytest.fail(
                "AdminController not found in apps.accounts.controllers — "
                "create AdminController with POST /{user_id}/roles endpoint"
            )

        from ninja.testing import TestClient

        admin_user = _get_or_fail_admin_user(True)
        member_user = _get_or_fail_member_user(True)
        client = TestClient(AdminController)
        client.force_login(admin_user)
        response = client.post(f"/{member_user.pk}/roles", json={"role": "member"})

        assert response.status_code == 200, (
            f"Expected 200 for assigning role, got {response.status_code}. "
            "POST /admin/users/{user_id}/roles must return 200 when role assignment succeeds."
        )

    @pytest.mark.django_db
    def test_assign_unknown_role(self) -> None:
        """Admin assigns an unknown role → 400."""
        try:
            from apps.accounts.controllers import AdminController
        except ImportError:
            pytest.fail(
                "AdminController not found in apps.accounts.controllers — "
                "create AdminController with POST /{user_id}/roles validation"
            )

        from ninja.testing import TestClient

        admin_user = _get_or_fail_admin_user(True)
        member_user = _get_or_fail_member_user(True)
        client = TestClient(AdminController)
        client.force_login(admin_user)
        response = client.post(f"/{member_user.pk}/roles", json={"role": "unknown_role"})

        assert response.status_code == 400, (
            f"Expected 400 for unknown role, got {response.status_code}. "
            "POST /admin/users/{user_id}/roles must return 400 for unrecognised role names."
        )

    @pytest.mark.django_db
    def test_assign_role_to_self(self) -> None:
        """Admin calls POST with own user_id → 400 (cannot modify own roles)."""
        try:
            from apps.accounts.controllers import AdminController
        except ImportError:
            pytest.fail(
                "AdminController not found in apps.accounts.controllers — "
                "create AdminController with self-assignment guard"
            )

        from ninja.testing import TestClient

        admin_user = _get_or_fail_admin_user(True)
        client = TestClient(AdminController)
        client.force_login(admin_user)
        response = client.post(f"/{admin_user.pk}/roles", json={"role": "member"})

        assert response.status_code == 400, (
            f"Expected 400 when assigning role to self, got {response.status_code}. "
            "POST /admin/users/{user_id}/roles must return 400 when user_id == request.user.id."
        )

    @pytest.mark.django_db
    def test_remove_role(self) -> None:
        """Admin removes 'member' role from user via DELETE /{user_id}/roles/member → 200."""
        try:
            from apps.accounts.controllers import AdminController
        except ImportError:
            pytest.fail(
                "AdminController not found in apps.accounts.controllers — "
                "create AdminController with DELETE /{user_id}/roles/{role} endpoint"
            )

        from ninja.testing import TestClient

        admin_user = _get_or_fail_admin_user(True)
        member_user = _get_or_fail_member_user(True)
        client = TestClient(AdminController)
        client.force_login(admin_user)
        response = client.delete(f"/{member_user.pk}/roles/member")

        assert response.status_code == 200, (
            f"Expected 200 for removing role, got {response.status_code}. "
            "DELETE /admin/users/{user_id}/roles/{role} must return 200 when removal succeeds."
        )

    @pytest.mark.django_db
    def test_remove_role_non_admin(self) -> None:
        """Member user (non-admin) calls DELETE /{user_id}/roles/{role} → 403."""
        try:
            from apps.accounts.controllers import AdminController
        except ImportError:
            pytest.fail(
                "AdminController not found in apps.accounts.controllers — "
                "create AdminController with permission guards"
            )

        from ninja.testing import TestClient

        admin_user = _get_or_fail_admin_user(True)
        member_user = _get_or_fail_member_user(True)
        client = TestClient(AdminController)
        client.force_login(member_user)
        response = client.delete(f"/{admin_user.pk}/roles/admin")

        assert response.status_code == 403, (
            f"Expected 403 for non-admin removing role, got {response.status_code}. "
            "DELETE /admin/users/{user_id}/roles/{role} must return 403 for non-admin users."
        )

    @pytest.mark.django_db
    def test_get_user_roles(self) -> None:
        """Admin calls GET /{user_id}/roles → 200 with list of role names."""
        try:
            from apps.accounts.controllers import AdminController
        except ImportError:
            pytest.fail(
                "AdminController not found in apps.accounts.controllers — "
                "create AdminController with GET /{user_id}/roles endpoint"
            )

        from ninja.testing import TestClient

        admin_user = _get_or_fail_admin_user(True)
        member_user = _get_or_fail_member_user(True)
        client = TestClient(AdminController)
        client.force_login(admin_user)
        response = client.get(f"/{member_user.pk}/roles")

        assert response.status_code == 200, (
            f"Expected 200 for getting user roles, got {response.status_code}. "
            "GET /admin/users/{user_id}/roles must return 200 for admin users."
        )
        data = response.json()
        assert isinstance(data, list), (
            f"Expected list of roles, got {type(data).__name__}. "
            "GET /admin/users/{user_id}/roles must return a JSON array of role name strings."
        )


# ---------------------------------------------------------------------------
# RBAC-03: Seed roles migration (Groups seeded by data migration)
# ---------------------------------------------------------------------------


class TestSeedRolesMigration:
    """RBAC-03: Data migration seeds 'admin' and 'member' Django Groups.

    Migration 0003_seed_roles must create both Groups when applied.
    The seed function must be callable directly for idempotency tests.
    """

    @pytest.mark.django_db
    def test_admin_group_exists(self) -> None:
        """After applying migrations, Group named 'admin' exists."""
        from django.contrib.auth.models import Group

        assert Group.objects.filter(name="admin").exists(), (
            "Group 'admin' does not exist. "
            "Create a Django data migration (0003_seed_roles.py) that calls "
            "Group.objects.get_or_create(name='admin')."
        )

    @pytest.mark.django_db
    def test_member_group_exists(self) -> None:
        """After applying migrations, Group named 'member' exists."""
        from django.contrib.auth.models import Group

        assert Group.objects.filter(name="member").exists(), (
            "Group 'member' does not exist. "
            "Create a Django data migration (0003_seed_roles.py) that calls "
            "Group.objects.get_or_create(name='member')."
        )

    @pytest.mark.django_db
    def test_migration_idempotent(self) -> None:
        """Calling seed_roles() twice does not raise and produces exactly 2 groups."""
        try:
            from apps.accounts.migrations.migration_0003_seed_roles import seed_roles
        except ImportError:
            pytest.fail(
                "Migration file apps/accounts/migrations/migration_0003_seed_roles.py "
                "not found — create a Django data migration at that path with a "
                "seed_roles(apps, schema_editor) function that creates 'admin' and "
                "'member' Groups using get_or_create."
            )

        import django.apps as django_apps_registry

        # Call twice — must not raise
        try:
            seed_roles(apps=django_apps_registry.apps, schema_editor=None)
            seed_roles(apps=django_apps_registry.apps, schema_editor=None)
        except Exception as exc:
            pytest.fail(
                f"seed_roles() raised {type(exc).__name__}: {exc} on second call. "
                "seed_roles must be idempotent — use get_or_create, not create."
            )

        from django.contrib.auth.models import Group

        group_count = Group.objects.filter(name__in=["admin", "member"]).count()
        assert group_count == 2, (
            f"Expected exactly 2 groups ('admin' and 'member'), found {group_count}. "
            "seed_roles() called twice must not create duplicate groups."
        )
