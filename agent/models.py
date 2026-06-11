"""核心数据模型"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
import json


class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class StopReason(str, Enum):
    END_TURN = "end_turn"
    TOOL_USE = "tool_use"
    MAX_TOKENS = "max_tokens"


@dataclass
class ToolCall:
    """LLM返回的工具调用"""
    id: str
    name: str
    arguments: dict[str, Any]

    @classmethod
    def from_dict(cls, d: dict) -> "ToolCall":
        args = d.get("arguments", "{}")
        if isinstance(args, str):
            args = json.loads(args)
        return cls(id=d["id"], name=d["name"], arguments=args)


@dataclass
class ToolResult:
    """工具执行结果"""
    tool_call_id: str
    content: str
    is_error: bool = False


@dataclass
class Message:
    """对话消息"""
    role: Role
    content: str | list[dict] = ""
    tool_calls: list[ToolCall] | None = None
    tool_call_id: str | None = None
    name: str | None = None

    def to_dict(self) -> dict:
        d: dict[str, Any] = {"role": self.role.value}
        if self.role == Role.TOOL:
            d["content"] = self.content
            d["tool_call_id"] = self.tool_call_id
            return d
        if self.tool_calls:
            d["content"] = self.content or ""
            d["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.name,
                        "arguments": json.dumps(tc.arguments, ensure_ascii=False),
                    },
                }
                for tc in self.tool_calls
            ]
        else:
            d["content"] = self.content
        return d


@dataclass
class AgentConfig:
    """Agent配置"""
    api_base: str = "https://coding.dashscope.aliyuncs.com/v1"
    api_key: str = ""
    model: str = "qwen3.5-plus"
    max_tokens: int = 4096
    temperature: float = 0
    max_turns: int = 50
    approval_mode: str = "suggest"  # suggest | auto-edit | full-auto
    project_file: str = "AGENTS.md"
    global_file: str = "~/.agent/AGENTS.md"
    memory_enabled: bool = True
    memory_path: str = "~/.agent/memory.json"
    auto_allow: list[str] = field(
        default_factory=lambda: ["read_file", "list_files", "search_files"]
    )
    ask_first: list[str] = field(
        default_factory=lambda: ["write_file", "edit_file"]
    )
    always_ask: list[str] = field(default_factory=lambda: ["shell"])
