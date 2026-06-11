"""文件操作工具 — Read / Write / Edit

Edit采用search-replace模式 (Claude Code风格)，比全文件覆写省context。
"""
from __future__ import annotations
import os
from typing import Any
from .base import BaseTool
from ..models import ToolResult


class ReadFileTool(BaseTool):
    name = "read_file"
    description = "读取文件内容，支持行号范围"
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "文件路径"},
            "offset": {"type": "integer", "description": "起始行号(1-indexed)", "default": 1},
            "limit": {"type": "integer", "description": "最大行数", "default": 500},
        },
        "required": ["path"],
    }

    def execute(self, path: str = "", offset: int = 1, limit: int = 500, **kw) -> ToolResult:
        try:
            path = os.path.expanduser(path)
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
            total = len(lines)
            selected = lines[offset - 1 : offset - 1 + limit]
            content = "".join(f"{offset + i}| {line}" for i, line in enumerate(selected))
            content += f"\n[lines {offset}-{min(offset + limit - 1, total)} of {total}]"
            return ToolResult(tool_call_id="", content=content)
        except Exception as e:
            return ToolResult(tool_call_id="", content=str(e), is_error=True)


class WriteFileTool(BaseTool):
    name = "write_file"
    description = "写入文件 (覆盖整个文件)"
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "文件路径"},
            "content": {"type": "string", "description": "文件内容"},
        },
        "required": ["path", "content"],
    }

    def execute(self, path: str = "", content: str = "", **kw) -> ToolResult:
        try:
            path = os.path.expanduser(path)
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return ToolResult(tool_call_id="", content=f"Written {len(content)} chars to {path}")
        except Exception as e:
            return ToolResult(tool_call_id="", content=str(e), is_error=True)


class EditFileTool(BaseTool):
    """Search-Replace编辑 (Claude Code核心设计)

    只发送差异部分，不传全文件 → 省context token。
    """
    name = "edit_file"
    description = "精确编辑文件: 查找old_text替换为new_text"
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "文件路径"},
            "old_text": {"type": "string", "description": "要查找的原文"},
            "new_text": {"type": "string", "description": "替换为的新文本"},
        },
        "required": ["path", "old_text", "new_text"],
    }

    def execute(self, path: str = "", old_text: str = "", new_text: str = "", **kw) -> ToolResult:
        try:
            path = os.path.expanduser(path)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            if old_text not in content:
                return ToolResult(
                    tool_call_id="",
                    content=f"old_text not found in {path}",
                    is_error=True,
                )
            count = content.count(old_text)
            if count > 1:
                return ToolResult(
                    tool_call_id="",
                    content=f"old_text found {count} times — must be unique. Add more context.",
                    is_error=True,
                )
            new_content = content.replace(old_text, new_text, 1)
            with open(path, "w", encoding="utf-8") as f:
                f.write(new_content)
            return ToolResult(tool_call_id="", content=f"Edited {path} (1 replacement)")
        except Exception as e:
            return ToolResult(tool_call_id="", content=str(e), is_error=True)
