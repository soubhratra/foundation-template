# Role-Based Access Control (RBAC)

> Defines the three-tier role system (`owner`, `admin`, `member`) using Django Groups, plus `RequireRole` permission class and `AdminController` for role management endpoints.

## Overview

RBAC in the template is intentionally minimal: three roles seeded as Django Groups via a data migration, a `RequireRole` Ninja Extra permission class, and an `AdminController` that gates role-management endpoints. There is no custom Role model — Django's built-in `Group` is sufficient and avoids an extra JOIN on every permission check.

`RequireRole.has_permission()` returns `False` (not raises `PermissionDenied`) — this is the idiomatic Ninja Extra pattern; the framework converts `False` to `HttpError(403)`. This is the most common mistake when porting DRF permissions to Ninja.

**Note:** This spec covers application-level RBAC (user roles within a single product). For org-level membership roles (`org_owner`, `org_admin`, `org_member`), see `openspec/specs/organization-model/spec.md`.

## Requirements

### Requirement: UserRole Model with Seeded Roles

The system SHALL define roles as Django Groups (`owner`, `admin`, `member`) seeded via a data migration, with users assigned to exactly one role group.

#### Scenario: Roles are seeded idempotently

- **WHEN** `apps/accounts/migrations/migration_0003_seed_roles.py` runs
- **THEN** three Django Groups SHALL be created: `"owner"`, `"admin"`, `"member"`
- **AND** running the migration twice SHALL NOT raise an IntegrityError (uses `get_or_create`)

#### Scenario: Role assignment via group membership

- **WHEN** a user is assigned the `admin` role
- **THEN** the user SHALL be added to the `"admin"` Django Group
- **AND** the user's role SHALL be determinable via `user.groups.filter(name="admin").exists()`

### Requirement: RequireRole Permission Class

The system SHALL provide a `RequireRole` permission class for Django Ninja Extra that enforces role-based access on API endpoints.

#### Scenario: Admin user passes RequireRole("admin")

- **WHEN** a user in the `"admin"` group calls an endpoint decorated with `RequireRole("admin")`
- **THEN** the endpoint SHALL return the expected response

#### Scenario: Non-admin user blocked by RequireRole("admin")

- **WHEN** a user NOT in the `"admin"` group calls an endpoint decorated with `RequireRole("admin")`
- **THEN** the system SHALL return `403 Forbidden`

#### Scenario: Unauthenticated request blocked by RequireRole

- **WHEN** an unauthenticated request reaches an endpoint decorated with `RequireRole`
- **THEN** the system SHALL return `403 Forbidden`

#### Scenario: RequireRole returns False from has_permission

- **WHEN** the permission check fails
- **THEN** `RequireRole.has_permission()` SHALL return `False` (not raise `PermissionDenied`)
- **AND** Django Ninja Extra SHALL convert `False` to `HttpError(403)` via its `permission_denied()` handler

### Requirement: AdminController for Role Management

The system SHALL provide an `AdminController` in `apps/accounts/controllers.py` that exposes role management endpoints gated by `RequireRole("admin")`.

#### Scenario: Admin can list users with their roles

- **WHEN** an admin calls `GET /api/v1/admin/users`
- **THEN** the response SHALL include a list of users with their assigned role

#### Scenario: Admin can assign a role to a user

- **WHEN** an admin calls `PATCH /api/v1/admin/users/{user_id}/role` with a valid role name
- **THEN** the user's group membership SHALL be updated
- **AND** the response SHALL confirm the new role

#### Scenario: Non-admin access to admin endpoints is blocked

- **WHEN** a non-admin user calls any `AdminController` endpoint
- **THEN** the system SHALL return `403 Forbidden`

### Requirement: Frontend Role-Aware Hooks (Product Pattern)

Products scaffolded from this template SHOULD implement a `useRole()` hook that returns the current user's role for conditional rendering. This hook is not shipped in the template itself — it is a prescribed pattern for product teams to implement against the `GET /api/v1/admin/users` or user profile endpoint.

#### Scenario: useRole returns current user role

- **WHEN** `useRole()` is called in a React component
- **THEN** it SHALL return the user's role string (`"owner"`, `"admin"`, or `"member"`)
- **AND** components SHALL use this to conditionally render admin-only UI elements

## Known Issues / Tech Debt

**1. AdminController missing explicit `auth=` parameter** (Phase 22 — non-critical)

`AdminController` in `apps/api/apps/accounts/controllers.py` has no `auth=[SessionAuth(), jwt_token_auth]` parameter. Access control relies on Django middleware for JWT parsing and `RequireRole` for authorization. This is deliberate (avoiding a double-auth pattern in tests) but departs from the `[SessionAuth(), jwt_token_auth]` pattern used on `UserController` and `AccountController`.

_Recommendation:_ Add `auth=[SessionAuth(), jwt_token_auth]` to `AdminController` for defense-in-depth. Adjust tests to use `force_login()` helper rather than relying on the absence of ninja auth to pass 401 checks.

## Implementation Decisions

### Why `RequireRole.has_permission()` returns `False` (not raises `PermissionDenied`)

Django Ninja Extra's permission system calls `has_permission()` and converts a `False` return to `HttpError(403)` via its internal `permission_denied()` handler. If `has_permission()` raises `PermissionDenied` instead, Ninja Extra's exception handler catches it differently and the response format may diverge from the standard Ninja error schema. Returning `False` is the idiomatic Ninja Extra approach.

**Important:** This differs from Django REST Framework's permission pattern (where raising `PermissionDenied` is common). Do not port DRF permission classes to Ninja without checking the return-vs-raise contract.

### Why Django Groups (not a custom Role model)

Django's built-in `Group` model is an established, well-understood pattern with direct ORM query support (`user.groups.filter(name=...).exists()`). A custom Role model adds a join and an additional migration without meaningfully increasing flexibility for the template's use case. Products with complex permission matrices (per-object permissions, hierarchical roles) should reach for `django-guardian` — but that is explicitly out of scope for the template.

### Why seed roles via data migration (not `post_migrate` signal or fixture)

Data migrations run deterministically in migration order, making them repeatable on both fresh installs and existing databases. Fixtures require explicit loading (`manage.py loaddata`), which is easy to forget. `post_migrate` signals can fire multiple times (once per app) and require more boilerplate to handle idempotency. `get_or_create` in the migration guarantees idempotency with no extra code.

**Migration filename note (tech debt):** The seed migration was named `migration_0003_seed_roles.py` instead of the conventional `0003_seed_roles.py`. Django discovers and runs it correctly (the loader does not filter on the `m` prefix), but the registered migration name (`migration_0003_seed_roles`) deviates from convention. A future rename to `0003_seed_roles.py` is safe in Django (no-op data migration rename) and recommended for clarity.

### Why `AdminController` has no `auth=` parameter (and why this is tech debt)

`AdminController` was implemented without `auth=[SessionAuth(), jwt_token_auth]` because the combination of Ninja's permission system and Django middleware was sufficient for functional correctness in tests. However, this departs from the `[SessionAuth(), jwt_token_auth]` pattern used on `UserController` and `AccountController`, which provides defense-in-depth (Ninja rejects the request before it reaches the permission class).

**Current behaviour:** Authentication relies on Django middleware for session/JWT parsing; `RequireRole` handles authorization. Unauthenticated requests still return 403 (not 401) because `RequireRole` sees an anonymous user and returns `False`. This is functional but violates the principle of least surprise.

**Recommended fix:** Add `auth=[SessionAuth(), jwt_token_auth]` to `AdminController`. Update tests that relied on the absence of Ninja auth to pass 401 checks to use `force_login()` instead.
