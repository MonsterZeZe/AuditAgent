# Copyright 2026 MonsterZeZe
# Licensed under the Apache License, Version 2.0
# Repository: https://github.com/MonsterZeZe/AuditAgent

"""文档加载器。

支持 TXT / PDF / DOCX 多格式，返回纯文本。各格式依赖采用懒加载，
未安装对应依赖时仅在首次使用时才报错，不影响其他格式。
"""

from abc import ABC, abstractmethod
from pathlib import Path


class DocumentLoader(ABC):
    """文档加载抽象。"""

    @abstractmethod
    def load(self, path: str) -> str:
        """加载文档为纯文本。"""


class TextLoader(DocumentLoader):
    """TXT 加载器（标准库）。"""

    def load(self, path: str) -> str:
        return Path(path).read_text(encoding="utf-8")


class PdfLoader(DocumentLoader):
    """PDF 加载器。"""

    def load(self, path: str) -> str:
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise ImportError("PDF 加载需要安装 pypdf") from exc
        reader = PdfReader(path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)


class DocxLoader(DocumentLoader):
    """DOCX 加载器。"""

    def load(self, path: str) -> str:
        try:
            import docx
        except ImportError as exc:
            raise ImportError("DOCX 加载需要安装 python-docx") from exc
        document = docx.Document(path)
        return "\n".join(p.text for p in document.paragraphs)


def get_loader(path: str) -> DocumentLoader:
    """根据文件扩展名返回对应加载器。"""
    suffix = Path(path).suffix.lower()
    if suffix in (".txt", ".md", ".markdown"):
        return TextLoader()
    if suffix == ".pdf":
        return PdfLoader()
    if suffix == ".docx":
        return DocxLoader()
    raise ValueError(f"暂不支持的文件格式: {suffix}")
