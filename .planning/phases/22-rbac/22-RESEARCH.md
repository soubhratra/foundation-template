# Phase 22: RBAC - Research

**Researched:** 2026-03-12
**Domain:** Django Ninja Extra permission classes, Django Groups, data migrations
**Confidence:** HIGH

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions

- `RequireRole("admin")` is a **Ninja Extra permission class** (`BasePermission`), not a function decorator
- Applied via `permissions=[IsAuthenticated, RequireRole("admin")]` on controllers or routes
- Backing store: Django's built-in `Group` model — `user.groups.filter(name=role).exists()`
- `IsAuthenticated` is always listed explicitly alongside `RequireRole` — no hidden coupling
- When role check fails: raises `PermissionDenied("Insufficient role.")` — handled by existing `permission_denied_handler` in `config/urls.py` as HTTP 403 JSON
- `POST /api/v1/admin/users/{user_id}/roles` — body `{"role": "admin" | "member"}` — assign (idempotent)
- `DELETE /api/v1/admin/users/{user_id}/roles/{role}` — remove (idempotent)
- `GET /api/v1/admin/users/{user_id}/roles` — returns current role list
- `GET /api/v1/admin/users` — paginated list of all users
- Unknown role names → 400; only `"admin"` and `"member"` are valid (validated against `KNOWN_ROLES`)
- Self-modification blocked → 400 `{"detail": "Cannot modify your own roles."}`
- All RBAC code lives in `apps/accounts/`: `permissions.py`, `controllers.py` (AdminController added), `migrations/0003_seed_roles.py`
- `AdminController` prefix `/admin/users`, gated at controller level with `permissions=[IsAuthenticated, RequireRole("admin")]`
- Data migration uses `RunPython` with `apps.get_model("auth", "Group")`, `get_or_create` for idempotency
- Reverse migration is a no-op (`migrations.RunPython.noop`)
- RBAC is core infrastructure — no `--without rbac` flag

### Claude's Discretion

- Exact pagination style for `GET /api/v1/admin/users` (follow existing codebase patterns)
- Whether `AdminController` gets its own `services.py` or uses `UserService` directly
- Exact `KNOWN_ROLES` placement (module-level constant in `permissions.py` or `settings.py`)

### Deferred Ideas (OUT OF SCOPE)

- Web/mobile UI for role management
- Role inheritance (e.g., admin implicitly has member permissions)
- Custom permission scopes (fine-grained object-level permissions)
- Audit log for role changes
  </user_constraints>

<phase_requirements>

## Phase Requirements

| ID      | Description                                                                                                                    | Research Support                                                                                                                                                           |
| ------- | ------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| RBAC-01 | API endpoints can be protected with a `RequireRole("admin")` permission class that returns HTTP 403 for users without the role | `RequireRole` subclasses `BasePermission`, overrides `has_permission()`, raises `PermissionDenied` which the existing `permission_denied_handler` formats as HTTP 403 JSON |
| RBAC-02 | Authenticated admin user can assign or remove roles from other users via role management endpoints                             | `AdminController` at `/admin/users` gated by `RequireRole("admin")` provides POST/DELETE/GET endpoints for role management                                                 |
| RBAC-03 | Default roles (`admin`, `member`) are seeded via data migration on first deploy                                                | `0003_seed_roles.py` uses `RunPython` with `get_or_create` — runs automatically on `migrate`, no manual steps                                                              |

</phase_requirements>

---

## Summary

Phase 22 adds role-based access control using Django's built-in `Group` model as the role store. The primary deliverable is a `RequireRole` permission class that integrates naturally into the Ninja Extra permission system — the same `BasePermission` interface used by `IsAuthenticated`. No new infrastructure is required: the error handling pipeline (`PermissionDenied` → `permission_denied_handler` → HTTP 403 JSON) already exists in `config/urls.py`.

The `AdminController` is the second deliverable: a Ninja Extra controller gated at class level with `permissions=[IsAuthenticated, RequireRole("admin")]`. It follows the same `@api_controller` + `ControllerBase` pattern as `UserController` and `AccountController`. It adds user listing and role management endpoints. The existing `UserService` can be extended (or `AdminController` can have its own service) to handle role assignment logic.

The data migration (`0003_seed_roles.py`) is a standard Django `RunPython` migration that seeds `admin` and `member` Groups via `get_or_create`. It depends on `accounts/0001_initial` (the current latest) and must also depend on the auth app's latest migration since `auth.Group` is a separate app's model.

