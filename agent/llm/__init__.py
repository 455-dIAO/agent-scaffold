"""LLM层 — 集成LiteLLM provider适配模式

统一接口: completion() / acompletion()
支持100+模型，自动provider路由
"""
from .client import LLMClient

__all__ = ["LLMClient"]
