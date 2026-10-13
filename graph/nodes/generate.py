"""推理生成节点。"""

from graph.services import get_llm
from graph.state import AgentState


def generate(state: AgentState) -> AgentState:
    """推理生成：组装 Prompt 调用本地大模型。"""
    if state.get("metadata", {}).get("injection", {}).get("detected"):
        return state  # 已拒绝注入，跳过模型调用
    llm = get_llm()
    query = state.get("normalized_input", "") or state.get("user_input", "")
    rag_context = state.get("rag_context")
    if rag_context and rag_context.get("assembled_prompt"):
        prompt = (
            "请根据以下参考资料回答用户问题，并注明引用来源。\n\n"
            f"参考资料:\n{rag_context['assembled_prompt']}\n\n"
            f"用户问题: {query}"
        )
    else:
        prompt = query
    history = [
        {"role": m.get("role"), "content": m.get("content")}
        for m in state.get("messages", [])
        if m.get("role") in ("user", "assistant")
    ]
    system_content = "你是一名专业的审计助手，回答需严谨、可追溯。"
    long_term = state.get("long_term_memory", [])
    if long_term:
        memory_text = "\n".join(
            f"[历史关注] {m.get('content', '')[:120]}" for m in long_term[:3]
        )
        system_content += f"\n\n用户近期关注与历史问答：\n{memory_text}"
    messages = (
        [{"role": "system", "content": system_content}]
        + history
        + [{"role": "user", "content": prompt}]
    )
    response = llm.chat(messages)
    state["generation"] = response.content
    return state
