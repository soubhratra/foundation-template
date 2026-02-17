"""
AI services for vector search and semantic retrieval.

Services:
- search_documents: Semantic search over document chunks using vector similarity
"""

import logging
from typing import Any

from django.conf import settings
from django.db.models import F
from openai import OpenAI
from pgvector.django import CosineDistance

from apps.ai.models import DocumentChunk

logger = logging.getLogger(__name__)


def search_documents(
    query: str,
    limit: int = 5,
    filters: dict[str, Any] | None = None,
    similarity_threshold: float = 0.7,
) -> list[dict[str, Any]]:
    """
    Semantic search over document chunks using vector similarity.

    Args:
        query: Search query string
        limit: Maximum number of results to return (default: 5)
        filters: Optional metadata filters (e.g., {"document_title": "Test"})
        similarity_threshold: Minimum similarity score (0-1, default: 0.7)

    Returns:
        List of dicts with chunk data and similarity scores:
        [
            {
                "id": 1,
                "text": "chunk text...",
                "similarity": 0.92,
                "metadata": {...},
                "document_title": "Document Title",
                "document_id": 123,
                "chunk_index": 0,
            },
            ...
        ]

    Implementation:
    1. Generate query embedding using OpenAI API
    2. Query DocumentChunks by cosine similarity
    3. Apply metadata filters if provided
    4. Filter by similarity threshold
    5. Return ranked results (most similar first)

    Edge cases:
    - Empty query -> return empty list
    - No results above threshold -> return empty list (not error)
    - OpenAI API errors -> log and re-raise (caller handles)
    """
    # Handle empty query
    if not query or not query.strip():
        return []

    # Initialize OpenAI client
    if not settings.OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY not configured")
        raise ValueError("OPENAI_API_KEY not configured")

    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    # Generate query embedding
    try:
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=query.strip(),
            encoding_format="float",
        )
        query_embedding = response.data[0].embedding
    except Exception as exc:
        logger.exception("Failed to generate query embedding")
        raise

    # Build query
    queryset = DocumentChunk.objects.exclude(embedding__isnull=True)

    # Apply metadata filters
    if filters:
        for key, value in filters.items():
            queryset = queryset.filter(**{f"metadata__{key}": value})

    # Annotate with cosine distance and convert to similarity
    # PGVector CosineDistance returns distance (0-2), convert to similarity (0-1)
    queryset = queryset.annotate(
        distance=CosineDistance("embedding", query_embedding),
    ).annotate(
        # Convert distance to similarity: similarity = 1 - (distance / 2)
        # This normalizes to 0-1 range where 1 = identical, 0 = opposite
        similarity=1 - (F("distance") / 2),
    )

    # Filter by similarity threshold
    queryset = queryset.filter(similarity__gte=similarity_threshold)

    # Order by distance (ascending = most similar first)
    queryset = queryset.order_by("distance")

    # Limit results
    queryset = queryset[:limit]

    # Select fields and convert to dict
    results = queryset.values(
        "id",
        "text",
        "similarity",
        "metadata",
        "chunk_index",
        document_title=F("document__title"),
        document_id=F("document__id"),
    )

    return list(results)
