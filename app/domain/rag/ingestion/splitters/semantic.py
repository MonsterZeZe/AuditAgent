# Copyright 2026 MonsterZeZe
# Licensed under the Apache License, Version 2.0
# Repository: https://github.com/MonsterZeZe/AuditAgent

"""语义分块器。

用嵌入模型计算相邻句子的语义相似度，在相似度骤降处切分，
保证每个分块的语义完整性，同时受 chunk_size 上限约束。
"""

import re

_SENTENCE_PATTERN = re.compile(r"[^。！？!?；;\n]+[。！？!?；;]?")


class SemanticSplitter:
    """基于语义相似度的分块器。"""

    def __init__(
        self,
        embedding,
        chunk_size: int = 500,
        breakpoint_threshold: float = 0.55,
    ) -> None:
        self._embedding = embedding
        self._chunk_size = chunk_size
        self._breakpoint_threshold = breakpoint_threshold

    def split(self, text: str) -> list[str]:
        """将文本按语义边界切分为分块。"""
        sentences = [s for s in _SENTENCE_PATTERN.findall(text.strip()) if s.strip()]
        if not sentences:
            return []
        if len(sentences) == 1:
            return [text.strip()]

        embeddings = self._embedding.embed(sentences)

        chunks: list[str] = []
        current = sentences[0]
        current_len = len(current)
        for i in range(1, len(sentences)):
            sentence = sentences[i]
            similarity = self._cosine(embeddings[i - 1], embeddings[i])
            # 断点：语义相似度低，或分块长度超限
            if similarity < self._breakpoint_threshold or current_len + len(sentence) > self._chunk_size:
                chunks.append(current)
                current = sentence
                current_len = len(sentence)
            else:
                current += sentence
                current_len += len(sentence)
        if current:
            chunks.append(current)
        return chunks

    @staticmethod
    def _cosine(a: list[float], b: list[float]) -> float:
        # 嵌入已归一化，余弦相似度即点积
        return sum(x * y for x, y in zip(a, b))
