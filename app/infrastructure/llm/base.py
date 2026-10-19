# Copyright 2026 MonsterZeZe
# Licensed under the Apache License, Version 2.0
# Repository: https://github.com/MonsterZeZe/AuditAgent

"""大模型接入抽象接口。

定义统一 LLM 接口，彻底屏蔽底层模型实现差异。当前由 Ollama 实现，
后续可零代码修改替换为审计领域微调模型或其他模型服务。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Iterator, Optional


@dataclass
class LLMUsage:
    """Token 用量统计。"""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class LLMResponse:
    """模型响应。"""

    content: str
    usage: LLMUsage = field(default_factory=LLMUsage)
    model: str = ""
    raw: Any = field(default_factory=dict)


@dataclass
class LLMParams:
    """模型调用参数。"""

    temperature: float = 0.2
    top_p: float = 0.9
    max_tokens: int = 2048
    timeout: int = 60
    stop: Optional[list[str]] = None


class LLMProvider(ABC):
    """统一大模型接入接口。"""

    @abstractmethod
    def chat(
        self,
        messages: list[dict],
        params: Optional[LLMParams] = None,
    ) -> LLMResponse:
        """同步聊天补全。"""

    @abstractmethod
    async def achat(
        self,
        messages: list[dict],
        params: Optional[LLMParams] = None,
    ) -> LLMResponse:
        """异步聊天补全。"""

    @abstractmethod
    def stream(
        self,
        messages: list[dict],
        params: Optional[LLMParams] = None,
    ) -> Iterator[str]:
        """流式输出，逐段返回文本。"""

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Token 计数，用于上下文窗口管理与成本管控。"""
