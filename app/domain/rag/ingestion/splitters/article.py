# Copyright 2026 MonsterZeZe
# Licensed under the Apache License, Version 2.0
# Repository: https://github.com/MonsterZeZe/AuditAgent

"""按"条"分块器（针对法律法规）。

识别"第X条"作为语义边界，每条条文作为独立分块，
保证条文完整性，避免固定长度切分破坏条文语义。
"""

import re

_ARTICLE_RE = re.compile(r"第[一二三四五六七八九十百千零〇]+条")


class ArticleSplitter:
    """按"条"分块：每条法规条文作为一个独立语义单元。"""

    def __init__(self, max_chunk_size: int = 1200) -> None:
        self._max_chunk_size = max_chunk_size

    def split(self, text: str) -> list[str]:
        text = text.strip()
        if not text:
            return []

        matches = list(_ARTICLE_RE.finditer(text))
        if not matches:
            # 无条文结构，退化为按空行段落切分
            return [p.strip() for p in text.split("\n\n") if p.strip()]

        chunks: list[str] = []
        # 条文之前的内容（标题、章标题、目录）作为头部
        if matches[0].start() > 0:
            head = text[: matches[0].start()].strip()
            if head:
                chunks.extend(self._split_long(head))

        # 按条切分
        for i, m in enumerate(matches):
            start = m.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            article = text[start:end].strip()
            if article:
                chunks.extend(self._split_long(article))

        return chunks

    def _split_long(self, text: str) -> list[str]:
        """超长文本按空行段落细分，避免单块过长。"""
        if len(text) <= self._max_chunk_size:
            return [text]
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        result: list[str] = []
        current = ""
        for p in paragraphs:
            if len(current) + len(p) + 2 > self._max_chunk_size and current:
                result.append(current)
                current = p
            else:
                current = f"{current}\n\n{p}" if current else p
        if current:
            result.append(current)
        return result
