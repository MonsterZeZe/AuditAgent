"""Ollama 嵌入模型实现。"""

import ollama

from app.core.config.settings import get_settings
from app.domain.rag.base import EmbeddingProvider


class OllamaEmbeddingProvider(EmbeddingProvider):
    """基于 Ollama 的嵌入生成。"""

    def __init__(self) -> None:
        settings = get_settings()
        self.model = settings.embedding_model
        self._client = ollama.Client(host=settings.ollama_base_url)

    def embed(self, texts: list[str]) -> list[list[float]]:
        """生成文本嵌入向量。"""
        embeddings: list[list[float]] = []
        for text in texts:
            resp = self._client.embeddings(model=self.model, prompt=text)
            embeddings.append(resp["embedding"])
        return embeddings


class SentenceTransformerEmbeddingProvider(EmbeddingProvider):
    """基于 sentence-transformers 的本地嵌入模型（bge-large-zh-v1.5）。"""

    def __init__(self, model_path: str | None = None) -> None:
        if model_path is None:
            from app.core.config.settings import get_settings

            model_path = get_settings().semantic_embedding_model
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(model_path)

    def embed(self, texts: list[str]) -> list[list[float]]:
        """生成文本嵌入向量（已归一化）。"""
        vectors = self._model.encode(texts, normalize_embeddings=True)
        return [v.tolist() for v in vectors]
