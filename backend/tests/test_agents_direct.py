"""Phase 1 - P1.2: Agent direct call tests."""
import pytest
import json
from unittest.mock import patch, AsyncMock, MagicMock
from app.agents.planner import PlannerAgent
from app.agents.character_agent import CharacterAgent
from app.agents.scene_agent import SceneAgent
from app.agents.prop_agent import PropAgent
from app.agents.storyboard_agent import StoryboardAgent
from app.agents.reviewer import ReviewerAgent
from app.agents.fixer import FixerAgent


SAMPLE_CHARACTERS = [
    {"name": "Father", "role": "main", "age": "35", "personality": ["caring"],
     "appearance": {"build": "average", "face": "kind", "eyes": "warm",
                   "hair": "short", "clothing": "shirt", "distinctive": ""},
     "consistencyKey": "Father description"}
]
SAMPLE_SCENES = [
    {"name": "Living Room", "timeOfDay": "evening",
     "environment": {"type": "indoor", "style": "modern", "size": "medium",
                    "furniture": [], "decor": [], "flooring": "wood"},
     "lighting": {"type": "warm", "color": "yellow", "mood": "cozy"},
     "atmosphere": "warm"}
]
SAMPLE_PROPS = [
    {"name": "Basin", "type": "anchor", "appearance": "wooden",
     "interaction": "carrying", "significance": "symbol"}
]


def mock_chat_response(json_data):
    """Create a mock for agnes_client.chat that returns JSON."""
    async def mock_chat(*args, **kwargs):
        return json.dumps(json_data, ensure_ascii=False)
    return mock_chat


@pytest.mark.asyncio
class TestPlannerAgent:
    async def test_plan_returns_dict(self):
        agent = PlannerAgent()
        with patch("app.agents.base.agnes_client.chat", new=mock_chat_response({
            "characters": ["Father", "Son"],
            "scene": "Living Room",
            "theme": "Family Love",
            "emotion": "warm",
            "duration": "45s"
        })):
            result = await agent.plan("A father comes home from work")
            assert isinstance(result, dict)
            assert "characters" in result
            assert "theme" in result

    async def test_plan_invalid_json_fallback(self):
        agent = PlannerAgent()
        async def bad_chat(*args, **kwargs):
            return "not valid json at all"
        with patch("app.agents.base.agnes_client.chat", new=bad_chat):
            result = await agent.plan("test")
            assert isinstance(result, dict)
            assert "raw" in result


@pytest.mark.asyncio
class TestCharacterAgent:
    async def test_generate_returns_list(self):
        agent = CharacterAgent()
        with patch("app.agents.base.agnes_client.chat", new=mock_chat_response(SAMPLE_CHARACTERS)):
            result = await agent.generate("test story")
            assert isinstance(result, list)
            assert len(result) > 0

    async def test_generate_invalid_json(self):
        agent = CharacterAgent()
        async def bad_chat(*args, **kwargs):
            return "[invalid json"
        with patch("app.agents.base.agnes_client.chat", new=bad_chat):
            result = await agent.generate("test")
            assert result == []


@pytest.mark.asyncio
class TestSceneAgent:
    async def test_generate_returns_list(self):
        agent = SceneAgent()
        with patch("app.agents.base.agnes_client.chat", new=mock_chat_response(SAMPLE_SCENES)):
            result = await agent.generate("test", SAMPLE_CHARACTERS)
            assert isinstance(result, list)

    async def test_generate_empty_input(self):
        agent = SceneAgent()
        with patch("app.agents.base.agnes_client.chat", new=mock_chat_response(SAMPLE_SCENES)):
            result = await agent.generate("", [])
            assert isinstance(result, list)


@pytest.mark.asyncio
class TestPropAgent:
    async def test_generate_returns_list(self):
        agent = PropAgent()
        with patch("app.agents.base.agnes_client.chat", new=mock_chat_response(SAMPLE_PROPS)):
            result = await agent.generate("test", SAMPLE_CHARACTERS, SAMPLE_SCENES)
            assert isinstance(result, list)


@pytest.mark.asyncio
class TestStoryboardAgent:
    async def test_generate_returns_dict_with_scenes(self):
        agent = StoryboardAgent()
        sample_sb = {"projectName": "Test", "globalBGM": "", "scenes": []}
        with patch("app.agents.base.agnes_client.chat", new=mock_chat_response(sample_sb)):
            result = await agent.generate("test", SAMPLE_CHARACTERS, SAMPLE_SCENES, SAMPLE_PROPS)
            assert isinstance(result, dict)
            assert "scenes" in result

    async def test_generate_invalid_fallback(self):
        agent = StoryboardAgent()
        async def bad_chat(*args, **kwargs):
            return "invalid"
        with patch("app.agents.base.agnes_client.chat", new=bad_chat):
            result = await agent.generate("test", [], [], [])
            assert result == {"projectName": "", "globalBGM": "", "scenes": []}


@pytest.mark.asyncio
class TestReviewerAgent:
    async def test_review_returns_dict(self):
        agent = ReviewerAgent()
        review_data = {"passed": True, "issues": [], "needs_fix": False}
        with patch("app.agents.base.agnes_client.chat", new=mock_chat_response(review_data)):
            mock_project = MagicMock()
            mock_project.characters = SAMPLE_CHARACTERS
            mock_project.scenes = SAMPLE_SCENES
            mock_project.props = SAMPLE_PROPS
            mock_project.storyboard = {"scenes": []}
            result = await agent.review(mock_project)
            assert isinstance(result, dict)
            assert "passed" in result


@pytest.mark.asyncio
class TestFixerAgent:
    async def test_fix_returns_dict_with_scenes(self):
        agent = FixerAgent()
        original_sb = {"projectName": "Test", "scenes": [{"title": "Act 1"}]}
        with patch("app.agents.base.agnes_client.chat", new=mock_chat_response(original_sb)):
            mock_project = MagicMock()
            mock_project.storyboard = original_sb
            review = {"issues": [{"severity": "high", "description": "missing emotion"}], "needs_fix": True}
            result = await agent.fix(mock_project, review)
            assert isinstance(result, dict)
            assert "scenes" in result

    async def test_fix_invalid_fallback(self):
        agent = FixerAgent()
        original_sb = {"projectName": "Test", "scenes": []}
        async def bad_chat(*args, **kwargs):
            return "bad data"
        with patch("app.agents.base.agnes_client.chat", new=bad_chat):
            mock_project = MagicMock()
            mock_project.storyboard = original_sb
            result = await agent.fix(mock_project, {"issues": []})
            assert result == original_sb  # Falls back to original
