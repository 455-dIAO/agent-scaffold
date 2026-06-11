"""OpenAI兼容Provider — 覆盖所有OpenAI格式API

兼容: OpenAI, Azure, vLLM, LM Studio, 任何OpenAI-compatible endpoint
设计来源: LiteLLM llms/openai/chat/gpt_transformation.py
"""
from __future__ import annotations
from typing import Any
from ..base import BaseProvider, ProviderConfig


class OpenAICompatProvider(BaseProvider):
    """OpenAI兼容Provider — 最通用的实现"""

    name = "openai"
    models = ["gpt-4", "gpt-3.5", "o1", "o3", "o4"]

    def get_api_base(self, config: ProviderConfig) -> str:
        return config.api_base or "https://api.openai.com/v1"

    # transform_request / transform_response 使用基类默认透传
    # 因为OpenAI格式本身就是"标准格式"
