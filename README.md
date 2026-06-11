# Agent Scaffold — 蒸馏自 Claude Code / Codex / Hermes

## 架构蒸馏

### 三者共性（核心Agent范式）
```
while True:
    response = llm.chat(messages, tools)
    if response.stop_reason == "end_turn": break
    for tool_call in response.tool_calls:
        result = execute_tool(tool_call)
        messages.append(tool_result(result))
```

### 各家亮点

| 特性 | Claude Code | Codex | Hermes |
|------|-------------|-------|--------|
| 编辑方式 | search-replace (old→new) | unified diff patch | search-replace |
| 权限模型 | 分级: auto/ask/deny | suggest/auto-edit/full-auto | 隐式信任 |
| 沙箱 | 无OS沙箱 | macOS Seatbelt / Docker | 无 |
| 子Agent | Agent tool (递归) | 无 | delegate_task (单层) |
| 技能系统 | 无 | 无 | Skills (markdown+scripts) |
| 记忆 | CLAUDE.md 文件 | instructions.md | Memory工具 + 持久化 |
| 上下文注入 | 层级CLAUDE.md | 系统prompt | AGENTS.md + Skills |
| UI框架 | 终端ANSI | Ink (React终端) | 终端ANSI |
| 持久Shell | ✓ | ✓ (subprocess) | ✓ |
| MCP | 无 | 无 | 原生支持 |
| 定时任务 | 无 | 无 | Cron jobs |

### 蒸馏出的核心设计原则

1. **Agent Loop极简** — 整个循环<200行，不需要框架
2. **Edit > Write** — search-replace比全文件覆写省context
3. **Tool = schema + execute** — 扁平注册，无需继承
4. **Permission是第一公民** — 工具和执行之间必须有权限层
5. **子Agent隔离上下文** — 复杂任务spawn子agent，返回summary
6. **项目文件注入** — CLAUDE.md/AGENTS.md注入system prompt
7. **Shell保持状态** — persistent session (cwd, env)

## 项目结构

```
agent-scaffold/
├── README.md              # 本文件
├── requirements.txt
├── config.yaml            # 配置
├── AGENTS.md              # 项目上下文注入
├── agent/
│   ├── __init__.py
│   ├── main.py            # 入口 + CLI
│   ├── loop.py            # 核心Agent循环
│   ├── models.py          # 数据模型
│   ├── llm.py             # LLM客户端 (OpenAI兼容)
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── registry.py    # Tool注册表
│   │   ├── base.py        # Tool基类
│   │   ├── shell.py       # Bash执行 (persistent)
│   │   ├── file_ops.py    # Read/Write/Edit
│   │   ├── search.py      # Glob/Grep
│   │   └── delegate.py    # 子Agent委托
│   ├── permissions.py     # 权限审批层
│   ├── context.py         # 上下文管理 (AGENTS.md加载)
│   ├── memory.py          # 持久记忆
│   └── skills.py          # 技能系统
└── examples/
    └── hello.py
```

## 快速开始

```bash
cd agent-scaffold
pip install -r requirements.txt
python -m agent.main --help
python -m agent.main "帮我看看当前目录有什么文件"
```
