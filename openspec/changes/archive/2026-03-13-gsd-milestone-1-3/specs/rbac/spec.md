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
