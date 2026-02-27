"""RAG pipeline orchestrator — retrieve → prompt → generate → score."""

import logging
import time

from app.rag.retriever import retrieve_relevant_chunks
from app.rag.prompt_builder import build_prompt
from app.rag.llm_client import generate_response
from app.rag.confidence import calculate_confidence

logger = logging.getLogger(__name__)


async def process_query(query: str) -> dict:
    """Run the full RAG pipeline for a customer query.

    Steps:
      1. Retrieve relevant document chunks from Qdrant
      2. Build a context-enriched prompt
      3. Generate an LLM response via Ollama
      4. Calculate confidence score from retrieval quality

    Args:
        query: The user's natural-language question.

    Returns:
        dict with:
          response      — str, the AI answer
          sources       — list[dict], each with title, page, chunk_text, score
          confidence    — dict with confidence_score, has_sufficient_evidence,
                          escalation_action
          response_time_ms — int, wall-clock milliseconds
    """
    start = time.perf_counter()

    # Step 1 — Retrieve
    chunks = retrieve_relevant_chunks(query, top_k=5)

    # Step 2 — Score confidence before generating (we need it for logging)
    confidence = calculate_confidence(chunks)

    # Step 3 — Build prompt
    prompt = build_prompt(query, chunks)

    # Step 4 — Generate LLM response
    response_text = await generate_response(prompt)

    # Build source references for the frontend
    sources = [
        {
            "title": c.get("source_title") or f"Document {c.get('document_id', '?')}",
            "page_number": c.get("page_number"),
            "chunk_text": c.get("chunk_text", ""),
            "score": round(c.get("score", 0), 4),
            "document_id": c.get("document_id"),
        }
        for c in chunks
    ]

    elapsed_ms = int((time.perf_counter() - start) * 1000)

    logger.info(
        "RAG pipeline complete in %dms  confidence=%.4f  sources=%d",
        elapsed_ms,
        confidence["confidence_score"],
        len(sources),
    )

    return {
        "response": response_text,
        "sources": sources,
        "confidence": confidence,
        "response_time_ms": elapsed_ms,
    }
