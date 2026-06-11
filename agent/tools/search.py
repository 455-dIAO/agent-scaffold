"""搜索工具 — Glob (文件名) / Grep (内容)"""
from __future__ import annotations
import glob as glob_mod
import os
import subprocess
from typing import Any
from .base import BaseTool
from ..models import ToolResult


class GlobTool(BaseTool):
    name = "list_files"
    description = "按glob模式查找文件"
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "glob模式, 如 **/*.py"},
            "path": {"type": "string", "description": "搜索根目录", "default": "."},
        },
        "required": ["pattern"],
    }

    def execute(self, pattern: str = "", path: str = ".", **kw) -> ToolResult:
        try:
            full = os.path.join(os.path.expanduser(path), pattern)
            files = sorted(glob_mod.glob(full, recursive=True))
            if not files:
                return ToolResult(tool_call_id="", content="No files found")
            return ToolResult(tool_call_id="", content="\n".join(files[:200]))
        except Exception as e:
            return ToolResult(tool_call_id="", content=str(e), is_error=True)


class GrepTool(BaseTool):
    name = "search_files"
    description = "在文件内容中搜索正则表达式 (backed by ripgrep)"
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "正则表达式"},
            "path": {"type": "string", "description": "搜索路径", "default": "."},
            "glob": {"type": "string", "description": "文件过滤, 如 *.py"},
        },
        "required": ["pattern"],
    }

    def execute(self, pattern: str = "", path: str = ".", glob: str = "", **kw) -> ToolResult:
        cmd = ["rg", "--no-heading", "-n", pattern, path]
        if glob:
            cmd.extend(["-g", glob])
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if r.returncode == 1:
                return ToolResult(tool_call_id="", content="No matches")
            return ToolResult(
                tool_call_id="",
                content=r.stdout[:5000] or r.stderr[:2000],
                is_error=r.returncode > 1,
            )
        except FileNotFoundError:
            return ToolResult(
                tool_call_id="",
                content="ripgrep (rg) not installed. Install with: apt install ripgrep",
                is_error=True,
            )
        except subprocess.TimeoutExpired:
            return ToolResult(tool_call_id="", content="Search timed out", is_error=True)
