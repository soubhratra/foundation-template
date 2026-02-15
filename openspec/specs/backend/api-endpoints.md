# API Endpoint Patterns (Django Ninja Extra)

> Baseline specification for the Foundation Template.
> This document is the source of truth. All implementations must conform to these specs.

## Overview

The Foundation Template API is built with Django Ninja Extra, which provides class-based controllers with decorators for routing, authentication, and input validation. All business logic is separated into service classes. Request/response contracts are defined as Pydantic schemas. The API auto-generates an OpenAPI 3.x specification consumed by the TypeScript type generation pipeline.

## Specifications

### 1. Controller Pattern

Controllers are the HTTP boundary layer. They use the `@api_controller` decorator to define a URL prefix and metadata. Each method maps to one HTTP endpoint.

```python
from ninja_extra import api_controller, route, ControllerBase
from ninja_extra.permissions import IsAuthenticated

from .schemas import ItemOut, ItemCreateIn, ItemUpdateIn, ItemListOut
from .services import ItemService


@api_controller("/items", tags=["Items"], permissions=[IsAuthenticated])
class ItemController(ControllerBase):
    """CRUD controller for items."""

    def __init__(self):
        self.service = ItemService()

    @route.post("", response={201: ItemOut}, url_name="item-create")
    def create_item(self, request, payload: ItemCreateIn):
        """Create a new item."""
        return 201, self.service.create_item(user=request.user, data=payload)

    @route.get("", response=ItemListOut, url_name="item-list")
    def list_items(self, request, offset: int = 0, limit: int = 20):
        """List items for the authenticated user."""
        return self.service.list_items(user=request.user, offset=offset, limit=limit)

    @route.get("/{item_id}", response=ItemOut, url_name="item-detail")
    def get_item(self, request, item_id: int):
        """Get a single item by ID."""
        return self.service.get_item(user=request.user, item_id=item_id)

    @route.patch("/{item_id}", response=ItemOut, url_name="item-update")
    def update_item(self, request, item_id: int, payload: ItemUpdateIn):
        """Update an item with partial data."""
        return self.service.update_item(
            user=request.user, item_id=item_id, data=payload
        )

    @route.delete("/{item_id}", response={204: None}, url_name="item-delete")
    def delete_item(self, request, item_id: int):
        """Delete an item."""
        self.service.delete_item(user=request.user, item_id=item_id)
        return 204, None
```

**Controller rules:**

| Rule | Description |
|------|-------------|
| Thin controllers | Controllers validate input (via schemas), check permissions (via decorators), and delegate to services. No ORM queries. No complex logic. |
| One service per controller | Each controller instantiates one primary service in `__init__`. |
| `ControllerBase` inheritance | All controllers inherit from `ControllerBase` for Django Ninja Extra features. |
| Auto-discovery | Controllers are auto-discovered by `api.auto_discover_controllers()` in `config/urls.py`. |
| Tags | Every controller declares `tags=["TagName"]` for OpenAPI grouping. |
| URL naming | Every route declares `url_name` for reverse URL resolution in tests. |

### 2. Service Layer Pattern

Services contain all business logic. They are plain Python classes with no HTTP awareness.

```python
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from .models import Item
from .schemas import ItemCreateIn, ItemUpdateIn

User = get_user_model()


class ItemService:
    def create_item(self, user: User, data: ItemCreateIn) -> Item:
        return Item.objects.create(owner=user, **data.dict())

    def list_items(self, user: User, offset: int = 0, limit: int = 20) -> dict:
        qs = Item.objects.filter(owner=user).order_by("-created_at")
        total = qs.count()
        items = list(qs[offset : offset + limit])
        return {
            "items": items,
            "total": total,
            "offset": offset,
            "limit": limit,
        }

    def get_item(self, user: User, item_id: int) -> Item:
        return get_object_or_404(Item, id=item_id, owner=user)

    def update_item(self, user: User, item_id: int, data: ItemUpdateIn) -> Item:
        item = get_object_or_404(Item, id=item_id, owner=user)
        for field, value in data.dict(exclude_unset=True).items():
            setattr(item, field, value)
        item.save()
        return item

    def delete_item(self, user: User, item_id: int) -> None:
        item = get_object_or_404(Item, id=item_id, owner=user)
        item.delete()
```

