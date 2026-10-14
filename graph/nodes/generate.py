"""推理生成节点。"""

from graph.services import get_llm
from graph.state import AgentState

_CASE_DISCLAIMER = "注意：判例仅作个案参考，不能作为执业依据，法定依据以法规为准。"


def generate(state: AgentState) -> AgentState:
    """推理生成：按 RAG 目标组装上下文，调用本地大模型。"""
    if state.get("metadata", {}).get("injection", {}).get("detected"):
        return state  # 已拒绝注入，跳过模型调用
    llm = get_llm()
    query = state.get("normalized_input", "") or state.get("user_input", "")
    target = state.get("rag_target", "law")

    law_ctx = state.get("rag_context")
    case_ctx = state.get("case_context")

    context_parts: list[str] = []
    if target in ("law", "both") and law_ctx and law_ctx.get("assembled_prompt"):
        context_parts.append(f"【法定依据 · 法规知识库】\n{law_ctx['assembled_prompt']}")
    if target in ("case", "both") and case_ctx and case_ctx.get("assembled_prompt"):
        context_parts.append(f"【案例参考 · 判例知识库】\n{case_ctx['assembled_prompt']}")

    if context_parts:
        context_text = "\n\n".join(context_parts)
        prompt = f"请根据以下参考资料回答用户问题，并注明引用来源。\n\n{context_text}\n\n用户问题: {query}"
        if target in ("case", "both"):
            prompt += f"\n\n{_CASE_DISCLAIMER}"
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
