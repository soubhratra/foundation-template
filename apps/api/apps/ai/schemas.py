"""
Request and response schemas for AI Module API endpoints.

Schemas:
- SearchRequest: Vector search query parameters
- SearchResult: Single search result with similarity score
- SearchResponse: List of search results with total count
- UploadDocumentRequest: Document upload payload
- DocumentResponse: Document status and metadata
- AskQuestionRequest: Q&A query
- QuestionResponse: Answer with context chunks
"""

from typing import Any

from ninja import Schema


class SearchRequest(Schema):
    """
    Vector search request.

    Example:
        {
            "query": "What is machine learning?",
            "limit": 5,
            "filters": {"document_title": "AI Guide"},
            "similarity_threshold": 0.7
        }
    """

    query: str
    limit: int | None = 5
    filters: dict[str, Any] | None = None
    similarity_threshold: float | None = 0.7


class SearchResult(Schema):
    """
    Single search result with chunk data and similarity score.

    Example:
        {
            "id": 123,
            "text": "Machine learning is...",
            "similarity": 0.92,
            "metadata": {"document_title": "AI Guide"},
            "document_title": "AI Guide",
            "document_id": 456,
            "chunk_index": 0
        }
    """

    id: int
    text: str
    similarity: float
    metadata: dict[str, Any]
    document_title: str
    document_id: int
    chunk_index: int


class SearchResponse(Schema):
    """
    Search results with total count.

    Example:
        {
            "results": [SearchResult, ...],
            "total": 5
        }
    """

    results: list[SearchResult]
    total: int


class UploadDocumentRequest(Schema):
    """
    Document upload request.

    Example:
        {
            "title": "Machine Learning Guide",
            "content": "This is a guide to machine learning...",
            "metadata": {"source": "web", "language": "en"}
        }
    """

    title: str
    content: str
    metadata: dict[str, Any] | None = None


class DocumentResponse(Schema):
    """
    Document status and metadata.

    Example:
        {
            "id": 123,
            "title": "Machine Learning Guide",
            "status": "completed",
            "chunk_count": 15,
            "task_id": "abc123"
        }
    """

    id: int
    title: str
    status: str
    chunk_count: int | None = None
    task_id: str | None = None


class AskQuestionRequest(Schema):
    """
    Q&A request using RAG agent.

    Example:
        {
            "question": "What is the capital of France?"
        }
    """

    question: str


class QuestionResponse(Schema):
    """
    Q&A response with answer and context chunks.

    Example:
        {
            "question": "What is the capital of France?",
            "answer": "The capital of France is Paris.",
            "context": ["Paris is the capital...", "France is a country..."]
        }
    """

    question: str
    answer: str
    context: list[str]
