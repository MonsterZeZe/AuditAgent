"""RAG 检索引擎（二阶检索）。

全链路：查询嵌入 → 多路召回（向量 + BM25）→ 加权融合去重 → 精排 → 上下文组装。
"""

from typing import Optional

from app.domain.rag.base import EmbeddingProvider, Reranker
from app.domain.rag.retrieval.bm25 import BM25Retriever
from app.infrastructure.vector_store.base import VectorStore


class RAGEngine:
    """二阶检索引擎。"""

    def __init__(
        self,
        vector_store: VectorStore,
        embedding: EmbeddingProvider,
        reranker: Optional[Reranker] = None,
        collection: str = "accounting_standards",
        vector_top_k: int = 20,
        bm25_top_k: int = 20,
        vector_weight: float = 0.6,
        bm25_weight: float = 0.4,
        top_n: int = 5,
    ) -> None:
        self._vector_store = vector_store
        self._embedding = embedding
        self._reranker = reranker
        self._collection = collection
        self._vector_top_k = vector_top_k
        self._bm25_top_k = bm25_top_k
        self._vector_weight = vector_weight
        self._bm25_weight = bm25_weight
        self._top_n = top_n
        self._bm25: Optional[BM25Retriever] = None

    def set_documents(self, documents: list[str]) -> None:
        """设置 BM25 关键词检索的文档集合（由数据接入模块调用）。"""
        self._bm25 = BM25Retriever(documents)

    def rebuild_bm25(self) -> None:
        """从向量库读取全部文档，重建 BM25 索引。"""
        documents = self._vector_store.get_documents(self._collection)
        self.set_documents(documents)

    def retrieve(self, query: str, filters: Optional[dict] = None) -> dict:
        """执行二阶检索，返回检索结果与组装后的上下文。"""
        query_embedding = self._embedding.embed([query])[0]

        vector_results = self._vector_store.query(
            self._collection,
            query_embedding,
            top_k=self._vector_top_k,
            filters=filters,
        )
        bm25_results = self._bm25.search(query, top_k=self._bm25_top_k) if self._bm25 else []

        fused = self._fuse(vector_results, bm25_results)

        if self._reranker and fused:
            final = self._reranker.rerank(query, fused, top_n=self._top_n)
        else:
            final = fused[: self._top_n]

        return {
            "chunks": final,
            "sources": [c.get("metadata", {}) for c in final],
            "assembled_prompt": self._assemble(final),
        }

    def _fuse(self, vector_results: list[dict], bm25_results: list[dict]) -> list[dict]:
        """多路结果加权融合去重（以 content 为去重键）。"""
        merged: dict[str, dict] = {}
        for r in vector_results:
            content = r.get("content", "")
            similarity = 1 - r.get("score", 0)  # 余弦距离 -> 相似度
            merged[content] = {
                "content": content,
                "metadata": r.get("metadata", {}),
                "doc_id": r.get("doc_id", ""),
                "score": similarity * self._vector_weight,
            }
        for r in bm25_results:
            content = r.get("content", "")
            bm25_score = r.get("score", 0)
            if content in merged:
                merged[content]["score"] += bm25_score * self._bm25_weight
            else:
                merged[content] = {
                    "content": content,
                    "metadata": {},
                    "doc_id": "",
                    "score": bm25_score * self._bm25_weight,
                }
        return sorted(merged.values(), key=lambda x: x["score"], reverse=True)

    @staticmethod
    def _assemble(chunks: list[dict]) -> str:
        """按模板拼接文档片段，注入来源元数据。"""
        parts: list[str] = []
        for i, c in enumerate(chunks, 1):
            meta = c.get("metadata", {})
            source = (
                f"来源: {meta.get('doc_name', '未知')} "
                f"章节: {meta.get('chapter', '')} 页码: {meta.get('page', '')}"
            )
            parts.append(f"[片段{i}] {source}\n{c.get('content', '')}")
        return "\n\n".join(parts)
