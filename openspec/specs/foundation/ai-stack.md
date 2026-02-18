# AI Stack Specification

> Baseline specification for the Foundation Template.
> This document is the source of truth. All implementations must conform to these specs.

## Overview

The AI module provides production-grade scaffolding for agent workflows (LangGraph), vector similarity search (PGVector), and background embedding generation (Celery). The entire module is isolated in `apps/api/apps/ai/` and designed to be cleanly removable by the CLI scaffolder for projects that do not need AI capabilities. No AI code, imports, or dependencies leak into non-AI parts of the codebase.

## Specifications

### Module Isolation Strategy

All AI-related code lives within a single Django app:

```
apps/api/apps/ai/
+-- __init__.py
+-- models.py            # Models with EmbeddingMixin
+-- schemas.py           # Pydantic schemas for AI endpoints
+-- controllers.py       # Ninja Extra controllers for AI endpoints
+-- services.py          # AI service layer (LangGraph invocation, search)
+-- tasks.py             # Celery tasks for background embedding
+-- graphs/              # LangGraph graph definitions
|   +-- __init__.py
|   +-- rag_agent.py     # RAG (Retrieval-Augmented Generation) graph
|   +-- base.py          # Shared graph utilities
+-- tests/
|   +-- __init__.py
|   +-- test_services.py
|   +-- test_graphs.py
|   +-- conftest.py
+-- migrations/
    +-- __init__.py
    +-- 0001_initial.py  # Creates models with vector fields + HNSW indexes
```

**Isolation rules:**

- No other Django app imports from `apps.ai`.
- No AI-specific Python dependencies (langchain, langgraph, openai) in the base requirements. They are in an optional dependency group.
- The `apps.ai` app is conditionally added to `INSTALLED_APPS` via an environment variable or feature flag.
- The EmbeddingMixin lives in `apps.ai.models`, not in `apps.core.models`. If the AI module is removed, the mixin goes with it.
- The PGVector extension migration (`CREATE EXTENSION vector`) lives in `apps.core` (since PGVector is a database-level extension), but the HNSW indexes live in `apps.ai` migrations.

**Removal checklist (for CLI scaffolder):**

1. Delete `apps/api/apps/ai/` directory.
2. Remove `"apps.ai"` from `INSTALLED_APPS`.
3. Remove AI-specific dependencies from `pyproject.toml` (langgraph, openai, tiktoken, etc.).
4. Remove AI endpoints from URL configuration.
5. Remove Celery worker configuration if no other tasks exist.
6. The PGVector extension migration in `apps.core` can optionally remain (harmless) or be removed.

### LangGraph Graph Patterns

#### State Definition

```python
# apps/api/apps/ai/graphs/base.py
from typing import Annotated, TypedDict
from langgraph.graph import add_messages


class AgentState(TypedDict):
    """Base state for all LangGraph graphs in the template."""
    messages: Annotated[list, add_messages]
    context: str | None          # Retrieved documents for RAG
    user_id: int | None          # Current user (for personalization)
    metadata: dict               # Arbitrary metadata
```

#### RAG Agent Graph

```python
# apps/api/apps/ai/graphs/rag_agent.py
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, AIMessage
from .base import AgentState


def retrieve_context(state: AgentState) -> AgentState:
    """Node: Retrieve relevant documents from PGVector."""
    from apps.ai.services import VectorSearchService

    query = state["messages"][-1].content
    service = VectorSearchService()
    documents = service.search(query, limit=5)
    context = "\n\n".join([doc.content for doc in documents])
    return {"context": context}


def generate_response(state: AgentState) -> AgentState:
    """Node: Generate response using LLM with retrieved context."""
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(model="gpt-4o-mini")
    system_prompt = f"""Answer the user's question using the following context.
If the context doesn't contain relevant information, say so.

Context:
{state.get('context', 'No context available.')}"""

    messages = [{"role": "system", "content": system_prompt}] + state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response]}


def should_retrieve(state: AgentState) -> str:
    """Conditional edge: decide whether to retrieve or respond directly."""
    last_message = state["messages"][-1]
    if isinstance(last_message, HumanMessage):
        return "retrieve"
    return "respond"


def build_rag_graph():
    """Build the RAG agent graph."""
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("retrieve", retrieve_context)
    graph.add_node("generate", generate_response)

    # Add edges
    graph.add_conditional_edges(START, should_retrieve, {
        "retrieve": "retrieve",
        "respond": "generate",
    })
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", END)

    return graph.compile()
```

