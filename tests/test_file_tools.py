"""
Tests for Phase 1: File Tools
Run with: pytest tests/test_file_tools.py -v
"""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

from backend.tools.file_tools import ReadFileTool, WriteFileTool, ListFilesTool, DeleteFileTool


@pytest.fixture
def temp_workspace(tmp_path):
    """Create a temporary workspace directory for tests."""
    with patch("backend.tools.file_tools.settings") as mock_settings:
        mock_settings.HOST_WORKSPACE_DIR = str(tmp_path)
        yield tmp_path


@pytest.mark.asyncio
async def test_write_then_read(temp_workspace):
    """WriteFileTool creates a file; ReadFileTool reads it back."""
    writer = WriteFileTool()
    reader = ReadFileTool()

    write_result = await writer.execute(path="hello.py", content="print('hello')")
    assert write_result.success
    assert "hello.py" in write_result.output

    read_result = await reader.execute(path="hello.py")
    assert read_result.success
    assert "print('hello')" in read_result.output


@pytest.mark.asyncio
async def test_read_nonexistent_file(temp_workspace):
    reader = ReadFileTool()
    result = await reader.execute(path="does_not_exist.py")
    assert not result.success
    assert "not found" in result.error.lower()


@pytest.mark.asyncio
async def test_path_traversal_blocked(temp_workspace):
    reader = ReadFileTool()
    result = await reader.execute(path="../../etc/passwd")
    assert not result.success
    assert "escape" in result.error.lower()


@pytest.mark.asyncio
async def test_list_files(temp_workspace):
    # Create some files
    (temp_workspace / "main.py").write_text("pass")
    (temp_workspace / "utils").mkdir()
    (temp_workspace / "utils" / "helpers.py").write_text("pass")

    lister = ListFilesTool()
    result = await lister.execute(path=".")
    assert result.success
    assert "main.py" in result.output
    assert "utils" in result.output


@pytest.mark.asyncio
async def test_delete_file(temp_workspace):
    (temp_workspace / "deleteme.txt").write_text("bye")

    deleter = DeleteFileTool()
    result = await deleter.execute(path="deleteme.txt")
    assert result.success
    assert not (temp_workspace / "deleteme.txt").exists()


@pytest.mark.asyncio
async def test_write_creates_parent_dirs(temp_workspace):
    writer = WriteFileTool()
    result = await writer.execute(path="nested/deep/file.py", content="x = 1")
    assert result.success
    assert (temp_workspace / "nested" / "deep" / "file.py").exists()
