# Data Models Specification

> Baseline specification for the Foundation Template.
> This document is the source of truth. All implementations must conform to these specs.

## Overview

The Foundation Template uses Django ORM as the exclusive data access layer. All models follow established patterns: a custom AbstractUser model, a base model mixin with timestamps and soft delete, and a PGVector embedding field mixin for the AI module. Models are always managed through Django migrations. Pydantic schemas define the API contract layer on top of these models.

## Specifications

### Custom AbstractUser Model

The custom user model MUST be created before the first `python manage.py migrate` is ever executed. Changing the user model after initial migration requires database recreation.

```python
# apps/api/apps/accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model. Extends AbstractUser to allow future field additions
    without painful migrations. MUST be defined before first migration.
    """

    email = models.EmailField(unique=True)

    # Override username to make email the primary identifier
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        db_table = "accounts_user"
        ordering = ["-date_joined"]

    def __str__(self):
        return self.email
```

```python
# config/settings/base.py
AUTH_USER_MODEL = "accounts.User"
```

**GIVEN** a new project is scaffolded from the template
**WHEN** the developer runs `python manage.py migrate` for the first time
**THEN** the accounts_user table is created with all AbstractUser fields plus any custom fields
**AND** AUTH_USER_MODEL points to "accounts.User"
**AND** all Django auth machinery (login, logout, password reset) uses this custom model

**GIVEN** a developer needs to add a field to the user model (e.g., avatar, phone_number)
**WHEN** they add the field to the User model class
**THEN** `python manage.py makemigrations` generates a migration
**AND** `python manage.py migrate` applies it cleanly
**AND** no database recreation is required

### Base Model Mixin

All application models (except User) inherit from BaseModel for consistent timestamps and soft delete:

```python
# apps/api/apps/core/models.py
from django.db import models
from django.utils import timezone


class BaseQuerySet(models.QuerySet):
    """QuerySet that filters out soft-deleted records by default."""

    def active(self):
        return self.filter(deleted_at__isnull=True)

    def deleted(self):
        return self.filter(deleted_at__isnull=False)


class BaseManager(models.Manager):
    """Manager that returns only active (non-deleted) records by default."""

    def get_queryset(self):
        return BaseQuerySet(self.model, using=self._db).active()

    def all_with_deleted(self):
        return BaseQuerySet(self.model, using=self._db)

    def deleted_only(self):
        return BaseQuerySet(self.model, using=self._db).deleted()


class BaseModel(models.Model):
    """
    Abstract base model providing timestamps and soft delete.
    All application models should inherit from this.
    """

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    objects = BaseManager()

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    def soft_delete(self):
        """Mark record as deleted without removing from database."""
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at", "updated_at"])

    def restore(self):
        """Restore a soft-deleted record."""
        self.deleted_at = None
        self.save(update_fields=["deleted_at", "updated_at"])

    @property
    def is_deleted(self):
        return self.deleted_at is not None
```

**GIVEN** a model inherits from BaseModel
**WHEN** a record is created
**THEN** `created_at` is set to the current timestamp automatically
**AND** `updated_at` is set to the current timestamp automatically
**AND** `deleted_at` is NULL

**GIVEN** a model instance has `soft_delete()` called
**WHEN** the default manager queries the model
**THEN** the soft-deleted record is NOT included in results
**AND** `Model.objects.all_with_deleted()` includes the record
**AND** `Model.objects.deleted_only()` returns only soft-deleted records

**GIVEN** a soft-deleted record has `restore()` called
**WHEN** the default manager queries the model
**THEN** the record IS included in results again
**AND** `deleted_at` is NULL

### PGVector Embedding Field Mixin

For models in the AI module that store vector embeddings. Requires the `pgvector` Python package (`pip install pgvector`) which provides Django ORM integration via `pgvector.django`.

**Required dependency:** `pgvector` (provides `VectorField`, `HnswIndex`, `CosineDistance`, `L2Distance`, `MaxInnerProduct`)

```python
# apps/api/apps/ai/models.py
from django.db import models
from pgvector.django import VectorField, HnswIndex


class EmbeddingMixin(models.Model):
    """
    Mixin for models that store vector embeddings.
    Uses PGVector with HNSW index for cosine similarity search.
    """

    embedding = VectorField(
        dimensions=1536,  # OpenAI text-embedding-3-small dimension
        null=True,
        blank=True,
        help_text="Vector embedding for similarity search",
    )
    embedding_model = models.CharField(
        max_length=100,
        default="text-embedding-3-small",
        help_text="Model used to generate the embedding",
    )
    embedded_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the embedding was last generated",
    )

    class Meta:
        abstract = True
        indexes = [
            HnswIndex(
                name="%(class)s_embedding_idx",
                fields=["embedding"],
                m=16,
                ef_construction=64,
                opclasses=["vector_cosine_ops"],
            ),
        ]
```

