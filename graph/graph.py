"""LangGraph 状态机组装。

定义 Agent 状态机的节点、边与条件路由。节点调用领域层接口，
通过懒加载单例获取服务实例，避免启动时建立重资源连接。
"""

import logging
from functools import lru_cache

from langgraph.graph import END, StateGraph

from graph.state import AgentState

logger = logging.getLogger(__name__)


# ---- 服务懒加载 ----

@lru_cache
def _get_intent_router():
    from app.domain.intent.router import IntentRouter

    return IntentRouter()


@lru_cache
def _get_llm():
    from app.infrastructure.llm.ollama_provider import OllamaLLMProvider

    return OllamaLLMProvider()


@lru_cache
def _get_rag_engine():
    from app.domain.rag.embedding import OllamaEmbeddingProvider
    from app.domain.rag.engine import RAGEngine
    from app.domain.rag.reranker import CrossEncoderReranker
    from app.infrastructure.vector_store.chroma_store import ChromaVectorStore

    vector_store = ChromaVectorStore()
    embedding = OllamaEmbeddingProvider()
    reranker = CrossEncoderReranker()
    engine = RAGEngine(vector_store=vector_store, embedding=embedding, reranker=reranker)
    engine.rebuild_bm25()  # 从向量库重建 BM25 索引
    return engine


# ---- 节点 ----

def preprocess(state: AgentState) -> AgentState:
    """输入预处理：清洗与标准化（脱敏、注入检测后续接入）。"""
    raw = state.get("user_input", "")
    state["normalized_input"] = raw.strip()
    state.setdefault("max_retries", 2)
    state.setdefault("retry_count", 0)
    return state


def classify_intent(state: AgentState) -> AgentState:
    """意图识别与路由。"""
    router = _get_intent_router()
    text = state.get("normalized_input", "") or state.get("user_input", "")
    intent = router.classify(text)
    state["intent"] = intent
    state["route"] = intent["route"]
    return state


def retrieve(state: AgentState) -> AgentState:
    """RAG 检索：二阶检索，组装上下文。检索失败时降级为纯问答。"""
    try:
        engine = _get_rag_engine()
        query = state.get("normalized_input", "") or state.get("user_input", "")
        result = engine.retrieve(query)
        state["retrieval_results"] = result["chunks"]
        state["rag_context"] = result
    except Exception as exc:  # noqa: BLE001 - 检索失败降级，不阻断主流程
        logger.warning("RAG 检索失败，降级为纯模型问答: %s", exc)
        state["retrieval_results"] = []
        state["rag_context"] = {"chunks": [], "sources": [], "assembled_prompt": ""}
    return state


def execute_tool(state: AgentState) -> AgentState:
    """工具执行：匹配工具并执行（工具插件接入后填充）。"""
    state["tool_results"] = []
    return state


def generate(state: AgentState) -> AgentState:
    """推理生成：组装 Prompt 调用本地大模型。"""
    llm = _get_llm()
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


def validate(state: AgentState) -> AgentState:
    """结果校验：合规 / 质量 / 敏感信息校验（骨架实现为通过）。"""
    state["validation"] = {"passed": True, "issues": [], "score": 1.0}
    return state


def save_checkpoint(state: AgentState) -> AgentState:
    """检查点保存：由 LangGraph checkpointer 自动处理，此处标记完成。"""
    state["execution_status"] = "success"
    return state


# ---- 条件路由 ----

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


# ---- 图组装 ----

def build_graph():
    """构建 Agent 状态机。"""
    builder = StateGraph(AgentState)

    builder.add_node("preprocess", preprocess)
    builder.add_node("classify_intent", classify_intent)
    builder.add_node("retrieve", retrieve)
    builder.add_node("execute_tool", execute_tool)
    builder.add_node("generate", generate)
    builder.add_node("validate", validate)
    builder.add_node("save_checkpoint", save_checkpoint)

    builder.set_entry_point("preprocess")
    builder.add_edge("preprocess", "classify_intent")

    builder.add_conditional_edges(
        "classify_intent",
        route_intent,
        {"rag": "retrieve", "tool": "execute_tool", "direct": "generate"},
    )
    builder.add_edge("retrieve", "generate")
    builder.add_edge("execute_tool", "generate")
    builder.add_edge("generate", "validate")

    builder.add_conditional_edges(
        "validate",
        should_retry,
        {"retry": "generate", "fallback": "save_checkpoint", "continue": "save_checkpoint"},
    )
    builder.add_edge("save_checkpoint", END)

    return builder.compile()