#### Compiled Graph Reuse

Graphs MUST be compiled once at module level and reused across requests. Recompiling per-request adds unnecessary overhead.

```python
# apps/api/apps/ai/graphs/rag_agent.py

# Compile once at module level
rag_graph = build_rag_graph()

# In controller/service, import the compiled instance:
# from apps.ai.graphs.rag_agent import rag_graph
# result = rag_graph.invoke({"messages": [HumanMessage(content=query)]})
```

#### Checkpoint Persistence (LangGraph)

For durable conversation state across requests, use `langgraph-checkpoint-postgres`:

```python
# apps/api/apps/ai/graphs/base.py
from langgraph.checkpoint.postgres import PostgresSaver
from django.conf import settings


def get_checkpointer():
    """Get a Postgres-backed checkpointer for durable conversation state."""
    return PostgresSaver.from_conn_string(settings.DATABASE_URL)


def build_graph_with_persistence(graph_builder):
    """Compile a graph with Postgres checkpoint persistence."""
    checkpointer = get_checkpointer()
    return graph_builder.compile(checkpointer=checkpointer)
```

```python
# Invoking a graph with thread-based persistence
config = {"configurable": {"thread_id": f"user-{user_id}-session-{session_id}"}}
result = rag_graph.invoke({"messages": [HumanMessage(content=query)]}, config=config)
```

**Checkpoint rules:**

- **Development:** In-memory checkpointer is acceptable for testing.
- **Production:** MUST use `langgraph-checkpoint-postgres`. Never use in-memory in production.
- **Thread IDs:** Use deterministic IDs based on user + session to enable conversation continuity.

#### Graph Design Rules

| Rule                                            | Rationale                                 |
| ----------------------------------------------- | ----------------------------------------- |
| Each graph is a single file in `graphs/`        | Easy to understand, test, and replace     |
| State is a TypedDict                            | Type safety, IDE support, clear contract  |
| Nodes are plain functions                       | Testable without the graph framework      |
| LLM calls are in nodes, not edges               | Separation of logic and control flow      |
| External service calls use dependency injection | Testable with mocks                       |
| Graph is compiled once at module level          | Avoids recompilation overhead per request |

#### LangGraph Implementation Patterns

##### Intent Detection Strategy

**Pattern:** Use keyword matching instead of LLM-based intent detection.

**Rationale:** Avoids API dependency, faster, lower cost, sufficient for basic routing.

**Implementation:**

```python
def detect_intent(query: str) -> str:
    """Simple keyword-based intent detection."""
    query_lower = query.lower()
    if any(word in query_lower for word in ["calculate", "compute", "math"]):
        return "calculator"
    elif any(word in query_lower for word in ["search", "find", "lookup"]):
        return "search"
    else:
        return "qa"
```

**Decision:** Phase 06-ai-module

##### Tool Security: Safe Calculator

**Pattern:** Use AST parsing to prevent code injection attacks.
**Anti-Pattern:** Never use Python's built-in string evaluation functions that execute arbitrary code.

**Safe Implementation:**

```python
import ast
import operator

def safe_calculate(expression: str) -> float:
    """Safely evaluate math expressions using AST."""
    operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
    }
    def eval_node(node):
        if isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.BinOp):
            return operators[type(node.op)](eval_node(node.left), eval_node(node.right))
        else:
            raise ValueError("Unsupported operation")
    tree = ast.parse(expression, mode='eval')
    return eval_node(tree.body)
```

**Decision:** Phase 06-ai-module

##### Authentication Requirements

**Pattern:** Require `OPENAI_API_KEY` at runtime for LLM tools.

```python
def generate_response(state: AgentState) -> AgentState:
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not configured")
    # Proceed with LLM call
```

