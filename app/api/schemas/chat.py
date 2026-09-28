"""问答接口请求/响应模型。"""

from typing import Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """问答请求。"""

    question: str = Field(..., min_length=1, max_length=8192)
    session_id: Optional[str] = None
    user_id: Optional[str] = None


class SourceInfo(BaseModel):
    """引用来源信息。"""

    doc_name: str = ""
    chapter: str = ""
    page: str = ""
    security_level: str = ""


class ChatResponse(BaseModel):
    """问答响应。"""

    trace_id: str
    session_id: str
    answer: str
    intent: str = ""
    route: str = ""
    sources: list[SourceInfo] = Field(default_factory=list)
    execution_status: str = "success"
