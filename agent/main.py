"""Agent Scaffold 入口 — CLI交互模式"""
from __future__ import annotations
import argparse
import os
import sys
import yaml
from pathlib import Path

from .models import AgentConfig
from .loop import AgentLoop, console


def load_config(config_path: str = "config.yaml") -> AgentConfig:
    """从YAML加载配置，环境变量自动替换"""
    path = Path(config_path)
    if not path.exists():
        return AgentConfig()

    with open(path) as f:
        raw = f.read()

    # 替换 ${ENV_VAR} 占位符
    import re
    for match in re.finditer(r"\$\{(\w+)\}", raw):
        env_key = match.group(1)
        env_val = os.environ.get(env_key, "")
        raw = raw.replace(match.group(0), env_val)

    data = yaml.safe_load(raw) or {}
    llm = data.get("llm", {})
    agent = data.get("agent", {})
    perms = data.get("permissions", {})
    ctx = data.get("context", {})
    mem = data.get("memory", {})

    return AgentConfig(
        api_base=llm.get("api_base", "https://coding.dashscope.aliyuncs.com/v1"),
        api_key=llm.get("api_key", ""),
        model=llm.get("model", "qwen3.5-plus"),
        max_tokens=llm.get("max_tokens", 4096),
        temperature=llm.get("temperature", 0),
        max_turns=agent.get("max_turns", 50),
        approval_mode=agent.get("approval_mode", "suggest"),
        project_file=ctx.get("project_file", "AGENTS.md"),
        global_file=ctx.get("global_file", "~/.agent/AGENTS.md"),
        memory_enabled=mem.get("enabled", True),
        memory_path=mem.get("path", "~/.agent/memory.json"),
        auto_allow=perms.get("auto_allow", ["read_file", "list_files", "search_files"]),
        ask_first=perms.get("ask_first", ["write_file", "edit_file"]),
        always_ask=perms.get("always_ask", ["shell"]),
    )


def interactive_mode(agent: AgentLoop) -> None:
    """交互式对话模式"""
    console.print("[bold green]Agent Scaffold[/bold green] — 输入消息开始对话，Ctrl+C 退出")
    console.print(f"  Model: {agent.config.model}")
    console.print(f"  Tools: {', '.join(agent.registry.names())}")
    console.print(f"  Approval: {agent.config.approval_mode}")
    console.print()

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]再见！[/dim]")
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit", "q"):
            break

        # 特殊命令
        if user_input.startswith("/"):
            handle_command(user_input, agent)
            continue

        agent.chat(user_input)


def handle_command(cmd: str, agent: AgentLoop) -> None:
    """处理斜杠命令"""
    parts = cmd.split(maxsplit=1)
    command = parts[0].lower()

    if command == "/skills":
        skills = agent.skills.list_skills()
        if skills:
            for s in skills:
                console.print(f"  {s.name}: {s.description}")
        else:
            console.print("  No skills found")

    elif command == "/load" and len(parts) > 1:
        name = parts[1].strip()
        content = agent.skills.load(name)
        if content:
            console.print(f"  [green]Loaded skill: {name}[/green]")
        else:
            console.print(f"  [red]Skill not found: {name}[/red]")

    elif command == "/memory":
        ctx = agent.memory.as_context()
        console.print(ctx or "  No memories")

    elif command == "/save" and len(parts) > 1:
        agent.memory.add(parts[1].strip())
        console.print("  [green]Saved to memory[/green]")

    elif command == "/tools":
        for name in agent.registry.names():
            t = agent.registry.get(name)
            console.print(f"  {name}: {t.description if t else ''}")

    else:
        console.print("  Commands: /skills, /load <name>, /memory, /save <text>, /tools")


def main():
    parser = argparse.ArgumentParser(description="Agent Scaffold — 蒸馏自 Claude Code / Codex / Hermes")
    parser.add_argument("prompt", nargs="?", help="单次执行的prompt (省略则进入交互模式)")
    parser.add_argument("--config", default="config.yaml", help="配置文件路径")
    parser.add_argument("--model", help="覆盖模型名")
    parser.add_argument("--approval", choices=["suggest", "auto-edit", "full-auto"], help="审批模式")
    parser.add_argument("--api-base", help="API base URL")
    parser.add_argument("--api-key", help="API key")
    args = parser.parse_args()

    config = load_config(args.config)
    if args.model:
        config.model = args.model
    if args.approval:
        config.approval_mode = args.approval
    if args.api_base:
        config.api_base = args.api_base
    if args.api_key:
        config.api_key = args.api_key

    agent = AgentLoop(config)

    if args.prompt:
        agent.chat(args.prompt)
    else:
        interactive_mode(agent)


if __name__ == "__main__":
    main()
