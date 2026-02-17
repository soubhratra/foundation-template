"""
State schemas for LangGraph agents.

These TypedDict schemas define the state that flows through agent graphs.
Using Annotated with operator.add allows message accumulation per LangGraph patterns.
"""

import operator
from typing import Annotated, Sequence, TypedDict

from langchain_core.messages import BaseMessage


class QAState(TypedDict):
    """
    State schema for Q&A agent graph.

    Flow:
    1. messages: Accumulated conversation messages
    2. query: Extracted user query from last message
    3. intent: Routing decision - "rag" | "tool_agent" | "invalid"
    4. retrieved_chunks: Results from vector search (RAG path)
    5. answer: Generated response to user query
    6. loop_count: Iteration counter for termination tracking

    Intent values:
    - "rag": Use vector retrieval + LLM generation
    - "tool_agent": Use ReAct agent with Python function tools
    - "invalid": Query failed validation (too short, malformed, etc.)
    """

    messages: Annotated[Sequence[BaseMessage], operator.add]
    query: str
    intent: str  # "rag" | "tool_agent" | "invalid"
    retrieved_chunks: list[dict]
    answer: str
    loop_count: int
