"""统一LLM客户端 — 蒸馏自LiteLLM的核心设计

核心流程 (来自LiteLLM ARCHITECTURE.md):
  request → resolve_provider → transform_request → HTTP → transform_response → parse

支持:
  - 100+模型自动路由 (provider/model格式)
  - Provider级参数转换
  - Fallback链
  - 成本追踪 (可选)
  - 同步/异步
"""
from __future__ import annotations
import json
import time
from typing import Any

import httpx

from ..models import Message, ToolCall, AgentConfig
from .base import BaseProvider, ProviderConfig
from .registry import ProviderRegistry
from .providers import (
    OpenAICompatProvider,
    DashScopeProvider,
    OllamaProvider,
    DeepSeekProvider,
)


class LLMClient:
    """统一LLM客户端

    设计来源:
    - LiteLLM main.py: completion() / acompletion() 统一入口
    - LiteLLM utils.py: get_llm_provider() 路由
    - LiteLLM llms/custom_httpx/llm_http_handler.py: HTTP执行
    """

    def __init__(self, config: AgentConfig):
        self.config = config
        self.registry = ProviderRegistry()
        self._http = httpx.Client(timeout=120)
        self._setup_providers()
        self._stats: list[dict[str, Any]] = []  # 调用统计

    def _setup_providers(self) -> None:
        """注册所有内置provider"""
        llm_cfg = self.config.llm_providers

        # 默认provider (从config.yaml的llm字段)
        default_config = ProviderConfig(
            api_base=self.config.api_base,
            api_key=self.config.api_key,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
        )

        # 注册provider (带config)
        providers_map = {
            "openai": (OpenAICompatProvider(), ProviderConfig(
                api_base=llm_cfg.get("openai", {}).get("api_base", "https://api.openai.com/v1"),
                api_key=llm_cfg.get("openai", {}).get("api_key", self.config.api_key),
            )),
            "dashscope": (DashScopeProvider(), ProviderConfig(
                api_base=llm_cfg.get("dashscope", {}).get("api_base", self.config.api_base),
                api_key=llm_cfg.get("dashscope", {}).get("api_key", self.config.api_key),
            )),
            "ollama": (OllamaProvider(), ProviderConfig(
                api_base=llm_cfg.get("ollama", {}).get("api_base", "http://localhost:11434/v1"),
            )),
            "deepseek": (DeepSeekProvider(), ProviderConfig(
                api_base=llm_cfg.get("deepseek", {}).get("api_base", "https://api.deepseek.com/v1"),
                api_key=llm_cfg.get("deepseek", {}).get("api_key", ""),
            )),
        }

        for name, (provider, cfg) in providers_map.items():
            self.registry.register(provider, cfg)

        # 默认provider (用config.yaml的主配置)
        default_provider = DashScopeProvider()  # 或根据api_base自动判断
        if "dashscope" in self.config.api_base:
            default_provider = DashScopeProvider()
        elif "openai.com" in self.config.api_base:
            default_provider = OpenAICompatProvider()
        elif "deepseek" in self.config.api_base:
            default_provider = DeepSeekProvider()
        elif "localhost" in self.config.api_base or "127.0.0.1" in self.config.api_base:
            default_provider = OllamaProvider()
        else:
            default_provider = OpenAICompatProvider()  # 兜底: OpenAI兼容

        self.registry.register(default_provider, default_config, default=True)

    def chat(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
        **kwargs,
    ) -> tuple[str, list[ToolCall]]:
        """发送对话请求，返回 (content, tool_calls)

        model格式:
          - None → 使用config默认model
          - "gpt-4o" → 自动路由到openai
          - "dashscope/qwen3.5-plus" → 显式指定provider
          - "deepseek/deepseek-chat" → 显式指定provider
        """
        model = model or self.config.model

        # 1) 解析provider
        provider, prov_config, actual_model = self.registry.resolve(model)

        # 2) 构建请求
        openai_msgs = [m.to_dict() for m in messages]

        payload = provider.transform_request(
            model=actual_model,
            messages=openai_msgs,
            tools=tools,
            max_tokens=kwargs.get("max_tokens", prov_config.max_tokens or self.config.max_tokens),
            temperature=kwargs.get("temperature", prov_config.temperature if prov_config.temperature is not None else self.config.temperature),
            **{k: v for k, v in kwargs.items() if k not in ("max_tokens", "temperature")},
        )

        # 3) HTTP请求
        api_base = provider.get_api_base(prov_config)
        headers = provider.get_headers(prov_config)
        headers["Content-Type"] = "application/json"

        start = time.time()
        try:
            resp = self._http.post(
                f"{api_base}/chat/completions",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            raw = resp.json()
        except httpx.HTTPStatusError as e:
            raise RuntimeError(
                f"LLM API error ({provider.name}): {e.response.status_code} - {e.response.text[:500]}"
            ) from e
        except httpx.RequestError as e:
            raise RuntimeError(
                f"LLM connection error ({provider.name}): {e}"
            ) from e

        # 4) 转换响应
        result = provider.transform_response(raw)
        latency = time.time() - start

        # 5) 解析结果
        choice = result.get("choices", [{}])[0]
        message = choice.get("message", {})
        content = message.get("content", "") or ""

        # 6) 提取tool_calls
        tool_calls_data = provider.parse_tool_calls(message)
        tool_calls = [
            ToolCall(id=tc["id"], name=tc["name"], arguments=tc["arguments"])
            for tc in tool_calls_data
        ]

        # 7) 记录统计
        usage = result.get("usage", {})
        self._stats.append({
            "model": model,
            "provider": provider.name,
            "latency": round(latency, 2),
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
        })

        return content, tool_calls

    def get_stats(self) -> dict[str, Any]:
        """返回调用统计"""
        if not self._stats:
            return {}
        total_latency = sum(s["latency"] for s in self._stats)
        total_prompt = sum(s["prompt_tokens"] for s in self._stats)
        total_completion = sum(s["completion_tokens"] for s in self._stats)
        return {
            "calls": len(self._stats),
            "total_latency": round(total_latency, 2),
            "avg_latency": round(total_latency / len(self._stats), 2),
            "total_prompt_tokens": total_prompt,
            "total_completion_tokens": total_completion,
            "total_tokens": total_prompt + total_completion,
            "by_provider": self._stats_by_provider(),
        }

    def _stats_by_provider(self) -> dict[str, dict]:
        by_prov: dict[str, dict] = {}
        for s in self._stats:
            p = s["provider"]
            if p not in by_prov:
                by_prov[p] = {"calls": 0, "latency": 0, "tokens": 0}
            by_prov[p]["calls"] += 1
            by_prov[p]["latency"] += s["latency"]
            by_prov[p]["tokens"] += s["prompt_tokens"] + s["completion_tokens"]
        return by_prov

    def close(self) -> None:
        self._http.close()

    def __del__(self):
        try:
            self._http.close()
        except Exception:
            pass
