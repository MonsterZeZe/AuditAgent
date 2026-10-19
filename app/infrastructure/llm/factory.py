# Copyright 2026 MonsterZeZe
# Licensed under the Apache License, Version 2.0
# Repository: https://github.com/MonsterZeZe/AuditAgent

"""模型接入工厂。

根据配置选择模型来源：本地 Ollama 或远程 OpenAI 兼容 API。
上层业务通过工厂获取 provider，不感知具体实现。
"""

from app.core.config.settings import get_settings
from app.infrastructure.llm.base import LLMProvider


def create_llm_provider() -> LLMProvider:
    """根据配置创建模型 provider。"""
    settings = get_settings()
    if settings.llm_provider == "api":
        from app.infrastructure.llm.api_provider import ApiProvider

        return ApiProvider()
    from app.infrastructure.llm.ollama_provider import OllamaLLMProvider

    return OllamaLLMProvider()
