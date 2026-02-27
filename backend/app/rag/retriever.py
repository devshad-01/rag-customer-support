"""Retriever — embed a user query and search Qdrant for relevant chunks."""

import logging

from app.rag.embedder import embed_query
from app.rag.vector_store import search_similar

logger = logging.getLogger(__name__)

# Minimum similarity score to keep a chunk (filter noise)
SIMILARITY_THRESHOLD = 0.3


def retrieve_relevant_chunks(
    query: str,
    top_k: int = 5,
    threshold: float = SIMILARITY_THRESHOLD,
) -> list[dict]:
    """Embed a user query and find the most relevant document chunks.

    Args:
        query: The user's natural-language question.
        top_k: Maximum number of chunks to retrieve.
        threshold: Minimum cosine-similarity score to include a chunk.

    Returns:
        List of dicts, each with:
          chunk_text, source_title, page_number, document_id, score
        Sorted by score descending.  Empty list when nothing is relevant.
    """
    logger.info("Retrieving chunks for query: %.80s…", query)

    # Step 1 — embed the query with the same model used during ingestion
    query_embedding = embed_query(query)

    # Step 2 — search Qdrant
    raw_results = search_similar(query_embedding, top_k=top_k)

    # Step 3 — apply similarity threshold
    filtered = [r for r in raw_results if r["score"] >= threshold]

    if not filtered:
        logger.info("No chunks above threshold %.2f for query", threshold)
        return []

    logger.info(
        "Retrieved %d/%d chunks (threshold=%.2f, top_score=%.4f)",
        len(filtered),
        len(raw_results),
        threshold,
        filtered[0]["score"],
    )
    return filtered
