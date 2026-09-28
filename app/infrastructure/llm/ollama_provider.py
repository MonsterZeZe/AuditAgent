"""Ollama 本地大模型适配器。"""

from typing import Iterator, Optional

import ollama

from app.core.config.settings import get_settings
from app.infrastructure.llm.base import LLMParams, LLMProvider, LLMResponse, LLMUsage


class OllamaLLMProvider(LLMProvider):
    """基于 ollama 库的本地模型实现。"""

    def __init__(self) -> None:
        settings = get_settings()
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_model
        self._client = ollama.Client(host=self.base_url)

    def _options(self, params: LLMParams) -> dict:
        return {
            "temperature": params.temperature,
            "top_p": params.top_p,
            "num_predict": params.max_tokens,
        }

    def chat(
        self,
        messages: list[dict],
        params: Optional[LLMParams] = None,
    ) -> LLMResponse:
        params = params or LLMParams()
        response = self._client.chat(
            model=self.model,
            messages=messages,
            options=self._options(params),
        )
        message = response["message"]
        content = getattr(message, "content", "") or ""
        if not content:
            # qwen3 思考模式下 content 可能为空，fallback 到 thinking
            content = getattr(message, "thinking", "") or ""
        usage = LLMUsage(
            prompt_tokens=response.get("prompt_eval_count", 0),
            completion_tokens=response.get("eval_count", 0),
        )
        usage.total_tokens = usage.prompt_tokens + usage.completion_tokens
        return LLMResponse(
            content=content,
            usage=usage,
            model=self.model,
            raw=response,
        )

    async def achat(
        self,
        messages: list[dict],
        params: Optional[LLMParams] = None,
    ) -> LLMResponse:
        # 骨架阶段委托同步实现，后续替换为真正的异步客户端
        return self.chat(messages, params)

    def stream(
        self,
        messages: list[dict],
        params: Optional[LLMParams] = None,
    ) -> Iterator[str]:
        params = params or LLMParams()
        stream = self._client.chat(
            model=self.model,
            messages=messages,
            options=self._options(params),
            stream=True,
        )
        for chunk in stream:
            piece = chunk.get("message", {}).get("content", "")
            if piece:
                yield piece

    def count_tokens(self, text: str) -> int:
        # 粗略估计：按字符数近似，后续接入精确 tokenizer
        return len(text)
