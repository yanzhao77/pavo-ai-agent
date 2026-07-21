"""Memory MCP Tools — save/search/list/delete memory."""
import uuid, logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.mcp_schemas import MCPToolResult
from ..memory.store import MemoryStore
from ..memory.importance import ImportanceStrategy

logger = logging.getLogger(__name__)

class MemoryTools:
    """Memory MCP tool handlers."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.store = MemoryStore(session)

    async def save_memory(self, args: dict) -> dict:
        user_id = args.get("user_id","")
        if not user_id:
            return MCPToolResult.fail("INVALID_PARAM","user_id is required").model_dump()
        memory = {
            "id": uuid.uuid4(),
            "user_id": user_id,
            "memory_type": args.get("memory_type","preference"),
            "content": args.get("content",{}),
            "importance": args.get("importance", ImportanceStrategy.from_user_saved()),
            "source": args.get("source","user_saved"),
            "tags": args.get("tags",[]),
        }
        saved = await self.store.save_memory(memory)
        return MCPToolResult.ok({"memory_id":saved["id"],"status":"saved"}).model_dump()

    async def search_memory(self, args: dict) -> dict:
        user_id = args.get("user_id","")
        if not user_id:
            return MCPToolResult.fail("INVALID_PARAM","user_id is required").model_dump()
        memories = await self.store.search_memory(
            user_id=user_id,
            query_text=args.get("query_text",""),
            memory_types=args.get("memory_types"),
            limit=min(args.get("limit",5),10),
            min_importance=args.get("min_importance",0.0),
        )
        return MCPToolResult.ok({"memories":memories,"total":len(memories)}).model_dump()

    async def list_memories(self, args: dict) -> dict:
        user_id = args.get("user_id","")
        if not user_id:
            return MCPToolResult.fail("INVALID_PARAM","user_id is required").model_dump()
        memories, total = await self.store.list_memories(
            user_id=user_id,
            memory_type=args.get("memory_type"),
            page=args.get("page",1),
            page_size=args.get("page_size",20),
        )
        return MCPToolResult.ok({"memories":memories,"total":total,"page":args.get("page",1)}).model_dump()

    async def delete_memory(self, args: dict) -> dict:
        user_id = args.get("user_id","")
        memory_id = args.get("memory_id","")
        if not user_id or not memory_id:
            return MCPToolResult.fail("INVALID_PARAM","user_id and memory_id are required").model_dump()
        deleted = await self.store.delete_memory(user_id, memory_id)
        if not deleted:
            return MCPToolResult.fail("NOT_FOUND",f"Memory {memory_id} not found").model_dump()
        return MCPToolResult.ok({"status":"deleted","memory_id":memory_id}).model_dump()
