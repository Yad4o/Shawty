"""
Tests for OllamaClient.
These tests require a running Ollama server — skip if not available.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from backend.llm.client import OllamaClient


@pytest.mark.asyncio
async def test_health_check_success():
    """Mock: health check returns True when Ollama responds 200."""
    client = OllamaClient()
    with patch.object(client._client, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = MagicMock(status_code=200)
        result = await client.health_check()
    assert result is True
    await client.close()


@pytest.mark.asyncio
async def test_health_check_failure():
    """Mock: health check returns False when connection refused."""
    import httpx
    client = OllamaClient()
    with patch.object(client._client, "get", side_effect=httpx.ConnectError("refused")):
        result = await client.health_check()
    assert result is False
    await client.close()


@pytest.mark.asyncio
async def test_tool_schema_format():
    """Tool schema must conform to Ollama's expected format."""
    from backend.llm.tool_schema import build_tool_schema
    schema = build_tool_schema(
        name="read_file",
        description="Read a file",
        parameters={"path": {"type": "string"}},
        required=["path"],
    )
    assert schema["type"] == "function"
    assert schema["function"]["name"] == "read_file"
    assert "path" in schema["function"]["parameters"]["properties"]
