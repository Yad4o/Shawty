"""
OmClaw FastAPI Application Entry Point
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import settings
from backend.core.logging import logger, setup_logging
from backend.database.connection import init_db
from backend.api.routes import chat, sessions, health


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle: startup and shutdown."""
    setup_logging()
    logger.info("omclaw_starting", model=settings.OLLAMA_MODEL)
    await init_db()
    logger.info("database_initialized")
    yield
    logger.info("omclaw_shutdown")


app = FastAPI(
    title="OmClaw",
    description="Local-first autonomous AI coding agent",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
