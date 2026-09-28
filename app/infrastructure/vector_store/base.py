"""向量库抽象接口。

定义统一的向量检索与数据入库接口，屏蔽 ChromaDB 等具体实现，
后续可切换为 Milvus、PGVector 等向量数据库而不影响上层业务。
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class VectorStore(ABC):
    """统一向量库接口。"""

    @abstractmethod
    def add(
        self,
        collection: str,
        documents: list[str],
        metadatas: list[dict],
        embeddings: list[list[float]],
    ) -> None:
        """批量写入向量。"""

    @abstractmethod
    def query(
        self,
        collection: str,
        embedding: list[float],
        top_k: int = 20,
        filters: Optional[dict] = None,
    ) -> list[dict]:
        """向量相似度检索，返回带得分与元数据的文档列表。"""

    @abstractmethod
    def delete(self, collection: str, ids: list[str]) -> None:
        """按 ID 删除文档。"""

    @abstractmethod
    def get_collection(self, collection: str) -> Any:
        """获取集合句柄。"""

    @abstractmethod
    def get_documents(self, collection: str) -> list[str]:
        """获取集合内全部文档内容（用于 BM25 索引重建）。"""
