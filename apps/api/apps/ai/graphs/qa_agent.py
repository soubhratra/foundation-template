"""
Q&A LangGraph agent demonstrating agentic RAG patterns.

This agent showcases:
- Guardrails for input validation
- Intent detection for routing (RAG vs tool agent)
- Vector retrieval using search_documents service
- LLM-based answer generation from retrieved chunks
- ReAct agent with Python function tools
- Conditional routing based on state
- Loop termination for safety

Architecture:
    Entry → Guardrails → Intent Detection → [RAG Path | Tool Agent Path] → End

RAG Path: rag_retrieval → generate_answer
Tool Path: tool_agent
Invalid: END (early exit)
"""

import logging
from typing import Literal

from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import create_react_agent

from apps.ai.graphs.state import QAState
from apps.ai.services import search_documents
from apps.ai.tools import calculate, count_words, reverse_string

logger = logging.getLogger(__name__)


def guardrails_node(state: QAState) -> dict:
    """
    Validate input query and extract query from messages.

    Rules:
    - Query must be at least 3 characters
    - Last message must be a HumanMessage

    Returns:
        Updates to state: query (extracted), intent ("invalid" or "pending")
    """
    messages = state["messages"]

    # Extract last message
    if not messages:
        logger.warning("No messages provided")
        return {"intent": "invalid", "query": ""}

    last_message = messages[-1]

    # Validate message type
    if not isinstance(last_message, HumanMessage):
        logger.warning(f"Last message is not HumanMessage: {type(last_message)}")
        return {"intent": "invalid", "query": ""}

    # Extract and validate query
    query = last_message.content.strip() if isinstance(last_message.content, str) else ""

    if len(query) < 3:
        logger.warning(f"Query too short: {query}")
        return {"intent": "invalid", "query": query}

    # Passed validation
    return {"intent": "pending", "query": query}


def intent_detection_node(state: QAState) -> dict:
    """
    Determine routing intent based on query content.

    Simple keyword-based routing (production would use LLM classification):
    - Keywords like "calculate", "reverse", "count" → tool_agent
    - All other queries → rag

    If intent is already "invalid" from guardrails, skip detection.

    Returns:
        Updates to state: intent ("rag" or "tool_agent")
    """
    # If guardrails already marked as invalid, don't override
    if state["intent"] == "invalid":
        logger.info("Query already marked invalid by guardrails")
        return {}

    query = state["query"].lower()

    # Check for tool-specific keywords
    tool_keywords = ["calculate", "reverse", "count", "add", "subtract", "multiply", "divide"]

    if any(keyword in query for keyword in tool_keywords):
        logger.info(f"Routing to tool_agent for query: {query}")
        return {"intent": "tool_agent"}

    # Default to RAG for knowledge retrieval
    logger.info(f"Routing to RAG for query: {query}")
    return {"intent": "rag"}


def rag_retrieval_node(state: QAState) -> dict:
    """
    Perform vector search to retrieve relevant document chunks.

    Uses search_documents service from apps.ai.services.
    Returns top 5 most similar chunks.

    Returns:
        Updates to state: retrieved_chunks, loop_count
    """
    query = state["query"]
    loop_count = state["loop_count"] + 1

    try:
        # Search for relevant chunks
        chunks = search_documents(
            query=query,
            limit=5,
            similarity_threshold=0.7,
        )

        logger.info(f"Retrieved {len(chunks)} chunks for query: {query}")
        return {"retrieved_chunks": chunks, "loop_count": loop_count}

    except Exception as e:
        logger.exception(f"RAG retrieval failed: {e}")
        # Return empty results on error (graceful degradation)
        return {"retrieved_chunks": [], "loop_count": loop_count}


