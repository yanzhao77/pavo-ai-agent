# verify imports
from app.config import settings
print("config OK:", settings.app_name)

from app.db.database import Base, engine
print("database OK")

from app.models.project import Project
print("models OK")

from app.agents.base import BaseAgent
print("agents base OK")

from app.agents.planner import PlannerAgent
from app.agents.character_agent import CharacterAgent
from app.agents.scene_agent import SceneAgent
from app.agents.prop_agent import PropAgent
from app.agents.storyboard_agent import StoryboardAgent
from app.agents.reviewer import ReviewerAgent
from app.agents.fixer import FixerAgent
print("all agents OK")

from app.services.agnes_client import agnes_client
print("agnes client OK")

from app.services.project_service import ProjectService
print("project service OK")

from app.api.routes import router
print("routes OK")

print("\nAll imports verified successfully!")
