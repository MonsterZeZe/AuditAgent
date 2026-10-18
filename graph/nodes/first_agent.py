"""first_agent 节点：LLM bind_tools，自主决策是否调用工具。"""

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

from app.core.config.settings import get_settings
from app.domain.tools.langchain_tools import LANGCHAIN_TOOLS
from graph.state import AgentState

_SYSTEM_PROMPT = (
    "你是一名专业的审计助手，回答需严谨、可追溯。"
    "若用户请求计算、生成底稿、识别发票等操作，请调用相应工具。"
)
_MAX_TOOL_ROUNDS = 3


def first_agent(state: AgentState) -> AgentState:
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

    # 统计已执行的工具轮数，超限则不再调用工具
    tool_rounds = sum(1 for m in messages if getattr(m, "type", "") == "tool")

    settings = get_settings()
    llm = ChatOllama(model=settings.ollama_model, temperature=settings.model_temperature)
    if tool_rounds >= _MAX_TOOL_ROUNDS:
        response = llm.invoke(messages)
    else:
        response = llm.bind_tools(LANGCHAIN_TOOLS).invoke(messages)

    return {"messages": [response]}
