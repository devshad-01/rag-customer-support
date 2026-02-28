"""RAG pipeline orchestrator — retrieve → prompt → generate → score."""

import logging
import time

from app.rag.retriever import retrieve_relevant_chunks
from app.rag.prompt_builder import build_prompt
from app.rag.llm_client import generate_response
from app.rag.confidence import calculate_confidence
from app.rag.explainability import (
    rank_sources_by_relevance,
    highlight_relevant_passages,
    assess_evidence_sufficiency,
)

logger = logging.getLogger(__name__)


async def process_query(query: str) -> dict:
    """Run the full RAG pipeline for a customer query.

    Steps:
      1. Retrieve relevant document chunks from Qdrant
      2. Calculate confidence & evidence sufficiency
      3. Build a context-enriched prompt
      4. Generate an LLM response via Ollama
      5. Rank sources & highlight relevant passages

    Args:
        query: The user's natural-language question.

    Returns:
        dict with:
          response      — str, the AI answer (prefixed with disclaimer if weak)
          sources       — list[dict], ranked, each with title, page, chunk_text,
                          score, document_id, chunk_id, rank, is_primary
          confidence    — dict with confidence_score, has_sufficient_evidence,
                          escalation_action
          evidence      — dict with evidence_quality, disclaimer
          highlights    — list[dict], response-to-source mappings
          total_sources_found — int
          response_time_ms — int, wall-clock milliseconds
    """
    start = time.perf_counter()

    # Step 1 — Retrieve
    chunks = retrieve_relevant_chunks(query, top_k=5)

    # Step 2 — Score confidence
    confidence = calculate_confidence(chunks)

    # Step 3 — Build source references & rank them
    sources = [
        {
            "title": c.get("source_title") or f"Document {c.get('document_id', '?')}",
            "page_number": c.get("page_number"),
            "chunk_text": c.get("chunk_text", ""),
            "score": round(c.get("score", 0), 4),
            "document_id": c.get("document_id"),
            "chunk_id": c.get("chunk_id", ""),
        }
        for c in chunks
    ]
    sources = rank_sources_by_relevance(sources)

    # Step 4 — Assess evidence sufficiency
    evidence = assess_evidence_sufficiency(sources, confidence["confidence_score"])

    # Step 5 — Build prompt & generate
    prompt = build_prompt(query, chunks)
    response_text = await generate_response(prompt)

    # Step 6 — Prepend disclaimer if evidence is weak
    if evidence["disclaimer"]:
        response_text = f"⚠️ {evidence['disclaimer']}\n\n{response_text}"

    # Step 7 — Highlight relevant passages
    highlights = highlight_relevant_passages(response_text, sources)

    elapsed_ms = int((time.perf_counter() - start) * 1000)

    logger.info(
        "RAG pipeline complete in %dms  confidence=%.4f  sources=%d  evidence=%s",
        elapsed_ms,
        confidence["confidence_score"],
        len(sources),
        evidence["evidence_quality"],
    )

    return {
        "response": response_text,
        "sources": sources,
        "confidence": confidence,
        "evidence": evidence,
        "highlights": highlights,
        "total_sources_found": len(sources),
        "response_time_ms": elapsed_ms,
    }