**Benefit:** Fails fast if API key missing.
**Decision:** Phase 06-ai-module

##### Graceful Error Handling

**Pattern:** Return degraded responses instead of crashing.

```python
def generate_response(state: AgentState) -> AgentState:
    try:
        llm = ChatOpenAI(model="gpt-4o-mini")
        response = llm.invoke(state["messages"])
        return {"messages": [response]}
    except Exception as e:
        logger.error(f"LLM failed: {e}")
        fallback = AIMessage(content="I'm having trouble. Please try again.")
        return {"messages": [fallback]}
```

**Decision:** Phase 06-ai-module

### PGVector Setup

#### Extension Migration

```python
# apps/api/apps/core/migrations/0001_enable_pgvector.py
from django.db import migrations

class Migration(migrations.Migration):
    dependencies = []
    operations = [
        migrations.RunSQL(
            sql="CREATE EXTENSION IF NOT EXISTS vector;",
            reverse_sql="DROP EXTENSION IF EXISTS vector;",
        ),
    ]
```

**Implementation Note:** The `IF NOT EXISTS` clause is critical for production deployments where the PGVector extension may be pre-installed at the database level. Without it, the migration would fail with a permission error if the extension already exists. _(Decision: Phase 06-ai-module)_

#### Embedding Model

```python
# apps/api/apps/ai/models.py
from django.db import models
from pgvector.django import VectorField, HnswIndex
from apps.core.models import BaseModel


class Document(BaseModel):
    """
    Document model with vector embedding for similarity search.
    """
    title = models.CharField(max_length=500)
    content = models.TextField()
    source_url = models.URLField(blank=True, null=True)

    # Embedding fields
    embedding = VectorField(
        dimensions=1536,
        null=True,
        blank=True,
        help_text="Vector embedding for similarity search (text-embedding-3-small)",
    )
    embedding_model = models.CharField(
        max_length=100,
        default="text-embedding-3-small",
    )
    embedded_at = models.DateTimeField(null=True, blank=True)

    # Content hash for change detection (avoid re-embedding unchanged content)
    content_hash = models.CharField(max_length=64, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            HnswIndex(
                name="document_embedding_idx",
                fields=["embedding"],
                m=16,
                ef_construction=64,
                opclasses=["vector_cosine_ops"],
            ),
        ]

    def __str__(self):
        return self.title
```

**Implementation Note:** The HNSW index must be declared in the concrete model's `Meta.indexes`, not in an abstract base model mixin. Django's migration system requires explicit index declarations in concrete models to generate the proper SQL. _(Decision: Phase 06-ai-module)_

#### HNSW Index Configuration

| Parameter       | Value             | Rationale                                                                                                        |
| --------------- | ----------------- | ---------------------------------------------------------------------------------------------------------------- |
| Index type      | HNSW              | No training needed, works with incremental inserts. Strictly better than IVFFlat for this use case.              |
| m               | 16                | Controls graph connectivity. Default is fine for < 1M vectors. Higher = better recall, more memory.              |
| ef_construction | 64                | Controls index build quality. Default is fine for < 1M vectors. Higher = better recall, slower build.            |
| Operator class  | vector_cosine_ops | Cosine similarity is standard for OpenAI/Anthropic embeddings. Must match the distance function used in queries. |

**GIVEN** the Document model has an HNSW index on the embedding field with vector_cosine_ops
**WHEN** a cosine similarity search is performed with a query vector
**THEN** PostgreSQL uses the HNSW index for approximate nearest neighbor search
**AND** EXPLAIN ANALYZE shows an index scan (not sequential scan)
**AND** query time is < 50ms for tables with < 100K rows

#### Vector Search Service

