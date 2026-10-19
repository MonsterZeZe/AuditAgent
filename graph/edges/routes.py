# Copyright 2026 MonsterZeZe
# Licensed under the Apache License, Version 2.0
# Repository: https://github.com/MonsterZeZe/AuditAgent

"""边与路由逻辑（条件边）。"""

from graph.state import AgentState


def should_call_tool(state: AgentState) -> str:
    """first_agent 后：有 tool_calls 进 tool_node，否则进 intent。"""
    messages = state.get("messages") or []
    if messages and getattr(messages[-1], "tool_calls", None):
        return "tools"
    return "intent"


def should_retrieve(state: AgentState) -> str:
    """intent 后：需要 RAG 进 retrieval，否则进 generate。"""
    if state.get("route") == "rag":
        return "retrieve"
    return "generate"


def should_retry(state: AgentState) -> str:
    """校验回流路由。"""
    validation = state.get("validation")
    if validation and not validation.get("passed"):
        if state.get("retry_count", 0) < state.get("max_retries", 2):
            return "retry"
        return "fallback"
    return "continue"
