"""
File Tools — Phase 1
Read, write, list, and delete files in the workspace.
All paths are resolved relative to the configured workspace directory.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from backend.core.config import settings
from backend.core.logging import logger
from backend.tools.base import BaseTool, ToolResult


def _safe_resolve(path: str, base: Path) -> Path:
    """Resolve path and ensure it stays within the workspace."""
    resolved = (base / path).resolve()
    if not str(resolved).startswith(str(base.resolve())):
        raise ValueError(f"Path escape attempt: {path!r}")
    return resolved


class ReadFileTool(BaseTool):
    name = "read_file"
    description = "Read the contents of a file in the workspace. Returns the file content as a string."
    schema: dict[str, Any] = {
        "properties": {
            "path": {"type": "string", "description": "Relative path to the file within the workspace."},
        },
        "required": ["path"],
    }

    async def execute(self, path: str) -> ToolResult:
        base = Path(settings.HOST_WORKSPACE_DIR)
        try:
            resolved = _safe_resolve(path, base)
            content = resolved.read_text(encoding="utf-8")
            logger.info("file_read", path=path, size=len(content))
            return ToolResult(success=True, output=content)
        except FileNotFoundError:
            return ToolResult(success=False, output="", error=f"File not found: {path}")
        except ValueError as e:
            return ToolResult(success=False, output="", error=str(e))
        except Exception as e:
            return ToolResult(success=False, output="", error=f"Read error: {e}")


class WriteFileTool(BaseTool):
    name = "write_file"
    description = "Write content to a file in the workspace. Creates parent directories if needed. Overwrites existing files."
    schema: dict[str, Any] = {
        "properties": {
            "path": {"type": "string", "description": "Relative path to the file within the workspace."},
            "content": {"type": "string", "description": "Content to write to the file."},
        },
        "required": ["path", "content"],
    }

    async def execute(self, path: str, content: str) -> ToolResult:
        base = Path(settings.HOST_WORKSPACE_DIR)
        try:
            resolved = _safe_resolve(path, base)
            resolved.parent.mkdir(parents=True, exist_ok=True)
            resolved.write_text(content, encoding="utf-8")
            logger.info("file_written", path=path, size=len(content))
            return ToolResult(success=True, output=f"Written {len(content)} bytes to {path}")
        except ValueError as e:
            return ToolResult(success=False, output="", error=str(e))
        except Exception as e:
            return ToolResult(success=False, output="", error=f"Write error: {e}")


class ListFilesTool(BaseTool):
    name = "list_files"
    description = "List files and directories in a workspace path. Returns a tree-like representation."
    schema: dict[str, Any] = {
        "properties": {
            "path": {
                "type": "string",
                "description": "Relative path to directory. Defaults to workspace root.",
                "default": ".",
            },
            "depth": {
                "type": "integer",
                "description": "Max depth to recurse. Default 2.",
                "default": 2,
            },
        },
        "required": [],
    }

    async def execute(self, path: str = ".", depth: int = 2) -> ToolResult:
        base = Path(settings.HOST_WORKSPACE_DIR)
        try:
            resolved = _safe_resolve(path, base)
            if not resolved.exists():
                return ToolResult(success=False, output="", error=f"Directory not found: {path}")
            lines = []
            self._walk(resolved, lines, prefix="", depth=depth, current=0)
            return ToolResult(success=True, output="\n".join(lines))
        except ValueError as e:
            return ToolResult(success=False, output="", error=str(e))
        except Exception as e:
            return ToolResult(success=False, output="", error=f"List error: {e}")

    def _walk(self, path: Path, lines: list[str], prefix: str, depth: int, current: int) -> None:
        if current > depth:
            return
        try:
            entries = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name))
        except PermissionError:
            return
        for i, entry in enumerate(entries):
            connector = "└── " if i == len(entries) - 1 else "├── "
            lines.append(f"{prefix}{connector}{entry.name}{'/' if entry.is_dir() else ''}")
            if entry.is_dir():
                extension = "    " if i == len(entries) - 1 else "│   "
                self._walk(entry, lines, prefix + extension, depth, current + 1)


class DeleteFileTool(BaseTool):
    name = "delete_file"
    description = "Delete a file from the workspace."
    schema: dict[str, Any] = {
        "properties": {
            "path": {"type": "string", "description": "Relative path to the file to delete."},
        },
        "required": ["path"],
    }

    async def execute(self, path: str) -> ToolResult:
        base = Path(settings.HOST_WORKSPACE_DIR)
        try:
            resolved = _safe_resolve(path, base)
            if not resolved.exists():
                return ToolResult(success=False, output="", error=f"File not found: {path}")
            resolved.unlink()
            logger.info("file_deleted", path=path)
            return ToolResult(success=True, output=f"Deleted: {path}")
        except ValueError as e:
            return ToolResult(success=False, output="", error=str(e))
        except Exception as e:
            return ToolResult(success=False, output="", error=f"Delete error: {e}")
