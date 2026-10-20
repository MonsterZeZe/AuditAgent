# Copyright 2026 MonsterZeZe
# Licensed under the Apache License, Version 2.0
# Repository: https://github.com/MonsterZeZe/AuditAgent

"""first_agent 节点：LLM bind_tools，自主决策是否调用工具。"""

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

from app.core.config.settings import get_settings
from app.domain.tools.langchain_tools import LANGCHAIN_TOOLS
from graph.state import AgentState

_SYSTEM_PROMPT = (
    "你是一名专业的审计助手。当用户请求以下操作时，必须调用对应工具，不要直接回答：\n"
    "1. 识别发票、提取发票信息 → 调用 invoice_ocr 工具\n"
    "2. 生成审计底稿、审定表、明细表、询证函 → 调用 working_paper_generator 工具\n"
    "3. 财务计算、勾稽校验、差异计算、计提/折旧/税费测算 → 调用 arithmetic_validator 工具\n"
    "只有与上述工具无关的问题才直接回答。"
)


async def first_agent(state: AgentState) -> AgentState:
    """LLM bind_tools，判断是否调用工具，返回 AIMessage（可能含 tool_calls）。"""
    messages = list(state.get("messages") or [])
    if not messages:
        system_content = _SYSTEM_PROMPT
        uploaded_files = state.get("uploaded_files") or []
        if uploaded_files:
            system_content += "\n\n当前会话已上传文件：\n" + "\n".join(
                f"- {f}" for f in uploaded_files
            )
            system_content += "\n如需识别发票，请调用 invoice_ocr 工具，file_path 传上述文件路径。"
        messages = [
            SystemMessage(content=system_content),
            HumanMessage(
                content=state.get("normalized_input", "") or state.get("user_input", "")
            ),
        ]

    # 已有工具执行结果（ToolMessage）时，不再调用工具，交由 generate 生成最终回答
    has_tool_result = any(getattr(m, "type", "") == "tool" for m in messages)
    if has_tool_result:
        return {}

    settings = get_settings()
    llm = ChatOllama(model=settings.ollama_model, temperature=settings.model_temperature)
    response = await llm.bind_tools(LANGCHAIN_TOOLS).ainvoke(messages)
    return {"messages": [response]}
