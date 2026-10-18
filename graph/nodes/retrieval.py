"""RAG 检索节点（按知识库列表检索）。"""

import logging
from typing import Any, cast

from langgraph.graph import END, StateGraph

from graph.services import get_engine
from graph.state import AgentState, RAGContext

logger = logging.getLogger(__name__)


def _retrieve(engine: Any, state: AgentState) -> RAGContext:
    """调用引擎检索，失败降级为空上下文。"""
    try:
        query = state.get("normalized_input", "") or state.get("user_input", "")
        result = engine.retrieve(query)
        return cast(RAGContext, result)
    except Exception as exc:  # noqa: BLE001 - 检索失败降级，不阻断主流程
        logger.warning("RAG 检索失败，降级为纯模型问答: %s", exc)
        return {"chunks": [], "sources": [], "assembled_prompt": ""}


def retrieve(state: AgentState) -> AgentState:
    """根据 rag_targets 列表检索对应知识库，结果存入 rag_contexts。"""
    targets = state.get("rag_targets") or ["law"]
    contexts: dict[str, RAGContext] = {}
    for target in targets:
        contexts[target] = _retrieve(get_engine(target), state)
    state["rag_contexts"] = contexts
    return state


def build_retrieval_subgraph():
    """RAG 检索子图。"""
    builder = StateGraph(AgentState)
    builder.add_node("retrieve", retrieve)
    builder.set_entry_point("retrieve")
    builder.add_edge("retrieve", END)
    return builder.compile()