**Primary recommendation:** Implement `RequireRole` as a `BasePermission` subclass that takes the role name in `__init__`, checks `user.groups.filter(name=self.role).exists()`, and raises `PermissionDenied` on failure. Keep the service logic for role operations in `UserService` (or a thin `AdminService` that `UserService` does not need to know about).

## Standard Stack

### Core

| Library                                   | Version                 | Purpose                          | Why Standard                                                                                                                   |
| ----------------------------------------- | ----------------------- | -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `ninja_extra.permissions.BasePermission`  | installed (ninja-extra) | Base class for permission checks | The correct extension point for Ninja Extra — verified in `.venv/lib/python3.12/site-packages/ninja_extra/permissions/base.py` |
| `django.contrib.auth.models.Group`        | Django built-in         | Role store                       | Already part of the Django auth app; `User.groups` M2M already in the `users` table migration                                  |
| `django.core.exceptions.PermissionDenied` | Django built-in         | Signals a 403                    | Already caught by `permission_denied_handler` in `config/urls.py`                                                              |
| `django.db.migrations.RunPython`          | Django built-in         | Data migration                   | Standard mechanism for seeding data in migrations                                                                              |

### Supporting

| Library                                                  | Version   | Purpose               | When to Use                                                |
| -------------------------------------------------------- | --------- | --------------------- | ---------------------------------------------------------- |
| `ninja_extra.permissions.IsAuthenticated`                | installed | Unauthenticated guard | Always listed before `RequireRole` in the permissions list |
| `allauth.headless.contrib.ninja.security.jwt_token_auth` | installed | JWT auth scheme       | Same auth list as existing controllers                     |
| `ninja.security.SessionAuth`                             | installed | Session auth scheme   | Same auth list as existing controllers                     |

No new packages need to be installed.

## Architecture Patterns

### Recommended Project Structure

```
apps/api/apps/accounts/
├── permissions.py          # NEW — RequireRole class + KNOWN_ROLES constant
├── controllers.py          # MODIFIED — add AdminController (do NOT change UserController/AccountController)
├── services.py             # MODIFIED — add role assignment/removal methods to UserService (or new AdminService)
├── schemas.py              # MODIFIED — add RoleAssignIn, UserRoleOut, AdminUserOut schemas
└── migrations/
    └── 0003_seed_roles.py  # NEW — data migration seeding admin + member Groups
```

### Pattern 1: RequireRole Permission Class

**What:** A `BasePermission` subclass that accepts a role name at construction time and checks Django Group membership.

**When to use:** Apply at controller level to gate entire controllers; apply at individual route level to gate a single endpoint.

**Example:**

```python
# apps/accounts/permissions.py
# Source: verified against .venv/lib/python3.12/site-packages/ninja_extra/permissions/base.py

from django.core.exceptions import PermissionDenied
from django.http import HttpRequest
from ninja_extra import ControllerBase
from ninja_extra.permissions import BasePermission

KNOWN_ROLES: frozenset[str] = frozenset({"admin", "member"})


class RequireRole(BasePermission):
    """Gate access to users who are members of a specific Django Group.

    Usage:
        permissions=[IsAuthenticated, RequireRole("admin")]

    IsAuthenticated MUST be listed before RequireRole — RequireRole assumes
    request.user is authenticated. The IsAuthenticated check runs first
    because ninja-extra evaluates the permissions list left-to-right.
    """

    def __init__(self, role: str) -> None:
        self.role = role

    def has_permission(self, request: HttpRequest, controller: ControllerBase) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            raise PermissionDenied("Insufficient role.")
        if not user.groups.filter(name=self.role).exists():
            raise PermissionDenied("Insufficient role.")
        return True
```

**Important:** `BasePermission.has_permission()` is documented to return `bool`. Raising `PermissionDenied` inside `has_permission` is the established project pattern — confirmed by `billing/decorators.py` and the existing `permission_denied_handler` in `config/urls.py`. Ninja Extra propagates the exception without swallowing it.

### Pattern 2: AdminController

**What:** A `ControllerBase` subclass with controller-level `RequireRole` guard. Follows the exact same pattern as `UserController` and `AccountController`.

**When to use:** All admin-gated endpoints live in this controller.

**Example:**