def generate_answer_node(state: QAState) -> dict:
    """
    Generate answer from retrieved chunks using LLM.

    Uses GPT-4o-mini with retrieved chunks as context.
    Appends AIMessage to conversation history.

    Returns:
        Updates to state: answer, messages (appended), loop_count
    """
    query = state["query"]
    chunks = state["retrieved_chunks"]
    loop_count = state["loop_count"] + 1

    # Build context from retrieved chunks
    if not chunks:
        context = "No relevant information found in the knowledge base."
    else:
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            context_parts.append(f"[{i}] {chunk['text']} (from: {chunk['document_title']})")
        context = "\n\n".join(context_parts)

    # Build prompt
    prompt = f"""Answer the following question using the provided context.
If the context doesn't contain relevant information, say so.

Context:
{context}

Question: {query}

Answer:"""

    try:
        # Generate answer using LLM
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        response = llm.invoke([HumanMessage(content=prompt)])
        answer = response.content

        logger.info(f"Generated answer for query: {query}")

        # Append AI message to conversation
        new_messages = [AIMessage(content=answer)]

        return {
            "answer": answer,
            "messages": new_messages,
            "loop_count": loop_count,
        }

    except Exception as e:
        logger.exception(f"Answer generation failed: {e}")
        error_message = "I encountered an error while generating an answer."

        return {
            "answer": error_message,
            "messages": [AIMessage(content=error_message)],
            "loop_count": loop_count,
        }


def tool_agent_node(state: QAState) -> dict:
    """
    Sub-agent with Python function tools using ReAct pattern.

    Creates an agent with calculator and string manipulation tools.
    Agent reasons about tool usage and executes them as needed.

    Returns:
        Updates to state: answer, messages (appended), loop_count
    """
    query = state["query"]
    loop_count = state["loop_count"] + 1

    try:
        # Create ReAct agent with tools
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        tools = [calculate, reverse_string, count_words]

        agent = create_react_agent(llm, tools)

        # Invoke agent with query
        result = agent.invoke({"messages": [HumanMessage(content=query)]})

        # Extract answer from agent response
        agent_messages = result.get("messages", [])
        if agent_messages:
            # Get last message (should be AI response)
            last_message = agent_messages[-1]
            answer = last_message.content if hasattr(last_message, "content") else str(last_message)
        else:
            answer = "Tool agent completed but produced no response."

        logger.info(f"Tool agent completed for query: {query}")

        # Append AI message to conversation
        new_messages = [AIMessage(content=answer)]

        return {
            "answer": answer,
            "messages": new_messages,
            "loop_count": loop_count,
        }

    except Exception as e:
        logger.exception(f"Tool agent failed: {e}")
        error_message = "I encountered an error while using tools."

        return {
            "answer": error_message,
            "messages": [AIMessage(content=error_message)],
            "loop_count": loop_count,
        }


def should_continue(state: QAState) -> Literal["rag_retrieval", "tool_agent", END]:
    """
    Conditional routing function.

    Routes based on intent and loop count:
    - invalid → END (early exit)
    - rag → rag_retrieval
    - tool_agent → tool_agent
    - loop_count >= 10 → END (prevent infinite loops)

    Returns:
        Next node name or END
    """
    intent = state["intent"]
    loop_count = state.get("loop_count", 0)

    # Termination check
    if loop_count >= 10:
        logger.warning(f"Max loop count reached: {loop_count}")
        return END

    # Route based on intent
    if intent == "invalid":
        logger.info("Invalid query, ending early")
        return END
    elif intent == "rag":
        return "rag_retrieval"
    elif intent == "tool_agent":
        return "tool_agent"
    else:
        logger.warning(f"Unknown intent: {intent}, ending")
        return END


def build_qa_graph():
    """
    Build and compile the Q&A agent graph.

    Flow:
        Entry → guardrails → intent_detection → [conditional routing]
            ├─ rag: rag_retrieval → generate_answer → END
            ├─ tool_agent: tool_agent → END
            └─ invalid: END

    Returns:
        Compiled LangGraph instance ready for invocation
    """
    graph = StateGraph(QAState)

    # Add nodes
    graph.add_node("guardrails", guardrails_node)
    graph.add_node("intent_detection", intent_detection_node)
    graph.add_node("rag_retrieval", rag_retrieval_node)
    graph.add_node("generate_answer", generate_answer_node)
    graph.add_node("tool_agent", tool_agent_node)

    # Add edges
    graph.set_entry_point("guardrails")
    graph.add_edge("guardrails", "intent_detection")
    graph.add_conditional_edges("intent_detection", should_continue)
    graph.add_edge("rag_retrieval", "generate_answer")
    graph.add_edge("generate_answer", END)
    graph.add_edge("tool_agent", END)

    return graph.compile()
