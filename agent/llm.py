"""LLM客户端 — 兼容OpenAI / DashScope / vLLM / Ollama"""
from __future__ import annotations
import uuid
from typing import Any
from openai import OpenAI
from .models import Message, ToolCall, AgentConfig


class LLMClient:
    """OpenAI兼容的LLM客户端"""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.client = OpenAI(
            api_key=config.api_key,
            base_url=config.api_base,
        )

    def chat(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
    ) -> tuple[str, list[ToolCall]]:
        """
        发送对话请求，返回 (content, tool_calls)
        """
        openai_msgs = [m.to_dict() for m in messages]
        kwargs: dict[str, Any] = {
            "model": self.config.model,
            "messages": openai_msgs,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        response = self.client.chat.completions.create(**kwargs)
        choice = response.choices[0]
        msg = choice.message

        content = msg.content or ""
        tool_calls = []
        if msg.tool_calls:
            for tc in msg.tool_calls:
                tool_calls.append(ToolCall(
                    id=tc.id,
                    name=tc.function.name,
                    arguments=tc.function.arguments,
                ))

        return content, tool_calls
