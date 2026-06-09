"""
AgentController — the central brain of OmClaw.

Orchestrates the agentic loop:
  1. Receive user message
  2. Build context (history + memory + tools)
  3. Call Ollama
  4. If model returns tool_calls → dispatch via ToolRegistry → inject results → repeat
  5. Return final response to caller

This is a minimal but production-quality implementation for Phase 1.
Subsequent phases add: Docker sandboxing, Git/GitHub tools, memory retrieval, self-healing.
"""
from __future__ import annotations

import json
from typing import Any

from backend.core.logging import logger
from backend.llm.client import OllamaClient
from backend.tools.registry import ToolRegistry

SYSTEM_PROMPT = """\
You are OmClaw, a local-first autonomous AI coding agent.

You have access to tools for reading/writing files, running commands in a Docker sandbox,
interacting with Git and GitHub, searching the codebase semantically, and automating the browser.

## Rules
- Always use tools to take real actions. Never pretend.
- When writing code, write complete, production-quality implementations — no TODOs or placeholders.
- When you encounter an error, analyze it, fix the code, and retry automatically.
- Think step-by-step before acting. Briefly explain what you're about to do, then do it.
- Be concise in explanations. Be exhaustive in code.

## Tool Calling
Use tools by name exactly as defined. Provide all required parameters.
After each tool result, decide whether to call more tools or respond to the user.
"""


class AgentController:
    """
    Core agent loop — handles a single conversation turn (possibly multi-step).

    Args:
        llm: Initialized OllamaClient.
        tools: Initialized ToolRegistry with tools to expose to the model.
        max_iterations: Safety limit on tool-calling loop depth.
    """

    def __init__(
        self,
        llm: OllamaClient,
        tools: ToolRegistry,
        max_iterations: int = 20,
    ) -> None:
        self.llm = llm
        self.tools = tools
        self.max_iterations = max_iterations

    async def run(
        self,
        user_message: str,
        history: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """
        Run one agent turn.

        Args:
            user_message: The user's input.
            history: Prior conversation messages (for multi-turn context).

        Returns:
            Dict with 'response' (str), 'tool_calls' (list), 'iterations' (int).
        """
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
        ]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_message})

        tool_schemas = self.tools.get_ollama_schemas()
        all_tool_calls: list[dict[str, Any]] = []
        iterations = 0

        while iterations < self.max_iterations:
            iterations += 1
            logger.info("agent_iteration", iteration=iterations)

            response = await self.llm.chat(messages=messages, tools=tool_schemas)
            message = response.get("message", {})
            tool_calls = message.get("tool_calls", [])

            if not tool_calls:
                # No more tool calls — return final text response
                final_text = message.get("content", "")
                logger.info("agent_done", iterations=iterations)
                return {
                    "response": final_text,
                    "tool_calls": all_tool_calls,
                    "iterations": iterations,
                }

            # Append assistant message with tool_calls to history
            messages.append({"role": "assistant", "content": message.get("content", ""), "tool_calls": tool_calls})

            # Execute each tool call and collect results
            tool_results = []
            for call in tool_calls:
                fn = call.get("function", {})
                tool_name = fn.get("name", "")
                raw_args = fn.get("arguments", {})

                # Ollama may return arguments as a JSON string
                if isinstance(raw_args, str):
                    try:
                        raw_args = json.loads(raw_args)
                    except json.JSONDecodeError:
                        raw_args = {}

                logger.info("tool_call_dispatching", tool=tool_name, args=raw_args)
                result = await self.tools.execute(tool_name, **raw_args)
                all_tool_calls.append({"tool": tool_name, "args": raw_args, "success": result.success})

                tool_results.append({
                    "role": "tool",
                    "content": result.output if result.success else f"ERROR: {result.error}",
                    "tool_call_id": call.get("id", tool_name),
                })

            messages.extend(tool_results)

        logger.warning("agent_max_iterations_reached", max=self.max_iterations)
        return {
            "response": "Reached maximum iteration limit. The task may be incomplete.",
            "tool_calls": all_tool_calls,
            "iterations": iterations,
        }
