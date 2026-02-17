# Phase 6: AI Module - Context

**Gathered:** 2026-02-16
**Status:** Ready for planning

<domain>
## Phase Boundary

An optional, fully isolated AI module provides vector search and LangGraph agent scaffolding. Developers using the template can either keep it or cleanly remove it. This phase delivers backend AI infrastructure with a working Q&A example, NOT a full production AI feature.

</domain>

<decisions>
## Implementation Decisions

### Example Agent Design
- **Use case**: Q&A over documents (classic RAG pattern)
- **Document source**: User upload via API (endpoint triggers embedding pipeline)
- **LangGraph nodes**:
  - Guardrails (input validation)
  - Intent detection/routing
  - RAG retrieval (vector search)
  - Sub-agent with simple Python function tools (MCP integration deferred)
- **Routing example**: "if question needs web search, use sub-agent; else use RAG" — demonstrates multi-step graph without scope creep

### Embedding Pipeline
- **Content type**: Text only (images/documents deferred to future phases)
- **Embedding model**: OpenAI text-embedding-3-small (1536 dims)
  - Document configurable optionality for future extensibility (local models, other providers)
- **Triggering**: REST API via Django Ninja Extra (async for performance)

### Vector Search API
- **Endpoint**: `POST /api/v1/ai/search`
- **Request body**: `{query: string, limit?: number, filters?: object, include?: string[]}`
- **Response fields** (controllable via `include` flags):
  - Document metadata (title, upload date, file name)
  - Matched chunk text
  - Similarity score (cosine, 0-1)
  - Source reference (document ID, chunk ID)
- **Similarity**: Cosine similarity
- **Default result count**: 5 (configurable via `limit` param)

### Removal Strategy
- **Success criteria**:
  - `rm -rf apps/api/apps/ai/` leaves project functional
  - All tests pass after removal (pytest, lint, type-check)
  - No dead imports elsewhere in codebase
  - Step-by-step removal docs verify process
- **Automation**: Include removal script that deletes module, updates settings, runs migrations, verifies
- **Documentation**:
  - Primary: `apps/api/apps/ai/README.md` (co-located with code)
  - Also sync with OpenSpec for template-wide context

### Claude's Discretion
- Embedding timing (immediate async task vs deferred queue)
- Chunking strategy (fixed size vs semantic boundaries)
- Re-embedding implementation (versioning vs simple replace) — document future phases for extensibility and scalability
- Vector search filtering options (metadata filters, similarity threshold, or both)
- Edge case handling (empty results — return empty array vs error)
- Dependency model (apps can call AI APIs, or fully isolated backend-only)
- Sub-agent tool implementation details

</decisions>

<specifics>
## Specific Ideas

**Documentation emphasis:**
- "Most important is to document so that next time I extend this for a specific project/product, the instructions can be followed for agentic development"
- Template should demonstrate patterns, not solve specific use cases
- Future extensibility is key — document extension points clearly

**Simplicity goal:**
- "Pick what fits template's simplicity goal but document future phases for extensibility"
- Balance working example with clean, understandable code

**OpenSpec integration:**
- AI module docs sync with OpenSpec trail for template-wide consistency

</specifics>

<deferred>
## Deferred Ideas

**Future Phases (New Capabilities):**
- **NLP2SQL for structured data** — Natural language to SQL queries, separate capability
- **Hybrid search with BM25** — Keyword-based search alongside vector search
- **OCR for PDF text extraction** — Knowledge extraction enhancement
- **Image/document embeddings** — Multimodal support beyond text
- **Batching via Celery/Temporal** — Could be Phase 6.1 or Phase 7+ infrastructure
- **MCP tool integration** — Sub-agents with MCP server connections
- **Configurable embedding models** — Support for local models (Sentence Transformers), other providers

**Extensibility Points to Document:**
- Embedding model swapping (OpenAI → local → custom)
- Additional search paradigms (BM25, NLP2SQL hooks)
- Chunking strategy customization
- Tool/MCP integration patterns for sub-agents

</deferred>

---

*Phase: 06-ai-module*
*Context gathered: 2026-02-16*
