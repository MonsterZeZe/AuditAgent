"""LangGraph 状态机组装。

图结构：
    preprocess → first_agent → intent → retrieval → generate → validation
                    ↑            ↓
                  tool_node ←（first_agent 有 tool_calls 时）
                              intent → generate（无需检索时）
"""

from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from app.domain.tools.langchain_tools import LANGCHAIN_TOOLS
from graph.edges.routes import should_call_tool, should_retrieve, should_retry
from graph.nodes.first_agent import first_agent
from graph.nodes.generate import generate
from graph.nodes.intent import classify_intent
from graph.nodes.preprocess import preprocess
from graph.nodes.retrieval import build_retrieval_subgraph
from graph.nodes.validation import build_validation_subgraph, save_checkpoint
from graph.state import AgentState


def build_graph():
    """构建 Agent 状态机。"""
    builder = StateGraph(AgentState)

    builder.add_node("preprocess", preprocess)
    builder.add_node("first_agent", first_agent)
    builder.add_node("tool_node", ToolNode(LANGCHAIN_TOOLS))
    builder.add_node("intent", classify_intent)
    builder.add_node("retrieval", build_retrieval_subgraph())
    builder.add_node("generate", generate)
    builder.add_node("validation", build_validation_subgraph())
    builder.add_node("save_checkpoint", save_checkpoint)

    builder.set_entry_point("preprocess")
    builder.add_edge("preprocess", "first_agent")

    builder.add_conditional_edges(
        "first_agent",
        should_call_tool,
        {"tools": "tool_node", "intent": "intent"},
    )
    builder.add_edge("tool_node", "first_agent")

    builder.add_conditional_edges(
        "intent",
        should_retrieve,
        {"retrieve": "retrieval", "generate": "generate"},
    )
    builder.add_edge("retrieval", "generate")
    builder.add_edge("generate", "validation")

    builder.add_conditional_edges(
        "validation",
        should_retry,
        {"retry": "generate", "fallback": "save_checkpoint", "continue": "save_checkpoint"},
    )
    builder.add_edge("save_checkpoint", END)

    return builder.compile()
