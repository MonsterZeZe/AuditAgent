"""CrossEncoder 精排实现。"""

from app.domain.rag.base import Reranker


class CrossEncoderReranker(Reranker):
    """基于 sentence-transformers CrossEncoder 的精排重排序。

    模型懒加载，避免服务启动时立即加载；首次调用时加载。
    默认从配置读取模型路径（models/bge-reranker-base）。
    """

    def __init__(self, model_name: str | None = None) -> None:
        if model_name is None:
            from app.core.config.settings import get_settings

            model_name = get_settings().reranker_model
        self._model_name = model_name
        self._model = None

    def _ensure_model(self):
        if self._model is None:
            from sentence_transformers import CrossEncoder

            self._model = CrossEncoder(self._model_name)
        return self._model

    def rerank(self, query: str, candidates: list[dict], top_n: int = 5) -> list[dict]:
        """对候选文档精准打分排序，返回 TopN。"""
        if not candidates:
            return []
        model = self._ensure_model()
        pairs = [(query, c["content"]) for c in candidates]
        scores = model.predict(pairs)
        for c, s in zip(candidates, scores):
            c["score"] = float(s)
        ranked = sorted(candidates, key=lambda c: c["score"], reverse=True)
        return ranked[:top_n]
