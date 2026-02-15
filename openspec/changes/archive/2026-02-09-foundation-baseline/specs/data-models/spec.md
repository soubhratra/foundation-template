# Data Models and Persistence

## ADDED Requirements

### Requirement: Custom AbstractUser Model
The Django backend MUST define a custom User model extending AbstractUser in apps/accounts/models.py BEFORE the first migration. The AUTH_USER_MODEL setting MUST point to "accounts.User" in base settings.

#### Scenario: Pre-Migration User Model Definition
- **WHEN** the repository is first cloned and migrations have never been run
- **THEN** apps/accounts/models.py contains a User class extending AbstractUser
- **AND** config/settings/base.py sets AUTH_USER_MODEL = "accounts.User"
- **AND** the first migration (accounts/migrations/0001_initial.py) creates the custom User table

#### Scenario: Adding Fields to User Model
- **WHEN** a developer adds a new field (e.g., avatar) to the User model
- **THEN** `python manage.py makemigrations` generates a new migration
- **AND** the migration applies cleanly without database recreation
- **AND** all Django auth machinery continues to work with the custom model

### Requirement: BaseModel Mixin with Timestamps and Soft Delete
All application models (except User) MUST inherit from BaseModel abstract class providing created_at, updated_at, and soft delete functionality. The default manager MUST filter out soft-deleted records.

#### Scenario: Automatic Timestamp Management
- **WHEN** a model inheriting from BaseModel is saved for the first time
- **THEN** created_at is set to the current timestamp automatically
- **AND** updated_at is set to the current timestamp automatically
- **AND** subsequent saves update only updated_at (via auto_now=True)

#### Scenario: Soft Delete Behavior
- **WHEN** `instance.soft_delete()` is called on a model instance
- **THEN** deleted_at is set to the current timestamp
- **AND** the record remains in the database
- **AND** `Model.objects.all()` excludes the record (default manager filters deleted_at__isnull=True)
- **AND** `Model.objects.all_with_deleted()` includes the record

#### Scenario: Soft Delete Restoration
- **WHEN** `instance.restore()` is called on a soft-deleted record
- **THEN** deleted_at is set to None
- **AND** the record reappears in default querysets
- **AND** updated_at is refreshed to the current timestamp

### Requirement: PGVector EmbeddingMixin
Models in the AI module that store vector embeddings MUST inherit from EmbeddingMixin providing a VectorField, embedding_model, and embedded_at fields. An HNSW index MUST be defined for vector similarity search.

#### Scenario: Vector Field Creation
- **WHEN** a model inheriting from EmbeddingMixin is migrated
- **THEN** the database table includes an embedding column of type vector(1536)
- **AND** embedding_model column stores the model identifier (e.g., "text-embedding-3-small")
- **AND** embedded_at column stores when the embedding was generated

#### Scenario: HNSW Index Creation
- **WHEN** the migration runs with EmbeddingMixin's Meta.indexes
- **THEN** an HNSW index is created on the embedding column
- **AND** the index uses vector_cosine_ops operator class for cosine similarity
- **AND** the index parameters are m=16, ef_construction=64

#### Scenario: Vector Similarity Search
- **WHEN** a service queries for nearest neighbors using cosine similarity
- **THEN** the HNSW index accelerates the search
- **AND** results are ordered by cosine distance (ascending = most similar first)
- **AND** the query performance scales logarithmically with dataset size

### Requirement: Django Migration Strategy
All database schema changes MUST be managed through Django migrations. Manual SQL schema changes are forbidden. The PGVector extension MUST be enabled via a Django migration before any VectorField models are migrated.

#### Scenario: PGVector Extension Enablement
- **WHEN** the first migration for the core app runs
- **THEN** the migration executes `CREATE EXTENSION IF NOT EXISTS vector`
- **AND** subsequent migrations can use VectorField without errors
- **AND** the reverse migration drops the extension

#### Scenario: Migration Validation in CI
- **WHEN** a pull request includes new migrations
- **THEN** CI runs `python manage.py migrate` against a fresh Postgres database
- **AND** all migrations apply cleanly in order
- **AND** the build fails if any migration errors occur

### Requirement: psycopg3 Database Adapter
The Django project MUST use psycopg (psycopg3) as the PostgreSQL adapter. The legacy psycopg2 or psycopg2-binary adapters MUST NOT be used.

#### Scenario: Database Connection with psycopg3
- **WHEN** Django connects to Postgres using the DATABASE_URL setting
- **THEN** psycopg3 establishes the connection
- **AND** all ORM queries use the psycopg3 adapter
- **AND** no psycopg2 imports exist in the codebase

#### Scenario: Dependency Declaration
- **WHEN** pyproject.toml declares database dependencies
- **THEN** it includes `psycopg[binary]` (psycopg3 with C speedups)
- **AND** psycopg2 or psycopg2-binary do NOT appear in dependencies
- **AND** uv.lock pins the psycopg3 version

### Requirement: Django ORM Query Optimization
All service layer methods that return related objects MUST use select_related (for ForeignKey/OneToOne) or prefetch_related (for ManyToMany/reverse FK) to prevent N+1 query problems.

#### Scenario: List Endpoint with Related Objects
- **WHEN** a service method returns a list of documents with authors (FK)
- **THEN** the queryset uses `.select_related("author")`
- **AND** all author data is fetched in a single JOIN query
- **AND** accessing `document.author.email` does NOT trigger additional queries

#### Scenario: ManyToMany Prefetching
- **WHEN** a service method returns resources with ManyToMany relationships (e.g., tags)
- **THEN** the queryset uses `.prefetch_related("tags")`
- **AND** tags are fetched in a separate optimized query
- **AND** the total query count is 2 (main query + prefetch) regardless of result count

### Requirement: Pydantic Schema-to-ORM Mapping
All Pydantic output schemas that serialize Django models MUST include `from_attributes = True` (formerly orm_mode). Input schemas MUST NOT use from_attributes as they define request shape independently of model structure.

#### Scenario: ORM Instance Serialization
- **WHEN** a controller returns a Django model instance with a UserOut schema
- **THEN** Pydantic reads attributes from the model instance (via from_attributes=True)
- **AND** only fields declared in the schema are included in the response
- **AND** no manual dict conversion is needed

#### Scenario: Nested Schema Serialization
- **WHEN** a DocumentOut schema includes a nested UserOut for the author field
- **THEN** both schemas have from_attributes=True
- **AND** the author relationship is traversed and serialized automatically
- **AND** the response includes the full nested user object