```python
# apps/api/apps/ai/services.py
from pgvector.django import CosineDistance
from django.db import connection
from .models import Document


class VectorSearchService:
    """Service for vector similarity search using PGVector."""

    def search(
        self,
        query_embedding: list[float],
        limit: int = 10,
        distance_threshold: float = 0.5,
    ) -> list[Document]:
        """
        Find documents similar to the query embedding.
        Uses cosine distance (lower = more similar).
        """
        # Set HNSW search parameters for this query
        with connection.cursor() as cursor:
            cursor.execute("SET hnsw.ef_search = 100")

        return (
            Document.objects
            .filter(embedding__isnull=False)
            .annotate(distance=CosineDistance("embedding", query_embedding))
            .filter(distance__lt=distance_threshold)
            .order_by("distance")[:limit]
        )

    def search_by_text(self, query: str, limit: int = 10) -> list[Document]:
        """Search by text query (generates embedding first)."""
        embedding = self._generate_embedding(query)
        return self.search(embedding, limit=limit)

    def _generate_embedding(self, text: str) -> list[float]:
        """Generate embedding using the configured model."""
        from openai import OpenAI
        client = OpenAI()
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=text,
        )
        return response.data[0].embedding
```

### Embedding Pipeline (Celery Background Task)

```python
# apps/api/apps/ai/tasks.py
import hashlib
from celery import shared_task
from django.utils import timezone


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
)
def generate_embedding(self, document_id: int):
    """
    Generate vector embedding for a document.
    Runs as a Celery background task to avoid blocking request cycle.
    Idempotent: checks content hash to skip unchanged content.
    """
    from .models import Document
    from openai import OpenAI

    document = Document.objects.get(id=document_id)

    # Check if content has changed since last embedding
    content_hash = hashlib.sha256(document.content.encode()).hexdigest()
    if document.content_hash == content_hash and document.embedding is not None:
        return  # Content unchanged, skip re-embedding

    # Generate embedding
    client = OpenAI()
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=document.content,
    )

    # Store embedding and metadata
    document.embedding = response.data[0].embedding
    document.embedding_model = "text-embedding-3-small"
    document.embedded_at = timezone.now()
    document.content_hash = content_hash
    document.save(update_fields=[
        "embedding", "embedding_model", "embedded_at", "content_hash"
    ])


@shared_task
def bulk_generate_embeddings(document_ids: list[int]):
    """
    Generate embeddings for multiple documents.
    Dispatches individual tasks for parallel processing.
    """
    for doc_id in document_ids:
        generate_embedding.delay(doc_id)
```

**GIVEN** a new document is created via the API
**WHEN** the controller saves the document
**THEN** a Celery task `generate_embedding` is dispatched asynchronously
**AND** the API returns 201 immediately (does not wait for embedding)
**AND** the Celery worker generates the embedding in the background
**AND** the document's embedding field is populated within seconds
**AND** the document becomes searchable via vector similarity

**GIVEN** a document's content is updated
**WHEN** the `generate_embedding` task runs
**THEN** it computes a SHA-256 hash of the new content
**AND** compares it to the stored `content_hash`
**AND** if the hash differs, generates a new embedding
**AND** if the hash matches, skips re-embedding (idempotent)

**GIVEN** the embedding API call fails (rate limit, network error)
**WHEN** the Celery task raises an exception
**THEN** Celery retries the task up to 3 times with 60-second delay
**AND** if all retries fail, the task is marked as failed
**AND** the document's embedding remains null (or stale)

#### Document Chunking Strategy

For large documents that exceed embedding model token limits, implement chunking:

**Strategy:**

