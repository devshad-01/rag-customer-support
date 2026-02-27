"""Ingestion pipeline — parse PDF → chunk → embed → store in Qdrant."""

import logging

import fitz  # pymupdf

from app.rag.chunker import Chunk, split_pages
from app.rag.embedder import embed_texts
from app.rag.vector_store import store_embeddings

logger = logging.getLogger(__name__)


def extract_pages_from_pdf(file_path: str) -> list[dict]:
    """Extract text from each page of a PDF file using PyMuPDF.

    Returns list of dicts: [{'page_number': 1, 'text': '...'}, ...]
    """
    pages: list[dict] = []
    doc = fitz.open(file_path)
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text("text").strip()
        if text:
            pages.append({"page_number": page_num + 1, "text": text})
    doc.close()
    logger.info("Extracted %d non-empty pages from %s", len(pages), file_path)
    return pages


def ingest_document(document_id: int, file_path: str, source_title: str = "") -> dict:
    """Full ingestion pipeline for a single document.

    1. Parse PDF → extract page texts
    2. Chunk pages into overlapping segments
    3. Generate embeddings for all chunks
    4. Store embeddings + metadata in Qdrant

    Returns dict with 'page_count', 'chunk_count', 'point_ids'.
    """
    # Step 1: Parse
    pages = extract_pages_from_pdf(file_path)
    if not pages:
        raise ValueError(f"No text could be extracted from {file_path}")

    page_count = len(pages)

    # Step 2: Chunk
    chunks: list[Chunk] = split_pages(pages)
    if not chunks:
        raise ValueError("Text splitting produced zero chunks")

    # Step 3: Embed
    chunk_texts = [c.text for c in chunks]
    embeddings = embed_texts(chunk_texts)

    # Step 4: Store in Qdrant
    chunk_dicts = [
        {"text": c.text, "index": c.index, "page_number": c.page_number}
        for c in chunks
    ]
    point_ids = store_embeddings(document_id, chunk_dicts, embeddings, source_title=source_title)

    logger.info(
        "Ingestion complete for document_id=%d: %d pages, %d chunks",
        document_id,
        page_count,
        len(chunks),
    )
    return {
        "page_count": page_count,
        "chunk_count": len(chunks),
        "point_ids": point_ids,
        "chunks": chunk_dicts,
    }
