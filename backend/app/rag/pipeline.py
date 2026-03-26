"""RAG pipeline orchestrator — retrieve → prompt → generate → score."""

import logging
import time

from app.rag.retriever import retrieve_relevant_chunks
from app.rag.prompt_builder import build_prompt, build_out_of_scope_prompt
from app.rag.llm_client import generate_response
from app.rag.confidence import calculate_confidence
from app.rag.explainability import (
    rank_sources_by_relevance,
    highlight_relevant_passages,
    assess_evidence_sufficiency,
)

logger = logging.getLogger(__name__)

_DANGLING_ENDINGS = {
    "about", "with", "for", "to", "and", "or", "of", "in", "on", "at", "from", "by", "as",
}


def _looks_like_provider_error_response(text: str) -> bool:
    """Detect fallback error text returned by provider clients."""
    normalized = (text or "").strip().lower()
    if not normalized:
        return True

    error_signals = [
        "something went wrong while processing your question",
        "i'm sorry, the ai service is currently unavailable",
        "i encountered an error while generating a response",
        "i'm sorry, i encountered an error while processing your question",
    ]
    return any(signal in normalized for signal in error_signals)


def _finalize_in_scope_response(response_text: str) -> str:
    """Normalize in-scope model output to avoid visibly cut-off endings."""
    text = (response_text or "").strip()
    if not text:
        return (
            "I couldn't generate a complete response just now. "
            "Please try again, and I can help with the details."
        )

    words = text.split()
    if words:
        last_word = words[-1].rstrip(".,!?;:").lower()
        if last_word in _DANGLING_ENDINGS:
            text = " ".join(words[:-1]).rstrip(" ,;:")

    if text and text[-1] not in ".!?":
        text = f"{text}."

    return text


def _finalize_out_of_scope_response(response_text: str) -> str:
    """Return a clean, complete out-of-scope response for customer-facing UX."""
    fallback = (
        "I can help with questions about our products and services. "
        "If you share a bit more context about what you're looking for, I can guide you to the best next step."
    )
    follow_up_sentence = (
        "If you tell me what you're trying to do, which product it's for, or your budget range, I can help more specifically."
    )

    text = (response_text or "").strip()
    if not text:
        return fallback

    words = text.split()
    last_word = words[-1].rstrip(".,!?;:").lower() if words else ""
    if last_word in _DANGLING_ENDINGS:
        return fallback

    if text[-1] not in ".!?":
        text = f"{text}."

    if len(words) < 8:
        text = (
            f"{text} Share a bit more context and I can give a more useful answer."
        )

    sentence_count = sum(1 for ch in text if ch in ".!?")
    if sentence_count < 2:
        text = f"{text} {follow_up_sentence}"

    if len(text.split()) < 16:
        text = f"{text} A little more detail will help me give a clearer recommendation."

    return text


async def process_query(
    query: str,
    ai_config: dict | None = None,
    customer_name: str | None = None,
    recent_messages: list[dict] | None = None,
) -> dict:
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

    try:
        ai_config = ai_config or {}
        system_template_extension = ai_config.get("system_template_extension", "")
        no_escalate_out_of_scope = bool(ai_config.get("no_escalate_out_of_scope", True))

        # Step 1 — Retrieve
        chunks = retrieve_relevant_chunks(query, top_k=5)

        # Out-of-scope handling (no-escalation policy when configured)
        if not chunks and no_escalate_out_of_scope:
            out_of_scope_prompt = build_out_of_scope_prompt(
                query=query,
                customer_name=customer_name,
                system_template_extension=system_template_extension,
                recent_messages=recent_messages,
            )
            dynamic_response = await generate_response(out_of_scope_prompt)
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            return {
                "response": _finalize_out_of_scope_response(dynamic_response),
                "sources": [],
                "confidence": {
                    "confidence_score": 0.0,
                    "has_sufficient_evidence": False,
                    "escalation_action": "none",
                },
                "evidence": {
                    "evidence_quality": "none",
                    "has_sufficient_evidence": False,
                    "disclaimer": None,
                },
                "highlights": [],
                "total_sources_found": 0,
                "response_time_ms": elapsed_ms,
            }

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
        prompt = build_prompt(
            query,
            chunks,
            system_template_extension=system_template_extension,
            recent_messages=recent_messages,
        )
        response_text = await generate_response(prompt)
        if _looks_like_provider_error_response(response_text):
            raise RuntimeError("LLM provider returned fallback error text")
        response_text = _finalize_in_scope_response(response_text)

        # Step 6 — Highlight relevant passages
        highlights = highlight_relevant_passages(response_text, sources)

    except Exception as exc:
        logger.error("RAG pipeline error: %s", exc, exc_info=True)
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return {
            "response": (
                "I couldn't complete that response right now due to a temporary issue. "
                "Please try again in a moment."
            ),
            "sources": [],
            "confidence": {
                "confidence_score": 0.0,
                "has_sufficient_evidence": False,
                "escalation_action": "none",
            },
            "evidence": {
                "evidence_quality": "none",
                "has_sufficient_evidence": False,
                "disclaimer": "An error occurred while processing your query.",
            },
            "highlights": [],
            "total_sources_found": 0,
            "response_time_ms": elapsed_ms,
        }

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
