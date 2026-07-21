"""Pavo MCP Server entry point — tools, resources, prompts registration."""
import asyncio
import json
import logging

from mcp.server import Server
import mcp.server.stdio

from app.config import settings
from app.db.database import async_session
from app.models.project import Project
from sqlalchemy import select

logger = logging.getLogger(__name__)
server = Server("pavo-mcp-server")


@server.list_tools()
async def list_tools():
    return [
        {"name": "pavo_create_project", "description": "根据故事创意创建项目并启动AI Agent管线", "inputSchema": {"type": "object", "properties": {"input": {"type": "string", "description": "故事创意文本"}, "user_id": {"type": "string"}, "context": {"type": "object", "description": "系统内部使用"}}, "required": ["input"]}},
        {"name": "pavo_get_project", "description": "获取项目完整数据", "inputSchema": {"type": "object", "properties": {"project_id": {"type": "string"}}, "required": ["project_id"]}},
        {"name": "pavo_list_projects", "description": "获取项目列表", "inputSchema": {"type": "object", "properties": {"user_id": {"type": "string"}}}},
        {"name": "pavo_generate_storyboard", "description": "重新生成指定模块", "inputSchema": {"type": "object", "properties": {"project_id": {"type": "string"}, "module": {"type": "string", "enum": ["storyboard", "characters", "scenes"]}, "context": {"type": "object"}}, "required": ["project_id", "module"]}},
        {"name": "pavo_render_video", "description": "触发视频渲染", "inputSchema": {"type": "object", "properties": {"project_id": {"type": "string"}, "context": {"type": "object"}}, "required": ["project_id"]}},
        {"name": "pavo_export_project", "description": "导出项目", "inputSchema": {"type": "object", "properties": {"project_id": {"type": "string"}, "format": {"type": "string", "enum": ["markdown", "script", "pdf"]}}, "required": ["project_id", "format"]}},
        {"name": "pavo_get_video_status", "description": "查询视频状态", "inputSchema": {"type": "object", "properties": {"project_id": {"type": "string"}}, "required": ["project_id"]}},
        {"name": "pavo_auth_login", "description": "获取认证Token", "inputSchema": {"type": "object", "properties": {"username": {"type": "string"}}, "required": ["username"]}},
        {"name": "pavo_save_memory", "description": "保存用户偏好到长期记忆", "inputSchema": {"type": "object", "properties": {"user_id": {"type": "string"}, "memory_type": {"type": "string", "enum": ["style", "character", "scene", "preference", "story_arc", "feedback"]}, "content": {"type": "object"}, "tags": {"type": "array", "items": {"type": "string"}}, "importance": {"type": "number"}}, "required": ["user_id", "memory_type", "content"]}},
        {"name": "pavo_search_memory", "description": "检索用户历史记忆", "inputSchema": {"type": "object", "properties": {"user_id": {"type": "string"}, "query_text": {"type": "string"}, "memory_types": {"type": "array", "items": {"type": "string"}}, "limit": {"type": "number"}}, "required": ["user_id", "query_text"]}},
        {"name": "pavo_list_memories", "description": "列出用户记忆", "inputSchema": {"type": "object", "properties": {"user_id": {"type": "string"}, "memory_type": {"type": "string"}, "page": {"type": "number"}, "page_size": {"type": "number"}}, "required": ["user_id"]}},
        {"name": "pavo_delete_memory", "description": "删除指定记忆", "inputSchema": {"type": "object", "properties": {"user_id": {"type": "string"}, "memory_id": {"type": "string"}}, "required": ["user_id", "memory_id"]}},
    ]


@server.list_resources()
async def list_resources():
    return [
        {"uri": "pavo://projects", "name": "项目列表", "mimeType": "application/json"},
        {"uri": "pavo://projects/{project_id}", "name": "项目详情", "mimeType": "application/json"},
        {"uri": "pavo://projects/{project_id}/storyboard", "name": "分镜数据", "mimeType": "application/json"},
        {"uri": "pavo://users/{user_id}/memories", "name": "用户记忆", "mimeType": "application/json"},
    ]


