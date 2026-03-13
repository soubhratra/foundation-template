## ADDED Requirements

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
