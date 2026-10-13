"""SQLite 持久化基类。

统一连接管理、建表与时间戳，子类只需声明建表 DDL 与业务方法，
避免各存储类重复连接/建表样板代码。
"""

import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path


class SqliteBase:
    """SQLite 持久化基类。"""

    _DDL: str = ""  # 子类覆写：建表 DDL

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_db(self) -> None:
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as conn:
            conn.executescript(self._DDL)
            conn.commit()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()
