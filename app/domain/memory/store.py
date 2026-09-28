"""长期记忆存储（SQLite 持久化）。

记忆分类对应 MemoryType 枚举：用户画像 / 领域知识 / 任务历史。
支持按用户与主题召回，用于会话初始化时增强上下文。
"""

import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import uuid4


class SqliteMemoryStore:
    """基于 SQLite 的长期记忆存储。"""

    def __init__(self, db_path: Optional[str] = None) -> None:
        if db_path is None:
            from app.core.config.settings import get_settings

            db_path = get_settings().memory_db_path
        self._db_path = db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self) -> None:
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS long_term_memories (
                    memory_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    memory_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    topic TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_memory_user
                    ON long_term_memories(user_id, created_at);
                """
            )
            conn.commit()

    def add_memory(
        self,
        user_id: str,
        memory_type: str,
        content: str,
        topic: Optional[str] = None,
    ) -> str:
        """添加一条长期记忆，返回记忆 ID。"""
        memory_id = uuid4().hex
        now = datetime.now(timezone.utc).isoformat()
        with closing(self._connect()) as conn:
            conn.execute(
                "INSERT INTO long_term_memories "
                "(memory_id, user_id, memory_type, content, topic, created_at) "
                "VALUES (?,?,?,?,?,?)",
                (memory_id, user_id, memory_type, content, topic, now),
            )
            conn.commit()
        return memory_id

    def recall(
        self,
        user_id: str,
        topic: Optional[str] = None,
        top_k: int = 5,
    ) -> list[dict]:
        """按用户召回长期记忆，可选按主题过滤，按时间倒序。"""
        with closing(self._connect()) as conn:
            if topic:
                rows = conn.execute(
                    "SELECT memory_type, content, topic, created_at "
                    "FROM long_term_memories "
                    "WHERE user_id=? AND (topic LIKE ? OR topic IS NULL) "
                    "ORDER BY created_at DESC LIMIT ?",
                    (user_id, f"%{topic}%", top_k),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT memory_type, content, topic, created_at "
                    "FROM long_term_memories "
                    "WHERE user_id=? ORDER BY created_at DESC LIMIT ?",
                    (user_id, top_k),
                ).fetchall()
        return [
            {"memory_type": r[0], "content": r[1], "topic": r[2], "created_at": r[3]}
            for r in rows
        ]
