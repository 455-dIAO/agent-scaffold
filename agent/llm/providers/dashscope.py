"""DashScope Provider — 阿里云百炼

DashScope的API完全兼容OpenAI格式，只需调整:
  - api_base: https://dashscope.aliyuncs.com/compatible-mode/v1
  - model名: qwen3.5-plus, qwen3.5-397B-A17B 等
  - 部分参数差异 (enable_thinking)

设计来源: LiteLLM llms/dashscope/
"""
from __future__ import annotations
from typing import Any
from ..base import BaseProvider, ProviderConfig


class DashScopeProvider(BaseProvider):
    """阿里云百炼Provider"""

    name = "dashscope"
    models = ["qwen", "qwq", "qwen3"]

    def get_api_base(self, config: ProviderConfig) -> str:
        return config.api_base or "https://dashscope.aliyuncs.com/compatible-mode/v1"

    def transform_request(
        self, model: str, messages: list[dict], tools: list[dict] | None,
        max_tokens: int, temperature: float, **kwargs
    ) -> dict[str, Any]:
        payload = super().transform_request(
            model, messages, tools, max_tokens, temperature, **kwargs
        )
        # DashScope特有参数
        if kwargs.get("enable_thinking"):
            payload["enable_thinking"] = True
            payload["temperature"] = 0.7  # thinking模式建议temperature>0
        return payload
