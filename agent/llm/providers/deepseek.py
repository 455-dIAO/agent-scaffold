"""DeepSeek Provider

DeepSeek兼容OpenAI格式，但有特有参数:
  - model: deepseek-chat, deepseek-reasoner
  - reasoning_content (reasoner模型的思考过程)
"""
from __future__ import annotations
from typing import Any
from ..base import BaseProvider, ProviderConfig


class DeepSeekProvider(BaseProvider):
    """DeepSeek Provider"""

    name = "deepseek"
    models = ["deepseek"]

    def get_api_base(self, config: ProviderConfig) -> str:
        return config.api_base or "https://api.deepseek.com/v1"

    def transform_response(self, raw: dict[str, Any]) -> dict[str, Any]:
        """处理DeepSeek的reasoning_content字段"""
        choices = raw.get("choices", [])
        for choice in choices:
            msg = choice.get("message", {})
            reasoning = msg.pop("reasoning_content", None)
            if reasoning:
                # 把推理过程放到_extra字段
                msg["_reasoning"] = reasoning
        return raw
