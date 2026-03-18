## Requirements

### Requirement: Module Isolation and Clean Removal

The AI module SHALL be completely isolated in a single Django app and designed for clean removal by the CLI scaffolder.

#### Scenario: AI module contained in single app

- **WHEN** the template is initialized with the AI module
- **THEN** all AI-related code MUST reside in `apps/api/apps/ai/` directory
- **AND** no other Django app MUST import from `apps.ai`
- **AND** AI-specific Python dependencies MUST be in an optional dependency group
- **AND** the `apps.ai` app MUST be conditionally added to `INSTALLED_APPS`

#### Scenario: AI module removed from template

- **WHEN** a developer removes the AI module using the CLI scaffolder
- **THEN** deleting the `apps/api/apps/ai/` directory MUST NOT break other parts of the application
- **AND** removing `"apps.ai"` from `INSTALLED_APPS` MUST NOT cause startup errors
- **AND** removing AI dependencies from `pyproject.toml` MUST NOT affect non-AI functionality
- **AND** the application MUST run correctly without any AI capabilities

### Requirement: PGVector Extension with HNSW Indexes

The system SHALL use PostgreSQL PGVector extension with HNSW indexes for efficient vector similarity search.

#### Scenario: PGVector extension enabled in database

- **WHEN** Django migrations are applied
- **THEN** the PGVector extension MUST be created with `CREATE EXTENSION IF NOT EXISTS vector`
- **AND** the extension migration MUST be in `apps.core` (database-level extension)
- **AND** HNSW index migrations MUST be in `apps.ai` (module-specific indexes)
- **AND** the extension MUST be safely reversible with `DROP EXTENSION IF EXISTS vector`

#### Scenario: Document model with HNSW vector index

- **WHEN** a Document model is defined with an embedding field
- **THEN** the embedding field MUST use `VectorField` with explicit dimensions (e.g., 1536)
- **AND** an HNSW index MUST be created on the embedding field
- **AND** the index MUST use `vector_cosine_ops` operator class
- **AND** the index MUST specify m=16 and ef_construction=64 parameters

#### Scenario: Vector search uses HNSW index

- **WHEN** a cosine similarity search is performed with a query vector
- **THEN** PostgreSQL MUST use the HNSW index for approximate nearest neighbor search
- **AND** query execution plan MUST show index scan (not sequential scan)
- **AND** query time MUST be under 50ms for tables with fewer than 100K rows
- **AND** search parameters MUST be tunable via `SET hnsw.ef_search` setting

### Requirement: LangGraph Agent Scaffold

The AI module SHALL provide a production-grade LangGraph agent scaffold with example RAG graph implementation.

#### Scenario: RAG agent graph defined with state

- **WHEN** the RAG agent graph is initialized
- **THEN** the graph MUST define a state using TypedDict with at least `messages`, `context`, and `user_id` fields
- **AND** the state MUST use the `add_messages` annotation for message handling
- **AND** each node MUST be a plain function that accepts and returns state
- **AND** the graph MUST be compiled once and reused across requests

#### Scenario: RAG agent retrieves context and generates response

- **WHEN** a user sends a question to the RAG endpoint
- **THEN** the retrieve node MUST search PGVector for relevant documents using vector similarity
- **AND** the retrieved documents MUST be formatted into a context string
- **AND** the generate node MUST call the LLM with the context and user's message
- **AND** the LLM response MUST be returned as JSON to the user

#### Scenario: RAG agent handles missing context gracefully

- **WHEN** no relevant documents exist above the similarity threshold
- **THEN** the context MUST be set to "No context available"
- **AND** the LLM MUST be informed that no relevant information was found
- **AND** the response MUST acknowledge the limitation honestly

### Requirement: Celery Embedding Pipeline

The AI module SHALL generate vector embeddings asynchronously using Celery to avoid blocking request cycles.

#### Scenario: Embedding task dispatched after document creation

- **WHEN** a new document is created via the API
- **THEN** the `generate_embedding` Celery task MUST be dispatched asynchronously
- **AND** the API MUST return 201 immediately without waiting for embedding
- **AND** the embedding MUST be generated in the background by a Celery worker
- **AND** the document MUST become searchable after embedding is stored

#### Scenario: Embedding generation with content hash check

- **WHEN** the embedding generation task runs
- **THEN** the task MUST compute a SHA-256 hash of the document content
- **AND** the task MUST compare the hash with the stored `content_hash`
- **AND** if the hash matches and embedding exists, the task MUST skip re-embedding
- **AND** if the hash differs, the task MUST generate a new embedding
- **AND** the new embedding, model name, timestamp, and hash MUST be stored

#### Scenario: Embedding task retries on API failure

- **WHEN** the embedding API call fails with rate limit or network error
- **THEN** the task MUST raise an exception
- **AND** Celery MUST automatically retry up to 3 times with 60-second delays
- **AND** if all retries fail, the task MUST be marked as failed
- **AND** the document's embedding field MUST remain null or contain stale data

### Requirement: Vector Search API Endpoint

The AI module SHALL provide a vector search API endpoint for semantic similarity queries.

#### Scenario: Semantic search by text query

- **WHEN** an authenticated user sends a search query via POST to `/api/v1/ai/search`
- **THEN** the service MUST generate an embedding for the query text
- **AND** the service MUST perform cosine distance search against document embeddings
- **AND** the service MUST filter documents below the distance threshold
- **AND** the service MUST return top N results ordered by similarity (distance ascending)
- **AND** each result MUST include document ID, title, truncated content, and distance score

#### Scenario: Vector search with tuned HNSW parameters

- **WHEN** a vector search is executed
- **THEN** the service MUST set `hnsw.ef_search` parameter for the query
- **AND** the search MUST use `CosineDistance` annotation for distance calculation
- **AND** the search MUST filter out documents with null embeddings
- **AND** the search MUST limit results to the requested number (default 10, max 50)

### Requirement: Embedding Model Metadata Tracking

The system SHALL track embedding model metadata to support model versioning and change detection.

#### Scenario: Embedding metadata stored with vector

- **WHEN** an embedding is generated and stored
- **THEN** the document MUST store the embedding vector in the VectorField
- **AND** the document MUST store the model name (e.g., "text-embedding-3-small")
- **AND** the document MUST store the embedding timestamp (`embedded_at`)
- **AND** the document MUST store a SHA-256 hash of the content (`content_hash`)
- **AND** all four fields MUST be updated atomically using `update_fields`
