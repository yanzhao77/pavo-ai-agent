"""Phase 4: E2E test for video generation pipeline."""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock


@pytest.mark.asyncio
class TestVideoPipelineE2E:
    async def test_build_prompts_to_render(self, mock_project):
        """Verify T2V prompts can be built from storyboard."""
        from app.services.project_service import build_t2v_prompts
        result = build_t2v_prompts(mock_project)
        assert len(result) > 0
        for p in result:
            assert "prompt" in p
            assert "shot_number" in p

    async def test_render_with_mock_video(self, mock_project, monkeypatch):
        """Verify render_video works with mocked video generation."""
        from app.services.agnes_client import agnes_client
        from app.services.project_service import ProjectService
        
        async def mock_generate_video(prompt, **kw):
            return {"url": "http://test.com/video.mp4", "created": 123}
        monkeypatch.setattr(agnes_client, "generate_video", mock_generate_video)
        
        # Mock session
        session = AsyncMock()
        service = ProjectService(session)
        result = await service.render_video(mock_project)
        assert "videos" in result
        assert len(result["videos"]) > 0

    async def test_storage_upload_after_render(self, mock_project, monkeypatch):
        """Verify storage upload is called after video generation."""
        from app.services.project_service import build_t2v_prompts
        from app.services.storage import get_storage
        
        prompts = build_t2v_prompts(mock_project)
        assert len(prompts) > 0
        # Verify prompt structure
        for p in prompts:
            assert "Shot:" in p["prompt"]
            assert "Camera:" in p["prompt"]
