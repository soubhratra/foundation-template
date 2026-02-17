# AI Module

**Optional, fully isolated AI capabilities for the Foundation Template.**

This module provides vector search, document embedding pipelines, and LangGraph agent scaffolding. It's designed to be either kept and extended for product-specific AI features, or cleanly removed if not needed.

## What's Included

- **Vector Search**: Semantic search over document chunks using OpenAI embeddings and PGVector
- **Embedding Pipeline**: Async document chunking and embedding generation via Celery
- **LangGraph Agents**: Q&A agent demonstrating RAG patterns and tool integration
- **REST API**: Django Ninja Extra endpoints for search, upload, and Q&A

## Use Cases

- **Q&A over documents**: Upload documents, ask questions, get answers with cited sources
- **Semantic search**: Find relevant content by meaning, not just keywords
- **Agent orchestration**: Build multi-step AI workflows with routing and tools
- **Template extensibility**: Starting point for product-specific AI features

---

## Architecture

### File Structure

```
apps/ai/
├── models.py              # Document and DocumentChunk models with PGVector
├── services.py            # search_documents (vector similarity service)
├── tasks.py               # generate_embeddings (Celery async pipeline)
├── schemas.py             # Pydantic request/response schemas
├── controllers.py         # Django Ninja Extra API endpoints
├── graphs/
│   ├── state.py           # LangGraph state schema
│   └── qa_agent.py        # Q&A agent with guardrails, intent, RAG, tools
├── tools/
│   └── __init__.py        # Python function tools (calculator, string ops)
└── scripts/
    ├── remove_ai_module.sh    # Automated removal script
    └── verify_removal.sh      # Verify clean removal
```

### Data Flow: Document Upload → Search

1. **Upload**: User POSTs document to `/api/v1/ai/documents`
2. **Storage**: Document created with `status=pending`
3. **Chunking**: Celery task splits text into 512-token chunks with 200-token overlap
4. **Embedding**: Each chunk embedded using OpenAI `text-embedding-3-small` (1536 dims)
5. **Indexing**: Chunks stored in PostgreSQL with HNSW vector index
6. **Search**: Query embedded → cosine similarity → ranked results

### Agent Flow: Q&A

```
Entry → Guardrails → Intent Detection → [RAG Path | Tool Agent Path] → End

RAG Path:       rag_retrieval → generate_answer
Tool Path:      tool_agent (ReAct with Python function tools)
Invalid Input:  END (early exit)
```

**Guardrails**: Validates input (minimum length, message type)
**Intent Detection**: Keyword-based routing (production could use LLM)
**RAG Retrieval**: Vector search for relevant chunks
**Generate Answer**: LLM synthesizes answer from context
**Tool Agent**: ReAct agent with calculator, string manipulation tools

---

## Quick Start

### Prerequisites

1. **PostgreSQL with PGVector extension** (handled by migrations)
2. **OpenAI API key** for embeddings and LLM calls
3. **Redis** for Celery task queue
4. **Celery worker** running in background

### Environment Variables

```bash
# In apps/api/.env
OPENAI_API_KEY=sk-...                   # Required for embeddings + LLM
CELERY_BROKER_URL=redis://localhost:6379/0  # For async tasks
```

### Start Celery Worker

```bash
cd apps/api
celery -A config worker --loglevel=info
```

### Example API Usage

**1. Upload a document**

```bash
curl -X POST http://localhost:8000/api/v1/ai/documents \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "title": "Machine Learning Guide",
    "content": "Machine learning is a subset of artificial intelligence...",
    "metadata": {"source": "web", "language": "en"}
  }'

# Response:
{
  "id": 123,
  "title": "Machine Learning Guide",
  "status": "pending",
  "chunk_count": null,
  "task_id": "abc-123-def"
}
```

**2. Check document status**

```bash
curl http://localhost:8000/api/v1/ai/documents/123 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Response (after processing):
{
  "id": 123,
  "title": "Machine Learning Guide",
  "status": "completed",
  "chunk_count": 15,
  "task_id": null
}
```

**3. Search documents**

