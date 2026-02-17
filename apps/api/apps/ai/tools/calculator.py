"""
Calculator tool for safe mathematical expression evaluation.

Uses AST parsing to prevent arbitrary code execution.
Supports basic arithmetic operations: +, -, *, /
"""

import ast
import operator as op

from langchain_core.tools import tool


@tool
def calculate(expression: str) -> str:
    """Evaluate a simple mathematical expression. Example: '2 + 2' returns '4'.
    Supports +, -, *, / operations only."""
    try:
        # Parse expression into AST
        node = ast.parse(expression, mode="eval").body

        # Define safe operators
        operators = {
            ast.Add: op.add,
            ast.Sub: op.sub,
            ast.Mult: op.mul,
            ast.Div: op.truediv,
        }

        def evaluate_node(node):
            if isinstance(node, ast.Num):  # Number
                return node.n
            elif isinstance(node, ast.Constant):  # Python 3.8+ constant
                return node.value
            elif isinstance(node, ast.BinOp):  # Binary operation
                left = evaluate_node(node.left)
                right = evaluate_node(node.right)
                return operators[type(node.op)](left, right)
            else:
                raise ValueError("Unsupported operation")

        result = evaluate_node(node)
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"
