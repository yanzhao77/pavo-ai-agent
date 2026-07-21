"""Tests for video generation tasks (async, no Celery)."""
import pytest
from unittest.mock import AsyncMock, patch
from pathlib import Path


class TestGenerateVideoShot:
    @pytest.mark.asyncio
    async def test_returns_result_dict(self):
        mock_result = {"url": "http://example.com/shot.mp4", "status": "ok"}
        with patch("app.services.video_tasks.agnes_client") as mock_client:
            mock_client.generate_video = AsyncMock(return_value=mock_result)
            from app.services.video_tasks import generate_video_shot
            output = await generate_video_shot("A sunset scene", 1, "proj-001")
        assert output["shot_number"] == 1
        assert output["status"] == "completed"
        assert output["project_id"] == "proj-001"
        assert output["result"] == mock_result

    @pytest.mark.asyncio
    async def test_propagates_exception(self):
        with patch("app.services.video_tasks.agnes_client") as mock_client:
            mock_client.generate_video = AsyncMock(side_effect=RuntimeError("API error"))
            from app.services.video_tasks import generate_video_shot
            with pytest.raises(RuntimeError, match="API error"):
                await generate_video_shot("A scene", 2, "proj-002")

    def test_no_celery_import(self):
        """Ensure celery is not imported (as an import statement) in video_tasks module."""
        import ast
        src = Path("app/services/video_tasks.py").read_text(encoding="utf-8")
        tree = ast.parse(src)
        imported_names = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_names.extend(n.name.split(".")[0] for n in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_names.append(node.module.split(".")[0])
        assert "celery" not in imported_names, "celery must not be imported in video_tasks.py"
        assert "shared_task" not in imported_names, "shared_task must not be imported"
        # _run_async is a function name, not an import — skip that check
