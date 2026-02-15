# AI Module Implementation

> Baseline specification for the Foundation Template.
> This document is the source of truth. All implementations must conform to these specs.

## Overview

This spec covers the Django-specific implementation of the AI module. It complements `openspec/specs/foundation/ai-stack.md` (architecture-level patterns) with implementation details: Django app configuration, dependency management, conditional loading, testing strategies, and the embedding ingestion pipeline. The entire AI module lives in `apps/api/apps/ai/` and is designed to be cleanly removable.

## Specifications

### Django App Configuration

```python
# apps/api/apps/ai/apps.py
from django.apps import AppConfig


class AiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.ai"
    verbose_name = "AI Module"

    def ready(self):
        # Import signal handlers for auto-embedding on document save
        import apps.ai.signals  # noqa: F401
```

### Conditional INSTALLED_APPS Loading

The AI module is conditionally included via environment variable:

```python
# apps/api/config/settings/base.py
INSTALLED_APPS = [
    # Django built-ins
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party
    "ninja_extra",
    "corsheaders",
    "allauth",
    "allauth.account",

    # Project apps
    "apps.core",
    "apps.accounts",
]

# Conditionally add AI module
if env.bool("ENABLE_AI_MODULE", default=True):
    INSTALLED_APPS += ["apps.ai"]
```

**GIVEN** `ENABLE_AI_MODULE=false` in the environment
**WHEN** Django starts up
**THEN** the `apps.ai` app is NOT loaded
**AND** no AI-related database tables are created
**AND** no AI endpoints appear in the OpenAPI spec
**AND** the rest of the application works normally

### Dependency Group in pyproject.toml

```toml
# apps/api/pyproject.toml
[project]
dependencies = [
    "django>=5.1,<6.0",
    "django-ninja-extra>=0.21",
    "django-allauth>=65.0",
    "django-cors-headers>=4.0",
    "django-environ>=0.11",
    "psycopg[binary]>=3.0",
    "gunicorn>=22.0",
    "whitenoise>=6.0",
    "celery>=5.0",
    "redis>=5.0",
    "pgvector>=0.3",
]

[project.optional-dependencies]
ai = [
    "langgraph>=0.2",
    "langchain-openai>=0.2",
    "langchain-core>=0.3",
    "langgraph-checkpoint-postgres>=2.0",
    "openai>=1.0",
    "tiktoken>=0.7",
]
dev = [
    "ruff>=0.8",
    "mypy>=1.0",
    "django-stubs>=5.0",
    "pytest>=8.0",
    "pytest-django>=4.0",
    "pytest-cov>=5.0",
    "factory-boy>=3.0",
]
```

```bash
# Install with AI dependencies
uv sync --extra ai

# Install without AI
uv sync
```

### Auto-Embedding via Django Signals

When a document is created or its content changes, automatically dispatch a Celery task:

```python
# apps/api/apps/ai/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Document
from .tasks import generate_embedding


@receiver(post_save, sender=Document)
def trigger_embedding_on_save(sender, instance, created, **kwargs):
    """Dispatch embedding task when document content changes."""
    if created:
        generate_embedding.delay(instance.id)
    elif instance.tracker.has_changed("content"):
        # Re-embed only if content actually changed
        generate_embedding.delay(instance.id)
```

**Note:** The `tracker.has_changed()` pattern requires `django-model-utils` `FieldTracker` or a manual content hash comparison. The content hash approach (see `foundation/ai-stack.md`) is preferred to avoid the extra dependency:

```python
# Alternative: hash-based change detection in the task itself
# (already implemented in apps/api/apps/ai/tasks.py)
# The signal simply dispatches on every save; the task checks the hash.
@receiver(post_save, sender=Document)
def trigger_embedding_on_save(sender, instance, **kwargs):
    """Dispatch embedding task on every save. Task handles idempotency via content hash."""
    generate_embedding.delay(instance.id)
```

### AI Endpoint Patterns

#### Semantic Search Endpoint

