"""推理生成节点（仅组装消息并生成，工具调用已移至 first_agent/tool_node）。"""

from langchain_ollama import ChatOllama

from app.core.config.settings import get_settings
from graph.state import AgentState

_CASE_DISCLAIMER = "注意：判例仅作个案参考，不能作为执业依据，法定依据以法规为准。"


def generate(state: AgentState) -> AgentState:
    """推理生成：组装 RAG 上下文与对话历史，调用 LLM 生成回答。"""
    if state.get("metadata", {}).get("injection", {}).get("detected"):
        return state  # 已拒绝注入，跳过

    query = state.get("normalized_input", "") or state.get("user_input", "")
    rag_contexts = state.get("rag_contexts") or {}

    # 组装 RAG 上下文（遍历所有检索到的知识库）
    context_parts: list[str] = []
    for target, ctx in rag_contexts.items():
        if ctx and ctx.get("assembled_prompt"):
            label = "法定依据 · 法规知识库" if target == "law" else f"知识库 · {target}"
            context_parts.append(f"【{label}】\n{ctx['assembled_prompt']}")

    if context_parts:
        context_text = "\n\n".join(context_parts)
        prompt = f"请根据以下参考资料回答用户问题，并注明引用来源。\n\n{context_text}\n\n用户问题: {query}"
        if "case" in rag_contexts:
            prompt += f"\n\n{_CASE_DISCLAIMER}"
    else:
        prompt = query

    # 组装消息
    system_content = "你是一名专业的审计助手，回答需严谨、可追溯。"
    long_term = state.get("long_term_memory", [])
    if long_term:
        memory_text = "\n".join(
            f"[历史关注] {m.get('content', '')[:120]}" for m in long_term[:3]
        )
        system_content += f"\n\n用户近期关注与历史问答：\n{memory_text}"

    history = [
        {"role": m.get("role"), "content": m.get("content")}
        for m in state.get("chat_history", [])
        if m.get("role") in ("user", "assistant")
    ]
    messages = (
        [{"role": "system", "content": system_content}]
        + history
        + [{"role": "user", "content": prompt}]
    )

    settings = get_settings()
    llm = ChatOllama(model=settings.ollama_model, temperature=settings.model_temperature)
    response = llm.invoke(messages)
    state["generation"] = getattr(response, "content", "") or ""
    return state
