---
phase: 06-ai-module
plan: 01
subsystem: ai-backend
tags: [pgvector, django-models, vector-search, database-setup]
dependency_graph:
  requires: [API-01, API-02]
  provides: [AI-01, AI-02]
  affects: [docker-compose, django-settings]
tech_stack:
  added: [pgvector, tiktoken]
  patterns: [vector-embeddings, hnsw-indexing]
key_files:
  created:
    - apps/api/apps/ai/__init__.py
    - apps/api/apps/ai/models.py
    - apps/api/apps/ai/migrations/__init__.py
    - apps/api/apps/ai/migrations/0001_initial.py
    - apps/api/apps/ai/migrations/0002_vector_extension.py
    - apps/api/apps/ai/migrations/0003_documentchunk_hnsw_index.py
  modified:
    - apps/api/config/settings/base.py
    - apps/api/pyproject.toml
    - apps/api/uv.lock
    - docker-compose.yml
decisions:
  - key: "HNSW index in concrete model not abstract mixin"
    rationale: "Django migration system doesn't detect HnswIndex from abstract model Meta classes"
    impact: "Future models with embeddings need explicit index declaration"
    alternatives: "Custom migration generation, but explicit is clearer"
  - key: "Index name shortened to ai_chunk_embedding_hnsw_idx"
    rationale: "Django enforces 31-character limit on index names"
    impact: "Shorter names required for all future indexes"
  - key: "PGVector extension with IF NOT EXISTS"
    rationale: "Avoids permission errors in production where extension may be pre-installed"
    impact: "Safe for both local dev and production deployment"
  - key: "Docker shm_size: 1gb and maintenance_work_mem: 256MB"
    rationale: "HNSW parallel index builds require shared memory beyond Docker's 64MB default"
    impact: "Template supports larger vector datasets without memory errors"
metrics:
  duration_minutes: 5
  tasks_completed: 3
  files_modified: 10
  commits: 3
  completed_at: "2026-02-17T01:30:41Z"
---

# Phase 06 Plan 01: PGVector Foundation Setup Summary

**PGVector extension enabled with Django models and HNSW indexing for vector similarity search**

## What Was Built

Created the foundation for the AI module's vector search capabilities:

1. **AI Django App Structure**: New `apps/api/apps/ai/` directory with models for document storage and vector embeddings
2. **Vector Database Models**:
   - `VectorEmbeddingMixin`: Abstract model with 1536-dim embedding field, model/version tracking
   - `Document`: User-uploaded documents with status tracking (pending → processing → completed → failed)
   - `DocumentChunk`: Text chunks with vector embeddings for semantic search
3. **PGVector Integration**: Extension enabled via migration with IF NOT EXISTS for production safety
4. **HNSW Indexing**: High-performance vector similarity search with cosine distance (m=16, ef_construction=64)
5. **Docker Configuration**: Increased shared memory (1GB) and maintenance_work_mem (256MB) for index builds

## Tasks Completed

### Task 1: Create AI Django app with PGVector models

- **Duration**: ~2 minutes
- **Commit**: `19ec10e`
- **Files**: 5 created
- **What was done**:
  - Installed pgvector (0.4.2) and tiktoken (0.12.0) dependencies via uv
  - Created apps/ai directory structure with migrations package
  - Implemented VectorEmbeddingMixin abstract model with embedding, model, version, and timestamp fields
  - Implemented Document model with upload metadata and embedding status tracking
  - Implemented DocumentChunk model with chunk_index, metadata JSONField, and document FK

### Task 2: Create migrations for PGVector extension and models

- **Duration**: ~2 minutes
- **Commit**: `9e5db87`
- **Files**: 4 created, 1 modified
- **What was done**:
  - Added `apps.ai` to INSTALLED_APPS in base settings
  - Generated 0001_initial migration for Document and DocumentChunk models
  - Created 0002_vector_extension migration with IF NOT EXISTS safety
  - Created 0003_documentchunk_hnsw_index migration (auto-fix: Django doesn't detect abstract model indexes)
  - Applied all migrations successfully
  - Verified PGVector extension enabled in database
  - Verified DocumentChunk table has vector(1536) column

### Task 3: Update Docker Compose for HNSW index builds

- **Duration**: ~1 minute
- **Commit**: `8cd7404`
- **Files**: 3 modified
- **What was done**:
  - Added `shm_size: 1gb` to db service for parallel HNSW index builds
  - Added `command: postgres -c maintenance_work_mem=256MB` override
  - Fixed HNSW index name length (Django 31-char limit): ai_documentchunk_embedding_hnsw_idx → ai_chunk_embedding_hnsw_idx
  - Moved HNSW index declaration from abstract VectorEmbeddingMixin to concrete DocumentChunk model
  - Restarted database and verified settings
  - Verified migrations run without shared memory errors

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] HNSW index not detected from abstract model**