```python
# apps/accounts/controllers.py (addition)
# Source: apps/api/apps/accounts/controllers.py (existing pattern)

from allauth.headless.contrib.ninja.security import jwt_token_auth
from ninja.security import SessionAuth
from ninja_extra import ControllerBase, api_controller, route
from ninja_extra.permissions import IsAuthenticated

from .permissions import KNOWN_ROLES, RequireRole
from .schemas import AdminUserOut, RoleAssignIn, UserRoleOut
from .services import UserService  # or AdminService


@api_controller(
    "/admin/users",
    tags=["Admin"],
    permissions=[IsAuthenticated, RequireRole("admin")],
    auth=[SessionAuth(), jwt_token_auth],
)
class AdminController(ControllerBase):
    def __init__(self):
        self.service = UserService()

    @route.get("", response=..., url_name="admin-user-list")
    def list_users(self, request, page: int = 1, page_size: int = 20):
        ...

    @route.get("/{user_id}/roles", response=UserRoleOut, url_name="admin-user-roles")
    def get_user_roles(self, request, user_id: int):
        ...

    @route.post("/{user_id}/roles", response={200: UserRoleOut, 400: dict}, url_name="admin-assign-role")
    def assign_role(self, request, user_id: int, payload: RoleAssignIn):
        ...

    @route.delete("/{user_id}/roles/{role}", response={200: UserRoleOut, 400: dict}, url_name="admin-remove-role")
    def remove_role(self, request, user_id: int, role: str):
        ...
```

### Pattern 3: Data Migration for Seeding Groups

**What:** A standard Django `RunPython` data migration. Uses `apps.get_model()` (historical reference) rather than direct model import.

**When to use:** Any time you need data seeded automatically on every fresh `migrate`.

**Example:**

```python
# apps/accounts/migrations/0003_seed_roles.py
# Source: Django data migration docs — apps.get_model is the correct pattern

from django.db import migrations


def seed_roles(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.get_or_create(name="admin")
    Group.objects.get_or_create(name="member")


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(seed_roles, migrations.RunPython.noop),
    ]
```

**Critical note on dependencies:** The migration must depend on BOTH `accounts/0001_initial` (to preserve ordering) AND `auth/0012_alter_user_first_name_max_length` (because it uses `auth.Group`). The `auth` migration is the same one that `accounts/0001_initial` already depends on — so this is safe and consistent.

### Anti-Patterns to Avoid

- **Importing `Group` directly at module level in the migration:** Use `apps.get_model("auth", "Group")` instead. Direct import bypasses Django's historical model resolution and will break if the model changes between migration states.
- **Raising `Http403` or returning `False` from `has_permission`:** The project pattern is to `raise PermissionDenied(message)` — this propagates through the existing `permission_denied_handler` which formats a consistent JSON error. Returning `False` in ninja-extra also works but produces a less informative response.
- **Putting `RequireRole` before `IsAuthenticated` in the permissions list:** If an unauthenticated request hits `RequireRole` first, `request.user` will be an `AnonymousUser` — the groups query will still fail correctly, but the error message will be wrong and the coupling is implicit. Always list `IsAuthenticated` first.
- **Using `user.has_perm()` instead of `user.groups.filter(name=role).exists()`:** `has_perm()` checks `Permission` objects, not `Group` membership. The decision in CONTEXT.md is to use `Group` directly.
- **Modifying `UserController` or `AccountController`:** `AdminController` is a new controller class added to `controllers.py`. It does not replace or extend existing controllers.

## Don't Hand-Roll

| Problem                              | Don't Build                                    | Use Instead                                                                                               | Why                                                                                              |
| ------------------------------------ | ---------------------------------------------- | --------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| Permission 403 formatting            | Custom JSON error response in permission class | `raise PermissionDenied` — caught by existing `permission_denied_handler`                                 | Already handles all 403s with consistent `{"error": {"code": "AUTH_005", ...}}` shape            |
| Group seeding in application startup | Signal or management command                   | Django data migration                                                                                     | Migrations run atomically on deploy; startup signals are unreliable and run on every worker boot |
| Role validation                      | Custom validator class                         | Module-level `KNOWN_ROLES` frozenset + inline check                                                       | Frozenset membership check is O(1) and trivially testable                                        |
| Pagination                           | Custom offset/limit logic                      | Follow whatever pattern exists in the codebase (no custom pagination framework was added in prior phases) | Consistent with existing API surface                                                             |

**Key insight:** Every component this phase needs already exists — `BasePermission`, `PermissionDenied`, `Group`, `RunPython`. This phase is configuration and composition, not new infrastructure.

## Common Pitfalls

### Pitfall 1: N+1 Query on User List with Groups

**What goes wrong:** `GET /api/v1/admin/users` returns users with their groups. If you iterate users and call `user.groups.all()` for each, you get one query per user.

