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
| 编辑方式 | search-replace | unified diff | search-replace |
| 权限模型 | 分级: auto/ask/deny | suggest/auto-edit/full-auto | 隐式信任 |
| 沙箱 | 无OS沙箱 | macOS Seatbelt / Docker | 无 |
| 子Agent | Agent tool (递归) | 无 | delegate_task |
| 技能系统 | 无 | 无 | Skills (markdown) |
| 记忆 | CLAUDE.md | instructions.md | Memory工具 |

### LiteLLM Provider适配模式 (新增)

集成LiteLLM的Translation层设计，支持100+模型自动路由：

```
config.yaml          →  ProviderRegistry  →  BaseProvider
(多provider配置)        (model→provider路由)    (transform_request/response)
                              ↓
                    OpenAI/DashScope/Ollama/DeepSeek...
```

## 项目结构

```
agent-scaffold/
├── README.md
├── config.yaml              # 多Provider配置
├── AGENTS.md                # 项目上下文注入
├── agent/
│   ├── main.py              # CLI入口
│   ├── loop.py              # 核心Agent循环
│   ├── models.py            # 数据模型
│   ├── permissions.py       # 权限审批层
│   ├── context.py           # 上下文管理
│   ├── memory.py            # 持久记忆
│   ├── skills.py            # 技能系统
│   ├── llm/                 # LLM层 (LiteLLM模式)
│   │   ├── client.py        # 统一客户端
│   │   ├── base.py          # Provider基类
│   │   ├── registry.py      # Provider注册表
│   │   └── providers/       # Provider实现
│   │       ├── openai_compat.py
│   │       ├── dashscope.py
│   │       ├── ollama.py
│   │       └── deepseek.py
│   └── tools/
│       ├── base.py          # Tool基类
│       ├── registry.py      # Tool注册表
│       ├── shell.py         # Bash执行
│       ├── file_ops.py      # Read/Write/Edit
│       ├── search.py        # Glob/Grep
│       └── delegate.py      # 子Agent委托
└── examples/
    ├── hello.py
    └── custom_tool.py
```

## 快速开始

```bash
pip install -r requirements.txt

# 交互模式 (默认DashScope)
DASHSCOPE_API_KEY=xxx python -m agent.main

# 指定模型
python -m agent.main --model "deepseek/deepseek-chat"
python -m agent.main --model "ollama/llama3"
python -m agent.main --model "openai/gpt-4o"

# 单次执行
python -m agent.main "帮我看看当前目录有什么文件"
```

## 添加自定义Provider

```python
from agent.llm.base import BaseProvider, ProviderConfig

class MyProvider(BaseProvider):
    name = "my_provider"
    models = ["my-model"]

    def transform_request(self, model, messages, tools, max_tokens, temperature, **kwargs):
        # OpenAI格式 → 你的格式
        return super().transform_request(model, messages, tools, max_tokens, temperature)

    def transform_response(self, raw):
        # 你的格式 → OpenAI格式
        return raw

# 注册
from agent.llm.registry import ProviderRegistry
registry.register(MyProvider(), ProviderConfig(api_base="...", api_key="..."))
```
