# Copyright 2026 MonsterZeZe
# Licensed under the Apache License, Version 2.0
# Repository: https://github.com/MonsterZeZe/AuditAgent

"""推理生成节点（基于 messages 含工具结果 + RAG 上下文生成回答）。"""

from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

from app.core.config.settings import get_settings
from graph.state import AgentState

_CASE_DISCLAIMER = "注意：判例仅作个案参考，不能作为执业依据，法定依据以法规为准。"


async def generate(state: AgentState) -> AgentState:
    """推理生成：基于 messages（含工具结果）与 RAG 上下文生成回答。"""
    if state.get("metadata", {}).get("injection", {}).get("detected"):
        return state  # 已拒绝注入，跳过

    # 基础消息：first_agent 产生的 messages（含工具调用与结果）
    messages = list(state.get("messages") or [])

    # RAG 上下文注入
    rag_contexts = state.get("rag_contexts") or {}
    context_parts: list[str] = []
    for target, ctx in rag_contexts.items():
        if ctx and ctx.get("assembled_prompt"):
            label = "法定依据 · 法规知识库" if target == "law" else f"知识库 · {target}"
            context_parts.append(f"【{label}】\n{ctx['assembled_prompt']}")

    if context_parts:
        context_text = "\n\n".join(context_parts)
        suffix = f"\n\n{_CASE_DISCLAIMER}" if "case" in rag_contexts else ""
        messages = [
            SystemMessage(content=f"参考资料（引用时注明来源）：\n{context_text}{suffix}")
        ] + messages

    # 无 messages（direct 且无工具）时，组装基础消息
    if not messages:
        query = state.get("normalized_input", "") or state.get("user_input", "")
        system_content = "你是一名专业的审计助手，回答需严谨、可追溯。"
        long_term = state.get("long_term_memory", [])
        if long_term:
            memory_text = "\n".join(
                f"[历史关注] {m.get('content', '')[:120]}" for m in long_term[:3]
            )
            system_content += f"\n\n用户近期关注与历史问答：\n{memory_text}"
        history: list[Any] = []
        for m in state.get("chat_history", []):
            if m.get("role") == "user":
                history.append(HumanMessage(content=m.get("content", "")))
            elif m.get("role") == "assistant":
                history.append(AIMessage(content=m.get("content", "")))
        messages = [SystemMessage(content=system_content)] + history + [
            HumanMessage(content=query)
        ]

    settings = get_settings()
    llm = ChatOllama(model=settings.ollama_model, temperature=settings.model_temperature)
    response = await llm.ainvoke(messages)
    state["generation"] = getattr(response, "content", "") or ""
    return state
