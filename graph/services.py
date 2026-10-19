# Copyright 2026 MonsterZeZe
# Licensed under the Apache License, Version 2.0
# Repository: https://github.com/MonsterZeZe/AuditAgent

"""服务懒加载单例。

节点通过懒加载获取领域层服务，避免启动时建立重资源连接。
"""

from functools import lru_cache

# 知识库标识 → ChromaDB Collection 映射（后续新增知识库在此扩展）
KNOWLEDGE_BASES = {
    "law": "regulatory_laws",
    "case": "case_library",
}


@lru_cache
def get_intent_router():
    from app.domain.intent.router import IntentRouter

    return IntentRouter()


@lru_cache
def get_injection_detector():
    from app.domain.validator.injection import InjectionDetector

    return InjectionDetector()


def _build_engine(collection: str):
    from app.domain.rag.engine import RAGEngine
    from app.domain.rag.retrieval.embedding import SentenceTransformerEmbeddingProvider
    from app.domain.rag.retrieval.reranker import CrossEncoderReranker
    from app.infrastructure.vector_store.chroma_store import ChromaVectorStore

    vector_store = ChromaVectorStore()
    embedding = SentenceTransformerEmbeddingProvider()
    reranker = CrossEncoderReranker()
    engine = RAGEngine(
        vector_store=vector_store,
        embedding=embedding,
        reranker=reranker,
        collection=collection,
    )
    engine.rebuild_bm25()  # 从向量库重建 BM25 索引
    return engine


@lru_cache
def get_engine(target: str):
    """按知识库标识（law/case）获取对应的检索引擎。"""
    collection = KNOWLEDGE_BASES[target]
    return _build_engine(collection)
