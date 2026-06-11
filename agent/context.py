"""上下文管理 — 加载AGENTS.md / CLAUDE.md注入system prompt

Claude Code: 层级CLAUDE.md (global → project)
Hermes: AGENTS.md + Skills注入
本脚手架: 合并两者
"""
from __future__ import annotations
import os
from .models import AgentConfig


class ContextManager:
    """管理项目上下文文件的加载和注入"""

    def __init__(self, config: AgentConfig):
        self.config = config

    def load_system_context(self) -> str:
        """加载全局 + 项目上下文"""
        parts = []

        # 全局上下文
        global_path = os.path.expanduser(self.config.global_file)
        if os.path.exists(global_path):
            with open(global_path, "r", encoding="utf-8") as f:
                parts.append(f"[Global Context]\n{f.read()}")

        # 项目上下文
        project_path = self.config.project_file
        if os.path.exists(project_path):
            with open(project_path, "r", encoding="utf-8") as f:
                parts.append(f"[Project Context]\n{f.read()}")

        return "\n\n---\n\n".join(parts) if parts else ""

    def build_system_prompt(self) -> str:
        """构建完整的system prompt"""
        context = self.load_system_context()

        return f"""你是一个编程Agent，能够执行shell命令、读写文件、搜索代码。

核心规则:
1. 使用工具获取真实信息，不要猜测
2. 文件编辑用 edit_file (search-replace)，不要 write_file 覆写整个文件
3. 执行命令前思考是否有破坏性
4. 完成后给出简洁总结

{context}

当前工作目录: {os.getcwd()}
"""
