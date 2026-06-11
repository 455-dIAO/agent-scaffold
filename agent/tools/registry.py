"""Tool注册表 — 扁平注册，按名称查找"""
from __future__ import annotations
from typing import Any
from .base import BaseTool
from ..models import ToolResult


class ToolRegistry:
    """工具注册表 (Codex风格扁平注册)"""

    def __init__(self):
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def execute(self, name: str, arguments: dict[str, Any]) -> ToolResult:
        tool = self._tools.get(name)
        if not tool:
            return ToolResult(
                tool_call_id="",
                content=f"Unknown tool: {name}",
                is_error=True,
            )
        try:
            return tool.execute(**arguments)
        except Exception as e:
            return ToolResult(
                tool_call_id="",
                content=f"Tool error ({name}): {e}",
                is_error=True,
            )

    def schemas(self) -> list[dict[str, Any]]:
        """返回所有工具的OpenAI schema"""
        return [t.to_schema() for t in self._tools.values()]

    def names(self) -> list[str]:
        return list(self._tools.keys())
