"""技能系统 — 可加载的工作流知识包

Hermes风格: Skills是Markdown文件，包含触发条件、步骤、注意事项。
Agent可以根据任务自动或手动加载相关skill。
"""
from __future__ import annotations
import os
import glob as glob_mod
from dataclasses import dataclass
from typing import Any


@dataclass
class Skill:
    """技能定义"""
    name: str
    description: str
    content: str
    path: str


class SkillManager:
    """技能管理器"""

    def __init__(self, skills_dir: str = "~/.agent/skills"):
        self.skills_dir = os.path.expanduser(skills_dir)
        self._skills: dict[str, Skill] = {}
        self._loaded_context: list[str] = []
        self._scan()

    def _scan(self) -> None:
        """扫描技能目录"""
        if not os.path.exists(self.skills_dir):
            return
        for path in glob_mod.glob(os.path.join(self.skills_dir, "*", "*.md")):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                name = os.path.basename(os.path.dirname(path))
                desc = content.split("\n")[0].strip("# ").strip()
                self._skills[name] = Skill(
                    name=name, description=desc, content=content, path=path
                )
            except Exception:
                continue

    def list_skills(self) -> list[Skill]:
        return list(self._skills.values())

    def load(self, name: str) -> str | None:
        """加载技能内容到上下文"""
        skill = self._skills.get(name)
        if skill:
            self._loaded_context.append(skill.content)
            return skill.content
        return None

    def as_context(self) -> str:
        """返回所有已加载技能的上下文"""
        if not self._loaded_context:
            return ""
        return "[Loaded Skills]\n\n" + "\n\n---\n\n".join(self._loaded_context)

    def match(self, query: str) -> list[Skill]:
        """根据query匹配相关技能"""
        query_lower = query.lower()
        return [
            s for s in self._skills.values()
            if query_lower in s.name.lower() or query_lower in s.description.lower()
        ]
