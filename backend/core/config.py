"""
OmClaw global settings — loaded from .env via pydantic-settings.
Single source of truth for all configuration.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # LLM
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5-coder:14b"

    # GitHub
    GITHUB_PAT: str = ""

    # Docker
    DOCKER_SANDBOX_IMAGE: str = "omclaw-sandbox:latest"
    DOCKER_WORKSPACE_DIR: str = "/workspace"
    HOST_WORKSPACE_DIR: str = "./workspace"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./omclaw.db"

    # Memory
    VECTOR_STORE: Literal["faiss", "chroma"] = "faiss"
    EMBEDDING_MODEL: str = "nomic-embed-text"

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_DEBUG: bool = True

    # Logging
    LOG_LEVEL: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
