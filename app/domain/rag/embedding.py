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
