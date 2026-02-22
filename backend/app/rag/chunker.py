"""Text chunker — splits extracted document text into overlapping chunks."""

import logging
from dataclasses import dataclass

from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

# Defaults aligned with proposal – small chunks for precise retrieval
DEFAULT_CHUNK_SIZE = 500
DEFAULT_CHUNK_OVERLAP = 50


@dataclass
class Chunk:
    """Represents a single text chunk with metadata."""

    text: str
    index: int
    page_number: int | None = None


def split_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[Chunk]:
    """Split a document's full text into overlapping chunks.

    Returns a list of Chunk objects with sequential indices.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    raw_chunks = splitter.split_text(text)
    chunks = [Chunk(text=c, index=i) for i, c in enumerate(raw_chunks)]
    logger.info("Split text into %d chunks (size=%d, overlap=%d)", len(chunks), chunk_size, chunk_overlap)
    return chunks


def split_pages(
    pages: list[dict],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[Chunk]:
    """Split page-separated text (from PDF parser) into chunks.

    Args:
        pages: List of dicts with 'text' and 'page_number' keys.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks: list[Chunk] = []
    idx = 0
    for page in pages:
        page_chunks = splitter.split_text(page["text"])
        for text in page_chunks:
            chunks.append(Chunk(text=text, index=idx, page_number=page["page_number"]))
            idx += 1

    logger.info("Split %d pages into %d chunks", len(pages), len(chunks))
    return chunks
