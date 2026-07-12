"""Tests for Celery video tasks (T2.5)."""
import pytest


class TestRunAsync:
    def test_run_async_basic(self):
        from app.services.video_tasks import _run_async
        async def sample():
            return "hello"
        result = _run_async(sample())
        assert result == "hello"

    def test_run_async_exception(self):
        from app.services.video_tasks import _run_async
        async def fail():
            raise ValueError("test error")
        with pytest.raises(ValueError):
            _run_async(fail())
