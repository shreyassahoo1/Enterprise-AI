import hashlib
import logging
from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import Config

logger = logging.getLogger(__name__)


def _content_hash(text: str) -> str:
    return hashlib.md5(text.strip().encode()).hexdigest()


def split_documents(
    documents: List[Document],
    chunk_size: int = Config.CHUNK_SIZE,
    chunk_overlap: int = Config.CHUNK_OVERLAP,
) -> List[Document]:
    if not documents:
        return []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", "! ", "? ", "; ", ", ", " ", ""],
        length_function=len,
        is_separator_regex=False,
    )

    chunks = splitter.split_documents(documents)

    # Deduplicate identical chunks (e.g. repeated headers/footers)
    seen_hashes = set()
    unique_chunks = []
    for chunk in chunks:
        h = _content_hash(chunk.page_content)
        if h not in seen_hashes:
            seen_hashes.add(h)
            unique_chunks.append(chunk)

    # Add per-(source, page) chunk index
    counters: dict = {}
    for chunk in unique_chunks:
        key = (chunk.metadata.get("source"), chunk.metadata.get("page"))
        counters[key] = counters.get(key, 0) + 1
        chunk.metadata["chunk_index"] = counters[key]

    logger.info(
        "Split %d doc(s) into %d unique chunk(s) (from %d raw, chunk_size=%d, overlap=%d).",
        len(documents), len(unique_chunks), len(chunks), chunk_size, chunk_overlap,
    )
    return unique_chunks
