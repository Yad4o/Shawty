"""
BaseTool — abstract base class all OmClaw tools inherit from.
Provides a consistent interface for tool registration and execution.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class ToolResult(BaseModel):
    """Standardized return type for every tool call."""

    success: bool
    output: str
    error: str | None = None
    metadata: dict[str, Any] = {}


class BaseTool(ABC):
    """
    Abstract base for all OmClaw tools.

    Subclasses must implement:
    - name: str            — snake_case identifier used in tool calls
    - description: str     — shown to the LLM to describe capability
    - schema: dict         — JSON Schema for parameters
    - execute(**kwargs)    — async execution logic
    """

    name: str
    description: str
    schema: dict[str, Any]

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the tool with provided arguments."""
        ...

    def to_ollama_schema(self) -> dict[str, Any]:
        """Return the Ollama-compatible tool definition."""
        from backend.llm.tool_schema import build_tool_schema
        return build_tool_schema(
            name=self.name,
            description=self.description,
            parameters=self.schema.get("properties", {}),
            required=self.schema.get("required", []),
        )
