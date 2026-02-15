# ORM and Database Configuration

> Baseline specification for the Foundation Template.
> This document is the source of truth. All implementations must conform to these specs.

## Overview

The Foundation Template uses Django ORM as the exclusive data access layer with PostgreSQL 16+ as the database. The database adapter is `psycopg` (psycopg3), configured via `django-environ` for environment-variable-driven settings. PGVector is enabled via the `pgvector/pgvector:pg16` Docker image. All database access goes through Django ORM -- no raw SQL unless justified for PGVector operations that cannot be expressed through the ORM.

## Specifications

### Database Configuration

```python
# apps/api/config/settings/base.py
import environ

env = environ.Env()

DATABASES = {
    "default": env.db("DATABASE_URL", default="postgres://foundation:foundation@localhost:5432/foundation"),
}

# Use psycopg3 (the package named `psycopg`) as the database backend
DATABASES["default"]["ENGINE"] = "django.db.backends.postgresql"

# Connection age limit (seconds). Close connections older than this.
# Prevents connection pool exhaustion from long-lived idle connections.
CONN_MAX_AGE = env.int("CONN_MAX_AGE", default=600)  # 10 minutes
DATABASES["default"]["CONN_MAX_AGE"] = CONN_MAX_AGE
```

```python
# apps/api/config/settings/development.py
from .base import *

# Use shorter connection age in development for easier debugging
DATABASES["default"]["CONN_MAX_AGE"] = 0  # Close after each request

# SQLite override for quick unit tests (optional, not recommended for CI)
# if env.bool("USE_SQLITE", default=False):
#     DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
```

```python
# apps/api/config/settings/production.py
from .base import *

DATABASES["default"]["CONN_MAX_AGE"] = env.int("CONN_MAX_AGE", default=600)

# Connection pooling for production (when PgBouncer is not used)
DATABASES["default"]["OPTIONS"] = {
    "pool": True,  # psycopg3 built-in connection pool
}
```

### Database Adapter: psycopg3

| Decision | Details |
|----------|---------|
| Package | `psycopg[binary]` (psycopg3, NOT psycopg2-binary) |
| Why psycopg3 | Pure Python with optional C acceleration. Actively maintained. Modern async support. psycopg2 is legacy. |
| Django backend | `django.db.backends.postgresql` (auto-detects psycopg3 in Django 5.1+) |
| pyproject.toml | `psycopg = {extras = ["binary"], version = "^3.x"}` |

**GIVEN** the Django project uses `django.db.backends.postgresql`
**WHEN** psycopg (v3) is installed
**THEN** Django 5.1+ automatically uses psycopg3 as the database adapter
**AND** no additional engine configuration is needed

### Django ORM Query Patterns

#### File Organization

All database queries live in the service layer, never in controllers:

```
apps/api/apps/[domain]/
+-- models.py        # Django models (schema only, no query logic)
+-- services.py      # Business logic + ORM queries
+-- controllers.py   # HTTP boundary (delegates to services)
+-- schemas.py       # Pydantic input/output schemas
```

#### Select Related and Prefetch Related

Every list endpoint MUST declare explicit joins to prevent N+1 queries.

```python
# apps/api/apps/[domain]/services.py

# ForeignKey / OneToOneField: use select_related (SQL JOIN)
items = Item.objects.select_related("owner", "category").filter(...)

# ManyToManyField / reverse ForeignKey: use prefetch_related (separate query, cached)
items = Item.objects.prefetch_related("tags", "comments").filter(...)

# Combined for complex models
documents = (
    Document.objects
    .select_related("author")        # FK: single JOIN
    .prefetch_related("tags")        # M2M: separate query
    .filter(author_id=user_id)
    .order_by("-created_at")
)
```

**GIVEN** a list endpoint returns resources with related objects
**WHEN** the service queries the database
**THEN** `select_related` is used for ForeignKey/OneToOne relationships
**AND** `prefetch_related` is used for ManyToMany/reverse FK relationships
**AND** the total query count does not scale with the number of results

#### QuerySet Best Practices

```python
# apps/api/apps/[domain]/services.py

class ItemService:
    def list_items(self, user, offset=0, limit=20, search=None, ordering="-created_at"):
        qs = Item.objects.filter(owner=user)

        # Filtering with Q objects for OR conditions
        if search:
            from django.db.models import Q
            qs = qs.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )

        # Whitelist-based ordering (never allow arbitrary field ordering)
        allowed_orderings = {"created_at", "-created_at", "title", "-title"}
        if ordering not in allowed_orderings:
            ordering = "-created_at"

        qs = qs.order_by(ordering)
        total = qs.count()
        items = list(qs[offset : offset + limit])
        return {"items": items, "total": total, "offset": offset, "limit": limit}

    def get_or_404(self, user, item_id):
        """Use get_object_or_404 pattern for single resource retrieval."""
        from django.shortcuts import get_object_or_404
        return get_object_or_404(Item, id=item_id, owner=user)
```

#### Bulk Operations

