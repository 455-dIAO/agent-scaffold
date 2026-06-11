"""权限审批层

Claude Code: auto / ask / deny 三级
Codex: suggest / auto-edit / full-auto 三种模式
本脚手架: 合并两者，按工具名分组 + approval_mode控制
"""
from __future__ import annotations
from enum import Enum
from typing import Callable
from .models import AgentConfig, ToolCall


class ApprovalMode(str, Enum):
    SUGGEST = "suggest"       # 所有工具都需要确认
    AUTO_EDIT = "auto-edit"   # 文件操作自动，shell需确认
    FULL_AUTO = "full-auto"   # 全自动 (需沙箱保护)


class PermissionChecker:
    """权限检查器 — 决定工具调用是否需要用户确认"""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.mode = ApprovalMode(config.approval_mode)
        self._session_allowed: set[str] = set()

    def check(self, tool_call: ToolCall) -> bool:
        """返回True=允许执行，False=拒绝"""
        name = tool_call.name

        # full-auto: 全部放行
        if self.mode == ApprovalMode.FULL_AUTO:
            return True

        # auto-edit: 文件操作自动，shell需确认
        if self.mode == ApprovalMode.AUTO_EDIT:
            if name in self.config.auto_allow or name in self.config.ask_first:
                return True
            # shell类需要确认
            return self._ask_user(tool_call)

        # suggest: 全部需要确认
        if name in self._session_allowed:
            return True
        return self._ask_user(tool_call)

    def _ask_user(self, tool_call: ToolCall) -> bool:
        """终端交互式确认"""
        import json
        print(f"\n{'='*50}")
        print(f"  Tool: {tool_call.name}")
        print(f"  Args: {json.dumps(tool_call.arguments, ensure_ascii=False, indent=2)[:500]}")
        print(f"{'='*50}")

        while True:
            choice = input("  [y]允许 / [a]本会话允许 / [d]拒绝: ").strip().lower()
            if choice in ("y", "yes", ""):
                return True
            if choice == "a":
                self._session_allowed.add(tool_call.name)
                return True
            if choice in ("d", "no", "n"):
                return False
            print("  请输入 y/a/d")
