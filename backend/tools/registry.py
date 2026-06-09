"""
Tool Registry — central registry for all available tools.
The AgentController loads tools from here and injects them into LLM calls.
"""
from __future__ import annotations

from typing import Any

from backend.tools.base import BaseTool, ToolResult
from backend.tools.file_tools import DeleteFileTool, ListFilesTool, ReadFileTool, WriteFileTool
from backend.core.logging import logger


class ToolRegistry:
    """
    Manages tool registration and dispatch.

    Usage:
        registry = ToolRegistry()
        registry.register_defaults()
        result = await registry.execute("read_file", path="main.py")
    """

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a single tool."""
        self._tools[tool.name] = tool
        logger.debug("tool_registered", name=tool.name)

    def register_defaults(self) -> None:
        """Register all Phase 1 tools (file tools)."""
        for tool in [ReadFileTool(), WriteFileTool(), ListFilesTool(), DeleteFileTool()]:
            self.register(tool)

    def get_ollama_schemas(self) -> list[dict[str, Any]]:
        """Return all tool schemas in Ollama format for injection into chat requests."""
        return [tool.to_ollama_schema() for tool in self._tools.values()]

    async def execute(self, tool_name: str, **kwargs: Any) -> ToolResult:
        """Dispatch a tool call by name."""
        tool = self._tools.get(tool_name)
        if not tool:
            logger.warning("tool_not_found", name=tool_name)
            return ToolResult(
                success=False,
                output="",
                error=f"Tool '{tool_name}' not found. Available: {list(self._tools.keys())}",
            )
        logger.info("tool_executing", name=tool_name, kwargs=list(kwargs.keys()))
        result = await tool.execute(**kwargs)
        logger.info("tool_result", name=tool_name, success=result.success)
        return result

    @property
    def tool_names(self) -> list[str]:
        return list(self._tools.keys())
