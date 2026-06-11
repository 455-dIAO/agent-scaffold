"""示例: 编程方式使用Agent (不走CLI)"""
import sys
sys.path.insert(0, "..")

import os
from agent.models import AgentConfig
from agent.loop import AgentLoop


def example():
    config = AgentConfig(
        api_base=os.environ.get("API_BASE", "https://coding.dashscope.aliyuncs.com/v1"),
        api_key=os.environ.get("DASHSCOPE_API_KEY", ""),
        model="qwen3.5-plus",
        approval_mode="suggest",
    )

    agent = AgentLoop(config)

    # 方式1: 单轮对话
    result = agent.chat("列出当前目录的Python文件")
    print(f"Result: {result}")

    # 方式2: 多轮对话 (自动保持上下文)
    agent.chat("把第一个文件的内容读出来")
    agent.chat("总结一下这个文件的功能")


if __name__ == "__main__":
    example()