```python
# Use bulk_create for inserting multiple records efficiently
tags = [Tag(name=name) for name in names]
Tag.objects.bulk_create(tags, ignore_conflicts=True)

# Use update() for mass updates (single SQL UPDATE, no model instantiation)
Tag.objects.filter(id__in=tag_ids).update(is_active=False)

# Use F() expressions for atomic field updates
from django.db.models import F
Item.objects.filter(id=item_id).update(view_count=F("view_count") + 1)
```

#### Aggregation and Annotation

```python
from django.db.models import Count, Avg, Sum

# Aggregate: returns a dict
stats = Item.objects.filter(owner=user).aggregate(
    total=Count("id"),
    avg_price=Avg("price"),
)

# Annotate: adds computed fields to each row
categories = (
    Category.objects
    .annotate(item_count=Count("items"))
    .order_by("-item_count")
)
```

### Migration Workflow

```bash
# Create migrations after model changes
cd apps/api && python manage.py makemigrations

# Apply migrations
cd apps/api && python manage.py migrate

# Check for missing migrations (CI gate)
cd apps/api && python manage.py makemigrations --check --dry-run
```

| Rule | Rationale |
|------|-----------|
| Never hand-write migrations | Always use `makemigrations`. Hand-written migrations drift from model state. |
| Never use `--fake` | Faking migrations causes silent drift between state and schema. |
| One migration per logical change | Keep migrations reviewable. Squash when count impacts startup. |
| CI validates migrations | `makemigrations --check --dry-run` in CI catches uncommitted migrations. |
| Custom user model first | `accounts.0001_initial` MUST be the first app migration. |
| PGVector extension before vector models | `core.0001_enable_pgvector` before any `VectorField` migration. |

### Database Indexes

```python
# apps/api/apps/[domain]/models.py
class Item(BaseModel):
    title = models.CharField(max_length=255, db_index=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="items")
    status = models.CharField(max_length=20, db_index=True)

    class Meta:
        # Composite indexes for common query patterns
        indexes = [
            models.Index(fields=["owner", "-created_at"], name="item_owner_created_idx"),
            models.Index(fields=["status", "-created_at"], name="item_status_created_idx"),
        ]
        # Unique constraints
        constraints = [
            models.UniqueConstraint(fields=["owner", "title"], name="unique_item_per_user"),
        ]
```

**Indexing rules:**
- Index fields used in `filter()`, `order_by()`, and `WHERE` clauses.
- Use `db_index=True` on single fields filtered frequently.
- Use `Meta.indexes` for composite indexes matching query patterns.
- ForeignKey fields are indexed automatically by Django.
- `created_at` is indexed via `BaseModel` (`db_index=True`).

### Transaction Patterns

```python
from django.db import transaction

class OrderService:
    def create_order(self, user, items):
        """Use atomic transactions for multi-table operations."""
        with transaction.atomic():
            order = Order.objects.create(user=user)
            OrderItem.objects.bulk_create([
                OrderItem(order=order, item=item) for item in items
            ])
            # If any step fails, the entire transaction rolls back
            return order
```

**GIVEN** a service method modifies multiple tables
**WHEN** it wraps operations in `transaction.atomic()`
**THEN** either all changes commit or none do
**AND** partial state is never visible to other queries

### Connection Scaling

| Users | Strategy | Configuration |
|-------|----------|---------------|
| < 100 | Default Django connections | `CONN_MAX_AGE = 0` (close after request) |
| 100-10K | Persistent connections | `CONN_MAX_AGE = 600` (reuse for 10 min) |
| 10K+ | PgBouncer connection pooler | External PgBouncer in front of Postgres. Django connects to PgBouncer. `CONN_MAX_AGE = 0` when using PgBouncer. |

**PostgreSQL default connection limit is 100.** At scale, Django workers can exhaust this. PgBouncer multiplexes many Django connections into fewer Postgres connections.

## Constraints

1. **All database access goes through Django ORM.** No raw SQL unless justified in a comment (PGVector operations only).
2. **No `--fake` migrations.** If migrations are out of sync, fix them properly.
3. **psycopg3 only.** psycopg2-binary is explicitly rejected. See `openspec/specs/foundation/stack.md`.
4. **Ordering parameters must be whitelisted.** Never allow arbitrary field ordering from client input.
5. **Every list query must use select_related/prefetch_related.** N+1 queries are a bug, not a performance issue to fix later.
6. **Transactions for multi-table writes.** Use `transaction.atomic()` for operations spanning multiple models.
7. **CI must validate migration state.** `makemigrations --check --dry-run` catches uncommitted schema changes.

## References

- `openspec/specs/foundation/data-models.md` -- Model patterns (BaseModel, User, EmbeddingMixin)
- `openspec/specs/foundation/stack.md` -- psycopg3, PostgreSQL 16+, PGVector versions
- `openspec/specs/backend/api-endpoints.md` -- Service layer pattern (where queries live)
- `.planning/research/STACK.md` -- psycopg3 rationale, database configuration patterns
- `.planning/research/ARCHITECTURE.md` -- Scaling considerations, connection pooling
