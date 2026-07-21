"""Shared MCP schemas - unified return format and error codes."""

from pydantic import BaseModel
from typing import Optional


class MCPError(BaseModel):
    """Unified error structure"""
    code: str
    message: str
    details: dict | None = None


ERROR_CODES = {
    "NOT_FOUND": "资源不存在",
    "INVALID_PARAM": "参数校验失败",
    "AUTH_FAILED": "认证失败，请检查 Token",
    "RATE_LIMITED": "请求频率过高，请稍后重试",
    "INTERNAL_ERROR": "服务内部错误，请联系管理员",
    "MEMORY_UNAVAILABLE": "记忆服务暂时不可用",
    "RAG_EMPTY_RESULT": "知识库检索无结果",
}


class MCPToolResult(BaseModel):
    """Standard tool call return"""
    success: bool
    data: dict | list | None = None
    error: MCPError | None = None

    @classmethod
    def ok(cls, data: dict | list | None = None) -> "MCPToolResult":
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, code: str, message: str = "", details: dict | None = None) -> "MCPToolResult":
        return cls(
            success=False,
            error=MCPError(
                code=code,
                message=message or ERROR_CODES.get(code, "未知错误"),
                details=details,
            ),
        )


class MCPProjectSummary(BaseModel):
    """Project summary (for listing)"""
    id: str
    title: str
    status: str
    created_at: str


class MCPCreateProjectInput(BaseModel):
    """Create project input"""
    input: str
    user_id: str = ""


class MCPRegenerateInput(BaseModel):
    """Regenerate module input"""
    project_id: str
    module: str  # storyboard | characters | scenes
