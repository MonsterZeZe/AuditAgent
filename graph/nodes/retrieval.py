"""RAG 检索节点与子图。"""

import logging

from langgraph.graph import END, StateGraph

from graph.services import get_rag_engine
from graph.state import AgentState

logger = logging.getLogger(__name__)


def retrieve(state: AgentState) -> AgentState:
    """RAG 检索：二阶检索，组装上下文。检索失败时降级为纯问答。"""
    try:
        engine = get_rag_engine()
        query = state.get("normalized_input", "") or state.get("user_input", "")
        result = engine.retrieve(query)
        state["retrieval_results"] = result["chunks"]
        state["rag_context"] = result
    except Exception as exc:  # noqa: BLE001 - 检索失败降级，不阻断主流程
        logger.warning("RAG 检索失败，降级为纯模型问答: %s", exc)
        state["retrieval_results"] = []
        state["rag_context"] = {"chunks": [], "sources": [], "assembled_prompt": ""}
    return state


def build_retrieval_subgraph():
    """RAG 检索子图。"""
    builder = StateGraph(AgentState)
    builder.add_node("retrieve", retrieve)
    builder.set_entry_point("retrieve")
    builder.add_edge("retrieve", END)
    return builder.compile()
