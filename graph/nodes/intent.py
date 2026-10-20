# Copyright 2026 MonsterZeZe
# Licensed under the Apache License, Version 2.0
# Repository: https://github.com/MonsterZeZe/AuditAgent

"""意图识别节点。"""

from typing import Optional

from graph.services import get_intent_router
from graph.state import AgentState


async def _llm_rag_routing(query: str) -> Optional[list[str]]:
    """LLM 决策 RAG 子路由（知识库列表），文本 JSON 输出。"""
    import json
    import re

    from langchain_ollama import ChatOllama

    from app.core.config.settings import get_settings

    prompt = (
        "你是审计知识库路由。判断用户问题应检索哪些知识库：\n"
        "1. law - 法规知识库（审计准则、法律法规，法定依据）\n"
        "2. case - 判例知识库（判决书、处罚案例，个案参考）\n\n"
        '只输出 JSON：{"targets": ["law"]} 或 {"targets": ["case"]} 或 {"targets": ["law", "case"]}\n\n'
        f"用户问题：{query}"
    )

    try:
        llm = ChatOllama(model=get_settings().ollama_model, temperature=0)
        response = await llm.ainvoke([{"role": "user", "content": prompt}])
        text = getattr(response, "content", "")
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            return None
        data = json.loads(match.group())
        targets = data.get("targets")
        if isinstance(targets, list):
            return [t for t in targets if t in ("law", "case")]
        return None
    except Exception:  # noqa: BLE001 - LLM 决策失败返回 None
        return None


async def classify_intent(state: AgentState) -> AgentState:
    """意图识别与路由（RAG 子路由低置信度时 LLM 兜底）。"""
    router = get_intent_router()
    text = state.get("normalized_input", "") or state.get("user_input", "")
    intent = router.classify(text)
    state["intent"] = intent
    state["route"] = intent["route"]

    rag_targets = intent.get("rag_targets")
    if intent["route"] == "rag" and not rag_targets:
        # 低置信度（规则未明确区分知识库），LLM 自主决策
        rag_targets = await _llm_rag_routing(text) or ["law"]
    state["rag_targets"] = rag_targets or ["law"]
    return state
