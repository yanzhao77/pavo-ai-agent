from pydantic import BaseModel, Field
from typing import Optional


class CharacterAppearance(BaseModel):
    build: str = ""
    face: str = ""
    eyes: str = ""
    hair: str = ""
    clothing: str = ""
    distinctive: str = ""


class CharacterSchema(BaseModel):
    name: str
    role: str = "supporting"
    age: str = ""
    gender: str = ""
    appearance: CharacterAppearance = Field(default_factory=CharacterAppearance)
    personality: list[str] = []
    voice: str = ""
    relationship: str = ""
    consistencyKey: str = ""


class SceneEnvironment(BaseModel):
    type: str = ""
    style: str = ""
    size: str = ""
    furniture: list[str] = []
    decor: list[str] = []
    flooring: str = ""


class SceneLighting(BaseModel):
    type: str = ""
    color: str = ""
    mood: str = ""


class SceneSchema(BaseModel):
    name: str
    timeOfDay: str = ""
    environment: SceneEnvironment = Field(default_factory=SceneEnvironment)
    lighting: SceneLighting = Field(default_factory=SceneLighting)
    atmosphere: str = ""


class PropSchema(BaseModel):
    name: str
    type: str = "prop"
    appearance: str = ""
    interaction: str = ""
    significance: str = ""


class ShotSchema(BaseModel):
    shotNumber: int
    shotType: str = "medium shot"
    cameraMove: str = "static"
    cameraAngle: str = "eye-level"
    description: str = ""
    dialogue: str = ""
    duration: str = "0s"
    characters: list[str] = []


class StoryboardSceneSchema(BaseModel):
    title: str = ""
    duration: str = "6s"
    mood: str = ""
    music: str = ""
    keyframe: str = ""
    shots: list[ShotSchema] = []


class StoryboardSchema(BaseModel):
    projectName: str = ""
    globalBGM: str = ""
    scenes: list[StoryboardSceneSchema] = []


def validate_characters(data: list) -> list:
    """Validate and clean character data."""
    if not isinstance(data, list):
        return []
    results = []
    for item in data:
        if not isinstance(item, dict):
            continue
        try:
            result = CharacterSchema(**item)
            results.append(result.model_dump())
        except Exception:
            results.append(item)  # Fallback to raw dict
    return results


def validate_scenes(data: list) -> list:
    """Validate and clean scene data."""
    if not isinstance(data, list):
        return []
    results = []
    for item in data:
        if not isinstance(item, dict):
            continue
        try:
            result = SceneSchema(**item)
            results.append(result.model_dump())
        except Exception:
            results.append(item)
    return results


def validate_props(data: list) -> list:
    if not isinstance(data, list):
        return []
    results = []
    for item in data:
        if not isinstance(item, dict):
            continue
        try:
            result = PropSchema(**item)
            results.append(result.model_dump())
        except Exception:
            results.append(item)
    return results


def validate_storyboard(data: dict) -> dict:
    if not isinstance(data, dict):
        return {"projectName": "", "globalBGM": "", "scenes": []}
    try:
        result = StoryboardSchema(**data)
        return result.model_dump()
    except Exception:
        return data
