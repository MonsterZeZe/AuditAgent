"""工具执行节点与子图。"""

from uuid import uuid4

from langgraph.graph import END, StateGraph

from graph.services import get_tool_registry
from graph.state import AgentState


def execute_tool(state: AgentState) -> AgentState:
    """工具执行：匹配工具并执行。"""
    registry = get_tool_registry()
    query = state.get("normalized_input", "") or state.get("user_input", "")
    result = registry.execute("compliance_check", {"text": query})
    state["tool_results"] = [
        {
            "call_id": uuid4().hex,
            "tool_name": "compliance_check",
            "status": result.status,
            "output": result.output,
            "error": result.error,
        }
    ]
    return state


def build_tool_subgraph():
    """工具执行子图。"""
    builder = StateGraph(AgentState)
    builder.add_node("execute_tool", execute_tool)
    builder.set_entry_point("execute_tool")
    builder.add_edge("execute_tool", END)
    return builder.compile()
