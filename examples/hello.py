"""示例: 自定义工具注册"""
import sys
sys.path.insert(0, "..")

from agent.models import AgentConfig, ToolResult
from agent.tools.base import BaseTool
from agent.loop import AgentLoop
from typing import Any


# 自定义工具示例
class WeatherTool(BaseTool):
    name = "get_weather"
    description = "查询天气"
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "城市名"},
        },
        "required": ["city"],
    }

    def execute(self, city: str = "", **kw) -> ToolResult:
        # 这里模拟，实际可调API
        return ToolResult(
            tool_call_id="",
            content=f"{city}: 晴 25°C, 湿度 60%",
        )


if __name__ == "__main__":
    import os
    config = AgentConfig(
        api_base=os.environ.get("API_BASE", "https://coding.dashscope.aliyuncs.com/v1"),
        api_key=os.environ.get("DASHSCOPE_API_KEY", ""),
        model="qwen3.5-plus",
        approval_mode="full-auto",
    )

    agent = AgentLoop(config)
    agent.add_tool(WeatherTool())  # 注册自定义工具

    agent.chat("杭州今天天气怎么样？")