**Service rules:**

| Rule | Description |
|------|-------------|
| No `request` object | Services never receive the HTTP `request`. They receive typed parameters (user, data, IDs). |
| ORM access | Services access the database via Django ORM. They are the query layer. |
| Use `select_related` / `prefetch_related` | All querysets backing list endpoints must declare explicit joins to prevent N+1 queries. |
| Return model instances or dicts | Services return Django model instances (serialized by schemas) or plain dicts for aggregate responses. |
| Raise `django.http.Http404` or custom exceptions | Services raise exceptions that controllers or exception handlers translate to HTTP responses. |

### 3. Schema Pattern

Schemas are Pydantic models that define request input validation and response serialization. They live in each app's `schemas.py`.

```python
from ninja import Schema, ModelSchema, Field
from typing import Optional
from datetime import datetime

from .models import Item


# --- Input Schemas (request body) ---

class ItemCreateIn(Schema):
    """Input schema for creating an item."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)


class ItemUpdateIn(Schema):
    """Input schema for updating an item (partial)."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)


# --- Output Schemas (response body) ---

class ItemOut(ModelSchema):
    """Output schema for a single item."""
    class Meta:
        model = Item
        fields = ["id", "title", "description", "created_at", "updated_at"]


class ItemListOut(Schema):
    """Output schema for a paginated list of items."""
    items: list[ItemOut]
    total: int
    offset: int
    limit: int


# --- Shared Error Schemas (in apps/core/schemas.py) ---

class ErrorOut(Schema):
    """Standard error response."""
    detail: str


class ValidationErrorOut(Schema):
    """Validation error response with field-level details."""
    detail: list[dict]
```

**Schema conventions:**

| Convention | Description |
|------------|-------------|
| `*In` suffix | Input schemas (request bodies). |
| `*Out` suffix | Output schemas (response bodies). |
| `*ListOut` suffix | Paginated list response schemas. |
| `ModelSchema` for output | Use `ModelSchema` with explicit `fields` for output to avoid exposing unintended model fields. |
| `Schema` for input | Use plain `Schema` for input to decouple request shape from model shape. |
| `Field(...)` for required | Use `Field(...)` with validation constraints (`min_length`, `max_length`, `ge`, `le`). |
| `Optional` for partial updates | Update schemas use `Optional` fields. `exclude_unset=True` on `.dict()` distinguishes "not sent" from "sent as null". |

### 4. Authentication and Permissions

Authentication uses Django Allauth in headless mode. Permissions are applied at the controller or route level.

```python
from ninja_extra import api_controller, route
from ninja_extra.permissions import IsAuthenticated, AllowAny


# Controller-level permission (applies to all routes)
@api_controller("/items", tags=["Items"], permissions=[IsAuthenticated])
class ItemController:
    ...

    # Route-level override (public access)
    @route.get("/public", response=list[ItemOut], permissions=[AllowAny])
    def list_public_items(self, request):
        ...
```

**Permission classes:**

| Class | Behavior |
|-------|----------|
| `IsAuthenticated` | Requires a valid session cookie or auth token. Returns `401` if not authenticated. |
| `AllowAny` | No authentication required. Public endpoint. |

**Auth transport mechanisms:**

| Client | Mechanism | Details |
|--------|-----------|---------|
| Next.js (web) | Session cookie | httpOnly cookie set by Django Allauth. Same-origin via Next.js API proxy or subdomain. |
| Expo (mobile) | Token-based | Auth token from Allauth headless mode. Stored in `expo-secure-store`. Sent via `Authorization` header. |

### 5. Error Handling

Django Ninja Extra handles common errors automatically. Custom exception handlers standardize the error response format.

**Standard error responses:**

| Status Code | Meaning | Response Body |
|-------------|---------|---------------|
| `400` | Bad Request / Validation Error | `{"detail": [...]}` with field-level errors |
| `401` | Unauthorized | `{"detail": "Authentication credentials were not provided."}` |
| `403` | Forbidden | `{"detail": "You do not have permission to perform this action."}` |
| `404` | Not Found | `{"detail": "Not found."}` |
| `422` | Unprocessable Entity | `{"detail": [...]}` Pydantic validation errors |
| `429` | Too Many Requests | `{"detail": "Request was throttled."}` |
| `500` | Internal Server Error | `{"detail": "Internal server error."}` (no stack trace in production) |

