"""LangGraph 状态机组装（含能力型子图）。

主图调度三类能力子图（RAG 检索 / 工具执行 / 结果校验），
为多智能体阶段 2 的能力型拆分预留边界。
节点定义在 nodes/，路由逻辑在 edges/，本文件只负责组装。
"""

from langgraph.graph import END, StateGraph

from graph.edges.routes import route_intent, should_retry
from graph.nodes.generate import generate
from graph.nodes.intent import classify_intent
from graph.nodes.preprocess import preprocess
from graph.nodes.retrieval import build_retrieval_subgraph
from graph.nodes.tool import build_tool_subgraph
from graph.nodes.validation import build_validation_subgraph, save_checkpoint
from graph.state import AgentState


def build_graph():
    """构建 Agent 状态机（主图调度能力子图）。"""
    builder = StateGraph(AgentState)

    builder.add_node("preprocess", preprocess)
    builder.add_node("classify_intent", classify_intent)
    builder.add_node("retrieval", build_retrieval_subgraph())
    builder.add_node("tool", build_tool_subgraph())
    builder.add_node("generate", generate)
    builder.add_node("validation", build_validation_subgraph())
    builder.add_node("save_checkpoint", save_checkpoint)

    builder.set_entry_point("preprocess")
    builder.add_edge("preprocess", "classify_intent")

    builder.add_conditional_edges(
        "classify_intent",
        route_intent,
        {"rag": "retrieval", "tool": "tool", "direct": "generate"},
    )
    builder.add_edge("retrieval", "generate")
    builder.add_edge("tool", "generate")
    builder.add_edge("generate", "validation")

    builder.add_conditional_edges(
        "validation",
        should_retry,
        {"retry": "generate", "fallback": "save_checkpoint", "continue": "save_checkpoint"},
    )
    builder.add_edge("save_checkpoint", END)

    return builder.compile()