```python
# apps/api/apps/ai/controllers.py
from ninja_extra import api_controller, route, ControllerBase
from ninja_extra.permissions import IsAuthenticated

from .schemas import SearchIn, SearchResultOut, ChatIn, ChatOut, DocumentCreateIn, DocumentOut
from .services import VectorSearchService, DocumentService
from .tasks import generate_embedding


@api_controller("/ai", tags=["AI"], permissions=[IsAuthenticated])
class AIController(ControllerBase):

    def __init__(self):
        self.search_service = VectorSearchService()
        self.document_service = DocumentService()

    @route.post("/search", response=list[SearchResultOut], url_name="ai-search")
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
                content=doc.content[:500],
                distance=doc.distance,
            )
            for doc in results
        ]

    @route.post("/documents", response={201: DocumentOut}, url_name="ai-document-create")
    def create_document(self, request, payload: DocumentCreateIn):
        """Create a document and dispatch async embedding generation."""
        document = self.document_service.create_document(
            user=request.user,
            data=payload,
        )
        # Embedding generated asynchronously via signal or explicit dispatch
        generate_embedding.delay(document.id)
        return 201, document

    @route.post("/chat", response=ChatOut, url_name="ai-chat")
    def chat(self, request, payload: ChatIn):
        """Non-streaming RAG chat endpoint."""
        from .graphs.rag_agent import rag_graph
        from langchain_core.messages import HumanMessage

        config = {"configurable": {"thread_id": f"user-{request.user.id}"}}
        result = rag_graph.invoke(
            {"messages": [HumanMessage(content=payload.message)], "user_id": request.user.id},
            config=config,
        )
        last_message = result["messages"][-1]
        return ChatOut(response=last_message.content)
```

#### AI Schemas

```python
# apps/api/apps/ai/schemas.py
from pydantic import BaseModel, Field
from datetime import datetime


class SearchIn(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    limit: int = Field(default=10, ge=1, le=50)


class SearchResultOut(BaseModel):
    id: int
    title: str
    content: str
    distance: float

    class Config:
        from_attributes = True


class DocumentCreateIn(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    content: str = Field(min_length=1)
    source_url: str | None = None


class DocumentOut(BaseModel):
    id: int
    title: str
    content: str
    source_url: str | None
    embedding_model: str
    embedded_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class ChatOut(BaseModel):
    response: str
```

### AI Service Layer

```python
# apps/api/apps/ai/services.py
import hashlib
from django.conf import settings
from django.db import connection
from pgvector.django import CosineDistance

from .models import Document
from .schemas import DocumentCreateIn


class VectorSearchService:
    """Vector similarity search using PGVector."""

    def search(
        self,
        query_embedding: list[float],
        limit: int = 10,
        distance_threshold: float = 0.5,
    ) -> list[Document]:
        # Tune HNSW search quality for this query
        with connection.cursor() as cursor:
            cursor.execute("SET hnsw.ef_search = 100")

        return list(
            Document.objects
            .filter(embedding__isnull=False)
            .annotate(distance=CosineDistance("embedding", query_embedding))
            .filter(distance__lt=distance_threshold)
            .order_by("distance")[:limit]
        )

    def search_by_text(self, query: str, limit: int = 10) -> list[Document]:
        embedding = self._generate_embedding(query)
        return self.search(embedding, limit=limit)

    def _generate_embedding(self, text: str) -> list[float]:
        from openai import OpenAI
        client = OpenAI()
        response = client.embeddings.create(
            model=getattr(settings, "AI_EMBEDDING_MODEL", "text-embedding-3-small"),
            input=text,
        )
        return response.data[0].embedding


class DocumentService:
    """CRUD for AI documents."""

    def create_document(self, user, data: DocumentCreateIn) -> Document:
        content_hash = hashlib.sha256(data.content.encode()).hexdigest()
        return Document.objects.create(
            title=data.title,
            content=data.content,
            source_url=data.source_url,
            content_hash=content_hash,
        )
```

### Testing AI Components

#### Testing Graphs (Unit)

```python
# apps/api/apps/ai/tests/test_graphs.py
from unittest.mock import patch, MagicMock
from langchain_core.messages import HumanMessage, AIMessage

from apps.ai.graphs.rag_agent import retrieve_context, generate_response


class TestRetrieveContextNode:
    """Test graph nodes as plain functions (no graph framework needed)."""

    @patch("apps.ai.services.VectorSearchService.search")
    def test_retrieve_returns_context(self, mock_search):
        mock_doc = MagicMock()
        mock_doc.content = "Relevant document content"
        mock_search.return_value = [mock_doc]

        state = {
            "messages": [HumanMessage(content="test query")],
            "context": None,
            "user_id": 1,
            "metadata": {},
        }
        result = retrieve_context(state)
        assert result["context"] == "Relevant document content"


class TestGenerateResponseNode:
    @patch("langchain_openai.ChatOpenAI.invoke")
    def test_generate_returns_ai_message(self, mock_invoke):
        mock_invoke.return_value = AIMessage(content="Generated answer")

        state = {
            "messages": [HumanMessage(content="test")],
            "context": "Some context",
            "user_id": 1,
            "metadata": {},
        }
        result = generate_response(state)
        assert len(result["messages"]) == 1
        assert result["messages"][0].content == "Generated answer"
```

#### Testing Vector Search (Integration)