@server.list_prompts()
async def list_prompts():
    return [
        {"name": "generate_storyboard", "description": "生成分镜", "arguments": [{"name": "input", "description": "故事", "required": True}, {"name": "characters", "description": "角色"}, {"name": "scenes", "description": "场景"}]},
        {"name": "design_characters", "description": "设计角色", "arguments": [{"name": "story", "description": "故事", "required": True}, {"name": "genre", "description": "类型"}]},
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    from .models.mcp_schemas import MCPToolResult
    from .middleware.memory_middleware import MemoryMiddleware
    from .tools.guards import check_api_key

    # Security: check API Key first
    err = check_api_key()
    if err:
        return err

    middleware = MemoryMiddleware()
    try:
        augmented_args = await middleware.pre_process(name, arguments)
        result = await _dispatch(name, augmented_args)
        await middleware.post_process(name, arguments, result)
        return result
    except Exception as e:
        logger.exception(f"Tool {name} failed")
        return MCPToolResult.fail("INTERNAL_ERROR", str(e)).model_dump()


async def _dispatch(name: str, args: dict) -> dict:
    from .models.mcp_schemas import MCPToolResult
    from .adapter.project_adapter import ProjectAdapter
    from .tools.memory_tools import MemoryTools

    async with async_session() as session:
        pa = ProjectAdapter(session)
        mt = MemoryTools(session)

        handlers = {
            "pavo_create_project": lambda: _ok(pa.create_project(args.get("input", ""), args.get("user_id", ""))),
            "pavo_get_project": lambda: _ok(pa.get_project(args.get("project_id", ""))),
            "pavo_list_projects": lambda: _ok(pa.list_projects(args.get("user_id", ""))),
            "pavo_generate_storyboard": lambda: _ok(pa.regenerate_module(args.get("project_id", ""), args.get("module", ""))),
            "pavo_save_memory": lambda: mt.save_memory(args),
            "pavo_search_memory": lambda: mt.search_memory(args),
            "pavo_list_memories": lambda: mt.list_memories(args),
            "pavo_delete_memory": lambda: mt.delete_memory(args),
        }

        if name in handlers:
            result = await handlers[name]()
            return result.model_dump() if hasattr(result, "model_dump") else result

        if name == "pavo_auth_login":
            from app.services.auth import create_token
            uid = args.get("username", "").strip().lower().replace(" ", "_")
            token = create_token(uid)
            return MCPToolResult.ok({"token": token, "user_id": uid}).model_dump()

        if name in ("pavo_render_video", "pavo_export_project", "pavo_get_video_status"):
            # FIX: Project.id is now String(64); query directly with the string value
            pid = args.get("project_id", "").strip()
            if not pid:
                return MCPToolResult.fail("INVALID_PARAM", "project_id is required").model_dump()
            stmt = select(Project).where(Project.id == pid)
            r = await session.execute(stmt)
            proj = r.scalar_one_or_none()
            if not proj:
                return MCPToolResult.fail("NOT_FOUND", "Project not found").model_dump()

            if name == "pavo_render_video":
                from app.services.project_service import ProjectService
                svc = ProjectService(session)
                vr = await svc.render_video(proj)
                return MCPToolResult.ok(vr).model_dump()
            elif name == "pavo_export_project":
                fmt = args.get("format", "markdown")
                from app.services.export.markdown import storyboard_to_markdown, storyboard_to_script
                if fmt == "markdown":
                    content = storyboard_to_markdown(proj)
                elif fmt == "script":
                    content = storyboard_to_script(proj)
                else:
                    return MCPToolResult.fail("INVALID_PARAM", "Unsupported format").model_dump()
                return MCPToolResult.ok({"format": fmt, "content": content, "filename": f"storyboard.{fmt}"}).model_dump()
            else:
                return MCPToolResult.ok({"videos": proj.videos or []}).model_dump()

        return MCPToolResult.fail("NOT_FOUND", f"Unknown tool: {name}").model_dump()


async def _ok(coro):
    from .models.mcp_schemas import MCPToolResult
    result = await coro
    return MCPToolResult.ok(result).model_dump()


@server.read_resource()
async def read_resource(uri: str):
    async with async_session() as session:
        if uri == "pavo://projects":
            r = await session.execute(select(Project).order_by(Project.created_at.desc()))
            data = [
                {
                    "id": str(p.id),
                    "title": p.title,
                    "status": p.status.value if hasattr(p.status, "value") else p.status,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                }
                for p in r.scalars().all()
            ]
            return json.dumps(data, ensure_ascii=False)

        if uri.startswith("pavo://projects/"):
            parts = uri.split("/")
            pid = parts[2]
            # FIX: Project.id is String(64); query directly without uuid.UUID conversion
            r = await session.execute(select(Project).where(Project.id == pid))
            p = r.scalar_one_or_none()
            if not p:
                return json.dumps({"error": "not found"})
            d = {
                "id": str(p.id),
                "title": p.title,
                "status": p.status.value if hasattr(p.status, "value") else p.status,
                "input": p.input_raw,
            }
            if len(parts) > 3:
                sub = parts[3]
                if sub == "storyboard":
                    return json.dumps(p.storyboard or {}, ensure_ascii=False)
                if sub == "characters":
                    return json.dumps(p.characters or [], ensure_ascii=False)
            return json.dumps(d, ensure_ascii=False)

        if uri.startswith("pavo://users/"):
            parts = uri.split("/")
            uid = parts[2]
            from .tools.memory_tools import MemoryTools
            mt = MemoryTools(session)
            mems, tot = await mt.store.list_memories(uid)
            if len(parts) > 4:
                mid = parts[4]
                mems = [m for m in mems if m.get("id") == mid]
            if len(parts) <= 4:
                return json.dumps({"memories": mems}, ensure_ascii=False)
            return json.dumps(mems[0] if mems else {}, ensure_ascii=False)

        return json.dumps({"error": "not found"})


async def main():
    # FIX: Initialize SQLite database (tables + WAL mode + sqlite-vec) before serving
    from app.db.database import init_db
    await init_db()

    async with mcp.server.stdio.stdio_server() as (read, write):
        await server.run(read, write)


if __name__ == "__main__":
    asyncio.run(main())