- **Found during**: Task 2 migration generation
- **Issue**: Django's makemigrations doesn't detect HnswIndex when declared in abstract model Meta class
- **Fix**: Created explicit migration 0003_documentchunk_hnsw_index to add the index manually
- **Files modified**: apps/api/apps/ai/migrations/0003_documentchunk_hnsw_index.py (created)
- **Commit**: 9e5db87

**2. [Rule 1 - Bug] Index name exceeds Django's 31-character limit**

- **Found during**: Task 3 model validation
- **Issue**: `ai_documentchunk_embedding_hnsw_idx` is 36 characters, Django enforces 31-char limit
- **Fix**: Shortened to `ai_chunk_embedding_hnsw_idx` (28 characters) in both model and migration
- **Files modified**: apps/api/apps/ai/models.py, apps/api/apps/ai/migrations/0003_documentchunk_hnsw_index.py
- **Commit**: 8cd7404

**3. [Rule 1 - Bug] Django migration state mismatch with abstract model index**

- **Found during**: Task 3 migration validation
- **Issue**: HNSW index in abstract VectorEmbeddingMixin Meta caused Django to think there were pending migrations
- **Fix**: Moved HNSW index declaration from abstract VectorEmbeddingMixin to concrete DocumentChunk model
- **Files modified**: apps/api/apps/ai/models.py
- **Commit**: 8cd7404

All deviations were correctness fixes (Rule 1) applied inline without user consultation.

## Key Decisions Made

1. **HNSW index placement**: Declared in concrete DocumentChunk model instead of abstract VectorEmbeddingMixin
   - **Why**: Django's migration system doesn't detect indexes from abstract model Meta classes
   - **Impact**: Future models inheriting VectorEmbeddingMixin will need explicit HNSW index declarations
   - **Trade-off**: Less DRY but clearer migration tracking

2. **Index naming convention**: Use abbreviated names within 31-character limit
   - **Why**: Django enforces strict index name length limit
   - **Impact**: All future indexes should follow pattern: `{app}_{short_model}_{field}_{type}_idx`
   - **Example**: `ai_chunk_embedding_hnsw_idx` instead of `ai_documentchunk_embedding_hnsw_idx`

3. **PGVector extension creation**: Use IF NOT EXISTS in RunSQL migration
   - **Why**: Production databases may have extension pre-installed by admin with superuser privileges
   - **Impact**: Migration safe for both local dev and production environments
   - **Alternative rejected**: VectorExtension() operation (requires superuser, fails in cloud Postgres)

4. **Docker memory configuration**: 1GB shared memory + 256MB maintenance_work_mem
   - **Why**: HNSW parallel index builds fail with Docker's 64MB default shared memory
   - **Impact**: Template supports larger vector datasets (100K+ documents) without memory errors
   - **Trade-off**: Slightly higher Docker resource usage, but necessary for production-ready indexing

## Verification Results

All verification criteria passed:

- [x] `apps/api/apps/ai/` directory exists with models module
- [x] pgvector (0.4.2) and tiktoken (0.12.0) packages installed
- [x] VectorEmbeddingMixin, Document, and DocumentChunk models defined
- [x] Three migrations exist: 0001_initial, 0002_vector_extension, 0003_documentchunk_hnsw_index
- [x] PGVector extension enabled in database (verified via `SELECT extname FROM pg_extension`)
- [x] DocumentChunk table has vector(1536) column
- [x] HNSW index created with m=16, ef_construction=64, vector_cosine_ops
- [x] docker-compose.yml has shm_size: 1gb and maintenance_work_mem: 256MB
- [x] apps.ai registered in INSTALLED_APPS
- [x] No pending migrations detected by Django

**Database verification**:

