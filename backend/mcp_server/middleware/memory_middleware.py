"""Memory Middleware — transparent memory context injection for MCP Tools."""
import logging, time
from typing import Optional
from ..models.mcp_schemas import MCPToolResult

logger = logging.getLogger(__name__)

class MemoryMiddleware:
    """Intercepts MCP Tool calls for automatic memory injection."""

    def __init__(self):
        self._metrics = {
            "pre_process_count": 0, "post_process_count": 0,
            "total_duration_ms": 0, "fallback_count": 0,
            "hit_count": 0, "miss_count": 0,
        }

    async def pre_process(self, tool_name: str, arguments: dict) -> dict:
        """Pre-process: inject memory context from user history."""
        start = time.time()
        self._metrics["pre_process_count"] += 1

        # Extract user_id from arguments
        user_id = arguments.get("user_id", "")
        if not user_id and "context" in arguments:
            ctx = arguments.get("context", {})
            user_id = ctx.get("user_id", "")

        if not user_id:
            self._metrics["total_duration_ms"] += (time.time() - start) * 1000
            return arguments

        # Ensure context field exists
        if "context" not in arguments:
            arguments["context"] = {}
        arguments["context"]["user_id"] = user_id

        try:
            # Try to inject memory context (best-effort, non-blocking)
            session_id = arguments["context"].get("session_id", "")
            from app.db.database import async_session
            from ..memory.store import MemoryStore

            async with async_session() as session:
                store = MemoryStore(session)
                memories = await store.search_memory(
                    user_id=user_id,
                    query_text=arguments.get("input", tool_name),
                    limit=3,
                    min_importance=0.3,
                )
                if memories:
                    arguments["context"]["memory"] = {"items": memories}
                    self._metrics["hit_count"] += 1
                else:
                    self._metrics["miss_count"] += 1

                # Touch session TTL
                if session_id:
                    try:
                        await store.touch_session(session_id)
                    except Exception:
                        pass

        except Exception as e:
            # Level 1 degradation: log and continue
            logger.warning(f"Memory pre_process degraded: {e}")
            self._metrics["fallback_count"] += 1

        duration = (time.time() - start) * 1000
        self._metrics["total_duration_ms"] += duration
        return arguments

    async def post_process(self, tool_name: str, arguments: dict, result: dict) -> None:
        """Post-process: record interaction to memory store."""
        start = time.time()
        self._metrics["post_process_count"] += 1

        user_id = None
        try:
            ctx = arguments.get("context", {})
            user_id = ctx.get("user_id") or arguments.get("user_id")
        except Exception:
            pass

        if not user_id or not result.get("success", False):
            return

        try:
            from app.db.database import async_session
            from ..memory.store import MemoryStore
            from ..memory.importance import ImportanceStrategy

            async with async_session() as session:
                store = MemoryStore(session)
                content = {
                    "tool": tool_name,
                    "input_preview": str(arguments.get("input", ""))[:200] or str(arguments.get("query_text", ""))[:200],
                }
                if result.get("data"):
                    data_str = str(result["data"])[:200]
                    content["output_preview"] = data_str

                importance = ImportanceStrategy.from_auto_extracted(mentions=1)
                if importance >= ImportanceStrategy.auto_promote_threshold():
                    memory = {
                        "user_id": user_id,
                        "memory_type": "preference",
                        "content": content,
                        "importance": importance,
                        "source": "auto_extracted",
                        "tags": [tool_name],
                    }
                    await store.save_memory(memory)
        except Exception as e:
            logger.warning(f"Memory post_process degraded: {e}")

    def get_metrics(self) -> dict:
        return dict(self._metrics)

    def get_hit_rate(self) -> float:
        total = self._metrics["hit_count"] + self._metrics["miss_count"]
        return self._metrics["hit_count"] / total if total > 0 else 0.0