```bash
curl -X POST http://localhost:8000/api/v1/ai/search \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "query": "What is supervised learning?",
    "limit": 5,
    "similarity_threshold": 0.7
  }'

# Response:
{
  "results": [
    {
      "id": 456,
      "text": "Supervised learning is a type of machine learning...",
      "similarity": 0.92,
      "metadata": {"document_title": "ML Guide"},
      "document_title": "Machine Learning Guide",
      "document_id": 123,
      "chunk_index": 3
    }
  ],
  "total": 1
}
```

**4. Ask a question**

```bash
curl -X POST http://localhost:8000/api/v1/ai/ask \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "question": "What is the difference between supervised and unsupervised learning?"
  }'

# Response:
{
  "question": "What is the difference between supervised and unsupervised learning?",
  "answer": "Supervised learning uses labeled data to train models...",
  "context": [
    "Supervised learning is a type of...",
    "Unsupervised learning finds patterns..."
  ]
}
```

---

## Extension Points

This module is designed for easy extension. Here are common customization points:

### 1. Embedding Model Swapping

**Current**: OpenAI `text-embedding-3-small` (1536 dims)

**To swap to a different model:**

1. **Update `tasks.py`**: Change `embedding_model` and dimensions
2. **Update `models.py`**: Change `VectorField(dimensions=...)` to match
3. **Create migration**: `python manage.py makemigrations --empty ai`
4. **Add re-embedding logic**: Iterate over existing chunks, regenerate embeddings

**Example alternatives:**
- OpenAI `text-embedding-3-large` (3072 dims) - higher quality
- Local models via Sentence Transformers (e.g., `all-MiniLM-L6-v2`, 384 dims)
- Cohere `embed-english-v3.0` (1024 dims)

**Migration path**:
```python
# In new migration
def reembed_all_documents(apps, schema_editor):
    Document = apps.get_model('ai', 'Document')
    for doc in Document.objects.filter(embedding_status='completed'):
        generate_embeddings.delay(doc.id)  # Re-embed with new model
```

### 2. Chunking Strategy

**Current**: Fixed 512-token chunks with 200-token overlap

**To customize**, edit `chunk_text()` in `tasks.py`:

- **Semantic boundaries**: Split on paragraph/sentence boundaries
- **Recursive splitting**: Try larger chunks, split if too big
- **Metadata-aware**: Different chunking per document type (code, prose, tables)

**Example: Semantic chunking**
```python
def chunk_text_semantic(text: str, max_tokens: int = 512):
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = []
    current_tokens = 0

    for para in paragraphs:
        para_tokens = len(encoding.encode(para))
        if current_tokens + para_tokens > max_tokens:
            chunks.append('\n\n'.join(current_chunk))
            current_chunk = [para]
            current_tokens = para_tokens
        else:
            current_chunk.append(para)
            current_tokens += para_tokens

    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))
    return chunks
```

### 3. Search Paradigms

**Current**: Vector-only semantic search

**Extensions:**

**A. Hybrid Search (Vector + Keyword)**

Combine vector similarity with BM25 keyword search:

```python
from django.contrib.postgres.search import SearchVector, SearchRank

def hybrid_search(query: str, limit: int = 5):
    # Vector search (as current)
    vector_results = search_documents(query, limit=20)

    # Keyword search (PostgreSQL full-text search)
    keyword_results = DocumentChunk.objects.annotate(
        rank=SearchRank(SearchVector('text'), query)
    ).filter(rank__gte=0.1).order_by('-rank')[:20]

    # Merge and re-rank (Reciprocal Rank Fusion or weighted score)
    combined = merge_results(vector_results, keyword_results)
    return combined[:limit]
```

**B. NLP2SQL for Structured Data**

Add natural language → SQL query translation:

```python
# In new tools/nlp2sql.py
from langchain_openai import ChatOpenAI
from langchain.chains import create_sql_query_chain

def nl_to_sql(question: str, schema: dict):
    """Convert natural language to SQL query for structured data."""
    llm = ChatOpenAI(model="gpt-4o-mini")
    chain = create_sql_query_chain(llm, db=schema)
    return chain.invoke({"question": question})
```

**C. Multi-Index Search**

Create separate indexes per document type or category:

