import uuid
import asyncio
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.project import Project, ProjectStatus
from app.agents.planner import PlannerAgent
from app.agents.character_agent import CharacterAgent
from app.agents.scene_agent import SceneAgent
from app.agents.prop_agent import PropAgent
from app.agents.storyboard_agent import StoryboardAgent
from app.agents.reviewer import ReviewerAgent
from app.agents.fixer import FixerAgent
from app.services.agnes_client import agnes_client
from app.services.storage import get_storage
from app.models.schema import validate_characters, validate_scenes, validate_props, validate_storyboard

logger = logging.getLogger(__name__)


def build_t2v_prompts(project):
    """Convert storyboard data into T2V prompt list, one per shot."""
    storyboard = project.storyboard or {}
    characters = project.characters or []
    stories = project.scenes or []
    props_data = project.props or []

    char_map = {}
    for c in characters:
        if isinstance(c, dict) and "name" in c:
            appr = c.get("appearance", {})
            desc = f'{appr.get("build","")} {appr.get("face","")} {appr.get("hair","")}'
            desc += f' wearing {appr.get("clothing","")}'
            char_map[c["name"]] = desc.strip()

    scene_map = {}
    for s in stories:
        if isinstance(s, dict) and "name" in s:
            env = s.get("environment", {})
            light = s.get("lighting", {})
            desc = f'{env.get("style","")} {env.get("type","")} with {light.get("type","")} lighting'
            scene_map[s["name"]] = desc.strip()

    results = []
    for scene_idx, scene in enumerate(storyboard.get("scenes", [])):
        for shot in scene.get("shots", []):
            shot_desc = shot.get("description", "")
            shot_type = shot.get("shotType", "medium shot")
            camera = shot.get("cameraMove", "static")
            angle = shot.get("cameraAngle", "eye-level")
            mood = scene.get("mood", "")
            music = scene.get("music", "")
            char_descs = []
            for cn in shot.get("characters", []):
                if cn in char_map:
                    char_descs.append(f"{cn}: {char_map[cn]}")
            sn = scene.get("title", "")
            sd = scene_map.get(sn, sn)
            prompt = f"Shot: {shot_type}. Camera: {camera} ({angle})."
            if char_descs: prompt += f" Characters: {';'.join(char_descs)}."
            if sd: prompt += f" Setting: {sd}."
            prompt += f" Action: {shot_desc}"
            if mood: prompt += f" Mood: {mood}."
            if music: prompt += f" Audio: {music}."
            results.append({"scene_idx": scene_idx, "shot_number": shot.get("shotNumber", 0), "prompt": prompt})
    return results

