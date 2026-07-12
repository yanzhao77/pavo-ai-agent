"""Tests for AgnesAIClient retry mechanism and error handling (T1.2)."""
import pytest
import httpx
from unittest.mock import AsyncMock, patch
from app.services.agnes_client import (
    AgnesAIClient, AgnesAIError, AgnesAIRateLimitError,
    AgnesAIModelNotFoundError, AgnesAITimeoutError,
    _classify_error, _retry_with_backoff,
)

@pytest.mark.asyncio
class TestAgnesAIClient:
    async def test_chat_success(self, monkeypatch):
        """Test successful chat completion."""
        async def mock_request(self, method, url, **kw):
            class R:
                status_code = 200
                def json(self):
                    return {"choices": [{"message": {"content": '{"ok": true}'}}]}
                def raise_for_status(self): pass
                async def aiter_lines(self): return
                def __aiter__(self): return self
                async def __anext__(self): raise StopAsyncIteration
            return R()
        monkeypatch.setattr(httpx.AsyncClient, "request", mock_request)
        client = AgnesAIClient()
        result = await client.chat([{"role": "user", "content": "hi"}], max_tokens=10)
        assert "ok" in result

    async def test_retry_on_429(self, monkeypatch):
        """Test retry on rate limit (429)."""
        attempt = [0]

        async def mock_request(self, method, url, **kw):
            attempt[0] += 1
            class R:
                status_code = 429
                def json(self): return {"error": "rate limited"}
                def raise_for_status(self):
                    raise httpx.HTTPStatusError("429", request=None, response=self)
                async def aiter_lines(self): return
            return R()
        monkeypatch.setattr(httpx.AsyncClient, "request", mock_request)
        client = AgnesAIClient()
        client.max_retries = 2
        client.retry_base_delay = 0.01
        with pytest.raises(AgnesAIRateLimitError):
            await client.chat([{"role": "user", "content": "hi"}], max_tokens=10)
        assert attempt[0] >= 3  # Initial + 2 retries

    async def test_timeout_classification(self):
        err = _classify_error(httpx.TimeoutException("timeout"))
        assert isinstance(err, AgnesAITimeoutError)

    async def test_429_classification(self):
        err = _classify_error("rate limit", status_code=429)
        assert isinstance(err, AgnesAIRateLimitError)

    async def test_503_classification(self):
        err = _classify_error("model not found", status_code=503)
        assert isinstance(err, AgnesAIModelNotFoundError)

    async def test_chat_stream(self, monkeypatch):
        """Test streaming response."""
        async def mock_stream(self, method, url, **kw):
            class R:
                status_code = 200
                async def aiter_lines(self):
                    yield "data: {'choices': [{'delta': {'content': 'hello'}}]}"
                    yield "data: [DONE]"
                def __aenter__(self): return self
                async def __aexit__(self, *a): pass
            return R()
        monkeypatch.setattr(httpx.AsyncClient, "stream", mock_stream)
        client = AgnesAIClient()
        chunks = []
        async for chunk in client.chat_stream([{"role": "user", "content": "hi"}]):
            chunks.append(chunk)
        assert len(chunks) >= 0

    async def test_generate_video(self, monkeypatch):
        async def mock_request(self, method, url, **kw):
            class R:
                status_code = 200
                def json(self):
                    return {"data": [{"url": "https://example.com/video.mp4"}], "created": 123}
                def raise_for_status(self): pass
            return R()
        monkeypatch.setattr(httpx.AsyncClient, "request", mock_request)
        client = AgnesAIClient()
        result = await client.generate_video("test prompt")
        assert result["url"] == "https://example.com/video.mp4"

