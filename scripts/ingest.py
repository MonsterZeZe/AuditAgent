"""审计文档批量入库脚本。

用法:
    python scripts/ingest.py <文件或目录> [--collection accounting_standards]

遍历目录下所有支持的文档（txt/pdf/docx），加载、分块、嵌入并入库。
"""

import argparse
import sys
from pathlib import Path

from app.core.logging.logger import setup_logging
from app.domain.rag.embedding import OllamaEmbeddingProvider
from app.domain.rag.ingestion import IngestionService
from app.infrastructure.vector_store.chroma_store import ChromaVectorStore

SUPPORTED_SUFFIXES = {".txt", ".md", ".markdown", ".pdf", ".docx"}


def collect_files(path: Path) -> list[Path]:
    """收集待入库的文件。"""
    if path.is_file():
        return [path]
    if path.is_dir():
        return [
            p
            for p in sorted(path.rglob("*"))
            if p.is_file() and p.suffix.lower() in SUPPORTED_SUFFIXES
        ]
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description="审计文档批量入库")
    parser.add_argument("path", help="文件或目录路径")
    parser.add_argument("--collection", default="accounting_standards", help="目标 Collection")
    parser.add_argument("--chunk-size", type=int, default=500)
    parser.add_argument("--chunk-overlap", type=int, default=50)
    args = parser.parse_args()

    setup_logging()

    vector_store = ChromaVectorStore()
    embedding = OllamaEmbeddingProvider()
    service = IngestionService(
        vector_store=vector_store,
        embedding=embedding,
        collection=args.collection,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
    )

    files = collect_files(Path(args.path))
    if not files:
        print("未找到可入库的文件（支持 txt/pdf/docx）")
        return 1

    total_chunks = 0
    for f in files:
        try:
            chunks = service.ingest_file(str(f))
            total_chunks += len(chunks)
            print(f"已入库: {f} ({len(chunks)} 个分块)")
        except Exception as exc:  # noqa: BLE001
            print(f"入库失败: {f} - {exc}")

    print(f"完成，共入库 {len(files)} 个文件 / {total_chunks} 个分块")
    return 0


if __name__ == "__main__":
    sys.exit(main())
