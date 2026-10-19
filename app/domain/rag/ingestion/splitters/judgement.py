# Copyright 2026 MonsterZeZe
# Licensed under the Apache License, Version 2.0
# Repository: https://github.com/MonsterZeZe/AuditAgent

"""判决书 / 政策解读结构化分块器。

按"一、二、"等分点标题切分（支持行内分点），并清理网页抓取残留。
适用于判决书、处罚决定书、政策解读等分点式文本。
"""

import re

# 匹配"一、""二、"等分点标题；负向后行排除"第X、"（如"第一、二款"）
_HEADING_RE = re.compile(r"(?<![第])[一二三四五六七八九十]+、")
_WEB_RESIDUE = ("【打印】", "【关闭窗口】")


class JudgementSplitter:
    """按"一、二、"分点标题切分的分块器。"""

    def __init__(self, max_chunk_size: int = 1200) -> None:
        self._max_chunk_size = max_chunk_size

    def split(self, text: str) -> list[str]:
        text = self._clean(text)
        if not text:
            return []

        matches = list(_HEADING_RE.finditer(text))
        if not matches:
            # 无分点结构，退化为整篇/按段落
            return self._split_long(text)

        chunks: list[str] = []
        # 分点前的头部（文号、当事人、引言）
        if matches[0].start() > 0:
            head = text[: matches[0].start()].strip()
            if head:
                chunks.extend(self._split_long(head))

        # 按分点切分
        for i, m in enumerate(matches):
            start = m.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            section = text[start:end].strip()
            if section:
                chunks.extend(self._split_long(section))

        return chunks

    @staticmethod
    def _clean(text: str) -> str:
        for residue in _WEB_RESIDUE:
            text = text.replace(residue, "")
        return text.strip()

    def _split_long(self, text: str) -> list[str]:
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
