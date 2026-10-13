"""API 大模型适配器（OpenAI 兼容）。

支持任意 OpenAI 兼容的远程模型服务（OpenAI / DeepSeek / 通义千问 / vLLM 等），
通过 base_url + api_key + model 配置接入。
"""

from typing import Iterator, Optional

import httpx

from app.core.config.settings import get_settings
from app.infrastructure.llm.base import LLMParams, LLMProvider, LLMResponse, LLMUsage


class ApiProvider(LLMProvider):
    """OpenAI 兼容 API 实现。"""

    def __init__(self) -> None:
        settings = get_settings()
        self.base_url = settings.api_base_url.rstrip("/")
        self.api_key = settings.api_key
        self.model = settings.api_model

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}"}

    def _body(self, messages: list[dict], params: LLMParams) -> dict:
        return {
            "model": self.model,
            "messages": messages,
            "temperature": params.temperature,
            "top_p": params.top_p,
            "max_tokens": params.max_tokens,
        }

    def chat(
        self,
        messages: list[dict],
        params: Optional[LLMParams] = None,
    ) -> LLMResponse:
        params = params or LLMParams()
        resp = httpx.post(
            f"{self.base_url}/chat/completions",
            json=self._body(messages, params),
            headers=self._headers(),
            timeout=params.timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"] or ""
        usage = LLMUsage(
            prompt_tokens=data.get("usage", {}).get("prompt_tokens", 0),
            completion_tokens=data.get("usage", {}).get("completion_tokens", 0),
        )
        usage.total_tokens = usage.prompt_tokens + usage.completion_tokens
        return LLMResponse(content=content, usage=usage, model=self.model, raw=data)

    async def achat(
        self,
        messages: list[dict],
        params: Optional[LLMParams] = None,
    ) -> LLMResponse:
        # 骨架阶段委托同步实现
        return self.chat(messages, params)

    def stream(
        self,
        messages: list[dict],
        params: Optional[LLMParams] = None,
    ) -> Iterator[str]:
        # 骨架阶段以非流式实现，后续可解析 SSE 流
        response = self.chat(messages, params)
        yield response.content

    def count_tokens(self, text: str) -> int:
        return len(text)
