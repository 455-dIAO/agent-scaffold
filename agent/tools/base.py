"""Tool基类 — 所有工具继承此类"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any
from ..models import ToolResult


class BaseTool(ABC):
    """工具基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称"""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述"""
        ...

    @property
    @abstractmethod
    def parameters(self) -> dict[str, Any]:
        """JSON Schema参数定义"""
        ...

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """执行工具，返回结果"""
        ...

    def to_schema(self) -> dict[str, Any]:
        """转换为OpenAI function calling格式"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }
