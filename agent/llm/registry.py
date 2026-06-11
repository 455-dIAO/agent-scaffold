"""Provider注册表 — model → provider路由

设计来源: LiteLLM utils.py get_llm_provider()
核心逻辑: 根据model名前缀匹配provider
"""
from __future__ import annotations
from typing import Any
from .base import BaseProvider, ProviderConfig


class ProviderRegistry:
    """Provider注册表"""

    def __init__(self):
        self._providers: dict[str, BaseProvider] = {}
        self._model_prefixes: dict[str, str] = {}  # prefix -> provider_name
        self._configs: dict[str, ProviderConfig] = {}

    def register(
        self,
        provider: BaseProvider,
        config: ProviderConfig | None = None,
        default: bool = False,
    ) -> None:
        """注册provider"""
        self._providers[provider.name] = provider
        if config:
            self._configs[provider.name] = config
        # 注册model前缀映射
        for prefix in provider.models:
            self._model_prefixes[prefix] = provider.name
        # 标记默认provider
        if default:
            self._default_provider = provider.name

    def resolve(self, model: str) -> tuple[BaseProvider, ProviderConfig, str]:
        """解析model名 → (provider, config, 实际model名)

        支持格式:
          - "openai/gpt-4o"          → openai provider, gpt-4o
          - "dashscope/qwen3.5-plus" → dashscope provider, qwen3.5-plus
          - "gpt-4o"                 → 自动匹配前缀
          - "qwen3.5-plus"           → 自动匹配前缀
        """
        # 格式1: "provider/model"
        if "/" in model:
            provider_name, actual_model = model.split("/", 1)
            if provider_name in self._providers:
                provider = self._providers[provider_name]
                config = self._configs.get(provider_name, ProviderConfig())
                return provider, config, actual_model

        # 格式2: 自动匹配前缀 (最长前缀优先)
        best_match = None
        best_len = 0
        for prefix, provider_name in self._model_prefixes.items():
            if model.startswith(prefix) and len(prefix) > best_len:
                best_match = (prefix, provider_name)
                best_len = len(prefix)

        if best_match:
            prefix, provider_name = best_match
            provider = self._providers[provider_name]
            config = self._configs.get(provider_name, ProviderConfig())
            # 前缀匹配时model名不变，不做截断
            return provider, config, model

        # 格式3: 默认provider
        default_name = getattr(self, "_default_provider", None)
        if default_name and default_name in self._providers:
            provider = self._providers[default_name]
            config = self._configs.get(default_name, ProviderConfig())
            return provider, config, model

        available = ", ".join(self._providers.keys())
        raise ValueError(
            f"No provider for model '{model}'. "
            f"Available: {available}. "
            f"Use 'provider/model' format."
        )

    def list_providers(self) -> list[str]:
        return list(self._providers.keys())

    def list_models(self) -> dict[str, list[str]]:
        """返回 {provider: [models]}"""
        result = {}
        for name, provider in self._providers.items():
            result[name] = provider.models
        return result