**Why it happens:** Django's M2M does not prefetch by default. The global `_nplusone_guard` fixture in `tests/conftest.py` will catch this during tests.

**How to avoid:** Use `User.objects.prefetch_related("groups")` in the query. Tests will fail immediately if you miss this because of the nplusone autouse fixture.

**Warning signs:** Tests fail with `NPlusOneError` on the user list endpoint test.

### Pitfall 2: Migration Dependency on `auth` App

**What goes wrong:** Migration fails because `auth.Group` model is not available in the migration state if the `auth` dependency is missing.

**Why it happens:** `apps.get_model("auth", "Group")` only works if the migration's `dependencies` list includes a migration from the `auth` app.

**How to avoid:** Add `("auth", "0012_alter_user_first_name_max_length")` to the migration's `dependencies`. This is the same auth migration that `accounts/0001_initial` already depends on, so no circular dependency is introduced.

**Warning signs:** `LookupError: No installed app with label 'auth'` or `ValueError: Related model 'auth.Group' cannot be resolved` during `migrate`.

### Pitfall 3: RequireRole Not Receiving the Authenticated User

**What goes wrong:** `request.user` inside `has_permission` is `AnonymousUser` even for a logged-in user.

**Why it happens:** If `IsAuthenticated` is not in the permissions list (or auth schemes are misconfigured), ninja-extra does not populate `request.user` with the authenticated user.

**How to avoid:** Always use `permissions=[IsAuthenticated, RequireRole("admin")]` AND include `auth=[SessionAuth(), jwt_token_auth]` on the controller. Both together are required — the `auth=` list triggers authentication; the `permissions=` list runs the checks.

**Warning signs:** `PermissionDenied` raised for a user who does have the role; `request.user.is_authenticated` is `False` inside `has_permission`.

### Pitfall 4: Test Isolation — Groups Created in One Test Bleed Into Another

**What goes wrong:** A test that creates Groups directly (not via migration) can fail if another test expects Groups not to exist, or vice versa.

**Why it happens:** `@pytest.mark.django_db` wraps each test in a transaction that rolls back, but Groups created by migration are part of the schema — they persist across tests.

**How to avoid:** In tests that check role assignment, use `User.objects.create_user(...)` fresh per test and rely on `user.groups.add(Group.objects.get(name="admin"))` to set up role state. Do not assume Group rows do or do not exist from fixture state — they always exist after migration.

**Warning signs:** Tests pass individually but fail when run together (`pytest tests/accounts/`).

### Pitfall 5: `auto_discover_controllers()` Already Handles Registration

**What goes wrong:** Implementer adds `AdminController` to `config/urls.py` manually, creating a double-registration error.

**Why it happens:** `urls.py` calls `api.auto_discover_controllers()` which scans all installed apps' controller modules automatically.

**How to avoid:** Do NOT add `AdminController` to `urls.py`. Adding the class to `apps/accounts/controllers.py` is sufficient — `auto_discover_controllers()` will pick it up automatically. This matches how `UserController` and `AccountController` are registered.

**Warning signs:** `NinjaExtraAPI` raises a duplicate URL name error on startup.

## Code Examples

### Verified: IsAuthenticated pattern (existing code, confirmed from codebase)

```python
# Source: apps/api/apps/accounts/controllers.py (lines 24-29)
@api_controller(
    "/users",
    tags=["Users"],
    permissions=[IsAuthenticated],
    auth=[SessionAuth(), jwt_token_auth],
)
class UserController(ControllerBase):
    ...
```

### Verified: BasePermission signature (from ninja_extra source)

```python
# Source: .venv/lib/python3.12/site-packages/ninja_extra/permissions/base.py (lines 57-73)
class BasePermission(ABC, _OperationHolderMixin, metaclass=BasePermissionMetaclass):
    message: t.Any = None

    @abstractmethod
    def has_permission(
        self, request: HttpRequest, controller: "ControllerBase"
    ) -> bool:
        return True

    def has_object_permission(
        self, request: HttpRequest, controller: "ControllerBase", obj: t.Any
    ) -> bool:
        return True
```

### Verified: PermissionDenied handler (from config/urls.py)

```python
# Source: apps/api/config/urls.py (lines 118-125)
@api.exception_handler(PermissionDenied)
def permission_denied_handler(request, exc: PermissionDenied):
    return _error_response(
        request,
        code="AUTH_005",
        message="You do not have permission to perform this action.",
        status=403,
    )
```