```sql
-- Extension enabled
SELECT extname FROM pg_extension WHERE extname = 'vector';
-- Result: vector

-- Table schema correct
\d ai_documentchunk
-- Result: embedding column is vector(1536)

-- HNSW index exists with correct config
SELECT indexname, indexdef FROM pg_indexes WHERE indexname = 'ai_chunk_embedding_hnsw_idx';
-- Result: CREATE INDEX ai_chunk_embedding_hnsw_idx ON public.ai_documentchunk
--         USING hnsw (embedding vector_cosine_ops) WITH (m='16', ef_construction='64')

-- Postgres settings verified
SHOW maintenance_work_mem;
-- Result: 256MB
```

## Self-Check: PASSED

**Files created**:

- [x] apps/api/apps/ai/**init**.py
- [x] apps/api/apps/ai/models.py
- [x] apps/api/apps/ai/migrations/**init**.py
- [x] apps/api/apps/ai/migrations/0001_initial.py
- [x] apps/api/apps/ai/migrations/0002_vector_extension.py
- [x] apps/api/apps/ai/migrations/0003_documentchunk_hnsw_index.py

**Commits exist**:

- [x] 19ec10e: feat(06-01): create AI Django app with PGVector models
- [x] 9e5db87: feat(06-01): create migrations for PGVector extension and models
- [x] 8cd7404: feat(06-01): update Docker Compose for HNSW index builds

**Requirements fulfilled**:

- [x] AI-01: PGVector extension enabled with model mixin for embedding fields
- [x] AI-02: HNSW index migration for vector similarity search

All files and commits verified present. No missing artifacts.

## Technical Notes

### PGVector Configuration

**Embedding dimensions**: 1536 (OpenAI text-embedding-3-small standard)

- Matches OpenAI's current embedding model output
- Future models can use different dimensions by updating VectorField declaration

**HNSW index parameters**:

- `m=16`: Each node connects to 16 neighbors (moderate recall/memory balance)
- `ef_construction=64`: Build quality setting (moderate build time/recall balance)
- `vector_cosine_ops`: Cosine distance operator class (industry standard for text embeddings)

**Performance implications**:

- HNSW provides O(log n) search time with >90% recall
- Index build is one-time cost during embedding generation
- Shared memory and maintenance_work_mem settings prevent build failures on large datasets

### Django Migration Gotchas

**Abstract model indexes**: Django's migration system doesn't detect index definitions in abstract model Meta classes. Always create explicit migrations for pgvector indexes.

**Index name length**: Django enforces PostgreSQL's 31-character limit. Use abbreviations:

- Good: `ai_chunk_embedding_hnsw_idx` (28 chars)
- Bad: `ai_documentchunk_embedding_hnsw_idx` (36 chars)

**Extension creation**: Always use `IF NOT EXISTS` to avoid permission errors:

```python
migrations.RunSQL(
    sql='CREATE EXTENSION IF NOT EXISTS vector',
    reverse_sql='DROP EXTENSION IF EXISTS vector'
)
```

### Next Steps

This plan establishes the database foundation. Upcoming plans will add:

1. **Embedding pipeline**: Celery tasks for chunking and embedding generation (Plan 02)
2. **Vector search API**: Django Ninja Extra endpoints for semantic search (Plan 03)
3. **LangGraph agents**: Q&A RAG agent with guardrails and routing (Plan 04)

The current implementation is ready for these additions - models are in place, indexes are created, and database configuration supports production workloads.

## Related Files

- **Models**: `/Users/soubhratra/workspace/foundation-template/apps/api/apps/ai/models.py`
- **Settings**: `/Users/soubhratra/workspace/foundation-template/apps/api/config/settings/base.py`
- **Docker**: `/Users/soubhratra/workspace/foundation-template/docker-compose.yml`
- **Migrations**: `/Users/soubhratra/workspace/foundation-template/apps/api/apps/ai/migrations/`

## Dependencies Added

```toml
# apps/api/pyproject.toml
dependencies = [
    # ... existing deps ...
    "pgvector==0.4.2",
    "tiktoken==0.12.0",
]
```

**pgvector**: PostgreSQL extension Python client, provides VectorField and HNSW indexing for Django
**tiktoken**: OpenAI's tokenizer library, required for accurate text chunking (upcoming Plan 02)
