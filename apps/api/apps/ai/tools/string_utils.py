"""
String manipulation tools for demonstration purposes.

These simple tools show the @tool decorator pattern for LangGraph agents.
"""

from langchain_core.tools import tool


@tool
def reverse_string(text: str) -> str:
    """Reverse a string. Example: 'hello' returns 'olleh'."""
    return text[::-1]


@tool
def count_words(text: str) -> str:
    """Count words in a string. Example: 'hello world' returns '2'."""
    return str(len(text.split()))
