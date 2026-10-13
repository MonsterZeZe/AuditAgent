"""服务懒加载单例。

节点通过懒加载获取领域层服务，避免启动时建立重资源连接。
"""

from functools import lru_cache


@lru_cache
def get_intent_router():
    from app.domain.intent.router import IntentRouter

    return IntentRouter()


@lru_cache
def get_llm():
    from app.infrastructure.llm.factory import create_llm_provider

    return create_llm_provider()


@lru_cache
def get_rag_engine():
    from app.domain.rag.embedding import OllamaEmbeddingProvider
    from app.domain.rag.engine import RAGEngine
    from app.domain.rag.reranker import CrossEncoderReranker
    from app.infrastructure.vector_store.chroma_store import ChromaVectorStore

    vector_store = ChromaVectorStore()
    embedding = OllamaEmbeddingProvider()
    reranker = CrossEncoderReranker()
    engine = RAGEngine(vector_store=vector_store, embedding=embedding, reranker=reranker)
    engine.rebuild_bm25()  # 从向量库重建 BM25 索引
    return engine


@lru_cache
def get_injection_detector():
    from app.domain.validator.injection import InjectionDetector

    return InjectionDetector()


@lru_cache
def get_tool_registry():
    from app.domain.tools.compliance import ComplianceCheckTool
    from app.domain.tools.registry import ToolRegistry

    registry = ToolRegistry()
    registry.register(ComplianceCheckTool())
    return registry