**Custom exception handler registration:**

```python
# config/urls.py
from ninja_extra import NinjaExtraAPI
from apps.core.exceptions import ServiceError

api = NinjaExtraAPI(title="Foundation API", version="1.0.0")


@api.exception_handler(ServiceError)
def service_error_handler(request, exc: ServiceError):
    return api.create_response(
        request,
        {"detail": exc.message},
        status=exc.status_code,
    )
```

**Custom exception classes (`apps/core/exceptions.py`):**

```python
class ServiceError(Exception):
    """Base exception for service layer errors."""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(ServiceError):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message=message, status_code=404)


class PermissionDeniedError(ServiceError):
    def __init__(self, message: str = "Permission denied"):
        super().__init__(message=message, status_code=403)
```

### 6. Pagination Pattern

The template uses offset-based pagination by default. Pagination parameters are query parameters on list endpoints.

**Query parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `offset` | `int` | `0` | Number of records to skip. |
| `limit` | `int` | `20` | Number of records to return. Max `100`. |

**Response shape:**

```json
{
  "items": [...],
  "total": 142,
  "offset": 0,
  "limit": 20
}
```

**Implementation in controller:**

```python
@route.get("", response=ItemListOut)
def list_items(self, request, offset: int = 0, limit: int = 20):
    limit = min(limit, 100)  # Hard cap at 100
    return self.service.list_items(user=request.user, offset=offset, limit=limit)
```

### 7. Filtering and Ordering

List endpoints accept optional query parameters for filtering and ordering.

```python
from ninja import Query
from typing import Optional


@route.get("", response=ItemListOut)
def list_items(
    self,
    request,
    offset: int = 0,
    limit: int = 20,
    search: Optional[str] = Query(None, description="Search title and description"),
    ordering: str = Query("-created_at", description="Field to order by. Prefix with - for descending."),
):
    return self.service.list_items(
        user=request.user,
        offset=offset,
        limit=limit,
        search=search,
        ordering=ordering,
    )
```

**Service-level filtering:**

```python
from django.db.models import Q


def list_items(self, user, offset=0, limit=20, search=None, ordering="-created_at"):
    qs = Item.objects.filter(owner=user)

    if search:
        qs = qs.filter(
            Q(title__icontains=search) | Q(description__icontains=search)
        )

    allowed_orderings = {"created_at", "-created_at", "title", "-title"}
    if ordering not in allowed_orderings:
        ordering = "-created_at"

    qs = qs.order_by(ordering)
    total = qs.count()
    items = list(qs[offset : offset + limit])
    return {"items": items, "total": total, "offset": offset, "limit": limit}
```

**Ordering whitelist:** The service MUST validate that the `ordering` parameter is in an allowed set. Arbitrary field ordering exposes internal model structure and can cause performance issues with unindexed columns.

### 8. File Upload Handling

File uploads use Django Ninja's `File` and `UploadedFile` types.

```python
from ninja import File, UploadedFile


@route.post("/upload", response={201: FileOut})
def upload_file(self, request, file: UploadedFile = File(...)):
    """Upload a file."""
    return 201, self.service.handle_upload(user=request.user, file=file)
```

**File upload rules:**

| Rule | Description |
|------|-------------|
| Max file size | Enforce via `DATA_UPLOAD_MAX_MEMORY_SIZE` in Django settings (default 2.5MB). Override per-endpoint if needed. |
| Allowed types | Validate MIME type in the service layer. Do not trust the client's `Content-Type`. |
| Storage | Use Django's default file storage. For production, configure `django-storages` with S3/R2 backend. |

### 9. Health Check Endpoint

A public health check endpoint verifies API availability and database connectivity.

