"""BM25 关键词检索。"""

import re

from rank_bm25 import BM25Okapi

_TOKEN_PATTERN = re.compile(r"[\s,，。;；:：!！?？、()（）\[\]【】]+")


class BM25Retriever:
    """基于 BM25 的关键词检索。"""

    def __init__(self, documents: list[str]) -> None:
        self._documents = documents
        self._tokenized = [self._tokenize(d) for d in documents]
        self._bm25 = BM25Okapi(self._tokenized) if self._tokenized else None

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        # 简单切分：按空白与标点切分；中文场景后续可接入 jieba 分词
        return [t for t in _TOKEN_PATTERN.split(text) if t]

    def search(self, query: str, top_k: int = 20) -> list[dict]:
        """检索与查询最相关的文档，返回带得分的文档列表。"""
        if not self._bm25:
            return []
        tokens = self._tokenize(query)
        if not tokens:
            return []
        scores = self._bm25.get_scores(tokens)
        ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        return [
            {
                "index": i,
                "content": self._documents[i],
                "score": float(scores[i]),
            }
            for i in ranked
            if scores[i] > 0
        ]
