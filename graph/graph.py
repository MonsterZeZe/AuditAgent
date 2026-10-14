"""LangGraph 状态机组装（含能力型子图）。

主图调度能力子图：RAG 检索细分为法规知识库、判例知识库、双路检索，
工具执行、结果校验各自封装为子图，为多智能体演进预留边界。
"""

from langgraph.graph import END, StateGraph

from graph.edges.routes import route_intent, should_retry
from graph.nodes.generate import generate
from graph.nodes.intent import classify_intent
from graph.nodes.preprocess import preprocess
from graph.nodes.retrieval import (
    build_both_rag_subgraph,
    build_case_rag_subgraph,
    build_law_rag_subgraph,
)
from graph.nodes.tool import build_tool_subgraph
from graph.nodes.validation import build_validation_subgraph, save_checkpoint
from graph.state import AgentState


def build_graph():
    """构建 Agent 状态机（主图调度能力子图）。"""
    builder = StateGraph(AgentState)

    builder.add_node("preprocess", preprocess)
    builder.add_node("classify_intent", classify_intent)
    builder.add_node("law_rag", build_law_rag_subgraph())
    builder.add_node("case_rag", build_case_rag_subgraph())
    builder.add_node("both_rag", build_both_rag_subgraph())
    builder.add_node("tool", build_tool_subgraph())
    builder.add_node("generate", generate)
    builder.add_node("validation", build_validation_subgraph())
    builder.add_node("save_checkpoint", save_checkpoint)

    builder.set_entry_point("preprocess")
    builder.add_edge("preprocess", "classify_intent")

    builder.add_conditional_edges(
        "classify_intent",
        route_intent,
        {
            "law": "law_rag",
            "case": "case_rag",
            "both": "both_rag",
            "tool": "tool",
            "direct": "generate",
        },
    )
    builder.add_edge("law_rag", "generate")
    builder.add_edge("case_rag", "generate")
    builder.add_edge("both_rag", "generate")
    builder.add_edge("tool", "generate")
    builder.add_edge("generate", "validation")

    builder.add_conditional_edges(
        "validation",
        should_retry,
        {"retry": "generate", "fallback": "save_checkpoint", "continue": "save_checkpoint"},
    )
    builder.add_edge("save_checkpoint", END)

    return builder.compile()
