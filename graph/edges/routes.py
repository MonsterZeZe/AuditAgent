"""边与路由逻辑（条件边）。"""

from graph.state import AgentState


def route_intent(state: AgentState) -> str:
    """意图条件路由。"""
    return state.get("route", "direct")


def should_retry(state: AgentState) -> str:
    """校验回流路由。"""
    validation = state.get("validation")
    if validation and not validation.get("passed"):
        if state.get("retry_count", 0) < state.get("max_retries", 2):
            return "retry"
        return "fallback"
    return "continue"
