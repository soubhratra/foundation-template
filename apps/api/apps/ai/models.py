"""
AI Module Models - Document storage with vector embeddings.

Models:
- VectorEmbeddingMixin: Reusable abstract model for embedding fields
- Document: Uploaded documents with metadata
- DocumentChunk: Text chunks with vector embeddings for semantic search
"""

from django.conf import settings
from django.db import models
from pgvector.django import HnswIndex, VectorField


class VectorEmbeddingMixin(models.Model):
    """
    Abstract model mixin for entities with vector embeddings.

    Provides:
    - embedding: 1536-dimensional vector (OpenAI text-embedding-3-small)
    - embedding_model: Model used to generate embedding (for version tracking)
    - embedding_version: Version identifier (enables re-embedding workflows)
    - embedded_at: Timestamp of embedding generation
    - HNSW index for fast cosine similarity search

    Usage:
        class MyModel(VectorEmbeddingMixin):
            # Your fields here
            pass
    """

    embedding = VectorField(
        dimensions=1536,
        null=True,
        blank=True,
        help_text="Vector embedding for semantic search",
    )
    embedding_model = models.CharField(
        max_length=100,
        default="text-embedding-3-small",
        help_text="Model used to generate embedding",
    )
    embedding_version = models.CharField(
        max_length=50,
        default="v1",
        help_text="Version for re-embedding tracking",
    )
    embedded_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When embedding was generated",
    )

    class Meta:
        abstract = True


class Document(models.Model):
    """
    User-uploaded document for AI processing.

    Workflow:
    1. User uploads document via API
    2. Document created with status='pending'
    3. Celery task chunks text and generates embeddings
    4. Status updates to 'completed' when done
    """

    EMBEDDING_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    title = models.CharField(
        max_length=255,
        help_text="Document title or filename",
    )
    content = models.TextField(
        help_text="Full document text content",
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="documents",
        help_text="User who uploaded this document",
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When document was uploaded",
    )
    embedding_status = models.CharField(
        max_length=20,
        choices=EMBEDDING_STATUS_CHOICES,
        default="pending",
        help_text="Status of embedding generation pipeline",
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional metadata (file type, size, etc.)",
    )

    class Meta:
        ordering = ["-uploaded_at"]
        indexes = [
            models.Index(fields=["uploaded_by", "-uploaded_at"]),
            models.Index(fields=["embedding_status"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.embedding_status})"


class DocumentChunk(VectorEmbeddingMixin):
    """
    Text chunk from a document with vector embedding.

    Chunking strategy:
    - Fixed-size chunking (512 tokens with 200-token overlap)
    - Chunks are independently searchable via vector similarity
    - chunk_index preserves document ordering

    Search workflow:
    1. Query is embedded using same model
    2. Cosine similarity search finds similar chunks
    3. Results include chunk text + source document reference
    """

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="chunks",
        help_text="Source document for this chunk",
    )
    text = models.TextField(
        help_text="Chunk text content",
    )
    chunk_index = models.IntegerField(
        help_text="0-based chunk position within document",
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Metadata for filtering (e.g., document_title, category)",
    )

    class Meta:
        ordering = ["document", "chunk_index"]
        indexes = [
            models.Index(fields=["document", "chunk_index"]),
            HnswIndex(
                name="ai_chunk_embedding_hnsw_idx",
                fields=["embedding"],
                m=16,  # Connections per node (tradeoff: recall vs build time)
                ef_construction=64,  # Build quality (higher = better recall, slower build)
                opclasses=["vector_cosine_ops"],  # Use cosine distance
            ),
        ]

    def __str__(self):
        return f"{self.document.title} - Chunk {self.chunk_index}"
