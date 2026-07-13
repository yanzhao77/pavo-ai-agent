import json
import asyncio
import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_session
from app.models.project import Project
from app.services.project_service import ProjectService
from app.models.project import VersionHistory, Feedback
from app.services.storage import get_storage
from app.services.auth import create_token, verify_token

from typing import Optional

router = APIRouter()

class CreateProjectRequest(BaseModel):
    input: str
    user_id: str = ""

class RegenerateRequest(BaseModel):
    module: str  # "storyboard" | "characters" | "scenes"

class LoginRequest(BaseModel):
    username: str

@router.post("/auth/login")
async def login(req: LoginRequest):
    user_id = req.username.strip().lower().replace(" ", "_")
    if not user_id:
        raise HTTPException(status_code=400, detail="Username required")
    token = create_token(user_id)
    return {"token": token, "user_id": user_id}

@router.get("/auth/me")
async def auth_me(token: Optional[str] = None):
    uid = verify_token(token or "")
    if not uid:
        raise HTTPException(status_code=401, detail="Invalid token")
    return {"user_id": uid}

def _get_user_id(token: str = "") -> str:
    uid = verify_token(token)
    return uid or ""

@router.post("/projects")
async def create_project(req: CreateProjectRequest, session: AsyncSession = Depends(get_session)):
    service = ProjectService(session)
    project = await service.create_project(req.input, req.user_id)
    asyncio.create_task(service.run_workflow(project.id))
    return {"projectId": str(project.id), "status": project.status.value}

