"""
AI Module API Controller - Django Ninja Extra endpoints.

Endpoints:
- POST /ai/search: Semantic search over document chunks
- POST /ai/documents: Upload document and trigger embedding pipeline
- GET /ai/documents/{id}: Get document status and chunk count
- POST /ai/ask: Ask a question using RAG agent
"""

import logging

from django.shortcuts import get_object_or_404
from langchain_core.messages import HumanMessage
from ninja_extra import api_controller, http_get, http_post
from ninja_extra.permissions import IsAuthenticated

from apps.ai.graphs.qa_agent import build_qa_graph
from apps.ai.models import Document
from apps.ai.schemas import (
    AskQuestionRequest,
    DocumentResponse,
    QuestionResponse,
    SearchRequest,
    SearchResponse,
    UploadDocumentRequest,
)
from apps.ai.services import search_documents
from apps.ai.tasks import generate_embeddings

logger = logging.getLogger(__name__)


@api_controller("/ai", tags=["AI Module"], permissions=[IsAuthenticated])
class AIController:
    """
    AI Module API controller exposing vector search, document upload, and Q&A.

    All endpoints require authentication.
    """

    @http_post("/search", response=SearchResponse)
    def search(self, request_data: SearchRequest):
        """
        Semantic search over document chunks using vector similarity.

        Query embeddings are generated on-the-fly and compared against stored
        document chunk embeddings using cosine similarity.

        Args:
            request_data: SearchRequest with query, limit, filters, and threshold

        Returns:
            SearchResponse with ranked results (most similar first)

        Example:
            POST /api/v1/ai/search
            {
                "query": "machine learning basics",
                "limit": 5,
                "similarity_threshold": 0.7
            }
        """
        # Call search service
        results = search_documents(
            query=request_data.query,
            limit=request_data.limit or 5,
            filters=request_data.filters,
            similarity_threshold=request_data.similarity_threshold or 0.7,
        )

        return SearchResponse(
            results=results,
            total=len(results),
        )

    @http_post("/documents", response=DocumentResponse)
    def upload_document(self, request, request_data: UploadDocumentRequest):
        """
        Upload document and trigger async embedding generation.

        Creates a Document instance and dispatches a Celery task to chunk the
        content and generate embeddings. Returns immediately with task ID.

        Args:
            request: Django HttpRequest (for user context)
            request_data: UploadDocumentRequest with title, content, metadata

        Returns:
            DocumentResponse with document ID, status, and task ID

        Example:
            POST /api/v1/ai/documents
            {
                "title": "ML Guide",
                "content": "Machine learning is...",
                "metadata": {"source": "web"}
            }
        """
        # Create Document instance
        document = Document.objects.create(
            title=request_data.title,
            content=request_data.content,
            uploaded_by=request.user,
            embedding_status="pending",
            metadata=request_data.metadata or {},
        )

        # Trigger async embedding task
        task = generate_embeddings.delay(document.id)

        logger.info(
            f"Document {document.id} created, embedding task {task.id} dispatched"
        )

        return DocumentResponse(
            id=document.id,
            title=document.title,
            status=document.embedding_status,
            chunk_count=None,  # Not yet processed
            task_id=str(task.id),
        )

    @http_get("/documents/{document_id}", response=DocumentResponse)
    def get_document(self, document_id: int):
        """
        Get document status and chunk count.

        Args:
            document_id: Document ID

        Returns:
            DocumentResponse with current status and chunk count

        Example:
            GET /api/v1/ai/documents/123
        """
        document = get_object_or_404(Document, id=document_id)

        # Count chunks
        chunk_count = document.chunks.count() if document.embedding_status == "completed" else None

        return DocumentResponse(
            id=document.id,
            title=document.title,
            status=document.embedding_status,
            chunk_count=chunk_count,
            task_id=None,
        )

    @http_post("/ask", response=QuestionResponse)
    def ask_question(self, request_data: AskQuestionRequest):
        """
        Ask a question using RAG agent (Q&A over documents).

        Invokes a LangGraph agent that:
        1. Validates input (guardrails)
        2. Detects intent (RAG vs tool agent)
        3. Retrieves relevant chunks or uses tools
        4. Generates an answer using LLM

        Args:
            request_data: AskQuestionRequest with question

        Returns:
            QuestionResponse with answer and context chunks

        Example:
            POST /api/v1/ai/ask
            {
                "question": "What is machine learning?"
            }
        """
        question = request_data.question

        # Build and invoke LangGraph agent
        graph = build_qa_graph()

        try:
            result = graph.invoke({
                "messages": [HumanMessage(content=question)],
                "query": "",
                "intent": "pending",
                "retrieved_chunks": [],
                "answer": "",
                "loop_count": 0,
            })

            answer = result.get("answer", "No answer generated.")
            retrieved_chunks = result.get("retrieved_chunks", [])

            # Extract context text from chunks
            context = [chunk["text"] for chunk in retrieved_chunks]

            logger.info(f"Q&A completed for question: {question}")

            return QuestionResponse(
                question=question,
                answer=answer,
                context=context,
            )

        except Exception as e:
            logger.exception(f"Q&A failed for question: {question}")
            return QuestionResponse(
                question=question,
                answer="I encountered an error while processing your question.",
                context=[],
            )
