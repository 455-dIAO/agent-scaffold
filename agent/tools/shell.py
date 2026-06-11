"""Shell工具 — 持久化shell会话 (保持cwd/env)"""
from __future__ import annotations
import subprocess
import os
from typing import Any
from .base import BaseTool
from ..models import ToolResult


class ShellTool(BaseTool):
    """持久化Shell执行 (Claude Code + Codex风格)

    关键设计: subprocess.run保持进程级状态，cwd跨调用共享。
    """

    name = "shell"
    description = "执行shell命令。返回stdout/stderr/exit_code。支持超时。"

    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "要执行的shell命令",
            },
            "timeout": {
                "type": "integer",
                "description": "超时秒数，默认60",
                "default": 60,
            },
        },
        "required": ["command"],
    }

    def __init__(self, cwd: str | None = None):
        self._cwd = cwd or os.getcwd()

    def execute(self, command: str = "", timeout: int = 60, **kw) -> ToolResult:
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self._cwd,
            )
            output = ""
            if result.stdout:
                output += result.stdout
            if result.stderr:
                output += f"\n[STDERR]\n{result.stderr}"
            output += f"\n[EXIT {result.returncode}]"
            return ToolResult(
                tool_call_id="",
                content=output.strip(),
                is_error=result.returncode != 0,
            )
        except subprocess.TimeoutExpired:
            return ToolResult(
                tool_call_id="",
                content=f"Command timed out after {timeout}s",
                is_error=True,
            )
        except Exception as e:
            return ToolResult(tool_call_id="", content=str(e), is_error=True)

    def update_cwd(self, new_cwd: str) -> None:
        """更新工作目录 (cd命令后调用)"""
        self._cwd = new_cwd