**GIVEN** a model inherits from both BaseModel and EmbeddingMixin
**WHEN** `python manage.py migrate` is run
**THEN** the table has an `embedding` column of type vector(1536)
**AND** an HNSW index is created with `vector_cosine_ops` operator class
**AND** the index uses m=16, ef_construction=64 parameters

**GIVEN** a record has a non-null embedding
**WHEN** a cosine similarity search is performed
**THEN** the HNSW index accelerates the search
**AND** results are ordered by cosine distance (ascending = most similar first)

### PGVector Extension Setup

The PGVector extension must be enabled via a Django migration. The Docker image `pgvector/pgvector:pg16` includes the extension pre-installed -- this migration only activates it.

```python
# apps/api/apps/core/migrations/0001_enable_pgvector.py
from django.db import migrations


class Migration(migrations.Migration):
    """Enable the pgvector extension. Must run before any model using VectorField."""

    dependencies = []

    operations = [
        migrations.RunSQL(
            sql="CREATE EXTENSION IF NOT EXISTS vector;",
            reverse_sql="DROP EXTENSION IF EXISTS vector;",
        ),
    ]
```

### Vector Similarity Search via ORM

The `pgvector` Python package provides Django ORM distance functions that integrate with HNSW indexes:

```python
# apps/api/apps/ai/services.py
from pgvector.django import CosineDistance
from django.db import connection

# ORM-based cosine similarity search (uses HNSW index)
results = (
    Document.objects
    .filter(embedding__isnull=False)
    .annotate(distance=CosineDistance("embedding", query_vector))
    .filter(distance__lt=0.5)  # threshold
    .order_by("distance")[:limit]
)

# Set HNSW search parameters per-query for recall/speed tradeoff
with connection.cursor() as cursor:
    cursor.execute("SET hnsw.ef_search = 100")
```

**Available distance functions from `pgvector.django`:**

| Function          | Operator Class      | Use Case                                                                       |
| ----------------- | ------------------- | ------------------------------------------------------------------------------ |
| `CosineDistance`  | `vector_cosine_ops` | Default for OpenAI/Anthropic embeddings. Range: 0 (identical) to 2 (opposite). |
| `L2Distance`      | `vector_l2_ops`     | Euclidean distance. Use when magnitude matters.                                |
| `MaxInnerProduct` | `vector_ip_ops`     | Dot product. Use for pre-normalized embeddings.                                |

**Rule:** The distance function used in queries MUST match the operator class on the HNSW index. Using `CosineDistance` with a `vector_l2_ops` index silently bypasses the index.

### Migration Strategy

| Rule                             | Rationale                                                                                    |
| -------------------------------- | -------------------------------------------------------------------------------------------- |
| Always use migrations            | Never modify the database schema manually. Django migrations are the source of truth.        |
| Never use `--fake`               | Faking migrations causes drift between migration state and actual database schema.           |
| One migration per logical change | Keep migrations small and reviewable. Squash only when migration count impacts startup time. |
| Test migrations in CI            | CI runs `python manage.py migrate` against a fresh Postgres database on every PR.            |
| Data migrations for data changes | Use `RunPython` operations for data transformations. Keep them idempotent.                   |
| Custom user model first          | `accounts.0001_initial` must be the first app migration to run.                              |

**GIVEN** a developer adds a new field to a model
**WHEN** they run `python manage.py makemigrations`
**THEN** Django generates a new migration file with the schema change
**AND** the migration is committed to version control
**AND** CI validates the migration applies cleanly to a fresh database

**GIVEN** a developer needs to change data in an existing table
**WHEN** they create a data migration with `RunPython`
**THEN** the migration is idempotent (can be run multiple times safely)
**AND** includes a reverse operation for rollback

### Django ORM Patterns

#### Select Related and Prefetch Related

```python
# CORRECT: Eager loading to avoid N+1 queries
class DocumentService:
    def list_documents(self, user_id: int) -> list:
        return (
            Document.objects
            .select_related("author")           # FK: single JOIN
            .prefetch_related("tags")           # M2M: separate query, cached
            .filter(author_id=user_id)
            .order_by("-created_at")
        )

# INCORRECT: N+1 queries (one query per document for author)
class DocumentService:
    def list_documents(self, user_id: int) -> list:
        documents = Document.objects.filter(author_id=user_id)
        for doc in documents:
            print(doc.author.email)  # Each access triggers a query
```

**GIVEN** a list endpoint returns resources with related objects
**WHEN** the service queries the database
**THEN** `select_related` is used for ForeignKey/OneToOne relationships
**AND** `prefetch_related` is used for ManyToMany/reverse FK relationships
**AND** the total query count does not scale with the number of results

#### QuerySet Filtering

