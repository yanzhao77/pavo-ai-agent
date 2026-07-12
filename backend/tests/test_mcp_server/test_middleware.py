"""Memory Middleware unit tests."""
import pytest, pytest_asyncio, os
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("AGNES_API_KEY", "test-key")
from mcp_server.middleware.memory_middleware import MemoryMiddleware


@pytest.mark.asyncio
async def test_middleware_empty_args():
    mw = MemoryMiddleware()
    result = await mw.pre_process("test_tool", {})
    assert "context" not in result


@pytest.mark.asyncio
async def test_middleware_with_user():
    mw = MemoryMiddleware()
    result = await mw.pre_process("test_tool", {"user_id": "alice"})
    assert result.get("context", {}).get("user_id") == "alice"


@pytest.mark.asyncio
async def test_middleware_degradation():
    mw = MemoryMiddleware()
    # Should not crash even with invalid input
    result = await mw.pre_process("test_tool", {"user_id": None})
    assert result is not None


@pytest.mark.asyncio
async def test_middleware_metrics():
    mw = MemoryMiddleware()
    await mw.pre_process("tool_a", {"user_id": "bob"})
    await mw.pre_process("tool_b", {"user_id": "bob"})
    metrics = mw.get_metrics()
    assert metrics["pre_process_count"] == 2
    assert "fallback_count" in metrics
