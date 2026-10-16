"""ChromaDB 向量库适配器。"""

from typing import Any, Optional

import chromadb

from app.core.config.settings import get_settings
from app.infrastructure.vector_store.base import VectorStore


class ChromaVectorStore(VectorStore):
    """ChromaDB 持久化实现。"""

    def __init__(self) -> None:
        settings = get_settings()
        self._client = chromadb.PersistentClient(path=settings.chroma_persist_dir)

    def add(
        self,
        collection: str,
        documents: list[str],
        metadatas: list[dict],
        embeddings: list[list[float]],
    ) -> None:
        coll = self.get_collection(collection)
        # 同一文档分块需唯一 ID，用 doc_id + 序号
        ids = [f"{m.get('doc_id', 'doc')}_{i}" for i, m in enumerate(metadatas)]
        coll.add(ids=ids, documents=documents, metadatas=metadatas, embeddings=embeddings)

    def query(
        self,
        collection: str,
        embedding: list[float],
        top_k: int = 20,
        filters: Optional[dict] = None,
    ) -> list[dict]:
        coll = self.get_collection(collection)
        result = coll.query(
            query_embeddings=[embedding],
            n_results=top_k,
            where=filters,
        )
        docs: list[dict] = []
        for i, doc_id in enumerate(result["ids"][0]):
            docs.append(
                {
                    "doc_id": doc_id,
                    "content": result["documents"][0][i],
                    "metadata": result["metadatas"][0][i] if result["metadatas"][0] else {},
                    "score": result["distances"][0][i] if result["distances"] else 0.0,
                }
            )
        return docs

    def delete(self, collection: str, ids: list[str]) -> None:
        coll = self.get_collection(collection)
        coll.delete(ids=ids)

    def get_collection(self, collection: str) -> Any:
        return self._client.get_or_create_collection(name=collection)

    def get_documents(
        self,
        collection: str,
        batch_size: int = 500,
        max_documents: Optional[int] = None,
    ) -> list[str]:
        """分页读取集合内文档，避免一次性加载大集合，可限制最大条数。"""
        coll = self.get_collection(collection)
        documents: list[str] = []
        offset = 0
        while True:
            if max_documents is not None and len(documents) >= max_documents:
                break
            limit = batch_size
            if max_documents is not None:
                limit = min(batch_size, max_documents - len(documents))
            data = coll.get(limit=limit, offset=offset, include=["documents"])
            batch = data.get("documents") or []
            if not batch:
                break
            documents.extend(batch)
            if len(batch) < limit:
                break
            offset += limit
        return documents
