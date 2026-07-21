"""Integration tests for the full pipeline (T1.7)."""
import pytest
import httpx
from app.services.agnes_client import AgnesAIClient, _retry_with_backoff, AgnesAIError


@pytest.mark.asyncio
class TestRetryWithBackoff:
    async def test_success_first_try(self):
        """Function succeeds on first attempt."""
        calls = []
        async def fn():
            calls.append(1)
            return "ok"
        result = await _retry_with_backoff(fn, max_retries=2, base_delay=0.01)
        assert result == "ok"
        assert len(calls) == 1

    async def test_retry_then_success(self):
        """Function fails twice then succeeds."""
        calls = []
        async def fn():
            calls.append(1)
            if len(calls) < 3:
                from app.services.agnes_client import AgnesAIRateLimitError
                raise AgnesAIRateLimitError("rate limit")
            return "ok"
        result = await _retry_with_backoff(fn, max_retries=3, base_delay=0.01)
        assert result == "ok"
        assert len(calls) == 3

    async def test_exhaust_retries(self):
        """Function always fails, retries exhausted."""
        calls = []
        async def fn():
            calls.append(1)
            from app.services.agnes_client import AgnesAIRateLimitError
            raise AgnesAIRateLimitError("always fails")
        with pytest.raises(Exception):
            await _retry_with_backoff(fn, max_retries=2, base_delay=0.01)
        assert len(calls) == 3  # Initial + 2 retries

    async def test_non_retryable_error(self):
        """Non-retryable error propagates immediately."""
        async def fn():
            from app.services.agnes_client import AgnesAIError
            raise AgnesAIError("non-retryable")
        with pytest.raises(AgnesAIError):
            await _retry_with_backoff(fn, max_retries=3, base_delay=0.01)
