"""Project adapter — bridges MCP Server to existing ProjectService."""
import uuid, logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.project import Project, ProjectStatus
from app.services.project_service import ProjectService
from app.agents.character_agent import CharacterAgent
from app.agents.scene_agent import SceneAgent
from app.agents.storyboard_agent import StoryboardAgent
from app.models.schema import validate_characters, validate_scenes, validate_storyboard

logger = logging.getLogger(__name__)

class ProjectAdapter:
    """Wraps existing ProjectService for MCP Tool use."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.service = ProjectService(session)

    async def create_project(self, input_text: str, user_id: str = "") -> dict:
        project = await self.service.create_project(input_text, user_id)
        import asyncio
        asyncio.create_task(self.service.run_workflow(project.id))
        return {"project_id": str(project.id), "status": "generating"}

    async def get_project(self, project_id_str: str) -> dict:
        try:
            project_id = uuid.UUID(project_id_str)
        except ValueError:
            raise ValueError(f"Invalid project_id: {project_id_str}")
        stmt = select(Project).where(Project.id == project_id)
        r = await self.session.execute(stmt)
        p = r.scalar_one_or_none()
        if not p:
            raise ValueError(f"Project {project_id_str} not found")
        return {
            "id": str(p.id), "title": p.title,
            "status": p.status.value if hasattr(p.status, "value") else p.status,
            "input": p.input_raw, "characters": p.characters or [],
            "scenes": p.scenes or [], "props": p.props or [],
            "storyboard": p.storyboard or {},
            "videos": p.videos or [],
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }

    async def list_projects(self, user_id: str = "") -> list:
        stmt = select(Project)
        if user_id:
            stmt = stmt.where(Project.user_id == user_id)
        stmt = stmt.order_by(Project.created_at.desc())
        r = await self.session.execute(stmt)
        return [{"id": str(p.id), "title": p.title,
                 "status": p.status.value if hasattr(p.status, "value") else p.status,
                 "created_at": p.created_at.isoformat() if p.created_at else None}
                for p in r.scalars().all()]

    async def regenerate_module(self, project_id_str: str, module: str) -> dict:
        try:
            project_id = uuid.UUID(project_id_str)
        except ValueError:
            raise ValueError(f"Invalid project_id: {project_id_str}")
        stmt = select(Project).where(Project.id == project_id)
        r = await self.session.execute(stmt)
        p = r.scalar_one_or_none()
        if not p:
            raise ValueError(f"Project {project_id_str} not found")
        if module == "characters":
            agent = CharacterAgent(); chars = await agent.generate(p.input_raw)
            p.characters = validate_characters(chars)
        elif module == "scenes":
            agent = SceneAgent(); sc = await agent.generate(p.input_raw, p.characters)
            p.scenes = validate_scenes(sc)
        elif module == "storyboard":
            agent = StoryboardAgent(); sb = await agent.generate(p.input_raw, p.characters, p.scenes, p.props)
            p.storyboard = validate_storyboard(sb)
        else:
            raise ValueError(f"Unknown module: {module}")
        await self.session.commit()
        return {"status": "regenerated", "module": module}
