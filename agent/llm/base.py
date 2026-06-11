"""Provider基类 — 蒸馏自LiteLLM的Translation层设计

每个Provider实现:
  - transform_request(): OpenAI格式 → Provider格式
  - transform_response(): Provider格式 → OpenAI格式
  - get_api_base(): 返回endpoint
  - get_headers(): 返回认证headers

LiteLLM核心洞察: 80%的provider都兼容OpenAI格式，
只有少数(Anthropic/Bedrock/Vertex)需要真正的转换。
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any
import json


@dataclass
class ProviderConfig:
    """Provider配置"""
    api_base: str = ""
    api_key: str = ""
    default_model: str = ""
    max_tokens: int = 4096
    temperature: float = 0
    extra: dict[str, Any] = field(default_factory=dict)


class BaseProvider(ABC):
    """Provider基类 — 每个provider继承此类

    设计来源: LiteLLM llms/base_llm/chat/transformation.py
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider名称，如 'openai', 'dashscope', 'ollama'"""
        ...

    @property
    def models(self) -> list[str]:
        """该provider支持的model前缀列表"""
        return []

    def get_api_base(self, config: ProviderConfig) -> str:
        """返回API endpoint"""
        return config.api_base

    def get_headers(self, config: ProviderConfig) -> dict[str, str]:
        """返回认证headers"""
        return {"Authorization": f"Bearer {config.api_key}"}

    def transform_request(
        self, model: str, messages: list[dict], tools: list[dict] | None,
        max_tokens: int, temperature: float, **kwargs
    ) -> dict[str, Any]:
        """OpenAI格式 → Provider格式 (默认透传，80%的provider不需要转换)"""
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        return payload

    def transform_response(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Provider格式 → OpenAI格式 (默认透传)"""
        return raw

    def parse_tool_calls(self, message: dict) -> list[dict]:
        """从response message中提取tool_calls"""
        tool_calls = []
        for tc in message.get("tool_calls", []):
            fn = tc.get("function", {})
            args = fn.get("arguments", "{}")
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {}
            tool_calls.append({
                "id": tc.get("id", ""),
                "name": fn.get("name", ""),
                "arguments": args,
            })
        return tool_calls
