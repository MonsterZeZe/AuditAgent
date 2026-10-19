# Copyright 2026 MonsterZeZe
# Licensed under the Apache License, Version 2.0
# Repository: https://github.com/MonsterZeZe/AuditAgent

"""ArticleSplitter 按条分块单元测试。"""

from app.domain.rag.ingestion.splitters.article import ArticleSplitter


def test_split_by_article() -> None:
    text = "第一章 总则\n第一条 内容一。\n第二条 内容二。\n第三条 内容三。"
    splitter = ArticleSplitter()
    chunks = splitter.split(text)
    assert len(chunks) == 4  # 头部 + 三条
    assert "第二条 内容二" in chunks[2]


def test_no_article_fallback() -> None:
    text = "没有条文结构的普通文本。\n\n第二段。"
    splitter = ArticleSplitter()
    chunks = splitter.split(text)
    assert len(chunks) == 2
