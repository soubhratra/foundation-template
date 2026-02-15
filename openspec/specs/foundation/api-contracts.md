# API Contracts Specification

> Baseline specification for the Foundation Template.
> This document is the source of truth. All implementations must conform to these specs.

## Overview

The API contract layer is the central integration point of the Foundation Template. Django Ninja Extra generates an OpenAPI 3.1 specification from Pydantic schemas. This spec is the single source of truth for all API contracts. TypeScript types are auto-generated from this spec, and a type-safe HTTP client (openapi-fetch) consumes those types. The pipeline is enforced in CI: if generated types drift from the Django API, the build fails.

## Specifications

### Type Generation Pipeline

```
+-------------------+     +------------------+     +-------------------+
| Django Ninja Extra|     | OpenAPI 3.1 JSON |     | TypeScript Types  |
| Pydantic Schemas  +---->+ Specification    +---->+ (types.d.ts)      |
| + Controllers     |     | (openapi.json)   |     |                   |
+-------------------+     +------------------+     +-------------------+
        |                         |                         |
   Python source            Committed to repo         Generated file
   (apps/api/)              (packages/api-client/)    (packages/api-client/)
                                  |                         |
                                  v                         v
                          +------------------+     +-------------------+
                          | CI Gate:         |     | openapi-fetch     |
                          | Fail if spec     |     | Client Instance   |
                          | differs from     |     | (client.ts)       |
                          | committed copy   |     +-------------------+
                          +------------------+
```

#### Step 1: Pydantic Schemas Define the Contract

```python
# apps/api/apps/accounts/schemas.py
from pydantic import BaseModel, EmailStr, Field

class UserOut(BaseModel):
    id: int
    email: EmailStr
    first_name: str
    last_name: str
    is_active: bool
    created_at: str  # ISO 8601

class UserCreateIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    first_name: str = Field(max_length=150)
    last_name: str = Field(max_length=150)

class UserUpdateIn(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
```

#### Step 2: Controllers Expose Endpoints

```python
# apps/api/apps/accounts/controllers.py
from ninja_extra import api_controller, route
from ninja_extra.permissions import IsAuthenticated
from .schemas import UserOut, UserCreateIn, UserUpdateIn
from .services import UserService

@api_controller("/users", tags=["Users"])
class UserController:
    def __init__(self):
        self.service = UserService()

    @route.get("/me", response=UserOut, permissions=[IsAuthenticated])
    def get_current_user(self, request):
        return self.service.get_user(request.user.id)

    @route.patch("/me", response=UserOut, permissions=[IsAuthenticated])
    def update_current_user(self, request, payload: UserUpdateIn):
        return self.service.update_user(request.user.id, payload)
```

#### Step 3: Export OpenAPI Spec

```bash
# Management command exports spec to packages/api-client/
python manage.py export_openapi_schema > ../../packages/api-client/openapi.json
```

The `openapi.json` file is committed to version control. This allows frontend development without a running Django server.

#### Step 4: Generate TypeScript Types

```bash
# In packages/api-client/package.json scripts:
"generate:types": "openapi-typescript ./openapi.json -o ./src/types.d.ts"
```

Run via Turborepo:
```bash
turbo generate:api-types
```

#### Step 5: Type-Safe Client

```typescript
// packages/api-client/src/client.ts
import createClient from "openapi-fetch";
import type { paths } from "./types.d.ts";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const apiClient = createClient<paths>({
  baseUrl: `${API_BASE_URL}/api/v1`,
});
```

#### Step 6: Consumption in Apps

```typescript
// apps/web/app/(dashboard)/page.tsx
import { apiClient } from "@repo/api-client";

async function DashboardPage() {
  const { data, error } = await apiClient.GET("/users/me");
  // data is fully typed as UserOut
  // error is fully typed as ErrorOut
  if (error) return <ErrorDisplay error={error} />;
  return <Dashboard user={data} />;
}
```

### Pipeline Execution

| Trigger | Command | What Happens |
|---------|---------|-------------|
| Developer changes API | `turbo generate:api-types` | Exports spec, regenerates types, developer commits both |
| CI pipeline | `turbo generate:api-types && git diff --exit-code` | Regenerates and fails if output differs from committed files |
| Development server | Manual trigger only | Types are NOT regenerated on dev server start |

**GIVEN** a developer modifies a Pydantic schema in apps/api/
**WHEN** they run `turbo generate:api-types`
**THEN** openapi.json and types.d.ts are regenerated
**AND** TypeScript compilation in apps/web/ and apps/mobile/ catches any type mismatches

**GIVEN** a developer pushes a PR that changes a Pydantic schema
**WHEN** the CI pipeline runs
**THEN** CI regenerates types from the running Django spec
**AND** CI compares output against committed types.d.ts
**AND** CI fails if they differ (forces developer to regenerate before merge)

### Request/Response Patterns

#### Successful Response

```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "is_active": true,
  "created_at": "2026-01-15T10:30:00Z"
}
```

Direct Pydantic schema serialization. No wrapper envelope for single-resource responses.

#### Paginated Response

```python
# apps/api/apps/core/schemas.py
from pydantic import BaseModel
from typing import Generic, TypeVar

T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    offset: int
    limit: int
```

```json
{
  "items": [
    { "id": 1, "email": "user@example.com", ... },
    { "id": 2, "email": "other@example.com", ... }
  ],
  "total": 42,
  "offset": 0,
  "limit": 20
}
```

**Pagination uses offset/limit (not page-based).** This aligns with Django ORM's native slice syntax (`qs[offset:offset+limit]`) and avoids computing page numbers.

