# Copyright 2026 MonsterZeZe
# Licensed under the Apache License, Version 2.0
# Repository: https://github.com/MonsterZeZe/AuditAgent

"""结果校验与检查点节点、校验子图。"""

from langgraph.graph import END, StateGraph

from graph.state import AgentState


def validate(state: AgentState) -> AgentState:
    """结果校验：合规 / 质量 / 敏感信息校验（骨架实现为通过）。"""
    state["validation"] = {"passed": True, "issues": [], "score": 1.0}
    return state


def save_checkpoint(state: AgentState) -> AgentState:
    """检查点保存：由 LangGraph checkpointer 自动处理，此处标记完成。"""
    if state.get("execution_status") != "failed":
        state["execution_status"] = "success"
    return state


def build_validation_subgraph():
    """结果校验子图。"""
    builder = StateGraph(AgentState)
    builder.add_node("validate", validate)
    builder.set_entry_point("validate")
    builder.add_edge("validate", END)
    return builder.compile()
