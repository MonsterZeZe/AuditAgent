"""记忆系统抽象接口。

统一记忆读写接口，所有 Agent 必须通过记忆网关访问记忆系统，
内置按角色分配的读写权限与数据范围。
"""

from abc import ABC, abstractmethod
from typing import Optional


class MemoryStore(ABC):
    """记忆存取抽象。"""

    @abstractmethod
    def load_short_term(self, session_id: str) -> list[dict]:
        """加载短期记忆（会话消息历史）。"""

    @abstractmethod
    def recall_long_term(
        self,
        user_id: str,
        topic: Optional[str] = None,
        top_k: int = 5,
    ) -> list[dict]:
        """召回长期记忆。"""

    @abstractmethod
    def archive(self, session_id: str) -> None:
        """会话结束后归档重要信息到长期记忆库。"""
