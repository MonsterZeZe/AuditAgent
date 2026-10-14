"""RAG 检索节点与子图（法规 / 判例 双知识库）。"""

import logging
from typing import Any, cast

from langgraph.graph import END, StateGraph

from graph.services import get_case_engine, get_law_engine
from graph.state import AgentState, RAGContext

logger = logging.getLogger(__name__)


def _retrieve(engine: Any, state: AgentState) -> RAGContext:
    """通用检索：调用引擎返回结果，失败降级为空上下文。"""
    try:
        query = state.get("normalized_input", "") or state.get("user_input", "")
        result = engine.retrieve(query)
        return cast(RAGContext, result)
    except Exception as exc:  # noqa: BLE001 - 检索失败降级，不阻断主流程
        logger.warning("RAG 检索失败，降级为纯模型问答: %s", exc)
        return {"chunks": [], "sources": [], "assembled_prompt": ""}


def retrieve_law(state: AgentState) -> AgentState:
    """法规知识库检索：审计准则、注册会计师法、财会法规。"""
    state["rag_context"] = _retrieve(get_law_engine(), state)
    return state


def retrieve_case(state: AgentState) -> AgentState:
    """判例知识库检索：判决书、处罚案例。"""
    state["case_context"] = _retrieve(get_case_engine(), state)
    return state


def retrieve_both(state: AgentState) -> AgentState:
    """法规 + 判例 双路检索。"""
    state = retrieve_law(state)
    state = retrieve_case(state)
    return state


def build_law_rag_subgraph():
    """法规 RAG 检索子图。"""
    builder = StateGraph(AgentState)
    builder.add_node("retrieve_law", retrieve_law)
    builder.set_entry_point("retrieve_law")
    builder.add_edge("retrieve_law", END)
    return builder.compile()


def build_case_rag_subgraph():
    """判例 RAG 检索子图。"""
    builder = StateGraph(AgentState)
    builder.add_node("retrieve_case", retrieve_case)
    builder.set_entry_point("retrieve_case")
    builder.add_edge("retrieve_case", END)
    return builder.compile()


def build_both_rag_subgraph():
    """法规 + 判例 双路检索子图。"""
    builder = StateGraph(AgentState)
    builder.add_node("retrieve_both", retrieve_both)
    builder.set_entry_point("retrieve_both")
    builder.add_edge("retrieve_both", END)
    return builder.compile()
