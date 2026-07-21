"""Tests for Schema validation (T1.5)."""
import pytest
from app.models.schema import (
    CharacterSchema, SceneSchema, PropSchema, ShotSchema,
    StoryboardSchema, CharacterAppearance,
    validate_characters, validate_scenes, validate_props, validate_storyboard,
)


class TestCharacterSchema:
    def test_valid_character(self):
        data = {
            "name": "Xiao Ming",
            "role": "main",
            "age": "8",
            "appearance": {"build": "slim", "face": "round", "eyes": "big",
                          "hair": "short", "clothing": "red shirt", "distinctive": "freckles"},
            "personality": ["brave", "curious"],
            "consistencyKey": "Boy: 8-year-old, red shirt",
        }
        c = CharacterSchema(**data)
        assert c.name == "Xiao Ming"
        assert c.role == "main"
        assert len(c.appearance.build) > 0

    def test_minimal_character(self):
        c = CharacterSchema(name="Test")
        assert c.name == "Test"
        assert c.role == "supporting"

    def test_validate_characters_list(self):
        data = [{"name": "A", "role": "main", "appearance": {"build": "", "face": "", "eyes": "",
                 "hair": "", "clothing": "", "distinctive": ""}, "personality": [], "consistencyKey": "k"}]
        result = validate_characters(data)
        assert len(result) == 1
        assert result[0]["name"] == "A"

    def test_validate_characters_invalid(self):
        result = validate_characters("not a list")
        assert result == []

    def test_validate_characters_mixed(self):
        data = [{"name": "A", "role": "main", "consistencyKey": "k"},
                "not a dict"]
        result = validate_characters(data)
        assert len(result) == 1


class TestSceneSchema:
    def test_valid_scene(self):
        data = {
            "name": "Park",
            "timeOfDay": "day",
            "environment": {"type": "outdoor", "style": "natural", "size": "large",
                           "furniture": [], "decor": ["trees"], "flooring": "grass"},
            "lighting": {"type": "natural", "color": "warm", "mood": "bright"},
            "atmosphere": "peaceful",
        }
        s = SceneSchema(**data)
        assert s.name == "Park"

    def test_validate_scenes(self):
        data = [{"name": "Scene 1"}]
        result = validate_scenes(data)
        assert len(result) == 1

    def test_validate_scenes_invalid(self):
        assert validate_scenes(None) == []


class TestPropSchema:
    def test_valid_prop(self):
        p = PropSchema(name="Sword", type="anchor", appearance="shiny")
        assert p.name == "Sword"
        assert p.type == "anchor"

    def test_validate_props(self):
        data = [{"name": "Key", "type": "anchor", "appearance": "golden"}]
        result = validate_props(data)
        assert len(result) == 1

    def test_validate_props_invalid(self):
        assert validate_props("bad") == []


class TestShotSchema:
    def test_valid_shot(self):
        s = ShotSchema(shotNumber=1, shotType="medium", description="Action")
        assert s.shotNumber == 1
        assert s.characters == []


class TestStoryboardSchema:
    def test_valid_storyboard(self):
        data = {
            "projectName": "Test",
            "globalBGM": "Piano",
            "scenes": [{
                "title": "Act 1",
                "duration": "10s",
                "mood": "happy",
                "music": "BGM: Piano",
                "keyframe": "Opening scene",
                "shots": [{"shotNumber": 1, "shotType": "wide", "description": "Scene opens",
                          "duration": "0-5s", "characters": []}]
            }]
        }
        sb = StoryboardSchema(**data)
        assert len(sb.scenes) == 1
        assert len(sb.scenes[0].shots) == 1

    def test_empty_storyboard(self):
        sb = StoryboardSchema()
        assert sb.scenes == []

    def test_validate_storyboard_valid(self):
        data = {"projectName": "Test", "globalBGM": "", "scenes": []}
        result = validate_storyboard(data)
        assert result["projectName"] == "Test"

    def test_validate_storyboard_invalid(self):
        assert validate_storyboard(None) == {"projectName": "", "globalBGM": "", "scenes": []}
