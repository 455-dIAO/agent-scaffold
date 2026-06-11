"""持久记忆 — 跨会话记忆存储

Hermes风格: 持久化记忆到JSON，每次对话注入。
"""
from __future__ import annotations
import json
import os
from typing import Any
from .models import AgentConfig


class MemoryStore:
    """JSON文件持久记忆"""

    def __init__(self, config: AgentConfig):
        self.enabled = config.memory_enabled
        self.path = os.path.expanduser(config.memory_path)
        self._memories: list[dict[str, Any]] = []
        if self.enabled:
            self._load()

    def _load(self) -> None:
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    self._memories = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._memories = []

    def _save(self) -> None:
        if not self.enabled:
            return
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self._memories, f, ensure_ascii=False, indent=2)

    def add(self, content: str, category: str = "general") -> None:
        self._memories.append({"content": content, "category": category})
        self._save()

    def search(self, query: str) -> list[str]:
        """简单关键词搜索"""
        query_lower = query.lower()
        return [
            m["content"]
            for m in self._memories
            if query_lower in m["content"].lower()
        ]

    def as_context(self, limit: int = 20) -> str:
        """导出为system prompt注入文本"""
        if not self._memories:
            return ""
        recent = self._memories[-limit:]
        lines = [f"- {m['content']}" for m in recent]
        return "[Memory]\n" + "\n".join(lines)

    def clear(self) -> None:
        self._memories = []
        self._save()
