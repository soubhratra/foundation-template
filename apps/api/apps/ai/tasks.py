"""
Celery tasks for AI module.

Tasks:
- generate_embeddings: Async pipeline for document chunking and embedding generation
"""

import logging
from typing import Any

import tiktoken
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from openai import OpenAI

from apps.ai.models import Document, DocumentChunk

logger = logging.getLogger(__name__)


def chunk_text(
    text: str,
    chunk_size: int = 512,
    overlap: int = 200,
    encoding_name: str = "cl100k_base",
) -> list[str]:
    """
    Split text into fixed-size token chunks with overlap.

    Args:
        text: Text to chunk
        chunk_size: Maximum tokens per chunk (default: 512)
        overlap: Token overlap between chunks (default: 200)
        encoding_name: Tiktoken encoding to use (default: cl100k_base for OpenAI)

    Returns:
        List of text chunks

    Implementation:
    - Uses tiktoken to split by tokens (not characters)
    - Overlapping chunks improve semantic continuity
    - Filters out chunks with <10 tokens (too short to be meaningful)
    """
    if not text or not text.strip():
        return []

    encoding = tiktoken.get_encoding(encoding_name)
    tokens = encoding.encode(text)

    if len(tokens) == 0:
        return []

    chunks = []
    start = 0

    while start < len(tokens):
        end = start + chunk_size
        chunk_tokens = tokens[start:end]

        # Skip chunks that are too small to be meaningful
        if len(chunk_tokens) < 10:
            break

        chunk_text = encoding.decode(chunk_tokens).strip()
        if chunk_text:
            chunks.append(chunk_text)

        # Move forward by (chunk_size - overlap) to create overlap
        start += chunk_size - overlap

        # Prevent infinite loop if overlap >= chunk_size
        if overlap >= chunk_size:
            start = end

    return chunks


@shared_task(bind=True, max_retries=3)
def generate_embeddings(self, document_id: int) -> dict[str, Any]:
    """
    Generate embeddings for a document.

    Workflow:
    1. Fetch Document by ID
    2. Chunk document.content using chunk_text utility
    3. For each chunk, generate embedding via OpenAI API
    4. Create DocumentChunk with text, embedding, and metadata
    5. Update document.embedding_status to "completed" on success
    6. On failure, retry with exponential backoff

    Task is idempotent: deletes existing chunks before processing.

    Args:
        document_id: ID of document to process

    Returns:
        Dict with status and chunk count
    """
    try:
        # Fetch document
        document = Document.objects.get(id=document_id)
        document.embedding_status = "processing"
        document.save(update_fields=["embedding_status"])

        # Initialize OpenAI client
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not configured")

        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        # Delete existing chunks (idempotency)
        document.chunks.all().delete()

        # Chunk text
        chunks = chunk_text(document.content)

        if not chunks:
            document.embedding_status = "failed"
            document.save(update_fields=["embedding_status"])
            return {
                "status": "failed",
                "error": "No valid chunks generated from document content",
            }

        # Generate embeddings for each chunk
        embedding_model = "text-embedding-3-small"
        embedding_version = "v1"
        created_chunks = []

        for idx, chunk_content in enumerate(chunks):
            # Call OpenAI embeddings API
            response = client.embeddings.create(
                model=embedding_model,
                input=chunk_content,
                encoding_format="float",
            )

            embedding = response.data[0].embedding

            # Create DocumentChunk
            chunk = DocumentChunk.objects.create(
                document=document,
                text=chunk_content,
                chunk_index=idx,
                embedding=embedding,
                embedding_model=embedding_model,
                embedding_version=embedding_version,
                embedded_at=timezone.now(),
                metadata={
                    "document_title": document.title,
                    "uploaded_at": document.uploaded_at.isoformat(),
                },
            )
            created_chunks.append(chunk.id)

        # Update document status
        document.embedding_status = "completed"
        document.save(update_fields=["embedding_status"])

        logger.info(f"Generated {len(created_chunks)} embeddings for document {document_id}")

        return {
            "status": "completed",
            "document_id": document_id,
            "chunks_created": len(created_chunks),
        }

    except Document.DoesNotExist:
        logger.error(f"Document {document_id} not found")
        return {
            "status": "failed",
            "error": f"Document {document_id} not found",
        }

    except Exception as exc:
        logger.exception(f"Failed to generate embeddings for document {document_id}")

        # Update document status
        try:
            document = Document.objects.get(id=document_id)
            document.embedding_status = "failed"
            document.save(update_fields=["embedding_status"])
        except Document.DoesNotExist:
            pass

        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60) from exc