**GIVEN** a client requests a list endpoint with `?offset=20&limit=10`
**WHEN** the API processes the request
**THEN** the response contains `items` (array of resources), `total` (total count), `offset`, `limit`
**AND** `items` length is at most `limit`
**AND** `limit` is capped at 100 by the service layer

#### Standardized Error Response

```python
# apps/api/apps/core/schemas.py
class ErrorOut(BaseModel):
    detail: str
    code: str | None = None
    errors: list[FieldError] | None = None

class FieldError(BaseModel):
    field: str
    message: str
```

**HTTP Status Code Mapping:**

| Status | Usage | Example code |
|--------|-------|-------------|
| 200 | Success (GET, PATCH) | -- |
| 201 | Resource created (POST) | -- |
| 204 | No content (DELETE) | -- |
| 400 | Validation error | `validation_error` |
| 401 | Not authenticated | `not_authenticated` |
| 403 | Permission denied | `permission_denied` |
| 404 | Resource not found | `not_found` |
| 409 | Conflict (duplicate) | `already_exists` |
| 422 | Unprocessable entity | `unprocessable` |
| 500 | Server error | `internal_error` |

**GIVEN** a client sends invalid data to a POST endpoint
**WHEN** Pydantic validation fails
**THEN** the API returns 400 with body:
```json
{
  "detail": "Validation failed",
  "code": "validation_error",
  "errors": [
    { "field": "email", "message": "Invalid email address" },
    { "field": "password", "message": "Must be at least 8 characters" }
  ]
}
```

**GIVEN** a client requests a resource that does not exist
**WHEN** the service raises a NotFound exception
**THEN** the API returns 404 with body:
```json
{
  "detail": "User not found",
  "code": "not_found"
}
```

### API Versioning Strategy

| Aspect | Decision |
|--------|----------|
| Versioning scheme | URL prefix: `/api/v1/` |
| When to increment | Breaking changes only (removed fields, changed types, removed endpoints) |
| Backward compatibility | Non-breaking changes (new fields, new endpoints) do NOT require a version bump |
| Multiple versions | Support at most 2 concurrent versions. Deprecate old version with sunset header. |

```python
# config/urls.py
from ninja_extra import NinjaExtraAPI

api_v1 = NinjaExtraAPI(
    title="Foundation API",
    version="1.0.0",
    urls_namespace="api_v1",
)
api_v1.auto_discover_controllers()

urlpatterns = [
    path("api/v1/", api_v1.urls),
]
```

### CORS Configuration

```python
# config/settings/base.py
INSTALLED_APPS = [
    "corsheaders",
    # ...
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # Must be before CommonMiddleware
    "django.middleware.common.CommonMiddleware",
    # ...
]

# config/settings/development.py
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # Next.js dev server
]
CORS_ALLOW_CREDENTIALS = True  # Required for session cookies

# config/settings/production.py
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS")
CORS_ALLOW_CREDENTIALS = True
```

**GIVEN** a Next.js client on `localhost:3000` makes a request to Django on `localhost:8000`
**WHEN** the browser sends a preflight OPTIONS request
**THEN** Django responds with `Access-Control-Allow-Origin: http://localhost:3000`
**AND** `Access-Control-Allow-Credentials: true`
**AND** the actual request proceeds

**Rules:**
- Never set `CORS_ALLOW_ALL_ORIGINS = True` in any environment.
- Always use explicit origin list.
- `CORS_ALLOW_CREDENTIALS = True` is required for session cookie auth.

### Nullable/Optional Field Convention

| Python Type | OpenAPI | TypeScript | Usage |
|-------------|---------|------------|-------|
| `str` | `string` (required) | `string` | Always present, never null |
| `str \| None` | `string` (nullable) | `string \| null` | May be null |
| `str \| None = None` | `string` (nullable, optional) | `string \| null \| undefined` | May be null, may be omitted |

**Rule:** Use `str | None` (not `Optional[str]`) for clarity. The `|` syntax makes nullable explicit.

### Health Check Endpoint

```python
@api_controller("/health", tags=["Health"])
class HealthController:
    @route.get("/", response={200: dict})
    def health_check(self, request):
        from django.db import connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return {"status": "healthy", "database": "connected"}
        except Exception:
            return {"status": "unhealthy", "database": "disconnected"}
```

Available at `/api/v1/health/`. Returns 200 with database connectivity status.

## Constraints

1. **Pydantic schemas are the single source of truth.** All API types originate from Python Pydantic schemas. TypeScript types are always generated, never manually written.
2. **openapi.json is committed.** Frontend developers can work without a running Django server. CI verifies freshness.
3. **No manual TypeScript type definitions for API types.** If a type exists in the OpenAPI spec, use the generated type. Creating manual types causes drift.
4. **codegen tool version is pinned.** openapi-typescript version pinned in packages/api-client/package.json. Never use `latest`.
5. **Error responses follow ErrorOut schema.** All error responses from the API conform to the ErrorOut Pydantic schema. No ad-hoc error formats.
6. **CORS is explicit.** No wildcard origins. Environment-variable-driven origin list.
7. **API version in URL.** All endpoints under `/api/v1/`. No versionless endpoints except health check.

## References

- `.planning/research/STACK.md` -- openapi-typescript + openapi-fetch configuration
- `.planning/research/ARCHITECTURE.md` -- OpenAPI pipeline diagram, BFF proxy pattern
- `.planning/research/PITFALLS.md` -- Pipeline fragility pitfalls (schema drift, nullable confusion)