- **Chunk Size:** 512 tokens
- **Overlap:** 200 tokens
- **Tokenizer:** tiktoken `cl100k_base` (OpenAI's tokenizer)

**Rationale:** Balances granularity with semantic context. Overlap ensures no information is lost at chunk boundaries, improving search quality for queries that span chunk edges.

**Implementation:**

```python
# apps/api/apps/ai/services.py
import tiktoken

def chunk_text(text: str, chunk_size: int = 512, overlap: int = 200) -> list[str]:
    """
    Split text into overlapping chunks using tiktoken.
    """
    encoding = tiktoken.get_encoding("cl100k_base")
    tokens = encoding.encode(text)

    chunks = []
    start = 0
    while start < len(tokens):
        end = start + chunk_size
        chunk_tokens = tokens[start:end]
        chunk_text = encoding.decode(chunk_tokens)
        chunks.append(chunk_text)
        start += (chunk_size - overlap)  # Move forward with overlap

    return chunks
```

**Decision:** Phase 06-ai-module

#### Idempotent Task Design

**Pattern:** Delete existing chunks before processing a document.

**Benefits:**

- Safe task retries (can re-run without creating duplicates)
- Re-embedding after model upgrades
- Content updates don't leave stale chunks

**Implementation:**

```python
@shared_task
def process_document_chunks(document_id: int):
    """
    Process document into chunks and generate embeddings.
    Idempotent: clears existing chunks first.
    """
    from .models import Document, DocumentChunk

    document = Document.objects.get(id=document_id)

    # Delete existing chunks (idempotent)
    DocumentChunk.objects.filter(document=document).delete()

    # Generate new chunks
    chunks = chunk_text(document.content)
    for i, chunk_text in enumerate(chunks):
        chunk = DocumentChunk.objects.create(
            document=document,
            content=chunk_text,
            sequence=i,
        )
        # Generate embedding for chunk
        generate_chunk_embedding.delay(chunk.id)
```

**Decision:** Phase 06-ai-module

### Vector Search API Patterns

```python
# apps/api/apps/ai/controllers.py
from ninja_extra import api_controller, route
from ninja_extra.permissions import IsAuthenticated
from .schemas import SearchIn, SearchResultOut, DocumentCreateIn, DocumentOut
from .services import VectorSearchService


@api_controller("/ai", tags=["AI"])
class AIController:
    def __init__(self):
        self.search_service = VectorSearchService()

    @route.post("/search", response=list[SearchResultOut], permissions=[IsAuthenticated])
    def semantic_search(self, request, payload: SearchIn):
        """Search documents by semantic similarity."""
        results = self.search_service.search_by_text(
            query=payload.query,
            limit=payload.limit,
        )
        return [
            SearchResultOut(
                id=doc.id,
                title=doc.title,
                content=doc.content[:500],  # Truncate for preview
                distance=doc.distance,
            )
            for doc in results
        ]
```

```python
# apps/api/apps/ai/schemas.py
from pydantic import BaseModel, Field


class SearchIn(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    limit: int = Field(default=10, ge=1, le=50)


class SearchResultOut(BaseModel):
    id: int
    title: str
    content: str
    distance: float  # Cosine distance (0 = identical, 1 = orthogonal)

    class Config:
        from_attributes = True
```

### SSE Streaming for Chat Responses

Long-running LLM responses MUST be streamed via Server-Sent Events (SSE) to avoid blocking and to improve perceived latency.

```python
# apps/api/apps/ai/controllers.py
from django.http import StreamingHttpResponse
from ninja_extra import api_controller, route
from ninja_extra.permissions import IsAuthenticated
from .schemas import ChatIn
from .graphs.rag_agent import rag_graph
from langchain_core.messages import HumanMessage


@api_controller("/ai", tags=["AI"])
class AIController:

    @route.post("/chat/stream", permissions=[IsAuthenticated])
    def chat_stream(self, request, payload: ChatIn):
        """Stream a chat response via SSE."""

        def event_stream():
            config = {
                "configurable": {
                    "thread_id": f"user-{request.user.id}"
                }
            }
            for event in rag_graph.stream(
                {"messages": [HumanMessage(content=payload.message)]},
                config=config,
                stream_mode="messages",
            ):
                # Each event is a token or message chunk
                if hasattr(event, "content") and event.content:
                    yield f"data: {event.content}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingHttpResponse(
            event_stream(),
            content_type="text/event-stream",
        )
```

**Streaming rules:**

- Use `stream_mode="messages"` for token-level streaming.
- Client receives `text/event-stream` content type.
- Stream ends with `data: [DONE]\n\n` sentinel.
- Non-streaming endpoints use `graph.invoke()`, streaming uses `graph.stream()`.

### LLM Provider Abstraction

The template defaults to OpenAI but LLM providers are swappable. All LLM instantiation goes through a factory pattern:

```python
# apps/api/apps/ai/graphs/base.py
from django.conf import settings
from langchain_openai import ChatOpenAI


def get_llm(model: str | None = None, temperature: float = 0.0):
    """Factory for LLM instances. Swap provider here."""
    return ChatOpenAI(
        model=model or settings.AI_DEFAULT_MODEL,
        temperature=temperature,
    )
```

```python
# config/settings/base.py
AI_DEFAULT_MODEL = env("AI_DEFAULT_MODEL", default="gpt-4o-mini")
AI_EMBEDDING_MODEL = env("AI_EMBEDDING_MODEL", default="text-embedding-3-small")
AI_EMBEDDING_DIMENSIONS = env.int("AI_EMBEDDING_DIMENSIONS", default=1536)
```

**Rule:** Never hardcode model names in graph nodes. Always read from settings or pass as parameters. This allows projects to switch to Anthropic (`langchain_anthropic.ChatAnthropic`) or other providers by changing the factory function and env vars.

### AI Workflow Scenarios

**GIVEN** a user sends a question to the RAG endpoint
**WHEN** the AI controller receives the request
**THEN** the controller invokes the compiled RAG graph with the user's message
**AND** the retrieve node searches PGVector for relevant documents
**AND** the generate node calls the LLM with retrieved context
**AND** the response is returned to the user as JSON

**GIVEN** no relevant documents exist in the vector store
**WHEN** the RAG graph's retrieve node finds no results above the similarity threshold
**THEN** the context is set to "No context available"
**AND** the generate node produces a response acknowledging lack of relevant information
**AND** the response is honest about the limitation

**GIVEN** a streaming response is required for the chat interface
**WHEN** the AI controller invokes the graph with streaming enabled
**THEN** the response is streamed via Server-Sent Events (SSE)
**AND** each token is sent as a separate event
**AND** the client renders tokens as they arrive

### Celery Configuration for AI Tasks

```python
# config/settings/base.py
CELERY_BROKER_URL = env("REDIS_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = "django-db"  # Store results in PostgreSQL
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"

# Task routing for AI tasks
CELERY_TASK_ROUTES = {
    "apps.ai.tasks.*": {"queue": "ai"},
}
```

**Implementation Note:** `CELERY_RESULT_BACKEND = "django-db"` stores task results in PostgreSQL using the `django-celery-results` package. This keeps all data centralized without requiring a separate result store like Redis. _(Decision: Phase 06-ai-module)_

```python
# config/celery.py
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("foundation")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
```

## Constraints

1. **AI module is fully removable.** Deleting `apps/api/apps/ai/` and removing it from INSTALLED_APPS must not break any other part of the application.
2. **No AI imports outside apps.ai.** No other Django app may import from `apps.ai`. If shared utilities are needed, they go in `apps.core`.
3. **HNSW only.** Do not use IVFFlat indexes. HNSW requires no training data and works with incremental inserts.
4. **Operator class must match distance function.** `vector_cosine_ops` for cosine similarity searches. Using the wrong operator class silently defeats the index.
5. **Embeddings generated asynchronously.** Never generate embeddings in the request cycle. Always use Celery tasks. Embedding generation adds 200-500ms latency per request.
6. **Embedding dimension must be explicit.** VectorField(dimensions=1536) -- never omit. Document the model name alongside the dimension.
7. **Content hash for idempotency.** Always check content_hash before re-embedding. Avoids unnecessary API calls and costs.
8. **LLM API keys in environment only.** OpenAI/Anthropic API keys in `.env`, never committed. Validated on startup.
9. **LangGraph checkpoint persistence.** Use `langgraph-checkpoint-postgres` for durable conversation state in production. Never use in-memory checkpointer in production. Thread IDs must be deterministic (user + session based).
10. **LLM model names never hardcoded.** All model names read from Django settings or environment variables. This enables provider swaps without code changes.
11. **AI dependencies are optional.** `langgraph`, `langchain-openai`, `openai`, `tiktoken`, `langgraph-checkpoint-postgres` live in an optional dependency group in `pyproject.toml`.

## References

- `.planning/research/ARCHITECTURE.md` -- AI module data flow, embedding pipeline diagram
- `.planning/research/PITFALLS.md` -- Pitfall #5: PGVector wrong index type
- `.planning/research/STACK.md` -- LangGraph, PGVector, Celery configuration
