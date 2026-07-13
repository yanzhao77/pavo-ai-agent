"""Unified security guards for MCP Tools."""
import os, logging
from ..models.mcp_schemas import MCPToolResult
logger = logging.getLogger(__name__)

def check_api_key():
    key = os.environ.get("AGNES_API_KEY", "")
    if not key:
        return MCPToolResult.fail("AUTH_FAILED", "AGNES_API_KEY 未设置。请执行: pavo-start 或设置环境变量 AGNES_API_KEY")
    return None

def require_env(var_name: str, label: str = "") -> str | None:
    val = os.environ.get(var_name, "")
    if not val:
        return f"{label or var_name} 未配置"
    return None
