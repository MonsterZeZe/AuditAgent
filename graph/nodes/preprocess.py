"""输入预处理节点。"""

from graph.services import get_injection_detector
from graph.state import AgentState


def preprocess(state: AgentState) -> AgentState:
    """输入预处理：注入检测 + 清洗标准化。"""
    raw = state.get("user_input", "")
    report = get_injection_detector().detect(raw)
    if report["detected"]:
        state["metadata"] = {"injection": report}
        state["generation"] = "检测到疑似注入内容，已拒绝处理。请勿尝试覆盖系统指令或泄露提示词。"
        state["execution_status"] = "failed"
    state["normalized_input"] = raw.strip()
    state.setdefault("max_retries", 2)
    state.setdefault("retry_count", 0)
    return state
