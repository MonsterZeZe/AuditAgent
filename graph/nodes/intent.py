"""意图识别节点。"""

from graph.services import get_intent_router
from graph.state import AgentState


def classify_intent(state: AgentState) -> AgentState:
    """意图识别与路由。"""
    router = get_intent_router()
    text = state.get("normalized_input", "") or state.get("user_input", "")
    intent = router.classify(text)
    state["intent"] = intent
    state["route"] = intent["route"]
    state["rag_target"] = intent.get("rag_target", "law")
    return state
