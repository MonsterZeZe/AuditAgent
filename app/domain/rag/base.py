"""RAG 领域接口定义。

定义嵌入生成与精排重排序的统一接口，实现为独立组件，可通过配置自由切换。
"""

from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    """嵌入模型抽象，统一嵌入生成接口。"""

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """生成文本嵌入向量。"""


class Reranker(ABC):
    """精排重排序抽象（CrossEncoder 交叉编码器）。"""

    @abstractmethod
    def rerank(
        self,
        query: str,
        candidates: list[dict],
        top_n: int = 5,
    ) -> list[dict]:
        """对候选文档精准打分排序，返回 TopN。"""
