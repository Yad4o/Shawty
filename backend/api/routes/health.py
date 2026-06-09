"""Health check endpoints."""
from __future__ import annotations

from fastapi import APIRouter

from backend.llm.client import OllamaClient
from backend.core.config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """Check API and Ollama connectivity."""
    client = OllamaClient()
    ollama_ok = await client.health_check()
    models = await client.list_models() if ollama_ok else []
    await client.close()
    return {
        "status": "ok",
        "ollama": ollama_ok,
        "model": settings.OLLAMA_MODEL,
        "model_available": settings.OLLAMA_MODEL in models,
        "available_models": models,
    }
