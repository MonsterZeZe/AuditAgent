"""SqliteMemoryStore 长期记忆单元测试。"""

from app.domain.memory.store import SqliteMemoryStore


def test_add_and_recall(tmp_path) -> None:
    store = SqliteMemoryStore(db_path=str(tmp_path / "memories.db"))
    store.add_memory("user-1", "task_history", "内容1", topic="会计")
    store.add_memory("user-1", "task_history", "内容2", topic="法规")
    memories = store.recall("user-1", top_k=5)
    assert len(memories) == 2


def test_topic_filter(tmp_path) -> None:
    store = SqliteMemoryStore(db_path=str(tmp_path / "memories.db"))
    store.add_memory("user-1", "task_history", "内容1", topic="会计准则")
    store.add_memory("user-1", "task_history", "内容2", topic="监管法规")
    memories = store.recall("user-1", topic="会计", top_k=5)
    assert len(memories) == 1
    assert memories[0]["topic"] == "会计准则"


def test_user_isolation(tmp_path) -> None:
    store = SqliteMemoryStore(db_path=str(tmp_path / "memories.db"))
    store.add_memory("user-1", "task_history", "用户1的记忆")
    memories = store.recall("user-2", top_k=5)
    assert memories == []
