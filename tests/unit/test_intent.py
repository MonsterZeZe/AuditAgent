"""意图识别单元测试。"""

from app.domain.intent.router import IntentRouter


def test_knowledge_query() -> None:
    router = IntentRouter()
    result = router.classify("什么是会计准则")
    assert result["route"] == "rag"
    assert result["intent_type"] == "knowledge_query"


def test_tool_operation() -> None:
    router = IntentRouter()
    result = router.classify("帮我计算这个报表的勾稽关系")
    assert result["route"] == "tool"
    assert result["intent_type"] == "tool_operation"


def test_direct_qa() -> None:
    router = IntentRouter()
    result = router.classify("你好")
    assert result["route"] == "direct"
    assert result["intent_type"] == "direct_qa"