```python
# apps/core/controllers.py
from ninja_extra import api_controller, route
from ninja_extra.permissions import AllowAny
from django.db import connection

from .schemas import HealthOut


@api_controller("/health", tags=["Health"], permissions=[AllowAny])
class HealthController:

    @route.get("", response=HealthOut, url_name="health-check")
    def health_check(self, request):
        """Check API health and database connectivity."""
        db_ok = False
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            db_ok = True
        except Exception:
            pass

        return {
            "status": "healthy" if db_ok else "degraded",
            "database": "connected" if db_ok else "disconnected",
        }
```

**Health check schema:**

```python
class HealthOut(Schema):
    status: str   # "healthy" or "degraded"
    database: str # "connected" or "disconnected"
```

### 10. OpenAPI Documentation Enrichment

Controllers and routes enrich the auto-generated OpenAPI spec with metadata.

| Mechanism | Purpose | Example |
|-----------|---------|---------|
| `tags=["TagName"]` on `@api_controller` | Groups endpoints in Swagger UI | `@api_controller("/items", tags=["Items"])` |
| Docstrings on route methods | Populates the "description" field in OpenAPI | `"""Create a new item."""` |
| `response={201: ItemOut}` | Documents response status codes and schemas | Multiple responses: `response={200: ItemOut, 404: ErrorOut}` |
| `summary` parameter on `@route` | Short summary for the endpoint | `@route.get("", summary="List all items")` |
| `Field(description=...)` on schema fields | Documents individual fields | `title: str = Field(..., description="The item title")` |

### 11. Accounts Controller (Auth Endpoints)

The accounts controller wraps Django Allauth headless endpoints with Ninja Extra patterns:

```python
# apps/accounts/controllers.py
from ninja_extra import api_controller, route, ControllerBase
from ninja_extra.permissions import IsAuthenticated, AllowAny

from .schemas import UserOut, UserUpdateIn
from .services import UserService


@api_controller("/users", tags=["Users"])
class UserController(ControllerBase):

    def __init__(self):
        self.service = UserService()

    @route.get("/me", response=UserOut, permissions=[IsAuthenticated])
    def get_current_user(self, request):
        """Get the authenticated user's profile."""
        return self.service.get_user(user_id=request.user.id)

    @route.patch("/me", response=UserOut, permissions=[IsAuthenticated])
    def update_current_user(self, request, payload: UserUpdateIn):
        """Update the authenticated user's profile."""
        return self.service.update_user(
            user_id=request.user.id, data=payload
        )
```

Django Allauth headless mode provides its own auth endpoints (signup, login, logout, email verification, password reset) at `/_allauth/` by default. These are NOT re-implemented in Ninja Extra controllers.

### 12. API Initialization and Registration

The full API setup lives in `apps/api/config/urls.py`. Controllers are auto-discovered.

```python
# apps/api/config/urls.py
from django.contrib import admin
from django.urls import path
from ninja_extra import NinjaExtraAPI

from apps.core.exceptions import ServiceError

api = NinjaExtraAPI(
    title="Foundation API",
    version="1.0.0",
    urls_namespace="api_v1",
)

# Auto-discover all controllers decorated with @api_controller
# Scans all INSTALLED_APPS for controllers.py modules
api.auto_discover_controllers()


@api.exception_handler(ServiceError)
def service_error_handler(request, exc: ServiceError):
    return api.create_response(
        request,
        {"detail": exc.message},
        status=exc.status_code,
    )


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", api.urls),
]
```

**Auto-discovery:** `api.auto_discover_controllers()` scans all `INSTALLED_APPS` for modules containing `@api_controller`-decorated classes. Controllers in `apps/api/apps/accounts/controllers.py`, `apps/api/apps/core/controllers.py`, and `apps/api/apps/ai/controllers.py` are found automatically. No manual registration required.

### 13. API Versioning

The template uses URL-prefix versioning. The initial version is `v1`, embedded in the API path.

When a breaking change is needed, a new `NinjaExtraAPI` instance is created for `v2` alongside `v1`:

```python
# config/urls.py -- when v2 is needed
api_v1 = NinjaExtraAPI(title="Foundation API", version="1.0.0", urls_namespace="api_v1")
api_v2 = NinjaExtraAPI(title="Foundation API", version="2.0.0", urls_namespace="api_v2")

api_v1.auto_discover_controllers()
api_v2.auto_discover_controllers()

urlpatterns = [
    path("api/v1/", api_v1.urls),
    path("api/v2/", api_v2.urls),
]
```

