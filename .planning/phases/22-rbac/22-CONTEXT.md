# Phase 22: RBAC - Context

**Gathered:** 2026-03-12
**Status:** Ready for planning

<domain>
## Phase Boundary

Add role-based access control to the template: a `RequireRole` Ninja Extra permission class, an `AdminController` with role assignment + user listing endpoints, and a data migration that seeds `admin` and `member` Django Groups on every fresh deploy.

No UI for role management, no role inheritance, no custom permission scopes — those are future phases.

</domain>

<decisions>
## Implementation Decisions

### Decorator integration style

- `RequireRole("admin")` is a **Ninja Extra permission class** (`BasePermission`), not a function decorator
- Applied via `permissions=[IsAuthenticated, RequireRole("admin")]` on controllers or routes — idiomatic to ninja-extra, composes cleanly, and can gate an entire controller at once
- Backing store: Django's built-in `Group` model — `user.groups.filter(name=role).exists()`
- `IsAuthenticated` is always listed explicitly alongside `RequireRole` — no hidden coupling
- When role check fails: raises `PermissionDenied("Insufficient role.")` → existing `permission_denied_handler` in `config/urls.py` formats it as HTTP 403 with JSON body `{"detail": "Insufficient role."}` — no stack trace, no 500

### Role assignment API shape

- `POST /api/v1/admin/users/{user_id}/roles` — body `{"role": "admin" | "member"}` — assigns role (idempotent: 200 always, even if already assigned)
- `DELETE /api/v1/admin/users/{user_id}/roles/{role}` — removes role (idempotent: 200 if not assigned)
- `GET /api/v1/admin/users/{user_id}/roles` — returns current role list for the user
- Unknown role names → 400 Bad Request; only `"admin"` and `"member"` are valid (validated against a `KNOWN_ROLES` constant)
- Self-modification blocked → 400 `{"detail": "Cannot modify your own roles."}` — prevents accidental admin lockout

### Code placement

- All RBAC code lives in `apps/accounts/`:
  - `apps/accounts/permissions.py` — `RequireRole` permission class
  - `apps/accounts/controllers.py` — add `AdminController` (new controller, does not modify `UserController`)
  - `apps/accounts/migrations/0003_seed_roles.py` — data migration for `admin`/`member` groups
- `AdminController` is at prefix `/admin/users` and is gated at the controller level with `permissions=[IsAuthenticated, RequireRole("admin")]`

### AdminController endpoints

The `AdminController` has three endpoints (keeping Phase 22 scope tight):

1. `GET /api/v1/admin/users` — paginated list of all users (fields: `id`, `email`, `first_name`, `last_name`, `groups`, `date_joined`) — makes role management actually usable without knowing user IDs upfront
2. `GET /api/v1/admin/users/{user_id}/roles` — current roles for a specific user
3. `POST /api/v1/admin/users/{user_id}/roles` — assign role
4. `DELETE /api/v1/admin/users/{user_id}/roles/{role}` — remove role

### Data migration

- `accounts/migrations/0003_seed_roles.py` — Django data migration using `RunPython`
- Uses `apps.get_model("auth", "Group")` (historical model reference — safe in migrations)
- `get_or_create(name="admin")` and `get_or_create(name="member")` — idempotent, safe to re-run
- Reverse migration is a no-op (`migrations.RunPython.noop`) — groups are not deleted on rollback to avoid breaking existing role assignments

### Scaffolder

- RBAC is **core infrastructure** — no `--without rbac` flag
- No external service dependencies, no billing complexity — always available; `RequireRole` is a utility that does nothing unless used

### Claude's Discretion

- Exact pagination style for `GET /api/v1/admin/users` (page + page_size query params or cursor — follow existing patterns in codebase if any)
- Whether `AdminController` gets its own `services.py` or uses `UserService` directly
- Exact `KNOWN_ROLES` placement (module-level constant in `permissions.py` or `settings.py`)

</decisions>

<specifics>
## Specific Ideas

- The `RequireRole` class is the RBAC equivalent of `@require_active_subscription` from billing — same philosophy (raise `PermissionDenied`, let `permission_denied_handler` format it), different integration style (permission class vs function decorator)
- `AdminController` prefix `/admin/users` (not `/users`) cleanly separates admin operations from self-service user endpoints in `UserController`
- Data migration reverse is intentionally a no-op — dropping groups on rollback would break existing user role assignments in production

</specifics>

<code_context>

## Existing Code Insights

### Reusable Assets

- `apps/billing/decorators.py` (`require_active_subscription`): Reference implementation for `PermissionDenied` + `permission_denied_handler` pattern — `RequireRole` follows same error flow but as a permission class
- `apps/accounts/controllers.py` (`UserController`, `AccountController`): Existing controller structure — `AdminController` follows same `@api_controller` + `ControllerBase` pattern
- `ninja_extra.permissions.IsAuthenticated`: Already used in existing controllers — compose with `RequireRole` using `permissions=[IsAuthenticated, RequireRole("admin")]`
- `apps/accounts/migrations/0001_initial.py`: Reference for migration dependency chain — `0003_seed_roles.py` depends on latest accounts migration

### Established Patterns

- Controller-level permissions: `@api_controller(..., permissions=[IsAuthenticated])` — apply `RequireRole` at same level
- Service layer: `UserService` in `apps/accounts/services.py` — role assignment logic lives in a service, not inline in the controller
- HTTP 403 via `PermissionDenied`: `config/urls.py` has `permission_denied_handler` — raises `PermissionDenied` already handled globally

### Integration Points

- `apps/accounts/controllers.py`: Add new `AdminController` class (do not modify `UserController`)
- `apps/accounts/permissions.py`: New file for `RequireRole`
- `apps/accounts/migrations/`: Add `0003_seed_roles.py` data migration
- `config/urls.py`: Register `AdminController` alongside existing controllers (if not using auto-registration)

</code_context>

<deferred>
## Deferred Ideas

- Web/mobile UI for role management — future admin dashboard phase
- Role inheritance (e.g., admin implicitly has member permissions) — future phase
- Custom permission scopes (fine-grained object-level permissions) — future phase
- Audit log for role changes (who assigned what, when) — future phase

</deferred>

---

_Phase: 22-rbac_
_Context gathered: 2026-03-12_
