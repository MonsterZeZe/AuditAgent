"""TextSplitter 分块器单元测试。"""

import pytest

from app.domain.rag.ingestion.splitters.text import TextSplitter


def test_split_with_overlap() -> None:
    s = TextSplitter(chunk_size=10, chunk_overlap=2)
    assert s.split("12345678901234567890") == ["1234567890", "9012345678", "7890"]


def test_split_empty() -> None:
    s = TextSplitter()
    assert s.split("") == []
    assert s.split("   ") == []


def test_split_short_text() -> None:
    s = TextSplitter(chunk_size=100, chunk_overlap=10)
    assert s.split("短文本") == ["短文本"]


def test_invalid_overlap() -> None:
    with pytest.raises(ValueError):
        TextSplitter(chunk_size=10, chunk_overlap=10)