## Scenarios

### GIVEN an authenticated user sends a POST to `/api/v1/items` with valid JSON body
### WHEN the controller receives the request
### THEN the input schema validates the body, the service creates the resource, and the controller returns `201` with the serialized resource

---

### GIVEN an authenticated user sends a GET to `/api/v1/items?offset=20&limit=10`
### WHEN the controller receives the request
### THEN the service queries the user's items ordered by `-created_at`, skips 20, returns 10, and the response includes `total`, `offset`, and `limit`

---

### GIVEN an authenticated user sends a PATCH to `/api/v1/items/{id}` with `{"title": "Updated"}`
### WHEN the controller receives the request
### THEN only the `title` field is updated (other fields unchanged), and the full updated resource is returned

---

### GIVEN a request sends a POST with an invalid body (missing required fields)
### WHEN the input schema validates the body
### THEN a `422` response is returned with field-level error details listing which fields failed and why

---

### GIVEN an unauthenticated request is sent to a route with `permissions=[IsAuthenticated]`
### WHEN the permission check runs
### THEN a `401` response is returned with `{"detail": "Authentication credentials were not provided."}`

---

### GIVEN an authenticated user requests `/api/v1/items/{id}` for an item they do not own
### WHEN the service calls `get_object_or_404(Item, id=item_id, owner=user)`
### THEN a `404` response is returned (resource not exposed to non-owners)

---

### GIVEN a GET request to `/api/v1/health`
### WHEN the database is connected
### THEN the response is `{"status": "healthy", "database": "connected"}` with status `200`

---

### GIVEN a GET request to `/api/v1/health`
### WHEN the database is unreachable
### THEN the response is `{"status": "degraded", "database": "disconnected"}` with status `200`

---

### GIVEN a GET request to `/api/v1/items?search=keyword&ordering=-title`
### WHEN the service processes the query
### THEN items are filtered by `title__icontains` or `description__icontains` matching "keyword" and ordered by title descending

---

### GIVEN the API server is running with all controllers registered
### WHEN a GET request is made to `/api/v1/openapi.json`
### THEN the response is a valid OpenAPI 3.x document with all endpoints documented, including tags, descriptions, request schemas, and response schemas

## Constraints

- Controllers MUST NOT contain ORM queries. All data access goes through the service layer.
- Every list endpoint MUST enforce a maximum `limit` of `100`. The service layer caps it.
- Every list endpoint MUST use `select_related` / `prefetch_related` in the service to prevent N+1 queries.
- Ordering parameters MUST be validated against an explicit whitelist. Arbitrary ordering is not allowed.
- Input schemas MUST NOT use `ModelSchema`. Input schemas are always plain `Schema` to decouple request shape from model structure.
- Output schemas MUST declare explicit `fields` when using `ModelSchema`. Never use `fields = "__all__"`.
- The health check endpoint MUST be public (`AllowAny`). It is used by load balancers and monitoring tools.
- Error responses MUST follow the standard format: `{"detail": "..."}` for string errors, `{"detail": [...]}` for validation errors.
- The OpenAPI spec MUST be available at runtime for auto-generation of TypeScript types. Do NOT disable it.
- File uploads MUST validate file type server-side. Client-provided MIME types are not trusted.
- Django Allauth endpoints are NOT re-implemented. The template relies on Allauth's headless endpoints for signup, login, logout, email verification, and password reset.

## References

- `.planning/research/ARCHITECTURE.md` -- Pattern 3: Layered Django App Structure (Controllers / Services / Repositories)
- `.planning/research/ARCHITECTURE.md` -- Pattern 2: OpenAPI-First Type Generation Pipeline
- `.planning/research/STACK.md` -- Django Ninja Extra as the API framework (non-negotiable)
- `.planning/research/PITFALLS.md` -- Pitfall #4: OpenAPI pipeline fragility; Pitfall #6: N+1 queries from Ninja serializers
- `.planning/PROJECT.md` -- Django Ninja Extra API with auto-generated OpenAPI spec requirement
