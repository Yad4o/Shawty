"""
Memory Store — Phase 5
SQLite-backed long-term memory + FAISS vector index for semantic retrieval.

The agent uses this to:
- Remember facts, errors, and fixes across sessions
- Retrieve relevant past context during new tasks
- Track goals and their completion status
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.core.config import settings
from backend.core.logging import logger
from backend.database.models import MemoryEntry
from backend.llm.client import OllamaClient


class MemoryStore:
    """
    Hybrid memory: SQLite (structured) + FAISS (semantic).
    
    On write: embed the content → store in FAISS + SQLite.
    On read: embed query → FAISS similarity → return top-k entries.
    """

    def __init__(self, index_path: str = "./memory/faiss.index") -> None:
        self._index_path = Path(index_path)
        self._index_path.parent.mkdir(exist_ok=True)
        self._faiss_index: Any = None  # Lazy-loaded
        self._id_map: dict[int, str] = {}  # FAISS int id → SQLite uuid

    def _get_index(self, dim: int = 768):
        """Lazy-init FAISS index."""
        if self._faiss_index is None:
            try:
                import faiss
                if self._index_path.exists():
                    self._faiss_index = faiss.read_index(str(self._index_path))
                else:
                    self._faiss_index = faiss.IndexFlatL2(dim)
            except ImportError:
                logger.warning("faiss_not_installed", msg="Memory semantic search disabled")
        return self._faiss_index

    async def add(
        self,
        content: str,
        category: str = "general",
        session_id: str | None = None,
        db: AsyncSession | None = None,
    ) -> str:
        """Store a memory entry. Returns the entry ID."""
        llm = OllamaClient()
        embedding = await llm.embed(content)
        await llm.close()

        entry_id = str(uuid.uuid4())

        # Store in FAISS
        index = self._get_index(dim=len(embedding))
        if index is not None:
            import faiss
            vec = np.array([embedding], dtype="float32")
            faiss_id = index.ntotal
            index.add(vec)
            self._id_map[faiss_id] = entry_id
            faiss.write_index(index, str(self._index_path))

        # Store in SQLite (if db session provided)
        if db:
            entry = MemoryEntry(
                id=entry_id,
                session_id=session_id,
                category=category,
                content=content,
                embedding_id=str(len(self._id_map) - 1),
            )
            db.add(entry)
            await db.flush()

        logger.debug("memory_added", id=entry_id[:8], category=category)
        return entry_id

    async def search(
        self,
        query: str,
        top_k: int = 5,
        db: AsyncSession | None = None,
    ) -> list[dict[str, str]]:
        """Semantic search over stored memories."""
        llm = OllamaClient()
        query_embedding = await llm.embed(query)
        await llm.close()

        index = self._get_index(dim=len(query_embedding))
        if index is None or index.ntotal == 0:
            return []

        import faiss
        vec = np.array([query_embedding], dtype="float32")
        distances, indices = index.search(vec, min(top_k, index.ntotal))

        entry_ids = [self._id_map.get(int(i)) for i in indices[0] if int(i) >= 0]
        entry_ids = [eid for eid in entry_ids if eid]

        if not entry_ids or db is None:
            return [{"id": eid, "content": "..."} for eid in entry_ids]

        result = await db.execute(select(MemoryEntry).where(MemoryEntry.id.in_(entry_ids)))
        entries = result.scalars().all()
        return [{"id": e.id, "category": e.category, "content": e.content} for e in entries]
