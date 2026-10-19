# Copyright 2026 MonsterZeZe
# Licensed under the Apache License, Version 2.0
# Repository: https://github.com/MonsterZeZe/AuditAgent

"""分块策略工厂。

按文档路径选择合适的分块器，实现差异化入库：
- 判例（judgements）→ 按"一、二、"结构化分块
- 政策解读 → 按"一、二、"分点分块
- 其他法规（laws）→ 按"第X条"分块
"""


def get_splitter_for_path(path: str):
    """根据文档路径返回对应的分块器。"""
    p = str(path)
    if "judgements" in p or "财政部政策解读" in p:
        from app.domain.rag.ingestion.splitters.judgement import JudgementSplitter

        return JudgementSplitter()
    from app.domain.rag.ingestion.splitters.article import ArticleSplitter

    return ArticleSplitter()


def get_collection_for_path(path: str) -> str:
    """根据文档路径返回对应的 ChromaDB Collection。"""
    p = str(path)
    if "judgements" in p:
        return "case_library"
    return "regulatory_laws"
