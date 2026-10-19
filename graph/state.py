# Copyright 2026 MonsterZeZe
# Licensed under the Apache License, Version 2.0
# Repository: https://github.com/MonsterZeZe/AuditAgent

"""LangGraph Agent 状态契约定义。

State 仅保留必要字段，大体积中间产物（检索结果、工具结果）按需持久化，
避免状态膨胀影响序列化与传输。所有字段必须可 JSON 序列化，
禁止在 State 中持有模型实例、连接句柄、文件句柄等对象。
"""

from typing import Annotated, Any, Literal, TypedDict

from langgraph.graph.message import add_messages
from typing_extensions import NotRequired


class Message(TypedDict):
    """对话消息（短期记忆的最小单元）。"""

    role: Literal["system", "user", "assistant", "tool"]
    content: str
    created_at: str
    tool_call_id: NotRequired[str]
    meta: NotRequired[dict]


class IntentResult(TypedDict):
    """意图识别结果。"""

    intent_type: Literal["knowledge_query", "direct_qa", "unknown"]
    confidence: float
    route: Literal["rag", "direct"]
    rag_targets: NotRequired[list[str]]
    sub_queries: NotRequired[list[str]]
    reason: NotRequired[str]


class ScoredDoc(TypedDict):
    """召回文档片段（含打分）。"""

    doc_id: str
    collection: str
    content: str
    score: float
    rank: NotRequired[int]
    metadata: dict


class ToolCall(TypedDict):
    """工具调用请求。"""

    tool_name: str
    params: dict
    call_id: str


class ToolResult(TypedDict):
    """工具执行结果。"""

    call_id: str
    tool_name: str
    status: Literal["success", "failed"]
    output: NotRequired[dict]
    error: NotRequired[str]


class RAGContext(TypedDict):
    """组装后的 RAG 上下文。"""

    chunks: list[ScoredDoc]
    assembled_prompt: str
    sources: list[dict]


class ValidationResult(TypedDict):
    """结果校验结果。"""

    passed: bool
    score: NotRequired[float]
    issues: list[str]
    filtered: NotRequired[str]


class Memory(TypedDict):
    """长期记忆条目。"""

    memory_id: str
    memory_type: Literal["user_profile", "domain_knowledge", "task_history"]
    content: str
    user_id: str
    topic: NotRequired[str]
    created_at: str
    updated_at: str


class AgentState(TypedDict, total=False):
    """Agent 全局状态。"""

    # 身份与会话
    session_id: str
    trace_id: str
    user_id: str
    tenant_id: NotRequired[str]

    # 输入
    user_input: str
    normalized_input: NotRequired[str]
    uploaded_files: NotRequired[list[str]]  # 当前会话上传的文件路径

    # agent 循环消息（LangChain BaseMessage，reducer: add_messages）
    messages: Annotated[list[Any], add_messages]

    # 对话历史（dict 格式，会话持久化用）
    chat_history: NotRequired[list[Message]]

    # 意图与路由
    intent: NotRequired[IntentResult]
    route: NotRequired[Literal["rag", "direct"]]
    rag_targets: NotRequired[list[str]]

    # 检索
    retrieval_results: NotRequired[list[ScoredDoc]]
    rag_contexts: NotRequired[dict[str, RAGContext]]  # {知识库标识: 检索上下文}

    # 工具
    tool_calls: NotRequired[list[ToolCall]]
    tool_results: NotRequired[list[ToolResult]]

    # 生成与校验
    generation: NotRequired[str]
    validation: NotRequired[ValidationResult]

    # 流程控制
    # 说明：检查点 ID 由 LangGraph checkpointer 框架级管理，不在 State 中维护
    retry_count: NotRequired[int]
    max_retries: NotRequired[int]
    execution_status: NotRequired[Literal["running", "success", "failed"]]

    # 记忆与扩展
    long_term_memory: NotRequired[list[Memory]]
    metadata: NotRequired[dict]
