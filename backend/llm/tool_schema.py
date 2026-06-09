"""
Tool schema builder.
Converts OmClaw tool definitions into Ollama-compatible JSON schemas.
"""
from __future__ import annotations

from typing import Any


def build_tool_schema(
    name: str,
    description: str,
    parameters: dict[str, Any],
    required: list[str] | None = None,
) -> dict[str, Any]:
    """
    Build an Ollama-compatible tool definition dict.

    Args:
        name: Tool function name (snake_case).
        description: What the tool does (shown to the LLM).
        parameters: JSON Schema object describing the parameters.
        required: List of required parameter names.

    Returns:
        Tool definition dict for inclusion in Ollama /api/chat payload.
    """
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": parameters,
                "required": required or [],
            },
        },
    }