@router.get("/projects/{project_id}")
async def get_project(project_id: str, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {
        "id": str(project.id),
        "userId": project.user_id,
        "title": project.title,
        "status": project.status.value,
        "input": project.input_raw,
        "characters": project.characters,
        "scenes": project.scenes,
        "props": project.props,
        "storyboard": project.storyboard,
        "videos": project.videos,
        "traceLog": project.trace_log,
        "createdAt": project.created_at.isoformat() if project.created_at else None,
        "updatedAt": project.updated_at.isoformat() if project.updated_at else None,
    }

@router.get("/projects")
async def list_projects(user_id: str = "", session: AsyncSession = Depends(get_session)):
    query = select(Project)
    if user_id:
        query = query.where(Project.user_id == user_id)
    query = query.order_by(Project.created_at.desc())
    result = await session.execute(query)
    projects = result.scalars().all()
    return [
        {"id": str(p.id), "title": p.title, "status": p.status.value, "userId": p.user_id,
         "createdAt": p.created_at.isoformat() if p.created_at else None}
        for p in projects
    ]

@router.get("/projects/{project_id}/stream")
async def stream_project(project_id: str, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    async def event_stream():
        last_trace_count = 0
        while True:
            await session.refresh(project)
            traces = project.trace_log or []
            for i in range(last_trace_count, len(traces)):
                t = traces[i]
                yield f"data: {json.dumps({'type': 'agent:progress', 'agent': t['agent'], 'action': t['action'], 'status': t['status'], 'timestamp': t['timestamp']})}\n\n"
                last_trace_count = i + 1
            if project.status.value in ("completed", "draft"):
                yield f"data: {json.dumps({'type': 'agent:complete', 'status': project.status.value})}\n\n"
                break
            await asyncio.sleep(1)

    return StreamingResponse(event_stream(), media_type="text/event-stream")

@router.patch("/projects/{project_id}")
async def update_project(project_id: str, body: dict, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    for key in ("characters", "scenes", "props", "storyboard"):
        if key in body:
            setattr(project, key, body[key])
    await session.commit()
    return {"status": "updated"}

@router.post("/projects/{project_id}/regenerate")
async def regenerate(project_id: str, req: RegenerateRequest, session: AsyncSession = Depends(get_session)):
    service = ProjectService(session)
    result = await session.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    module = req.module
    if module == "characters":
        chars = await service.character_agent.generate(project.input_raw)
        project.characters = chars
    elif module == "scenes":
        scenes = await service.scene_agent.generate(project.input_raw, project.characters)
        project.scenes = scenes
    elif module == "storyboard":
        sb = await service.storyboard_agent.generate(project.input_raw, project.characters, project.scenes, project.props)
        project.storyboard = sb
    await session.commit()
    return {"status": "regenerated", "module": module}

@router.post("/projects/{project_id}/render")
async def render_project(project_id: str, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not project.storyboard:
        raise HTTPException(status_code=400, detail="No storyboard to render")
    service = ProjectService(session)
    video_result = await service.render_video(project)
    await session.commit()
    return video_result

from app.models.project import VersionHistory, Feedback
from app.services.storage import get_storage

@router.get("/projects/{project_id}/tasks")
async def get_task_status(project_id: str, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    task_ids = project.task_ids or []
    return {"task_ids": task_ids, "video_count": len(project.videos or [])}

@router.post("/projects/{project_id}/versions")
async def create_version(project_id: str, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404)
    snapshot = {
        "characters": project.characters,
        "scenes": project.scenes,
        "props": project.props,
        "storyboard": project.storyboard,
    }
    versions_count = await session.execute(
        select(VersionHistory).where(VersionHistory.project_id == project_id)
    )
    ver_num = len(versions_count.scalars().all()) + 1
    version = VersionHistory(
        id=uuid.uuid4(), project_id=project_id,
        version_number=ver_num, snapshot=snapshot,
        description="auto-save",
    )
    session.add(version)
    await session.commit()
    return {"version_id": str(version.id), "version_number": ver_num}

@router.get("/projects/{project_id}/versions")
async def list_versions(project_id: str, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(VersionHistory).where(VersionHistory.project_id == project_id)
        .order_by(VersionHistory.version_number.desc())
    )
    versions = result.scalars().all()
    return [{"id": str(v.id), "version_number": v.version_number,
             "description": v.description,
             "created_at": v.created_at.isoformat() if v.created_at else None}
            for v in versions]

@router.post("/projects/{project_id}/versions/{version_id}/restore")
async def restore_version(project_id: str, version_id: str,
                          session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(VersionHistory).where(
        VersionHistory.id == version_id, VersionHistory.project_id == project_id))
    version = result.scalar_one_or_none()
    if not version:
        raise HTTPException(status_code=404)
    proj_result = await session.execute(select(Project).where(Project.id == project_id))
    project = proj_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404)
    for key in ("characters", "scenes", "props", "storyboard"):
        if key in version.snapshot:
            setattr(project, key, version.snapshot[key])
    await session.commit()
    return {"status": "restored", "version_number": version.version_number}

@router.post("/projects/{project_id}/feedback")
async def submit_feedback(project_id: str, body: dict,
                         session: AsyncSession = Depends(get_session)):
    fb = Feedback(
        id=uuid.uuid4(), project_id=project_id,
        user_id=body.get("user_id", ""),
        rating=body.get("rating", ""),
        comment=body.get("comment", ""),
    )
    session.add(fb)
    await session.commit()
    return {"status": "submitted", "id": str(fb.id)}

@router.get("/projects/{project_id}/videos")
async def get_video_details(project_id: str,
                           session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404)
    videos = project.videos or []
    for v in videos:
        if v.get("result") and v["result"].get("url"):
            storage = get_storage()
            object_name = f"projects/{project_id}/shots/{v.get("shot_number", 0)}.mp4"
            v["storage_url"] = storage.get_url(object_name)
    return {"videos": videos}



@router.delete("/projects/{project_id}")
async def delete_project(project_id: str, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    await session.delete(project)
    await session.commit()
    return {"status": "deleted"}

@router.get("/projects/{project_id}/export")
async def export_project(project_id: str, format: str = "markdown",
                         session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if format == "markdown":
        from app.services.export.markdown import storyboard_to_markdown
        content = storyboard_to_markdown(project)
        return Response(
            content=content,
            media_type="text/markdown",
            headers={"Content-Disposition": "attachment; filename=storyboard.md"},
        )
    elif format == "script":
        from app.services.export.markdown import storyboard_to_script
        content = storyboard_to_script(project)
        return Response(
            content=content,
            media_type="text/plain",
            headers={"Content-Disposition": "attachment; filename=storyboard.txt"},
        )

    elif format == "pdf":
        from app.services.export.pdf import storyboard_to_pdf
        content = storyboard_to_pdf(project)
        return Response(
            content=content,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=storyboard.pdf"},
        )

    raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")