class ProjectService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.planner = PlannerAgent()
        self.character_agent = CharacterAgent()
        self.scene_agent = SceneAgent()
        self.prop_agent = PropAgent()
        self.storyboard_agent = StoryboardAgent()
        self.reviewer = ReviewerAgent()
        self.fixer = FixerAgent()

    async def create_project(self, input_text: str, user_id: str = "") -> Project:
        project_id = str(uuid.uuid4())
        project = Project(id=project_id, input_raw=input_text, user_id=user_id, status=ProjectStatus.GENERATING)
        self.session.add(project)
        await self.session.commit()
        return project

    async def _log_trace(self, project, agent_name, action, input_data, output_data, status="passed"):
        trace = {"agent": agent_name, "action": action,
                 "input": str(input_data)[:500], "output": str(output_data)[:500],
                 "status": status, "timestamp": datetime.utcnow().isoformat()}
        traces = project.trace_log or []
        traces.append(trace)
        project.trace_log = traces
        await self.session.commit()

    async def render_video(self, project):
        """Generate video prompts from storyboard and call video model."""
        prompts = build_t2v_prompts(project)
        if not prompts:
            return {"error": "No prompts generated"}
        await self._log_trace(project, "video", f"Generating {len(prompts)} video prompts", "", "")
        video_results = []
        for i, p in enumerate(prompts):
            # Delay between shot renders to avoid rate limiting
            if i > 0:
                await asyncio.sleep(15)
            await self._log_trace(project, "video", f"Generating shot {p['shot_number']}", p["prompt"][:80], "")
            try:
                result = await agnes_client.generate_video(p["prompt"])
                storage_url = ""
                try:
                    if result and result.get("url"):
                        import httpx
                        resp = httpx.get(result["url"])
                        if resp.status_code == 200:
                            object_name = f"projects/{str(project.id)}/shots/{p[chr(115)+chr(104)+chr(111)+chr(116)+chr(95)+chr(110)+chr(117)+chr(109)+chr(98)+chr(101)+chr(114)]}.mp4"
                            storage = get_storage()
                            storage_url = storage.upload_bytes(resp.content, object_name)
                except Exception as store_err:
                    logger.warning(f"Storage upload failed: {store_err}")
                video_results.append({"scene_idx": p["scene_idx"], "shot_number": p["shot_number"],
                                     "result": result, "storage_url": storage_url,
                                     "status": "completed"})
            except Exception as e:
                logger.error(f"Video gen failed for shot {p[chr(115)+chr(104)+chr(111)+chr(116)+chr(95)+chr(110)+chr(117)+chr(109)+chr(98)+chr(101)+chr(114)]}: {e}")
                video_results.append({"scene_idx": p["scene_idx"], "shot_number": p["shot_number"], "result": None, "status": "failed", "error": str(e)})
        project.videos = video_results
        return {"videos": video_results}

    async def run_workflow(self, project_id: str):
        result = await self.session.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()
        if not project:
            raise ValueError(f"Project {project_id} not found")

        try:
            await self._log_trace(project, "planner", "Analyzing story", project.input_raw, "")
            plan = await self.planner.plan(project.input_raw)
            await self._log_trace(project, "planner", "Plan created", project.input_raw, plan)
            await asyncio.sleep(2)  # Wait before next agent call

            await self._log_trace(project, "character", "Generating characters", project.input_raw, "")
            chars = await self.character_agent.generate(project.input_raw)
            chars = validate_characters(chars)
            project.characters = chars
            await self._log_trace(project, "character", "Done", project.input_raw, chars)
            await asyncio.sleep(2)

            await self._log_trace(project, "scene", "Generating scenes", project.input_raw, "")
            scenes = await self.scene_agent.generate(project.input_raw, chars)
            scenes = validate_scenes(scenes)
            project.scenes = scenes
            await self._log_trace(project, "scene", "Done", project.input_raw, scenes)
            await asyncio.sleep(2)

            await self._log_trace(project, "prop", "Generating props", project.input_raw, "")
            props = await self.prop_agent.generate(project.input_raw, chars, scenes)
            props = validate_props(props)
            project.props = props
            await self._log_trace(project, "prop", "Done", project.input_raw, props)
            await asyncio.sleep(2)

            await self._log_trace(project, "storyboard", "Generating storyboard", project.input_raw, "")
            storyboard = await self.storyboard_agent.generate(project.input_raw, chars, scenes, props)
            storyboard = validate_storyboard(storyboard)
            project.storyboard = storyboard
            await self._log_trace(project, "storyboard", "Done", project.input_raw, storyboard)
            await asyncio.sleep(2)

            review = await self.reviewer.review(project)
            if review.get("needs_fix"):
                await self._log_trace(project, "reviewer", "Needs fix", storyboard, review, "failed")
                fixed = await self.fixer.fix(project, review)
                project.storyboard = fixed
                await self._log_trace(project, "fixer", "Fixed", review, fixed)

            project.status = ProjectStatus.COMPLETED
        except Exception as e:
            logger.error(f"Workflow failed: {e}")
            project.status = ProjectStatus.DRAFT
            await self._log_trace(project, "system", f"Error: {e}", "", "", "failed")

        await self.session.commit()
        return project
