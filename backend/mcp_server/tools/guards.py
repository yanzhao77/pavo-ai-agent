"""Unified security guards for MCP Tools."""
import os, logging
from ..models.mcp_schemas import MCPToolResult
logger = logging.getLogger(__name__)

def check_api_key():
    key = os.environ.get("AGNES_API_KEY", "")
    if not key:
        return MCPToolResult.fail("AUTH_FAILED", "AGNES_API_KEY \u672a\u8bbe\u7f6e\u3002\u8bf7\u6267\u884c: pavo-start \u6216\u8bbe\u7f6e\u73af\u5883\u53d8\u91cf AGNES_API_KEY")
    return None

def require_env(var_name: str, label: str = "") -> str | None:
    val = os.environ.get(var_name, "")
    if not val:
        return f"{label or var_name} \u672a\u914d\u7f6e"
    return None
