import pytest
import os

# Force test environment BEFORE any app imports
os.environ["AGNES_API_KEY"] = "test-key-12345"
os.environ["APP_ENV"] = "test"
os.environ["LOG_LEVEL"] = "CRITICAL"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["MINIO_ENDPOINT"] = "http://localhost:9000"
os.environ["MINIO_ACCESS_KEY"] = "minioadmin"
os.environ["MINIO_SECRET_KEY"] = "minioadmin"
os.environ["MINIO_BUCKET"] = "pavo-videos"



@pytest.fixture
def mock_project():
    """Create a mock project with sample data for testing."""
    class MockProject:
        pass
    p = MockProject()
    p.id = "test-id-123"
    p.title = "Test Project"
    p.input_raw = "A father comes home from work, his son brings him a foot basin"
    p.characters = [
        {
            "name": "Father",
            "role": "main",
            "age": "35",
            "appearance": {"build": "average", "face": "tired", "eyes": "kind",
                          "hair": "short black", "clothing": "white shirt and tie",
                          "distinctive": "wears glasses"},
            "personality": ["hardworking", "caring"],
            "consistencyKey": "Father: mid-30s Asian male, tired face",
        },
        {
            "name": "Son",
            "role": "main",
            "age": "5",
            "appearance": {"build": "small", "face": "round", "eyes": "big",
                          "hair": "short", "clothing": "pajamas",
                          "distinctive": "holding a small basin"},
            "personality": ["loving", "curious"],
            "consistencyKey": "Son: 5-year-old boy, round face",
        },
    ]
    p.scenes = [{
        "name": "Living Room",
        "timeOfDay": "evening",
        "environment": {"type": "indoor", "style": "modern", "size": "medium",
                       "furniture": ["sofa", "table"], "decor": ["family photos"],
                       "flooring": "wooden"},
        "lighting": {"type": "warm", "color": "yellow", "mood": "cozy"},
        "atmosphere": "warm and welcoming",
    }]
    p.props = [{
        "name": "Foot Basin",
        "type": "anchor",
        "appearance": "wooden basin with warm water",
        "interaction": "carrying, placing on floor",
        "significance": "symbol of filial piety",
    }]
    p.storyboard = {
        "projectName": "Test Project",
        "globalBGM": "Warm piano",
        "scenes": [{
            "title": "Act 1 - Homecoming",
            "duration": "15s",
            "mood": "Tired but warm",
            "music": "BGM: Piano",
            "keyframe": "Father enters door",
            "shots": [
                {"shotNumber": 1, "shotType": "wideshot", "cameraMove": "static",
                 "cameraAngle": "eye-level",
                 "description": "Father opens the door, looking tired",
                 "dialogue": "-", "duration": "0-8s", "characters": ["Father"]},
                {"shotNumber": 2, "shotType": "medium", "cameraMove": "static",
                 "cameraAngle": "eye-level",
                 "description": "Son approaches with basin",
                 "dialogue": "Son: Daddy, sit down", "duration": "8-15s",
                 "characters": ["Father", "Son"]},
            ],
        }],
    }
    p.trace_log = []
    p.videos = []
    p.status = "completed"
    return p