```python
# In models.py
class DocumentCategory(models.TextChoices):
    TECHNICAL = 'tech'
    MARKETING = 'marketing'
    LEGAL = 'legal'

class Document(models.Model):
    category = models.CharField(choices=DocumentCategory.choices)

# In services.py
def search_by_category(query: str, category: str):
    return search_documents(
        query=query,
        filters={"metadata__category": category}
    )
```

### 4. Additional Tools & MCP Integration

**Current**: Simple Python function tools (calculator, string manipulation)

**To add more tools:**

1. **Define tool function** in `tools/` directory
2. **Add to agent** in `qa_agent.py`
3. **Document tool** with clear docstrings (LLM uses these)

**Example: Web search tool**

```python
# In tools/web_search.py
from langchain_core.tools import tool

@tool
def web_search(query: str) -> str:
    """Search the web for current information.

    Use this when the question requires up-to-date information
    not found in the knowledge base.

    Args:
        query: Search query string

    Returns:
        Search results as formatted text
    """
    # Integrate with Tavily, Serper, or other search API
    results = tavily_client.search(query)
    return format_results(results)

# In qa_agent.py
from apps.ai.tools.web_search import web_search
tools = [calculate, reverse_string, count_words, web_search]
```

**MCP Server Integration** (Model Context Protocol):

```python
# Future extension: Connect to MCP servers for external tools
from mcp import MCPClient

mcp_client = MCPClient(server_url="http://localhost:8080")
mcp_tools = mcp_client.get_tools()
agent = create_react_agent(llm, tools + mcp_tools)
```

### 5. Agent Customization

**Current**: Linear Q&A flow with RAG and tool routing

**To customize**, edit `qa_agent.py`:

- **Add new nodes**: Create function, add to graph
- **Modify routing**: Update `should_continue()` logic
- **Add memory**: Persist conversation history in state
- **Multi-step reasoning**: Add loops with checkpoints

**Example: Add reflection node**

```python
def reflection_node(state: QAState) -> dict:
    """Review answer quality before returning to user."""
    answer = state["answer"]
    query = state["query"]

    prompt = f"Review this answer: {answer}\nFor query: {query}\n\nIs it accurate and complete?"
    llm = ChatOpenAI(model="gpt-4o-mini")
    reflection = llm.invoke([HumanMessage(content=prompt)])

    # If reflection says "incomplete", loop back to RAG
    if "incomplete" in reflection.content.lower():
        return {"intent": "rag", "loop_count": state["loop_count"] + 1}

    return {}

# Add to graph
graph.add_node("reflection", reflection_node)
graph.add_edge("generate_answer", "reflection")
graph.add_conditional_edges("reflection", should_continue_or_end)
```

---

## Cost Estimates

### OpenAI Pricing (as of 2024)

**Embeddings** (`text-embedding-3-small`):
- **Cost**: $0.00002 per 1,000 tokens
- **Example**: 1,000 documents × 500 words each ≈ 650,000 tokens ≈ **$0.013**

**LLM Calls** (`gpt-4o-mini`):
- **Input**: $0.15 per 1M tokens
- **Output**: $0.60 per 1M tokens
- **Example**: 100 Q&A queries × (1,000 input + 300 output tokens) ≈ **$0.03**

**Recommendation**: For production, track costs using:
- `django-celery-results` for embedding task monitoring
- OpenAI usage dashboard for API spend
- Add cost tracking fields to `Document` model

---

## Troubleshooting

### Common Pitfalls

**1. PGVector extension permission errors**

```
django.db.utils.ProgrammingError: permission denied to create extension "vector"
```

**Solution**: Use `IF NOT EXISTS` (already implemented in migrations), or pre-install:

```sql
-- Run as superuser
CREATE EXTENSION IF NOT EXISTS vector;
```

**2. Celery tasks not processing**

**Symptoms**: Document status stuck at `pending`

**Check**:
```bash
# Is Celery running?
ps aux | grep celery

# Check Redis connection
redis-cli ping

# Check Celery logs
celery -A config worker --loglevel=debug
```

**3. Empty search results**

**Causes**:
- Similarity threshold too high (default: 0.7)
- No documents embedded yet
- Query too short (filtered by guardrails)

