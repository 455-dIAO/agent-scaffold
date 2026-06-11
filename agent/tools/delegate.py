"""子Agent委托工具 — 隔离上下文的子任务执行

Claude Code的Agent tool + Hermes的delegate_task模式:
父agent spawn子agent → 子agent独立执行 → 返回summary给父agent。
"""
from __future__ import annotations
from typing import Any, TYPE_CHECKING
from .base import BaseTool
from ..models import ToolResult, AgentConfig, Message, Role

if TYPE_CHECKING:
    from ..loop import AgentLoop


class DelegateTool(BaseTool):
    name = "delegate_task"
    description = "委托子任务给子Agent执行，返回结果摘要。用于隔离上下文的独立子任务。"
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "goal": {"type": "string", "description": "子Agent要完成的目标"},
            "context": {"type": "string", "description": "需要传递给子Agent的背景信息"},
            "tool_names": {
                "type": "array",
                "items": {"type": "string"},
                "description": "子Agent可用的工具名列表，空=继承全部",
            },
        },
        "required": ["goal"],
    }

    def __init__(self, parent_loop: "AgentLoop"):
        self._parent = parent_loop

    def execute(
        self, goal: str = "", context: str = "", tool_names: list[str] | None = None, **kw
    ) -> ToolResult:
        from ..loop import AgentLoop

        child_config = AgentConfig(
            api_base=self._parent.config.api_base,
            api_key=self._parent.config.api_key,
            model=self._parent.config.model,
            max_turns=min(self._parent.config.max_turns, 20),
            approval_mode="full-auto",  # 子agent自动执行
        )

        child = AgentLoop(child_config)
        child.messages.append(
            Message(role=Role.SYSTEM, content=f"你是一个专注的子Agent。\n\n目标: {goal}\n\n背景: {context}")
        )
        child.messages.append(Message(role=Role.USER, content=goal))

        # 如果指定了工具，只注册指定的
        if tool_names:
            from .registry import ToolRegistry
            child.registry = ToolRegistry()
            for name in tool_names:
                t = self._parent.registry.get(name)
                if t:
                    child.registry.register(t)

        try:
            result = child.run()
            return ToolResult(
                tool_call_id="",
                content=f"[子Agent完成]\n{result}",
            )
        except Exception as e:
            return ToolResult(
                tool_call_id="",
                content=f"[子Agent失败] {e}",
                is_error=True,
            )
