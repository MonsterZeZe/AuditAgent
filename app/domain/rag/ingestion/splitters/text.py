# Copyright 2026 MonsterZeZe
# Licensed under the Apache License, Version 2.0
# Repository: https://github.com/MonsterZeZe/AuditAgent

"""文本分块器。"""


class TextSplitter:
    """按字符数分块，支持重叠。语义分块策略后续优化。"""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50) -> None:
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap 必须小于 chunk_size")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split(self, text: str) -> list[str]:
        """将文本切分为固定大小的重叠分块。"""
        text = text.strip()
        if not text:
            return []
        chunks: list[str] = []
        start = 0
        length = len(text)
        while start < length:
            end = min(start + self.chunk_size, length)
            chunks.append(text[start:end])
            if end >= length:
                break
            start = end - self.chunk_overlap
        return chunks