**Solution**:
```python
# Lower threshold
results = search_documents(query="...", similarity_threshold=0.5)

# Check document status
Document.objects.filter(embedding_status='completed').count()
```

**4. LangGraph infinite loops**

**Symptoms**: Agent times out or hits loop limit

**Causes**:
- Routing logic creates cycle
- `loop_count` not incremented

**Solution**: Check `loop_count` increments in every node, add max loop termination in `should_continue()`.

**5. Embedding model version mismatch**

**Symptoms**: Search results poor after changing embedding model

**Cause**: Query embedded with new model, chunks embedded with old model

**Solution**: Re-embed all documents after model change:

```python
# In Django shell
from apps.ai.models import Document
from apps.ai.tasks import generate_embeddings

for doc in Document.objects.filter(embedding_status='completed'):
    doc.embedding_status = 'pending'
    doc.save()
    generate_embeddings.delay(doc.id)
```

### Debugging LangGraph Execution

Add logging to nodes for visibility:

```python
import logging
logger = logging.getLogger(__name__)

def my_node(state: QAState) -> dict:
    logger.info(f"Node state: {state}")
    # ... node logic
    logger.info(f"Node output: {output}")
    return output
```

Run with debug logging:

```bash
DJANGO_LOG_LEVEL=DEBUG python manage.py runserver
```

---

## Removal Instructions

This module is designed to be completely removable. Follow these steps to cleanly delete the AI module from your project:

### Automated Removal (Recommended)

```bash
cd apps/api
bash apps/ai/scripts/remove_ai_module.sh
```

This script will:
1. Remove `apps.ai` from `INSTALLED_APPS`
2. Run `python manage.py migrate ai zero` to drop database tables
3. Delete `apps/ai/` directory
4. Run verification checks

### Manual Removal

If you prefer manual removal or need more control:

**1. Remove from INSTALLED_APPS**

Edit `apps/api/config/settings/base.py`:

```python
INSTALLED_APPS = [
    # ... other apps
    # "apps.ai",  # Remove this line
]
```

**2. Drop database tables**

```bash
cd apps/api
python manage.py migrate ai zero
```

**3. Remove directory**

```bash
rm -rf apps/api/apps/ai/
```

**4. Remove dependencies** (optional, if not used elsewhere)

Edit `apps/api/pyproject.toml`, remove:

```toml
# AI Module dependencies
pgvector = "^0.2.4"
langgraph = "^0.2.0"
langchain-core = "^0.3.0"
langchain-openai = "^0.2.0"
celery = "^5.3.0"
redis = "^5.0.0"
openai = "^1.0.0"
tiktoken = "^0.7.0"
```

Then sync:

```bash
uv sync
```

**5. Verify removal**

```bash
bash apps/ai/scripts/verify_removal.sh
```

Or manually:

```bash
# No AI imports in other apps
grep -r "from apps.ai" apps/ --exclude-dir=ai

# Tests pass
pytest apps/ --ignore=apps/ai

# Lint passes
ruff check apps/ --exclude apps/ai

# Django check passes
python manage.py check
```

### Success Criteria

✅ All tests pass without AI module
✅ No import errors from other apps
✅ API server starts and serves non-AI endpoints
✅ Database migrations don't reference AI tables
✅ Linting/type-check passes

### What Gets Removed

- ❌ All AI models (Document, DocumentChunk)
- ❌ Vector indexes and embeddings
- ❌ Celery tasks for embedding generation
- ❌ LangGraph agents and tools
- ❌ API endpoints under `/api/v1/ai/*`

### What Stays

- ✅ Core authentication
- ✅ User accounts
- ✅ Other API endpoints
- ✅ Admin interface
- ✅ Database (non-AI tables)

---

## Next Steps

After setting up the AI module:

1. **Test the endpoints**: Use the example API calls above
2. **Customize for your product**: Add domain-specific tools, prompts, and data sources
3. **Monitor costs**: Track OpenAI usage and optimize chunking strategy
4. **Extend agents**: Add more sophisticated routing, memory, or multi-step reasoning
5. **Or remove it**: If not needed, follow the removal instructions

For questions or issues, refer to the Foundation Template documentation or open an issue on GitHub.
