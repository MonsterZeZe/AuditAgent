"""会话管理（SQLite 持久化）。

会话生命周期：创建 → 激活 → 挂起 → 归档 → 销毁。
对话历史（短期记忆）持久化到 SQLite，支持窗口截断与跨重启恢复。
"""

import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import uuid4


class SessionManager:
    """基于 SQLite 的会话管理器。"""

    def __init__(self, db_path: Optional[str] = None, max_messages: int = 20) -> None:
        if db_path is None:
            from app.core.config.settings import get_settings

            db_path = get_settings().session_db_path
        self._db_path = db_path
        self._max_messages = max_messages
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_db(self) -> None:
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, id);
                """
            )
            conn.commit()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def get_or_create(self, session_id: Optional[str], user_id: str = "anonymous") -> str:
        """获取已存在会话，不存在则创建并返回会话 ID。"""
        new_id = session_id or uuid4().hex
        with closing(self._connect()) as conn:
            exists = conn.execute(
                "SELECT 1 FROM sessions WHERE session_id=?", (new_id,)
            ).fetchone()
            if exists:
                return new_id
            now = self._now()
            conn.execute(
                "INSERT INTO sessions (session_id, user_id, status, created_at, updated_at) "
                "VALUES (?,?,?,?,?)",
                (new_id, user_id, "active", now, now),
            )
            conn.commit()
        return new_id

    def load_messages(self, session_id: str) -> list[dict]:
        """加载会话历史消息（短期记忆，最近窗口）。"""
        with closing(self._connect()) as conn:
            rows = conn.execute(
                "SELECT role, content FROM messages WHERE session_id=? "
                "ORDER BY id DESC LIMIT ?",
                (session_id, self._max_messages),
            ).fetchall()
        return [{"role": r[0], "content": r[1]} for r in reversed(rows)]

    def append(self, session_id: str, role: str, content: str) -> None:
        """追加一条消息，并截断超窗口的旧消息。"""
        now = self._now()
        with closing(self._connect()) as conn:
            conn.execute(
                "INSERT INTO messages (session_id, role, content, created_at) "
                "VALUES (?,?,?,?)",
                (session_id, role, content, now),
            )
            conn.execute(
                "UPDATE sessions SET updated_at=? WHERE session_id=?",
                (now, session_id),
            )
            conn.execute(
                "DELETE FROM messages WHERE session_id=? AND id NOT IN ("
                "SELECT id FROM messages WHERE session_id=? ORDER BY id DESC LIMIT ?)",
                (session_id, session_id, self._max_messages),
            )
            conn.commit()

    def clear(self, session_id: str) -> None:
        """删除会话及其历史消息。"""
        with closing(self._connect()) as conn:
            conn.execute("DELETE FROM sessions WHERE session_id=?", (session_id,))
            conn.commit()

    def list_sessions(self, user_id: Optional[str] = None) -> list[dict]:
        """列出会话（可选按用户过滤），按更新时间倒序。"""
        with closing(self._connect()) as conn:
            if user_id:
                rows = conn.execute(
                    "SELECT session_id, user_id, status, created_at, updated_at "
                    "FROM sessions WHERE user_id=? ORDER BY updated_at DESC",
                    (user_id,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT session_id, user_id, status, created_at, updated_at "
                    "FROM sessions ORDER BY updated_at DESC",
                ).fetchall()
        return [
            {
                "session_id": r[0],
                "user_id": r[1],
                "status": r[2],
                "created_at": r[3],
                "updated_at": r[4],
            }
            for r in rows
        ]
