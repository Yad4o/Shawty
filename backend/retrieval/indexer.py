"""
Repository Indexer — Phase 6
Indexes a codebase for semantic search.
Chunks files by function/class, embeds with Ollama, stores in FAISS.
The agent can then query: "find where rate limiting is implemented"
"""
from __future__ import annotations

import ast
import asyncio
from pathlib import Path
from typing import Any

import numpy as np

from backend.core.logging import logger
from backend.llm.client import OllamaClient

SUPPORTED_EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java", ".md"}
CHUNK_SIZE = 100  # lines per chunk for non-parsed files


class RepoIndexer:
    """
    Indexes repository files into a FAISS vector store for semantic search.
    
    Design decisions:
    - Python files: parsed with AST → extract functions/classes as chunks
    - Other files: chunked by CHUNK_SIZE lines
    - Each chunk stores: file path, start line, content snippet
    """

    def __init__(self, workspace_path: str) -> None:
        self.workspace = Path(workspace_path)
        self._chunks: list[dict[str, Any]] = []
        self._embeddings: list[list[float]] = []
        self._index: Any = None

    def _collect_files(self) -> list[Path]:
        files = []
        for ext in SUPPORTED_EXTENSIONS:
            files.extend(self.workspace.rglob(f"*{ext}"))
        # Skip node_modules, __pycache__, .git
        skip = {"node_modules", "__pycache__", ".git", "venv", ".venv"}
        return [f for f in files if not any(s in f.parts for s in skip)]

    def _chunk_python(self, path: Path) -> list[dict[str, Any]]:
        """Use AST to extract functions and classes as separate chunks."""
        try:
            source = path.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(source)
            lines = source.splitlines()
            chunks = []
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    start = node.lineno - 1
                    end = getattr(node, "end_lineno", start + 20)
                    snippet = "\n".join(lines[start:end])
                    chunks.append({
                        "file": str(path.relative_to(self.workspace)),
                        "type": type(node).__name__,
                        "name": node.name,
                        "line": node.lineno,
                        "content": snippet[:2000],  # cap size
                    })
            return chunks
        except SyntaxError:
            return self._chunk_generic(path)

    def _chunk_generic(self, path: Path) -> list[dict[str, Any]]:
        """Chunk non-Python files by line count."""
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except Exception:
            return []
        chunks = []
        for i in range(0, len(lines), CHUNK_SIZE):
            chunk_lines = lines[i: i + CHUNK_SIZE]
            chunks.append({
                "file": str(path.relative_to(self.workspace)),
                "type": "chunk",
                "name": f"lines_{i}_{i + CHUNK_SIZE}",
                "line": i + 1,
                "content": "\n".join(chunk_lines),
            })
        return chunks

    async def index(self) -> int:
        """Index the entire workspace. Returns number of chunks indexed."""
        files = self._collect_files()
        logger.info("repo_indexer_start", files=len(files))

        all_chunks = []
        for file in files:
            if file.suffix == ".py":
                all_chunks.extend(self._chunk_python(file))
            else:
                all_chunks.extend(self._chunk_generic(file))

        if not all_chunks:
            logger.warning("repo_indexer_no_chunks")
            return 0

        # Embed all chunks
        llm = OllamaClient()
        embeddings = []
        for chunk in all_chunks:
            text = f"File: {chunk['file']}\n{chunk['content']}"
            emb = await llm.embed(text)
            embeddings.append(emb)
        await llm.close()

        # Build FAISS index
        import faiss
        dim = len(embeddings[0])
        index = faiss.IndexFlatL2(dim)
        matrix = np.array(embeddings, dtype="float32")
        index.add(matrix)

        self._chunks = all_chunks
        self._embeddings = embeddings
        self._index = index

        logger.info("repo_indexed", chunks=len(all_chunks))
        return len(all_chunks)

    async def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Semantic search over indexed codebase."""
        if self._index is None or self._index.ntotal == 0:
            return [{"error": "Repository not indexed. Call index() first."}]

        llm = OllamaClient()
        q_emb = await llm.embed(query)
        await llm.close()

        vec = np.array([q_emb], dtype="float32")
        distances, indices = self._index.search(vec, min(top_k, self._index.ntotal))

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx >= 0:
                chunk = self._chunks[int(idx)].copy()
                chunk["score"] = float(dist)
                results.append(chunk)
        return results