Note: The handler uses a fixed message ("You do not have permission to perform this action.") regardless of `exc` content. The `exc` argument is `PermissionDenied("Insufficient role.")` from `RequireRole`, but the response body will always say "You do not have permission to perform this action." with code `AUTH_005`. This is the correct behavior — the CONTEXT.md success criteria says "HTTP 403 with a JSON error body — no stack trace, no 500", which is satisfied.

### Verified: RunPython data migration pattern

```python
# Source: Django migrations framework — apps.get_model is the documented historical reference pattern
def seed_roles(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.get_or_create(name="admin")
    Group.objects.get_or_create(name="member")
```

### Verified: Existing accounts migration dependency chain

```python
# Source: apps/api/apps/accounts/migrations/0001_initial.py (lines 13-15)
dependencies = [
    ('auth', '0012_alter_user_first_name_max_length'),
]
```

The `0003_seed_roles.py` migration MUST include this same `auth` dependency to reference `auth.Group`.

### Verified: Test client pattern for controller tests (from accounts conftest)

```python
# Source: apps/api/tests/accounts/conftest.py
# ninja_extra.testing.TestClient supports ControllerBase subclasses
# NinjaClientBase.force_login() is patched in — use it for auth in tests
from ninja.testing import TestClient  # patched to ninja_extra.testing.TestClient in conftest

client = TestClient(AdminController)
client.force_login(admin_user)
response = client.get("/")
```

## State of the Art

| Old Approach                         | Current Approach                                 | When Changed      | Impact                                                                        |
| ------------------------------------ | ------------------------------------------------ | ----------------- | ----------------------------------------------------------------------------- |
| Function decorator (`@require_role`) | Permission class (`RequireRole(BasePermission)`) | Phase 22 decision | Composes at controller level, cleaner than per-endpoint decoration            |
| Custom permission tables             | Django built-in `Group` model                    | Phase 22 decision | Zero extra dependencies, zero migration complexity, built-in admin UI support |

**Not applicable / not deprecated in this phase:** The `require_active_subscription` decorator in `billing/decorators.py` remains as-is. `RequireRole` is a separate, parallel mechanism that does not replace it.

## Open Questions

1. **Pagination implementation for `GET /api/v1/admin/users`**
   - What we know: No existing paginated endpoint exists in the codebase to reference
   - What's unclear: Whether to use simple `page`/`page_size` query params with a manual `User.objects.all()[offset:limit]` or whether to add a pagination helper
   - Recommendation: Use `page: int = 1, page_size: int = 20` query params with inline slicing. Keep it simple. The planner can decide whether to extract a reusable paginator class or leave it inline.

2. **`AdminService` vs extending `UserService`**
   - What we know: `UserService` currently handles only profile operations; it has no knowledge of Group membership
   - What's unclear: Whether role operations are close enough to "user management" to belong in `UserService`, or whether they warrant a separate `AdminService`
   - Recommendation: Add role management methods directly to `UserService` to avoid a new file. If the service grows unwieldy, the planner can split it into `AdminService`. Either choice is correct — this is marked as Claude's discretion in CONTEXT.md.

3. **`KNOWN_ROLES` placement**
   - What we know: CONTEXT.md marks this as Claude's discretion; must be accessible from both `permissions.py` (for `RequireRole`) and `controllers.py` (for validation in endpoints)
   - Recommendation: Module-level constant in `permissions.py` as `KNOWN_ROLES: frozenset[str] = frozenset({"admin", "member"})`. Import it into `controllers.py` and `services.py` as needed. Avoids Django settings coupling for what is a pure application-layer constant.

## Validation Architecture

### Test Framework

| Property           | Value                                                   |
| ------------------ | ------------------------------------------------------- |
| Framework          | pytest 8.0+ with pytest-django 4.9+                     |
| Config file        | `apps/api/pyproject.toml` (`[tool.pytest.ini_options]`) |
| Quick run command  | `cd apps/api && python -m pytest tests/accounts/ -x -q` |
| Full suite command | `cd apps/api && python -m pytest -x -q`                 |

### Phase Requirements → Test Map

