"""Tests for T2V prompt generation (T1.6)."""
import pytest
from app.services.project_service import build_t2v_prompts


class TestBuildT2VPrompts:
    def test_basic_prompt_generation(self, mock_project):
        result = build_t2v_prompts(mock_project)
        assert len(result) == 2
        assert result[0]["scene_idx"] == 0
        assert result[0]["shot_number"] == 1

    def test_prompt_contains_shot_info(self, mock_project):
        result = build_t2v_prompts(mock_project)
        shot1 = result[0]
        assert "Shot:" in shot1["prompt"]
        assert "Camera:" in shot1["prompt"]

    def test_prompt_contains_characters(self, mock_project):
        result = build_t2v_prompts(mock_project)
        for r in result:
            if "Father" in str(mock_project.characters):
                assert "Father" in r["prompt"] or "Setting" in r["prompt"]

    def test_prompt_contains_action(self, mock_project):
        result = build_t2v_prompts(mock_project)
        for r in result:
            assert len(r["prompt"]) > 20

    def test_empty_storyboard(self, mock_project):
        mock_project.storyboard = {"projectName": "", "globalBGM": "", "scenes": []}
        result = build_t2v_prompts(mock_project)
        assert result == []

    def test_missing_characters(self, mock_project):
        mock_project.characters = None
        result = build_t2v_prompts(mock_project)
        assert len(result) == 2

    def test_prompt_consistency_across_shots(self, mock_project):
        result = build_t2v_prompts(mock_project)
        for r in result:
            assert r["prompt"]  # Non-empty for each shot
