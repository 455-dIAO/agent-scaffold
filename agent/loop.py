"""核心Agent循环 — 蒸馏自三家的设计精华

Claude Code: message-tool loop, edit>write, sub-agent
Codex: approval modes, sandbox-ready
Hermes: skills, memory, delegation
"""
from __future__ import annotations
import uuid
import json
from typing import Any
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from .models import Message, Role, ToolCall, ToolResult, AgentConfig
from .llm import LLMClient
from .tools.registry import ToolRegistry
from .tools.shell import ShellTool
from .tools.file_ops import ReadFileTool, WriteFileTool, EditFileTool
from .tools.search import GlobTool, GrepTool
from .permissions import PermissionChecker
from .context import ContextManager
from .memory import MemoryStore
from .skills import SkillManager

console = Console()


class AgentLoop:
    """
    核心Agent循环

    设计来源:
    - Claude Code: 简洁的 message→tool→message 循环
    - Codex: 权限审批层 (suggest/auto-edit/full-auto)
    - Hermes: 技能加载 + 记忆注入 + 子Agent委托
    """

    def __init__(self, config: AgentConfig):
        self.config = config
        self.messages: list[Message] = []
        self.registry = ToolRegistry()
        self.llm = LLMClient(config)
        self.permissions = PermissionChecker(config)
        self.context = ContextManager(config)
        self.memory = MemoryStore(config)
        self.skills = SkillManager()

        # 注册内置工具
        self._register_builtins()

        # 初始化system prompt
        self._init_system()

    def _register_builtins(self) -> None:
        """注册内置工具集"""
        self.registry.register(ReadFileTool())
        self.registry.register(WriteFileTool())
        self.registry.register(EditFileTool())
        self.registry.register(GlobTool())
        self.registry.register(GrepTool())
        self.registry.register(ShellTool())
        # delegate_tool 在 run() 中注入，因为它需要引用 self

    def _init_system(self) -> None:
        """构建初始system prompt"""
        system_text = self.context.build_system_prompt()

        # 注入记忆
        memory_ctx = self.memory.as_context()
        if memory_ctx:
            system_text += f"\n\n{memory_ctx}"

        # 注入技能目录
        available = self.skills.list_skills()
        if available:
            skill_list = "\n".join(f"  - {s.name}: {s.description}" for s in available)
            system_text += f"\n\n[Available Skills]\n{skill_list}\n用 load_skill(name) 加载。"

        self.messages.append(Message(role=Role.SYSTEM, content=system_text))

    def run(self, user_input: str | None = None) -> str:
        """
        主循环 — 蒸馏自三家的核心设计

        Claude Code: while True → chat → tool_calls → execute → append → loop
        Codex: 每个tool_call经过permission check
        Hermes: 子Agent委托、技能加载
        """
        # 注入delegate_tool (需要self引用)
        from .tools.delegate import DelegateTool
        self.registry.register(DelegateTool(self))

        if user_input:
            self.messages.append(Message(role=Role.USER, content=user_input))

        last_response = ""

        for turn in range(self.config.max_turns):
            # 1) 调用LLM
            console.print(f"\n[dim]--- Turn {turn + 1} ---[/dim]")
            content, tool_calls = self.llm.chat(
                self.messages, self.registry.schemas()
            )

            # 2) 显示assistant输出
            if content:
                console.print(Panel(Markdown(content), title="Assistant", border_style="blue"))
                last_response = content

            # 3) 无工具调用 → 结束
            if not tool_calls:
                break

            # 4) 记录assistant消息 (含tool_calls)
            self.messages.append(
                Message(role=Role.ASSISTANT, content=content, tool_calls=tool_calls)
            )

            # 5) 逐个执行工具
            for tc in tool_calls:
                console.print(f"\n[yellow]⚡ {tc.name}[/yellow]")
                console.print(f"  [dim]{json.dumps(tc.arguments, ensure_ascii=False)[:200]}[/dim]")

                # 权限检查 (Codex风格)
                if not self.permissions.check(tc):
                    result = ToolResult(
                        tool_call_id=tc.id,
                        content="User denied this tool call",
                        is_error=True,
                    )
                    console.print("  [red]✗ Denied[/red]")
                else:
                    result = self.registry.execute(tc.name, tc.arguments)
                    result.tool_call_id = tc.id

                    if result.is_error:
                        console.print(f"  [red]✗ {result.content[:200]}[/red]")
                    else:
                        console.print(f"  [green]✓[/green] {result.content[:200]}")

                # 将结果追加到messages
                self.messages.append(
                    Message(
                        role=Role.TOOL,
                        content=result.content,
                        tool_call_id=tc.id,
                    )
                )

        return last_response

    def chat(self, user_input: str) -> str:
        """单轮对话接口"""
        return self.run(user_input)

    def add_tool(self, tool) -> None:
        """注册自定义工具"""
        self.registry.register(tool)