| Req ID  | Behavior                                                   | Test Type   | Automated Command                                                                        | File Exists? |
| ------- | ---------------------------------------------------------- | ----------- | ---------------------------------------------------------------------------------------- | ------------ |
| RBAC-01 | `RequireRole("admin")` returns HTTP 403 for non-admin user | unit        | `cd apps/api && python -m pytest tests/accounts/test_rbac.py::TestRequireRole -x`        | ❌ Wave 0    |
| RBAC-01 | `RequireRole("admin")` allows admin user through           | unit        | `cd apps/api && python -m pytest tests/accounts/test_rbac.py::TestRequireRole -x`        | ❌ Wave 0    |
| RBAC-01 | `RequireRole` propagates `PermissionDenied`, not 500       | unit        | `cd apps/api && python -m pytest tests/accounts/test_rbac.py -x`                         | ❌ Wave 0    |
| RBAC-02 | `POST /admin/users/{id}/roles` — admin assigns role        | unit        | `cd apps/api && python -m pytest tests/accounts/test_rbac.py::TestAdminController -x`    | ❌ Wave 0    |
| RBAC-02 | `POST /admin/users/{id}/roles` — non-admin gets 403        | unit        | `cd apps/api && python -m pytest tests/accounts/test_rbac.py::TestAdminController -x`    | ❌ Wave 0    |
| RBAC-02 | `DELETE /admin/users/{id}/roles/{role}` — removes role     | unit        | `cd apps/api && python -m pytest tests/accounts/test_rbac.py::TestAdminController -x`    | ❌ Wave 0    |
| RBAC-02 | Self-modification blocked — 400                            | unit        | `cd apps/api && python -m pytest tests/accounts/test_rbac.py::TestAdminController -x`    | ❌ Wave 0    |
| RBAC-02 | Unknown role — 400                                         | unit        | `cd apps/api && python -m pytest tests/accounts/test_rbac.py::TestAdminController -x`    | ❌ Wave 0    |
| RBAC-03 | Migration seeds `admin` and `member` groups                | integration | `cd apps/api && python -m pytest tests/accounts/test_rbac.py::TestSeedRolesMigration -x` | ❌ Wave 0    |
| RBAC-03 | Migration is idempotent (re-runnable)                      | integration | `cd apps/api && python -m pytest tests/accounts/test_rbac.py::TestSeedRolesMigration -x` | ❌ Wave 0    |

### Sampling Rate

- **Per task commit:** `cd apps/api && python -m pytest tests/accounts/ -x -q`
- **Per wave merge:** `cd apps/api && python -m pytest -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/accounts/test_rbac.py` — RED test stubs covering all RBAC-01, RBAC-02, RBAC-03 behaviors above
- [ ] `tests/accounts/conftest.py` — already exists; may need `admin_user` and `member_user` fixtures added

_(No new framework install required — pytest + pytest-django already installed)_

## Sources

### Primary (HIGH confidence)

- Codebase read: `apps/api/apps/accounts/controllers.py` — existing controller patterns (`UserController`, `AccountController`, `AppleSignInController`)
- Codebase read: `apps/api/apps/billing/decorators.py` — `require_active_subscription` as reference for `PermissionDenied` raise pattern
- Codebase read: `apps/api/config/urls.py` — `permission_denied_handler` and `auto_discover_controllers()` confirmed
- Codebase read: `apps/api/apps/accounts/migrations/0001_initial.py` — confirmed `auth/0012` dependency, confirmed `User.groups` M2M already exists
- Codebase read: `apps/api/apps/accounts/services.py` — `UserService` pattern confirmed
- Codebase read: `.venv/.../ninja_extra/permissions/base.py` — `BasePermission.has_permission(request, controller) -> bool` signature confirmed
- Codebase read: `.venv/.../ninja_extra/permissions/common.py` — `IsAuthenticated` implementation confirmed; `request.user or request.auth` pattern
- Codebase read: `apps/api/tests/conftest.py` — `_nplusone_guard` autouse fixture confirmed; `user` fixture available
- Codebase read: `apps/api/tests/accounts/conftest.py` — `force_login` patch pattern confirmed for controller tests
- Codebase read: `apps/api/pyproject.toml` — pytest configuration and test paths confirmed

### Secondary (MEDIUM confidence)

- Django documentation (training knowledge, corroborated by codebase): `RunPython` data migrations use `apps.get_model()` for historical model references; `get_or_create` for idempotency

### Tertiary (LOW confidence)

None — all critical claims are verified directly from the installed codebase.

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — all libraries verified from installed `.venv` source
- Architecture: HIGH — patterns extracted directly from existing controllers and services
- Pitfalls: HIGH — N+1 guard confirmed from `tests/conftest.py`; migration dependency confirmed from `0001_initial.py`; auto-discovery confirmed from `config/urls.py`

**Research date:** 2026-03-12
**Valid until:** 2026-06-12 (stable Django/ninja-extra APIs; 90 days)