```python
# Service layer uses querysets, not raw SQL
class UserService:
    def search_users(self, query: str) -> QuerySet:
        return User.objects.filter(
            models.Q(email__icontains=query)
            | models.Q(first_name__icontains=query)
            | models.Q(last_name__icontains=query)
        )

    def get_user_or_404(self, user_id: int) -> User:
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise NotFoundError(f"User {user_id} not found")
```

#### Bulk Operations

```python
# Use bulk operations for multiple records
class TagService:
    def create_tags(self, names: list[str]) -> list:
        tags = [Tag(name=name) for name in names]
        return Tag.objects.bulk_create(tags, ignore_conflicts=True)

    def update_tags(self, tag_ids: list[int], active: bool) -> int:
        return Tag.objects.filter(id__in=tag_ids).update(
            is_active=active,
            updated_at=timezone.now(),
        )
```

### Pydantic Schema Patterns for Ninja Extra

#### Schema-to-Model Mapping

```python
# apps/api/apps/accounts/schemas.py
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


# Output schema: what the API returns
class UserOut(BaseModel):
    id: int
    email: EmailStr
    first_name: str
    last_name: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True  # Enable ORM mode


# Input schema: what the API accepts for creation
class UserCreateIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    first_name: str = Field(max_length=150)
    last_name: str = Field(max_length=150)


# Update schema: all fields optional for PATCH
class UserUpdateIn(BaseModel):
    first_name: str | None = None
    last_name: str | None = None


# Filter schema: query parameters for list endpoints
class UserFilter(BaseModel):
    search: str | None = None
    is_active: bool | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
```

#### Config.from_attributes = True

All output schemas that map to Django models MUST include `from_attributes = True` (formerly `orm_mode = True`). This allows Pydantic to read data from Django model instances directly:

```python
# In controller:
user = User.objects.get(id=1)
return UserOut.from_orm(user)  # Works because from_attributes = True
```

#### Nested Schemas

```python
class DocumentOut(BaseModel):
    id: int
    title: str
    author: UserOut        # Nested schema
    tags: list[TagOut]     # List of nested schemas
    created_at: datetime

    class Config:
        from_attributes = True
```

**GIVEN** a controller returns a Django model instance
**WHEN** Ninja Extra serializes the response using the Pydantic schema
**THEN** the schema reads attributes from the model instance (via from_attributes)
**AND** nested relationships are serialized recursively
**AND** only fields declared in the schema are included in the response

### Model Lifecycle Scenarios

**GIVEN** a new user signs up via the API
**WHEN** UserCreateIn schema validates the request body
**THEN** UserService.create_user() creates a User instance via Django ORM
**AND** the password is hashed via Django's `set_password()`
**AND** the user is saved to the database with a generated ID
**AND** UserOut schema serializes the response (excluding password)

**GIVEN** a user updates their profile via PATCH /users/me
**WHEN** UserUpdateIn schema validates the request body (only provided fields)
**THEN** UserService.update_user() calls `dict(exclude_unset=True)` on the schema
**AND** only provided fields are updated on the model instance
**AND** `updated_at` is refreshed automatically (auto_now=True)
**AND** the full UserOut is returned

**GIVEN** a resource is soft-deleted via DELETE endpoint
**WHEN** the controller calls `service.delete_resource(id)`
**THEN** the service calls `instance.soft_delete()`
**AND** `deleted_at` is set to the current timestamp
**AND** the resource is excluded from future default queries
**AND** the resource can be restored via `instance.restore()`
**AND** the API returns 204 No Content

## Constraints

1. **Custom User model is mandatory.** AUTH_USER_MODEL must point to accounts.User before first migration. Using Django's default User model is forbidden.
2. **All application models inherit from BaseModel.** Timestamps and soft delete are universal. The only exception is the User model (inherits from AbstractUser directly, but should add created_at/updated_at if AbstractUser does not provide them).
3. **No raw SQL except for PGVector operations.** Use Django ORM for all standard queries. Raw SQL is acceptable only for vector similarity searches that cannot be expressed through the ORM.
4. **No `--fake` migrations.** Ever. If migrations are out of sync, fix them properly.
5. **Pydantic schemas always use `from_attributes = True` for output schemas.** Required for ORM-to-schema conversion.
6. **Embedding dimension must be declared explicitly.** VectorField(dimensions=1536) -- never omit the dimensions parameter. Mismatched dimensions cause cryptic errors.
7. **HNSW index operator class must match the distance function.** Use `vector_cosine_ops` for cosine similarity (default). Using the wrong operator class means the index is not utilized.

## Note on Research Files

The `.planning/` directory is excluded from projects scaffolded using this template. This spec is the self-contained source of rationale — all decisions, alternatives considered, and implementation constraints are documented inline above. No external research files are required to understand or implement the decisions in this spec.