```python
# apps/api/apps/ai/tests/test_services.py
import pytest
from apps.ai.models import Document
from apps.ai.services import VectorSearchService


@pytest.mark.django_db
class TestVectorSearchService:
    """Integration tests requiring a Postgres database with PGVector."""

    def test_search_returns_similar_documents(self):
        # Create test document with a known embedding
        doc = Document.objects.create(
            title="Test Document",
            content="Test content",
            embedding=[0.1] * 1536,  # Dummy 1536-dim vector
        )

        service = VectorSearchService()
        # Search with a similar vector
        results = service.search(
            query_embedding=[0.1] * 1536,
            limit=5,
            distance_threshold=0.5,
        )
        assert len(results) >= 1
        assert results[0].id == doc.id

    def test_search_excludes_distant_documents(self):
        Document.objects.create(
            title="Distant",
            content="Not relevant",
            embedding=[0.9] * 1536,
        )

        service = VectorSearchService()
        results = service.search(
            query_embedding=[0.1] * 1536,
            limit=5,
            distance_threshold=0.1,  # Very tight threshold
        )
        assert len(results) == 0
```

#### Testing Celery Tasks

```python
# apps/api/apps/ai/tests/test_tasks.py
import pytest
from unittest.mock import patch, MagicMock
from apps.ai.tasks import generate_embedding


@pytest.mark.django_db
class TestGenerateEmbeddingTask:
    @patch("openai.OpenAI")
    def test_generates_and_stores_embedding(self, mock_openai_cls):
        from apps.ai.models import Document

        doc = Document.objects.create(title="Test", content="Test content")

        # Mock OpenAI response
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1] * 1536)]
        mock_client.embeddings.create.return_value = mock_response

        # Run task synchronously (not via Celery broker)
        generate_embedding(doc.id)

        doc.refresh_from_db()
        assert doc.embedding is not None
        assert doc.embedded_at is not None
        assert doc.content_hash != ""

    @patch("openai.OpenAI")
    def test_skips_unchanged_content(self, mock_openai_cls):
        from apps.ai.models import Document
        import hashlib

        content = "Same content"
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        doc = Document.objects.create(
            title="Test",
            content=content,
            embedding=[0.1] * 1536,
            content_hash=content_hash,
        )

        generate_embedding(doc.id)

        # OpenAI should NOT be called (content unchanged)
        mock_openai_cls.assert_not_called()
```

### HNSW Index Tuning Reference

| Parameter | Build-time (`ef_construction`) | Query-time (`ef_search`) |
|-----------|-------------------------------|--------------------------|
| Purpose | Controls index quality during construction | Controls search quality per query |
| Default | 64 | 40 |
| Template default | 64 | 100 (set per-query in service) |
| Higher value | Better recall, slower build | Better recall, slower query |
| Recommendation | Increase to 200 for > 100K vectors | Increase to 200 for better recall when query latency allows |

```sql
-- Set query-time search parameter (per-connection, not persistent)
SET hnsw.ef_search = 100;

-- Check index is being used
EXPLAIN ANALYZE
SELECT * FROM ai_document
ORDER BY embedding <=> '[0.1, 0.2, ...]'::vector
LIMIT 10;
-- Should show: Index Scan using document_embedding_idx
```

## Constraints

1. **AI module is optional.** `ENABLE_AI_MODULE=false` must disable all AI functionality without errors.
2. **AI dependencies are in optional group.** `uv sync` without `--extra ai` installs no AI libraries.
3. **No AI imports outside `apps.ai`.** If a non-AI app needs to trigger embedding, it dispatches a Celery task by name string, not by import.
4. **Graph nodes are testable as plain functions.** No test should require a running LLM service. Mock all external calls.
5. **Vector search tests need Postgres.** SQLite does not support PGVector. Integration tests require the `pgvector/pgvector:pg16` Docker image.
6. **Celery tasks are tested synchronously.** Call tasks directly in tests, not via `.delay()`. No Celery broker needed for unit tests.
7. **Embedding model name comes from settings.** `settings.AI_EMBEDDING_MODEL`, never hardcoded in services or tasks.

## References

- `openspec/specs/foundation/ai-stack.md` -- Architecture-level AI patterns (LangGraph, PGVector, Celery)
- `openspec/specs/foundation/data-models.md` -- EmbeddingMixin, PGVector extension setup, CosineDistance queries
- `openspec/specs/backend/api-endpoints.md` -- Controller/service/schema patterns
- `.planning/research/STACK.md` -- LangGraph, PGVector, Celery version recommendations
- `.planning/research/ARCHITECTURE.md` -- AI module data flow, embedding pipeline diagram
- `.planning/research/FEATURES.md` -- AI module as optional differentiator feature
