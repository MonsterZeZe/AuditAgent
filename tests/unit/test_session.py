# Copyright 2026 MonsterZeZe
# Licensed under the Apache License, Version 2.0
# Repository: https://github.com/MonsterZeZe/AuditAgent

"""SessionManager（SQLite 持久化）单元测试。"""

from app.application.session.session import SessionManager


def test_get_or_create_reuses(tmp_path) -> None:
    sm = SessionManager(db_path=str(tmp_path / "sessions.db"))
    sid = sm.get_or_create(None, "user-1")
    assert sid
    assert sm.get_or_create(sid, "user-1") == sid


def test_append_and_load(tmp_path) -> None:
    sm = SessionManager(db_path=str(tmp_path / "sessions.db"))
    sid = sm.get_or_create(None, "user-1")
    sm.append(sid, "user", "问题1")
    sm.append(sid, "assistant", "答案1")
    messages = sm.load_messages(sid)
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"


def test_window_truncation(tmp_path) -> None:
    sm = SessionManager(db_path=str(tmp_path / "sessions.db"), max_messages=2)
    sid = sm.get_or_create(None, "user-1")
    for i in range(5):
        sm.append(sid, "user", f"消息{i}")
    messages = sm.load_messages(sid)
    assert len(messages) == 2
    assert messages[0]["content"] == "消息3"
    assert messages[1]["content"] == "消息4"


def test_persistence_across_instances(tmp_path) -> None:
    db = str(tmp_path / "sessions.db")
    sm_a = SessionManager(db_path=db)
    sid = sm_a.get_or_create(None, "user-1")
    sm_a.append(sid, "user", "问题")

    sm_b = SessionManager(db_path=db)
    assert len(sm_b.load_messages(sid)) == 1


def test_clear(tmp_path) -> None:
    sm = SessionManager(db_path=str(tmp_path / "sessions.db"))
    sid = sm.get_or_create(None, "user-1")
    sm.append(sid, "user", "问题")
    sm.clear(sid)
    assert sm.load_messages(sid) == []
