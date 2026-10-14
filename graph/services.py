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


def _build_engine(collection: str):
    from app.domain.rag.engine import RAGEngine
    from app.domain.rag.retrieval.embedding import OllamaEmbeddingProvider
    from app.domain.rag.retrieval.reranker import CrossEncoderReranker
    from app.infrastructure.vector_store.chroma_store import ChromaVectorStore

    vector_store = ChromaVectorStore()
    embedding = OllamaEmbeddingProvider()
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
def get_law_engine():
    """法规知识库检索引擎（审计准则、注册会计师法、财会法规）。"""
    return _build_engine("regulatory_laws")


@lru_cache
def get_case_engine():
    """判例知识库检索引擎（判决书、处罚案例）。"""
    return _build_engine("case_library")


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
