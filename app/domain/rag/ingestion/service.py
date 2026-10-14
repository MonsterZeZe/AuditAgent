"""数据接入服务。

文档加载 → 分块 → 嵌入 → 入库（ChromaDB）。入库以文档 ID 为幂等键，
重复入库同一文档覆盖旧数据。
"""

from pathlib import Path
from typing import Any, Optional

from app.domain.rag.base import EmbeddingProvider
from app.domain.rag.ingestion.loader import get_loader
from app.domain.rag.ingestion.splitters.factory import get_splitter_for_path
from app.domain.rag.ingestion.splitters.text import TextSplitter
from app.infrastructure.vector_store.base import VectorStore


class IngestionService:
    """数据接入服务。"""

    def __init__(
        self,
        vector_store: VectorStore,
        embedding: EmbeddingProvider,
        collection: str = "accounting_standards",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        splitter: Any = None,
    ) -> None:
        self._vector_store = vector_store
        self._embedding = embedding
        self._collection = collection
        self._default_splitter = splitter or TextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )

    def ingest_file(
        self,
        path: str,
        doc_id: Optional[str] = None,
        doc_name: Optional[str] = None,
    ) -> list[str]:
        """加载单个文件并入库（按路径选择分块策略），返回分块列表。"""
        loader = get_loader(path)
        text = loader.load(path)
        name = doc_name or Path(path).name
        splitter = get_splitter_for_path(str(path))
        return self.ingest_text(
            text, doc_id=doc_id or str(Path(path)), doc_name=name, splitter=splitter
        )

    def ingest_text(
        self,
        text: str,
        doc_id: str,
        doc_name: str = "",
        metadata: Optional[dict] = None,
        splitter: Any = None,
    ) -> list[str]:
        """将文本分块、嵌入并入库，返回分块列表。"""
        chunks = (splitter or self._default_splitter).split(text)
        if not chunks:
            return []
        embeddings = self._embedding.embed(chunks)
        metadatas = []
        for i in range(len(chunks)):
            meta = {
                "doc_id": doc_id,
                "doc_name": doc_name,
                "chapter": "",
                "page": i + 1,
                "publish_time": "",
                "source": doc_id,
                "security_level": "internal",
            }
            if metadata:
                meta.update(metadata)
            metadatas.append(meta)
        self._vector_store.add(self._collection, chunks, metadatas, embeddings)
        return chunks
