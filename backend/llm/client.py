"""
OllamaClient — thin async wrapper around the Ollama HTTP API.
Handles chat completions with tool-calling support.
"""
from __future__ import annotations

import json
from typing import Any

import httpx

from backend.core.config import settings
from backend.core.logging import logger


class OllamaClient:
    """
    Async client for the Ollama local LLM server.

    Supports:
    - Single-turn completions
    - Multi-turn chat with message history
    - Tool calling via Ollama's native tool API
    - Streaming responses (Phase 1+)
    """

    def __init__(
        self,
        base_url: str = settings.OLLAMA_BASE_URL,
        model: str = settings.OLLAMA_MODEL,
        timeout: float = 120.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._client = httpx.AsyncClient(timeout=timeout)

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.2,
        stream: bool = False,
    ) -> dict[str, Any]:
        """
        Send a chat request to Ollama.

        Args:
            messages: Conversation history in OpenAI-compatible format.
            tools: Tool definitions (JSON schema) for tool-calling.
            temperature: Sampling temperature. Lower = more deterministic.
            stream: Whether to stream the response.

        Returns:
            Ollama response dict containing message content and tool_calls.
        """
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "options": {"temperature": temperature},
        }
        if tools:
            payload["tools"] = tools

        logger.debug("ollama_chat_request", model=self.model, message_count=len(messages))

        response = await self._client.post(
            f"{self.base_url}/api/chat",
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        logger.debug("ollama_chat_response", finish_reason=data.get("done_reason"))
        return data

    async def embed(self, text: str) -> list[float]:
        """Generate an embedding vector for the given text."""
        response = await self._client.post(
            f"{self.base_url}/api/embed",
            json={"model": settings.EMBEDDING_MODEL, "input": text},
        )
        response.raise_for_status()
        data = response.json()
        return data["embeddings"][0]

    async def health_check(self) -> bool:
        """Return True if Ollama server is reachable."""
        try:
            r = await self._client.get(f"{self.base_url}/api/tags", timeout=5.0)
            return r.status_code == 200
        except httpx.ConnectError:
            return False

    async def list_models(self) -> list[str]:
        """Return names of locally available Ollama models."""
        r = await self._client.get(f"{self.base_url}/api/tags")
        r.raise_for_status()
        return [m["name"] for m in r.json().get("models", [])]

    async def close(self) -> None:
        await self._client.aclose()
