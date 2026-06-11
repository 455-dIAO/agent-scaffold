"""Ollama Provider — 本地模型

Ollama兼容OpenAI格式: http://localhost:11434/v1
"""
from __future__ import annotations
from ..base import BaseProvider, ProviderConfig


class OllamaProvider(BaseProvider):
    """本地Ollama Provider"""

    name = "ollama"
    models = ["llama", "mistral", "qwen2", "deepseek-r1", "phi", "gemma"]

    def get_api_base(self, config: ProviderConfig) -> str:
        return config.api_base or "http://localhost:11434/v1"

    def get_headers(self, config: ProviderConfig) -> dict[str, str]:
        # Ollama通常不需要认证
        return {}
