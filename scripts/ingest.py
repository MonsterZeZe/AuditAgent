"""审计文档批量入库脚本。

用法:
    python scripts/ingest.py <文件或目录> [--collection accounting_standards]

遍历目录下所有支持的文档（txt/pdf/docx），加载、分块、嵌入并入库。
"""

import argparse
import sys
from pathlib import Path

# 确保项目根目录在 sys.path 中，支持任意位置执行脚本
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.logging.logger import setup_logging  # noqa: E402
from app.domain.rag.ingestion.service import IngestionService  # noqa: E402
from app.domain.rag.ingestion.splitters.factory import get_collection_for_path  # noqa: E402
from app.domain.rag.retrieval.embedding import SentenceTransformerEmbeddingProvider  # noqa: E402
from app.infrastructure.vector_store.chroma_store import ChromaVectorStore  # noqa: E402

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
    parser.add_argument("--collection", default=None, help="目标 Collection（默认按路径自动判断）")
    parser.add_argument("--chunk-size", type=int, default=500)
    parser.add_argument("--chunk-overlap", type=int, default=50)
    args = parser.parse_args()

    setup_logging()

    collection = args.collection or get_collection_for_path(args.path)
    print(f"目标 Collection: {collection}")

    vector_store = ChromaVectorStore()
    embedding = SentenceTransformerEmbeddingProvider()
    service = IngestionService(
        vector_store=vector_store,
        embedding=embedding,
        collection=collection,
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
