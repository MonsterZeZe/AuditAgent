# Copyright 2026 MonsterZeZe
# Licensed under the Apache License, Version 2.0
# Repository: https://github.com/MonsterZeZe/AuditAgent

"""问答接口路由。"""

from typing import Any
from uuid import uuid4

from fastapi import APIRouter

from app.api.schemas.chat import ChatRequest, ChatResponse, SourceInfo
from app.application.orchestrator.orchestrator import AgentOrchestrator
from app.application.session.session import SessionManager
from app.core.logging.logger import get_logger
from app.domain.memory.store import SqliteMemoryStore

router = APIRouter()
logger = get_logger(__name__)

_orchestrator = AgentOrchestrator()
_session_manager = SessionManager()
_memory_store = SqliteMemoryStore()


def _build_sources(state: Any) -> list[SourceInfo]:
    """从状态中提取引用来源。"""
    rag_context = state.get("rag_context") or {}
    sources = rag_context.get("sources") or []
    return [
        SourceInfo(
            doc_name=s.get("doc_name", ""),
            chapter=str(s.get("chapter", "")),
            page=str(s.get("page", "")),
            security_level=s.get("security_level", ""),
        )
        for s in sources
    ]


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    """执行一次审计问答。"""
    user_id = req.user_id or "anonymous"
    trace_id = uuid4().hex
    session_id = _session_manager.get_or_create(req.session_id, user_id)
    logger.info("收到问答请求", extra={"trace_id": trace_id, "session_id": session_id})

    history = _session_manager.load_messages(session_id)
    memories = _memory_store.recall(user_id, top_k=3)
    initial_state = {
        "user_input": req.question,
        "session_id": session_id,
        "trace_id": trace_id,
        "user_id": user_id,
        "chat_history": history,
        "long_term_memory": memories,
    }
    result = await _orchestrator.ainvoke(initial_state)
    _session_manager.append(session_id, "user", req.question)
    _session_manager.append(session_id, "assistant", result.get("generation", ""))
    _memory_store.add_memory(
        user_id,
        "task_history",
        f"问：{req.question}\n答：{result.get('generation', '')[:200]}",
        topic=req.question[:50],
    )

    return ChatResponse(
        trace_id=trace_id,
        session_id=session_id,
        answer=result.get("generation", ""),
        intent=result.get("intent", {}).get("intent_type", ""),
        route=result.get("route", ""),
        sources=_build_sources(result),
        execution_status=result.get("execution_status", "failed"),
    )
